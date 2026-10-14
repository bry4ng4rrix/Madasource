"""Fabrique de l'application FastAPI (architecture.md §3 et §4).

Aucune logique métier ici : configuration, journalisation, cycle de vie, middlewares,
gestionnaires d'erreurs et routers. Lancement : `uvicorn --factory app.main:create_app`.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import API_V1_PREFIX, api_router
from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import CORS_EXPOSED_HEADERS, REQUEST_ID_HEADER, RequestContextMiddleware
from app.db.session import create_engine, create_session_factory

API_TITLE = "MadaSource API"
API_VERSION = "0.1.0"

logger = logging.getLogger(__name__)

# En-têtes acceptés et exposés aux origines autorisées (api-conventions.md §11).
CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type", REQUEST_ID_HEADER, "X-Organization-Id"]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construit l'application. Sans argument, la configuration est lue dans l'environnement."""
    settings = settings or Settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        logger.info("application_started", extra={"app_env": settings.app_env})
        try:
            yield
        finally:
            await engine.dispose()
            logger.info("application_stopped")

    docs = settings.docs_enabled
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        lifespan=lifespan,
        # Documentation sous /api/v1 seulement, désactivée en production et en démo
        # (api-conventions.md §13, security-design.md §16).
        openapi_url=f"{API_V1_PREFIX}/openapi.json" if docs else None,
        docs_url=f"{API_V1_PREFIX}/docs" if docs else None,
        swagger_ui_oauth2_redirect_url=f"{API_V1_PREFIX}/docs/oauth2-redirect" if docs else None,
        redoc_url=None,
    )
    app.state.settings = settings

    register_exception_handlers(app, settings)
    # Le dernier middleware ajouté est le plus externe : le contexte de requête englobe
    # CORS, pour que même les réponses de pré-vérification portent X-Request-ID.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
        expose_headers=list(CORS_EXPOSED_HEADERS),
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware, demo=settings.app_env == "demo")

    app.include_router(api_router)
    return app
