import json
import time
import httpx
from datetime import datetime, timezone
import subprocess
import os

API_BASE = "http://localhost:8000"
PREDEFINED_MEMOS = "../without_reviewer/results/all_memos.json"
RESULTS_DIR = "./results/claude_temperature"
TEMPERATURES = [0.02, 0.5, 0.05, 0.7, 0.9] 
METRICS = ["cosine", "dot", "euclidean"]
THRESHOLDS = [0.6, 0.7, 0.8, 0.9]
os.makedirs(RESULTS_DIR, exist_ok=True)

__SCRIPT_VERSION__ = "temp_eval_v1.0.0"

def get_git_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"
    
model_choice = input("\nChoose reviewer model (1 = ChatGPT / 2 = Claude): ").strip()
if model_choice == "2":
    MODEL_NAME = "claude-4-sonnet"
else:
    MODEL_NAME = "gpt-4.1"
print(f"→ Using reviewer model: {MODEL_NAME}")

with open(PREDEFINED_MEMOS, "r", encoding="utf-8") as f:
    predefined_memos = json.load(f)

client = httpx.Client(timeout=httpx.Timeout(120.0, read=120.0))

for temp in TEMPERATURES:
    print(f"\nRunning temperature: {temp}")
    refined_memos = []
    results = []
    output_file = f"{RESULTS_DIR}/eval_results/results_temp_{temp}.jsonl"
    refined_file = f"{RESULTS_DIR}/memos/refined_memos_temp_{temp}.json"

    seen_case_ids = set()

    for entry in predefined_memos:
        case_id = entry.get("case_id")
        if case_id in seen_case_ids:
            continue
        seen_case_ids.add(case_id)

        memo_raw = entry.get("memo")
        chunks = entry.get("chunks")
        original_created_at = entry.get("created_at")

        if not memo_raw or not chunks:
            print(f"Skipping case {case_id}: missing memo or chunks.")
            continue

        try:
            print(f"\nRefining case {case_id} with T={temp} and model {MODEL_NAME}")
            refine_resp = client.post(f"{API_BASE}/refine-existing-memo", json={
                "memo": memo_raw,
                "chunks": chunks,
                "temperature": temp,
                "model": MODEL_NAME
            })
            refine_resp.raise_for_status()
            memo_refined = refine_resp.json().get("memo_refined")

            if not memo_refined:
                print(f"No refined memo for case {case_id}")
                continue

            refined_entry = {
                "case_id": case_id,
                "created_at": original_created_at,
                "refined_at": datetime.now(timezone.utc).isoformat(),
                "temperature": temp,
                "model": MODEL_NAME,
                "memo": memo_refined,
                "form_data": entry.get("form_data"),
                "chunks": chunks
            }
            refined_memos.append(refined_entry)

            for metric in METRICS:
                for threshold in THRESHOLDS:
                    print(f"Evaluating {metric} @ {threshold}")
                    eval_resp = client.post(
                        f"{API_BASE}/evaluate-memo?similarity_metric={metric}&threshold={threshold}",
                        json={"memo": memo_refined, "chunks": chunks}
                    )
                    eval_resp.raise_for_status()
                    evaluation = eval_resp.json()

                    log_entry = {
                        "case_id": case_id,
                        "created_at": original_created_at,
                        "evaluated_at": datetime.now(timezone.utc).isoformat(),
                        "temperature": temp,
                        "model": MODEL_NAME,
                        "memo_refined": memo_refined,
                        "chunks": chunks,
                        "evaluation": evaluation,
                        "similarity_metric": metric,
                        "threshold": threshold,
                        "script_version": __SCRIPT_VERSION__,
                        "git_commit": get_git_commit_hash()
                    }
                    with open(output_file, "a", encoding="utf-8") as fout:
                        fout.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

                    results.append(log_entry)
                    time.sleep(0.5)

        except Exception as e:
            print(f"Error processing case {case_id} at T={temp}: {e}")

    with open(refined_file, "w", encoding="utf-8") as f:
        json.dump(refined_memos, f, ensure_ascii=False, indent=2)

    print(f"Saved refined memos for T={temp} to {refined_file}")
    print(f"Total evaluations for T={temp}: {len(results)}")
