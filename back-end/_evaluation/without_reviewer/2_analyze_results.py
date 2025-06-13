import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

RESULTS_PATH = "./results/results.jsonl"
SUMMARY_JSON = "./results/results_summary.json"
HEATMAP_DIR = Path("heatmaps")
HEATMAP_DIR.mkdir(parents=True, exist_ok=True)

records = []
with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        flat = {
            "case_id": item["case_id"],
            "similarity_metric": item["similarity_metric"],
            "threshold": float(item["threshold"]),
        }
        flat.update(item["evaluation"])
        records.append(flat)

df = pd.DataFrame(records)
df["hallucinated"] = df["hallucinated"].astype(int)

summary = df.groupby(["similarity_metric", "threshold"]).agg({
    "citation_precision": "mean",
    "citation_recall": "mean",
    "fabricated_eclis": "mean",
    "ungrounded_statements": "mean",
    "ungrounded_ratio": "mean",
    "hallucinated": "mean"
}).reset_index()

def compute_f1(row):
    p, r = row["citation_precision"], row["citation_recall"]
    return 2 * p * r / (p + r) if (p + r) > 0 else 0

summary["f1_score"] = summary.apply(compute_f1, axis=1)

best_precision = summary.sort_values("citation_precision", ascending=False).iloc[0]
best_recall = summary.sort_values("citation_recall", ascending=False).iloc[0]
lowest_hallucination = summary.sort_values("hallucinated", ascending=True).iloc[0]
best_f1 = summary.sort_values("f1_score", ascending=False).iloc[0]

print(f"Best Precision: {best_precision['similarity_metric']} @ {best_precision['threshold']} ({best_precision['citation_precision']:.2f})")
print(f"Best Recall: {best_recall['similarity_metric']} @ {best_recall['threshold']} ({best_recall['citation_recall']:.2f})")
print(f"Lowest Hallucination Rate: {lowest_hallucination['similarity_metric']} @ {lowest_hallucination['threshold']} ({lowest_hallucination['hallucinated']:.2f})")
print(f"Best Balanced (F1): {best_f1['similarity_metric']} @ {best_f1['threshold']} (F1 = {best_f1['f1_score']:.2f})")

metadata = {
    "best_precision": {
        "metric": best_precision["similarity_metric"],
        "threshold": best_precision["threshold"],
        "value": round(best_precision["citation_precision"], 2)
    },
    "best_recall": {
        "metric": best_recall["similarity_metric"],
        "threshold": best_recall["threshold"],
        "value": round(best_recall["citation_recall"], 2)
    },
    "lowest_hallucination_rate": {
        "metric": lowest_hallucination["similarity_metric"],
        "threshold": lowest_hallucination["threshold"],
        "value": round(lowest_hallucination["hallucinated"], 2)
    },
    "best_f1_score": {
        "metric": best_f1["similarity_metric"],
        "threshold": best_f1["threshold"],
        "value": round(best_f1["f1_score"], 2)
    }
}

# Full JSON structure
summary_json = {
    "metadataW": metadata,
    "results": summary.to_dict(orient="records")
}

# Save to file
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(summary_json, f, indent=2)

def plot_heatmap(metric, title):
    pivot = df.pivot_table(values=metric, index="similarity_metric", columns="threshold", aggfunc="mean")
    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={"label": metric})
    plt.title(title)
    plt.xlabel("Threshold")
    plt.ylabel("Similarity Metric")
    plt.tight_layout()
    plt.savefig(HEATMAP_DIR / f"{metric}.png")
    plt.close()

for metric in ["citation_precision", "citation_recall", "ungrounded_ratio", "fabricated_eclis", "hallucinated"]:
    plot_heatmap(metric, f"Average {metric.replace('_', ' ').title()}")

# Plot f1_score separately from `summary` DataFrame
pivot_f1 = summary.pivot_table(values="f1_score", index="similarity_metric", columns="threshold")
plt.figure(figsize=(8, 5))
sns.heatmap(pivot_f1, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={"label": "F1 Score"})
plt.title("Average F1 Score")
plt.xlabel("Threshold")
plt.ylabel("Similarity Metric")
plt.tight_layout()
plt.savefig(HEATMAP_DIR / "f1_score.png")
plt.close()


