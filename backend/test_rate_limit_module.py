"""
AcademiaLINK Rate Limiting Module Test Suite
Tests the standalone in-process limiter in app/rate_limit.py:
1. Requests under the configured budget pass through freely
2. Exceeding the budget raises HTTP 429 with a Retry-After header
3. Backoff grows exponentially across repeated violations (not a fixed/flat delay)
4. Backoff is capped at the configured maximum
5. A blocked key is rejected immediately (without consuming a fresh window slot) until its
   cooldown expires
6. Per-IP and per-account keys are tracked independently (the "combination" requirement)
7. reset_rate_limit() clears a key's state immediately
8. Thresholds are read from environment variables, not hard-coded (changing the env var
   changes behavior without touching code)
9. The global RATE_LIMIT_ENABLED switch disables enforcement entirely
10. An unrecognized tier fails open (logs, does not block) rather than crashing the request
"""
import asyncio
import os
import sys
import time
import uuid

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.rate_limit import (
    _buckets,
    check_rate_limit,
    is_enabled,
    reset_rate_limit,
)


def _unique_key(label: str) -> str:
    return f"test:{label}:{uuid.uuid4().hex[:10]}"


@pytest.fixture(autouse=True)
def _isolate_env_and_buckets(monkeypatch):
    """Every test gets a clean slate: rate limiting enabled, no leaked env overrides, and a
    fresh, empty bucket store so tests can't interfere with each other's counters."""
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    for name in list(os.environ):
        if name.startswith("RATE_LIMIT_"):
            monkeypatch.delenv(name, raising=False)
    _buckets.clear()
    yield
    _buckets.clear()


def test_requests_under_budget_pass_through():
    print("\n--- Testing requests under the configured budget are never blocked ---")
    key = _unique_key("under_budget")

    async def run():
        # Default 'user' tier budget is 30/window - well under that.
        for _ in range(5):
            await check_rate_limit(key, "user")

    asyncio.run(run())
    print("[PASS] 5 requests under the 30-request budget all succeeded with no exception.")


def test_exceeding_budget_raises_429_with_retry_after():
    print("\n--- Testing that exceeding the budget raises HTTP 429 with Retry-After ---")
    key = _unique_key("exceed_budget")

    async def run():
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "3"
        os.environ["RATE_LIMIT_USER_WINDOW_SECONDS"] = "60"
        for _ in range(3):
            await check_rate_limit(key, "user")
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(key, "user")
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers
        assert int(exc_info.value.headers["Retry-After"]) > 0
        return exc_info.value

    exc = asyncio.run(run())
    print(f"[PASS] 4th request within the 3-attempt budget raised 429 (detail: {exc.detail!r}).")


def test_backoff_grows_exponentially_across_violations():
    print("\n--- Testing exponential backoff growth across repeated violations ---")
    key = _unique_key("exponential")

    async def run():
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "1"
        os.environ["RATE_LIMIT_USER_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_USER_BACKOFF_BASE_SECONDS"] = "10"
        os.environ["RATE_LIMIT_USER_BACKOFF_MAX_SECONDS"] = "10000"

        await check_rate_limit(key, "user")  # consumes the only slot in the window

        retry_afters = []
        for _ in range(3):
            with pytest.raises(HTTPException) as exc_info:
                await check_rate_limit(key, "user")
            retry_afters.append(int(exc_info.value.headers["Retry-After"]))
            # Force the next check to see the cooldown as already expired (so it re-evaluates
            # the window instead of just re-reporting the still-active block) while leaving
            # the recorded attempt timestamp in place, so the window is still "at capacity"
            # and the next check produces a fresh violation that doubles the backoff.
            from app.rate_limit import _buckets as buckets
            buckets[key].blocked_until = time.time() - 1  # cooldown just expired, but keep the violation streak intact

        # Expect roughly 10s, 20s, 40s (base * 2^0, 2^1, 2^2) - allow +/-1s for the retry-after
        # rounding-up in the implementation.
        assert retry_afters[0] in (10, 11)
        assert retry_afters[1] in (20, 21)
        assert retry_afters[2] in (40, 41)
        return retry_afters

    result = asyncio.run(run())
    print(f"[PASS] Backoff sequence was {result} - each violation roughly doubles the previous one.")


def test_backoff_capped_at_configured_maximum():
    print("\n--- Testing backoff never exceeds the configured maximum ---")
    key = _unique_key("capped")

    async def run():
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "1"
        os.environ["RATE_LIMIT_USER_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_USER_BACKOFF_BASE_SECONDS"] = "10"
        os.environ["RATE_LIMIT_USER_BACKOFF_MAX_SECONDS"] = "25"  # caps after the 2nd doubling

        await check_rate_limit(key, "user")
        from app.rate_limit import _buckets as buckets

        last_retry_after = None
        for _ in range(6):
            with pytest.raises(HTTPException) as exc_info:
                await check_rate_limit(key, "user")
            last_retry_after = int(exc_info.value.headers["Retry-After"])
            buckets[key].blocked_until = time.time() - 1  # cooldown just expired, but keep the violation streak intact

        assert last_retry_after <= 26  # 25s cap + 1s rounding
        return last_retry_after

    result = asyncio.run(run())
    print(f"[PASS] After repeated violations, backoff capped at ~{result}s (configured max: 25s).")


