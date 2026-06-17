from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from common.config import get_settings
from fastapi import FastAPI

from api.routes import health, reports

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Email Super Agent API starting up")
    yield
    logger.info("Email Super Agent API shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Email Super Agent",
        description="AI-powered email analysis and reporting",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(reports.router, tags=["reports"])
    return app


app = create_app()
