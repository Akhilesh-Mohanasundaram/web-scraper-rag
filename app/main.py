from fastapi import FastAPI
from app.core.config import settings
from app.workers.celery_app import celery_app

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "neo4j_uri": settings.NEO4J_URI,
        "redis_url": settings.CELERY_BROKER_URL
    }

@app.get("/test-celery")
def test_celery_task():
    """
    Trigger a simple background task to verify Redis connection.
    """
    # We will define tasks properly later, this is just a quick check
    return {"message": "Celery integration pending task definition"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)