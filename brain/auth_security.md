# Auth & Security

> See [api.md](api.md) for header details, [frontend.md](frontend.md) for localStorage usage.

## API Key Model

**Zero server-side key storage.** All user LLM API keys flow through request headers only.

```
Client (browser localStorage)
  → sets X-Gemini-API-Key, X-OpenAI-API-Key, X-Anthropic-API-Key, X-Jina-API-Key headers
  → on every /api/chat, /api/parse, /api/parse_url request
  
Backend (get_api_keys dependency)
  → reads from headers
  → falls back to server .env only if header is empty/placeholder
  → keys exist only in memory for duration of request
  → never logged except partial debug prints (see: "found"/"missing" labels)
  → never stored in DB
```

## Key Validation (`get_api_keys()` dependency)

```python
def clean_key(header_val, env_var_name):
    val = header_val.strip() if header_val else ""
    # Reject: empty, starts with "●" (masked), contains "dummy"
    if not val or val.startswith("●") or "dummy" in val.lower():
        val = os.getenv(env_var_name) or ""
    return val.strip().strip('"').strip("'") or None
```

Priorities for Gemini:
1. `X-Gemini-API-Key` header
2. `GEMINI_API_KEY` env var
3. `gemini_api_key` env var (alternate case)
4. `GOOGLE_API_KEY` env var

## Frontend Key Storage

Keys stored exclusively in browser `localStorage`:
```javascript
localStorage.setItem("key_gemini", geminiKey)    // on every state change
localStorage.setItem("key_openai", openaiKey)
localStorage.setItem("key_anthropic", anthropicKey)
localStorage.setItem("key_jina", jinaKey)
localStorage.setItem("parser_mode", parserMode)
```

Displayed as `type="password"` inputs. Keys are sent with every relevant request.

## CORS Configuration

```python
# main.py
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> ⚠️ `"*"` in `allow_origins` is a known loose setting (suitable for dev; tighten for production)

## Supabase Access

- Backend uses **service role key** (`SUPABASE_KEY`) — full DB access
- No RLS (Row Level Security) enforced by default (schema does not define RLS policies)
- All documents/chunks accessible by any request reaching the backend
- Supabase Storage `figures` bucket: public (no auth for figure reads)

## ArXiv URL Validation

PDF downloads from URLs are validated before processing:
```python
if not file_content.startswith(b"%PDF"):
    raise HTTPException(400, "Downloaded content is not a valid PDF file (missing %PDF header)")
```

## Limitations / Risks

| Risk | Mitigation |
|------|-----------|
| CORS `"*"` allows any origin | Set `FRONTEND_URL` env to production domain |
| No RLS on Supabase | All users share same DB; no user isolation |
| No authentication on `/api/*` | Backend is assumed to be private/self-hosted |
| Keys in localStorage | Cleared when browser storage cleared; no server exposure |
| Debug prints log "found"/"missing" key status | Not sensitive; no key values logged |
| Adobe credentials in `.env.example` contain sample values | Rotate before any public deployment |
