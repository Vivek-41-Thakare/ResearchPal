import os
import json
import matplotlib.pyplot as plt

# Define directories
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data")
results_dir = os.path.join(base_dir, "results")
root_dir = os.path.dirname(base_dir)

os.makedirs(results_dir, exist_ok=True)

paper_dirs = [
    os.path.join(data_dir, "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzE3MDYuMDM3NjJ2Ny5wZGY=", "eval data"),
    os.path.join(data_dir, "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTAuMjEyMzZ2MS5wZGY=", "eval data"),
    os.path.join(data_dir, "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTIuMTgzMTl2Mi5wZGY=", "eval data"),
    os.path.join(data_dir, "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDIuMTAyNDh2MS5wZGY=", "eval data")
]

chunk_sizes = [1000, 1500, 2000, 2500]
k_values_default = [3, 5, 7, 9, 11, 13, 15]
k_values_advanced = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# -------------------------------------------------------------
# 1. Compute Default Mode CP / CR Results
# -------------------------------------------------------------
cp_cr_default = {}
for cs in chunk_sizes:
    cp_cr_default[cs] = {}
    for k in k_values_default:
        cp_matches, cp_total = 0, 0
        cr_matches, cr_total = 0, 0
        for p_dir in paper_dirs:
            gt_path = os.path.join(p_dir, "CP_CR", f"question_gt_context_mapping_{cs}.json")
            rt_path = os.path.join(p_dir, "CP_CR", f"question_rt_context_mapping_{cs}_{k}.json")
            if not (os.path.exists(gt_path) and os.path.exists(rt_path)):
                continue
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
            with open(rt_path, "r", encoding="utf-8") as f:
                rt_data = json.load(f)
            for i in range(min(len(gt_data), len(rt_data))):
                gt_ids = gt_data[i]['ground_truth_context_ids']
                rt_ids = rt_data[i]['retrieved_context_ids']
                common = set(gt_ids) & set(rt_ids)
                cp_matches += len(common)
                cr_matches += len(common)
                cp_total += len(rt_ids)
                cr_total += len(gt_ids)
        cp_val = round(cp_matches / cp_total, 3) if cp_total > 0 else 0.0
        cr_val = round(cr_matches / cr_total, 3) if cr_total > 0 else 0.0
        cp_cr_default[cs][k] = {"cp": cp_val, "cr": cr_val}

with open(os.path.join(results_dir, "cp_cr_results_default.json"), "w") as f:
    json.dump(cp_cr_default, f, indent=4)

# -------------------------------------------------------------
# 2. Compute Advanced Mode CP / CR Results (chunk_size = 2500)
# -------------------------------------------------------------
cp_cr_advanced = {}
for k in k_values_advanced:
    cp_matches, cp_total = 0, 0
    cr_matches, cr_total = 0, 0
    for p_dir in paper_dirs:
        gt_path = os.path.join(p_dir, "CP_CR", "question_gt_context_mapping_2500.json")
        rt_path = os.path.join(p_dir, "CP_CR", f"question_rt_context_mapping_2500_{k}_advanced.json")
        if not (os.path.exists(gt_path) and os.path.exists(rt_path)):
            continue
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)
        with open(rt_path, "r", encoding="utf-8") as f:
            rt_data = json.load(f)
        for i in range(min(len(gt_data), len(rt_data))):
            gt_ids = gt_data[i]['ground_truth_context_ids']
            rt_ids = rt_data[i]['retrieved_context_ids']
            common = set(gt_ids) & set(rt_ids)
            cp_matches += len(common)
            cr_matches += len(common)
            cp_total += len(rt_ids)
            cr_total += len(gt_ids)
    cp_val = round(cp_matches / cp_total, 3) if cp_total > 0 else 0.0
    cr_val = round(cr_matches / cr_total, 3) if cr_total > 0 else 0.0
    cp_cr_advanced[k] = {"cp": cp_val, "cr": cr_val}

with open(os.path.join(results_dir, "cp_cr_results_advanced.json"), "w") as f:
    json.dump(cp_cr_advanced, f, indent=4)

# -------------------------------------------------------------
# 3. Compute Figure Hit Rate
# -------------------------------------------------------------
figure_hitrate = {}
for cs in chunk_sizes:
    figure_hitrate[cs] = {}
    for k in k_values_default:
        matches, total = 0, 0
        for p_dir in paper_dirs:
            true_path = os.path.join(p_dir, "figures", "question_true_figure@1.json")
            ret_path = os.path.join(p_dir, "figures", f"question_retrieved_figure@1_{cs}_{k}.json")
            if not (os.path.exists(true_path) and os.path.exists(ret_path)):
                continue
            with open(true_path, "r", encoding="utf-8") as f:
                true_data = json.load(f)
            with open(ret_path, "r", encoding="utf-8") as f:
                ret_data = json.load(f)
            for i in range(min(len(true_data), len(ret_data))):
                true_ids = true_data[i]['true_labels']
                ret_ids = ret_data[i]['retrieved_figure_ids']
                if set(true_ids) & set(ret_ids):
                    matches += 1
                total += 1
        figure_hitrate[cs][k] = round(matches / total, 3) if total > 0 else 0.0

with open(os.path.join(results_dir, "figure@1_hitrate_results.json"), "w") as f:
    json.dump(figure_hitrate, f, indent=4)

