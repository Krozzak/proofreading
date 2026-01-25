"""
Quota management service using Firestore.
Handles daily comparison limits for users.
"""

from datetime import datetime, timezone, timedelta
from typing import TypedDict
from google.cloud.firestore_v1 import FieldFilter
from services.firebase_admin import get_firestore_client


# Quota limits by subscription tier
QUOTA_LIMITS = {
    'anonymous': 1,      # Not logged in - 1 comparison/day
    'free': 5,           # Logged in free account - 5 comparisons/day
    'pro': 100,          # Pro subscription - 100 comparisons/day
    'enterprise': 999999,  # Enterprise - unlimited (on quote)
}


class QuotaInfo(TypedDict):
    """Quota information returned to frontend."""
    used: int
    limit: int
    remaining: int
    resetsAt: str


def get_today_string() -> str:
    """Get today's date as string in UTC."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def get_reset_time() -> str:
    """Get next midnight UTC as ISO string."""
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return tomorrow.isoformat()


def get_quota(uid: str, tier: str = 'free') -> QuotaInfo:
    """
    Get current quota for a user.

    If it's a new day, the quota is automatically reset.

    Args:
        uid: Firebase user ID
        tier: User subscription tier ('free', 'pro', 'enterprise')

    Returns:
        QuotaInfo with used, limit, remaining, and resetsAt
    """
    db = get_firestore_client()
    today = get_today_string()

    quota_ref = db.collection('quotas').document(uid)
    quota_doc = quota_ref.get()

    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS['free'])

    if quota_doc.exists:
        data = quota_doc.to_dict()
        last_reset = data.get('lastReset', '')

        # Reset quota if it's a new day
        if last_reset != today:
            quota_ref.set({
                'comparisons': 0,
                'lastReset': today,
            })
            used = 0
        else:
            used = data.get('comparisons', 0)
    else:
        # Create new quota document for first-time user
        quota_ref.set({
            'comparisons': 0,
            'lastReset': today,
        })
        used = 0

    return QuotaInfo(
        used=used,
        limit=limit,
        remaining=max(0, limit - used),
        resetsAt=get_reset_time(),
    )


def increment_quota(uid: str) -> None:
    """
    Increment the comparison count for a user.

    Uses Firestore increment to avoid race conditions.

    Args:
        uid: Firebase user ID
    """
    from google.cloud.firestore_v1 import Increment

    db = get_firestore_client()
    today = get_today_string()

    quota_ref = db.collection('quotas').document(uid)
    quota_doc = quota_ref.get()

    if quota_doc.exists:
        data = quota_doc.to_dict()
        if data.get('lastReset') != today:
            # New day - reset and set to 1
            quota_ref.set({
                'comparisons': 1,
                'lastReset': today,
            })
        else:
            # Same day - increment
            quota_ref.update({
                'comparisons': Increment(1),
            })
    else:
        # First comparison ever
        quota_ref.set({
            'comparisons': 1,
            'lastReset': today,
        })


def check_and_increment_quota(uid: str, tier: str = 'free') -> tuple[bool, QuotaInfo]:
    """
    Check if user has quota remaining and increment if so.

    This is the main function to call before allowing a comparison.

    Args:
        uid: Firebase user ID
        tier: User subscription tier

    Returns:
        Tuple of:
        - success (bool): True if quota was available and incremented
        - quota_info (QuotaInfo): Updated quota information
    """
    # Get current quota first
    quota = get_quota(uid, tier)

    # Check if quota exceeded
    if quota['remaining'] <= 0:
        return False, quota

    # Increment the quota
    increment_quota(uid)

    # Return updated quota info
    updated_quota = get_quota(uid, tier)
    return True, updated_quota


def get_user_tier(uid: str) -> str:
    """
    Get user's subscription tier from Firestore.

    Args:
        uid: Firebase user ID

    Returns:
        Tier string ('free', 'pro', or 'enterprise')
    """
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if user_doc.exists:
        data = user_doc.to_dict()
        return data.get('tier', 'free')

    return 'free'


def get_anonymous_quota(ip_address: str) -> QuotaInfo:
    """
    Get quota for anonymous user based on IP address.

    Args:
        ip_address: Client IP address

    Returns:
        QuotaInfo with 1 comparison/day limit
    """
    # Use IP hash as document ID to avoid storing raw IPs
    import hashlib
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    uid = f"anon_{ip_hash}"

    return get_quota(uid, 'anonymous')


def check_and_increment_anonymous_quota(ip_address: str) -> tuple[bool, QuotaInfo]:
    """
    Check and increment quota for anonymous user.

    Args:
        ip_address: Client IP address

    Returns:
        Tuple of (success, quota_info)
    """
    import hashlib
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    uid = f"anon_{ip_hash}"

    return check_and_increment_quota(uid, 'anonymous')
