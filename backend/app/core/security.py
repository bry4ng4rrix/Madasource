"""Primitives de sécurité transverses (Jour 8, security-design.md §4).

- Mots de passe : Argon2id par argon2-cffi (S-01), paramètres OWASP par défaut, rehachage
  transparent quand ils changent, vérification à durée comparable pour un compte inexistant
  ou une empreinte illisible (S-06). Le hachage s'exécute hors de la boucle d'événements, avec
  un nombre borné de calculs simultanés (mémoire : paramètre x concurrence).
- Politique de mot de passe : longueurs seulement, sans règle de composition (S-02, Q-76).
  La saisie brute est bornée avant toute normalisation (coût de NFKC sur une entrée géante).
- Jetons opaques (rafraîchissement, vérification d'email, réinitialisation : S-04, S-07) :
  256 bits aléatoires, seule leur empreinte SHA-256 est stockée, comparaison en temps constant.

Aucune cryptographie maison : uniquement argon2-cffi et la bibliothèque standard
(`secrets`, `hashlib`, `hmac`).
"""

import asyncio
import contextlib
import hashlib
import hmac
import secrets
import unicodedata
import weakref
from collections.abc import Callable
from dataclasses import dataclass

from argon2 import PasswordHasher as _Argon2Hasher
from argon2 import Type, extract_parameters
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import (
    MAX_ARGON2_MEMORY_KIB,
    MAX_ARGON2_PARALLELISM,
    MAX_ARGON2_TIME_COST,
    Settings,
)
from app.core.exceptions import PasswordPolicyError, ServiceUnavailableError

# 256 bits d'aléa (S-04) : 43 caractères en base64 URL.
TOKEN_BYTES = 32


@dataclass(frozen=True, slots=True)
class PasswordVerification:
    """Résultat d'une vérification. `needs_rehash` : rehacher avec les paramètres courants."""

    valid: bool
    needs_rehash: bool = False


def _is_encodable(text: str) -> bool:
    """Faux pour une chaîne non encodable en UTF-8 (surrogate isolé, accepté par le JSON)."""
    try:
        text.encode()
    except UnicodeEncodeError:
        return False
    return True


def normalize_password(password: str) -> str:
    """Forme NFKC : une même saisie donne le même hachage quel que soit le clavier.

    À n'appeler que sur une saisie déjà bornée (`check_password_policy`, `verify`).
    """
    return unicodedata.normalize("NFKC", password)


def check_password_policy(password: str, *, min_length: int, max_length: int) -> None:
    """Longueurs de la politique (S-02 ; valeurs : Q-76), sans règle de composition.

    - Saisie brute plus longue que le maximum : refusée avant normalisation.
    - Minimum : sur la plus courte des deux formes, brute et normalisée, pour qu'une
      ligature qui s'étend en NFKC (« ﷺ » : 18 caractères) ne compte pas pour plusieurs.
    - Maximum : sur la plus longue des deux.
    Le refus des mots de passe compromis exige une liste ou un service externe : non
    implémenté, À VALIDER (Q-76).
    """
    if len(password) > max_length:
        raise PasswordPolicyError("The password is too long.")
    if not _is_encodable(password):
        raise PasswordPolicyError("The password contains invalid characters.")
    normalized = normalize_password(password)
    if min(len(password), len(normalized)) < min_length:
        raise PasswordPolicyError("The password is too short.")
    if len(normalized) > max_length:
        raise PasswordPolicyError("The password is too long.")


