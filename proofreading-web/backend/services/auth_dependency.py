"""
FastAPI dependency for Firebase authentication.
Provides reusable authentication for protected endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.firebase_admin import verify_token
from services.quota_service import get_user_tier


# Security scheme - extracts Bearer token from Authorization header
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """
    Represents an authenticated user.

    Attributes:
        uid: Firebase user ID
        email: User's email address
        tier: Subscription tier ('free', 'pro', 'enterprise')
    """

    def __init__(self, uid: str, email: str, tier: str = 'free'):
        self.uid = uid
        self.email = email
        self.tier = tier

    def __repr__(self):
        return f"AuthenticatedUser(uid={self.uid}, email={self.email}, tier={self.tier})"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    FastAPI dependency to get the current authenticated user.

    Usage:
        @app.post("/api/protected")
        async def protected_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
            return {"uid": user.uid}

    Raises:
        HTTPException 401: If no token provided or token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify the Firebase token
        decoded = verify_token(credentials.credentials)

        # Get user's subscription tier from Firestore
        tier = get_user_tier(decoded['uid'])

        return AuthenticatedUser(
            uid=decoded['uid'],
            email=decoded.get('email', ''),
            tier=tier,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication dependency.

    Returns None if not authenticated instead of raising an error.
    Useful for endpoints that work differently for authenticated vs anonymous users.

    Usage:
        @app.get("/api/public")
        async def public_endpoint(user: Optional[AuthenticatedUser] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello anonymous"}
    """
    if not credentials:
        return None

    try:
        decoded = verify_token(credentials.credentials)
        tier = get_user_tier(decoded['uid'])

        return AuthenticatedUser(
            uid=decoded['uid'],
            email=decoded.get('email', ''),
            tier=tier,
        )
    except ValueError:
        return None