def test_blocked_key_rejected_immediately_during_cooldown():
    print("\n--- Testing a key still inside its cooldown is rejected without re-evaluating the window ---")
    key = _unique_key("cooldown")

    async def run():
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "1"
        os.environ["RATE_LIMIT_USER_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_USER_BACKOFF_BASE_SECONDS"] = "50"
        os.environ["RATE_LIMIT_USER_BACKOFF_MAX_SECONDS"] = "3600"

        await check_rate_limit(key, "user")
        with pytest.raises(HTTPException):
            await check_rate_limit(key, "user")  # triggers the cooldown
        # Still inside the 50s cooldown - must reject immediately again.
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(key, "user")
        return exc_info.value

    exc = asyncio.run(run())
    assert exc.status_code == 429
    print("[PASS] Repeated requests during an active cooldown are consistently rejected with 429.")


def test_per_ip_and_per_account_keys_are_independent():
    print("\n--- Testing per-IP and per-account buckets don't interfere with each other ---")

    async def run():
        os.environ["RATE_LIMIT_AUTH_MAX_ATTEMPTS"] = "2"
        os.environ["RATE_LIMIT_AUTH_WINDOW_SECONDS"] = "60"

        ip_key = f"auth:ip:{uuid.uuid4().hex[:8]}"
        account_key = f"auth:account:{uuid.uuid4().hex[:8]}"

        # Exhaust the IP bucket only.
        await check_rate_limit(ip_key, "auth")
        await check_rate_limit(ip_key, "auth")
        with pytest.raises(HTTPException):
            await check_rate_limit(ip_key, "auth")

        # The account bucket (a different key, same tier) must be completely unaffected.
        await check_rate_limit(account_key, "auth")
        await check_rate_limit(account_key, "auth")

    asyncio.run(run())
    print("[PASS] Exhausting the per-IP bucket did not consume or block the independent per-account bucket.")


def test_reset_clears_key_immediately():
    print("\n--- Testing reset_rate_limit() clears a key's state immediately ---")
    key = _unique_key("reset")

    async def run():
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "1"
        os.environ["RATE_LIMIT_USER_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_USER_BACKOFF_BASE_SECONDS"] = "3600"

        await check_rate_limit(key, "user")
        with pytest.raises(HTTPException):
            await check_rate_limit(key, "user")

        await reset_rate_limit(key)
        # Should succeed immediately post-reset despite the huge backoff configured above.
        await check_rate_limit(key, "user")

    asyncio.run(run())
    print("[PASS] reset_rate_limit() immediately un-blocked a key that was mid-cooldown.")


def test_thresholds_are_environment_configurable_not_hardcoded():
    print("\n--- Testing thresholds change behavior via environment variables alone ---")
    key_a = _unique_key("env_a")
    key_b = _unique_key("env_b")

    async def run():
        # Tight budget: 2nd request in the same window must fail.
        os.environ["RATE_LIMIT_PUBLIC_MAX_ATTEMPTS"] = "1"
        os.environ["RATE_LIMIT_PUBLIC_WINDOW_SECONDS"] = "60"
        await check_rate_limit(key_a, "public")
        with pytest.raises(HTTPException):
            await check_rate_limit(key_a, "public")

        # Loosen the same tier's budget via env var alone (no code change) - a fresh key under
        # the new, higher budget must now tolerate several requests.
        os.environ["RATE_LIMIT_PUBLIC_MAX_ATTEMPTS"] = "10"
        for _ in range(5):
            await check_rate_limit(key_b, "public")

    asyncio.run(run())
    print("[PASS] Changing RATE_LIMIT_PUBLIC_MAX_ATTEMPTS via env var alone changed enforcement behavior.")


def test_disabled_switch_bypasses_all_enforcement():
    print("\n--- Testing RATE_LIMIT_ENABLED=false disables enforcement entirely ---")
    key = _unique_key("disabled")

    async def run():
        os.environ["RATE_LIMIT_ENABLED"] = "false"
        os.environ["RATE_LIMIT_USER_MAX_ATTEMPTS"] = "1"
        assert is_enabled() is False
        for _ in range(20):
            await check_rate_limit(key, "user")  # would raise well before 20 if enabled

    asyncio.run(run())
    print("[PASS] With RATE_LIMIT_ENABLED=false, 20 rapid requests against a 1-attempt budget all succeeded.")


def test_unknown_tier_fails_open():
    print("\n--- Testing an unrecognized tier name fails open instead of crashing ---")
    key = _unique_key("unknown_tier")

    async def run():
        for _ in range(50):
            await check_rate_limit(key, "not_a_real_tier")

    asyncio.run(run())
    print("[PASS] An unrecognized tier never raised - it fails open by design, protecting request handling from a config typo.")


if __name__ == "__main__":
    print("================================================================")
    print("RUNNING ACADEMIALINK RATE LIMITING MODULE TEST SUITE")
    print("================================================================")
    test_requests_under_budget_pass_through()
    test_exceeding_budget_raises_429_with_retry_after()
    test_backoff_grows_exponentially_across_violations()
    test_backoff_capped_at_configured_maximum()
    test_blocked_key_rejected_immediately_during_cooldown()
    test_per_ip_and_per_account_keys_are_independent()
    test_reset_clears_key_immediately()
    test_thresholds_are_environment_configurable_not_hardcoded()
    test_disabled_switch_bypasses_all_enforcement()
    test_unknown_tier_fails_open()
    print("================================================================")
    print("ALL RATE LIMITING TESTS PASSED SUCCESSFULLY!")
    print("================================================================")
