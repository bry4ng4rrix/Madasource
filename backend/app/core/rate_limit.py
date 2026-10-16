"""Limitation de débit applicative (Jour 8, security-design.md §15).

Stratégie retenue avec l'utilisateur le 2026-10-16 :
- limites grossières au reverse proxy (déploiement) ; limites fines ici, par règle et par clé ;
- implémentation **en mémoire**, valable pour **un seul processus** : avec plusieurs workers ou
  instances, chaque processus compte de son côté. Un stockage partagé (Redis) remplacera
  `InMemoryRateLimiter` derrière la même interface quand plusieurs instances seront
  déployées (D-20 : pas de Redis sans besoin démontré) ;
- dépassement : 429 `RATE_LIMITED` avec `Retry-After`.

Les règles par endpoint (connexion, inscription, réinitialisation…) seront posées avec ces
endpoints, à partir du Jour 10 ; leurs seuils sont À VALIDER (Q-76).
"""

import math
import time
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from fastapi import Request

from app.core.exceptions import RateLimitedError

# Nombre maximal de clés suivies : au-delà, les plus anciennes sont oubliées, pour qu'un
# attaquant qui varie les clés (adresses, comptes) ne puisse pas épuiser la mémoire.
DEFAULT_MAX_KEYS = 100_000


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """Au plus `limit` requêtes par fenêtre glissante de `window_seconds`, pour une clé."""

    name: str
    limit: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.limit < 1 or self.window_seconds <= 0:
            raise ValueError("Une règle de limitation exige limit ≥ 1 et une fenêtre positive.")


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter(Protocol):
    """Interface commune à l'implémentation en mémoire et à un futur stockage partagé."""

    async def hit(self, rule: RateLimitRule, key: str) -> RateLimitDecision: ...


class InMemoryRateLimiter:
    """Fenêtre glissante exacte (journal des instants), par processus.

    Les appels ne contiennent aucun `await` : dans une boucle d'événements, chaque `hit` est
    atomique sans verrou. Horloge monotone, injectable pour les tests.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = DEFAULT_MAX_KEYS,
    ) -> None:
        self._clock = clock
        self._max_keys = max_keys
        self._events: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()

    async def hit(self, rule: RateLimitRule, key: str) -> RateLimitDecision:
        now = self._clock()
        bucket_key = (rule.name, key)
        events = self._events.get(bucket_key)
        if events is None:
            events = deque()
            self._events[bucket_key] = events
            while len(self._events) > self._max_keys:
                self._events.popitem(last=False)
        else:
            self._events.move_to_end(bucket_key)
        horizon = now - rule.window_seconds
        while events and events[0] <= horizon:
            events.popleft()
        if len(events) >= rule.limit:
            # La plus ancienne requête retenue sort de la fenêtre à events[0] + fenêtre.
            wait = events[0] + rule.window_seconds - now
            return RateLimitDecision(allowed=False, retry_after_seconds=max(1, math.ceil(wait)))
        events.append(now)
        return RateLimitDecision(allowed=True)


def client_ip(request: Request) -> str:
    """Adresse du client vue par l'application.

    Derrière un reverse proxy, uvicorn doit être lancé avec `--proxy-headers` et
    `--forwarded-allow-ips` limité au proxy : sinon toutes les requêtes partagent l'adresse
    du proxy, ou un client pourrait choisir la sienne par `X-Forwarded-For`.
    """
    return request.client.host if request.client else "unknown"


def rate_limit(
    rule: RateLimitRule, key: Callable[[Request], str] = client_ip
) -> Callable[[Request], Awaitable[None]]:
    """Dépendance FastAPI : refuse en 429 au-delà de la règle, pour la clé calculée."""

    async def dependency(request: Request) -> None:
        limiter: RateLimiter = request.app.state.rate_limiter
        decision = await limiter.hit(rule, key(request))
        if not decision.allowed:
            raise RateLimitedError(
                "Too many requests. Retry later.", retry_after=decision.retry_after_seconds
            )

    return dependency
