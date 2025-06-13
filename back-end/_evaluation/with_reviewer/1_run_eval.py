import json
import time
import httpx
from datetime import datetime
import subprocess

__SCRIPT_VERSION__ = "eval_refined_v1.0.0"

def get_git_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"

API_BASE = "http://localhost:8000"
PREDEFINED_MEMOS = "../without_reviewer/results/all_memos.json"  
OUTPUT_FILE = "./results/results.jsonl"
REFINED_MEMOS_FILE = "./results/all_refined_memos.json"
refined_memos = []
METRICS = ["cosine", "dot", "euclidean"]
THRESHOLDS = [0.6, 0.7, 0.8, 0.9]

with open(PREDEFINED_MEMOS, "r", encoding="utf-8") as f:
    predefined_memos = json.load(f)

seen_case_ids = set()
client = httpx.Client(timeout=httpx.Timeout(120.0, read=120.0))
results = []
print(f"Running reviewed memo evaluation script version: {__SCRIPT_VERSION__}")
print(f"Git commit: {get_git_commit_hash()}")

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
        print(f"\nRefining memo for case: {case_id}")
        refine_resp = client.post(f"{API_BASE}/refine-existing-memo", json={
            "memo": memo_raw,
            "chunks": chunks,
        })
        refine_resp.raise_for_status()
        refined_data = refine_resp.json()

        memo_refined = refined_data.get("memo_refined")

        refined_memos.append({
            "case_id": case_id,
            "created_at": original_created_at,
            "refined_at": datetime.utcnow().isoformat(),
            "memo": memo_refined,
            "form_data": entry.get("form_data"),  
            "chunks": chunks
        })

        if not memo_refined:
            print(f"No refined memo returned for {case_id}")
            continue

        for metric in METRICS:
            for threshold in THRESHOLDS:
                print(f"Evaluating {metric} @ {threshold}")
                eval_payload = {
                    "memo": memo_refined,
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
                    "original_created_at": original_created_at,
                    "evaluated_at": datetime.utcnow().isoformat(),
                    "memo_raw": memo_raw,
                    "memo_refined": memo_refined,
                    "chunks": chunks,
                    "evaluation": evaluation,
                    "similarity_metric": metric,
                    "threshold": threshold,
                    "script_version": __SCRIPT_VERSION__,
                    "git_commit": get_git_commit_hash()
                }

                with open(OUTPUT_FILE, "a", encoding="utf-8") as fout:
                    fout.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

                results.append(log_entry)
                time.sleep(0.5)

    except Exception as e:
        print(f"Failed for case {case_id}: {e}")
        continue

with open(REFINED_MEMOS_FILE, "w", encoding="utf-8") as f:
    json.dump(refined_memos, f, ensure_ascii=False, indent=2)
print(f"Saved all refined memos to: {REFINED_MEMOS_FILE}")
print(f"\nFinished evaluating {len(predefined_memos)} cases → {len(results)} total evaluations.")
