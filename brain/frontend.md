# Frontend

> See [architecture.md](architecture.md) for system context, [api.md](api.md) for endpoint specs.

## Stack
- **React 19** (SPA, single file: `src/App.jsx` — 1363 lines)
- **Vite 8** (dev server :5173, build tool)
- **Vanilla CSS** (`App.css` + `index.css`)
- **lucide-react** for icons
- **No router** — tab switching is pure state
- **No state management library** — all `useState`/`useEffect`

## File Structure
```
server_side/frontend/
├── src/
│   ├── App.jsx        # Entire application (state + logic + JSX)
│   ├── App.css        # Component styles
│   ├── index.css      # CSS variables + animations + base
│   └── main.jsx       # ReactDOM.render entry
├── index.html         # Vite entry HTML
├── vite.config.js     # Vite React plugin config
└── package.json
```

## Design System (index.css CSS Variables)
```css
--bg-main:    #090d16    /* Deep dark navy */
--bg-sidebar: #0f1624    /* Sidebar dark */
--bg-card:    rgba(17,24,39,0.7)
--primary:    #8b5cf6    /* Purple accent */
--secondary:  #10b981    /* Green accent */
--text-main:  #f3f4f6
--text-muted: #9ca3af
--border:     rgba(255,255,255,0.08)
--font-sans:  'Inter'
--font-heading: 'Outfit'
Animations: pulseGlow, spinSlow, slideInUp, fadeIn
```

## State Variables

| State | Type | Purpose |
|-------|------|---------|
| `activeTab` | `"discovery"\|"assistant"` | Tab navigation |
| `geminiKey` | string | Persisted to localStorage |
| `openaiKey` | string | Persisted to localStorage |
| `anthropicKey` | string | Persisted to localStorage |
| `jinaKey` | string | Persisted to localStorage |
| `parserMode` | `"basic"\|"advanced"` | Persisted to localStorage |
| `showSettings` | bool | API keys panel toggle |
| `selectedProvider` | `"google"\|"openai"\|"anthropic"` | Chat LLM selector |
| `papers` | array | ArXiv results |
| `documents` | array | User library from DB |
| `isUploading` | bool | PDF upload in progress |
| `uploadProgress` | string | Status message |
| `uploadError` | string | Error message |
| `activeDocument` | object\|null | Currently opened doc |
| `selectedDocumentIds` | string[] | Multi-doc selection |
| `messages` | array | Chat `[{role,content}]` |
| `inputMessage` | string | Chat input field |
| `isSending` | bool | Request in flight |
| `sidebarMinimized` | bool | Sidebar collapse |
| `paneMinimized` | bool | Chat pane collapse |
| `zoomedImage` | string\|null | Lightbox image URL |
| `expandedSources` | `{[msgIdx]: bool}` | Source cards toggle |

## Key Functions

### API Calls
| Function | Endpoint | Trigger |
|----------|----------|---------|
| `fetchTrendingPapers()` | GET /api/papers/trending | Mount |
| `handleSearch()` | GET /api/papers/search | Search form submit |
| `fetchDocuments()` | GET /api/documents | Mount + post-upload polling |
| `handleFileUpload()` | POST /api/parse | File picker change |
| `handleAnalyzePaper()` | POST /api/parse_url | "Analyze" button on ArXiv card |
| `handleSendMessage()` | POST /api/chat | Chat form submit |
| `handleClearHistory()` | DELETE /api/chat/history | Clear button |

### Upload Polling Pattern
```javascript
// After POST /api/parse returns 200 (background task queued):
const originalCount = documents.length;
const interval = setInterval(async () => {
  await fetchDocuments();
  retries++;
  if (documents.length > originalCount || retries > 20) {
    clearInterval(interval);  // stop after new doc appears or 60s
  }
}, 3000);
```

### Chat Streaming
```javascript
// Reads from ReadableStream (text/plain SSE-like)
const reader = response.body.getReader();
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  assistantText += decode(value);
  // Update last message in state with cumulative text
  setMessages(prev => { prev[last].content = assistantText; return [...prev]; });
}
// After stream: parse __SOURCES_METADATA__ from assistantText
```

### Sources Metadata Parsing
```javascript
// Backend appends at end of stream:
// "\n\n__SOURCES_METADATA__\n[{id, document_id, paper_title, chunk_type, content, page_number, image_path}]"
// Frontend splits on "__SOURCES_METADATA__" to separate display text from sources
```

### Citation Click Flow
```javascript
handleCitationClick(msgIdx, sourceIdx):
  1. setExpandedSources({...prev, [msgIdx]: true})
  2. setTimeout(() => {
       el = document.getElementById(`source-${msgIdx}-${sourceIdx}`)
       el.scrollIntoView({behavior:'smooth'})
       el.classList.add("highlighted-source")
       setTimeout(() => el.classList.remove("highlighted-source"), 2500)
     }, 100)
```

### Markdown Renderer (`renderMarkdown()`)
Custom inline parser — no library. Supports:
- `**bold**`, `` `code` ``, headings `#/##/###`
- Bullet lists `* ` or `- `
- Code blocks (``` fences)
- Citation badges: `[Source N]` or `[N]` → clickable `<button className="citation-badge">`
  - If `sourceIdx > sources.length` → degrades to plain text (hallucination guard)

## Layout Structure
```
<div.app-container>  (flex row, 100vh)
  <aside.sidebar [.minimized]>
    Brand logo + title
    Config section (API keys toggle, provider select, parser mode select)
    PDF upload area
    Library list (documents, checkboxes for multi-doc)
  </aside>
  <main.main-content>
    Tab bar (Discovery | Assistant)
    [Discovery] Paper feed grid + search bar + ArXiv cards
    [Assistant] Chat workspace
      <div.chat-pane [.minimized]>
        Chat header (doc title, clear button)
        Messages list (user/assistant bubbles)
        Source cards (expandable, figures w/ lightbox)
        Input form
      </div>
  </main>
  <div.lightbox> (fixed overlay, zoomedImage != null)
</div>
```

## Multi-Document Mode
- Checkbox per library doc → `selectedDocumentIds: string[]`
- If `selectedDocumentIds.length > 1`: `activeDocument = null`, multi-doc session
- `document_id` sent to API as comma-joined string: `"uuid1,uuid2,..."`
- Chat history fetched/stored against `null` document_id session on backend

## localStorage Keys
| Key | Value |
|-----|-------|
| `key_gemini` | Gemini API key string |
| `key_openai` | OpenAI API key string |
| `key_anthropic` | Anthropic API key string |
| `key_jina` | Jina API key string |
| `parser_mode` | `"basic"` or `"advanced"` |

## API_BASE Configuration
```javascript
// Hard-coded in App.jsx line 27:
const API_BASE = "http://192.168.1.13:8000";
// Change to http://localhost:8000 for local dev
```
