"""Configuration de l'application, lue dans l'environnement et validée au démarrage (D-11).

Une configuration invalide empêche le démarrage. En production, les réglages dangereux
sont refusés : origines CORS `*` ou non HTTPS, mode DEMO, mot de passe d'exemple.
Aucun fichier `.env` n'est lu implicitement : en local, `uv run --env-file ../.env` le charge.
"""

from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

AppEnv = Literal["local", "test", "staging", "production", "demo"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

REQUIRED_DRIVER = "postgresql+asyncpg"
# Marqueur des valeurs factices de .env.example : refusé en production.
PLACEHOLDER_MARKER = "changeme"
# Environnements où la documentation interactive et le schéma OpenAPI sont servis
# (api-conventions.md §13 ; désactivés en production et en démonstration publique).
DOCS_ENVIRONMENTS: frozenset[str] = frozenset({"local", "test", "staging"})


class Settings(BaseSettings):
    """Réglages de l'application. Les noms de variables sont ceux des champs, en majuscules."""

    # hide_input_in_errors : une erreur de validation ne recopie jamais la valeur reçue,
    # qui peut contenir un mot de passe (DATABASE_URL).
    model_config = SettingsConfigDict(
        env_file=None, extra="ignore", frozen=True, hide_input_in_errors=True
    )

    app_env: AppEnv = "local"
    database_url: SecretStr
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    database_statement_timeout_ms: int = Field(default=30_000, ge=100, le=600_000)
    readiness_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = ()
    log_level: LogLevel = "INFO"
    demo_mode: bool = False

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, value: SecretStr) -> SecretStr:
        # Les messages d'erreur ne citent jamais l'URL : elle contient le mot de passe.
        try:
            url = make_url(value.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL n'est pas une URL de base de données valide.") from None
        if url.drivername != REQUIRED_DRIVER:
            raise ValueError(f"DATABASE_URL doit utiliser le pilote {REQUIRED_DRIVER}.")
        if not url.database:
            raise ValueError("DATABASE_URL doit nommer une base de données.")
        return value

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accepte une liste séparée par des virgules (variable d'environnement)."""
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def _check_origins(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for origin in value:
            if origin == "*":
                continue
            scheme, _, rest = origin.partition("://")
            if scheme not in {"http", "https"} or not rest or "/" in rest:
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS : chaque origine est de la forme "
                    "https://hôte[:port], sans chemin ni barre finale."
                )
        return value

    @model_validator(mode="after")
    def _check_environment(self) -> Self:
        problems: list[str] = []
        if self.demo_mode != (self.app_env == "demo"):
            problems.append("DEMO_MODE=true exige APP_ENV=demo, et inversement (D-18).")
        if self.app_env == "test" and not self.database_name.endswith("_test"):
            problems.append("En APP_ENV=test, le nom de la base doit se terminer par _test.")
        if self.app_env == "production":
            if "*" in self.cors_allowed_origins:
                problems.append("CORS_ALLOWED_ORIGINS ne peut pas contenir * en production.")
            if any(not origin.startswith("https://") for origin in self.cors_allowed_origins):
                problems.append("En production, les origines CORS doivent être en HTTPS.")
            password = make_url(self.database_url.get_secret_value()).password or ""
            if PLACEHOLDER_MARKER in password.lower():
                problems.append(
                    "Le mot de passe d'exemple de .env.example est refusé en production."
                )
        if problems:
            raise ValueError(" ".join(problems))
        return self

    @property
    def database_name(self) -> str:
        return make_url(self.database_url.get_secret_value()).database or ""

    @property
    def docs_enabled(self) -> bool:
        return self.app_env in DOCS_ENVIRONMENTS
