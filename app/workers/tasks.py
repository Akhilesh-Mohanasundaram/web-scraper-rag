import asyncio
import sys
from asgiref.sync import async_to_sync
from celery import shared_task
from app.services.search_service import search_service
from app.services.scraper_service import scraper_service

# FIX: Windows Event Loop Policy for Celery Worker
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@shared_task(bind=True, name="ingest_pipeline")
def ingest_pipeline_task(self, query: str, num_results: int):
    """
    Celery task that:
    1. Searches Google for URLs.
    2. Scrapes those URLs using Playwright.
    3. Returns the raw data (Phase 3 will inject this into Neo4j).
    """
    try:
        # Step 1: Search (Async wrapped in Sync)
        search_results = async_to_sync(search_service.search)(query, num_results)
        urls = [item.link for item in search_results]
        
        if not urls:
            return {"status": "failed", "reason": "No URLs found"}

        # Step 2: Scrape (Async wrapped in Sync)
        scrape_results = async_to_sync(scraper_service.scrape_urls)(urls)
        
        # Convert Pydantic models to JSON-serializable dicts
        results_json = [
            {
                "url": res.url, 
                "title": res.title, 
                "content_preview": res.content[:200] + "..." # Truncate for log readability
            } 
            for res in scrape_results
        ]

        return {
            "status": "completed",
            "query": query,
            "scraped_count": len(results_json),
            "data": results_json
        }

    except Exception as e:
        # Log the error and re-raise so Celery marks it as FAILED
        print(f"Task Failed: {str(e)}")
        raise e