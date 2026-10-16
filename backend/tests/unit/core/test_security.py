"""Primitives de sécurité : Argon2id, politique de mot de passe, jetons opaques (Jour 8)."""

import asyncio
import unicodedata
from collections.abc import Callable
from typing import Any, Literal

import pytest
from argon2 import PasswordHasher as Argon2PasswordHasher

from app.core.exceptions import PasswordPolicyError, ServiceUnavailableError
from app.core.security import (
    PasswordHasher,
    check_password_policy,
    generate_token,
    hash_token,
    normalize_password,
    token_matches,
)
from tests.support import make_settings

pytestmark = pytest.mark.unit

NormalizationForm = Literal["NFC", "NFD", "NFKC", "NFKD"]

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
    hasher: PasswordHasher, argon2_calls: list[str]
) -> None:
    # S-06 : sans compte, un vrai calcul Argon2id a lieu (durée comparable), puis un refus.
    assert hasher.verify(None, SAMPLE).valid is False
    assert len(argon2_calls) == 1
    assert argon2_calls[0].startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_hash_from_older_parameters_needs_rehash(hasher: PasswordHasher) -> None:
    older = PasswordHasher(
        memory_cost_kib=12 * 1024, time_cost=3, parallelism=1, max_password_length=128
    )

    result = hasher.verify(older.hash(SAMPLE), SAMPLE)

    assert result.valid is True
    assert result.needs_rehash is True


def test_unicode_equivalent_inputs_match(hasher: PasswordHasher) -> None:
    # « é » composé (U+00E9) et décomposé (e + U+0301) : même mot de passe après NFKC.
    composed, decomposed = "test-café-secret", "test-café-secret"

    assert normalize_password(composed) == normalize_password(decomposed)
    assert hasher.verify(hasher.hash(composed), decomposed).valid is True


@pytest.mark.anyio
async def test_async_variants_run_in_a_worker_thread(
    hasher: PasswordHasher, monkeypatch: pytest.MonkeyPatch
) -> None:
    offloaded: list[str] = []
    real_to_thread = asyncio.to_thread

    async def spy(func: Callable[..., Any], /, *args: Any) -> Any:
        offloaded.append(func.__name__)
        return await real_to_thread(func, *args)

    monkeypatch.setattr(asyncio, "to_thread", spy)

    stored = await hasher.hash_async(SAMPLE)
    assert (await hasher.verify_async(stored, SAMPLE)).valid is True
    assert (await hasher.verify_async(None, SAMPLE)).valid is False
    assert offloaded == ["hash", "verify", "verify"]


@pytest.mark.parametrize("password", ["a" * 12, "a" * 128, "é" * 12])
def test_password_within_policy_is_accepted(password: str) -> None:
    check_password_policy(password, min_length=12, max_length=128)


@pytest.mark.parametrize(
    ("password", "detail"),
    [
        ("a" * 11, "The password is too short."),
        ("", "The password is too short."),
        ("a" * 129, "The password is too long."),
    ],
)
def test_password_outside_policy_is_refused(password: str, detail: str) -> None:
    with pytest.raises(PasswordPolicyError) as excinfo:
        check_password_policy(password, min_length=12, max_length=128)

    assert excinfo.value.code == "PASSWORD_POLICY_VIOLATION"
    assert excinfo.value.status_code == 422
    # Message fixe : jamais la saisie ni le seuil.
    assert excinfo.value.detail == detail


def test_minimum_counts_the_shorter_form() -> None:
    # 12 « é » décomposés (e + accent, 24 caractères saisis) = 12 après NFKC : accepté au
    # minimum de 12 ; 11 seraient refusés.
    check_password_policy("e\u0301" * 12, min_length=12, max_length=128)
    with pytest.raises(PasswordPolicyError, match="too short"):
        check_password_policy("e\u0301" * 11, min_length=12, max_length=128)


def test_generated_tokens_are_long_and_unique() -> None:
    tokens = {generate_token() for _ in range(100)}

    assert len(tokens) == 100
    # 32 octets d'aléa (256 bits) en base64 URL sans remplissage : 43 caractères.
    assert all(len(token) == 43 for token in tokens)


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


