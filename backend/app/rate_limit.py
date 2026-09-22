"""
Configurable rate limiting for the AcademiaLINK API.

Design:
- Three named tiers - AUTH (strict), PUBLIC (moderate), USER (authenticated actions) -
  each independently configurable via environment variables. No threshold is hard-coded;
  every number below is only a fallback default used when the corresponding env var is unset.
- Combines a per-IP key and a per-account key wherever an account identity is available at
  check time, so a single account can't be hammered from many IPs and a single IP can't be
  used to spray attempts across many accounts.
- Uses a sliding window + exponential backoff, never a hard/permanent lockout: once a key
  exceeds its window's attempt budget, it is blocked for a cooldown that starts at
  <TIER>_BACKOFF_BASE_SECONDS and doubles on each further violation while abuse continues,
  capped at <TIER>_BACKOFF_MAX_SECONDS. The cooldown always expires on its own; a legitimate
  user is never locked out indefinitely, and a burst of good behavior after the cooldown
  naturally decays the violation streak back toward zero (see _Bucket.maybe_decay).

Storage is in-process (a plain dict guarded by an asyncio.Lock). That is correct for a
single-process deployment (this API currently runs as a single uvicorn process) but will NOT
share state across multiple processes/instances behind a load balancer - if this service is
ever scaled horizontally, this module's in-memory store should be swapped for a shared
backend (e.g. Redis) using the same tier/key/config model defined here.
"""
from __future__ import annotations

import logging
import os
import time
from asyncio import Lock
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger("academialink.rate_limit")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid float for %s=%r, using default %s", name, raw, default)
        return default


def _env_int(name: str, default: int) -> int:
    return int(_env_float(name, float(default)))


@dataclass
class TierConfig:
    """Read fresh from the environment on every check - never cached at import time - so
    thresholds can be changed via .env / deployment config without touching code."""

    max_attempts_default: int
    window_seconds_default: float
    backoff_base_seconds_default: float
    backoff_max_seconds_default: float
    env_prefix: str

    @property
    def max_attempts(self) -> int:
        return _env_int(f"{self.env_prefix}_MAX_ATTEMPTS", self.max_attempts_default)

    @property
    def window_seconds(self) -> float:
        return _env_float(f"{self.env_prefix}_WINDOW_SECONDS", self.window_seconds_default)

    @property
    def backoff_base_seconds(self) -> float:
        return _env_float(f"{self.env_prefix}_BACKOFF_BASE_SECONDS", self.backoff_base_seconds_default)

    @property
    def backoff_max_seconds(self) -> float:
        return _env_float(f"{self.env_prefix}_BACKOFF_MAX_SECONDS", self.backoff_max_seconds_default)


# Fallback defaults only - every value is overridable via the named environment variable.
TIERS: Dict[str, TierConfig] = {
    # Strict: the real authentication boundary of this API (Firebase ID token verification,
    # first-time profile provisioning on PUT /users/me, and other credential-adjacent actions).
    # Firebase Auth itself (sign-in/sign-up/password-reset) runs client-side against Google's
    # infrastructure and is rate-limited there; this tier protects OUR backend's own auth
    # boundary - the equivalent of "login" from this API's point of view.
    "auth": TierConfig(
        max_attempts_default=5,
        window_seconds_default=300,   # 5 minutes
        backoff_base_seconds_default=30,
        backoff_max_seconds_default=3600,  # 1 hour ceiling
        env_prefix="RATE_LIMIT_AUTH",
    ),
    # Moderate: unauthenticated, publicly-reachable read endpoints (e.g. job listings).
    "public": TierConfig(
        max_attempts_default=60,
        window_seconds_default=60,
        backoff_base_seconds_default=10,
        backoff_max_seconds_default=600,
        env_prefix="RATE_LIMIT_PUBLIC",
    ),
    # Per-account: sensitive actions taken by an already-authenticated user (assessment
    # submission, evidence upload, role changes, job posting) - more headroom than the auth
    # tier since the caller is a verified account, but still bounded.
    "user": TierConfig(
        max_attempts_default=30,
        window_seconds_default=60,
        backoff_base_seconds_default=15,
        backoff_max_seconds_default=900,
        env_prefix="RATE_LIMIT_USER",
    ),
}


