from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from app.workers.tasks import ingest_pipeline_task

router = APIRouter()

class IngestRequest(BaseModel):
    query: str
    num_results: int = 1

class IngestResponse(BaseModel):
    task_id: str
    message: str

@router.post("/ingest", response_model=IngestResponse)
async def start_ingest(payload: IngestRequest):
    """
    Starts the background ingestion pipeline (Search -> Scrape -> Graph).
    """
    task = ingest_pipeline_task.delay(payload.query, payload.num_results)
    return {"task_id": task.id, "message": "Ingestion started"}

# --- THIS WAS MISSING ---
@router.get("/ingest/status/{task_id}")
async def get_status(task_id: str):
    """
    Check the status of a Celery background task.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    }
    
    # Clean up result if it's an exception (not JSON serializable)
    if task_result.status == "FAILURE":
        response["result"] = str(task_result.result)
        
    return response