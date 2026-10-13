"""Moteur asynchrone et session par requête (D-08).

Le moteur est créé au démarrage de l'application et libéré à l'arrêt (cycle de vie,
`app.main`). Chaque requête qui en a besoin reçoit sa propre session ; elle est annulée
si la requête échoue, puis fermée avant l'envoi de la réponse (portée `function`).
La base déclarative, les modèles et la base de test isolée sont l'objet du Jour 6.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings

APPLICATION_NAME = "madasource-backend"


def create_engine(settings: Settings) -> AsyncEngine:
    """Crée le moteur asyncpg à partir de la configuration validée."""
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        # Les paramètres des requêtes n'apparaissent pas dans les messages d'erreur,
        # donc pas dans les journaux (données personnelles, secrets).
        hide_parameters=True,
        connect_args={
            "timeout": settings.database_connect_timeout_seconds,
            "server_settings": {
                "application_name": APPLICATION_NAME,
                # Requête trop longue : annulée par PostgreSQL (SQLSTATE 57014, réponse 503).
                "statement_timeout": str(settings.database_statement_timeout_ms),
            },
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False : un objet lu reste utilisable après validation, sans requête
    # implicite, qui échouerait en asynchrone (D-08).
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Fournit une session ; l'annule si la requête échoue ; la ferme dans tous les cas."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise


# Portée `function` : la session est fermée avant l'envoi de la réponse, et non après
# (FastAPI 0.121 et suivants, architecture.md D-08).
DbSession = Annotated[AsyncSession, Depends(get_db_session, scope="function")]
