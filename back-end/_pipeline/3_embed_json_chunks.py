import os
import json
import torch
import numpy as np
from uuid import uuid4
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE = os.environ["SUPABASE_SERVICE_ROLE"]
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
CHUNKS_FILE = "../_data/chunks.jsonl"

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)

texts = []
metas = []
ecli_ids = []

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        text = record["text"]
        ecli = record.get("ecli", "")
        meta = record.get("metadata", {})

        # Format input for E5 model
        texts.append(f"passage: {text}")
        ecli_ids.append(ecli)
        metas.append(meta)

print(f"Encoding {len(texts)} chunks...")

embeddings = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("Uploading to Supabase...")
rows = []
for emb, text, meta, ecli in zip(embeddings, texts, metas, ecli_ids):
    meta["ecli"] = ecli

    row = {
        "ecli": ecli, 
        "content": text.replace("passage: ", ""),
        "metadata": meta, 
        "embedding": emb.tolist()
    }
    rows.append(row)

# Batch insert (up to 500 rows per call to avoid limits)
batch_size = 500
total_uploaded = 0

for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    try:
        response = supabase.table("case_chunks").insert(batch).execute()
        print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} rows")
        total_uploaded += len(batch)
    except Exception as e:
        print(f"Error uploading batch {i//batch_size + 1}: {e}")
        
print(f"Upload complete. Total uploaded: {total_uploaded} chunks")

# Verify count in database
try:
    count_response = supabase.table("case_chunks").select("id", count="exact").execute()
    db_count = count_response.count
    print(f"Database now contains: {db_count} total chunks")
except Exception as e:
    print(f"Could not verify database count: {e}")