import asyncio

from clients.llm import DeepseekLLMClient, OpenAILLMClient
from clients.search import BochaSearchClient
from core.assistant import Assistant
from schemas.chat_message import ChatMessage
from utils.config import settings


async def main():
    analysis_llm = OpenAILLMClient(
        api_key=settings.ANALYSIS_LLM_API_KEY,
        base_url=settings.ANALYSIS_LLM_BASE_URL,
        model=settings.ANALYSIS_LLM_MODEL,
        temperature=settings.ANALYSIS_LLM_TEMPERATURE,
    )
    answer_llm = DeepseekLLMClient(
        api_key=settings.ANSWER_LLM_API_KEY,
        base_url=settings.ANSWER_LLM_BASE_URL,
        model=settings.ANSWER_LLM_MODEL,
        temperature=settings.ANSWER_LLM_TEMPERATURE,
        is_reasoning=True,
    )
    search_client = BochaSearchClient(settings.BOCHA_API_KEY, needs_filter=True, needs_crawler=True)

    assistant = Assistant(analysis_llm, answer_llm, search_client)

    messages = [ChatMessage(role="user", content="佛山用高压聚乙烯的工厂及联系方式")]

    async for chunk in assistant.answer_question_with_stream(messages):
        print(chunk, end="", flush=True)

    if hasattr(search_client, "close"):
        await search_client.close()


if __name__ == "__main__":
    asyncio.run(main())
