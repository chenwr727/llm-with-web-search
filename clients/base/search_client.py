import re
from abc import ABC, abstractmethod
from typing import List

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer

from schemas.search_result import SearchResult


class SearchClient(ABC):

    def __init__(self, max_concurrent: int, needs_crawler: bool = False, needs_filter: bool = False):
        self.max_concurrent = max_concurrent
        self.needs_crawler = needs_crawler
        self.needs_filter = needs_filter

    def _clean_web_content(self, content: str) -> str:
        """
        Clean web content from HTML tags, scripts, styles, comments, non-breaking spaces, and other elements.

        Args:
            content (str): The web content to be cleaned.

        Returns:
            str: The cleaned web content.
        """
        content = content.replace("\n", " ")
        content = re.sub(r"<[^>]+>", "", content)
        content = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", content, flags=re.IGNORECASE)
        content = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", content, flags=re.IGNORECASE)
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        content = re.sub(r"&nbsp;", " ", content)
        content = re.sub(r"&lt;", "<", content)
        content = re.sub(r"&gt;", ">", content)
        content = re.sub(r"&amp;", "&", content)
        content = re.sub(r"&quot;", '"', content)
        content = re.sub(r"&apos;", "'", content)
        content = re.sub(r"\s+", " ", content)
        content = re.sub(r"<[^>]*>\s*<\/[^>]*>", "", content)
        content = content.strip()
        return content

    async def _crawler_by_requests(self, search_results: List[SearchResult]) -> List[SearchResult]:
        """
        Crawl web content by requests

        Args:
            search_results (List[SearchResult]): The search results to be crawled.

        Returns:
            List[SearchResult]: The crawled search results.
        """
        urls = [result.source for result in search_results]
        loader = AsyncHtmlLoader(urls, requests_per_second=self.max_concurrent)
        docs = await loader.aload()

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)

        for doc, search_result in zip(docs_transformed, search_results):
            search_result.content += "\n" + self._clean_web_content(doc.page_content)

        return search_results

    @abstractmethod
    async def search(self, query: str, count: int = 10) -> List[SearchResult]:
        pass
