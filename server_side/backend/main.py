import os
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ResearchPaL Next-Gen Backend", version="1.0.0")

# Allow requests from the Next.js and Vite frontends
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.supabase_service import SupabaseService
from services.parse_service import ParseService
from services.embeddings_service import EmbeddingsService
from services.pwc_service import PWCService
from graph.agent import agent_graph

# Setup services
db_service = SupabaseService()
parse_service = ParseService()
pwc_service = PWCService()

import base64
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

gemini_api_key = os.getenv("GEMINI_API_KEY")

def extract_text_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        return "".join(text_parts)
    return str(content)

def semantic_chunk_text(text: str, api_keys: Dict[str, str], provider: str, max_chunk_size: int = 3000, min_chunk_size: int = 400) -> List[str]:
    # 1. Split into sentences
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        return [text] if text.strip() else []
        
    # 2. Get embeddings for sentences in batches
    sentence_embeddings = []
    batch_size = 16
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i+batch_size]
        try:
            embeds = EmbeddingsService.get_embeddings(
                texts=batch,
                api_keys=api_keys,
                provider=provider
            )
            sentence_embeddings.extend(embeds)
        except Exception as e:
            print(f"⚠️ Error getting sentence embeddings for semantic chunking: {str(e)}")
            sentence_embeddings.extend([[]] * len(batch))
            
    # Cosine similarity helper
    def cosine_similarity(v1, v2):
        if not v1 or not v2:
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = sum(a * a for a in v1) ** 0.5
        magnitude_v2 = sum(b * b for b in v2) ** 0.5
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)
        
    chunks = []
    current_chunk = []
    current_length = 0
    
    for idx, sentence in enumerate(sentences):
        if not current_chunk:
            current_chunk.append(sentence)
            current_length = len(sentence)
            continue
            
        sim = 1.0
        if idx < len(sentence_embeddings) and (idx - 1) < len(sentence_embeddings):
            sim = cosine_similarity(sentence_embeddings[idx - 1], sentence_embeddings[idx])
            
        if (sim < 0.75 and current_length >= min_chunk_size) or (current_length + len(sentence) > max_chunk_size):
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks
    
