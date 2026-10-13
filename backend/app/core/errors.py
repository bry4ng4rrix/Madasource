"""Gestion centralisée des erreurs : réponses Problem Details (RFC 9457, error-handling.md).

Forme retenue le 2026-10-13 (D-24) : `type` vaut `about:blank` ; `title` est alors la
phrase HTTP standard du statut (RFC 9457 §4.2.1). Le sens précis est porté par le membre
d'extension `code`, contrat stable du client. `request_id` relie la réponse aux journaux.

Aucune réponse ne contient de trace, de requête SQL, de valeur saisie ou de détail interne.
"""

import logging
from collections.abc import Iterable, Mapping, Sequence
from http import HTTPStatus
from typing import Any, Final, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import DBAPIError
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.middleware import apply_response_headers, new_request_id, request_id_from_scope

logger = logging.getLogger("app.errors")

PROBLEM_CONTENT_TYPE: Final = "application/problem+json"
PROBLEM_TYPE: Final = "about:blank"

# SQLSTATE réessayables : interblocage, conflit de sérialisation, attente de verrou expirée.
RETRYABLE_SQLSTATES: Final = frozenset({"40P01", "40001", "55P03"})
STATEMENT_TIMEOUT_SQLSTATE: Final = "57014"
CONNECTION_SQLSTATE_CLASS: Final = "08"

# Erreurs HTTP levées par Starlette ou FastAPI (route inconnue, méthode non permise…).
_HTTP_STATUS_CODES: Final[Mapping[int, str]] = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "PERMISSION_DENIED",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}
# En-têtes d'une HTTPException de Starlette conservés dans la réponse.
_FORWARDED_HTTP_HEADERS: Final = ("Allow", "Retry-After", "WWW-Authenticate")


class ProblemFieldError(BaseModel):
    """Erreur sur un champ : jamais la valeur saisie (error-handling.md §3)."""

    model_config = ConfigDict(frozen=True)

    field: str
    code: str
    message: str


class ProblemDetails(BaseModel):
    """Corps d'une réponse d'erreur (documenté dans l'OpenAPI)."""

    model_config = ConfigDict(frozen=True)

    type: str = PROBLEM_TYPE
    title: str
    status: int
    detail: str | None = None
    code: str
    request_id: str
    errors: list[ProblemFieldError] | None = None


def _request_id(request: Request) -> str:
    return request_id_from_scope(request.scope) or new_request_id()


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    detail: str | None = None,
    errors: Sequence[ProblemFieldError] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    problem = ProblemDetails(
        title=HTTPStatus(status).phrase,
        status=status,
        detail=detail,
        code=code,
        request_id=_request_id(request),
        errors=list(errors) if errors is not None else None,
    )
    return JSONResponse(
        problem.model_dump(mode="json", exclude_none=True),
        status_code=status,
        media_type=PROBLEM_CONTENT_TYPE,
        headers=dict(headers or {}),
    )


def _field_name(location: Iterable[Any]) -> str:
    return ".".join(str(part) for part in location)


def sanitize_validation_errors(errors: Iterable[Mapping[str, Any]]) -> list[ProblemFieldError]:
    """Garde l'emplacement, le type et le message ; retire `input`, `ctx` et `url`."""
    return [
        ProblemFieldError(
            field=_field_name(error.get("loc", ())),
            code=str(error.get("type", "invalid")),
            message=str(error.get("msg", "Invalid value")),
        )
        for error in errors
    ]


def _log(status: int, code: str, request: Request) -> None:
    extra = {
        "code": code,
        "status": status,
        "method": request.method,
        "path": request.url.path,
        "request_id": _request_id(request),
    }
    level = logging.WARNING if status in {401, 403, 429} else logging.INFO
    logger.log(level, "request_error", extra=extra)


def sqlstate_of(exc: DBAPIError) -> str | None:
    """Code SQLSTATE de l'erreur du pilote (asyncpg via SQLAlchemy : `orig.sqlstate`)."""
    value = getattr(exc.orig, "sqlstate", None)
    return value if isinstance(value, str) else None


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    allowed_origins = frozenset(settings.cors_allowed_origins)
    demo = settings.app_env == "demo"

    async def handle_app_error(request: Request, exc: Exception) -> JSONResponse:
        # Les gestionnaires ne reçoivent que le type pour lequel ils sont enregistrés.
        error = cast("AppError", exc)
        _log(error.status_code, error.code, request)
        return problem_response(
            request,
            status=error.status_code,
            code=error.code,
            detail=error.detail,
            headers=error.headers,
        )

    async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
        validation_error = cast("RequestValidationError", exc)
        _log(422, "VALIDATION_ERROR", request)
        return problem_response(
            request,
            status=422,
            code="VALIDATION_ERROR",
            detail="The request contains invalid data.",
            errors=sanitize_validation_errors(validation_error.errors()),
        )

    async def handle_http_error(request: Request, exc: Exception) -> JSONResponse:
        http_error = cast("StarletteHTTPException", exc)
        status = http_error.status_code
        code = _HTTP_STATUS_CODES.get(status, "INTERNAL_ERROR" if status >= 500 else "BAD_REQUEST")
        headers = {
            name: value
            for name, value in (http_error.headers or {}).items()
            if name.title() in _FORWARDED_HTTP_HEADERS
        }
        _log(status, code, request)
        return problem_response(request, status=status, code=code, headers=headers)

    async def handle_database_error(request: Request, exc: Exception) -> JSONResponse:
        database_error = cast("DBAPIError", exc)
        sqlstate = sqlstate_of(database_error)
        if sqlstate in RETRYABLE_SQLSTATES:
            status, code = 409, "CONCURRENT_MODIFICATION"
        elif (
            sqlstate == STATEMENT_TIMEOUT_SQLSTATE
            or database_error.connection_invalidated
            or (sqlstate or "").startswith(CONNECTION_SQLSTATE_CLASS)
        ):
            # Requête annulée par statement_timeout, ou connexion perdue.
            status, code = 503, "SERVICE_UNAVAILABLE"
        else:
            # Contrainte non associée à un code connu, ou erreur imprévue : 500 sans détail.
            return await handle_unexpected_error(request, exc)
        logger.warning(
            "database_error",
            extra={"code": code, "sqlstate": sqlstate, "request_id": _request_id(request)},
        )
        return problem_response(request, status=status, code=code)

    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Erreur 500. Appelée par le middleware d'erreur serveur de Starlette, situé à
        l'extérieur des autres middlewares : l'identifiant de requête, les en-têtes de
        sécurité et les en-têtes CORS sont donc posés ici (C31)."""
        request_id = _request_id(request)
        logger.error(
            "unhandled_exception",
            exc_info=(type(exc), exc, exc.__traceback__),
            extra={"method": request.method, "path": request.url.path, "request_id": request_id},
        )
        response = problem_response(
            request,
            status=500,
            code="INTERNAL_ERROR",
            detail="An unexpected error occurred.",
        )
        apply_response_headers(response.headers, request_id=request_id, demo=demo)
        _apply_cors_headers(response.headers, request, allowed_origins)
        return response

    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(DBAPIError, handle_database_error)
    app.add_exception_handler(Exception, handle_unexpected_error)


def _apply_cors_headers(
    headers: MutableHeaders, request: Request, allowed_origins: frozenset[str]
) -> None:
    origin = request.headers.get("origin")
    if origin and (origin in allowed_origins or "*" in allowed_origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Expose-Headers"] = "X-Request-ID, Retry-After"
        headers.add_vary_header("Origin")
