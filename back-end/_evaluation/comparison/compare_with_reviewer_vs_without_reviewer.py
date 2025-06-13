import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

ORIGINAL_RESULTS_PATH = "./with_reviewer/results/results.jsonl"
REVIEWED_RESULTS_PATH = "./without_reviewer/results/results.jsonl"
COMPARE_DIR = Path("comparison_outputs")
COMPARE_DIR.mkdir(parents=True, exist_ok=True)

def load_results(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            flat = {
                "case_id": item["case_id"],
                "similarity_metric": item["similarity_metric"],
                "threshold": float(item["threshold"]),
            }
            flat.update(item["evaluation"])
            records.append(flat)
    return pd.DataFrame(records)

df_orig = load_results(ORIGINAL_RESULTS_PATH)
df_reviewed = load_results(REVIEWED_RESULTS_PATH)

# Add identifier for merging
df_orig["source"] = "original"
df_reviewed["source"] = "reviewed"

merge_keys = ["case_id", "similarity_metric", "threshold"]
combined = pd.merge(
    df_orig,
    df_reviewed,
    on=merge_keys,
    suffixes=("_orig", "_reviewed")
)

# Compute deltas
combined["delta_precision"] = combined["citation_precision_reviewed"] - combined["citation_precision_orig"]
combined["delta_recall"] = combined["citation_recall_reviewed"] - combined["citation_recall_orig"]
combined["delta_hallucination"] = combined["hallucinated_reviewed"].astype(int) - combined["hallucinated_orig"].astype(int)
combined["delta_ungrounded_ratio"] = combined["ungrounded_ratio_reviewed"] - combined["ungrounded_ratio_orig"]

def f1(p, r):
    return 2 * p * r / (p + r) if (p + r) > 0 else 0

combined["f1_orig"] = combined.apply(lambda row: f1(row["citation_precision_orig"], row["citation_recall_orig"]), axis=1)
combined["f1_reviewed"] = combined.apply(lambda row: f1(row["citation_precision_reviewed"], row["citation_recall_reviewed"]), axis=1)
combined["delta_f1"] = combined["f1_reviewed"] - combined["f1_orig"]

json_records = combined.to_dict(orient="records")
with open(COMPARE_DIR / "llm_review_comparison.json", "w", encoding="utf-8") as f:
    json.dump(json_records, f, indent=2)

agg = combined.groupby(["similarity_metric", "threshold"]).agg({
    "delta_precision": "mean",
    "delta_recall": "mean",
    "delta_hallucination": "mean",
    "delta_ungrounded_ratio": "mean",
    "delta_f1": "mean"
}).reset_index()

def plot_metric(metric, ylabel):
    plt.figure(figsize=(8, 5))
    pivot = agg.pivot(index="similarity_metric", columns="threshold", values=metric)
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="RdYlGn", center=0, cbar_kws={"label": f"Δ {ylabel}"})
    plt.title(f"LLM Review Impact on {ylabel}")
    plt.xlabel("Threshold")
    plt.ylabel("Similarity Metric")
    plt.tight_layout()
    plt.savefig(COMPARE_DIR / f"{metric}_heatmap.png")
    plt.close()

for m, label in [
    ("delta_precision", "Citation Precision"),
    ("delta_recall", "Citation Recall"),
    ("delta_hallucination", "Hallucination Rate"),
    ("delta_ungrounded_ratio", "Ungrounded Ratio"),
    ("delta_f1", "F1 Score")
]:
    plot_metric(m, label)

summary = {}

summary["average_deltas"] = {
    "delta_precision": round(combined["delta_precision"].mean(), 4),
    "delta_recall": round(combined["delta_recall"].mean(), 4),
    "delta_hallucination": round(combined["delta_hallucination"].mean(), 4),
    "delta_ungrounded_ratio": round(combined["delta_ungrounded_ratio"].mean(), 4),
    "delta_f1": round(combined["delta_f1"].mean(), 4),
}

# Count of improvement/worsening
def count_delta_change(df, col):
    return {
        "improved": int((df[col] > 0).sum()),
        "worsened": int((df[col] < 0).sum()),
        "unchanged": int((df[col] == 0).sum())
    }

summary["delta_change_counts"] = {
    "citation_precision": count_delta_change(combined, "delta_precision"),
    "citation_recall": count_delta_change(combined, "delta_recall"),
    "hallucination_rate": count_delta_change(combined, "delta_hallucination"),
    "ungrounded_ratio": count_delta_change(combined, "delta_ungrounded_ratio"),
    "f1_score": count_delta_change(combined, "delta_f1"),
}

# Best-performing similarity/threshold config
best_config = agg.sort_values("delta_f1", ascending=False).iloc[0]
summary["best_config_by_f1_gain"] = {
    "similarity_metric": best_config["similarity_metric"],
    "threshold": best_config["threshold"],
    "delta_f1": round(best_config["delta_f1"], 4),
    "delta_precision": round(best_config["delta_precision"], 4),
    "delta_recall": round(best_config["delta_recall"], 4),
    "delta_hallucination": round(best_config["delta_hallucination"], 4),
}

# Save summary
with open(COMPARE_DIR / "llm_review_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("Comparison complete.")
print(f"- Per-case JSON:  {COMPARE_DIR / 'llm_review_comparison.json'}")
print(f"- Summary JSON:   {COMPARE_DIR / 'llm_review_summary.json'}")
print(f"- Heatmaps:       {COMPARE_DIR}/*_heatmap.png")

