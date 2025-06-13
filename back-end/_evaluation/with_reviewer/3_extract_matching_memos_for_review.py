import json
from pathlib import Path

ORIGINAL_SAMPLE_PATH = Path("../without_reviewer/sampled_memo_evaluations.json")
REVIEWED_RESULTS_PATH = Path("./results/results.jsonl")
OUTPUT_PATH = Path("./sampled_reviewed_memo_evaluations.json")

with open(ORIGINAL_SAMPLE_PATH, "r", encoding="utf-8") as f:
    sampled = json.load(f)

sample_keys = set(
    (item["case_id"], item["similarity_metric"], float(item["threshold"]))
    for item in sampled
)

with open(REVIEWED_RESULTS_PATH, "r", encoding="utf-8") as f:
    reviewed_entries = [json.loads(line) for line in f]

matching = []
for entry in reviewed_entries:
    key = (entry["case_id"], entry["similarity_metric"], float(entry["threshold"]))
    if key in sample_keys:
        matching.append({
            "case_id": entry["case_id"],
            "similarity_metric": entry["similarity_metric"],
            "threshold": float(entry["threshold"]),
            "hallucinated": entry["evaluation"].get("hallucinated", False),
            "ungrounded_sentences": entry["evaluation"].get("ungrounded_sentences", []),
            "memo": entry["memo_refined"],
            "chunks": entry["chunks"]
        })

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(matching, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(matching)} matching reviewed memos to: {OUTPUT_PATH}")
