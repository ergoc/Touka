import time

from fastapi import APIRouter

from config import cfg
from touka.core.model import model
from touka.core.touka import NAME, VERSION

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health():
    return {
        "status": "ok" if model.is_ready() else "loading",
        "ready": model.is_ready(),
        "name": NAME,
        "version": VERSION,
        "model": cfg.model.filename,
        "uptime": round(time.time() - _start_time, 1),
    }