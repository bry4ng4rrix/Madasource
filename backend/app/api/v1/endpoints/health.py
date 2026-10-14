"""Sondes de santé (architecture.md §7.5).

- `GET /api/v1/health/live` : le processus répond. Ne consulte aucune dépendance.
- `GET /api/v1/health/ready` : la base de données répond (`SELECT 1`, délai borné).
  Sinon 503 `SERVICE_UNAVAILABLE`, sans détail sur la cause.
"""

import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings
from app.core.errors import PROBLEM_RESPONSE_DOC
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Délai conseillé au client avant une nouvelle tentative, en secondes.
READINESS_RETRY_AFTER_SECONDS = 5


class LivenessStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]


class ReadinessStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    database: Literal["ok"]


@router.get("/live", operation_id="health_live", summary="Sonde de vivacité")
async def live() -> LivenessStatus:
    return LivenessStatus(status="ok")


@router.get(
    "/ready",
    operation_id="health_ready",
    summary="Sonde de disponibilité : la base de données répond",
    responses={
        503: {
            **PROBLEM_RESPONSE_DOC,
            "description": "Base de données indisponible (`SERVICE_UNAVAILABLE`).",
        }
    },
)
async def ready(request: Request) -> ReadinessStatus:
    engine: AsyncEngine = request.app.state.engine
    settings: Settings = request.app.state.settings
    try:
        async with asyncio.timeout(settings.readiness_timeout_seconds):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        # Le type d'erreur suffit au diagnostic ; le message pourrait contenir l'hôte.
        logger.warning("readiness_check_failed", extra={"error_type": type(exc).__name__})
        raise ServiceUnavailableError(
            "The database is not available.", retry_after=READINESS_RETRY_AFTER_SECONDS
        ) from None
    return ReadinessStatus(status="ok", database="ok")
