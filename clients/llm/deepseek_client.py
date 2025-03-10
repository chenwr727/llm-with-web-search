from langchain_deepseek import ChatDeepSeek

from clients.base import LLMClient


class DeepseekLLMClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.7, is_reasoning: bool = False):
        llm = ChatDeepSeek(api_key=api_key, api_base=base_url, temperature=temperature, model=model)
        super().__init__(llm, is_reasoning)
