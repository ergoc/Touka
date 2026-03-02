from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any, Iterator

from llama_cpp import Llama
from huggingface_hub import hf_hub_download

from config import cfg
from touka.core.logger import logger
from touka.core.touka import build_messages, NOT_READY_MSG, ERROR_MSG


def _chat_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


class ToukaEngine:
    def __init__(self) -> None:
        self.llm: Llama | None = None

    def _ensure_model(self) -> str:
        model_dir = Path(cfg.model.model_dir)
        model_path = model_dir / cfg.model.filename

        if model_path.exists():
            logger.info("Model found at {}", model_path)
            return str(model_path)

        model_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Model not found — downloading {} from {} ...", cfg.model.filename, cfg.model.repo_id)
        logger.info("This may take a few minutes (~900MB)...")

        downloaded = hf_hub_download(
            repo_id=cfg.model.repo_id,
            filename=cfg.model.filename,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
        )
        logger.success("Download complete → {}", downloaded)
        return downloaded

    def load(self) -> bool:
        try:
            model_path = self._ensure_model()
            logger.info("Loading Touka into memory...")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=cfg.model.n_ctx,
                n_threads=cfg.model.n_threads,
                n_batch=cfg.model.n_batch,
                n_gpu_layers=cfg.model.n_gpu_layers,
                use_mlock=True,
                use_mmap=True,
                verbose=False,
            )
            logger.success("Touka v{} is awake ✓", cfg.version)
            return True
        except Exception as exc:
            logger.error("Failed to load Touka: {}", exc)
            return False

    def is_ready(self) -> bool:
        return self.llm is not None

    def info(self) -> dict[str, Any]:
        return {
            "model": cfg.model.filename,
            "repo": cfg.model.repo_id,
            "n_ctx": cfg.model.n_ctx,
            "n_threads": cfg.model.n_threads,
            "ready": self.is_ready(),
        }

    def respond(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        if not self.is_ready():
            return _error_response(NOT_READY_MSG)
        try:
            output = self.llm.create_chat_completion(
                messages=build_messages(messages),
                max_tokens=max_tokens if max_tokens is not None else cfg.model.max_tokens,
                temperature=temperature if temperature is not None else cfg.model.temperature,
                top_k=cfg.model.top_k,
                top_p=cfg.model.top_p,
                repeat_penalty=cfg.model.repeat_penalty,
            )
            content = output["choices"][0]["message"]["content"].strip()
            usage = output.get("usage", {})
            return {
                "id": _chat_id(),
                "object": "chat.completion",
                "created": int(time.time()),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": output["choices"][0].get("finish_reason", "stop"),
                    }
                ],
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            }
        except Exception as exc:
            logger.error("Generation error: {}", exc)
            return _error_response(ERROR_MSG)

    def respond_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[dict]:
        if not self.is_ready():
            yield _stream_chunk(_chat_id(), NOT_READY_MSG, finish_reason="stop")
            return
        chat_id = _chat_id()
        try:
            stream = self.llm.create_chat_completion(
                messages=build_messages(messages),
                max_tokens=max_tokens if max_tokens is not None else cfg.model.max_tokens,
                temperature=temperature if temperature is not None else cfg.model.temperature,
                top_k=cfg.model.top_k,
                top_p=cfg.model.top_p,
                repeat_penalty=cfg.model.repeat_penalty,
                stream=True,
            )
            for chunk in stream:
                choice = chunk["choices"][0]
                delta = choice["delta"].get("content", "")
                finish_reason = choice.get("finish_reason")
                if delta or finish_reason:
                    yield _stream_chunk(chat_id, delta, finish_reason=finish_reason)
        except Exception as exc:
            logger.error("Stream error: {}", exc)
            yield _stream_chunk(chat_id, ERROR_MSG, finish_reason="stop")


def _stream_chunk(chat_id: str, content: str, finish_reason: str | None = None) -> dict:
    return {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
    }


def _error_response(message: str) -> dict:
    return {
        "id": _chat_id(),
        "object": "chat.completion",
        "created": int(time.time()),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": message},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


engine = ToukaEngine()