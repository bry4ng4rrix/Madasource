"""Routeur `/api/v1` : agrège les routers actifs (architecture.md §3)."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health.router)
