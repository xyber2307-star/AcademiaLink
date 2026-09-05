"""Firebase integration layer for AcademiaLINK.

Application services should use this package instead of importing the Firebase SDK
for authentication, Firestore, or Storage operations.
"""

from .auth import verify_id_token
from .firestore import get_firestore_client
from .storage import get_storage_bucket

__all__ = ["verify_id_token", "get_firestore_client", "get_storage_bucket"]
