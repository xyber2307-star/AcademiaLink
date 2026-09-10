"""
AcademiaLINK Backend Test Suite
Tests endpoints, schemas, authentication error handling, and deterministic skill gap calculations.
"""

import sys
import os
from fastapi.testclient import TestClient

# Ensure app package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.routes.matching import compute_skill_gap, normalize_proficiency_to_comparison

client = TestClient(app)


def test_health_endpoint():
    """Verify /api/health responds with 200 OK and valid payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "academialink-api"
    assert "version" in data
    assert "timestamp" in data
    print("[PASS] test_health_endpoint passed")


def test_openapi_docs():
    """Verify FastAPI automatically generates valid OpenAPI specification."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert "paths" in spec
    assert "/api/health" in spec["paths"]
    assert "/api/auth/me" in spec["paths"]
    assert "/api/users/me" in spec["paths"]
    assert "/api/skills/me" in spec["paths"]
    assert "/api/jobs" in spec["paths"]
    assert "/api/matching/job/{job_id}" in spec["paths"]
    print("[PASS] test_openapi_docs passed")


def test_auth_me_missing_token():
    """Verify /api/auth/me rejects requests without Authorization header with HTTP 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Authorization header" in response.json()["detail"]
    print("[PASS] test_auth_me_missing_token passed")


def test_auth_me_invalid_token():
    """Verify /api/auth/me rejects invalid bearer token with HTTP 401."""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_fake_token_xyz"})
    assert response.status_code == 401
    print("[PASS] test_auth_me_invalid_token passed")


def test_deterministic_skill_gap_1_to_5_scale():
    """
    Test deterministic skill-gap calculation using 1-5 scale:
    Required: Python = 4, React = 3, SQL = 3
    Student: Python = 4, React = 2, SQL = 3
    Result:
      Python -> matched
      React  -> gap
      SQL    -> matched
    Match score = 2 / 3 * 100 = 67%
    """
    required = [
        {"name": "Python", "minimumProficiency": 4},
        {"name": "React", "minimumProficiency": 3},
        {"name": "SQL", "minimumProficiency": 3},
    ]
    student = {
        "Python": 4,
        "React": 2,
        "SQL": 3,
    }

    score, matched, gaps = compute_skill_gap(student, required)

    assert score == 67, f"Expected 67% match score, got {score}"
    assert len(matched) == 2, f"Expected 2 matched skills, got {len(matched)}"
    assert len(gaps) == 1, f"Expected 1 skill gap, got {len(gaps)}"

    matched_names = {m.skill for m in matched}
    assert "Python" in matched_names
    assert "SQL" in matched_names

    gap_item = gaps[0]
    assert gap_item.skill == "React"
    assert gap_item.current == 2
    assert gap_item.required == 3
    assert gap_item.gap == 20  # normalized gap
    print("[PASS] test_deterministic_skill_gap_1_to_5_scale passed (Match score: 67%)")


def test_deterministic_skill_gap_percentage_scale():
    """
    Test deterministic skill-gap calculation using 0-100 scale:
    Required: React: 80, JavaScript: 85, TypeScript: 80
    Student:  React: 86, JavaScript: 88, TypeScript: 62
    Result:
      React: 86 >= 80 -> matched
      JavaScript: 88 >= 85 -> matched
      TypeScript: 62 < 80 -> gap (gap = 18)
    Match score = 2 / 3 * 100 = 67%
    """
    required = [
        {"name": "React", "minimumProficiency": 80},
        {"name": "JavaScript", "minimumProficiency": 85},
        {"name": "TypeScript", "minimumProficiency": 80},
    ]
    student = {
        "React": 86,
        "JavaScript": 88,
        "TypeScript": 62,
    }

    score, matched, gaps = compute_skill_gap(student, required)

    assert score == 67
    assert len(matched) == 2
    assert len(gaps) == 1
    assert gaps[0].skill == "TypeScript"
    assert gaps[0].gap == 18
    print("[PASS] test_deterministic_skill_gap_percentage_scale passed (Match score: 67%)")


def test_deterministic_skill_gap_100_percent():
    """Test when all required skills are satisfied."""
    required = [
        {"name": "React", "minimumProficiency": 70},
        {"name": "Node.js", "minimumProficiency": 70},
    ]
    student = {
        "React": 80,
        "Node.js": 75,
    }

    score, matched, gaps = compute_skill_gap(student, required)
    assert score == 100
    assert len(matched) == 2
    assert len(gaps) == 0
    print("[PASS] test_deterministic_skill_gap_100_percent passed")


if __name__ == "__main__":
    print("\n--- Running AcademiaLINK Backend Tests ---")
    test_health_endpoint()
    test_openapi_docs()
    test_auth_me_missing_token()
    test_auth_me_invalid_token()
    test_deterministic_skill_gap_1_to_5_scale()
    test_deterministic_skill_gap_percentage_scale()
    test_deterministic_skill_gap_100_percent()
    print("\nAll automated tests passed successfully!")

