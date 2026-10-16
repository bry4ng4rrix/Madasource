"""Limiteur en mémoire : fenêtre glissante, clés et règles indépendantes, mémoire bornée."""

import pytest

from app.core.rate_limit import InMemoryRateLimiter, RateLimitRule, normalize_ip

pytestmark = [pytest.mark.unit, pytest.mark.anyio]

RULE = RateLimitRule(name="test-login", limit=3, window_seconds=60)


class FakeClock:
    """Horloge monotone contrôlée par le test."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> InMemoryRateLimiter:
    return InMemoryRateLimiter(clock=clock)


async def test_requests_within_limit_are_allowed(limiter: InMemoryRateLimiter) -> None:
    decisions = [await limiter.hit(RULE, "test-ip-1") for _ in range(3)]

    assert all(decision.allowed for decision in decisions)


async def test_request_over_limit_is_refused_with_retry_after(
    limiter: InMemoryRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        await limiter.hit(RULE, "test-ip-1")
        clock.now += 10

    decision = await limiter.hit(RULE, "test-ip-1")

    assert decision.allowed is False
    # Première requête à t=1000, fenêtre de 60 s, on est à t=1030 : 30 s d'attente.
    assert decision.retry_after_seconds == 30


async def test_window_slides(limiter: InMemoryRateLimiter, clock: FakeClock) -> None:
    for _ in range(3):
        await limiter.hit(RULE, "test-ip-1")
    assert (await limiter.hit(RULE, "test-ip-1")).allowed is False

    clock.now += 60

    assert (await limiter.hit(RULE, "test-ip-1")).allowed is True


async def test_refused_requests_do_not_extend_the_window(
    limiter: InMemoryRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        await limiter.hit(RULE, "test-ip-1")
    for _ in range(10):
        clock.now += 5
        assert (await limiter.hit(RULE, "test-ip-1")).allowed is False

    clock.now = 1000.0 + 60

    assert (await limiter.hit(RULE, "test-ip-1")).allowed is True


async def test_retry_after_is_at_least_one_second(
    limiter: InMemoryRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        await limiter.hit(RULE, "test-ip-1")
    clock.now += 59.9

    assert (await limiter.hit(RULE, "test-ip-1")).retry_after_seconds == 1


async def test_keys_and_rules_are_independent(limiter: InMemoryRateLimiter) -> None:
    other_rule = RateLimitRule(name="test-signup", limit=1, window_seconds=60)
    for _ in range(3):
        await limiter.hit(RULE, "test-ip-1")

    assert (await limiter.hit(RULE, "test-ip-1")).allowed is False
    assert (await limiter.hit(RULE, "test-ip-2")).allowed is True
    assert (await limiter.hit(other_rule, "test-ip-1")).allowed is True


async def test_tracked_keys_are_bounded(clock: FakeClock) -> None:
    limiter = InMemoryRateLimiter(clock=clock, max_keys=2)
    one_shot = RateLimitRule(name="test-one", limit=1, window_seconds=60)
    await limiter.hit(one_shot, "test-ip-1")
    await limiter.hit(one_shot, "test-ip-2")
    # La clé la plus ancienne est oubliée quand une troisième arrive.
    await limiter.hit(one_shot, "test-ip-3")

    assert (await limiter.hit(one_shot, "test-ip-1")).allowed is True
    assert (await limiter.hit(one_shot, "test-ip-3")).allowed is False


async def test_recently_used_key_is_kept(clock: FakeClock) -> None:
    limiter = InMemoryRateLimiter(clock=clock, max_keys=2)
    one_shot = RateLimitRule(name="test-one", limit=1, window_seconds=60)
    await limiter.hit(one_shot, "test-ip-1")
    await limiter.hit(one_shot, "test-ip-2")
    await limiter.hit(one_shot, "test-ip-1")
    await limiter.hit(one_shot, "test-ip-3")

    assert (await limiter.hit(one_shot, "test-ip-1")).allowed is False


@pytest.mark.parametrize(("limit", "window"), [(0, 60), (-1, 60), (1, 0), (1, -5)])
def test_invalid_rule_is_refused(limit: int, window: float) -> None:
    with pytest.raises(ValueError, match="limit"):
        RateLimitRule(name="test-bad", limit=limit, window_seconds=window)


async def test_flooding_one_rule_does_not_reset_another(clock: FakeClock) -> None:
    limiter = InMemoryRateLimiter(clock=clock, max_keys=10)
    flooded = RateLimitRule(name="test-signup", limit=1, window_seconds=60)
    for _ in range(3):
        await limiter.hit(RULE, "test-victim@example.com")
    for index in range(50):
        await limiter.hit(flooded, f"test-noise-{index}")

    assert (await limiter.hit(RULE, "test-victim@example.com")).allowed is False


async def test_long_keys_are_stored_as_fixed_size_digests(limiter: InMemoryRateLimiter) -> None:
    long_key = "test-" + "k" * 1_000_000
    for _ in range(3):
        await limiter.hit(RULE, long_key)

    assert (await limiter.hit(RULE, long_key)).allowed is False
    assert (await limiter.hit(RULE, long_key + "x")).allowed is True
    stored_keys = [key for buckets in limiter._rules.values() for key in buckets]
    assert {len(key) for key in stored_keys} == {32}


async def test_unencodable_key_is_accepted(limiter: InMemoryRateLimiter) -> None:
    assert (await limiter.hit(RULE, "test-\ud800")).allowed is True


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("203.0.113.7", "203.0.113.7"),
        ("::ffff:203.0.113.7", "203.0.113.7"),
        ("2001:db8:1:2:aaaa::1", "2001:db8:1:2::/64"),
        ("2001:db8:1:2:ffff:ffff:ffff:ffff", "2001:db8:1:2::/64"),
        ("2001:db8:1:3::1", "2001:db8:1:3::/64"),
        ("testclient", "testclient"),
    ],
)
def test_client_addresses_are_normalized(host: str, expected: str) -> None:
    assert normalize_ip(host) == expected


async def test_rules_with_the_same_name_do_not_share_counters(
    limiter: InMemoryRateLimiter,
) -> None:
    strict = RateLimitRule(name="test-same", limit=1, window_seconds=60)
    lenient = RateLimitRule(name="test-same", limit=100, window_seconds=60)
    await limiter.hit(strict, "test-ip-1")

    assert (await limiter.hit(strict, "test-ip-1")).allowed is False
    assert (await limiter.hit(lenient, "test-ip-1")).allowed is True
