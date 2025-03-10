from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str
