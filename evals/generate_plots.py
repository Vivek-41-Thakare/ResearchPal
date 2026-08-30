"""
ResearchPaL — Plot Generator for All Evaluation Metrics
Generates 8 publication-quality plots from computed metric JSON files.
"""
import os, json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
BASE     = os.path.dirname(os.path.abspath(__file__))
RES      = os.path.join(BASE, "results")
PLOT_DIR = os.path.join(BASE, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)
CHUNK_SIZES = [1000, 1500, 2000, 2500]
K_VALUES    = [3, 5, 7, 9, 11, 13, 15]
K_ADV       = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
MARKERS = {1000: 'o', 1500: 's', 2000: '^', 2500: 'D'}
COLORS  = {1000: '#ef4444', 1500: '#3b82f6', 2000: '#10b981', 2500: '#8b5cf6'}
plt.rcParams.update({
    'font.family':     'DejaVu Sans',
    'axes.facecolor':  '#f8fafc',
    'axes.edgecolor':  '#cbd5e1',
    'grid.color':      '#e2e8f0',
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.dpi':       150,
})
def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)
def savefig(name, fig=None):
    path = os.path.join(PLOT_DIR, name)
    (fig or plt).savefig(path, dpi=180, bbox_inches='tight')
    plt.close('all')
    print(f"  ✓ {name}")
dm  = {int(k): {int(kk): vv for kk, vv in v.items()} for k, v in load("retrieval_metrics_default.json").items()}
adv = {int(k): v for k, v in load("retrieval_metrics_advanced.json").items()}
fhr = {int(k): {int(kk): vv for kk, vv in v.items()} for k, v in load("figure_hitrate.json").items()}
thr = {int(k): {int(kk): vv for kk, vv in v.items()} for k, v in load("table_hitrate.json").items()}
rrd = load("reranker_delta.json")
p50 = load("p50_latencies.json")
smr = load("summary.json")
print("Generating plots...")
# ── Plot 1: CP & CR Default ──────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for cs in CHUNK_SIZES:
    cp_y = [dm[cs][k]['cp'] for k in K_VALUES]
    cr_y = [dm[cs][k]['cr'] for k in K_VALUES]
    kw   = dict(marker=MARKERS[cs], color=COLORS[cs], label=f"Chunk={cs}", linewidth=2, markersize=6)
    axes[0].plot(K_VALUES, cp_y, **kw)
    axes[1].plot(K_VALUES, cr_y, **kw)
for ax, title in zip(axes, ["Context Precision vs k", "Context Recall vs k"]):
    ax.set_xlabel("k (Retrieved Chunks)", fontsize=11); ax.set_ylabel("Score", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=9)
plt.suptitle("Retrieval Quality — Default Mode (Semantic Chunking + Hybrid Search)", fontsize=12, y=1.01)
plt.tight_layout()
savefig("01_cp_cr_default.png", fig)
# ── Plot 2: F1 Default ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
for cs in CHUNK_SIZES:
    y = [dm[cs][k]['f1'] for k in K_VALUES]
    ax.plot(K_VALUES, y, marker=MARKERS[cs], color=COLORS[cs], label=f"Chunk={cs}", linewidth=2.5, markersize=6)
ax.set_xlabel("k", fontsize=11); ax.set_ylabel("F1 Score", fontsize=11)
ax.set_title("F1 Score (Harmonic Mean CP & CR) — Default Mode", fontsize=13, fontweight='bold')
ax.set_ylim(0, 0.8); ax.grid(True, linestyle='--', alpha=0.6); ax.legend()
savefig("02_f1_default.png", fig)
# ── Plot 3: MRR & NDCG Default ──────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for cs in CHUNK_SIZES:
    mrr_y  = [dm[cs][k]['mrr']  for k in K_VALUES]
    ndcg_y = [dm[cs][k]['ndcg'] for k in K_VALUES]
    kw = dict(marker=MARKERS[cs], color=COLORS[cs], label=f"Chunk={cs}", linewidth=2, markersize=6)
    axes[0].plot(K_VALUES, mrr_y,  **kw)
    axes[1].plot(K_VALUES, ndcg_y, **kw)
for ax, title in zip(axes, ["MRR (Mean Reciprocal Rank)", "NDCG (Normalized DCG)"]):
    ax.set_xlabel("k", fontsize=11); ax.set_ylabel("Score", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.6); ax.legend(fontsize=9)
plt.tight_layout()
savefig("03_mrr_ndcg_default.png", fig)
# ── Plot 4: Hit@K Default ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
hit_ks = ['hit@3', 'hit@5', 'hit@10']
hit_colors = ['#f59e0b', '#8b5cf6', '#10b981']
# Use chunk=2500 only
for hk, hc in zip(hit_ks, hit_colors):
    y = [dm[2500][k][hk] for k in K_VALUES]
    ax.plot(K_VALUES, y, marker='D', color=hc, label=hk, linewidth=2.5, markersize=6)
