from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.retrieval import query_knowledge_base

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    try:
        response = query_knowledge_base(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
