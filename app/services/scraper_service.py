import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
from app.schemas.scrape import ScrapeResult
import trafilatura

class PlaywrightScraper:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _scrape_single_url(self, context: BrowserContext, url: str) -> ScrapeResult:
        """
        Scrapes a single URL with resource blocking and timeout handling.
        """
        page = await context.new_page()
        try:
            # 1. Optimize: Block unnecessary resources to speed up loading
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
                else route.continue_()
            )

            # 2. Navigate with timeout (20 seconds max)
            await page.goto(str(url), wait_until="domcontentloaded", timeout=20000)
            
            # 3. Extract content
            content_html = await page.content()
            title = await page.title()
            
            # 4. Clean HTML to Text using Trafilatura (Best for article extraction)
            cleaned_text = trafilatura.extract(content_html) or ""
            
            if not cleaned_text:
                # Fallback if trafilatura fails: get basic body text
                cleaned_text = await page.inner_text("body")

            return ScrapeResult(url=str(url), title=title, content=cleaned_text)

        except Exception as e:
            return ScrapeResult(url=str(url), title="Error", content="", error=str(e))
        finally:
            await page.close()

    async def scrape_urls(self, urls: list[str]) -> list[ScrapeResult]:
        """
        Main entry point: Scrapes a list of URLs in parallel (managed by semaphore).
        """
        async with async_playwright() as p:
            # Launch browser (headless=True for production)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            tasks = []
            for url in urls:
                # Wrap each scrape task with the semaphore to limit concurrency
                async with self.semaphore:
                    task = asyncio.create_task(self._scrape_single_url(context, str(url)))
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            await browser.close()
            return results

# Singleton instance
scraper_service = PlaywrightScraper(max_concurrent=5)