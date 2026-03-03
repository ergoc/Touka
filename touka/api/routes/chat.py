from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from touka.core.model import model
from touka.core.stream import token_stream
from touka.core.logger import logger

router = APIRouter(tags=["chat"])


class Message(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1)


@router.post("/chat")
async def chat(req: dict):
    return ChatHandler(req).handle()


class ChatHandler:
    def __init__(self, req: dict) -> None:
        self.req = req
        self.messages = [
            Message(**m).model_dump()
            for m in req.get("messages", [])
        ]
        self.stream_mode = req.get("stream", False)
        self.temperature = req.get("temperature", 0.8)
        self.max_tokens = req.get("max_tokens", 512)

    def _log(self) -> None:
        logger.debug("Incoming chat: stream={}, temperature={}, max_tokens={}", self.stream_mode, self.temperature, self.max_tokens)
        logger.debug("Message count: {}", len(self.messages))
        for i, msg in enumerate(self.messages):
            content = msg.get("content", "")
            logger.debug("Message[{}]: role='{}', content_len={}", i, msg.get("role"), len(content))
            logger.debug("Message[{}] content: {}", i, content[:100] + ("..." if len(content) > 100 else ""))

    def stream(self) -> StreamingResponse:
        return StreamingResponse(
            token_stream(
                self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    def respond(self) -> dict:
        return model.respond(
            self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def handle(self) -> StreamingResponse | dict:
        self._log()
        if self.stream_mode:
            logger.debug("Processing as streaming response")
            return self.stream()
        logger.debug("Processing as non-streaming response")
        return self.respond()