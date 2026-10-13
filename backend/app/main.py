"""Point d'entrée ASGI du backend MadaSource.

Jour 4 : application minimale et sonde de vivacité, sans logique métier.
Les chemins suivent api-conventions.md (§3 et §13) : API et schéma OpenAPI sous ``/api/v1``.
Le Jour 5 la remplace par une fabrique d'application : configuration validée,
routeur ``/api/v1``, sonde de disponibilité ``/api/v1/health/ready``, gestion centralisée
des erreurs, journalisation structurée, documentation désactivée en production.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict


class LivenessResponse(BaseModel):
    """Réponse de la sonde de vivacité."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]


API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="MadaSource API",
    version="0.1.0",
    openapi_url=f"{API_V1_PREFIX}/openapi.json",
    docs_url=f"{API_V1_PREFIX}/docs",
    redoc_url=None,
)


@app.get(f"{API_V1_PREFIX}/health/live", tags=["health"])
async def health_live() -> LivenessResponse:
    """Indique que le processus répond. Ne consulte pas la base (sonde de vivacité)."""
    return LivenessResponse(status="ok")


@app.get("/hello", tags=["hello"])
async def hello() -> dict[str, str]:
    """Point d'entrée de test pour vérifier que l'application fonctionne."""
    return {"message": "Hello, MadaSource!"}
