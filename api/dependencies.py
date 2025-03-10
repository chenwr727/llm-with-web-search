from functools import lru_cache

from fastapi import Depends

from api.services import ChatService
from clients.llm import DeepseekLLMClient, OpenAILLMClient
from clients.search import BochaSearchClient
from core.assistant import Assistant
from utils.config import settings


@lru_cache()
def get_assistant() -> Assistant:
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

    search_client = BochaSearchClient(settings.BOCHA_API_KEY)
    return Assistant(analysis_llm, answer_llm, search_client)


def get_chat_service(assistant: Assistant = Depends(get_assistant)) -> ChatService:
    assistant = get_assistant()
    return ChatService(assistant)
