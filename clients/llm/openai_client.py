from langchain_openai import ChatOpenAI

from clients.base import LLMClient


class OpenAILLMClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.7, is_reasoning: bool = False):
        llm = ChatOpenAI(api_key=api_key, base_url=base_url, temperature=temperature, model=model)
        super().__init__(llm, is_reasoning)
