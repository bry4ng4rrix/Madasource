"""Moteur asynchrone et session par requête (D-08).

Le moteur est créé au démarrage de l'application et libéré à l'arrêt (cycle de vie,
`app.main`). Chaque requête qui en a besoin reçoit sa propre session ; elle est annulée
si la requête échoue, puis fermée avant l'envoi de la réponse (portée `function`).

Une connexion impossible à ouvrir (refus, adresse introuvable, délai dépassé) devient
`DatabaseUnavailableError` (503) : asyncpg lève alors des erreurs du système, que
SQLAlchemy ne traduit pas. La conversion est limitée à l'ouverture d'une connexion à la
base : une erreur de fichier ou un délai dépassé ailleurs dans l'application restent 500.
"""

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.exceptions import DEFAULT_RETRY_AFTER_SECONDS, ServiceUnavailableError

APPLICATION_NAME = "madasource-backend"


class DatabaseUnavailableError(ServiceUnavailableError):
    """La base ne répond pas à l'ouverture d'une connexion (503, réessayable)."""

    def __init__(self) -> None:
        super().__init__("The database is not available.", retry_after=DEFAULT_RETRY_AFTER_SECONDS)


def create_engine(settings: Settings) -> AsyncEngine:
    """Crée le moteur asyncpg à partir de la configuration validée."""
    engine = create_async_engine(
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
                # Attente de verrou trop longue : SQLSTATE 55P03, réponse 409 réessayable (D-09).
                "lock_timeout": str(settings.database_lock_timeout_ms),
                # Transaction ouverte et inactive : fermée par le serveur, verrous libérés.
                "idle_in_transaction_session_timeout": str(
                    settings.database_idle_in_transaction_timeout_ms
                ),
            },
        },
    )
    event.listen(engine.sync_engine, "do_connect", _connect_or_unavailable)
    return engine


def _connect_or_unavailable(
    dialect: Any, connection_record: Any, cargs: tuple[Any, ...], cparams: dict[str, Any]
) -> Any:
    """Ouvre la connexion ; une erreur réseau ou un délai dépassé deviennent un 503.

    `OSError` couvre le refus de connexion, l'échec de toutes les adresses d'un hôte et la
    résolution de nom impossible (`socket.gaierror`) ; `TimeoutError` en hérite. Les erreurs
    du pilote (authentification refusée, base absente) sont traduites par SQLAlchemy, puis
    par le gestionnaire des SQLSTATE (`app.core.errors`).
    """
    try:
        return dialect.connect(*cargs, **cparams)
    except OSError as exc:
        raise DatabaseUnavailableError() from exc


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
