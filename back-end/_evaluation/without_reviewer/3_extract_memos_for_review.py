import json
import random
from pathlib import Path

RESULTS_PATH = Path("./results/results.jsonl")
OUTPUT_PATH = Path("sampled_memo_reviews.json")
NUM_MEMOS = 5
THRESHOLDS = [0.7, 0.9]
METRICS = ["cosine", "dot", "euclidean"]

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    all_entries = [json.loads(line) for line in f]

cases = {}
for entry in all_entries:
    cid = entry["case_id"]
    cases.setdefault(cid, []).append(entry)

selected_case_ids = random.sample(list(cases.keys()), NUM_MEMOS)

filtered = []
for cid in selected_case_ids:
    for entry in cases[cid]:
        metric = entry.get("similarity_metric")
        threshold = float(entry.get("threshold", 0.0))
        if metric in METRICS and threshold in THRESHOLDS:
            evaluation = entry["evaluation"]
            filtered.append({
                "case_id": cid,
                "similarity_metric": metric,
                "threshold": threshold,
                "hallucinated": evaluation.get("hallucinated", False),
                "ungrounded_sentences": evaluation.get("ungrounded_sentences", []),
                "memo": entry["memo"],
                "chunks": entry["chunks"]
            })

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2, ensure_ascii=False)

print(f"Saved {len(filtered)} evaluation cases to: {OUTPUT_PATH}")
