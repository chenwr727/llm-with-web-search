from typing import Any, AsyncGenerator, Dict, Optional, Type

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from utils.json import parse_result_to_json
from utils.logger import logger


class LLMClient:
    def __init__(self, llm: ChatOpenAI, is_reasoning: bool = False):
        self.llm = llm
        self.is_reasoning = is_reasoning

    async def _build_chain(self, system_prompt: str, **partials: Any) -> RunnableSequence:
        """
        Build a chain with the given system prompt and partials

        Args:
            system_prompt (str): The system prompt to use for the chain
            **partials (Any): The partials to use for the chain

        Returns:
            RunnableSequence: The built chain
        """
        prompt = ChatPromptTemplate.from_template(system_prompt).partial(**partials)
        return prompt | self.llm

    async def _invoke_chain(self, chain: RunnableSequence, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Invoke the given chain with the given kwargs and parse the response

        Args:
            chain (RunnableSequence): The chain to invoke
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            Optional[Dict[str, Any]]: The parsed response
        """
        response = await chain.ainvoke(kwargs)
        return await self._parse_content(response.content)

    async def _parse_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse the content to json

        Args:
            content (str): The content to parse

        Returns:
            Optional[Dict[str, Any]]: The parsed content
        """
        json_data = parse_result_to_json(content)
        if isinstance(json_data, dict):
            return json_data

        if json_data is None:
            raise ValueError("Failed to parse result to json")

    async def _handle_response_with_retry(self, chain: RunnableSequence, retries: int = 2, **kwargs) -> Dict[str, Any]:
        """
        Handle the response with retry

        Args:
            chain (RunnableSequence): The chain to invoke
            retries (int, optional): The number of retries to attempt. Defaults to 2.
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            Dict[str, Any]: The response
        """
        for attempt in range(retries):
            try:
                response = await self._invoke_chain(chain, **kwargs)
                if response:
                    return response
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to handle response: {e}")
        return {}

    async def generate_dict_response(self, prompt: str, retries: int = 2, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate a dict response

        Args:
            prompt (str): The prompt to use for the chain
            retries (int, optional): The number of retries to attempt. Defaults to 2.
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            Dict[str, Any]: The response
        """
        chain = await self._build_chain(prompt)
        response = await self._handle_response_with_retry(chain, retries, **kwargs)
        return response

    async def generate_dict_stream_response(
        self, prompt: str, pydantic_object: Type[BaseModel], **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], Any]:
        """
        Generate a dict stream response

        Args:
            prompt (str): The prompt to use for the chain
            pydantic_object (Type[BaseModel]): The pydantic object to use for the chain
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            AsyncGenerator[Dict[str, Any], Any]: The response
        """
        parse = JsonOutputParser(pydantic_object=pydantic_object)
        format_instructions = f"\n\n{parse.get_format_instructions()}"

        chain = await self._build_chain(prompt, format_instructions=format_instructions)
        chain = chain | parse

        async for chunk in chain.astream(kwargs):
            yield chunk

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a response

        Args:
            prompt (str): The prompt to use for the chain
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            str: The response
        """
        chain = await self._build_chain(prompt)
        response = await chain.ainvoke(kwargs)
        return response.content

    async def generate_stream_response(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, Any]:
        """
        Generate a stream response

        Args:
            prompt (str): The prompt to use for the chain
            **kwargs (Any): The kwargs to pass to the chain

        Returns:
            AsyncGenerator[str, Any]: The response
        """
        chain = await self._build_chain(prompt)
        if not self.is_reasoning:
            async for chunk in chain.astream(kwargs):
                yield chunk.content
        else:
            is_answering = False
            yield "[THINK]"
            async for chunk in chain.astream(kwargs):
                if (
                    hasattr(chunk, "additional_kwargs")
                    and "reasoning_content" in chunk.additional_kwargs
                    and chunk.additional_kwargs["reasoning_content"]
                ):
                    yield chunk.additional_kwargs["reasoning_content"]
                else:
                    if chunk.content != "" and not is_answering:
                        is_answering = True
                        yield "[/THINK]"
                    if is_answering:
                        yield chunk.content
