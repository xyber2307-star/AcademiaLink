"""Firebase Admin SDK configuration and application initialization.

Secrets are supplied through the existing Pydantic settings layer. This module
never contains service-account credentials or project secrets in source code.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials

from app.core.config import Settings, get_settings


class FirebaseConfigurationError(RuntimeError):
    """Raised when Firebase cannot be configured from the application settings."""


def _credential_from_settings(settings: Settings) -> credentials.Base:
    raw = settings.firebase_service_account_json
    if not raw:
        raise FirebaseConfigurationError(
            "Firebase credentials are not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON."
        )

    value = raw.strip()
    try:
        service_account = json.loads(value) if value.startswith("{") else None
    except json.JSONDecodeError as exc:
        raise FirebaseConfigurationError(
            "FIREBASE_SERVICE_ACCOUNT_JSON contains invalid JSON."
        ) from exc

    if service_account is not None:
        return credentials.Certificate(service_account)

    credential_path = Path(value).expanduser()
    if not credential_path.is_file():
        raise FirebaseConfigurationError(
            "Firebase credential path does not exist: " f"{credential_path}"
        )
    return credentials.Certificate(str(credential_path))


@lru_cache
def get_firebase_app() -> firebase_admin.App:
    """Return the singleton Firebase Admin application for this process."""
    existing = firebase_admin.get_app() if firebase_admin._apps else None
    if existing is not None:
        return existing

    settings = get_settings()
    return firebase_admin.initialize_app(_credential_from_settings(settings), {
        **({"storageBucket": settings.firebase_storage_bucket}
           if settings.firebase_storage_bucket else {})
    })


def get_firebase_settings() -> Settings:
    """Expose the application's Firebase-related settings without duplicating config."""
    return get_settings()
