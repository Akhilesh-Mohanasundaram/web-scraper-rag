from fastapi import APIRouter
from celery.result import AsyncResult
from app.schemas.ingest import IngestRequest, IngestResponse
from app.workers.tasks import ingest_pipeline_task

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def start_ingestion(request: IngestRequest):
    """
    Triggers the Search + Scrape pipeline in the background.
    """
    # Trigger Celery Task
    task = ingest_pipeline_task.delay(request.query, request.num_results)
    
    return IngestResponse(
        task_id=task.id,
        status="Processing",
        message="Ingestion started in background."
    )

@router.get("/ingest/{task_id}")
async def get_ingestion_status(task_id: str):
    """
    Check the status of a background task.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    return response