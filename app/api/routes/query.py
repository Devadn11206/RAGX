from fastapi import APIRouter, Depends
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import rag_service
from app.security.auth import get_current_user
from app.security.models import User

router = APIRouter()

@router.post("", response_model=QueryResponse)
async def process_query(req: QueryRequest, current_user: User = Depends(get_current_user)):
    return await rag_service.process_query(req.query, current_user, req.top_k, mode=req.retrieval_mode)
