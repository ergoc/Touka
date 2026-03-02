from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from touka.core.touka import NAME, VERSION
from touka.api.routes.chat import router as chat_router
from touka.api.routes.health import router as health_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title=NAME,
        version=VERSION,
        description="Touka AI",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, prefix=API_PREFIX)
    app.include_router(health_router, prefix=API_PREFIX)

    return app