@dataclass
class _Bucket:
    timestamps: List[float] = field(default_factory=list)
    violation_count: int = 0
    blocked_until: float = 0.0
    last_violation_at: float = 0.0

    def maybe_decay(self, now: float, window_seconds: float) -> None:
        """
        A sustained period of good behavior resets the backoff streak: once the current
        cooldown has been over for at least two full windows with no further violation, the
        next violation starts back at the base backoff instead of continuing to double
        forever. This is what makes the block "exponential backoff" rather than a permanent
        escalating lockout.
        """
        if self.violation_count and now - self.blocked_until > 2 * window_seconds:
            self.violation_count = 0


_buckets: Dict[str, _Bucket] = {}
_lock = Lock()


def is_enabled() -> bool:
    return _env_bool("RATE_LIMIT_ENABLED", True)


def get_client_ip(request: Request) -> str:
    """
    Resolves the caller's IP for per-IP limiting. Only trusts X-Forwarded-For when
    RATE_LIMIT_TRUST_PROXY is explicitly enabled (this API is not behind a known proxy by
    default, and blindly trusting a client-supplied header would let the IP-based limit be
    trivially spoofed).
    """
    if _env_bool("RATE_LIMIT_TRUST_PROXY", False):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(key: str, tier: str) -> None:
    """
    Records one attempt for `key` under the given tier and raises HTTP 429 (with a
    Retry-After header) if the key is currently in its backoff cooldown or has just exceeded
    its window's attempt budget. Never raises for an unrecognized tier misconfiguration -
    logs and fails open instead, since a bug in rate limiting must not itself take the API down.
    """
    if not is_enabled():
        return

    config = TIERS.get(tier)
    if config is None:
        logger.error("Unknown rate limit tier '%s' - failing open (no limit applied).", tier)
        return

    now = time.time()

    async with _lock:
        bucket = _buckets.setdefault(key, _Bucket())
        bucket.maybe_decay(now, config.window_seconds)

        if now < bucket.blocked_until:
            retry_after = round(bucket.blocked_until - now, 1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        # Prune attempts outside the current sliding window.
        window_start = now - config.window_seconds
        bucket.timestamps = [t for t in bucket.timestamps if t >= window_start]

        if len(bucket.timestamps) >= config.max_attempts:
            bucket.violation_count += 1
            bucket.last_violation_at = now
            backoff = min(
                config.backoff_base_seconds * (2 ** (bucket.violation_count - 1)),
                config.backoff_max_seconds,
            )
            bucket.blocked_until = now + backoff
            logger.warning(
                "Rate limit exceeded for key=%s tier=%s (violation #%d) - backing off %.1fs",
                key, tier, bucket.violation_count, backoff,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {backoff:.0f} seconds.",
                headers={"Retry-After": str(int(backoff) + 1)},
            )

        bucket.timestamps.append(now)


async def reset_rate_limit(key: str) -> None:
    """
    Clears a key's recorded attempts and violation streak immediately. Intended to be called
    after a genuinely successful sensitive action (e.g. a successful login) so a legitimate
    user who mistyped a password a few times isn't still throttled on their next real attempt.
    """
    async with _lock:
        _buckets.pop(key, None)


async def require_auth_rate_limit(request: Request) -> None:
    """Dependency for the auth-tier boundary: per-IP only (no account identity yet available)."""
    await check_rate_limit(f"auth:ip:{get_client_ip(request)}", "auth")


async def require_public_rate_limit(request: Request) -> None:
    """Dependency for moderate-tier public endpoints: per-IP only."""
    await check_rate_limit(f"public:ip:{get_client_ip(request)}", "public")


async def check_user_rate_limit(uid: str, action: str) -> None:
    """
    User-tier check keyed per-account (per Firebase UID) for a specific sensitive action.
    Callers pass a short `action` label (e.g. "assessment_submit", "evidence_upload") so
    different actions don't share one bucket per user. Call this at the top of a route body,
    once `current_user.uid` is available from `Depends(get_current_user)`.
    """
    await check_rate_limit(f"user:{action}:{uid}", "user")


async def check_account_rate_limit(account_identifier: str) -> None:
    """
    Auth-tier check keyed by a claimed account identifier (e.g. an email address from a
    request body, or a decoded token's UID) rather than by IP - combined with
    `require_auth_rate_limit`'s per-IP check, this stops both "many attempts against one
    account from many IPs" and "many accounts attempted from one IP".
    """
    await check_rate_limit(f"auth:account:{account_identifier.lower()}", "auth")
