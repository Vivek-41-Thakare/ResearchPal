# ResearchPaL — Brain (Master Index)

> AI-optimized knowledge base. Cross-reference files; do not duplicate. Last sync: 2026-07-26.

## What Is ResearchPaL?
Multi-agent academic RAG assistant. Users upload/fetch research PDFs → system parses, chunks, embeds, and indexes them → users chat using a 4-node LangGraph pipeline with hybrid retrieval, Jina reranking, and streaming responses citing exact pages.

## Knowledge Map

| File | Contents |
|------|----------|
| [architecture.md](architecture.md) | System topology, component relationships, data flow diagram |
| [backend.md](backend.md) | FastAPI endpoints, background tasks, services, request lifecycle |
| [agent.md](agent.md) | LangGraph 4-node multi-agent graph, state machine, routing logic |
| [database.md](database.md) | Supabase schema, tables, SQL functions, storage buckets |
| [frontend.md](frontend.md) | React SPA: state, components, streaming, citation UX |
| [ingestion.md](ingestion.md) | PDF parsing pipeline, semantic chunking, embedding, indexing |
| [search.md](search.md) | Hybrid search algorithm, RRF fusion, Jina reranker |
| [services.md](services.md) | EmbeddingsService, ParseService, PWCService, SupabaseService |
| [api.md](api.md) | All HTTP endpoints, request/response schemas, headers |
| [auth_security.md](auth_security.md) | API key handling, CORS, localStorage, security model |
| [evals.md](evals.md) | Evaluation suite metrics, benchmark results, scripts |
| [dependencies.md](dependencies.md) | Backend/frontend dependency manifest |
| [directory_map.md](directory_map.md) | Full file tree with purpose annotations |
| [conventions.md](conventions.md) | Coding patterns, fallback strategies, error handling |

## Key Numbers
- Embedding dim: **768** (Jina v3 / Gemini Embedding-2 / OpenAI text-embedding-3-small)
- RRF constant: **k=60**
- Retrieval candidates: **15** → reranked to **5**
- Semantic chunk cosine split threshold: **0.75**
- Best eval F1: **0.556** (chunk=2500, k=7)
- Backend port: **8000** | Frontend port: **5173**

## Critical Paths
```
PDF Ingest:  POST /api/parse → BackgroundTask → parse_pdf() → semantic_chunk → embed → DB insert
URL Ingest:  POST /api/parse_url → arxiv URL rewrite → download → same as above
Chat:        POST /api/chat → agent_graph.astream_events() → SSE stream → __SOURCES_METADATA__ trailer
ArXiv:       GET /api/papers/trending|search → PWCService → arxiv.org Atom XML parse
```

## Provider Matrix
| Role | Google | OpenAI | Anthropic | Jina |
|------|--------|--------|-----------|------|
| Chat LLM | gemini-3.1-flash-lite | gpt-4o-mini | claude-3-5-sonnet-20241022 | — |
| Embeddings | gemini-embedding-2 (768d) | text-embedding-3-small | — | jina-embeddings-v3 (768d) |
| Reranker | — | — | — | jina-reranker-v2-base-multilingual |
| Vision | gemini-3.1-flash-lite | — | — | — |
| Vision Fallback | — | — | — | Groq llama-3.2-11b-vision-preview |
