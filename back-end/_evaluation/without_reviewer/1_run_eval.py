import json
import time
import httpx
from datetime import datetime
import subprocess
import os

__SCRIPT_VERSION__ = "eval_v1.0.0"

def get_git_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"

API_BASE = "http://localhost:8000"
PREDEFINED_CASES_FILE = "../data/0_input_cases.json"
EVAL_OUTPUT_FILE = "./results/results.jsonl"
MEMO_OUTPUT_FILE = "./results/all_memos.json"
METRICS = ["cosine", "dot", "euclidean"]
THRESHOLDS = [0.6, 0.7, 0.8, 0.9]

os.makedirs(os.path.dirname(EVAL_OUTPUT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(MEMO_OUTPUT_FILE), exist_ok=True)

with open(PREDEFINED_CASES_FILE, "r", encoding="utf-8") as f:
    cases = json.load(f)

client = httpx.Client(timeout=httpx.Timeout(120.0, read=120.0))

results = []
memo_entries = []

print(f"Running evaluation script version: {__SCRIPT_VERSION__}")
print(f"Git commit: {get_git_commit_hash()}")

for case in cases:
    form_data = case["formData"]
    case_id = case["id"]

    print(f"Generating memo for case: {case_id}")
    try:
        resp = client.post(f"{API_BASE}/generate-memo", json=form_data)
        resp.raise_for_status()
        result = resp.json()
        memo_text = result["memo"]
        chunks = result["chunks"]

        # Collect memo entry
        memo_entries.append({
            "case_id": case_id,
            "created_at": datetime.utcnow().isoformat(),
            "memo": memo_text,
            "form_data": form_data,
            "chunks": chunks
        })

        for metric in METRICS:
            for threshold in THRESHOLDS:
                print(f"Evaluating with {metric} @ threshold={threshold}")
                eval_payload = {
                    "memo": memo_text,
                    "chunks": chunks
                }
                eval_resp = client.post(
                    f"{API_BASE}/evaluate-memo?similarity_metric={metric}&threshold={threshold}",
                    json=eval_payload
                )
                eval_resp.raise_for_status()
                evaluation = eval_resp.json()

                log_entry = {
                    "case_id": case_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "memo": memo_text,
                    "chunks": chunks,
                    "evaluation": evaluation,
                    "similarity_metric": metric,
                    "threshold": threshold,
                    "script_version": __SCRIPT_VERSION__,
                    "git_commit": get_git_commit_hash()
                }

                with open(EVAL_OUTPUT_FILE, "a", encoding="utf-8") as fout:
                    fout.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

                results.append(log_entry)
                time.sleep(0.5)

    except Exception as e:
        print(f"Failed for case {case_id}: {e}")
        continue

# Save all memos to a single JSON file
with open(MEMO_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(memo_entries, f, ensure_ascii=False, indent=2)

print(f"\nFinished evaluating {len(cases)} cases with {len(results)} total evaluations.")
print(f"Saved all memos to: {MEMO_OUTPUT_FILE}")
