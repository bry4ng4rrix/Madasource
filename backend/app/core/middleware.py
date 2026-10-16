"""Middleware ASGI pur de contexte de requête (architecture.md §4, C31).

Pour chaque requête HTTP :
- identifiant de requête : repris de `X-Request-ID` s'il est un UUID valide, sinon généré ;
  placé dans `scope["state"]` (relu par le gestionnaire des erreurs 500) et dans une
  variable de contexte (relue par les journaux) ; renvoyé dans l'en-tête de réponse ;
- un seul journal d'accès, sans chaîne de requête (elle peut contenir un jeton) ;
- en-têtes de sécurité et marquage DEMO sur toute réponse passant par ce middleware ; HSTS
  dans les environnements déployés (security-design.md §16).

`BodySizeLimitMiddleware` borne la taille des corps de requête (security-design.md §15).

Middleware ASGI pur, et non `BaseHTTPMiddleware`, pour s'appliquer aussi aux réponses
d'erreur et ne pas interférer avec la diffusion des réponses.
"""

import logging
import re
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

from fastapi import HTTPException
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
    # API sans page à encadrer : refus de tout affichage dans un cadre (détournement de clic).
    "Content-Security-Policy": "frame-ancestors 'none'",
    "X-Frame-Options": "DENY",
}
# Environnements déployés seulement, derrière HTTPS : un an, sous-domaines compris. Sans
# `preload`, qui engage le domaine durablement (décision du propriétaire du domaine).
# Longueur déclarée lisible : chiffres ASCII seulement, 19 au plus (entier sur 64 bits).
_CONTENT_LENGTH = re.compile(r"[0-9]{1,19}")
HSTS_HEADER = ("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

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


def apply_response_headers(
    headers: MutableHeaders, *, request_id: str, demo: bool, hsts: bool = False
) -> None:
    headers[REQUEST_ID_HEADER] = request_id
    for name, value in SECURITY_HEADERS.items():
        headers[name] = value
    if hsts:
        headers[HSTS_HEADER[0]] = HSTS_HEADER[1]
    if demo:
        headers[DEMO_MODE_HEADER] = "demo"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, *, demo: bool = False, hsts: bool = False) -> None:
        self.app = app
        self.demo = demo
        self.hsts = hsts

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
                    MutableHeaders(scope=message),
                    request_id=request_id,
                    demo=self.demo,
                    hsts=self.hsts,
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


class BodySizeLimitMiddleware:
    """Refuse en 413 un corps de requête au-delà de `max_bytes`.

    Contrôle à la lecture du corps : un `Content-Length` annoncé trop grand est refusé sans
    rien lire (illisible : 400) ; un corps transmis par morceaux est compté au fil de la
    lecture. L'exception `HTTPException` est relayée par FastAPI telle quelle, puis traduite
    en Problem Details (`PAYLOAD_TOO_LARGE`, `BAD_REQUEST`) par le gestionnaire central. Une
    route qui ne lit pas son corps n'est pas concernée.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = Headers(scope=scope).get("content-length")
        max_bytes = self.max_bytes
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            if declared is not None and _CONTENT_LENGTH.fullmatch(declared) is None:
                # Longueur illisible (négative, non numérique) : requête mal formée.
                raise HTTPException(status_code=400)
            if declared is not None and int(declared) > max_bytes:
                raise HTTPException(status_code=413)
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    raise HTTPException(status_code=413)
            return message

        await self.app(scope, limited_receive, send)
