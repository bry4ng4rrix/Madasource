"""Aides partagées par les tests : configuration explicite, sans dépendre de l'environnement."""

from typing import Any

from app.core.config import Settings

# Aucun service n'écoute sur ce port : toute connexion est refusée immédiatement.
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://unused:unused@127.0.0.1:9/unreachable"
ALLOWED_ORIGIN = "http://localhost:3000"
# URL injoignable au mot de passe assez fort pour un environnement déployé (valeur factice).
DEPLOYED_DATABASE_URL = "postgresql+asyncpg://madasource:StrongValue42xyz@127.0.0.1:9/madasource"


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": "local",
        "database_url": UNREACHABLE_DATABASE_URL,
        "database_pool_size": 2,
        "database_max_overflow": 0,
        "database_connect_timeout_seconds": 2.0,
        "database_statement_timeout_ms": 5_000,
        "readiness_timeout_seconds": 2.0,
        "cors_allowed_origins": (ALLOWED_ORIGIN,),
        "log_level": "INFO",
        "demo_mode": False,
    }
    values.update(overrides)
    return Settings(**values)