async def parse_and_index_task(
    file_content: bytes, 
    filename: str, 
    gemini_api_key: str, 
    jina_api_key: Optional[str] = None, 
    source_url: Optional[str] = None,
    parser_mode: str = "basic"
):
    """
    Background worker that handles PyMuPDF + Adobe PDF Extract API parsing, chunking, 
    visual figure/table summarization, embedding generation, and DB upload.
    """
    try:
        # 1. Parse using PyMuPDF & Adobe PDF Services
        plain_text, figures, tables = await parse_service.parse_pdf(file_content, filename, parser_mode)
        
        # Extract title from plain text using Gemini
        paper_title = filename.replace(".pdf", "").replace("_", " ")
        try:
            if plain_text:
                sample_text = plain_text[:1500]
                prompt = (
                    "Extract ONLY the main title of the research paper from the following text. "
                    "Return ONLY the title string, no markdown, no quotes, no extra text:\n\n"
                    f"{sample_text}"
                )
                from langchain_google_genai import ChatGoogleGenerativeAI
                title_llm = ChatGoogleGenerativeAI(
                    model="gemini-3.1-flash-lite",
                    google_api_key=gemini_api_key
                )
                title_res = title_llm.invoke(prompt)
                extracted_title = extract_text_content(title_res.content).strip().strip('"').strip("'")
                if extracted_title and len(extracted_title) > 5 and len(extracted_title) < 200 and "extract only" not in extracted_title.lower():
                    paper_title = extracted_title
        except Exception as te:
            print(f"⚠️ Warning: Failed to extract paper title using LLM: {te}")
        
        # 2. Insert master document record
        document_id = db_service.insert_document(
            paper_title=paper_title,
            paper_url=source_url or filename
        )
        
        # 3. Chunk the parsed plain text semantically
        print("ℹ️ Splitting text using Semantic Chunking...")
        embed_provider = "jina" if jina_api_key else "google"
        api_keys_dict = {"gemini": gemini_api_key, "jina": jina_api_key}
        text_chunks = semantic_chunk_text(
            text=plain_text,
            api_keys=api_keys_dict,
            provider=embed_provider
        )
        print(f"✅ Generated {len(text_chunks)} semantic chunks.")
        
        # 4. Generate summaries of figures using Gemini 3.1 Flash Lite Vision
        vision_model = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=gemini_api_key
        ).bind(response_mime_type="application/json")
        
        # Define a retry helper with exponential backoff for rate limits, with Groq fallback
        async def call_llm_with_retry(prompt, is_image=False, retries=3, initial_delay=4):
            delay = initial_delay
            groq_key = os.getenv("GROQ_API_KEY")
            
            for attempt in range(retries):
                try:
                    import asyncio
                    loop = asyncio.get_running_loop()
                    res = await loop.run_in_executor(None, lambda: vision_model.invoke([prompt]))
                    return extract_text_content(res.content)
                except Exception as e:
                    err_msg = str(e)
                    is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower()
                    print(f"⚠️ Gemini failed on attempt {attempt+1}/{retries}: {err_msg}")
                    
                    if is_rate_limit and groq_key:
                        print("ℹ️ Gemini rate limit hit. Skipping Gemini retries and falling back to Groq immediately...")
                        break
                        
                    if is_rate_limit and not groq_key:
                        print("⚠️ Daily/Minute rate limit hit and no GROQ_API_KEY configured. Fast-failing task to avoid massive delays.")
                        raise e
                        
                    if attempt < retries - 1:
                        print(f"Waiting {delay}s before retrying...")
                        await asyncio.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise e
            
            if groq_key:
                print(f"ℹ️ Initiating fallback to Groq...")
                try:
                    import asyncio
                    loop = asyncio.get_running_loop()
                    model_name = "llama-3.2-11b-vision-preview" if is_image else "llama-3.1-8b-instant"
                    groq_model = ChatGroq(
                        model=model_name,
                        groq_api_key=groq_key,
                        temperature=0.2
                    )
                    res = await loop.run_in_executor(None, lambda: groq_model.invoke([prompt]))
                    print(f"✅ Successfully fell back to Groq ({model_name})!")
                    return extract_text_content(res.content)
                except Exception as ge:
                    print(f"❌ Groq fallback also failed: {str(ge)}")
                    raise ge
            else:
                print("⚠️ Groq fallback skipped (no GROQ_API_KEY configured).")
                raise Exception("Gemini failed and no Groq fallback was available.")

        import json
        
        def clean_json_string(s):
            s = s.strip()
            if s.startswith("```"):
                lines = s.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                s = "\n".join(lines).strip()
            return s

        db_chunks = []
        
        # Process and summarize figures in batch
        if figures:
            print(f"ℹ️ Batch summarizing {len(figures)} figures...")
            content_list = [
                {"type": "text", "text": (
                    "You are analyzing a research paper. You are provided with multiple figures/diagrams extracted from the paper. "
                    "For each figure, describe it in detail. Focus on labels, axes, trends, and the main conclusion. "
                    "Provide a dense summary to be used for search retrieval. "
                    "You MUST respond ONLY with a JSON object in this exact format:\n"
                    "{\n"
                    "  \"summaries\": [\n"
                    "    {\n"
                    "      \"filename\": \"filename_of_figure.png\",\n"
                    "      \"summary\": \"Detailed summary of the figure...\"\n"
                    "    }\n"
                    "  ]\n"
                    "}\n"
                )}
            ]
            
            fig_storage_map = {}
            for img in figures:
                storage_path = f"documents/{document_id}/figures/{img['filename']}"
                db_service.upload_file(
                    bucket_name="figures",
                    path_on_bucket=storage_path,
                    file_content=img["content"],
                    content_type="image/png"
                )
                fig_storage_map[img["filename"]] = storage_path
                
                img_b64 = base64.b64encode(img["content"]).decode("utf-8")
                content_list.append({
                    "type": "text", "text": f"Filename: {img['filename']}"
                })
                content_list.append({
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{img_b64}"
                })
                
            prompt_msg = HumanMessage(content=content_list)
            
            summary_content = {}
            try:
                raw_res = await call_llm_with_retry(prompt_msg, is_image=True)
                clean_res = clean_json_string(raw_res)
                summary_data = json.loads(clean_res)
                summary_content = {item["filename"]: item["summary"] for item in summary_data.get("summaries", [])}
            except Exception as le:
                print(f"⚠️ Warning: Vision model failed to batch summarize figures: {str(le)}")
                
            import re
            for img in figures:
                desc = summary_content.get(img["filename"], "Figure image stored in database.")
                fig_page = 1
                page_match = re.search(r'(?:page|p)[_-]?(\d+)', img["filename"], re.IGNORECASE)
                if page_match:
                    fig_page = int(page_match.group(1))
                    
                db_chunks.append({
                    "document_id": document_id,
                    "content": f"[Figure Summary - {img['filename']}]: {desc}",
                    "page_number": fig_page,
                    "chunk_type": "figure_summary",
                    "image_path": fig_storage_map[img["filename"]]
                })
                
        # Process and summarize tables in batch
        if tables:
            print(f"ℹ️ Batch summarizing {len(tables)} tables...")
            table_prompt = (
                "You are analyzing a research paper. You are provided with multiple tables in CSV format. "
                "For each table, summarize the key information, data trends, and metrics found in it. "
                "You MUST respond ONLY with a JSON object in this exact format:\n"
                "{\n"
                "  \"summaries\": [\n"
                "    {\n"
                "      \"filename\": \"filename_of_table.csv\",\n"
                "      \"summary\": \"Detailed summary of the table...\"\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
            )
            for tbl in tables:
                table_prompt += f"--- Filename: {tbl['filename']} ---\n{tbl['content']}\n\n"
                
            prompt_msg = HumanMessage(content=table_prompt)
            
            summary_content = {}
            try:
                raw_res = await call_llm_with_retry(prompt_msg, is_image=False)
                clean_res = clean_json_string(raw_res)
                summary_data = json.loads(clean_res)
                summary_content = {item["filename"]: item["summary"] for item in summary_data.get("summaries", [])}
            except Exception as le:
                print(f"⚠️ Warning: Model failed to batch summarize tables: {str(le)}")
                
            import re
            for tbl in tables:
                desc = summary_content.get(tbl["filename"], "Raw table data indexed.")
                tbl_page = 1
                page_match = re.search(r'(?:page|p)[_-]?(\d+)', tbl["filename"], re.IGNORECASE)
                if page_match:
                    tbl_page = int(page_match.group(1))
                    
                db_chunks.append({
                    "document_id": document_id,
                    "content": f"[Table Summary - {tbl['filename']}]: {desc}\n\nRaw Table Data:\n{tbl['content']}",
                    "page_number": tbl_page,
                    "chunk_type": "table"
                })
            
        # Add text chunks with page tracking
        import re
        active_page = 1
        for chunk in text_chunks:
            markers = re.findall(r'\[PAGE_MARKER_(\d+)\]', chunk)
            if markers:
                active_page = int(markers[-1])
                
            cleaned_chunk = re.sub(r'\[PAGE_MARKER_\d+\]', '', chunk).strip()
            if not cleaned_chunk:
                continue
                
            db_chunks.append({
                "document_id": document_id,
                "content": cleaned_chunk,
                "page_number": active_page,
                "chunk_type": "text"
            })
            
        # 5. Generate embeddings dynamically using user's keys
        all_texts = [c["content"] for c in db_chunks]
        api_keys = {"gemini": gemini_api_key}
        provider = "google"
        if jina_api_key:
            api_keys["jina"] = jina_api_key
            provider = "jina"
            
        chunk_embeddings = EmbeddingsService.get_embeddings(
            texts=all_texts,
            api_keys=api_keys,
            provider=provider
        )
        
        # Add embeddings to chunk objects
        for chunk_obj, embedding in zip(db_chunks, chunk_embeddings):
            chunk_obj["embedding"] = embedding
            
        # 6. Insert chunks into DB
        db_service.insert_chunks(db_chunks)
        print(f"Successfully indexed document: {filename} ({document_id})")

    except Exception as e:
        print(f"Error parsing and indexing document {filename}: {str(e)}")

