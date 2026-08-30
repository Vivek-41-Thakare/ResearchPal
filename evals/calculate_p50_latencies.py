import json
import numpy as np

file_path = "evals/results/latencies.json"
with open(file_path, "r") as file:
    data = json.load(file)

def calculate_medians(latency_data):
    medians = {}
    for category, subcategories in latency_data.items():
        medians[category] = {}
        for subcategory, values in subcategories.items():
            medians[category][subcategory] = np.median(values)
    return medians

query_medians = calculate_medians(data["query_latencies"])
response_medians = calculate_medians(data["response_latencies"])

query_medians, response_medians