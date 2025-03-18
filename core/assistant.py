import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, List, Optional

from clients.base.llm_client import LLMClient
from clients.base.search_client import SearchClient
from clients.llm.prompts import (
    ANALYZE_SEARCH_PROMPT,
    FILTER_RESULTS_PROMPT,
    GENERATE_ANSWER_PROMPT,
    GENERATE_ANSWER_WITH_SEARCH_PROMPT,
)
from schemas.chat_message import ChatMessage
from schemas.search_result import SearchResult
from utils.logger import logger


class Assistant:
    def __init__(self, analysis_llm: LLMClient, answer_llm: LLMClient, search_client: SearchClient):
        self.analysis_llm = analysis_llm
        self.answer_llm = answer_llm
        self.search_client = search_client

    async def _analyze_search_need(self, messages: List[ChatMessage]) -> dict:
        """
        Analyze the search need and decide whether to perform search.

        Args:
            messages (List[ChatMessage]): The chat messages.

        Returns:
            dict: The analysis result.
        """
        logger.info("分析搜索需求...")
        question = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        result = await self.analysis_llm.generate_dict_response(
            ANALYZE_SEARCH_PROMPT, question=question, cur_date=datetime.now().strftime("%Y-%m-%d")
        )
        logger.info(f"分析搜索需求结果: {result}")
        return result

    async def _perform_search(self, search_queries: List[str]) -> List[SearchResult]:
        """
        Perform search based on the search queries.

        Args:
            search_queries (List[str]): The search queries.

        Returns:
            List[SearchResult]: The search results.
        """
        all_results = []
        for query in search_queries:
            results = await self._search_and_filter(query)
            all_results.extend(results)

        return all_results

    async def _perform_search_with_concurrent(self, search_queries: List[str]) -> List[SearchResult]:
        """
        Perform search based on the search queries using concurrent tasks.

        Args:
            search_queries (List[str]): The search queries.

        return:
            List[SearchResult]: The search results.
        """
        search_tasks = []
        for query in search_queries:
            search_tasks.append(self._search_and_filter(query))

        results_list = await asyncio.gather(*search_tasks)

        all_results = []
        for results in results_list:
            all_results.extend(results)

        return all_results

    async def _search_and_filter(self, query: str) -> List[SearchResult]:
        """
        Perform search based on the search query.

        Args:
            query (str): The search query.

        Returns:
            List[SearchResult]: The search results.
        """
        results = await self.search_client.search(query)
        logger.debug(f"搜索结果数: {len(results)}")
        if self.search_client.needs_filter:
            return await self._filter_search_results(results, query)
        return results

    async def _filter_search_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """
        Filter search results based on the search query.

        Args:
            results (List[SearchResult]): The search results.
            query (str): The search query.

        return:
            List[SearchResult]: The filtered search results.
        """
        if not results:
            return []

        async def filter_result(result: SearchResult):
            try:
                filtered_content = await self.analysis_llm.generate_response(
                    FILTER_RESULTS_PROMPT, query=query, content=result.content
                )
                return SearchResult(title=result.title, content=filtered_content.strip(), source=result.source)
            except Exception as e:
                logger.error(f"过滤搜索结果失败: {str(e)}")
                return None

        filtered_results = await asyncio.gather(*(filter_result(result) for result in results))

        return [result for result in filtered_results if result is not None]

    async def _generate_answer(
        self, messages: List[ChatMessage], search_results: Optional[List[SearchResult]] = None
    ) -> str:
        """
        Generate an answer based on the chat messages and search results.

        Args:
            messages (List[ChatMessage]): The chat messages.
            search_results (Optional[List[SearchResult]]): The search results.

        Returns:
            str: The generated answer.
        """
        question = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

        if search_results:
            search_results = "\n".join(
                [
                    f"[webpage {i} begin]...[webpage {i} end]{r.model_dump_json()}"
                    for i, r in enumerate(search_results, 1)
                ]
            )
            return await self.answer_llm.generate_response(
                GENERATE_ANSWER_WITH_SEARCH_PROMPT,
                question=question,
                search_results=search_results,
                cur_date=datetime.now().strftime("%Y-%m-%d"),
            )
        else:
            return await self.answer_llm.generate_response(GENERATE_ANSWER_PROMPT, question=question)

    async def _generate_answer_with_stream(
        self, messages: List[ChatMessage], search_results: Optional[List[SearchResult]] = None
    ) -> AsyncGenerator[str, Any]:
        """
        Generate an answer based on the chat messages and search results using streaming.

        Args:
            messages (List[ChatMessage]): The chat messages.
            search_results (Optional[List[SearchResult]]): The search results.

        Returns:
            AsyncGenerator[str, Any]: The generated answer using streaming.
        """
        question = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

        if search_results:
            search_results = "\n".join(
                [
                    f"[webpage {i} begin]...[webpage {i} end]{r.model_dump_json()}"
                    for i, r in enumerate(search_results, 1)
                ]
            )
            async for chunk in self.answer_llm.generate_stream_response(
                GENERATE_ANSWER_WITH_SEARCH_PROMPT,
                question=question,
                search_results=search_results,
                cur_date=datetime.now().strftime("%Y-%m-%d"),
            ):
                yield chunk
        else:
            async for chunk in self.answer_llm.generate_stream_response(GENERATE_ANSWER_PROMPT, question=question):
                yield chunk

    async def answer_question(self, messages: List[ChatMessage]) -> str:
        """
        Answer a question based on the chat messages.

        Args:
            messages (List[ChatMessage]): The chat messages.

        Returns:
            str: The generated answer.
        """
        search_decision = await self._analyze_search_need(messages)

        if search_decision["needs_search"] and search_decision["search_queries"]:
            search_results = await self._perform_search(search_decision["search_queries"])
            return await self._generate_answer(messages, search_results)
        else:
            return await self._generate_answer(messages)

    async def answer_question_with_stream(self, messages: List[ChatMessage]) -> AsyncGenerator[str, Any]:
        """
        Answer a question based on the chat messages using streaming.

        Args:
            messages (List[ChatMessage]): The chat messages.

        Returns:
            AsyncGenerator[str, Any]: The generated answer using streaming.
        """
        search_decision = await self._analyze_search_need(messages)

        if search_decision["needs_search"] and search_decision["search_queries"]:
            yield "[SEARCH]"

            yield "Searching...\n"
            for search_query in search_decision["search_queries"]:
                yield f"- {search_query}\n"

            search_results = await self._perform_search(search_decision["search_queries"])
            for i, result in enumerate(search_results, 1):
                yield f"{i}. [{result.title}]({result.source})\n"

            yield "[/SEARCH]"

            async for chunk in self._generate_answer_with_stream(messages, search_results):
                yield chunk
        else:
            async for chunk in self._generate_answer_with_stream(messages):
                yield chunk

        yield "[DONE]"