class ChatRequest(BaseModel):
    query: str
    document_id: str
    chat_history: Optional[List[dict]] = []

def get_api_keys(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    x_openai_api_key: Optional[str] = Header(None, alias="X-OpenAI-API-Key"),
    x_anthropic_api_key: Optional[str] = Header(None, alias="X-Anthropic-API-Key"),
    x_jina_api_key: Optional[str] = Header(None, alias="X-Jina-API-Key"),
):
    """
    Dependency to extract API keys from headers.
    Falls back to backend environment variables if headers are missing or placeholders.
    """
    keys = {}
    
    print(f"DEBUG: Headers received: gemini={x_gemini_api_key}, openai={x_openai_api_key}, anthropic={x_anthropic_api_key}, jina={x_jina_api_key}")
    print(f"DEBUG: Env vars: gemini_api_key={os.getenv('gemini_api_key')}, GOOGLE_API_KEY={os.getenv('GOOGLE_API_KEY')}")

    # helper to clean and validate
    def clean_key(header_val: Optional[str], env_var_name: str) -> Optional[str]:
        val = header_val.strip() if header_val else ""
        # If header val is empty, a placeholder, or a dummy string, check environment variable
        if not val or val.startswith("●") or "dummy" in val.lower():
            val = os.getenv(env_var_name) or ""
        val = val.strip().strip('"').strip("'")
        return val if val else None

    gemini = clean_key(x_gemini_api_key, "GEMINI_API_KEY") or clean_key(x_gemini_api_key, "gemini_api_key") or os.getenv("GOOGLE_API_KEY")
    openai = clean_key(x_openai_api_key, "OPENAI_API_KEY")
    anthropic = clean_key(x_anthropic_api_key, "ANTHROPIC_API_KEY")
    jina = clean_key(x_jina_api_key, "JINA_API_KEY") or clean_key(x_jina_api_key, "jina_api_key")
    
    print(f"DEBUG: Resolved keys: gemini={'found' if gemini else 'missing'}, openai={'found' if openai else 'missing'}, anthropic={'found' if anthropic else 'missing'}, jina={'found' if jina else 'missing'}")

    if gemini:
        keys["gemini"] = gemini
    if openai:
        keys["openai"] = openai
    if anthropic:
        keys["anthropic"] = anthropic
    if jina:
        keys["jina"] = jina
        
    llm_keys_present = gemini or openai or anthropic
    if not llm_keys_present:
        raise HTTPException(
            status_code=401, 
            detail="No LLM API keys provided. Please supply at least one API key (Gemini, OpenAI, or Anthropic) in the headers or backend .env file."
        )
    return keys

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ResearchPaL Next-Gen Backend"}

