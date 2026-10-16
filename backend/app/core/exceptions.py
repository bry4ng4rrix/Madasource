"""Exceptions de l'application (error-handling.md §5).

Les services lèvent ces exceptions, jamais `HTTPException` : ils ignorent HTTP. Le
gestionnaire central (`app.core.errors`) les traduit en réponses Problem Details.
Le `detail` ne contient jamais de valeur saisie, de montant, de jeton ni d'identifiant
d'un objet d'une autre organisation (error-handling.md §7).
"""

from collections.abc import Mapping
from http import HTTPStatus
from types import MappingProxyType
from typing import ClassVar

# Délai conseillé au client avant une nouvelle tentative, quand une dépendance est indisponible.
DEFAULT_RETRY_AFTER_SECONDS = 5


class AppError(Exception):
    """Racine des erreurs de l'application : un statut HTTP et un code stable."""

    status_code: ClassVar[int] = HTTPStatus.INTERNAL_SERVER_ERROR
    code: ClassVar[str] = "INTERNAL_ERROR"
    default_headers: ClassVar[Mapping[str, str]] = MappingProxyType({})

    def __init__(self, detail: str | None = None, *, headers: Mapping[str, str] | None = None):
        super().__init__(detail or self.code)
        self.detail = detail
        self.headers: dict[str, str] = {**self.default_headers, **(headers or {})}


class ValidationAppError(AppError):
    """Règle métier non respectée par les données saisies."""

    status_code = HTTPStatus.UNPROCESSABLE_CONTENT
    code = "BUSINESS_RULE_VIOLATION"


class PasswordPolicyError(ValidationAppError):
    """Mot de passe hors de la politique (S-02) ; le `detail` ne recopie jamais la saisie."""

    code = "PASSWORD_POLICY_VIOLATION"


class BadRequestError(AppError):
    """Requête mal formée hors validation de schéma (en-tête obligatoire absent…)."""

    status_code = HTTPStatus.BAD_REQUEST
    code = "BAD_REQUEST"


class AuthenticationError(AppError):
    """Authentification absente ou invalide. L'en-tête est exigé par la RFC 9110 §15.5.2."""

    status_code = HTTPStatus.UNAUTHORIZED
    code = "AUTHENTICATION_REQUIRED"
    default_headers = MappingProxyType({"WWW-Authenticate": "Bearer"})


class PermissionDeniedError(AppError):
    """Action interdite sur un objet visible (dont la séparation des tâches)."""

    status_code = HTTPStatus.FORBIDDEN
    code = "PERMISSION_DENIED"


class PayloadTooLargeError(AppError):
    """Corps ou fichier au-delà de la taille permise, levée par un service (dépôts de documents,
    Jour 29). Le middleware de taille des corps lève, lui, une `HTTPException(413)`, que
    FastAPI relaie pendant la lecture du corps (security-design.md §15)."""

    status_code = HTTPStatus.CONTENT_TOO_LARGE
    code = "PAYLOAD_TOO_LARGE"


class NotFoundError(AppError):
    """Ressource inexistante ou hors du périmètre de l'acteur : même réponse (D-25)."""

    status_code = HTTPStatus.NOT_FOUND
    code = "RESOURCE_NOT_FOUND"


class ConflictError(AppError):
    """Conflit générique avec l'état courant ; préférer une sous-classe au code précis."""

    status_code = HTTPStatus.CONFLICT
    code = "CONFLICT"


class InvalidStateTransitionError(ConflictError):
    code = "INVALID_STATE_TRANSITION"


class ConcurrentModificationError(ConflictError):
    """Interblocage, conflit de sérialisation ou attente de verrou expirée : réessayable."""

    code = "CONCURRENT_MODIFICATION"


class _RetryAfterError(AppError):
    def __init__(
        self,
        detail: str | None = None,
        *,
        retry_after: int | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        extra = {"Retry-After": str(retry_after)} if retry_after is not None else {}
        super().__init__(detail, headers={**extra, **(headers or {})})


class RateLimitedError(_RetryAfterError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "RATE_LIMITED"


class ServiceUnavailableError(_RetryAfterError):
    """Dépendance indisponible (base de données, stockage) ou requête trop longue."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"
