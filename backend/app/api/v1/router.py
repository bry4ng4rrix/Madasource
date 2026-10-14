"""Routeur `/api/v1` : agrège les routers actifs (architecture.md §3)."""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.core.errors import PROBLEM_RESPONSE_DOC

API_V1_PREFIX = "/api/v1"

# Le 422 documenté est celui que l'API renvoie réellement (Problem Details), et non le
# HTTPValidationError par défaut de FastAPI, qui contient la valeur saisie.
api_router = APIRouter(
    prefix=API_V1_PREFIX,
    responses={
        422: {**PROBLEM_RESPONSE_DOC, "description": "Données invalides (`VALIDATION_ERROR`)."}
    },
)
api_router.include_router(health.router)
