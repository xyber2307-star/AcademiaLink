import json
import logging
import os
from typing import Optional
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth

logger = logging.getLogger("academialink.firebase")

# Load .env file from project root or backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

_firebase_initialized = False
_db: Optional[firestore.Client] = None


def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK using environment variables or service account file."""
    global _firebase_initialized, _db

    if _firebase_initialized and firebase_admin._apps:
        return True

    # 1. Check if already initialized by firebase_admin
    if firebase_admin._apps:
        _firebase_initialized = True
        _db = firestore.client()
        return True

    cred = None
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    project_id = os.getenv("FIREBASE_PROJECT_ID", "academialink-b10b3")

    # 2. Check for credentials file path
    if cred_path:
        if not os.path.isabs(cred_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(backend_dir, cred_path)
            if os.path.exists(candidate):
                cred_path = candidate

        if os.path.exists(cred_path):
            try:
                logger.info("Initializing Firebase Admin with credentials file: %s", cred_path)
                cred = credentials.Certificate(cred_path)
            except Exception as e:
                logger.error("Failed to load credentials file from %s: %s", cred_path, e)

    # 3. Check for individual environment variables
    if not cred:
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

        if private_key and client_email:
            try:
                # Replace literal \n with actual newlines
                clean_private_key = private_key.replace("\\n", "\n").strip('"\'')
                cred_dict = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", "key_id"),
                    "private_key": clean_private_key,
                    "client_email": client_email,
                    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", ""),
                }
                logger.info("Initializing Firebase Admin with environment credentials for %s", client_email)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                logger.error("Failed to parse Firebase service account environment variables: %s", e)

    # 4. Check for JSON string in single env var
    if not cred:
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if service_account_json:
            try:
                cred_dict = json.loads(service_account_json)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                logger.error("Failed to parse FIREBASE_SERVICE_ACCOUNT_KEY JSON: %s", e)

    database_id = os.getenv("FIRESTORE_DATABASE_ID", "academia")

    # 5. Initialize application
    try:
        if cred:
            firebase_admin.initialize_app(cred, {"projectId": project_id})
            _firebase_initialized = True
            _db = firestore.client(database_id=database_id)
            logger.info("Firebase Admin initialized successfully with Project ID: %s, Database: %s", project_id, database_id)
            return True
        else:
            # Attempt default credentials or log configuration warning
            try:
                firebase_admin.initialize_app(options={"projectId": project_id})
                _firebase_initialized = True
                _db = firestore.client(database_id=database_id)
                logger.info("Firebase Admin initialized with default credentials / project ID: %s, Database: %s", project_id, database_id)
                return True
            except Exception as e:
                logger.warning(
                    "Firebase Admin credentials not found in environment. "
                    "Set FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and FIREBASE_PRIVATE_KEY in backend/.env. "
                    "Error: %s",
                    e,
                )
                return False
    except Exception as e:
        logger.error("Error during Firebase Admin initialization: %s", e)
        return False


def get_db() -> firestore.Client:
    """Get the Firestore database client. Initializes Firebase if not already initialized."""
    global _db
    if _db is not None:
        return _db
    if not initialize_firebase() or _db is None:
        raise RuntimeError(
            "Firestore is not configured. Please supply Firebase Admin service account credentials in backend/.env"
        )
    return _db


def get_auth_client():
    """Get the Firebase Admin Auth module."""
    if not initialize_firebase():
        raise RuntimeError(
            "Firebase Auth is not configured. Please supply Firebase Admin service account credentials in backend/.env"
        )
    return auth


def is_firebase_ready() -> bool:
    """Check if Firebase Admin is currently initialized and ready."""
    return _firebase_initialized and bool(firebase_admin._apps)
