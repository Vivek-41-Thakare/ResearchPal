# Ingestion Pipeline

> See [backend.md](backend.md) for orchestration, [services.md](services.md) for service details, [database.md](database.md) for storage.

## Overview

```
PDF bytes (upload or URL download)
        │
        ▼
    ParseService.parse_pdf(bytes, filename, mode)
        │
        ├── Always: PyMuPDF text extraction
        │           → "[PAGE_MARKER_1]\ntext...\n[PAGE_MARKER_2]\ntext..."
        │
        └── If mode=="advanced" AND Adobe creds configured:
                Adobe PDF Extract API (cloud job)
                → ZIP: figures/*.png + tables/*.csv
        │
        ▼
    Gemini LLM: Extract paper title from first 1500 chars
    Fallback: filename.replace(".pdf","").replace("_"," ")
        │
        ▼
    db_service.insert_document(title, url) → document_id (UUID)
        │
        ├── Text chunks: semantic_chunk_text(plain_text)
        │       → list of cleaned strings (PAGE_MARKERs stripped)
        │
        ├── Figures (if any):
        │       Upload each PNG → Supabase Storage figures/ bucket
        │       Batch Vision LLM summarize (Gemini → Groq fallback)
        │       → [{filename, summary}] per figure
        │
        └── Tables (if any):
                Batch LLM summarize CSV data
                → [{filename, summary}] per table
        │
        ▼
    Build db_chunks list:
        - figure_summary chunks: {content: "[Figure Summary - x]: desc", page, chunk_type, image_path}
        - table chunks:          {content: "[Table Summary - x]: desc\n\nRaw Table:\n...", page, chunk_type}
        - text chunks:           {content: cleaned_text, page_number: active_page, chunk_type: "text"}
        │
        ▼
    EmbeddingsService.get_embeddings(all_chunk_texts)
    Provider: "jina" if jina_key else "google"
        │
        ▼
    db_service.insert_chunks(db_chunks_with_embeddings)
```

## ParseService (`services/parse_service.py`)

### Basic Mode (Always Active)
```python
pymupdf.open(temp_pdf_path)
for idx, page in enumerate(doc):
    marked_pages.append(f"\n[PAGE_MARKER_{idx+1}]\n{page.get_text()}")
return "".join(marked_pages)
```

### Advanced Mode (Adobe PDF Services)
Triggers when: `parser_mode=="advanced"` AND `client_id`/`client_secret` are set and not placeholder.
```python
credentials = ServicePrincipalCredentials(client_id, client_secret)
pdf_services = PDFServices(credentials)
input_asset = pdf_services.upload(file_stream, PDFServicesMediaType.PDF)
params = ExtractPDFParams(
    elements_to_extract=[TEXT, TABLES],
    elements_to_extract_renditions=[TABLES, FIGURES],
    table_structure_type=TableStructureType.CSV
)
job = ExtractPDFJob(input_asset, params)
location = pdf_services.submit(job)
result = pdf_services.get_job_result(location, ExtractPDFResult)
# → ZIP containing: tables/*.csv, figures/*.png
```
On failure → gracefully falls back to text-only output.

## Semantic Chunking Algorithm

Source: `semantic_chunk_text()` in `main.py`

```
Parameters:
  max_chunk_size = 3000 chars
  min_chunk_size = 400 chars
  split_threshold = 0.75 cosine similarity

Algorithm:
1. Split text on sentence boundaries: re.split(r'(?<=[.!?])\s+', text)
2. Embed sentences in batches of 16 using EmbeddingsService
3. Iterate sentences:
   a. If current_chunk is empty → start new chunk
   b. Compute cosine_similarity(embed[i-1], embed[i])
   c. SPLIT if: (sim < 0.75 AND len(current) >= 400) OR (len(current) + len(sentence) > 3000)
   d. APPEND if: similarity high AND within size limit
4. Flush remaining sentences as final chunk
```

Cosine similarity computed inline (no library):
```python
dot = sum(a*b for a,b in zip(v1,v2))
mag1 = sum(a*a for a in v1)**0.5
mag2 = sum(b*b for b in v2)**0.5
sim = dot / (mag1 * mag2)
```

## Page Number Tracking
- Text chunks: tracks `[PAGE_MARKER_N]` tokens within chunk; uses last marker found
- Figure chunks: regex `r'(?:page|p)[_-]?(\d+)'` on filename; defaults to page 1
- Table chunks: same filename regex as figures

## Vision Summarization (Batch)

### Figures
```python
# Single multipart message with ALL figures base64-encoded
content_list = [
    {"type": "text", "text": FIGURE_BATCH_PROMPT},
    {"type": "text",  "text": f"Filename: {img['filename']}"},
    {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
    # ... repeated per figure
]
prompt_msg = HumanMessage(content=content_list)
# Response format: {"summaries": [{"filename": "...", "summary": "..."}]}
```

### Tables
```python
# All CSVs concatenated in single text prompt
table_prompt = BATCH_PROMPT + "\n".join(f"--- Filename: {f} ---\n{csv}" for each table)
# Response format: {"summaries": [{"filename": "...", "summary": "..."}]}
```

## Content Type in DB
| Source | `chunk_type` | `content` prefix | `image_path` |
|--------|-------------|-----------------|-------------|
| PyMuPDF text | `text` | raw text | null |
| Adobe figures | `figure_summary` | `[Figure Summary - filename]: desc` | Storage path |
| Adobe tables | `table` | `[Table Summary - filename]: desc\n\nRaw Table Data:\n{csv}` | null |

## Fallback Chain
```
Basic mode always produces text (PyMuPDF never fails)
Advanced mode:
  Adobe fails → log warning, return text-only (figures=[], tables=[])
  Vision model 429 → Groq vision fallback (llama-3.2-11b-vision-preview)
  Vision complete fail → default desc "Figure image stored in database."
  Tables complete fail → default desc "Raw table data indexed."
Gemini title extraction fails → filename used as title
```
