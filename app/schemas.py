from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    topic: str | None
    steps: list[str]