ax.set_xlabel("k", fontsize=11); ax.set_ylabel("Hit Rate", fontsize=11)
ax.set_title("Hit@K Rates — Default Mode (Chunk=2500)", fontsize=13, fontweight='bold')
ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.6); ax.legend()
savefig("04_hit_at_k.png", fig)
# ── Plot 5: Advanced mode CP CR MRR ─────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
cp_a  = [adv[k]['cp']  for k in K_ADV]
cr_a  = [adv[k]['cr']  for k in K_ADV]
mrr_a = [adv[k]['mrr'] for k in K_ADV]
for ax, y, title, color in zip(axes, [cp_a, cr_a, mrr_a],
        ["Context Precision", "Context Recall", "MRR"],
        ['#3b82f6', '#8b5cf6', '#10b981']):
    ax.plot(K_ADV, y, marker='o', color=color, linewidth=2.5, markersize=6)
    ax.set_xlabel("k", fontsize=11); ax.set_ylabel("Score", fontsize=11)
    ax.set_title(f"{title} — Advanced Mode", fontsize=12, fontweight='bold')
    ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.6)
plt.suptitle("Retrieval Quality — Advanced Mode (Adobe Layout + Figures/Tables)", fontsize=12, y=1.01)
plt.tight_layout()
savefig("05_advanced_cp_cr_mrr.png", fig)
# ── Plot 6: Figure@1 & Table@1 Hit-Rate ─────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for cs in CHUNK_SIZES:
    fig_y = [fhr[cs][k] for k in K_VALUES]
    tbl_y = [thr[cs][k] for k in K_VALUES]
    kw = dict(marker=MARKERS[cs], color=COLORS[cs], label=f"Chunk={cs}", linewidth=2, markersize=6)
    axes[0].plot(K_VALUES, fig_y, **kw)
    axes[1].plot(K_VALUES, tbl_y, **kw)
for ax, title in zip(axes, ["Figure@1 Hit-Rate", "Table@1 Hit-Rate"]):
    ax.set_xlabel("k", fontsize=11); ax.set_ylabel("Hit Rate", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.set_ylim(0, 1.05); ax.grid(True, linestyle='--', alpha=0.6); ax.legend(fontsize=9)
plt.tight_layout()
savefig("06_figure_table_hitrate.png", fig)
# ── Plot 7: Reranker Delta ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
configs = ['without_rerank_k9', 'without_rerank_k15', 'with_rerank_k9_adv', 'with_rerank_k15_adv']
labels  = ['Vector-only\n(k=9)', 'Vector-only\n(k=15)', 'Hybrid+Rerank\n(k=9)', 'Hybrid+Rerank\n(k=15)']
cp_vals  = [rrd[c]['cp']  for c in configs]
cr_vals  = [rrd[c]['cr']  for c in configs]
mrr_vals = [rrd[c]['mrr'] for c in configs]
x = np.arange(len(labels)); w = 0.25
b1 = ax.bar(x - w, cp_vals,  w, label='CP',  color='#3b82f6', alpha=0.85)
b2 = ax.bar(x,     cr_vals,  w, label='CR',  color='#8b5cf6', alpha=0.85)
b3 = ax.bar(x + w, mrr_vals, w, label='MRR', color='#10b981', alpha=0.85)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("Score", fontsize=11)
ax.set_title("Reranker Effectiveness: Vector-only vs Hybrid+Layout Rerank", fontsize=12, fontweight='bold')
ax.set_ylim(0, 1.1); ax.legend(); ax.grid(axis='y', linestyle='--', alpha=0.6)
for bars in [b1, b2, b3]:
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02,
                f"{bar.get_height():.2f}", ha='center', fontsize=8)
savefig("07_reranker_delta.png", fig)
# ── Plot 8: Latency Summary ──────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
categories  = list(p50["query_latencies"].keys())
cat_labels  = ["Text Only", "Text + Image", "Text + File"]
bar_w = 0.35
for ax_idx, metric_key, title in [(0,"query_latencies","Query Latency (P50, ms)"),
                                    (1,"response_latencies","Response Latency (P50, ms)")]:
    ax = axes[ax_idx]
    def_vals = [p50[metric_key][c]["default"] for c in categories]
    adv_vals = [p50[metric_key][c]["advanced"] for c in categories]
    x = np.arange(len(categories))
    b1 = ax.bar(x - bar_w/2, def_vals, bar_w, label='Default Mode', color='#3b82f6', alpha=0.85)
    b2 = ax.bar(x + bar_w/2, adv_vals, bar_w, label='Advanced Mode', color='#8b5cf6', alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(cat_labels, fontsize=10)
    ax.set_ylabel("Latency (ms)", fontsize=11); ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(); ax.grid(axis='y', linestyle='--', alpha=0.6)
    for bars in [b1, b2]:
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+30,
                    f"{int(bar.get_height())}", ha='center', fontsize=8)
plt.tight_layout()
savefig("08_latency_p50.png", fig)
print(f"\n✅ All 8 plots saved to evals/plots/")
