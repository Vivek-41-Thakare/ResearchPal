# Evaluation Suite

> Source: `evals/` directory. See [architecture.md](architecture.md) for system context.

## Purpose
Offline benchmarking of retrieval quality across chunk sizes, k values, and modes.
Dataset: 4 research papers × 10 questions each = 40 Q&A pairs.

## Eval Scripts

| Script | Purpose |
|--------|---------|
| `compute_all_metrics.py` | Master: computes all metrics offline from data/ files |
| `generate_plots.py` | Generates all 8 evaluation PNG plots |
| `generate_all_eval_plots.py` | Extended plot generation |
| `generate_cp_cr_results_default.py` | Context Precision/Recall for default mode |
| `generate_cp_cr_results_advanced.py` | CP/CR for advanced (Adobe) mode |
| `generate_figure@1_hitrate_results.py` | Figure retrieval hit rate |
| `generate_table@1_hitrate_results.py` | Table retrieval hit rate |
| `generate_question_vs_context_for_relevance_check.py` | Relevance evaluation data |
| `split_and_save_text.py` | Preprocessing: splits PDFs into eval chunks |
| `calculate_p50_latencies.py` | P50 latency computation |

## Metrics Computed

| Metric | Formula | Best Value |
|--------|---------|------------|
| Context Precision (CP) | Relevant retrieved / Total retrieved | 0.511 (chunk=2500, k=3) |
| Context Recall (CR) | Relevant retrieved / Total relevant | 0.991 (chunk=2500, k=13) |
| F1 | 2×CP×CR / (CP+CR) | **0.556** (chunk=2500, k=7) |
| MRR | 1/rank of first relevant | 0.757 (chunk=2500) |
| NDCG@K | DCG / ideal DCG | 0.765 (chunk=2500) |
| Hit@K | 1 if any relevant in top-K | 1.000 at Hit@5 |
| Figure@1 Hit-Rate | Figure query → figure in top-1 | 1.000 at k≥13 |
| Table@1 Hit-Rate | Table query → table in top-1 | 1.000 at k≥13 |

## Sweep Parameters
```python
CHUNK_SIZES = [1000, 1500, 2000, 2500]
K_VALUES    = [3, 5, 7, 9, 11, 13, 15]          # default mode
K_ADV       = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]  # advanced mode
```

## Helper Functions (compute_all_metrics.py)
```python
def dcg(ranked_ids, relevant_ids):
    return sum(1.0/log2(rank+1) for rank, id in enumerate(ranked_ids,1) if id in relevant_ids)

def ndcg(ranked_ids, relevant_ids):
    return dcg(ranked_ids, relevant_ids) / ideal_dcg(len(relevant_ids))

def mrr(ranked_ids, relevant_ids):
    for rank, id in enumerate(ranked_ids, 1):
        if id in relevant_ids: return 1.0/rank
    return 0.0
```

## Data Structure (evals/data/)
```
data/
  {paper_name}/
    eval data/
      *.json    # Ground truth: {question, relevant_chunk_ids[], ...}
results/
  *.json        # Computed metric JSONs
plots/
  01_cp_cr_default.png
  02_f1_default.png
  03_mrr_ndcg_default.png
  04_hit_at_k.png
  05_advanced_cp_cr_mrr.png
  06_figure_table_hitrate.png
  07_reranker_delta.png
  08_latency_p50.png
```

## Key Findings
- **Optimal for text**: chunk=2500, k=9 → CR=0.927, CP=0.374, F1=0.556
- **Perfect recall**: chunk=2500, k=13 → CR=0.991 (near-perfect coverage)
- **Perfect Hit@5**: Every text query finds ≥1 relevant chunk in top 5
- **Advanced mode reranker**: +4.2% Context Precision at k=9 for visual queries
- **P50 text query latency**: 646ms (default) vs 870ms (advanced)
- **P50 text response latency**: 2620ms (default) vs 4374ms (advanced)
- **Vision queries are slower**: ~3-4× text-only queries due to vision model calls
