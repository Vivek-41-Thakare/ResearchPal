# Services Reference

> See [backend.md](backend.md) for how services are used, [ingestion.md](ingestion.md) for pipeline context.

## EmbeddingsService
**Source**: `services/embeddings_service.py`  
**Pattern**: Static methods only (no instance state)

```python
EmbeddingsService.get_embeddings(texts: List[str], api_keys: dict, provider: str) -> List[List[float]]
```

| Provider | Model | Dim | Notes |
|----------|-------|-----|-------|
| `"google"` | `models/gemini-embedding-2` | 768 | Uses LangChain `GoogleGenerativeAIEmbeddings` |
| `"openai"` | `text-embedding-3-small` | 768 | Uses LangChain `OpenAIEmbeddings` |
| `"jina"` | `jina-embeddings-v3` | 768 | Direct HTTP POST to `https://api.jina.ai/v1/embeddings` |

Jina task type: `"retrieval.passage"` (batch >1) or `"retrieval.query"` (single)

---

## ParseService
**Source**: `services/parse_service.py`  
**Pattern**: Async methods; reads Adobe creds from env at `__init__`

```python
async parse_pdf(pdf_bytes, filename, parser_mode) -> (plain_text, figures, tables)
```

- `plain_text`: full text with `[PAGE_MARKER_N]` tokens injected
- `figures`: `[{"filename": str, "content": bytes}]` (PNG files from Adobe)
- `tables`: `[{"filename": str, "content": str}]` (CSV text from Adobe)

Internally uses `run_in_threadpool` (FastAPI's async wrapper) for blocking PyMuPDF and Adobe calls.

Advanced mode requires: `parser_mode=="advanced"` AND creds set AND not containing "your-adobe" placeholder.

---

## PWCService
**Source**: `services/pwc_service.py`  
**Pattern**: Async methods; wraps ArXiv Atom XML API

### `get_trending_papers(page, items)`
```
URL: https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&start={offset}&max_results={items}
```

### `search_papers(query, page, items)`
```
URL: https://export.arxiv.org/api/query?search_query=all:term1+AND+all:term2&start={offset}&max_results={items}
```

### `_parse_arxiv_xml(xml_content)`
Parses Atom XML with namespaces (`atom:`, `opensearch:`, `arxiv:`):
- Extracts: id, title, abstract, authors, published date, PDF URL
- Date format: `"12 January 2023"` from ISO `"2023-01-12T..."`
- PDF URL: from `<link rel="related" title="pdf">` or constructs from abs URL
- GitHub detection: regex `r'https?://github\.com/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_/]+'` in abstract
- Framework detection: "pytorch" / "tensorflow" in abstract → `framework` field

Return schema:
```python
[{
    "paper": {"id", "arxiv_id", "url_pdf", "title", "abstract", "authors", "published"},
    "repository": {"url", "owner", "name", "stars": 0, "framework"} | None
}]
```

---

## SupabaseService
**Source**: `services/supabase_service.py`  
**Pattern**: Singleton instantiated at `main.py` module level; reads `SUPABASE_URL` / `SUPABASE_KEY` from env

### Public Methods

#### CRUD
```python
insert_document(paper_title, paper_url, pdf_path=None) -> str   # returns UUID
insert_chunks(chunks: List[Dict])                               # batch insert
upload_file(bucket_name, path_on_bucket, file_content, content_type) -> str  # public URL
```

#### Search
```python
similarity_search(document_ids, query_embedding, match_count) -> List[Dict]
hybrid_search(document_ids, query_text, query_embedding, match_count) -> List[Dict]
```

#### Chat Persistence
```python
get_or_create_session(document_id) -> session_uuid   # handles single + multi-doc
get_chat_history(document_id) -> List[Dict]
add_chat_message(document_id, role, content)
delete_chat_history(document_id)
```

### Multi-Doc Session Logic
```python
# document_id can be: str UUID, comma-separated UUIDs, or list
is_multi = "," in document_id or not document_id
# Multi-doc: session stored with document_id = NULL
# Query: .is_("document_id", "null") 
# Single-doc: .eq("document_id", document_id)
```

### Storage Upload
```python
client.storage.create_bucket(bucket_name)  # no-op if exists
client.storage.from_(bucket_name).upload(
    path=path_on_bucket,
    file=file_content,
    file_options={"content-type": content_type, "x-upsert": "true"}
)
```
