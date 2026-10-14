"""Gestion centralisée des erreurs : réponses Problem Details (RFC 9457, error-handling.md).

Forme retenue le 2026-10-13 (D-24) : `type` vaut `about:blank` ; `title` est alors la
phrase HTTP standard du statut (RFC 9457 §4.2.1). Le sens précis est porté par le membre
d'extension `code`, contrat stable du client. `request_id` relie la réponse aux journaux.

Aucune réponse ne contient de trace, de requête SQL, de valeur saisie ou de détail interne.
Les journaux des erreurs 500 ne contiennent aucun message d'exception : ceux d'asyncpg
recopient des lignes de la base (`DETAIL`), ceux d'une erreur de validation de réponse
recopient les données servies. Seuls les types, le SQLSTATE, la contrainte et les cadres
de la pile sont journalisés.
"""

import logging
from collections.abc import Iterable, Mapping, Sequence
from http import HTTPStatus
from typing import Any, Final, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.exc import DBAPIError
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.logging import summarize_exception
from app.core.middleware import (
    CORS_EXPOSED_HEADERS,
    apply_response_headers,
    new_request_id,
    request_id_from_scope,
)

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
    409: "CONFLICT",
    410: "RESOURCE_NOT_FOUND",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}
# En-têtes d'une HTTPException conservés dans la réponse (comparés en minuscules).
_FORWARDED_HTTP_HEADERS: Final = frozenset({"allow", "retry-after", "www-authenticate"})

# Types d'erreur Pydantic dont le message recopie tout ou partie de la valeur saisie.
_INPUT_ECHOING_ERROR_TYPES: Final = frozenset(
    {
        "union_tag_invalid",
        "uuid_parsing",
        "uuid_version",
        "json_invalid",
        "date_parsing",
        "datetime_parsing",
        "time_parsing",
        "date_from_datetime_parsing",
        "datetime_from_date_parsing",
        "time_delta_parsing",
        "url_parsing",
        "url_syntax_violation",
    }
)
GENERIC_FIELD_MESSAGE: Final = "Invalid value."


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


# Réponse d'erreur documentée dans l'OpenAPI ; remplace le 422 par défaut de FastAPI.
PROBLEM_RESPONSE_DOC: Final[dict[str, Any]] = {
    "model": ProblemDetails,
    "content": {PROBLEM_CONTENT_TYPE: {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
}


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


def _safe_message(error: Mapping[str, Any]) -> str:
    """Message de Pydantic, sauf s'il peut recopier la valeur saisie."""
    message = str(error.get("msg", GENERIC_FIELD_MESSAGE))
    if error.get("type") in _INPUT_ECHOING_ERROR_TYPES:
        return GENERIC_FIELD_MESSAGE
    submitted = error.get("input")
    if isinstance(submitted, str) and submitted and submitted in message:
        return GENERIC_FIELD_MESSAGE
    return message


def sanitize_validation_errors(errors: Iterable[Mapping[str, Any]]) -> list[ProblemFieldError]:
    """Garde l'emplacement, le type et un message sûr ; retire `input`, `ctx` et `url`."""
    return [
        ProblemFieldError(
            field=_field_name(error.get("loc", ())),
            code=str(error.get("type", "invalid")),
            message=_safe_message(error),
        )
        for error in errors
    ]


def sqlstate_of(exc: DBAPIError) -> str | None:
    """Code SQLSTATE de l'erreur du pilote (asyncpg via SQLAlchemy : `orig.sqlstate`)."""
    value = getattr(exc.orig, "sqlstate", None)
    return value if isinstance(value, str) else None


def _constraint_name(exc: DBAPIError) -> str | None:
    # L'erreur asyncpg d'origine est la cause de l'erreur adaptée par SQLAlchemy.
    for candidate in (exc.orig, getattr(exc.orig, "__cause__", None)):
        value = getattr(candidate, "constraint_name", None)
        if isinstance(value, str):
            return value
    return None


def exception_summary(exc: BaseException) -> dict[str, Any]:
    """Résumé journalisable d'une exception, sans aucun message d'exception."""
    summary = summarize_exception(exc)
    if isinstance(exc, DBAPIError):
        summary["sqlstate"] = sqlstate_of(exc)
        summary["constraint"] = _constraint_name(exc)
    if isinstance(exc, (ResponseValidationError, RequestValidationError, ValidationError)):
        summary["validation_errors"] = [
            {"loc": _field_name(error.get("loc", ())), "type": error.get("type")}
            for error in exc.errors()
        ]
    return summary


def _log(status: int, code: str, request: Request) -> None:
    extra = {
        "code": code,
        "status": status,
        "method": request.method,
        "path": request.url.path,
        "request_id": _request_id(request),
    }
    if status >= 500:
        level = logging.ERROR
    elif status in {401, 403, 429}:
        level = logging.WARNING
    else:
        level = logging.INFO
    logger.log(level, "request_error", extra=extra)


def _internal_error_response(request: Request, exc: BaseException) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        extra={
            "method": request.method,
            "path": request.url.path,
            "request_id": _request_id(request),
            **exception_summary(exc),
        },
    )
    return problem_response(
        request, status=500, code="INTERNAL_ERROR", detail="An unexpected error occurred."
    )


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    allowed_origins = frozenset(settings.cors_allowed_origins)
    demo = settings.app_env == "demo"

    # Les gestionnaires ne reçoivent que le type pour lequel ils sont enregistrés.
    async def handle_app_error(request: Request, exc: Exception) -> JSONResponse:
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
            if name.lower() in _FORWARDED_HTTP_HEADERS
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
            # Cette réponse traverse encore les middlewares (CORS, en-têtes) : pas d'ajout ici.
            return _internal_error_response(request, database_error)
        logger.log(
            logging.ERROR if status >= 500 else logging.WARNING,
            "database_error",
            extra={
                "code": code,
                "status": status,
                "sqlstate": sqlstate,
                "method": request.method,
                "path": request.url.path,
                "request_id": _request_id(request),
            },
        )
        return problem_response(request, status=status, code=code)

    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Erreur 500. Appelée par le middleware d'erreur serveur de Starlette, situé à
        l'extérieur des autres middlewares : l'identifiant de requête, les en-têtes de
        sécurité et les en-têtes CORS sont donc posés ici (C31)."""
        response = _internal_error_response(request, exc)
        apply_response_headers(response.headers, request_id=_request_id(request), demo=demo)
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
    """Reproduit la réponse de CORSMiddleware (sans identifiants de connexion)."""
    origin = request.headers.get("origin")
    if not origin:
        return
    if "*" in allowed_origins:
        headers["Access-Control-Allow-Origin"] = "*"
    elif origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers.add_vary_header("Origin")
    else:
        return
    headers["Access-Control-Expose-Headers"] = ", ".join(CORS_EXPOSED_HEADERS)