@app.post("/api/parse")
async def parse_and_index_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    google_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    x_jina_api_key: Optional[str] = Header(None, alias="X-Jina-API-Key"),
    x_parser_mode: Optional[str] = Header("basic", alias="X-Parser-Mode"),
):
    """
    Receives a PDF, parses it using LlamaParse in the background, 
    and inserts chunks and embeddings into Supabase.
    """
    gemini_key = google_api_key.strip() if google_api_key else ""
    if not gemini_key or gemini_key.startswith("●") or "dummy" in gemini_key.lower():
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key") or os.getenv("GOOGLE_API_KEY") or ""
    gemini_key = gemini_key.strip().strip('"').strip("'")

    if not gemini_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is required for vision processing."
        )
        
    jina_key = x_jina_api_key.strip() if x_jina_api_key else ""
    if not jina_key or jina_key.startswith("●") or "dummy" in jina_key.lower():
        jina_key = os.getenv("JINA_API_KEY") or os.getenv("jina_api_key") or ""
    jina_key = jina_key.strip().strip('"').strip("'")
    if not jina_key:
        jina_key = None
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_content = await file.read()
    background_tasks.add_task(
        parse_and_index_task, 
        file_content, 
        file.filename, 
        gemini_key,
        jina_key,
        None,
        x_parser_mode
    )

    return {
        "message": "File upload successful. Parsing and embedding generation has been queued in the background.",
        "filename": file.filename
    }

class ParseUrlRequest(BaseModel):
    url: str
    filename: Optional[str] = "document.pdf"

