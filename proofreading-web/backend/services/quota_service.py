"""
Quota management service using Firestore.
Handles SSIM comparison limits and AI analysis limits per tier.

Tiers:
  - anonymous:  SSIM only (no AI), 1 SSIM/day (IP-based)
  - free:       SSIM unlimited, 10 AI analyses lifetime (trial)
  - pro:        SSIM unlimited, 100 AI analyses/month (reset monthly)
  - enterprise: SSIM unlimited, AI unlimited
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import TypedDict
from google.cloud import firestore as cloud_firestore
from services.firebase_admin import get_firestore_client


# SSIM daily quota limits (anonymous only — authenticated users are unlimited)
SSIM_QUOTA_LIMITS = {
    'anonymous': 1,       # IP-based, 1 SSIM/day
    'free': 10,           # 10 SSIM/day (encourages upgrade)
    'pro': 999999,        # Unlimited SSIM
    'enterprise': 999999, # Unlimited SSIM
}

# AI analysis quota limits
AI_QUOTA_LIMITS = {
    'anonymous': 0,       # No AI for anonymous users
    'free': 10,           # 10 AI analyses lifetime (trial)
    'pro': 100,           # 100 AI analyses per month
    'enterprise': 999999, # Unlimited AI
}

# Legacy alias kept for backward compatibility with existing code
QUOTA_LIMITS = SSIM_QUOTA_LIMITS


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


# ─── AI Quota ─────────────────────────────────────────────────────────────────

class AIQuotaInfo(TypedDict):
    """AI quota information returned to frontend."""
    used: int
    limit: int
    remaining: int
    resetsAt: str  # ISO string — monthly for pro, 'never' for free lifetime


def get_current_month_string() -> str:
    """Get current year-month as string in UTC (e.g. '2026-04')."""
    return datetime.now(timezone.utc).strftime('%Y-%m')


def get_month_reset_time() -> str:
    """Get first day of next month UTC as ISO string."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1,
                                  hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now.replace(month=now.month + 1, day=1,
                                  hour=0, minute=0, second=0, microsecond=0)
    return next_month.isoformat()


def get_ai_quota(uid: str, tier: str = 'free') -> AIQuotaInfo:
    """
    Get current AI analysis quota for a user.

    Free tier: lifetime counter (never resets).
    Pro tier: monthly counter (resets on 1st of each month).
    Enterprise: always unlimited.

    Args:
        uid: Firebase user ID
        tier: User subscription tier

    Returns:
        AIQuotaInfo with used, limit, remaining, resetsAt
    """
    limit = AI_QUOTA_LIMITS.get(tier, 0)

    if tier == 'enterprise':
        return AIQuotaInfo(used=0, limit=limit, remaining=limit, resetsAt='never')

    db = get_firestore_client()
    ai_ref = db.collection('ai_quota').document(uid)
    ai_doc = ai_ref.get()

    if tier == 'pro':
        # Monthly reset
        current_month = get_current_month_string()
        if ai_doc.exists:
            data = ai_doc.to_dict()
            if data.get('month') != current_month:
                ai_ref.set({'analyses': 0, 'month': current_month})
                used = 0
            else:
                used = data.get('analyses', 0)
        else:
            ai_ref.set({'analyses': 0, 'month': current_month})
            used = 0
        resets_at = get_month_reset_time()
    else:
        # Free tier: lifetime counter
        if ai_doc.exists:
            used = ai_doc.to_dict().get('analyses', 0)
        else:
            ai_ref.set({'analyses': 0})
            used = 0
        resets_at = 'never'

    return AIQuotaInfo(
        used=used,
        limit=limit,
        remaining=max(0, limit - used),
        resetsAt=resets_at,
    )


@cloud_firestore.transactional
def _check_and_increment_ai_in_transaction(transaction, ai_ref, tier: str, limit: int):
    """
    Atomically check AI quota and increment within a Firestore transaction.

    Returns:
        Tuple of (success: bool, used: int)
    """
    if tier == 'enterprise':
        return True, 0

    current_month = get_current_month_string()
    snapshot = ai_ref.get(transaction=transaction)

    if tier == 'pro':
        if snapshot.exists:
            data = snapshot.to_dict()
            if data.get('month') != current_month:
                transaction.set(ai_ref, {'analyses': 1, 'month': current_month})
                return True, 1
            current = data.get('analyses', 0)
            if current >= limit:
                return False, current
            new_count = current + 1
            transaction.update(ai_ref, {'analyses': new_count})
            return True, new_count
        else:
            transaction.set(ai_ref, {'analyses': 1, 'month': current_month})
            return True, 1
    else:
        # Free tier: lifetime
        if snapshot.exists:
            current = snapshot.to_dict().get('analyses', 0)
            if current >= limit:
                return False, current
            new_count = current + 1
            transaction.update(ai_ref, {'analyses': new_count})
            return True, new_count
        else:
            transaction.set(ai_ref, {'analyses': 1})
            return True, 1


def check_and_increment_ai_quota(uid: str, tier: str = 'free') -> tuple[bool, AIQuotaInfo]:
    """
    Atomically check if user has AI quota remaining and increment if so.

    Args:
        uid: Firebase user ID
        tier: User subscription tier

    Returns:
        Tuple of:
        - success (bool): True if quota was available and incremented
        - ai_quota_info (AIQuotaInfo): Updated AI quota information
    """
    if tier == 'anonymous':
        # Anonymous users cannot use AI
        info = AIQuotaInfo(used=0, limit=0, remaining=0, resetsAt='never')
        return False, info

    limit = AI_QUOTA_LIMITS.get(tier, 0)

    if tier == 'enterprise':
        info = AIQuotaInfo(used=0, limit=limit, remaining=limit, resetsAt='never')
        return True, info

    db = get_firestore_client()
    ai_ref = db.collection('ai_quota').document(uid)
    transaction = db.transaction()
    success, used = _check_and_increment_ai_in_transaction(transaction, ai_ref, tier, limit)

    resets_at = get_month_reset_time() if tier == 'pro' else 'never'
    info = AIQuotaInfo(
        used=used,
        limit=limit,
        remaining=max(0, limit - used),
        resetsAt=resets_at,
    )
    return success, info
