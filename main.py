import sys
import uvicorn

from config import cfg
from touka.core.engine import engine
from touka.core.logger import logger
from touka.core.touka import NAME, VERSION
from touka.api.app import create_app


def boot() -> None:
    logger.info("Booting {} v{}", NAME, VERSION)

    if not engine.load():
        logger.error("Failed to load model. Exiting.")
        sys.exit(1)

    app = create_app()

    logger.success("{} is live → http://{}:{}", NAME, cfg.server.host, cfg.server.port)
    uvicorn.run(
        app,
        host=cfg.server.host,
        port=cfg.server.port,
        log_level=cfg.server.log_level,
    )


if __name__ == "__main__":
    boot()