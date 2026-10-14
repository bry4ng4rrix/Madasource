"""Journalisation structurée en JSON sur la sortie standard (D-12).

Chaque ligne porte l'horodatage UTC, le niveau, le logger, le message et, dans une
requête, son identifiant. Les champs supplémentaires (`extra=`) dont le nom évoque un
secret sont masqués. Règle d'usage : un message ne contient jamais de secret, de donnée
personnelle ni de composante de prix ; on journalise des identifiants.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, TextIO

# Identifiant de la requête en cours, posé par le middleware de contexte de requête.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "iban",
    "account_number",
    "bic",
    "database_url",
)
# Attributs propres à LogRecord : tout autre attribut vient de `extra=`. `color_message`
# est ajouté par uvicorn (codes de couleur ANSI), inutile dans un journal JSON.
_RECORD_ATTRIBUTES = frozenset(vars(logging.makeLogRecord({}))) | {
    "message",
    "asctime",
    "color_message",
}


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def sanitize(key: str, value: Any) -> Any:
    """Masque une valeur dont la clé évoque un secret, à toute profondeur.

    Les dictionnaires et les séquences sont parcourus ; un objet d'un autre type est
    remplacé par le nom de son type, pour qu'aucune représentation imprévue ne fuie.
    """
    if _is_sensitive(key):
        return REDACTED
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(k): sanitize(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [sanitize(key, item) for item in value]
    return f"<{type(value).__name__}>"


class JsonFormatter(logging.Formatter):
    """Formateur JSON, sans dépendance (D-12)."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, UTC)
        payload: dict[str, Any] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _RECORD_ATTRIBUTES and key != "request_id" and not key.startswith("_"):
                payload[key] = sanitize(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class _MadaSourceHandler(logging.StreamHandler[TextIO]):
    """Gestionnaire reconnaissable, pour qu'une reconfiguration ne l'ajoute pas deux fois."""


class DropServerErrorReplay(logging.Filter):
    """Écarte la trace qu'uvicorn journalise après une erreur 500.

    Starlette relance l'exception une fois la réponse 500 envoyée, et uvicorn la journalise
    avec son message complet. Le gestionnaire d'erreurs de l'application l'a déjà
    journalisée, nettoyée et avec son request_id : ce doublon est supprimé.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not str(record.msg).startswith("Exception in ASGI application")


def configure_logging(level: str) -> None:
    """Installe le formateur JSON sur le logger racine, sans retirer les autres gestionnaires.

    Les loggers d'uvicorn sont redirigés vers ce gestionnaire ; son journal d'accès est
    coupé, pour qu'il n'y ait qu'un seul journal d'accès : celui de l'application (D-12).
    """
    root = logging.getLogger()
    for handler in [h for h in root.handlers if isinstance(h, _MadaSourceHandler)]:
        root.removeHandler(handler)
    handler = _MadaSourceHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    error_logger = logging.getLogger("uvicorn.error")
    if not any(isinstance(f, DropServerErrorReplay) for f in error_logger.filters):
        error_logger.addFilter(DropServerErrorReplay())
    logging.getLogger("uvicorn.access").disabled = True
