# Architecture

> See [brain.md](brain.md) for index. See [backend.md](backend.md), [frontend.md](frontend.md), [agent.md](agent.md), [database.md](database.md).

## System Topology

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (React 19 + Vite SPA)  :5173                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Discovery│  │  Assistant   │  │  Settings Sidebar    │  │
│  │  Tab     │  │  Tab (Chat)  │  │  (API Keys persist   │  │
│  │ ArXiv    │  │  Streaming   │  │   to localStorage)   │  │
│  │ Search   │  │  Citations   │  │                      │  │
│  └────┬─────┘  └──────┬───────┘  └──────────────────────┘  │
└───────┼───────────────┼─────────────────────────────────────┘
        │               │  HTTP + SSE (text/plain streaming)
        ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend  :8000                                     │
│                                                             │
│  /api/parse          → BackgroundTask: parse_and_index_task │
│  /api/parse_url      → BackgroundTask: parse_and_index_task │
│  /api/chat           → StreamingResponse via LangGraph      │
│  /api/papers/*       → PWCService (ArXiv API proxy)        │
│  /api/documents      → Supabase direct query                │
│  /api/figures/*      → Supabase Storage redirect            │
│  /api/chat/history   → SupabaseService chat ops             │
│                                                             │
│  Services:                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ ParseService │ │EmbeddingsService│ │ PWCService  │       │
│  │ (PyMuPDF +  │ │(Jina/Gemini/ │ │ (ArXiv XML   │        │
│  │  Adobe PDF) │ │ OpenAI)      │ │  parser)     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  LangGraph Multi-Agent:                                     │
│  intent_router → [retrieve_context → rerank_context] →     │
│                   generate_response                         │
└─────────────────────────┬───────────────────────────────────┘
                          │  supabase-py SDK
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Supabase (PostgreSQL + pgvector + Storage)                 │
│                                                             │
│  Tables: documents, document_chunks, chat_sessions,         │
│          chat_messages                                      │
│  Functions: match_chunks_v2() (cosine similarity RPC)       │
│  Storage: figures/ bucket (PNG files per document)          │
└─────────────────────────────────────────────────────────────┘
```

## Component Relationships

| Component | Depends On | Provides To |
|-----------|-----------|-------------|
| `App.jsx` | FastAPI REST + SSE | User UI |
| `main.py` | All Services + LangGraph | Frontend |
| `agent.py` | SupabaseService, EmbeddingsService, LLM SDKs | main.py |
| `supabase_service.py` | supabase-py | agent.py, main.py |
| `parse_service.py` | PyMuPDF, Adobe SDK | main.py (bg task) |
| `embeddings_service.py` | Jina REST, LangChain Google/OpenAI | main.py, agent.py |
| `pwc_service.py` | httpx + ArXiv Atom XML | main.py |

## Data Flow: Chat Request

```
User types message
  → POST /api/chat {query, document_id, chat_history}
    API keys extracted from headers (X-Gemini-API-Key etc.)
    → db_service.add_chat_message(user)
    → agent_graph.astream_events(initial_state)
      → intent_router node (LLM classifies intent)
      → [if not greeting] retrieve_context node
           EmbeddingsService.get_embeddings(query)
           supabase_service.hybrid_search()  ← vector + keyword + RRF
      → rerank_context node (Jina API or top-5 fallback)
      → generate_response node (LLM streams answer w/ inline citations)
    → yield text chunks to client
    → append __SOURCES_METADATA__ JSON trailer
    → db_service.add_chat_message(assistant, full_response)
```

## Data Flow: PDF Ingestion

```
User uploads PDF / clicks Analyze on ArXiv card
  → POST /api/parse or /api/parse_url
    [URL path] arxiv.org/abs/ → arxiv.org/pdf/ rewrite
    validate %PDF magic bytes
    → BackgroundTask: parse_and_index_task()
      1. parse_service.parse_pdf() → (plain_text, figures[], tables[])
      2. Gemini LLM extracts paper title from first 1500 chars
      3. db_service.insert_document() → UUID
      4. semantic_chunk_text() → text chunks (cosine 0.75 split)
      5. [if figures] Vision LLM batch summarizes → upload to Storage
      6. [if tables] LLM batch summarizes CSV data
      7. EmbeddingsService.get_embeddings(all_chunks)
      8. db_service.insert_chunks(db_chunks)
```
