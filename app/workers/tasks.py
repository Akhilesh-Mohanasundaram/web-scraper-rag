import asyncio
import sys
from asgiref.sync import async_to_sync
from celery import shared_task
from app.services.search_service import search_service
from app.services.scraper_service import scraper_service
from app.services.graph_service import graph_service  # <--- NEW IMPORT

# Windows Fix
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@shared_task(bind=True, name="ingest_pipeline")
def ingest_pipeline_task(self, query: str, num_results: int):
    """
    Full Pipeline: Search -> Scrape -> Knowledge Graph Injection
    """
    try:
        # Step 1: Search
        self.update_state(state='PROGRESS', meta={'status': 'Searching Google...'})
        
        # FIX: Fetch more results (e.g., +3 buffer) to account for filtering
        buffer_size = 3 
        search_results = async_to_sync(search_service.search)(query, num_results + buffer_size)
        
        # Filter Wikipedia
        valid_urls = [
            item.link for item in search_results 
            if "wikipedia.org" not in item.link
        ]
        
        # Slice to get exactly the number the user asked for
        urls = valid_urls[:num_results]
        
        if not urls:
             return {"status": "failed", "reason": "No valid URLs found"}

        # Step 2: Scrape
        self.update_state(state='PROGRESS', meta={'status': f'Scraping {len(urls)} sites...'})
        scrape_results = async_to_sync(scraper_service.scrape_urls)(urls)
        
        # Step 3: Graph Injection (NEW STEP)
        total_scraped = len(scrape_results)
        for i, result in enumerate(scrape_results):
            if result.error:
                continue
            
            # Update progress for the user to see
            self.update_state(state='PROGRESS', meta={
                'status': f'Building Graph: Processing {i+1}/{total_scraped}',
                'current_url': result.url
            })
            
            # INJECT INTO NEO4J
            graph_service.process_document(result.content, result.url)

        return {
            "status": "completed",
            "query": query,
            "scraped_count": total_scraped,
            "message": "Knowledge Graph built successfully."
        }

    except Exception as e:
        print(f"Task Failed: {str(e)}")
        # Re-raise so Celery marks it as FAILED
        raise e