from fastapi import APIRouter, HTTPException
from app.schemas.search import SearchResponse
from app.services.search_service import search_service

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def perform_search(query: str, num_results: int = 10):
    try:
        results = await search_service.search(query, num_results)
        return SearchResponse(query=query, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))