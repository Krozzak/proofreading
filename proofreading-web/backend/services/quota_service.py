"""
Quota management service using Firestore.
Handles daily comparison limits for users with atomic transactions.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import TypedDict
from google.cloud import firestore as cloud_firestore
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


def _build_quota_info(used: int, tier: str) -> QuotaInfo:
    """Build a QuotaInfo dict from current usage and tier."""
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS['free'])
    return QuotaInfo(
        used=used,
        limit=limit,
        remaining=max(0, limit - used),
        resetsAt=get_reset_time(),
    )


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

    if quota_doc.exists:
        data = quota_doc.to_dict()
        last_reset = data.get('lastReset', '')

        if last_reset != today:
            quota_ref.set({
                'comparisons': 0,
                'lastReset': today,
            })
            used = 0
        else:
            used = data.get('comparisons', 0)
    else:
        quota_ref.set({
            'comparisons': 0,
            'lastReset': today,
        })
        used = 0

    return _build_quota_info(used, tier)


@cloud_firestore.transactional
def _check_and_increment_in_transaction(transaction, quota_ref, today: str, limit: int):
    """
    Atomically check quota and increment within a Firestore transaction.
    Prevents race conditions from concurrent requests.

    Returns:
        Tuple of (success: bool, used: int)
    """
    snapshot = quota_ref.get(transaction=transaction)

    if snapshot.exists:
        data = snapshot.to_dict()
        last_reset = data.get('lastReset', '')

        if last_reset != today:
            # New day - reset and set to 1
            transaction.set(quota_ref, {
                'comparisons': 1,
                'lastReset': today,
            })
            return True, 1
        else:
            current = data.get('comparisons', 0)
            if current >= limit:
                return False, current
            new_count = current + 1
            transaction.update(quota_ref, {'comparisons': new_count})
            return True, new_count
    else:
        # First comparison ever
        transaction.set(quota_ref, {
            'comparisons': 1,
            'lastReset': today,
        })
        return True, 1


def check_and_increment_quota(uid: str, tier: str = 'free') -> tuple[bool, QuotaInfo]:
    """
    Atomically check if user has quota remaining and increment if so.

    Uses a Firestore transaction to prevent race conditions where
    concurrent requests could bypass the quota limit.

    Args:
        uid: Firebase user ID
        tier: User subscription tier

    Returns:
        Tuple of:
        - success (bool): True if quota was available and incremented
        - quota_info (QuotaInfo): Updated quota information
    """
    db = get_firestore_client()
    today = get_today_string()
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS['free'])
    quota_ref = db.collection('quotas').document(uid)

    transaction = db.transaction()
    success, used = _check_and_increment_in_transaction(transaction, quota_ref, today, limit)

    return success, _build_quota_info(used, tier)


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
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
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
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
    uid = f"anon_{ip_hash}"

    return check_and_increment_quota(uid, 'anonymous')
