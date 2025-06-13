import json
import glob
from pathlib import Path

EVAL_RESULTS_DIR = "./results/gpt_temperature/eval_results"  
CASE_FILTERS_PATH = "../data/extracted_sample_cases.json"  
OUTPUT_DIR = "./results/gpt_temperature/extracted_eval_results"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

with open(CASE_FILTERS_PATH, "r", encoding="utf-8") as f:
    filters = json.load(f)

filter_set = {(f["case_id"], f["similarity_metric"], f["threshold"]) for f in filters}
collected = {}

# Loop over all result files
for filepath in glob.glob(f"{EVAL_RESULTS_DIR}/results_temp_*.jsonl"):
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                key = (entry.get("case_id"), entry.get("similarity_metric"), entry.get("threshold"))
                if key in filter_set:
                    collected.setdefault(entry["case_id"], []).append(entry)
            except Exception as e:
                print(f"Error parsing line in {filepath}: {e}")

for case_id, entries in collected.items():
    out_path = Path(OUTPUT_DIR) / f"{case_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(entries)} entries for case: {case_id}")

print(f"\nDone. Extracted {sum(len(v) for v in collected.values())} entries across {len(collected)} cases.")