# -------------------------------------------------------------
# 4. Compute Table Hit Rate
# -------------------------------------------------------------
table_hitrate = {}
for cs in chunk_sizes:
    table_hitrate[cs] = {}
    for k in k_values_default:
        matches, total = 0, 0
        for p_dir in paper_dirs:
            true_path = os.path.join(p_dir, "tables", "question_true_table@1.json")
            ret_path = os.path.join(p_dir, "tables", f"question_retrieved_table@1_{cs}_{k}.json")
            if not (os.path.exists(true_path) and os.path.exists(ret_path)):
                continue
            with open(true_path, "r", encoding="utf-8") as f:
                true_data = json.load(f)
            with open(ret_path, "r", encoding="utf-8") as f:
                ret_data = json.load(f)
            for i in range(min(len(true_data), len(ret_data))):
                true_ids = true_data[i]['true_labels']
                ret_ids = ret_data[i]['retrieved_table_ids']
                if set(true_ids) & set(ret_ids):
                    matches += 1
                total += 1
        table_hitrate[cs][k] = round(matches / total, 3) if total > 0 else 0.0

with open(os.path.join(results_dir, "table@1_hitrate_results.json"), "w") as f:
    json.dump(table_hitrate, f, indent=4)

# =============================================================
# Plotting Utilities
# =============================================================
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.facecolor'] = '#f8fafc'
plt.rcParams['grid.color'] = '#e2e8f0'

markers = {1000: 'o', 1500: 's', 2000: '^', 2500: 'D'}
colors = {1000: '#ef4444', 1500: '#3b82f6', 2000: '#10b981', 2500: '#8b5cf6'}

# 1. Context Recall Plot (Default Mode)
plt.figure(figsize=(8, 5.5))
for cs in chunk_sizes:
    y = [cp_cr_default[cs][k]['cr'] for k in k_values_default]
    plt.plot(k_values_default, y, marker=markers[cs], color=colors[cs], label=f"Chunk Size = {cs}", linewidth=2)
plt.title("Context Recall vs. Number of Retrieved Chunks (k)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Number of Retrieved Chunks (k)", fontsize=11, labelpad=8)
plt.ylabel("Context Recall", fontsize=11, labelpad=8)
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
plt.tight_layout()
plt.savefig(os.path.join(root_dir, "Context Recall Plot.png"), dpi=300)
plt.close()

# 2. Context Precision Plot (Default Mode)
plt.figure(figsize=(8, 5.5))
for cs in chunk_sizes:
    y = [cp_cr_default[cs][k]['cp'] for k in k_values_default]
    plt.plot(k_values_default, y, marker=markers[cs], color=colors[cs], label=f"Chunk Size = {cs}", linewidth=2)
plt.title("Context Precision vs. Number of Retrieved Chunks (k)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Number of Retrieved Chunks (k)", fontsize=11, labelpad=8)
plt.ylabel("Context Precision", fontsize=11, labelpad=8)
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
plt.tight_layout()
plt.savefig(os.path.join(root_dir, "Context Precision Plot.png"), dpi=300)
plt.close()

# 3. Context Precision & Context Recall Advanced Plot
plt.figure(figsize=(8, 5.5))
y_cp = [cp_cr_advanced[k]['cp'] for k in k_values_advanced]
y_cr = [cp_cr_advanced[k]['cr'] for k in k_values_advanced]
plt.plot(k_values_advanced, y_cp, marker='o', color='#3b82f6', label="Context Precision (Advanced)", linewidth=2.5)
plt.plot(k_values_advanced, y_cr, marker='D', color='#8b5cf6', label="Context Recall (Advanced)", linewidth=2.5)
plt.title("Context Precision & Recall vs. k (Advanced Mode, Chunk = 2500)", fontsize=12, fontweight='bold', pad=15)
plt.xlabel("Number of Retrieved Chunks (k)", fontsize=11, labelpad=8)
plt.ylabel("Metric Score", fontsize=11, labelpad=8)
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
plt.tight_layout()
plt.savefig(os.path.join(root_dir, "Context Precision & Context Recall Advanced.png"), dpi=300)
plt.close()

# 4. Figure@1 Hit-Rate Plot
plt.figure(figsize=(8, 5.5))
for cs in chunk_sizes:
    y = [figure_hitrate[cs][k] for k in k_values_default]
    plt.plot(k_values_default, y, marker=markers[cs], color=colors[cs], label=f"Chunk Size = {cs}", linewidth=2)
plt.title("Figure@1 Hit-Rate vs. Number of Retrieved Chunks (k)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Number of Retrieved Chunks (k)", fontsize=11, labelpad=8)
plt.ylabel("Figure Hit-Rate", fontsize=11, labelpad=8)
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
plt.tight_layout()
plt.savefig(os.path.join(root_dir, "Figure@1 Hit-Rate Plot.png"), dpi=300)
plt.close()

# 5. Table@1 Hit-Rate Plot
plt.figure(figsize=(8, 5.5))
for cs in chunk_sizes:
    y = [table_hitrate[cs][k] for k in k_values_default]
    plt.plot(k_values_default, y, marker=markers[cs], color=colors[cs], label=f"Chunk Size = {cs}", linewidth=2)
plt.title("Table@1 Hit-Rate vs. Number of Retrieved Chunks (k)", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Number of Retrieved Chunks (k)", fontsize=11, labelpad=8)
plt.ylabel("Table Hit-Rate", fontsize=11, labelpad=8)
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
plt.tight_layout()
plt.savefig(os.path.join(root_dir, "Table@1 Hit-Rate Plot.png"), dpi=300)
plt.close()

print("Successfully calculated all metrics and generated all 5 plots.")
