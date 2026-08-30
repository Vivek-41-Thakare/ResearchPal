import os
import json

paper_data_paths = [
    "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzE3MDYuMDM3NjJ2Ny5wZGY=\eval data",
    "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTAuMjEyMzZ2MS5wZGY=\eval data",
    "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTIuMTgzMTl2Mi5wZGY=\eval data",
    "aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDIuMTAyNDh2MS5wZGY=\eval data"
]

num_fetch_vectors = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

cp_cr_results_advanced = {}

for k in num_fetch_vectors:
    cp_cr_results_advanced[k] = { "cp": 0, "cr": 0 }

for k in num_fetch_vectors:
    cp_matches, cp_total_contexts = 0, 0
    cr_matches, cr_total_contexts = 0, 0
    for paper_data_path in paper_data_paths:
        gt_json_path = os.path.join(paper_data_path, "CP_CR", "question_gt_context_mapping_2500.json")
        rt_json_path = os.path.join(paper_data_path, "CP_CR", f"question_rt_context_mapping_2500_{k}_advanced.json")
        gt_json_data, rt_json_data = None, None
        with open(gt_json_path, "r", encoding="utf-8") as f:
            gt_json_data = json.load(f)
        with open(rt_json_path, "r", encoding="utf-8") as f:
            rt_json_data = json.load(f)
        assert len(gt_json_data) == len(rt_json_data)
        for i in range(len(gt_json_data)):
            curr_gt_context_ids = gt_json_data[i]['ground_truth_context_ids']
            curr_rt_context_ids = rt_json_data[i]['retrieved_context_ids']
            common_elements = set(curr_gt_context_ids) & set(curr_rt_context_ids)
            num_common_elements = len(common_elements)
            cp_matches += num_common_elements
            cr_matches += num_common_elements
            cp_total_contexts += len(curr_rt_context_ids)
            cr_total_contexts += len(curr_gt_context_ids)
    cp_cr_results_advanced[k]['cp'] = round(cp_matches / cp_total_contexts, 3)
    cp_cr_results_advanced[k]['cr'] = round(cr_matches / cr_total_contexts, 3)

save_path = "results/cp_cr_results_advanced.json"
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(cp_cr_results_advanced, f, indent=4)