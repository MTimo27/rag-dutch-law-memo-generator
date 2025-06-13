from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.rag import supabase
from app.models import MemoRequest
from app.prompt import build_query, build_prompt
from app.rag import embed_query, retrieve_chunks, generate_memo
from app.evaluation import evaluate_memo
from fastapi import Body, HTTPException
from app.env import get_memo_table_name
from datetime import datetime
from fastapi import Query
from app.rag import refine_memo

# Initialize FastAPI and limiter
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "https://memo-generator.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-memo")
@limiter.limit("5/minute")  # Limit each IP to 5 requests per minute
def generate_legal_memo(payload: MemoRequest, request: Request):
    query = build_query(payload.model_dump())
    vector = embed_query(query)
    chunks = retrieve_chunks(vector, top_k=6, max_per_ecli=2)
    full_prompt = build_prompt(query, chunks)
    memo = generate_memo(full_prompt)
    return {"memo": memo, "chunks": chunks}

@app.post("/refine-existing-memo")
@limiter.limit("5/minute")
def refine_existing_memo(request: Request, payload: dict = Body(...)):
    memo_raw = payload.get("memo")
    chunks = payload.get("chunks")
    
    if not memo_raw or not chunks:
        raise HTTPException(status_code=400, detail="Missing memo or chunks")

    try:
        memo_refined = refine_memo(memo_raw, chunks)
        return {"memo_refined": memo_refined, "chunks": chunks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")

@app.get("/get-all-chunks")
def list_all_chunks(limit: int = Query(1000, ge=1, le=1000), offset: int = Query(0, ge=0)):
    try:
        # Fetch rows using Supabase pagination
        response = supabase.table("case_chunks") \
            .select("content, metadata") \
            .range(offset, offset + limit - 1) \
            .execute()

        formatted = []
        for row in response.data:
            metadata = row.get("metadata", {})
            title = metadata.get("title", "")
            ecli = metadata.get("ecli") or (title.split()[0] if title else "UNKNOWN")

            formatted.append({
                "ecli": ecli,
                "metadata": metadata,
                "text": row.get("content", "")
            })

        return {
            "total_chunks": len(formatted),
            "chunks": formatted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/save-memo")
async def save_memo(request: Request):
    body = await request.json()
    memo_id = body["id"]
    table_name = get_memo_table_name()

    # Check if memo exists
    existing = supabase.table(table_name).select("id").eq("id", memo_id).execute()
    if existing.data:
        supabase.table(table_name).update({
            "content": body["content"],
            "form_data": body["formData"],
            "chunks": body["chunks"],
            "feedback": body["feedback"],
            "updated_at": body.get("updatedAt"),
        }).eq("id", memo_id).execute()
    else:
        supabase.table(table_name).insert({
            "id": memo_id,
            "content": body["content"],
            "form_data": body["formData"],
            "chunks": body["chunks"],
            "feedback": body["feedback"],
            "created_at": body["createdAt"],
        }).execute()

    return { "id": memo_id }

@app.post("/evaluate-memo")
def evaluate_generated_memo(
    payload: dict = Body(...),
    similarity_metric: str = Query(
        "cosine",
        enum=["cosine", "dot", "euclidean"],
        description="Similarity metric to use for sentence grounding"
    ),
    threshold: float = Query(
        0.70,
        ge=0.0,
        le=1.0,
        description="Threshold for similarity to consider a sentence grounded"
    )
):
    memo = payload.get("memo", "")
    chunks = payload.get("chunks", [])

    if not memo or not chunks:
        raise HTTPException(status_code=400, detail="Missing memo or chunks")

    try:
        # Run evaluation
        evaluation = evaluate_memo(
            memo=memo,
            chunks=chunks,
            threshold=threshold,
            similarity_metric=similarity_metric
        )

        # Prepare and insert into Supabase
        log_entry = {
            "memo": memo,
            "chunks": chunks,
            "evaluation": evaluation,
            "similarity_metric": similarity_metric,
            "threshold": threshold,
            "created_at": datetime.utcnow().isoformat()
        }

        response = supabase.table("evaluation_logs").insert(log_entry).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save evaluation to Supabase.")

        return evaluation

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/evaluation-logs")
def list_evaluation_logs(limit: int = 100):
    try:
        response = supabase.table("evaluation_logs") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))