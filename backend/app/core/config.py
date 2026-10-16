"""Configuration de l'application, lue dans l'environnement et validée au démarrage (D-11).

Une configuration invalide empêche le démarrage, sans jamais recopier la valeur reçue dans
le message d'erreur. `APP_ENV` est obligatoire : son absence ne doit pas faire tomber une
instance déployée dans le régime permissif de `local`. Dans les environnements déployés
(`staging`, `production`, `demo`), les réglages dangereux sont refusés ; la production
exige en plus des origines HTTPS et refuse les journaux de débogage.
Aucun fichier `.env` n'est lu implicitement : en local, `uv run --env-file ../.env` le charge.
"""

from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

AppEnv = Literal["local", "test", "staging", "production", "demo"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

REQUIRED_DRIVER = "postgresql+asyncpg"
# Marqueur des valeurs factices de .env.example : refusé dans les environnements déployés.
PLACEHOLDER_MARKER = "changeme"
# Environnements déployés : garde-fous de configuration (D-11 ; extension à staging et à
# demo proposée au Jour 5, Q-102).
DEPLOYED_ENVIRONMENTS: frozenset[str] = frozenset({"staging", "production", "demo"})
# Longueur minimale du mot de passe de la base dans un environnement déployé (proposé, Q-102).
MIN_DEPLOYED_PASSWORD_LENGTH = 12
# Clé de signature des jetons (Jour 10) : au moins 256 bits, soit 43 caractères en base64 URL
# (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).
MIN_SIGNING_KEY_LENGTH = 43
# Environnements déployés : clé sans espace, en ASCII imprimable, d'au moins 16 caractères
# distincts. Ce n'est pas une mesure d'entropie : seulement le refus des clés manifestement
# fabriquées à la main (« aaaa… », espaces) ; proposé, Q-106 d.
MIN_SIGNING_KEY_DISTINCT_CHARACTERS = 16
# Argon2id (S-01) : profils minimaux de l'OWASP (Password Storage Cheat Sheet, consultée le
# 2026-10-16), tous de même niveau : 46 MiB x 1, 19 MiB x 2, 12 MiB x 3, 9 MiB x 4, 7 MiB x 5.
# Plancher : la mémoire minimale du profil correspondant au nombre d'itérations (au-delà de 5,
# celle du profil à 5 itérations).
OWASP_ARGON2_MIN_MEMORY_KIB: dict[int, int] = {
    1: 46 * 1024,
    2: 19 * 1024,
    3: 12 * 1024,
    4: 9 * 1024,
    5: 7 * 1024,
}
# Environnements où la documentation interactive et le schéma OpenAPI sont servis
# (api-conventions.md §13 ; désactivés en production et en démonstration publique).
DOCS_ENVIRONMENTS: frozenset[str] = frozenset({"local", "test", "staging"})

_INVALID_URL_MESSAGE = "DATABASE_URL n'est pas une URL de base de données valide."
# Seuls paramètres de requête admis, une fois chacun (liste blanche, À VALIDER : Q-105).
# SQLAlchemy transmet la requête telle quelle à asyncpg.connect : `database`, `host`, `port`,
# `user`, `password`, `dsn`, `service`, `servicefile` ou `passfile` y remplaceraient la cible
# vérifiée sur l'URL (garde-fou _test, même cible pour les deux URL de test).
_ALLOWED_QUERY_KEYS = frozenset({"ssl", "prepared_statement_cache_size"})


def parse_database_url(raw: str) -> URL:
    """Analyse une URL de base sans jamais laisser passer un message qui en citerait une partie.

    Utilisée par la configuration et par Alembic. Un mot de passe contenant « @ » ou « : »
    fait échouer l'analyse du port par une ValueError dont le message cite la fin de l'URL
    (constat E1) ; sans port, la fin du mot de passe glisserait dans l'hôte. Les deux cas
    sont refusés avec un message fixe : encoder ces caractères (%40, %3A). La cible de la
    connexion ne vient que de l'URL : un paramètre de requête hors de la liste blanche, ou
    répété, est refusé.
    """
    try:
        url = make_url(raw)
    except ArgumentError, ValueError, TypeError:
        raise ValueError(_INVALID_URL_MESSAGE) from None
    if url.host is not None and "@" in url.host:
        raise ValueError(_INVALID_URL_MESSAGE)
    if not url.query.keys() <= _ALLOWED_QUERY_KEYS or any(
        isinstance(value, tuple) for value in url.query.values()
    ):
        raise ValueError(_INVALID_URL_MESSAGE)
    return url


def _has_explicit_server(url: URL) -> bool:
    """L'URL nomme l'hôte et le port : rien n'est complété par l'environnement (PGHOST…)."""
    return bool(url.host) and url.port is not None


def has_explicit_test_target(url: URL) -> bool:
    """Garde-fou des bases de test : hôte et port explicites, base dont le nom finit par _test."""
    return _has_explicit_server(url) and (url.database or "").endswith("_test")


def _parse_url(value: SecretStr) -> URL:
    return parse_database_url(value.get_secret_value())


class Settings(BaseSettings):
    """Réglages de l'application. Les noms de variables sont ceux des champs, en majuscules."""

    # hide_input_in_errors : une erreur de validation ne recopie jamais la valeur reçue,
    # qui peut contenir un mot de passe (DATABASE_URL).
    model_config = SettingsConfigDict(
        env_file=None, extra="ignore", frozen=True, hide_input_in_errors=True
    )

    app_env: AppEnv
    database_url: SecretStr
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    database_statement_timeout_ms: int = Field(default=30_000, ge=100, le=600_000)
    # Valeurs proposées au Jour 6, à valider (Q-103).
    database_lock_timeout_ms: int = Field(default=5_000, ge=100, le=600_000)
    database_idle_in_transaction_timeout_ms: int = Field(default=60_000, ge=1_000, le=3_600_000)
    readiness_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = ()
    # Lue aussi par uvicorn (adresses des proxys dignes de confiance, `X-Forwarded-For`) :
    # vérifiée ici pour refuser `*` en déploiement (Q-106 e).
    forwarded_allow_ips: str | None = None
    log_level: LogLevel = "INFO"
    demo_mode: bool = False
    # Secrets et primitives de sécurité (Jour 8, security-design.md §4, §15, §17).
    auth_signing_key: SecretStr
    # Profil OWASP m=19 MiB, t=2, p=1 (choix de l'utilisateur, 2026-10-16).
    password_hash_memory_kib: int = Field(default=19 * 1024, le=256 * 1024)
    password_hash_time_cost: int = Field(default=2, ge=1, le=10)
    password_hash_parallelism: int = Field(default=1, ge=1, le=8)
    # Calculs Argon2id simultanés par processus (mémoire : 19 MiB x 4 par défaut), puis
    # attente bornée avant 503 (proposé, Q-106 f).
    password_hash_max_concurrency: int = Field(default=4, ge=1, le=32)
    password_hash_queue_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    # Politique de mot de passe proposée, À VALIDER (Q-76). Bornes disjointes (min ≤ 64 ≤ max) :
    # le minimum ne peut pas dépasser le maximum.
    password_min_length: int = Field(default=12, ge=8, le=64)
    password_max_length: int = Field(default=128, ge=64, le=1024)
    # Taille maximale d'un corps de requête JSON, proposée (security-design.md §15).
    max_request_body_bytes: int = Field(default=1024 * 1024, ge=1024, le=100 * 1024 * 1024)

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, value: SecretStr) -> SecretStr:
        url = _parse_url(value)
        if url.drivername != REQUIRED_DRIVER:
            raise ValueError(f"DATABASE_URL doit utiliser le pilote {REQUIRED_DRIVER}.")
        if not url.database:
            raise ValueError("DATABASE_URL doit nommer une base de données.")
        return value

    @field_validator("auth_signing_key")
    @classmethod
    def _check_signing_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SIGNING_KEY_LENGTH:
            raise ValueError(
                f"AUTH_SIGNING_KEY doit compter au moins {MIN_SIGNING_KEY_LENGTH} caractères."
            )
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
        owasp_floor = OWASP_ARGON2_MIN_MEMORY_KIB[min(self.password_hash_time_cost, 5)]
        if self.password_hash_memory_kib < owasp_floor:
            problems.append(
                "Paramètres Argon2id sous les minimums de l'OWASP (46, 19, 12, 9 ou 7 MiB "
                "pour 1, 2, 3, 4 ou 5 itérations et plus)."
            )
        if self.demo_mode != (self.app_env == "demo"):
            problems.append("DEMO_MODE=true exige APP_ENV=demo, et inversement (D-18).")
        if self.app_env == "test" and not self.database_name.endswith("_test"):
            problems.append("En APP_ENV=test, le nom de la base doit se terminer par _test.")
        if self.app_env == "test" and not _has_explicit_server(_parse_url(self.database_url)):
            # Sans hôte ni port dans l'URL, asyncpg les prendrait dans PGHOST, PGPORT ou les
            # valeurs par défaut : le serveur réel ne serait plus celui qui a été vérifié.
            problems.append("En APP_ENV=test, l'URL de la base précise l'hôte et le port.")
        if self.app_env in DEPLOYED_ENVIRONMENTS:
            password = _parse_url(self.database_url).password or ""
            if "*" in self.cors_allowed_origins:
                problems.append(f"CORS_ALLOWED_ORIGINS ne peut pas contenir * en {self.app_env}.")
            if PLACEHOLDER_MARKER in password.lower():
                problems.append(
                    f"Le mot de passe d'exemple de .env.example est refusé en {self.app_env}."
                )
            signing_key = self.auth_signing_key.get_secret_value()
            if PLACEHOLDER_MARKER in signing_key.lower():
                problems.append(
                    f"La clé de signature d'exemple de .env.example est refusée en {self.app_env}."
                )
            if not (signing_key.isascii() and signing_key.isprintable()) or (
                " " in signing_key or len(set(signing_key)) < MIN_SIGNING_KEY_DISTINCT_CHARACTERS
            ):
                problems.append(
                    f"En {self.app_env}, AUTH_SIGNING_KEY doit être générée aléatoirement "
                    "(ASCII imprimable, sans espace, au moins "
                    f"{MIN_SIGNING_KEY_DISTINCT_CHARACTERS} caractères distincts)."
                )
            if self.forwarded_allow_ips is not None and "*" in self.forwarded_allow_ips:
                problems.append(
                    f"FORWARDED_ALLOW_IPS ne peut pas contenir * en {self.app_env} : un client "
                    "choisirait son adresse."
                )
            if len(password) < MIN_DEPLOYED_PASSWORD_LENGTH:
                problems.append(
                    f"En {self.app_env}, le mot de passe de la base doit compter au moins "
                    f"{MIN_DEPLOYED_PASSWORD_LENGTH} caractères."
                )
        if self.app_env == "production":
            if any(not origin.startswith("https://") for origin in self.cors_allowed_origins):
                problems.append("En production, les origines CORS doivent être en HTTPS.")
            if self.log_level == "DEBUG":
                problems.append("LOG_LEVEL=DEBUG est refusé en production.")
        if problems:
            raise ValueError(" ".join(problems))
        return self

    @property
    def database_name(self) -> str:
        return _parse_url(self.database_url).database or ""

    @property
    def docs_enabled(self) -> bool:
        return self.app_env in DOCS_ENVIRONMENTS
