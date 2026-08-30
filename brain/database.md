# Database

> See [architecture.md](architecture.md) for system view, [search.md](search.md) for query functions.

## Source: `server_side/backend/schema.sql`

## Technology
- **Supabase** (hosted PostgreSQL) with **pgvector** extension
- **Storage Bucket**: `figures` (public, stores PNG files)
- **Python SDK**: `supabase-py >= 2.3.7`

## Tables

### `documents`
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | `gen_random_uuid()` |
| `paper_title` | text NOT NULL | LLM-extracted or filename-derived |
| `paper_url` | text NOT NULL | Source URL or filename |
| `pdf_path` | text | Optional storage path |
| `created_at` | timestamptz | UTC default |

### `document_chunks`
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `document_id` | uuid FK → documents.id | ON DELETE CASCADE |
| `content` | text NOT NULL | Chunk text (cleaned of PAGE_MARKERs for figures: `[Figure Summary - x]: desc`) |
| `page_number` | int | Extracted from PAGE_MARKER or filename |
| `chunk_type` | text NOT NULL | `'text'` / `'table'` / `'figure_summary'` |
| `image_path` | text | Supabase Storage path (figures only) |
| `embedding` | vector(768) | 768-dim float vector |
| `created_at` | timestamptz | UTC default |

### `chat_sessions`
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `document_id` | uuid FK → documents.id | NULL for multi-doc sessions |
| `title` | text NOT NULL | "Chat: {paper_title}" or "Library Synthesis Chat" |
| `created_at` | timestamptz | UTC default |

### `chat_messages`
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `session_id` | uuid FK → chat_sessions.id | ON DELETE CASCADE |
| `role` | text NOT NULL | `'user'` / `'assistant'` |
| `content` | text NOT NULL | Raw text including `__SOURCES_METADATA__` suffix for assistant |
| `created_at` | timestamptz | UTC default |

## SQL Functions

### `match_chunks_v2(query_embedding, match_threshold, match_count, filter_document_ids)`
Multi-document cosine similarity search.
```sql
-- Called with: match_threshold=0.05, match_count=15 (2× retrieval candidates)
SELECT id, document_id, content, page_number, chunk_type, image_path,
       1 - (embedding <=> query_embedding) AS similarity
FROM document_chunks
WHERE (filter_document_ids IS NULL OR document_id = ANY(filter_document_ids))
  AND 1 - (embedding <=> query_embedding) > match_threshold
ORDER BY embedding <=> query_embedding
LIMIT match_count;
```

### `match_chunks()` (legacy, single-doc)
Older version with `filter_document_id uuid` (singular). Still in schema but superseded by v2.

## Storage: `figures` Bucket

- Path pattern: `documents/{document_id}/figures/{filename}.png`
- Upsert on upload (`x-upsert: true`)
- Public URL: `client.storage.from_("figures").get_public_url(path)`
- `/api/figures/download?path=...` → RedirectResponse to public URL

## SupabaseService Key Operations

| Method | DB Action |
|--------|-----------|
| `insert_document()` | INSERT into documents, return UUID |
| `insert_chunks()` | Batch INSERT into document_chunks |
| `similarity_search()` | RPC `match_chunks_v2` |
| `hybrid_search()` | vector search + keyword frequency + RRF merge |
| `upload_file()` | Storage upload (auto-creates bucket) |
| `get_or_create_session()` | SELECT/INSERT chat_sessions |
| `get_chat_history()` | SELECT chat_messages ORDER BY created_at |
| `add_chat_message()` | INSERT into chat_messages |
| `delete_chat_history()` | DELETE chat_sessions (cascades to messages) |

## Multi-Document Session Logic
- `document_id` stored as `NULL` in `chat_sessions` for multi-doc
- Queries check `is_("document_id", "null")` for multi-doc sessions
- `delete_chat_history()` similarly matches on null for multi-doc

## Setup
```bash
# Run schema.sql in Supabase SQL Editor
# Creates: extension, tables, match_chunks, match_chunks_v2
# Enable pgvector: already in schema (CREATE EXTENSION IF NOT EXISTS vector)
```
