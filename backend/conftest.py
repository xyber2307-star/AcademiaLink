"""
Pytest session-wide configuration.

Rate limiting (see app/rate_limit.py) is disabled for the test session. This is NOT a way of
avoiding testing it - app/rate_limit.py has its own dedicated, thorough unit test suite
(test_rate_limit_module.py) that exercises the limiter directly with real per-key assertions.

It's disabled here because FastAPI's TestClient reports the same synthetic client host
("testclient") for every request in every test module, so every test file's freshly-created
accounts (most modules mint several fresh UUID-based test UIDs) would otherwise share a single
per-IP bucket and start tripping each other's 429s partway through an unrelated test file -
an artifact of the test client, not a real security signal. Setting this before any test module
imports app.main ensures every route sees rate limiting off for the whole session.
"""
import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
