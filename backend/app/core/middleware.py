"""Middleware ASGI pur de contexte de requête (architecture.md §4, C31).

Pour chaque requête HTTP :
- identifiant de requête : repris de `X-Request-ID` s'il est un UUID valide, sinon généré ;
  placé dans `scope["state"]` (relu par le gestionnaire des erreurs 500) et dans une
  variable de contexte (relue par les journaux) ; renvoyé dans l'en-tête de réponse ;
- un seul journal d'accès, sans chaîne de requête (elle peut contenir un jeton) ;
- en-têtes de sécurité et marquage DEMO sur toute réponse passant par ce middleware.

Middleware ASGI pur, et non `BaseHTTPMiddleware`, pour s'appliquer aussi aux réponses
d'erreur et ne pas interférer avec la diffusion des réponses.
"""

import logging
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
DEMO_MODE_HEADER = "X-MadaSource-Mode"
# En-têtes de réponse lisibles par le frontend d'une autre origine (api-conventions.md §11).
CORS_EXPOSED_HEADERS: tuple[str, ...] = (REQUEST_ID_HEADER, "Retry-After")
# Sondes appelées en boucle par l'orchestrateur : journal d'accès au niveau DEBUG.
QUIET_ACCESS_LOG_PREFIXES: tuple[str, ...] = ("/api/v1/health/",)
# security-design.md §16 : toute réponse de l'API est privée par défaut.
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

access_logger = logging.getLogger("app.access")


def new_request_id() -> str:
    return str(uuid.uuid7())


def incoming_request_id(headers: Headers) -> str | None:
    """Renvoie l'identifiant fourni par le client s'il est un UUID, sinon None."""
    value = headers.get(REQUEST_ID_HEADER)
    if not value or len(value) > 36:
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def request_id_from_scope(scope: MutableMapping[str, Any]) -> str | None:
    state = scope.get("state")
    if isinstance(state, dict):
        value = state.get("request_id")
        return value if isinstance(value, str) else None
    return None


def apply_response_headers(headers: MutableHeaders, *, request_id: str, demo: bool) -> None:
    headers[REQUEST_ID_HEADER] = request_id
    for name, value in SECURITY_HEADERS.items():
        headers[name] = value
    if demo:
        headers[DEMO_MODE_HEADER] = "demo"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, *, demo: bool = False) -> None:
        self.app = app
        self.demo = demo

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = incoming_request_id(Headers(scope=scope)) or new_request_id()
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                apply_response_headers(
                    MutableHeaders(scope=message), request_id=request_id, demo=self.demo
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            level = (
                logging.DEBUG
                if scope["path"].startswith(QUIET_ACCESS_LOG_PREFIXES)
                else logging.INFO
            )
            access_logger.log(
                level,
                "request",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)
