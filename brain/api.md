# API Endpoints

> See [backend.md](backend.md) for implementation details, [auth_security.md](auth_security.md) for key handling.

## Base URL
`http://localhost:8000` (configurable via `API_BASE` in frontend)

## Request Headers (API Key Auth)
All endpoints that need LLM keys use dependency injection:
| Header | Provider | Notes |
|--------|----------|-------|
| `X-Gemini-API-Key` | Google | Required for indexing; fallback to `GEMINI_API_KEY` env |
| `X-OpenAI-API-Key` | OpenAI | Optional |
| `X-Anthropic-API-Key` | Anthropic | Optional |
| `X-Jina-API-Key` | Jina | Optional; improves embeddings+reranking |
| `X-Parser-Mode` | — | `"basic"` (default) or `"advanced"` |

---

## Endpoints

### `GET /health`
```
Response: {"status": "healthy", "service": "ResearchPaL Next-Gen Backend"}
```

---

### `POST /api/parse`
Upload PDF for parsing and indexing (background task).

**Request**: `multipart/form-data`
- `file`: PDF file (content-type must be `application/pdf`)
- Headers: `X-Gemini-API-Key`, `X-Jina-API-Key`, `X-Parser-Mode`

**Response** (immediate, 200):
```json
{"message": "File upload successful. Parsing... queued in the background.", "filename": "paper.pdf"}
```
**Errors**: 400 (no Gemini key, not PDF)

---

### `POST /api/parse_url`
Download and index a PDF from URL (background task).

**Request Body** (JSON):
```json
{"url": "https://arxiv.org/abs/2301.00001", "filename": "optional_name.pdf"}
```
- Headers: `X-Gemini-API-Key`, `X-Jina-API-Key`, `X-Parser-Mode`
- ArXiv URL rewrite: `/abs/` → `/pdf/` (automatic)
- Validates `%PDF` magic bytes before queuing

**Response** (immediate, 200):
```json
{"message": "URL PDF fetched successfully. Parsing... queued.", "filename": "arxiv_2301.00001.pdf"}
```
**Errors**: 400 (no Gemini key, invalid PDF), 500 (download failure)

---

### `POST /api/chat`
Stream chat response from LangGraph multi-agent pipeline.

**Request Body** (JSON):
```json
{
  "query": "What is the main contribution?",
  "document_id": "uuid1,uuid2",
  "chat_history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
```
- Headers: all `X-*-API-Key` headers
- `document_id` is comma-separated for multi-doc mode

**Response**: `StreamingResponse (text/plain)`
```
<streamed text chunks>
...
\n\n__SOURCES_METADATA__\n[{"id":"...","document_id":"...","paper_title":"...","chunk_type":"text|table|figure_summary","content":"...","page_number":3,"image_path":null}]
```
**Errors**: 401 (no LLM key)

---

### `GET /api/chat/history?document_id=<id>`
Fetch persisted chat history.

**Response**:
```json
[{"role": "user", "content": "...", "created_at": "..."}, ...]
```

---

### `DELETE /api/chat/history?document_id=<id>`
Clear chat session and all messages.

**Response**: `{"message": "Chat history cleared successfully."}`

---

### `GET /api/papers/trending?page=1&items=10`
Fetch latest AI/ML papers from ArXiv (cs.AI + cs.LG + cs.CV).

**Response**:
```json
{
  "results": [
    {
      "paper": {
        "id": "arxiv_id",
        "arxiv_id": "2301.00001",
        "url_pdf": "https://arxiv.org/pdf/2301.00001",
        "title": "...",
        "abstract": "...",
        "authors": ["Name1", "Name2"],
        "published": "12 January 2023"
      },
      "repository": {"url": "https://github.com/...", "owner": "...", "name": "...", "stars": 0, "framework": "PyTorch"}
    }
  ],
  "next_page": 2
}
```

---

### `GET /api/papers/search?query=<q>&page=1&items=10`
Search ArXiv by keyword query.

**Query Formation**: `all:term1+AND+all:term2+AND+...`

**Response**: Same schema as trending papers.

---

### `GET /api/documents`
List all indexed documents (ordered by created_at desc).

**Response**:
```json
[{"id": "uuid", "paper_title": "...", "paper_url": "...", "pdf_path": null, "created_at": "..."}]
```

---

### `GET /api/figures/download?path=<storage_path>`
Redirect to public Supabase Storage URL for a figure PNG.

**Response**: `RedirectResponse` to public Supabase URL  
**Error**: 404 if figure not found

---

## Missing Endpoints (TODO)
- `DELETE /api/documents` — mentioned in frontend code but not implemented in `main.py`
