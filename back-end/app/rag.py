import numpy as np
import httpx
import certifi
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic 
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from supabase import create_client
import os
import requests
from collections import defaultdict
from app.prompt import build_reviewer_prompt

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
http_client = httpx.Client(verify=certifi.where())

DEEP_INFRA_API_TOKEN = os.getenv("DEEP_INFRA_API_TOKEN")

DEEP_INFRA_URL = "https://api.deepinfra.com/v1/openai/embeddings"
DEEP_INFRA_HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {DEEP_INFRA_API_TOKEN}",
    "Content-Type": "application/json",
}

def embed_query(text: str) -> np.ndarray:
    payload = {
        "input": f"query: {text}",
        "model": "intfloat/multilingual-e5-large",
        "encoding_format": "float"
    }

    response = requests.post(DEEP_INFRA_URL, headers=DEEP_INFRA_HEADERS, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Deep Infra embedding API failed: {response.text}")

    try:
        data = response.json()
        embedding = data["data"][0]["embedding"]
        return np.array(embedding, dtype=np.float32)
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected response structure: {response.text}") from e
    
def embed_batch(texts: list[str]) -> list[np.ndarray]:
    payload = {
        "input": [f"passage: {t}" for t in texts],
        "model": "intfloat/multilingual-e5-large",
        "encoding_format": "float"
    }

    response = requests.post(DEEP_INFRA_URL, headers=DEEP_INFRA_HEADERS, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Deep Infra embedding API failed: {response.text}")
    # All embeddings were L2-normalized to ensure consistent vector length across similarity metrics, enabling valid comparison between cosine similarity and dot-product scores.

    data = response.json()
    embeddings = [np.array(obj["embedding"], dtype=np.float32) for obj in data["data"]]

    # Normalize all
    normalized = []
    for vec in embeddings:
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        normalized.append(vec)

    return normalized

# Query Supabase for the most similar chunks and return structured entries.
# Limits to `top_k` total, and `max_per_ecli` chunks per ECLI.
def retrieve_chunks(vector: np.ndarray, top_k: int = 6, max_per_ecli: int = 2):
    vector_str = f"[{', '.join(map(str, vector.tolist()))}]"

    try:
        response = supabase.rpc("match_case_chunks", {
            "query_embedding": vector_str,
            "match_threshold": 0.7,
            # We fetch more so we can filter
            "match_count": 50  
        }).execute()

        raw_chunks = response.data
        if not raw_chunks:
            return []

        grouped_by_ecli = defaultdict(list)

        for c in raw_chunks:
            meta = c.get("metadata", {})
            ecli = c.get("ecli") or meta.get("ecli") or meta.get("title", "").split()[0] or "UNKNOWN"
            chunk_entry = {
                "id": c.get("id", "UNKNOWN"),
                "chunk_index": meta.get("chunk_index", -1),
                "sub_chunk_index": meta.get("sub_chunk_index", 0),
                "ecli": ecli,
                "text": c.get("content", ""),
                "similarity": round(c.get("similarity", 0), 4),
                "metadata": meta
            }
            grouped_by_ecli[ecli].append(chunk_entry)

        # Flatten, limiting to max_per_ecli per ECLI
        flattened = []
        for chunks in grouped_by_ecli.values():
            flattened.extend(chunks[:max_per_ecli])

        flattened.sort(key=lambda x: x["similarity"], reverse=True)

        return flattened[:top_k]

    except Exception as e:
        raise RuntimeError(f"Supabase RPC match_case_chunks failed: {str(e)}")

def generate_memo(full_prompt: str) -> str:
    chat = ChatOpenAI(
        model="gpt-4.1",
        temperature=0.2,
        http_client=http_client
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Je bent een juridisch assistent gespecialiseerd in Nederlandse sociale zekerheidszaken. Je schrijft juridisch correcte en duidelijke memo's gebaseerd op gerechtelijke uitspraken."),
        ("user", "{memo_input}")
    ])
    formatted = prompt.invoke({"memo_input": full_prompt})
    return chat.invoke(formatted).content

def refine_memo(draft: str, chunks: list[dict], temperature: float = 0.2, model_name: str = "gpt-4.1") -> str:
    if model_name == "claude-4-sonnet":
        chat = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"]
        )
    else:
        chat = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            http_client=http_client
        )

    full_prompt = build_reviewer_prompt(draft=draft, chunks=chunks)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Je bent een juridisch assistent gespecialiseerd in Nederlandse sociale zekerheidszaken. Je controleert of een memo juridisch correct en goed onderbouwd is."),
        ("user", "{review_input}")
    ])
    formatted = prompt.invoke({"review_input": full_prompt})
    return chat.invoke(formatted).content