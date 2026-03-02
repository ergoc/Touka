from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from touka.core.engine import engine
from touka.core.stream import token_stream

router = APIRouter(tags=["chat"])


class Message(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
    stream: bool = Field(default=False)
    temperature: float = Field(default=0.8, ge=0.1, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=2048)


@router.post("/chat")
async def chat(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]

    if req.stream:
        return StreamingResponse(
            token_stream(
                messages,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return engine.respond(
        messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )