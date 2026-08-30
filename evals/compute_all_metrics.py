"""
ResearchPaL — Comprehensive Evaluation Suite
=============================================
Metrics computed (all offline from existing data files):
  1. Context Precision (CP)
  2. Context Recall (CR)
  3. Mean Reciprocal Rank (MRR)
  4. NDCG@K (Normalized Discounted Cumulative Gain)
  5. Hit@K  (K=3,5,10)
  6. Figure@1 Hit-Rate
  7. Table@1 Hit-Rate
  8. Reranker Delta  (vector-only vs hybrid, chunk_size=2500, k=9)
  9. P50 Query & Response Latency
 10. F1 = harmonic mean of CP & CR
"""
import os, json, math
from statistics import median

BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "data")
RES    = os.path.join(BASE, "results")
os.makedirs(RES, exist_ok=True)

PAPER_DIRS = [
    os.path.join(DATA, d, "eval data")
    for d in os.listdir(DATA)
    if os.path.isdir(os.path.join(DATA, d))
]

CHUNK_SIZES     = [1000, 1500, 2000, 2500]
K_VALUES        = [3, 5, 7, 9, 11, 13, 15]
K_ADV           = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def dcg(ranked_ids, relevant_ids):
    score = 0.0
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid in relevant_ids:
            score += 1.0 / math.log2(rank + 1)
    return score

def ndcg(ranked_ids, relevant_ids):
    ideal = sorted([1] * len(relevant_ids), reverse=True)
    ideal_dcg = sum(v / math.log2(r + 2) for r, v in enumerate(ideal))
    if ideal_dcg == 0:
        return 0.0
    return dcg(ranked_ids, relevant_ids) / ideal_dcg

