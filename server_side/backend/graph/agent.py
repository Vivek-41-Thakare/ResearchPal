import os
from typing import TypedDict, List, Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, START, END

from services.supabase_service import SupabaseService
from services.embeddings_service import EmbeddingsService

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

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

# Define LangGraph State
class AgentState(TypedDict):
    query: str
    document_id: str
    api_keys: Dict[str, str]
    chat_history: List[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    final_response: str
    selected_provider: Literal["google", "openai", "anthropic"]
    critic_feedback: Optional[str] # compatibility
    iteration_count: int # compatibility
    intent: Optional[str]

def get_llm(provider: str, api_keys: Dict[str, str]):
    """
    Helper to instantiate LLM based on user's API Key.
    """
    if provider == "google":
        return ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite", 
            google_api_key=api_keys["gemini"]
        )
    elif provider == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini", 
            openai_api_key=api_keys["openai"]
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022", 
            anthropic_api_key=api_keys["anthropic"]
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

# --- Node 1: Intent Router Agent ---
def intent_router(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user's query and classifies it into one of four routes:
    - greetings_or_general (chit-chat, greetings, questions not requiring document lookup)
    - visual_tabular (lookup metrics, values, labels on figures or tables)
    - global_synthesis (summaries, conclusion, structure, overall methodology)
    - document_search (dense text retrieval)
    """
    print("--- RUNNING INTENT ROUTER ---")
    query = state["query"]
    api_keys = state["api_keys"]
    provider = state["selected_provider"]
    
    system_prompt = (
        "You are the Intent Router for an AI academic research paper assistant.\n"
        "Your task is to classify the user's query into one of these four categories:\n"
        "- greetings_or_general: Greetings, small talk, general questions not requiring facts from the document.\n"
        "- visual_tabular: Questions asking specifically about tables, metrics, figures, graphs, or charts.\n"
        "- global_synthesis: Questions asking for general summaries, structure, limitations, or the overall contribution of the paper.\n"
        "- document_search: Specific text-based lookups, equations, baseline comparison text, algorithms, or paragraph-level details.\n\n"
        "Respond ONLY with one of the four intent strings: 'greetings_or_general', 'visual_tabular', 'global_synthesis', or 'document_search'. Do not return any other text."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    try:
        llm = get_llm(provider, api_keys)
        response = llm.invoke(messages)
        intent = extract_text_content(response.content).strip().strip("'").strip('"').lower()
        
        valid_intents = ["greetings_or_general", "visual_tabular", "global_synthesis", "document_search"]
        matched = "document_search"
        for vi in valid_intents:
            if vi in intent:
                matched = vi
                break
        print(f"Matched Intent: {matched}")
        return {"intent": matched}
    except Exception as e:
        print(f"⚠️ Intent router failed: {str(e)}. Defaulting to document_search.")
        return {"intent": "document_search"}

# --- Node 2: Retrieve Context Node ---
def retrieve_context(state: AgentState) -> Dict[str, Any]:
    """
    Runs dynamic vector & keyword search (Hybrid Search) based on Router intent classification.
    """
    print("--- RUNNING RETRIEVE CONTEXT ---")
    query = state["query"]
    document_id = state["document_id"]
    api_keys = state["api_keys"]
    provider = state["selected_provider"]
    intent = state.get("intent", "document_search")
    
    # Greetings or general queries do not need document retrieval
    if intent == "greetings_or_general":
        return {"retrieved_documents": []}
        
    embed_provider = "jina" if "jina" in api_keys and api_keys["jina"] else provider
    query_embeddings = EmbeddingsService.get_embeddings(
        texts=[query], 
        api_keys=api_keys, 
        provider=embed_provider
    )
    query_embedding = query_embeddings[0]
    
    db_service = SupabaseService()
    # Support multiple document IDs if passed as a comma-separated string
    doc_ids = [d.strip() for d in document_id.split(",") if d.strip()] if document_id else []
    matches = db_service.hybrid_search(
        document_ids=doc_ids,
        query_text=query,
        query_embedding=query_embedding,
        match_count=15
    )
    
    # Map document_id to paper_title for citation clarity
    try:
        docs_res = db_service.client.table("documents").select("id, paper_title").execute()
        doc_map = {d["id"]: d["paper_title"] for d in (docs_res.data or [])}
    except Exception as e:
        print(f"⚠️ Error mapping document titles: {e}")
        doc_map = {}

    for match in matches:
        match["paper_title"] = doc_map.get(match.get("document_id"), "Unknown Document")
    
    # Boost matches based on query intent
    if intent == "visual_tabular":
        # Prioritize figure summaries and tables
        visual = [m for m in matches if m.get("chunk_type") in ["figure_summary", "table"]]
        text = [m for m in matches if m.get("chunk_type") == "text"]
        matches = visual + text
    elif intent == "global_synthesis":
        # Prioritize summary sections, abstracts, conclusions, and figure summaries
        global_chunks = []
        other_chunks = []
        for m in matches:
            content = m.get("content", "").lower()
            if m.get("chunk_type") in ["figure_summary", "table"] or "abstract" in content or "conclusion" in content or "summary" in content:
                global_chunks.append(m)
            else:
                other_chunks.append(m)
        matches = global_chunks + other_chunks
        
    return {"retrieved_documents": matches}

# --- Node 3: Jina Rerank Node ---
def rerank_context(state: AgentState) -> Dict[str, Any]:
    """
    Applies Jina Reranker to filter context down to the top 5 most highly relevant chunks.
    """
    print("--- RUNNING RERANK CONTEXT ---")
    query = state["query"]
    retrieved_docs = state.get("retrieved_documents", [])
    api_keys = state["api_keys"]
    jina_key = api_keys.get("jina")
    
    if not retrieved_docs:
        return {"retrieved_documents": []}
        
    # Check if user has Jina Key configured
    if jina_key:
        print("ℹ️ Using Jina Reranker...")
        import httpx
        url = "https://api.jina.ai/v1/rerank"
        headers = {
          "Content-Type": "application/json",
          "Authorization": f"Bearer {jina_key}"
        }
        
        doc_texts = [doc.get("content", "") for doc in retrieved_docs]
        data = {
          "model": "jina-reranker-v2-base-multilingual",
          "query": query,
          "documents": doc_texts,
          "top_n": 5
        }
        
        try:
            response = httpx.post(url, headers=headers, json=data, timeout=10.0)
            if response.status_code == 200:
                res_json = response.json()
                ranked_docs = []
                for item in res_json.get("results", []):
                    idx = item["index"]
                    doc = retrieved_docs[idx]
                    doc["relevance_score"] = item["relevance_score"]
                    ranked_docs.append(doc)
                print(f"✅ Jina Reranker successful: selected {len(ranked_docs)} chunks.")
                return {"retrieved_documents": ranked_docs}
            else:
                print(f"⚠️ Jina Reranker API error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"⚠️ Exception during Jina Reranking: {str(e)}")
            
    # Default fallback: keep top 5
    print("ℹ_ Fallback: keeping top 5 default ranked chunks.")
    return {"retrieved_documents": retrieved_docs[:5]}

# --- Node 4: Generate Response Node ---
def generate_response(state: AgentState) -> Dict[str, Any]:
    """
    Drafts the final assistant response with inline citation attribution.
    """
    print("--- RUNNING GENERATE RESPONSE ---")
    query = state["query"]
    retrieved_docs = state.get("retrieved_documents", [])
    chat_history = state["chat_history"]
    api_keys = state["api_keys"]
    provider = state["selected_provider"]
    intent = state.get("intent", "document_search")
    
    if intent == "greetings_or_general":
        system_prompt = (
            "You are a helpful, professional AI academic research paper assistant.\n"
            "Answer the user's greeting or general question directly, warmly, and concisely.\n"
            "Do not cite any papers or page numbers since this is a general query."
        )
    else:
        context_str = ""
        for idx, doc in enumerate(retrieved_docs):
            page_num = doc.get("page_number", "Unknown")
            content_type = doc.get("chunk_type", "text")
            image_path = doc.get("image_path", "")
            
            # Format clean citations
            paper_title = doc.get("paper_title", "Document")
            short_title = paper_title[:30] + "..." if len(paper_title) > 33 else paper_title
            
            citation = f"{short_title} | Page {page_num}"
            if content_type == "figure_summary":
                citation = f"{short_title} | Figure: {os.path.basename(image_path) if image_path else 'Image'} | Page {page_num}"
            elif content_type == "table":
                citation = f"{short_title} | Table | Page {page_num}"
                
            context_str += f"\n--- Source {idx+1} ({citation}) ---\n{doc.get('content')}\n"
            
        system_prompt = (
            "You are a professional academic research paper Q&A assistant.\n"
            "Your task is to answer the user's question accurately using ONLY the retrieved context below.\n"
            "Always cite your sources inline using their corresponding Source number (e.g. [Source 1], [Source 2]) when stating facts based on them. Do not use other citation formats in your text response.\n"
            "If the answer cannot be found in the context, state that you do not know based on the document.\n\n"
            f"RETRIEVED CONTEXT:\n{context_str}"
        )
        
    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content")))
    messages.append(HumanMessage(content=query))
    
    llm = get_llm(provider, api_keys)
    response = llm.invoke(messages)
    
    return {
        "final_response": extract_text_content(response.content),
        "critic_feedback": None, # compatibility
        "iteration_count": state.get("iteration_count", 0) + 1 # compatibility
    }

# --- Router Edges ---
def route_after_intent(state: AgentState) -> Literal["retrieve_context", "generate_response"]:
    if state["intent"] == "greetings_or_general":
        return "generate_response"
    return "retrieve_context"

# Compile Multi-Agent Graph
workflow = StateGraph(AgentState)

workflow.add_node("intent_router", intent_router)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("rerank_context", rerank_context)
workflow.add_node("generate_response", generate_response)

workflow.add_edge(START, "intent_router")

workflow.add_conditional_edges(
    "intent_router",
    route_after_intent,
    {
        "retrieve_context": "retrieve_context",
        "generate_response": "generate_response"
    }
)

workflow.add_edge("retrieve_context", "rerank_context")
workflow.add_edge("rerank_context", "generate_response")
workflow.add_edge("generate_response", END)

agent_graph = workflow.compile()
