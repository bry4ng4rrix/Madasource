"""Primitives de sécurité : Argon2id, politique de mot de passe, jetons opaques (Jour 8)."""

import pytest
from argon2 import PasswordHasher as Argon2PasswordHasher

from app.core.exceptions import PasswordPolicyError
from app.core.security import (
    TOKEN_BYTES,
    PasswordHasher,
    check_password_policy,
    generate_token,
    hash_token,
    normalize_password,
    token_matches,
)
from tests.support import make_settings

pytestmark = pytest.mark.unit

# Saisie factice des tests (préfixe test-).
SAMPLE = "test-correct horse battery staple"


@pytest.fixture(scope="module")
def hasher() -> PasswordHasher:
    return PasswordHasher.from_settings(make_settings())


def test_hash_is_argon2id_with_owasp_parameters(hasher: PasswordHasher) -> None:
    stored = hasher.hash(SAMPLE)

    assert stored.startswith("$argon2id$v=19$m=19456,t=2,p=1$")
    assert SAMPLE not in stored


def test_same_password_gives_distinct_hashes(hasher: PasswordHasher) -> None:
    # Sel aléatoire par hachage : deux comptes au même mot de passe restent indiscernables.
    assert hasher.hash(SAMPLE) != hasher.hash(SAMPLE)


def test_correct_password_is_accepted(hasher: PasswordHasher) -> None:
    result = hasher.verify(hasher.hash(SAMPLE), SAMPLE)

    assert result.valid is True
    assert result.needs_rehash is False


@pytest.mark.parametrize("attempt", ["test-wrong", "", SAMPLE.upper(), SAMPLE + " "])
def test_wrong_password_is_refused(hasher: PasswordHasher, attempt: str) -> None:
    assert hasher.verify(hasher.hash(SAMPLE), attempt).valid is False


@pytest.mark.parametrize("stored", ["", "not-a-hash", "$argon2id$v=19$m=19456,t=2,p=1$broken"])
def test_unreadable_stored_hash_is_refused_without_error(
    hasher: PasswordHasher, stored: str
) -> None:
    assert hasher.verify(stored, SAMPLE).valid is False


def test_unknown_account_costs_a_full_verification(
    hasher: PasswordHasher, monkeypatch: pytest.MonkeyPatch
) -> None:
    # S-06 : sans compte, un vrai calcul Argon2id a lieu (durée comparable), puis un refus.
    calls: list[str] = []
    real_verify = Argon2PasswordHasher.verify

    def spy(self: Argon2PasswordHasher, stored: str, password: str) -> bool:
        calls.append(stored)
        return real_verify(self, stored, password)

    monkeypatch.setattr(Argon2PasswordHasher, "verify", spy)

    assert hasher.verify(None, SAMPLE).valid is False
    assert len(calls) == 1
    assert calls[0].startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_hash_from_older_parameters_needs_rehash(hasher: PasswordHasher) -> None:
    older = PasswordHasher(memory_cost_kib=12 * 1024, time_cost=3, parallelism=1)

    result = hasher.verify(older.hash(SAMPLE), SAMPLE)

    assert result.valid is True
    assert result.needs_rehash is True


def test_unicode_equivalent_inputs_match(hasher: PasswordHasher) -> None:
    # « é » composé (U+00E9) et décomposé (e + U+0301) : même mot de passe après NFKC.
    composed, decomposed = "test-café-secret", "test-café-secret"

    assert normalize_password(composed) == normalize_password(decomposed)
    assert hasher.verify(hasher.hash(composed), decomposed).valid is True


@pytest.mark.anyio
async def test_async_variants_run_off_the_event_loop(hasher: PasswordHasher) -> None:
    stored = await hasher.hash_async(SAMPLE)

    assert (await hasher.verify_async(stored, SAMPLE)).valid is True
    assert (await hasher.verify_async(None, SAMPLE)).valid is False


@pytest.mark.parametrize("password", ["a" * 12, "a" * 128, "é" * 12])
def test_password_within_policy_is_accepted(password: str) -> None:
    check_password_policy(password, min_length=12, max_length=128)


@pytest.mark.parametrize(
    ("password", "message"),
    [("a" * 11, "too short"), ("", "too short"), ("a" * 129, "too long")],
)
def test_password_outside_policy_is_refused(password: str, message: str) -> None:
    with pytest.raises(PasswordPolicyError, match=message) as excinfo:
        check_password_policy(password, min_length=12, max_length=128)

    assert excinfo.value.code == "PASSWORD_POLICY_VIOLATION"
    assert excinfo.value.status_code == 422
    # Message fixe : jamais la saisie ni le seuil.
    assert excinfo.value.detail in {"The password is too short.", "The password is too long."}


def test_policy_counts_characters_after_normalization() -> None:
    # 12 caractères décomposés (e + accent) = 12 caractères après NFKC, pas 24.
    check_password_policy("é" * 12, min_length=12, max_length=12)


def test_generated_tokens_are_long_and_unique() -> None:
    tokens = {generate_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(token) == 43 for token in tokens)
    assert TOKEN_BYTES * 8 == 256


def test_token_is_stored_as_sha256_digest() -> None:
    token = generate_token()
    stored = hash_token(token)

    assert len(stored) == 64
    assert token not in stored
    assert stored == hash_token(token)


def test_token_matching() -> None:
    token = generate_token()
    stored = hash_token(token)

    assert token_matches(token, stored) is True
    assert token_matches(generate_token(), stored) is False
    assert token_matches(token, "") is False
