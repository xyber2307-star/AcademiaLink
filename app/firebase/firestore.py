"""Small Firestore gateway used by application repositories/services.

Business logic should pass plain mappings to this module. Pydantic/domain models
stay outside the Firebase SDK boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from google.cloud.firestore_v1 import Client

from .config import get_firebase_app


def get_firestore_client() -> Client:
    """Return the process-wide Firestore client for the configured Firebase app."""
    get_firebase_app()
    from firebase_admin import firestore

    return firestore.client()


def get_document(collection: str, document_id: str) -> dict[str, Any] | None:
    """Read one Firestore document, returning ``None`` when it does not exist."""
    if not collection or not document_id:
        raise ValueError("collection and document_id are required")

    snapshot = get_firestore_client().collection(collection).document(document_id).get()
    if not snapshot.exists:
        return None
    return {"id": snapshot.id, **(snapshot.to_dict() or {})}


def list_documents(
    collection: str,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """List documents from a collection, optionally capped by ``limit``."""
    if not collection:
        raise ValueError("collection is required")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be greater than zero")

    query = get_firestore_client().collection(collection)
    if limit is not None:
        query = query.limit(limit)
    return [{"id": doc.id, **(doc.to_dict() or {})} for doc in query.stream()]


def set_document(
    collection: str,
    document_id: str,
    data: Mapping[str, Any],
    *,
    merge: bool = False,
) -> None:
    """Create or replace a document, with optional Firestore merge semantics."""
    if not collection or not document_id:
        raise ValueError("collection and document_id are required")
    get_firestore_client().collection(collection).document(document_id).set(
        dict(data), merge=merge
    )


def update_document(collection: str, document_id: str, data: Mapping[str, Any]) -> None:
    """Update fields on an existing Firestore document."""
    if not collection or not document_id:
        raise ValueError("collection and document_id are required")
    if not data:
        raise ValueError("data must not be empty")
    get_firestore_client().collection(collection).document(document_id).update(dict(data))


def delete_document(collection: str, document_id: str) -> None:
    """Delete one Firestore document."""
    if not collection or not document_id:
        raise ValueError("collection and document_id are required")
    get_firestore_client().collection(collection).document(document_id).delete()


def batch_set_documents(
    collection: str,
    documents: Sequence[tuple[str, Mapping[str, Any]]],
) -> None:
    """Write multiple documents atomically in one Firestore batch."""
    if not collection:
        raise ValueError("collection is required")
    if not documents:
        return

    client = get_firestore_client()
    batch = client.batch()
    collection_ref = client.collection(collection)
    for document_id, data in documents:
        if not document_id:
            raise ValueError("document_id is required for every batch item")
        batch.set(collection_ref.document(document_id), dict(data))
    batch.commit()
