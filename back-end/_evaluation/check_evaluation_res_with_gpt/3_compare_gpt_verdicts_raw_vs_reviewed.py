import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

VERDICT_RAW = Path("./without_reviewer/llm_review_evaluation_no_review_step.json")
VERDICT_REVIEWED = Path("./with_reviewer/llm_review_evaluation_with_review_step.json")
OUTPUT_JSON = Path("comparison_outputs/gpt_verdict_change_summary.json")
HEATMAP_IMAGE = Path("comparison_outputs/gpt_verdict_delta_heatmap.png")
Path("comparison_outputs").mkdir(parents=True, exist_ok=True)

def load_majority_flags(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for entry in data:
        key = (entry["case_id"], entry["similarity_metric"], float(entry["threshold"]))
        gpt_flags = [v["verdict"]["is_hallucinated"] for v in entry["gpt4_structured_verdicts"]]
        majority = sum(gpt_flags) > len(gpt_flags) / 2 if gpt_flags else False
        results.append({
            "case_id": entry["case_id"],
            "similarity_metric": entry["similarity_metric"],
            "threshold": float(entry["threshold"]),
            "gpt_hallucinated": majority
        })
    return pd.DataFrame(results)

df_raw = load_majority_flags(VERDICT_RAW).rename(columns={"gpt_hallucinated": "gpt_raw"})
df_reviewed = load_majority_flags(VERDICT_REVIEWED).rename(columns={"gpt_hallucinated": "gpt_reviewed"})

merge_keys = ["case_id", "similarity_metric", "threshold"]
df = pd.merge(df_raw, df_reviewed, on=merge_keys)

df["resolved"] = (df["gpt_raw"] == True) & (df["gpt_reviewed"] == False)
df["regressed"] = (df["gpt_raw"] == False) & (df["gpt_reviewed"] == True)
df["unchanged"] = df["gpt_raw"] == df["gpt_reviewed"]

summary = {
    "total_cases": len(df),
    "resolved_count": int(df["resolved"].sum()),
    "regressed_count": int(df["regressed"].sum()),
    "unchanged_count": int(df["unchanged"].sum()),
    "resolution_rate": round(df["resolved"].sum() / len(df), 3),
    "regression_rate": round(df["regressed"].sum() / len(df), 3),
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump({
        "summary": summary,
        "per_case_deltas": df.to_dict(orient="records")
    }, f, indent=2)

heatmap_data = df.groupby(["similarity_metric", "threshold"])["resolved"].mean().unstack()
plt.figure(figsize=(8, 5))
sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="Greens", cbar_kws={"label": "Resolution Rate"})
plt.title("GPT Verdict Resolution Rate (Raw → Reviewed)")
plt.xlabel("Threshold")
plt.ylabel("Similarity Metric")
plt.tight_layout()
plt.savefig(HEATMAP_IMAGE)
plt.show()

print(f"\nGPT hallucination resolution rate: {summary['resolution_rate']*100:.1f}%")
print(f"Saved: {OUTPUT_JSON}")
print(f"Heatmap: {HEATMAP_IMAGE}")
