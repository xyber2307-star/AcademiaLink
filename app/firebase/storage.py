"""Minimal Firebase Storage gateway for evidence/file workflows."""

from __future__ import annotations

from pathlib import PurePosixPath

from google.cloud.storage import Blob
from google.cloud.storage.bucket import Bucket

from .config import get_firebase_app, get_firebase_settings


class FirebaseStorageError(RuntimeError):
    """Raised when Firebase Storage is not configured or an operation fails."""


def get_storage_bucket() -> Bucket:
    """Return the configured Firebase Storage bucket."""
    get_firebase_app()
    from firebase_admin import storage

    bucket_name = get_firebase_settings().firebase_storage_bucket
    try:
        return storage.bucket(bucket_name) if bucket_name else storage.bucket()
    except Exception as exc:
        raise FirebaseStorageError("Firebase Storage is not configured") from exc


def build_storage_path(*parts: str) -> str:
    """Build a normalized object path without allowing path traversal."""
    cleaned: list[str] = []
    for part in parts:
        value = str(part).replace("\\", "/").strip("/")
        if not value or value in {".", ".."} or "../" in f"{value}/":
            raise ValueError("invalid storage path segment")
        cleaned.append(value)
    if not cleaned:
        raise ValueError("at least one storage path segment is required")
    return str(PurePosixPath(*cleaned))


def upload_bytes(
    data: bytes,
    storage_path: str,
    *,
    content_type: str | None = None,
) -> str:
    """Upload bytes and return the Firebase Storage object path."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not storage_path:
        raise ValueError("storage_path is required")

    blob: Blob = get_storage_bucket().blob(storage_path)
    blob.upload_from_string(data, content_type=content_type)
    return blob.name


def delete_file(storage_path: str) -> None:
    """Delete one object from Firebase Storage."""
    if not storage_path:
        raise ValueError("storage_path is required")
    get_storage_bucket().blob(storage_path).delete()