def mrr(ranked_ids, relevant_ids):
    for rank, cid in enumerate(ranked_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0

def hit_at_k(ranked_ids, relevant_ids, k):
    return 1.0 if set(ranked_ids[:k]) & set(relevant_ids) else 0.0

# ─────────────────────────────────────────────────────────────────────────────
# 1-5  Retrieval metrics (CP, CR, F1, MRR, NDCG, Hit@K)
#      for Default mode across chunk_sizes × k_values
# ─────────────────────────────────────────────────────────────────────────────
print("Computing retrieval metrics (Default mode)...")
default_metrics = {}

for cs in CHUNK_SIZES:
    default_metrics[cs] = {}
    for k in K_VALUES:
        cp_m, cp_t = 0, 0
        cr_m, cr_t = 0, 0
        mrr_scores, ndcg_scores = [], []
        hit3, hit5, hit10 = [], [], []

        for p_dir in PAPER_DIRS:
            gt_path = os.path.join(p_dir, "CP_CR", f"question_gt_context_mapping_{cs}.json")
            rt_path = os.path.join(p_dir, "CP_CR", f"question_rt_context_mapping_{cs}_{k}.json")
            gt = load_json(gt_path)
            rt = load_json(rt_path)
            if not gt or not rt:
                continue
            for g, r in zip(gt, rt):
                gt_ids = set(g["ground_truth_context_ids"])
                rt_ids = r["retrieved_context_ids"]
                common = gt_ids & set(rt_ids)
                cp_m  += len(common); cp_t  += len(rt_ids)
                cr_m  += len(common); cr_t  += len(gt_ids)
                mrr_scores.append(mrr(rt_ids, gt_ids))
                ndcg_scores.append(ndcg(rt_ids, gt_ids))
                hit3.append(hit_at_k(rt_ids, gt_ids, 3))
                hit5.append(hit_at_k(rt_ids, gt_ids, 5))
                hit10.append(hit_at_k(rt_ids, gt_ids, 10))

        cp = round(cp_m / cp_t, 3) if cp_t else 0.0
        cr = round(cr_m / cr_t, 3) if cr_t else 0.0
        f1 = round(2*cp*cr/(cp+cr), 3) if (cp+cr) else 0.0
        default_metrics[cs][k] = {
            "cp":     cp,
            "cr":     cr,
            "f1":     f1,
            "mrr":    round(sum(mrr_scores)  / len(mrr_scores),  3) if mrr_scores  else 0.0,
            "ndcg":   round(sum(ndcg_scores) / len(ndcg_scores), 3) if ndcg_scores else 0.0,
            "hit@3":  round(sum(hit3)  / len(hit3),  3) if hit3  else 0.0,
            "hit@5":  round(sum(hit5)  / len(hit5),  3) if hit5  else 0.0,
            "hit@10": round(sum(hit10) / len(hit10), 3) if hit10 else 0.0,
        }

with open(os.path.join(RES, "retrieval_metrics_default.json"), "w") as f:
    json.dump(default_metrics, f, indent=2)
print("  ✓ retrieval_metrics_default.json")

# ─────────────────────────────────────────────────────────────────────────────
# Advanced mode metrics (chunk_size=2500)
# ─────────────────────────────────────────────────────────────────────────────
print("Computing retrieval metrics (Advanced mode)...")
adv_metrics = {}
for k in K_ADV:
    cp_m, cp_t, cr_m, cr_t = 0, 0, 0, 0
    mrr_scores, ndcg_scores = [], []
    hit3, hit5, hit10 = [], [], []
    for p_dir in PAPER_DIRS:
        gt_path = os.path.join(p_dir, "CP_CR", "question_gt_context_mapping_2500.json")
        rt_path = os.path.join(p_dir, "CP_CR", f"question_rt_context_mapping_2500_{k}_advanced.json")
        gt = load_json(gt_path)
        rt = load_json(rt_path)
        if not gt or not rt:
            continue
        for g, r in zip(gt, rt):
            gt_ids = set(g["ground_truth_context_ids"])
            rt_ids = r["retrieved_context_ids"]
            common = gt_ids & set(rt_ids)
            cp_m += len(common); cp_t += len(rt_ids)
            cr_m += len(common); cr_t += len(gt_ids)
            mrr_scores.append(mrr(rt_ids, gt_ids))
            ndcg_scores.append(ndcg(rt_ids, gt_ids))
            hit3.append(hit_at_k(rt_ids, gt_ids, 3))
            hit5.append(hit_at_k(rt_ids, gt_ids, 5))
            hit10.append(hit_at_k(rt_ids, gt_ids, 10))

    cp = round(cp_m / cp_t, 3) if cp_t else 0.0
    cr = round(cr_m / cr_t, 3) if cr_t else 0.0
    f1 = round(2*cp*cr/(cp+cr), 3) if (cp+cr) else 0.0
    adv_metrics[k] = {
        "cp":   cp, "cr":  cr, "f1": f1,
        "mrr":  round(sum(mrr_scores)/len(mrr_scores), 3)  if mrr_scores  else 0.0,
        "ndcg": round(sum(ndcg_scores)/len(ndcg_scores),3) if ndcg_scores else 0.0,
        "hit@3":  round(sum(hit3)/len(hit3),3)   if hit3   else 0.0,
        "hit@5":  round(sum(hit5)/len(hit5),3)   if hit5   else 0.0,
        "hit@10": round(sum(hit10)/len(hit10),3) if hit10  else 0.0,
    }

with open(os.path.join(RES, "retrieval_metrics_advanced.json"), "w") as f:
    json.dump(adv_metrics, f, indent=2)
print("  ✓ retrieval_metrics_advanced.json")

# ─────────────────────────────────────────────────────────────────────────────
# Reranker Delta: compare k=9 (no rerank) vs k=15→top5 (simulated rerank)
# Using chunk_size=2500 default mode
# ─────────────────────────────────────────────────────────────────────────────
print("Computing Reranker Delta...")
def compute_retrieval_at_k(cs, k, mode=""):
    cp_m, cp_t, cr_m, cr_t, mrr_s = 0, 0, 0, 0, []
    for p_dir in PAPER_DIRS:
        gt_path = os.path.join(p_dir, "CP_CR", f"question_gt_context_mapping_{cs}.json")
        suffix  = f"_{mode}" if mode else ""
        rt_path = os.path.join(p_dir, "CP_CR", f"question_rt_context_mapping_{cs}_{k}{suffix}.json")
        gt = load_json(gt_path); rt = load_json(rt_path)
        if not gt or not rt: continue
        for g, r in zip(gt, rt):
            gt_ids = set(g["ground_truth_context_ids"]); rt_ids = r["retrieved_context_ids"]
            common = gt_ids & set(rt_ids)
            cp_m += len(common); cp_t += len(rt_ids)
            cr_m += len(common); cr_t += len(gt_ids)
            mrr_s.append(mrr(rt_ids, gt_ids))
    cp = round(cp_m/cp_t, 3) if cp_t else 0.0
    cr = round(cr_m/cr_t, 3) if cr_t else 0.0
    return {"cp": cp, "cr": cr, "mrr": round(sum(mrr_s)/len(mrr_s),3) if mrr_s else 0.0}

reranker_delta = {
    "without_rerank_k9":  compute_retrieval_at_k(2500, 9),
    "without_rerank_k15": compute_retrieval_at_k(2500, 15),
    "with_rerank_k9_adv": compute_retrieval_at_k(2500, 9,  "advanced"),
    "with_rerank_k15_adv":compute_retrieval_at_k(2500, 15, "advanced"),
    "note": "Reranker simulated by Advanced mode (figure/table boosting + layout chunks). Delta = adv - default."
}
for label in ["k9","k15"]:
    k = int(label[1:])
    base = reranker_delta[f"without_rerank_{label}"]
    adv  = reranker_delta[f"with_rerank_{label}_adv"]
    reranker_delta[f"delta_{label}"] = {
        "cp_delta":  round(adv["cp"]  - base["cp"],  3),
        "cr_delta":  round(adv["cr"]  - base["cr"],  3),
        "mrr_delta": round(adv["mrr"] - base["mrr"], 3),
    }

with open(os.path.join(RES, "reranker_delta.json"), "w") as f:
    json.dump(reranker_delta, f, indent=2)
print("  ✓ reranker_delta.json")

# ─────────────────────────────────────────────────────────────────────────────
# Figure@1 & Table@1 Hit-Rate
# ─────────────────────────────────────────────────────────────────────────────
print("Computing Figure & Table Hit-Rates...")
fig_hr, tbl_hr = {}, {}
for cs in CHUNK_SIZES:
    fig_hr[cs] = {}; tbl_hr[cs] = {}
    for k in K_VALUES:
        fig_m, fig_t, tbl_m, tbl_t = 0, 0, 0, 0
        for p_dir in PAPER_DIRS:
            for kind, hr_dict, m_ref, t_ref in [
                ("figures", fig_hr, "fig_m", "fig_t"),
                ("tables",  tbl_hr, "tbl_m", "tbl_t"),
            ]:
                true_path = os.path.join(p_dir, kind, f"question_true_{kind.rstrip('s')}@1.json" if kind=="figures" else f"question_true_{kind.rstrip('s')}@1.json")
                ret_path  = os.path.join(p_dir, kind, f"question_retrieved_{kind.rstrip('s')}@1_{cs}_{k}.json")
                true_d = load_json(true_path); ret_d = load_json(ret_path)
                if not true_d or not ret_d: continue
                for td, rd in zip(true_d, ret_d):
                    hit = bool(set(td["true_labels"]) & set(rd.get("retrieved_figure_ids", rd.get("retrieved_table_ids", []))))
                    if kind == "figures": fig_m += hit; fig_t += 1
                    else:                tbl_m += hit; tbl_t += 1
        fig_hr[cs][k] = round(fig_m/fig_t, 3) if fig_t else 0.0
        tbl_hr[cs][k] = round(tbl_m/tbl_t, 3) if tbl_t else 0.0

with open(os.path.join(RES, "figure_hitrate.json"), "w") as f:
    json.dump(fig_hr, f, indent=2)
with open(os.path.join(RES, "table_hitrate.json"), "w") as f:
    json.dump(tbl_hr, f, indent=2)
print("  ✓ figure_hitrate.json  table_hitrate.json")

# ─────────────────────────────────────────────────────────────────────────────
# Latency P50
# ─────────────────────────────────────────────────────────────────────────────
print("Computing P50 Latencies...")
lat_path = os.path.join(RES, "latencies.json")
lat_data = load_json(lat_path) or {}
p50 = {}
for metric_key in ["query_latencies", "response_latencies"]:
    p50[metric_key] = {}
    for category, modes in lat_data.get(metric_key, {}).items():
        p50[metric_key][category] = {}
        for mode, vals in modes.items():
            p50[metric_key][category][mode] = round(median(vals))

with open(os.path.join(RES, "p50_latencies.json"), "w") as f:
    json.dump(p50, f, indent=2)
print("  ✓ p50_latencies.json")

# ─────────────────────────────────────────────────────────────────────────────
# Summary table — best config per metric
# ─────────────────────────────────────────────────────────────────────────────
print("Building summary table...")
best = {}
for cs in CHUNK_SIZES:
    for k in K_VALUES:
        m = default_metrics[cs][k]
        key = f"cs={cs}, k={k}"
        best[key] = m["f1"]

best_config = max(best, key=best.get)
best_m = default_metrics[int(best_config.split(",")[0].split("=")[1])][int(best_config.split(",")[1].split("=")[1])]

summary = {
    "best_default_config": best_config,
    "best_f1":             best_m["f1"],
    "best_cp":             best_m["cp"],
    "best_cr":             best_m["cr"],
    "best_mrr":            best_m["mrr"],
    "best_ndcg":           best_m["ndcg"],
    "best_hit@5":          best_m["hit@5"],
    "best_hit@10":         best_m["hit@10"],
    "figure@1_best":       max(fig_hr[2500].values()),
    "table@1_best":        max(tbl_hr[2500].values()),
    "adv_best_f1":         max(v["f1"]  for v in adv_metrics.values()),
    "adv_best_mrr":        max(v["mrr"] for v in adv_metrics.values()),
    "p50_query_text_default_ms":    p50.get("query_latencies",{}).get("only_text",{}).get("default", "N/A"),
    "p50_response_text_default_ms": p50.get("response_latencies",{}).get("only_text",{}).get("default", "N/A"),
}

with open(os.path.join(RES, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print("\n✅ All metrics computed. Results saved to evals/results/")
print(f"   Best Default Config : {summary['best_default_config']}")
print(f"   Best F1             : {summary['best_f1']}")
print(f"   Best MRR            : {summary['best_mrr']}")
print(f"   Best NDCG           : {summary['best_ndcg']}")
print(f"   Figure@1 (best)     : {summary['figure@1_best']}")
print(f"   Table@1  (best)     : {summary['table@1_best']}")
