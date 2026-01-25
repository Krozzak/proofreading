"""
Firebase Admin SDK initialization and helpers.
Handles token verification for authenticated API requests.
"""

import os
import json
import logging
from functools import lru_cache
import firebase_admin
from firebase_admin import credentials, auth, firestore

logger = logging.getLogger(__name__)

# Track initialization state
_initialized = False
_init_error = None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK (lazy initialization).

    Supports multiple credential sources:
    1. FIREBASE_SERVICE_ACCOUNT env var (JSON string) - for Cloud Run secrets
    2. GOOGLE_APPLICATION_CREDENTIALS env var (file path) - for local dev
    3. Application Default Credentials - for Cloud Run with proper IAM
    """
    global _initialized, _init_error

    if _initialized:
        return  # Already initialized successfully

    if firebase_admin._apps:
        _initialized = True
        return  # Already initialized by another path

    try:
        # Check for service account key in environment variable (JSON string)
        if os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
            logger.info("Initializing Firebase with FIREBASE_SERVICE_ACCOUNT env var")
            cred_dict = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
            cred = credentials.Certificate(cred_dict)
        # Check for file path to service account key
        elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            logger.info("Initializing Firebase with GOOGLE_APPLICATION_CREDENTIALS file")
            cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        else:
            # Use Application Default Credentials (Cloud Run with proper IAM)
            logger.info("Initializing Firebase with Application Default Credentials")
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred)
        _initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        _init_error = str(e)
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def ensure_firebase_initialized():
    """Ensure Firebase is initialized before use. Raises clear error if not."""
    if not _initialized and not firebase_admin._apps:
        if _init_error:
            raise RuntimeError(f"Firebase initialization failed: {_init_error}")
        initialize_firebase()


@lru_cache()
def get_firestore_client():
    """Get Firestore client (cached for performance)."""
    ensure_firebase_initialized()
    return firestore.client()


def verify_token(id_token: str) -> dict:
    """
    Verify Firebase ID token and return decoded claims.

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token claims dict containing:
        - uid: User's Firebase UID
        - email: User's email (if available)
        - email_verified: Whether email is verified
        - And other Firebase claims

    Raises:
        ValueError: If token is invalid, expired, or verification fails
    """
    ensure_firebase_initialized()
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise ValueError("Invalid ID token")
    except auth.ExpiredIdTokenError:
        raise ValueError("Token has expired")
    except auth.RevokedIdTokenError:
        raise ValueError("Token has been revoked")
    except auth.CertificateFetchError:
        raise ValueError("Failed to fetch public key certificates")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")


