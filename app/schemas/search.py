from pydantic import BaseModel, HttpUrl

class SearchResultItem(BaseModel):
    title: str
    link: str
    snippet: str

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]