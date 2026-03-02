import time

from fastapi import APIRouter

from config import cfg
from touka.core.engine import engine
from touka.core.touka import NAME, VERSION, random_greeting

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health():
    return {
        "status": "ok" if engine.is_ready() else "loading",
        "ready": engine.is_ready(),
        "name": NAME,
        "version": VERSION,
        "message": random_greeting() if engine.is_ready() else "Still waking up...",
        "model": cfg.model.filename,
        "uptime_seconds": round(time.time() - _start_time, 1),
    }