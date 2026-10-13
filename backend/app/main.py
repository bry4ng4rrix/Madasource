"""Point d'entrée ASGI du backend MadaSource.

Jour 4 : application minimale et sonde de vivacité, sans logique métier.
Le Jour 5 la remplace par une fabrique d'application : configuration validée,
routeur ``/api/v1``, sonde de disponibilité ``/health/ready``, gestion centralisée
des erreurs et journalisation structurée.
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict


class LivenessResponse(BaseModel):
    """Réponse de la sonde de vivacité."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]


app = FastAPI(title="MadaSource API", version="0.1.0")


@app.get("/health/live", tags=["health"])
async def health_live() -> LivenessResponse:
    """Indique que le processus répond. Ne consulte pas la base (sonde de vivacité)."""
    return LivenessResponse(status="ok")
