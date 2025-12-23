from pydantic import BaseModel

class IngestRequest(BaseModel):
    query: str
    num_results: int = 5

class IngestResponse(BaseModel):
    task_id: str
    status: str
    message: str