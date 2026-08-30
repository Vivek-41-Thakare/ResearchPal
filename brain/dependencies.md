# Dependencies

> See [backend.md](backend.md) and [frontend.md](frontend.md) for usage context.

## Backend (`server_side/backend/requirements.txt`)

| Package | Version | Role |
|---------|---------|------|
| `fastapi` | ≥0.110.0 | HTTP framework, routing, dependency injection |
| `uvicorn` | ≥0.28.0 | ASGI server |
| `pydantic` | ≥2.6.0 | Request/response model validation |
| `langchain` | ≥0.1.12 | Text splitter, message types |
| `langchain-google-genai` | ≥1.0.1 | ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings |
| `langchain-openai` | ≥0.0.8 | ChatOpenAI, OpenAIEmbeddings |
| `langchain-anthropic` | ≥0.1.4 | ChatAnthropic |
| `langgraph` | ≥0.0.26 | StateGraph, multi-agent pipeline |
| `supabase` | ≥2.3.7 | PostgreSQL + pgvector + Storage client |
| `pdfservices-sdk` | ≥4.1.0 | Adobe PDF Extract API (figures/tables) |
| `PyMuPDF` | ≥1.25.1 | Fast PDF text extraction (`pymupdf`) |
| `python-dotenv` | ≥1.0.1 | `.env` loading |
| `httpx` | ≥0.27.0 | Async HTTP (ArXiv API, PDF downloads) |
| `python-multipart` | ≥0.0.9 | Form file uploads |
| `pandas` | ≥2.2.1 | CSV table processing (evals) |
| `pyarrow` | ≥15.0.0 | Fast parquet/data support for pandas |
| `py7zr` | ≥0.22.0 | 7-zip archive support |
| `jinja2` | ≥3.1.3 | Template rendering (FastAPI dependency) |

Notable **not** in requirements.txt but used:
- `langchain-groq` — used in `main.py` for Groq fallback (`from langchain_groq import ChatGroq`)
- `requests` — used in `embeddings_service.py` for Jina HTTP calls

## Frontend (`server_side/frontend/package.json`)

| Package | Version | Role |
|---------|---------|------|
| `react` | ^19.2.7 | UI framework |
| `react-dom` | ^19.2.7 | DOM rendering |
| `lucide-react` | ^1.23.0 | Icon library (BookOpen, Search, Upload, etc.) |
| `vite` | ^8.1.1 | Dev server + build tool |
| `@vitejs/plugin-react` | ^6.0.3 | Vite React JSX transform |
| `oxlint` | ^1.71.0 | Fast JS/TS linter |

No CSS preprocessor (vanilla CSS only). No routing library. No state management library. No markdown library (custom renderer).

## External APIs (Runtime Dependencies)

| Service | URL | Used For |
|---------|-----|---------|
| Google Gemini | `generativelanguage.googleapis.com` | Chat LLM + vision + embeddings |
| OpenAI | `api.openai.com` | Chat LLM + embeddings (optional) |
| Anthropic | `api.anthropic.com` | Chat LLM (optional) |
| Jina AI | `api.jina.ai` | Embeddings + reranking (optional) |
| Groq | `api.groq.com` | Vision fallback on Gemini rate limit |
| ArXiv | `export.arxiv.org/api/query` | Paper discovery + search |
| Adobe PDF Services | `pdfservices.adobe.io` | Advanced PDF parsing (optional) |
| Supabase | `*.supabase.co` | DB + storage |

## Infrastructure
- **Database**: Supabase (PostgreSQL 15 + pgvector)
- **Backend Runtime**: Python 3.10+, uvicorn ASGI
- **Frontend Runtime**: Node.js v16+, served by Vite or any static server
- **No Docker/CI/CD config** in repository
