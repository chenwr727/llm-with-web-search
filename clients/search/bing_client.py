import asyncio
from typing import List

from fake_useragent import UserAgent
from playwright.async_api import async_playwright

from clients.base import SearchClient
from schemas.search_result import SearchResult
from utils.logger import logger


class BingSearchClient(SearchClient):
    def __init__(self, max_concurrent: int = 5, needs_crawler: bool = True, needs_filter: bool = True):
        self.results = []
        self.semaphore = None

        self.playwright = None
        self.browser = None
        self.context = None
        self._initialized = False
        self._lock = asyncio.Lock()

        super().__init__(max_concurrent, needs_crawler, needs_filter)

    async def init_browser(self):
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    self.playwright = await async_playwright().start()
                    self.browser = await self.playwright.chromium.launch(headless=True)
                    self.context = await self.browser.new_context(
                        viewport={"width": 1920, "height": 1080}, user_agent=UserAgent().random
                    )
                    self.semaphore = asyncio.Semaphore(self.max_concurrent)
                    self._initialized = True

    async def close(self):
        if self.browser:
            async with self._lock:
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
                self._initialized = False

    async def scrape_single_page(self, link: str) -> dict:
        """
        Scrape a single page from a link.

        Args:
            link (str): The link to scrape.

        Returns:
            dict: A dictionary containing the scraped data.
        """
        try:
            async with self.semaphore:
                new_page = await self.context.new_page()
                response = await new_page.goto(link, wait_until="networkidle", timeout=30000)

                content_type = response.headers.get("content-type", "").lower()
                is_pdf = "pdf" in content_type or link.lower().endswith(".pdf")

                await new_page.wait_for_load_state("networkidle")

                title = await new_page.title()
                if is_pdf:
                    text = await new_page.evaluate(
                        """() => {
                        const pdfViewer = document.querySelector('#plugin');
                        if (pdfViewer) {
                            return pdfViewer.textContent;
                        }
                        const pdfContent = document.querySelector('.textLayer');
                        if (pdfContent) {
                            return pdfContent.textContent;
                        }
                        return document.body.innerText;
                    }"""
                    )
                else:
                    text = await new_page.evaluate(
                        """() => {
                        const scripts = document.querySelectorAll('script, style');
                        scripts.forEach(s => s.remove());
                        return document.body.innerText;
                    }"""
                    )

                await new_page.close()
                return {"title": title, "url": link, "content": " ".join(text.split())}
        except Exception as e:
            logger.error(f"爬取页面失败: {str(e)}")
            return None

    async def search(self, query: str, count: int = 10) -> List[SearchResult]:
        """
        Search for a query on Bing and return the top results.

        Args:
            query (str): The search query.
            count (int, optional): The number of search results to return. Defaults to 10.

        Returns:
            List[SearchResult]: A list of SearchResult objects containing the search results.
        """
        try:
            await self.init_browser()
            page = await self.context.new_page()

            search_url = f"https://www.bing.com/search?q={query}"
            await page.goto(search_url, wait_until="networkidle")

            search_results = await page.query_selector_all("li.b_algo")
            tasks = []

            for result in search_results[:count]:
                try:
                    link_element = await result.query_selector("a")
                    if not link_element:
                        continue

                    link = await link_element.get_attribute("href")
                    tasks.append(self.scrape_single_page(link))

                except Exception as e:
                    logger.error(f"处理搜索结果失败: {str(e)}")
                    continue

            results = await asyncio.gather(*tasks)
            self.results = [r for r in results if r is not None]

            return [
                SearchResult(title=result["title"], content=result["content"], source=result["url"])
                for result in self.results
            ]

        except Exception as e:
            logger.error(f"搜索请求失败: {str(e)}")
            return []
        finally:
            await page.close()
