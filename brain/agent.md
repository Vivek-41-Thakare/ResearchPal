# LangGraph Multi-Agent Pipeline

> See [architecture.md](architecture.md) for system context, [search.md](search.md) for retrieval details, [backend.md](backend.md) for streaming.

## Source: `server_side/backend/graph/agent.py`

## State Definition (`AgentState` TypedDict)

| Field | Type | Description |
|-------|------|-------------|
| `query` | str | Current user query |
| `document_id` | str | Comma-separated document UUIDs |
| `api_keys` | Dict[str,str] | `{gemini, openai, anthropic, jina}` |
| `chat_history` | List[Dict] | Prior messages `[{role, content}]` |
| `retrieved_documents` | List[Dict] | Chunks from hybrid search |
| `final_response` | str | LLM-generated answer |
| `selected_provider` | Literal | `"google"/"openai"/"anthropic"` |
| `intent` | Optional[str] | Classified intent |
| `critic_feedback` | Optional[str] | Legacy compat field (unused) |
| `iteration_count` | int | Legacy compat field |

## Graph Topology

```
START
  │
  ▼
[intent_router]
  │
  ├── intent == "greetings_or_general"  ──────────────────┐
  │                                                        │
  └── all other intents                                    │
        │                                                  │
        ▼                                                  │
  [retrieve_context]                                       │
        │                                                  │
        ▼                                                  │
  [rerank_context]                                         │
        │                                                  │
        ▼                                                  ▼
  [generate_response] ◄────────────────────────────────────┘
        │
        ▼
      END
```

## Node 1: `intent_router`

**Input**: `query`, `api_keys`, `selected_provider`  
**Output**: `{intent: str}`

```python
# System prompt classifies to exactly one of:
intents = [
    "greetings_or_general",   # chit-chat, no retrieval needed
    "visual_tabular",         # tables, figures, charts
    "global_synthesis",       # summaries, conclusions, methodology
    "document_search"         # dense text, equations, algorithms
]
# Fallback: "document_search" on any exception
```

## Node 2: `retrieve_context`

**Input**: `query`, `document_id`, `api_keys`, `intent`  
**Output**: `{retrieved_documents: list}`

```python
# Skip retrieval entirely for greetings
if intent == "greetings_or_general":
    return {"retrieved_documents": []}

# Embed query (prefer Jina if key present)
embed_provider = "jina" if "jina" in api_keys else provider
query_embedding = EmbeddingsService.get_embeddings([query], ...)

# Parse comma-separated doc IDs for multi-doc mode
doc_ids = [d.strip() for d in document_id.split(",")]

# Hybrid search: 15 candidates
matches = supabase_service.hybrid_search(doc_ids, query, query_embedding, match_count=15)

# Map document_id → paper_title (for citations)
doc_map = {d["id"]: d["paper_title"] for d in documents_table}

# Intent-based boosting (reordering, not re-scoring):
if intent == "visual_tabular":
    visual = [m for m in matches if chunk_type in ["figure_summary","table"]]
    text   = [m for m in matches if chunk_type == "text"]
    matches = visual + text

elif intent == "global_synthesis":
    global_chunks = [m for m in matches
                     if chunk_type in ["figure_summary","table"]
                     or "abstract"/"conclusion"/"summary" in content.lower()]
    matches = global_chunks + other_chunks
```

## Node 3: `rerank_context`

**Input**: `query`, `retrieved_documents`, `api_keys`  
**Output**: `{retrieved_documents: top-5 list}`

```python
if jina_key:
    # POST https://api.jina.ai/v1/rerank
    data = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": [doc["content"] for doc in retrieved_docs],
        "top_n": 5
    }
    # Returns indexed results with relevance_score
    # On API error → fallback

# Fallback: retrieved_docs[:5]
```

## Node 4: `generate_response`

**Input**: all state fields  
**Output**: `{final_response, critic_feedback:None, iteration_count:+1}`

### Greeting path (no retrieval)
```
SystemPrompt: "Answer warmly and concisely. No citations."
Messages: [SystemMessage] + history + [HumanMessage(query)]
```

### RAG path (with context)
```
# Build context string:
for idx, doc in enumerate(retrieved_docs):
    citation = f"{short_title} | Page {page_num}"
    # figure → "... | Figure: filename | Page N"
    # table  → "... | Table | Page N"
    context_str += f"--- Source {idx+1} ({citation}) ---\n{content}\n"

SystemPrompt: "Answer ONLY from context. Cite as [Source N]. State 'I don't know' if absent."
Messages: [SystemMessage(context)] + history + [HumanMessage(query)]
```

LLM is invoked synchronously (not streaming here — streaming happens via `astream_events` at the `main.py` level).

## LLM Instantiation: `get_llm(provider, api_keys)`

```python
google:    ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
openai:    ChatOpenAI(model="gpt-4o-mini")
anthropic: ChatAnthropic(model="claude-3-5-sonnet-20241022")
```

## Compilation
```python
workflow = StateGraph(AgentState)
workflow.add_node("intent_router", intent_router)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("rerank_context", rerank_context)
workflow.add_node("generate_response", generate_response)

workflow.add_edge(START, "intent_router")
workflow.add_conditional_edges("intent_router", route_after_intent, {...})
workflow.add_edge("retrieve_context", "rerank_context")
workflow.add_edge("rerank_context", "generate_response")
workflow.add_edge("generate_response", END)

agent_graph = workflow.compile()
```

## Streaming Hook (in main.py)
```python
# Only events from "generate_response" node are yielded to client
if kind == "on_chat_model_stream" and node == "generate_response":
    yield text_chunk
# Retrieved docs captured from "on_chain_end" events
if kind == "on_chain_end" and "retrieved_documents" in output:
    captured = output["retrieved_documents"]
```