class PasswordHasher:
    """Hachage Argon2id configuré par `Settings` ; sans état propre à un utilisateur.

    Le constructeur calcule l'empreinte factice (un hachage complet) : une seule instance par
    application, créée au démarrage (`app.state.password_hasher`), jamais une par requête.
    """

    def __init__(
        self,
        *,
        memory_cost_kib: int,
        time_cost: int,
        parallelism: int,
        max_password_length: int,
        max_concurrency: int = 4,
        queue_timeout_seconds: float = 5.0,
    ) -> None:
        self._hasher = _Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_cost_kib,
            parallelism=parallelism,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )
        self._max_password_length = max_password_length
        # Au plus `max_concurrency` calculs simultanés : la mémoire reste bornée et le pool
        # de fils partagé n'est pas saturé. Au-delà du délai d'attente : 503. Un sémaphore
        # par boucle d'événements (un sémaphore asyncio est lié à la boucle qui l'attend).
        self._max_concurrency = max_concurrency
        self._semaphores: weakref.WeakKeyDictionary[
            asyncio.AbstractEventLoop, asyncio.Semaphore
        ] = weakref.WeakKeyDictionary()
        self._queue_timeout_seconds = queue_timeout_seconds
        # Hachage d'une valeur aléatoire jamais conservée : vérifié quand le compte n'existe
        # pas ou que son empreinte est illisible, pour que la durée de la réponse ne révèle
        # ni l'un ni l'autre (S-06).
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(TOKEN_BYTES))

    @classmethod
    def from_settings(cls, settings: Settings) -> PasswordHasher:
        return cls(
            memory_cost_kib=settings.password_hash_memory_kib,
            time_cost=settings.password_hash_time_cost,
            parallelism=settings.password_hash_parallelism,
            max_password_length=settings.password_max_length,
            max_concurrency=settings.password_hash_max_concurrency,
            queue_timeout_seconds=settings.password_hash_queue_timeout_seconds,
        )

    def hash(self, password: str) -> str:
        """Empreinte d'un mot de passe déjà accepté par `check_password_policy`."""
        if len(password) > self._max_password_length or not _is_encodable(password):
            raise PasswordPolicyError("The password does not satisfy the policy.")
        return self._hasher.hash(normalize_password(password))

    def verify(self, stored_hash: str | None, password: str) -> PasswordVerification:
        """Vérifie un mot de passe, toujours au prix d'un calcul Argon2id complet.

        Refus, après un calcul sur l'empreinte factice : compte inexistant
        (`stored_hash=None`), empreinte stockée illisible, saisie trop longue ou non
        encodable. L'écart de durée restant (empreinte faite avec d'anciens paramètres) est
        inhérent au rehachage progressif.
        """
        if len(password) > self._max_password_length or not _is_encodable(password):
            self._verify_quietly(self._dummy_hash, "")
            return PasswordVerification(valid=False)
        candidate = normalize_password(password)
        if stored_hash is None:
            self._verify_quietly(self._dummy_hash, candidate)
            return PasswordVerification(valid=False)
        if not _has_bounded_parameters(stored_hash):
            self._verify_quietly(self._dummy_hash, candidate)
            return PasswordVerification(valid=False)
        try:
            self._hasher.verify(stored_hash, candidate)
        except VerifyMismatchError:
            # Mot de passe différent : le calcul complet a déjà eu lieu.
            return PasswordVerification(valid=False)
        except InvalidHashError, VerificationError:
            # Empreinte illisible ou tronquée (« Decoding failed »…) : refus immédiat
            # d'argon2, compensé par un calcul sur l'empreinte factice.
            self._verify_quietly(self._dummy_hash, candidate)
            return PasswordVerification(valid=False)
        return PasswordVerification(
            valid=True, needs_rehash=self._hasher.check_needs_rehash(stored_hash)
        )

    async def hash_async(self, password: str) -> str:
        """Comme `hash`, dans un fil du pool : le calcul ne bloque pas la boucle d'événements."""
        return await self._offload(self.hash, password)

    async def verify_async(self, stored_hash: str | None, password: str) -> PasswordVerification:
        return await self._offload(self.verify, stored_hash, password)

    async def _offload[**P, T](self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Exécute `func` dans un fil, une place de calcul occupée jusqu'à la fin du fil.

        Si l'appelant est annulé, le fil continue (un fil ne s'interrompt pas) : la place
        n'est rendue qu'à sa fin, pour que la borne de concurrence reste vraie.
        """
        semaphore = self._semaphore()
        try:
            async with asyncio.timeout(self._queue_timeout_seconds):
                await semaphore.acquire()
        except TimeoutError:
            raise ServiceUnavailableError(
                "The service is busy. Retry later.", retry_after=1
            ) from None
        future = asyncio.ensure_future(asyncio.to_thread(func, *args, **kwargs))

        def release(done: asyncio.Future[T]) -> None:
            semaphore.release()
            if not done.cancelled():
                done.exception()  # récupérée : pas d'avertissement si l'appelant est parti

        future.add_done_callback(release)
        return await asyncio.shield(future)

    def _semaphore(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        semaphore = self._semaphores.get(loop)
        if semaphore is None:
            semaphore = asyncio.Semaphore(self._max_concurrency)
            self._semaphores[loop] = semaphore
        return semaphore

    def _verify_quietly(self, stored_hash: str, candidate: str) -> None:
        with contextlib.suppress(InvalidHashError, VerificationError):
            self._hasher.verify(stored_hash, candidate)


def _has_bounded_parameters(stored_hash: str) -> bool:
    """Faux pour une empreinte illisible ou aux paramètres au-delà des plafonds de Settings."""
    try:
        parameters = extract_parameters(stored_hash)
    except InvalidHashError, ValueError:
        return False
    return (
        parameters.memory_cost <= MAX_ARGON2_MEMORY_KIB
        and parameters.time_cost <= MAX_ARGON2_TIME_COST
        and parameters.parallelism <= MAX_ARGON2_PARALLELISM
    )


def generate_token() -> str:
    """Jeton opaque de 256 bits, à transmettre une seule fois et à ne jamais journaliser."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Empreinte SHA-256 (hexadécimale) stockée à la place du jeton.

    Un jeton de 256 bits aléatoires n'a pas besoin d'un hachage lent : SHA-256 suffit à ce
    qu'une fuite de la base ne livre aucun jeton utilisable. Une empreinte par usage
    (rafraîchissement, vérification, réinitialisation) : colonnes ou tables distinctes.
    """
    # surrogatepass : un jeton reçu non encodable (surrogate isolé) donne une empreinte qui ne
    # correspond à aucune autre, au lieu d'une erreur 500.
    return hashlib.sha256(token.encode(errors="surrogatepass")).hexdigest()


def token_matches(token: str, stored_hash: str) -> bool:
    """Comparaison en temps constant de l'empreinte d'un jeton reçu et de l'empreinte stockée."""
    return hmac.compare_digest(hash_token(token), stored_hash)
