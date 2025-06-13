import os
import json
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from transformers import AutoTokenizer

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
SUPABASE_TABLE = "case_chunks"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-large")
LOCAL_CHUNKS_FILE = "../_data/chunks.jsonl"

#Helpers
def extract_year_quarter(date_str, fallback_quarter=None):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    except:
        return fallback_quarter

def validate_chunks(chunks, source_name=""):
    year_quarter_dist = Counter()
    missing_fields = Counter()
    token_lengths = []
    section_counts = Counter()
    ecli_seen = set()

    for chunk in chunks:
        try:
            meta = chunk.get("metadata", {})
            ecli = chunk.get("ecli", "")
            text = chunk.get("text", "")

            # Check required metadata fields
            for field in ["title", "procedure", "subject", "court", "section"]:
                if not meta.get(field):
                    missing_fields[field] += 1
            if not text.strip():
                missing_fields["empty_text"] += 1

            section_counts[meta.get("section", "UNKNOWN")] += 1
            token_lengths.append(len(tokenizer.tokenize(text)))

            # Count year/quarter only once per unique ECLI
            if ecli not in ecli_seen:
                ecli_seen.add(ecli)
                date = meta.get("date")
                quarter_num = meta.get("quarter")
                quarter_str = extract_year_quarter(date, fallback_quarter=f"UNKNOWN-Q{quarter_num}" if quarter_num else None)
                if quarter_str:
                    year_quarter_dist[quarter_str] += 1
                else:
                    missing_fields["quarter_parse_fail"] += 1

        except Exception as ex:
            print(f"[{source_name}] Failed to process chunk: {ex}")
            missing_fields["json_load_fail"] += 1

    print(f"\n{source_name} Validation")
    print(f"Total chunks: {len(token_lengths)}")
    print(f"Average tokens per chunk: {sum(token_lengths) // max(1, len(token_lengths))}")
    print(f"Chunks under 50 tokens: {sum(1 for t in token_lengths if t < 50)}")
    print(f"Chunks over 512 tokens: {sum(1 for t in token_lengths if t > 512)}")

    print("Year/Quarter distribution:")
    for k, v in sorted(year_quarter_dist.items()):
        print(f"  {k}: {v}")
    print("\nMissing fields:")
    for k, v in missing_fields.items():
        print(f"  {k}: {v}")
    print("\nTop sections:")
    for section, count in section_counts.most_common(10):
        print(f"  {section}: {count}")

print("Loading local chunks...")
with open(LOCAL_CHUNKS_FILE, "r", encoding="utf-8") as f:
    local_chunks = [json.loads(line) for line in f]

validate_chunks(local_chunks, source_name="Local")

print("\nFetching remote chunks from Supabase...")
try:
    page_size = 1000
    offset = 0
    all_chunks = []

    while True:
        print(f"Fetching rows {offset}–{offset + page_size - 1}...")
        response = supabase.table(SUPABASE_TABLE).select("*").range(offset, offset + page_size - 1).execute()
        batch = response.data
        if not batch:
            break
        all_chunks.extend(batch)
        offset += page_size

    formatted_remote_chunks = []
    for c in all_chunks:
        meta = c.get("metadata") or {}
        formatted_remote_chunks.append({
            "ecli": c.get("ecli", ""),
            "text": c.get("content", ""),
            "metadata": {
                "title": meta.get("title", ""),
                "procedure": meta.get("procedure", ""),
                "subject": meta.get("subject", ""),
                "court": meta.get("court", ""),
                "section": meta.get("section", ""),
                "date": meta.get("date", ""),
                "quarter": meta.get("quarter", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "sub_chunk_index": meta.get("sub_chunk_index", 0),
            }
        })

    validate_chunks(formatted_remote_chunks, source_name="Supabase")

except Exception as e:
    print(f"Supabase fetch failed: {e}")
