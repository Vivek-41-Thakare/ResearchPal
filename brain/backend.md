# Backend

> See [architecture.md](architecture.md) for system view, [api.md](api.md) for endpoint specs, [agent.md](agent.md) for LangGraph details.

## Entry Point: `server_side/backend/main.py`

**FastAPI app** with CORS, all routes, background task runner, and service instantiation.

### Services Instantiated at Module Level
```python
db_service   = SupabaseService()   # singleton, reads SUPABASE_URL/KEY from env
parse_service = ParseService()     # reads PDF_SERVICES_CLIENT_ID/SECRET from env
pwc_service   = PWCService()       # stateless, uses arxiv.org
```

### API Key Dependency: `get_api_keys()`
- Reads `X-Gemini-API-Key`, `X-OpenAI-API-Key`, `X-Anthropic-API-Key`, `X-Jina-API-Key` headers
- Falls back to env vars if header is empty/placeholder (`●`-prefixed or `dummy`)
- Returns `dict` keyed by `"gemini"/"openai"/"anthropic"/"jina"`
- Raises `HTTP 401` if no LLM key is present

### Provider Selection Logic (in `POST /api/chat`)
```python
provider = "google"            # default
if "openai" in api_keys:  provider = "openai"
elif "anthropic" in api_keys: provider = "anthropic"
# Jina key → used for embeddings/reranking, not as chat provider
```

## Background Task: `parse_and_index_task()`

Long-running async function scheduled via `BackgroundTasks.add_task()`.

```
Steps:
1. parse_service.parse_pdf(bytes, filename, parser_mode)
   → returns (plain_text:str, figures:list[{filename, content}], tables:list[{filename, content}])
2. Title extraction: Gemini LLM on first 1500 chars → fallback to filename
3. db_service.insert_document() → document UUID
4. semantic_chunk_text() → text_chunks list
5. Figure processing:
   a. Upload PNG to Supabase Storage: documents/{doc_id}/figures/{filename}
   b. Batch vision summarize via Gemini (base64 multipart) → JSON {summaries:[]}
   c. Retry 3x with exponential backoff; fallback to Groq llama-3.2-11b-vision on 429
6. Table processing: Batch summarize CSV via LLM → JSON {summaries:[]}
7. Text chunks: strip [PAGE_MARKER_N] markers; track active_page
8. embed all chunks via EmbeddingsService
9. db_service.insert_chunks(db_chunks)
```

### Semantic Chunking Algorithm (`semantic_chunk_text()`)
```python
sentences = re.split(r'(?<=[.!?])\s+', text)
# embed sentences in batches of 16
for each consecutive pair:
    sim = cosine_similarity(embed[i-1], embed[i])
    if sim < 0.75 and len(current_chunk) >= 400:
        flush chunk
    elif len(current_chunk) + len(sentence) > 3000:
        flush chunk
    else:
        append to current_chunk
```
- min_chunk_size=400 chars, max_chunk_size=3000 chars, split threshold=0.75

### Chat Streaming (`POST /api/chat`)
```python
async def response_streamer():
    async for event in agent_graph.astream_events(state, version="v2"):
        if event == "on_chain_end" and "retrieved_documents" in output:
            captured_docs = output["retrieved_documents"]
        elif event == "on_chat_model_stream" and node == "generate_response":
            yield text_chunk           # stream to client
    # After stream ends:
    yield "__SOURCES_METADATA__\n" + json.dumps(sources_data)
    db_service.add_chat_message(doc_id, "assistant", full_response)
```

### Vision LLM Retry Strategy
```python
for attempt in 3:
    try: Gemini vision call
    except 429/RESOURCE_EXHAUSTED:
        if groq_key: break → Groq fallback
        else: raise immediately (no delay)
    except other: exponential backoff (4s, 8s, 16s)
# Groq fallback models:
#   image=True  → llama-3.2-11b-vision-preview
#   image=False → llama-3.1-8b-instant
```

## Startup / Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
# Or: python main.py  (uses uvicorn.run internally)
```

## Environment Variables
| Var | Required | Purpose |
|-----|----------|---------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Service role key |
| `GEMINI_API_KEY` | Yes (for indexing) | Vision + title extraction |
| `JINA_API_KEY` | Recommended | Jina embeddings + reranker |
| `PDF_SERVICES_CLIENT_ID` | Optional | Adobe advanced parser |
| `PDF_SERVICES_CLIENT_SECRET` | Optional | Adobe advanced parser |
| `GROQ_API_KEY` | Optional | Vision fallback LLM |
| `FRONTEND_URL` | Optional | CORS allowlist |
| `GOOGLE_API_KEY` | Alias | Also checked for Gemini |
