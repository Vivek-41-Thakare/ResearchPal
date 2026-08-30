# Hybrid Search & Retrieval

> See [agent.md](agent.md) for agent context, [database.md](database.md) for SQL functions.

## Source: `services/supabase_service.py` — `hybrid_search()`

## Algorithm

```
Input: document_ids[], query_text, query_embedding, match_count=15

1. VECTOR SEARCH (fetch 2× candidates)
   similarity_search(doc_ids, query_embedding, match_count=30)
   → RPC match_chunks_v2(query_embedding, threshold=0.05, count=30, doc_ids)
   → cosine similarity: 1 - (embedding <=> query_embedding)
   Returns: ranked list of chunks with similarity scores

2. KEYWORD SEARCH
   SELECT all chunks for document_ids
   For each chunk:
     score = sum(content_lower.count(kw) for kw in keywords if len(kw)>2)
   Sort by score descending → top 30 chunks
   Keywords = query.split() filtered by len > 2

3. RECIPROCAL RANK FUSION (RRF)
   rrf_scores = {}
   for rank, chunk in vector_results:
       rrf_scores[chunk.id] += 1.0 / (60.0 + rank + 1)
   for rank, chunk in keyword_results:
       rrf_scores[chunk.id] += 1.0 / (60.0 + rank + 1)

   merged = sorted(rrf_scores, by score desc)[:match_count]

   Formula: Score(d) = 1/(60+rank_v) + 1/(60+rank_k)
```

## RRF Formula (from README)
$$\text{Score}(d) = \frac{1}{60 + \text{Rank}_{\text{vector}}} + \frac{1}{60 + \text{Rank}_{\text{keyword}}}$$

The constant 60 prevents high ranks from dominating when only one ranking has the document.

## Vector Search Parameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| `match_threshold` | 0.05 | Very low; optimized for Jina asymmetric search |
| `match_count` | 30 | 2× the final result count (15) |
| Distance metric | Cosine (`<=>`) | pgvector cosine distance operator |

## Similarity Search: `similarity_search()`
```python
pg_array = f"{{{','.join(document_ids)}}}"  # PostgreSQL array literal
params = {
    "query_embedding": embedding,
    "match_threshold": 0.05,
    "match_count": match_count * 2,
    "filter_document_ids": pg_array
}
response = client.rpc("match_chunks_v2", params).execute()
```

## Jina Reranker (Node 3 of LangGraph)
```
POST https://api.jina.ai/v1/rerank
{
  "model": "jina-reranker-v2-base-multilingual",
  "query": query_text,
  "documents": [chunk.content for chunk in retrieved_docs],  # 15 chunks
  "top_n": 5
}
Response: {"results": [{"index": int, "relevance_score": float}]}
Fallback: retrieved_docs[:5] (first 5 by RRF score)
```

## Intent-Based Reordering (Node 2 of LangGraph)
After hybrid search, results reordered (not re-scored) based on intent:

| Intent | Reordering Strategy |
|--------|---------------------|
| `greetings_or_general` | Skip retrieval entirely → [] |
| `visual_tabular` | Push `figure_summary`/`table` chunks first, then text |
| `global_synthesis` | Push abstract/conclusion/summary chunks + figure_summary/table first |
| `document_search` | Keep RRF order unchanged |

## Multi-Document Support
- `document_id` arrives as comma-separated string
- Both services split: `[d.strip() for d in doc_id.split(",")]`
- `match_chunks_v2` accepts UUID array: `document_id = ANY(filter_document_ids)`
- Keyword search uses `client.table().in_("document_id", document_ids)`
- Results merged across all documents; `paper_title` added per chunk for citations

## Embedding Provider Selection
```python
# In retrieve_context node:
embed_provider = "jina" if "jina" in api_keys and api_keys["jina"] else provider
# Query embedding: task="retrieval.query" (single text)
# Passage embedding (indexing): task="retrieval.passage" (batch)
```

## Jina v3 Task Types
```python
# EmbeddingsService.get_embeddings():
task = "retrieval.passage" if len(texts) > 1 else "retrieval.query"
# Different task types produce asymmetric embeddings optimized for retrieval
```