@app.post("/api/parse_url")
async def parse_and_index_pdf_url(
    request: ParseUrlRequest,
    background_tasks: BackgroundTasks,
    google_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
    x_jina_api_key: Optional[str] = Header(None, alias="X-Jina-API-Key"),
    x_parser_mode: Optional[str] = Header("basic", alias="X-Parser-Mode"),
):
    """
    Downloads a PDF from a URL and parses/indexes it in the background.
    """
    gemini_key = google_api_key.strip() if google_api_key else ""
    if not gemini_key or gemini_key.startswith("●") or "dummy" in gemini_key.lower():
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key") or os.getenv("GOOGLE_API_KEY") or ""
    gemini_key = gemini_key.strip().strip('"').strip("'")

    if not gemini_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is required for vision processing."
        )
        
    jina_key = x_jina_api_key.strip() if x_jina_api_key else ""
    if not jina_key or jina_key.startswith("●") or "dummy" in jina_key.lower():
        jina_key = os.getenv("JINA_API_KEY") or os.getenv("jina_api_key") or ""
    jina_key = jina_key.strip().strip('"').strip("'")
    if not jina_key:
        jina_key = None
    
    target_url = request.url.strip()
    if "arxiv.org/abs/" in target_url:
        target_url = target_url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        # Ensure it has a pdf extension for filename if downloading a direct paper
        if request.filename == "document.pdf":
            paper_id = target_url.split("/")[-1]
            request.filename = f"arxiv_{paper_id}.pdf"
            
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(target_url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch PDF from the provided URL.")
        
        file_content = response.content
        if not file_content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400, 
                detail="Downloaded content is not a valid PDF file (missing %PDF header). Please check the URL."
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF from URL: {str(e)}")

    background_tasks.add_task(
        parse_and_index_task, 
        file_content, 
        request.filename, 
        gemini_key,
        jina_key,
        request.url,
        x_parser_mode
    )

    return {
        "message": "URL PDF fetched successfully. Parsing and embedding generation has been queued in the background.",
        "filename": request.filename
    }

@app.get("/api/chat/history")
async def get_chat_history(document_id: str):
    """
    Fetches the persisted chat history for a document.
    """
    return db_service.get_chat_history(document_id)

@app.delete("/api/chat/history")
async def delete_chat_history(document_id: str):
    """
    Deletes the persisted chat history for a document.
    """
    db_service.delete_chat_history(document_id)
    return {"message": "Chat history cleared successfully."}

@app.post("/api/chat")
async def chat_with_paper(
    request: ChatRequest,
    api_keys: dict = Depends(get_api_keys)
):
    """
    Streams chatbot agent responses using LangGraph and the user's provided API keys.
    """
    # Detect provider based on key supplied
    provider = "google"
    if "openai" in api_keys:
        provider = "openai"
    elif "anthropic" in api_keys:
        provider = "anthropic"

    # Save User message to db
    db_service.add_chat_message(request.document_id, "user", request.query)

    # Fetch database chat history
    db_history = db_service.get_chat_history(request.document_id)
    # The last message in db_history is the query we just inserted.
    # We pass the history prior to the current message to the agent state.
    history_to_use = request.chat_history
    if db_history and len(db_history) > 0:
        # Exclude the last message (which is the current query)
        history_to_use = db_history[:-1]

    async def response_streamer():
        # Setup initial state
        initial_state = {
            "query": request.query,
            "document_id": request.document_id,
            "api_keys": api_keys,
            "chat_history": history_to_use,
            "retrieved_documents": [],
            "final_response": "",
            "selected_provider": provider,
            "critic_feedback": None,
            "iteration_count": 0
        }
        
        full_response = []
        retrieved_documents = []
        try:
            async for event in agent_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event")
                if kind == "on_chain_end":
                    # Capture retrieved documents from any node that sets them (e.g. retrieve_context)
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "retrieved_documents" in output:
                        retrieved_documents = output["retrieved_documents"]
                elif kind == "on_chat_model_stream":
                    # Only yield from the final generate_response node
                    node = event.get("metadata", {}).get("langgraph_node")
                    if node == "generate_response":
                        content = event["data"]["chunk"].content
                        text = extract_text_content(content)
                        if text:
                            full_response.append(text)
                            yield text
            
            # Append sources metadata at the end of the text stream
            if retrieved_documents:
                import json
                sources_data = []
                for doc in retrieved_documents:
                    sources_data.append({
                        "id": doc.get("id"),
                        "document_id": doc.get("document_id"),
                        "paper_title": doc.get("paper_title"),
                        "chunk_type": doc.get("chunk_type"),
                        "content": doc.get("content"),
                        "page_number": doc.get("page_number"),
                        "image_path": doc.get("image_path")
                    })
                metadata_str = f"\n\n__SOURCES_METADATA__\n{json.dumps(sources_data)}"
                full_response.append(metadata_str)
                yield metadata_str
        except Exception as e:
            print(f"⚠️ Streaming error: {e}")
            yield f"❌ Error during response generation: {str(e)}"
            return
            
        # Save Assistant Response to db (including metadata for persistence)
        response_text = "".join(full_response)
        if response_text:
            db_service.add_chat_message(request.document_id, "assistant", response_text)
        
    return StreamingResponse(response_streamer(), media_type="text/plain")


@app.get("/api/papers/trending")
async def get_trending_papers(page: int = 1, items: int = 10):
    """
    Directly searches trending papers using the PWC Service.
    """
    return await pwc_service.get_trending_papers(page=page, items=items)

@app.get("/api/papers/search")
async def search_papers(query: str, page: int = 1, items: int = 10):
    """
    Directly searches papers by query using the PWC Service.
    """
    return await pwc_service.search_papers(query=query, page=page, items=items)

@app.get("/api/documents")
async def list_documents():
    """
    Fetches the list of all documents in the database.
    """
    try:
        response = db_service.client.table("documents").select("id, paper_title, paper_url, pdf_path, created_at").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

@app.get("/api/figures/download")
async def download_figure(path: str):
    """
    Redirects to the public URL of a figure in the Supabase storage bucket.
    """
    try:
        url_res = db_service.client.storage.from_("figures").get_public_url(path)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url_res)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Figure not found: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
