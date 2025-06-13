import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

WITH_REVIEW_FILE = Path("./test-case-12-reviewed-gpt.json")
WITHOUT_REVIEW_FILE = Path("./test-case-12-reviewed-claude.json")

def load_eval_data(path, label):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sentence_rows = []
    for entry in data:
        case_id = entry["case_id"]
        auto_flag = bool(entry["hallucinated_by_eval"])
        for verdict_entry in entry["gpt4_structured_verdicts"]:
            sentence = verdict_entry["sentence"]
            gpt_flag = verdict_entry["verdict"]["is_hallucinated"]
            sentence_rows.append({
                "case_id": case_id,
                "sentence": sentence,
                "auto_flag": auto_flag,
                "gpt_flag": gpt_flag,
                "disagreement": auto_flag != gpt_flag,
                "eval_type": label
            })
    return pd.DataFrame(sentence_rows)

df_with = load_eval_data(WITH_REVIEW_FILE, "GPT-4.1 Reviewer")
df_without = load_eval_data(WITHOUT_REVIEW_FILE, "Claude Reviewer")
df_all = pd.concat([df_with, df_without])

summary = (
    df_all
    .groupby(["eval_type", "disagreement"])
    .size()
    .reset_index(name="count")
)

# Add total per eval_type
total_counts = df_all.groupby("eval_type").size().reset_index(name="total")
summary = summary.merge(total_counts, on="eval_type")
summary["percent"] = (summary["count"] / summary["total"]) * 100
summary["category"] = summary["disagreement"].map({True: "Disagreement", False: "Agreement"})

plt.figure(figsize=(9, 6))
ax = sns.barplot(
    data=summary,
    x="category",
    y="percent",
    hue="eval_type",
    palette=["#4E79A7", "#F28E2B"]
)

# Annotate with % + count (e.g., "42.1% (34/81)")
for bar, (_, row) in zip(ax.patches, summary.iterrows()):
    percent = row["percent"]
    count = row["count"]
    total = row["total"]
    label = f"{percent:.1f}%\n({count}/{total})"
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        label,
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold"
    )

plt.title("Relative Agreement vs Disagreement (% of Sentences)\nGPT-4.1 Case 12 vs Claude Case 12")
plt.ylabel("Percentage of Sentences")
plt.xlabel("Evaluation Outcome")
plt.ylim(0, 100)
plt.legend(title="Evaluation Type")
plt.tight_layout()
plt.savefig("relative_agreement_with_gpt_claude_12.png")
plt.show()
