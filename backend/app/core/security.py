"""Primitives de sécurité transverses (Jour 8, security-design.md §4).

- Mots de passe : Argon2id par argon2-cffi (S-01), paramètres OWASP par défaut, rehachage
  transparent quand ils changent, vérification à durée comparable pour un compte inexistant
  (S-06). Le hachage s'exécute hors de la boucle d'événements.
- Politique de mot de passe : longueurs seulement, sans règle de composition (S-02, Q-76).
- Jetons opaques (rafraîchissement, vérification d'email, réinitialisation : S-04, S-07) :
  256 bits aléatoires, seule leur empreinte SHA-256 est stockée, comparaison en temps constant.

Aucune cryptographie maison : uniquement argon2-cffi et la bibliothèque standard
(`secrets`, `hashlib`, `hmac`).
"""

import asyncio
import hashlib
import hmac
import secrets
import unicodedata
from dataclasses import dataclass

from argon2 import PasswordHasher as _Argon2Hasher
from argon2 import Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings
from app.core.exceptions import PasswordPolicyError

# 256 bits d'aléa (S-04) : 43 caractères en base64 URL.
TOKEN_BYTES = 32


@dataclass(frozen=True, slots=True)
class PasswordVerification:
    """Résultat d'une vérification. `needs_rehash` : rehacher avec les paramètres courants."""

    valid: bool
    needs_rehash: bool = False


def normalize_password(password: str) -> str:
    """Forme NFKC : une même saisie donne le même hachage quel que soit le clavier."""
    return unicodedata.normalize("NFKC", password)


class PasswordHasher:
    """Hachage Argon2id configuré par `Settings` ; sans état propre à un utilisateur."""

    def __init__(self, *, memory_cost_kib: int, time_cost: int, parallelism: int) -> None:
        self._hasher = _Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_cost_kib,
            parallelism=parallelism,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )
        # Hachage d'une valeur aléatoire jamais conservée : vérifié quand le compte n'existe
        # pas, pour que la durée de la réponse ne révèle pas son existence (S-06).
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(TOKEN_BYTES))

    @classmethod
    def from_settings(cls, settings: Settings) -> PasswordHasher:
        return cls(
            memory_cost_kib=settings.password_hash_memory_kib,
            time_cost=settings.password_hash_time_cost,
            parallelism=settings.password_hash_parallelism,
        )

    def hash(self, password: str) -> str:
        return self._hasher.hash(normalize_password(password))

    def verify(self, stored_hash: str | None, password: str) -> PasswordVerification:
        """Vérifie un mot de passe. `stored_hash=None` (compte inexistant) : toujours faux,
        après un calcul de même coût."""
        candidate = normalize_password(password)
        if stored_hash is None:
            self._verify_quietly(self._dummy_hash, candidate)
            return PasswordVerification(valid=False)
        if not self._verify_quietly(stored_hash, candidate):
            return PasswordVerification(valid=False)
        return PasswordVerification(
            valid=True, needs_rehash=self._hasher.check_needs_rehash(stored_hash)
        )

    async def hash_async(self, password: str) -> str:
        """Comme `hash`, dans un fil du pool : le calcul (mémoire et CPU) ne bloque pas la boucle."""
        return await asyncio.to_thread(self.hash, password)

    async def verify_async(self, stored_hash: str | None, password: str) -> PasswordVerification:
        return await asyncio.to_thread(self.verify, stored_hash, password)

    def _verify_quietly(self, stored_hash: str, candidate: str) -> bool:
        try:
            return self._hasher.verify(stored_hash, candidate)
        except VerifyMismatchError:
            return False
        except InvalidHashError, VerificationError:
            # Hachage stocké illisible ou corrompu : refus, sans exception vers l'appelant.
            return False


def check_password_policy(password: str, *, min_length: int, max_length: int) -> None:
    """Longueur en caractères après normalisation NFKC (S-02 ; valeurs : Q-76).

    Pas de règle de composition. Le refus des mots de passe compromis (S-02) exige une liste
    ou un service externe : non implémenté, À VALIDER (Q-76).
    """
    length = len(normalize_password(password))
    if length < min_length:
        raise PasswordPolicyError("The password is too short.")
    if length > max_length:
        raise PasswordPolicyError("The password is too long.")


def generate_token() -> str:
    """Jeton opaque de 256 bits, à transmettre une seule fois et à ne jamais journaliser."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Empreinte SHA-256 (hexadécimale) stockée à la place du jeton.

    Un jeton de 256 bits aléatoires n'a pas besoin d'un hachage lent : SHA-256 suffit à ce
    qu'une fuite de la base ne livre aucun jeton utilisable.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def token_matches(token: str, stored_hash: str) -> bool:
    """Comparaison en temps constant de l'empreinte d'un jeton reçu et de l'empreinte stockée."""
    return hmac.compare_digest(hash_token(token), stored_hash)
