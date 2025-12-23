from pydantic import BaseModel, HttpUrl

class ScrapeRequest(BaseModel):
    urls: list[HttpUrl]

class ScrapeResult(BaseModel):
    url: str
    title: str
    content: str
    error: str | None = None