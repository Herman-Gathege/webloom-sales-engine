"""The FastAPI application.

This is the smallest skeleton that can serve the Lead API. The rest of the
rails (Docker Compose, workers, auth middleware) are Mark's piece.
"""

from fastapi import FastAPI

from app.api.v1 import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Epic 1: leads, and the activity history behind them.",
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"], summary="Liveness check")
def health() -> dict[str, str]:
    return {"status": "ok"}