@pytest.fixture
def argon2_calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Empreintes passées à argon2 `verify` : prouve qu'un calcul complet a eu lieu."""
    calls: list[str] = []
    real_verify = Argon2PasswordHasher.verify

    def spy(self: Argon2PasswordHasher, stored: str, password: str) -> bool:
        calls.append(stored)
        return real_verify(self, stored, password)

    monkeypatch.setattr(Argon2PasswordHasher, "verify", spy)
    return calls


@pytest.mark.parametrize("stored", ["", "not-a-hash"])
def test_unreadable_stored_hash_costs_a_full_verification(
    hasher: PasswordHasher, argon2_calls: list[str], stored: str
) -> None:
    assert hasher.verify(stored, SAMPLE).valid is False
    # Tentative sur l'empreinte illisible, puis calcul sur l'empreinte factice (S-06).
    assert argon2_calls[-1].startswith("$argon2id$v=19$m=19456,t=2,p=1$")


@pytest.mark.parametrize("attempt", ["a" * 129, "test-\ud800-lone-surrogate"])
def test_oversized_or_unencodable_attempt_is_refused_after_full_cost(
    hasher: PasswordHasher, argon2_calls: list[str], attempt: str
) -> None:
    stored = hasher.hash(SAMPLE)
    argon2_calls.clear()

    assert hasher.verify(stored, attempt).valid is False
    assert hasher.verify(None, attempt).valid is False
    assert len(argon2_calls) == 2


def test_oversized_input_is_refused_before_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    normalized: list[int] = []
    real_normalize = unicodedata.normalize

    def spy(form: NormalizationForm, text: str) -> str:
        normalized.append(len(text))
        return real_normalize(form, text)

    monkeypatch.setattr(unicodedata, "normalize", spy)

    with pytest.raises(PasswordPolicyError, match="too long"):
        check_password_policy("\ufdfa" * 100_000, min_length=12, max_length=128)
    assert normalized == []


def test_nfkc_expansion_does_not_satisfy_the_minimum() -> None:
    # 7 ligatures (U+FDFA) deviennent 126 caractères en NFKC : 7 caractères saisis.
    with pytest.raises(PasswordPolicyError, match="too short"):
        check_password_policy("\ufdfa" * 7, min_length=12, max_length=128)


def test_nfkc_expansion_beyond_maximum_is_refused() -> None:
    with pytest.raises(PasswordPolicyError, match="too long"):
        check_password_policy("\ufdfa" * 12, min_length=12, max_length=128)


def test_unencodable_password_is_refused_by_policy_and_hash(hasher: PasswordHasher) -> None:
    lone_surrogate = "test-\ud800-" + "a" * 12

    with pytest.raises(PasswordPolicyError, match="invalid characters"):
        check_password_policy(lone_surrogate, min_length=12, max_length=128)
    with pytest.raises(PasswordPolicyError):
        hasher.hash(lone_surrogate)


def test_unencodable_token_does_not_match() -> None:
    assert token_matches("\ud800", hash_token(generate_token())) is False


@pytest.mark.anyio
async def test_concurrent_hashing_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    hasher = PasswordHasher.from_settings(make_settings(password_hash_max_concurrency=2))
    running = peak = 0
    real_to_thread = asyncio.to_thread

    async def tracking(func: Callable[..., Any], /, *args: Any) -> Any:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        try:
            await asyncio.sleep(0.01)
            return await real_to_thread(func, *args)
        finally:
            running -= 1

    monkeypatch.setattr(asyncio, "to_thread", tracking)

    results = await asyncio.gather(*(hasher.verify_async(None, SAMPLE) for _ in range(6)))

    assert peak == 2
    assert not any(result.valid for result in results)


@pytest.mark.anyio
async def test_saturated_hashing_returns_service_unavailable() -> None:
    hasher = PasswordHasher.from_settings(
        make_settings(password_hash_max_concurrency=1, password_hash_queue_timeout_seconds=0.05)
    )
    await hasher._slots.acquire()  # place unique occupée
    try:
        with pytest.raises(ServiceUnavailableError) as excinfo:
            await hasher.verify_async(None, SAMPLE)
    finally:
        hasher._slots.release()

    assert excinfo.value.headers["Retry-After"] == "1"
