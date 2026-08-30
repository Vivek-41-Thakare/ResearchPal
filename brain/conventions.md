# Coding Conventions & Patterns

> See [backend.md](backend.md), [agent.md](agent.md), [frontend.md](frontend.md) for implementation context.

## Backend Conventions

### Service Instantiation
- Services instantiated at **module level** in `main.py` (singletons):
  ```python
  db_service = SupabaseService()    # raises ValueError if env vars missing
  parse_service = ParseService()
  pwc_service = PWCService()
  ```
- `SupabaseService` created fresh inside agent nodes (not the singleton):
  ```python
  # In retrieve_context node:
  db_service = SupabaseService()   # ← new instance per invocation
  ```

### Async Pattern
- Route handlers are `async def`
- Long-running blocking operations wrapped in `run_in_threadpool()` (parse_service)
- Background tasks use `BackgroundTasks.add_task()` — non-blocking response
- LangGraph invoked via `agent_graph.astream_events()` (async generator)

### API Key Handling
- `clean_key()` always strips: whitespace, surrounding quotes, placeholder markers
- Multi-level fallback: header → env var (multiple names) → None
- Keys passed as `dict` through entire call chain; never global state

### Error Handling Pattern
```python
try:
    result = await some_operation()
except Exception as e:
    print(f"⚠️ Warning: {description}: {str(e)}")
    # Usually: graceful degradation (fallback value) not re-raise
    # Except: required operations (DB insert, PDF validation) → raise
```

### Content Extraction Helper
`extract_text_content(content)` used in both `main.py` and `agent.py`:
```python
# Handles: str, list of str/dict, or any object
# Extracts text parts from LangChain multimodal content
```

### JSON Cleaning
`clean_json_string(s)` strips markdown code fences from LLM JSON responses:
```python
if s.startswith("```"):
    # Remove first line (```json) and last line (```)
    s = "\n".join(lines[1:-1]).strip()
```

### Regex Patterns
| Pattern | Use |
|---------|-----|
| `r'(?<=[.!?])\s+'` | Sentence splitting for semantic chunking |
| `r'\[PAGE_MARKER_(\d+)\]'` | Page number extraction from text |
| `r'(?:page\|p)[_-]?(\d+)'` | Page extraction from filenames |
| `r'(https?://github\.com/[a-zA-Z0-9\-_]+/...)'` | GitHub URL extraction |

## Frontend Conventions

### State Updates
- Immutable updates: `setMessages(prev => [...prev, newMsg])`
- Streaming updates: mutate array copy: `updated[updated.length-1].content = text`
- `useEffect` dependencies kept minimal; localStorage sync on individual key change

### Component Structure
All UI in single `App()` function. Layout sections marked with comments:
```javascript
// ==========================================
// 1. STATE VARIABLES (React Local Memory)
// 2. EFFECTS (React Lifecycle Hooks)
// 3. API CALLS & COMPONENT LOGIC
// 4. HTML LAYOUT RENDER (JSX)
// ==========================================
```

### CSS Conventions
- CSS variables in `:root` for all colors, fonts, shadows, transitions
- Component classes in `App.css`; variables/animations in `index.css`
- Transition: `var(--transition)` = `all 0.2s cubic-bezier(0.4, 0, 0.2, 1)`
- No inline styles except for dynamic/computed values

### Event Propagation
`e.stopPropagation()` used where child elements (delete buttons, checkboxes) are inside clickable parent cards.

## Fallback Chain Pattern

The project consistently uses this fallback priority:
```
1. Try primary operation
2. On rate limit (429) → immediate switch to fallback provider
3. On other errors → exponential backoff (4s, 8s, 16s)
4. After max retries → propagate exception with clear message
5. Fallback providers: Gemini → Groq (vision), top-N → [:5] (reranking)
```

## Multi-Document ID Encoding
Documents IDs are comma-separated strings throughout the entire stack:
- Frontend: `selectedDocumentIds.join(",")`
- API body: `document_id: "uuid1,uuid2"`
- Backend parse: `[d.strip() for d in document_id.split(",")]`
- Supabase: `pg_array = f"{{{','.join(ids)}}}"` for PostgreSQL array literal

## Naming Conventions
| Scope | Style | Examples |
|-------|-------|---------|
| Python functions | `snake_case` | `semantic_chunk_text`, `get_api_keys` |
| Python classes | `PascalCase` | `SupabaseService`, `AgentState` |
| Python constants | `UPPER_SNAKE` | `CHUNK_SIZES`, `K_VALUES` |
| JS state variables | `camelCase` | `selectedProvider`, `isUploading` |
| JS handlers | `handle*` prefix | `handleSearch`, `handleSendMessage` |
| CSS classes | `kebab-case` | `app-container`, `citation-badge` |
| DB tables | `snake_case` | `document_chunks`, `chat_sessions` |
| DB columns | `snake_case` | `paper_title`, `chunk_type`, `image_path` |

## Chunk Type Values (DB Constraint by Convention)
| Value | Source |
|-------|--------|
| `"text"` | PyMuPDF text chunks |
| `"table"` | Adobe-extracted tables |
| `"figure_summary"` | Adobe-extracted figures (vision summarized) |

## Page Marker Convention
PyMuPDF injects: `\n[PAGE_MARKER_N]\n` before each page's text.
- Used to track page numbers through semantic chunking
- Stripped from final chunk content before DB storage
- Last marker in a chunk determines its `page_number`
