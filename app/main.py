import sys
import asyncio
from fastapi import FastAPI
from app.core.config import settings

# --- UPDATE IMPORTS: Add 'chat' to the list ---
from app.api.endpoints import search, scrape, ingest, chat 
from app.workers.celery_app import celery_app

# --- FIX: FORCE WINDOWS TO USE PROACTOR EVENT LOOP ---
# This must run before any async code to support Playwright on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# -----------------------------------------------------

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Register Routers
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(scrape.router, prefix="/api/v1", tags=["Scrape"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])

# --- NEW: Register Chat Router ---
# The endpoint will be available at: POST /api/v1/chat/stream
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])

if __name__ == "__main__":
    import uvicorn
    # Note: Sometimes 'reload=True' causes issues on Windows even with the fix.
    # If it still fails, try removing 'reload=True'.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)