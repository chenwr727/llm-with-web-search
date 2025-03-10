from typing import AsyncGenerator, List

from core.assistant import Assistant
from schemas.chat_message import ChatMessage
from utils.logger import logger


class ChatService:
    def __init__(self, assistant: Assistant):
        self.assistant = assistant

    async def stream_response(
        self, messages: List[ChatMessage], needs_crawler: bool, needs_filter: bool
    ) -> AsyncGenerator[str, None]:
        try:
            self.assistant.search_client.needs_crawler = needs_crawler
            self.assistant.search_client.needs_filter = needs_filter

            async for chunk in self.assistant.answer_question_with_stream(messages):
                yield chunk + "\r\n"

        except Exception as e:
            logger.error(str(e))
            yield f"[ERROR] {str(e)}\r\n"
