from typing import List

import requests

from clients.base import SearchClient
from schemas.search_result import SearchResult
from utils.logger import logger


class BochaSearchClient(SearchClient):
    def __init__(self, api_key: str, max_concurrent: int = 4, needs_crawler: bool = False, needs_filter: bool = False):
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.session = requests.Session()
        self.session.headers.update(headers)

        self.url = "https://api.bochaai.com/v1/web-search"
        self.needs_crawler = needs_crawler

        super().__init__(max_concurrent, needs_crawler, needs_filter)

    async def search(self, query: str, count: int = 10, freshness: str = "noLimit") -> List[SearchResult]:
        """
        Search for web pages using the Bocha Search API.

        Args:
            query (str): The search query.
            count (int, optional): The number of results to return. Defaults to 10.
            freshness (str, optional): The freshness of the results. Defaults to "noLimit".

        Returns:
            List[SearchResult]: A list of SearchResult objects.
        """
        data = {"query": query, "freshness": freshness, "summary": True, "count": count}

        response = self.session.post(self.url, json=data)

        if response.status_code == 200:
            json_response = response.json()
            try:
                if json_response["code"] != 200 or not json_response["data"]:
                    logger.error(f"搜索API请求失败，原因是: {response.msg or '未知错误'}")
                    return []

                webpages = json_response["data"]["webPages"]["value"]
                if not webpages:
                    logger.error("未找到相关结果。")
                    return []
                formatted_results = [
                    SearchResult(title=page["name"], content=page["summary"], source=page["url"]) for page in webpages
                ]
                if self.needs_crawler:
                    formatted_results = await self._crawler_by_requests(formatted_results)
                return formatted_results
            except Exception as e:
                logger.error(f"搜索API请求失败，原因是：搜索结果解析失败 {str(e)}")
                return []
        else:
            logger.error(f"搜索API请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
            return []
