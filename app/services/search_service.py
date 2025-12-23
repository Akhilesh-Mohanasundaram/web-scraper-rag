import httpx
from app.core.config import settings
from app.schemas.search import SearchResultItem

class SearchService:
    BASE_URL = "https://google.serper.dev/search"

    async def search(self, query: str, num_results: int = 10) -> list[SearchResultItem]:
        """
        Searches Google via Serper.dev and returns a list of formatted results.
        """
        if not settings.SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY is not set in environment variables.")

        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Parse organic results
        results = []
        if "organic" in data:
            for item in data["organic"]:
                results.append(SearchResultItem(
                    title=item.get("title", "No Title"),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", "")
                ))
        
        return results

# Singleton instance for easy import
search_service = SearchService()