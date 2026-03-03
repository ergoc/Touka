from __future__ import annotations

import json
import time
import asyncio
from collections.abc import AsyncGenerator

from config import cfg
from touka.core.model import model


class Stream:
    def __init__(self, chat_id: str) -> None:
        self.chat_id = chat_id
        self.created = int(time.time())

    def _build(self, delta: dict, finish_reason: str | None) -> str:
        data = {
            "id": self.chat_id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": cfg.model.filename,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }
        return f"data: {json.dumps(data)}\n\n"

    def first(self) -> str:
        return self._build({"role": "assistant", "content": ""}, None)

    def content(self, text: str) -> str:
        return self._build({"content": text}, None)

    def final(self, finish_reason: str = "stop") -> str:
        return self._build({}, finish_reason)

    @staticmethod
    def done() -> str:
        return "data: [DONE]\n\n"


async def token_stream(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncGenerator[str, None]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    def _produce() -> None:
        try:
            for chunk in model.respond_stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    future = loop.run_in_executor(None, _produce)

    stream: Stream | None = None
    finish_reason = "stop"
    first = True

    while True:
        chunk = await queue.get()
        if chunk is None:
            break

        choices = chunk.get("choices", [])
        if not choices:
            continue

        choice = choices[0]
        content = choice.get("delta", {}).get("content", "")
        chunk_finish = choice.get("finish_reason")

        if chunk_finish:
            finish_reason = chunk_finish
            continue

        if not content:
            continue

        if first:
            stream = Stream(chunk.get("id", "chatcmpl-unknown"))
            yield stream.first()
            first = False

        yield stream.content(content)

    if stream:
        yield stream.final(finish_reason)

    yield Stream.done()
    await future