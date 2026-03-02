from __future__ import annotations

import json
import asyncio
from collections.abc import AsyncGenerator

from touka.core.engine import engine


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _sse_done() -> str:
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
            for chunk in engine.respond_stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    future = loop.run_in_executor(None, _produce)

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield _sse(chunk)

    yield _sse_done()
    await future