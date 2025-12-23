from fastapi import APIRouter, HTTPException
from app.schemas.scrape import ScrapeRequest, ScrapeResult
from app.services.scraper_service import scraper_service

router = APIRouter()

@router.post("/scrape", response_model=list[ScrapeResult])
async def scrape_urls(request: ScrapeRequest):
    """
    Accepts a list of URLs and returns cleaned text content.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="List of URLs cannot be empty")
    
    results = await scraper_service.scrape_urls(request.urls)
    return results