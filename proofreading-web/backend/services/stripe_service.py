"""
Stripe integration service.
Handles checkout sessions, subscription management, and webhook processing.
"""

import os
import stripe
import logging
from typing import Optional, TypedDict
from datetime import datetime, timezone

from services.firebase_admin import get_firestore_client

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_MONTHLY = os.environ.get('STRIPE_PRICE_ID_MONTHLY')
STRIPE_PRICE_ID_YEARLY = os.environ.get('STRIPE_PRICE_ID_YEARLY')


class SubscriptionInfo(TypedDict):
    """Subscription information returned to the frontend."""
    status: str  # 'active', 'canceled', 'past_due', 'trialing', 'none'
    currentPeriodEnd: Optional[str]
    cancelAtPeriodEnd: bool
    customerId: Optional[str]
    subscriptionId: Optional[str]
    billingPeriod: Optional[str]  # 'monthly', 'yearly'


def get_price_id(billing_period: str) -> str:
    """Get the Stripe price ID for the given billing period."""
    if billing_period == 'yearly':
        if not STRIPE_PRICE_ID_YEARLY:
            raise ValueError("Yearly price ID not configured")
        return STRIPE_PRICE_ID_YEARLY
    else:
        if not STRIPE_PRICE_ID_MONTHLY:
            raise ValueError("Monthly price ID not configured")
        return STRIPE_PRICE_ID_MONTHLY


def get_or_create_stripe_customer(uid: str, email: str) -> str:
    """
    Get existing or create new Stripe customer for a user.
    Stores customer ID in Firestore users/{uid} document.

    Args:
        uid: Firebase user ID
        email: User's email address

    Returns:
        Stripe customer ID
    """
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if user_doc.exists:
        data = user_doc.to_dict()
        if data and data.get('stripeCustomerId'):
            return data['stripeCustomerId']

    # Create new Stripe customer
    customer = stripe.Customer.create(
        email=email,
        metadata={'firebaseUid': uid}
    )

    # Store in Firestore
    user_ref.set({
        'stripeCustomerId': customer.id,
        'email': email,
    }, merge=True)

    logger.info(f"Created Stripe customer {customer.id} for user {uid}")
    return customer.id


def create_checkout_session(
    uid: str,
    email: str,
    billing_period: str,
    success_url: str,
    cancel_url: str
) -> str:
    """
    Create a Stripe Checkout session for Pro subscription.

    Args:
        uid: Firebase user ID
        email: User's email address
        billing_period: 'monthly' or 'yearly'
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is canceled

    Returns:
        Checkout session URL
    """
    customer_id = get_or_create_stripe_customer(uid, email)
    price_id = get_price_id(billing_period)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'firebaseUid': uid,
            'billingPeriod': billing_period,
        },
        subscription_data={
            'metadata': {
                'firebaseUid': uid,
                'billingPeriod': billing_period,
            }
        },
        allow_promotion_codes=True,
    )

    logger.info(f"Created checkout session for user {uid}, period: {billing_period}")
    return session.url


def create_customer_portal_session(uid: str, return_url: str) -> str:
    """
    Create a Stripe Customer Portal session for managing subscription.

    Args:
        uid: Firebase user ID
        return_url: URL to redirect after portal session

    Returns:
        Customer portal URL

    Raises:
        ValueError: If user not found or has no Stripe customer
    """
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise ValueError("User not found")

    data = user_doc.to_dict()
    if not data:
        raise ValueError("User data is empty")

    customer_id = data.get('stripeCustomerId')

    if not customer_id:
        raise ValueError("No Stripe customer found for this user")

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )

    logger.info(f"Created portal session for user {uid}")
    return session.url


def get_subscription_info(uid: str) -> SubscriptionInfo:
    """
    Get subscription information for a user.

    Args:
        uid: Firebase user ID

    Returns:
        SubscriptionInfo with current subscription details
    """
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    default_info: SubscriptionInfo = {
        'status': 'none',
        'currentPeriodEnd': None,
        'cancelAtPeriodEnd': False,
        'customerId': None,
        'subscriptionId': None,
        'billingPeriod': None,
    }

    if not user_doc.exists:
        return default_info

    data = user_doc.to_dict()
    if not data:
        return default_info

    return SubscriptionInfo(
        status=data.get('subscriptionStatus', 'none'),
        currentPeriodEnd=data.get('subscriptionPeriodEnd'),
        cancelAtPeriodEnd=data.get('cancelAtPeriodEnd', False),
        customerId=data.get('stripeCustomerId'),
        subscriptionId=data.get('stripeSubscriptionId'),
        billingPeriod=data.get('billingPeriod'),
    )


def _find_user_by_customer_id(customer_id: str) -> Optional[str]:
    """Find Firebase UID by Stripe customer ID."""
    db = get_firestore_client()
    users = db.collection('users').where(
        'stripeCustomerId', '==', customer_id
    ).limit(1).get()

    if users:
        return users[0].id
    return None


def handle_checkout_completed(session: dict) -> None:
    """
    Handle successful checkout. Updates user tier to 'pro'.

    Args:
        session: Stripe checkout.session object
    """
    metadata = session.get('metadata', {})
    uid = metadata.get('firebaseUid')
    billing_period = metadata.get('billingPeriod', 'monthly')

    if not uid:
        logger.error("No firebaseUid in checkout session metadata")
        return

    subscription_id = session.get('subscription')
    customer_id = session.get('customer')

    # Fetch subscription details
    subscription = stripe.Subscription.retrieve(subscription_id)

    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    user_ref.set({
        'tier': 'pro',
        'stripeCustomerId': customer_id,
        'stripeSubscriptionId': subscription_id,
        'subscriptionStatus': subscription.status,
        'subscriptionPeriodEnd': datetime.fromtimestamp(
            subscription.current_period_end, timezone.utc
        ).isoformat(),
        'cancelAtPeriodEnd': subscription.cancel_at_period_end,
        'billingPeriod': billing_period,
        'upgradedAt': datetime.now(timezone.utc).isoformat(),
    }, merge=True)

    logger.info(f"User {uid} upgraded to Pro ({billing_period})")


def handle_subscription_updated(subscription: dict) -> None:
    """
    Handle subscription updates (status changes, renewals, cancellations).

    Args:
        subscription: Stripe subscription object
    """
    metadata = subscription.get('metadata', {})
    uid = metadata.get('firebaseUid')

    if not uid:
        # Try to find user by customer ID
        customer_id = subscription.get('customer')
        uid = _find_user_by_customer_id(customer_id)
        if not uid:
            logger.error(f"No user found for subscription {subscription.get('id')}")
            return

    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    # Determine tier based on subscription status
    status = subscription.get('status')
    tier = 'pro' if status in ['active', 'trialing'] else 'free'

    user_ref.set({
        'tier': tier,
        'subscriptionStatus': status,
        'subscriptionPeriodEnd': datetime.fromtimestamp(
            subscription.get('current_period_end'), timezone.utc
        ).isoformat(),
        'cancelAtPeriodEnd': subscription.get('cancel_at_period_end', False),
    }, merge=True)

    logger.info(f"User {uid} subscription updated: {status}")


def handle_subscription_deleted(subscription: dict) -> None:
    """
    Handle subscription cancellation. Downgrades user to free tier.

    Args:
        subscription: Stripe subscription object
    """
    metadata = subscription.get('metadata', {})
    uid = metadata.get('firebaseUid')

    if not uid:
        customer_id = subscription.get('customer')
        uid = _find_user_by_customer_id(customer_id)
        if not uid:
            logger.error(f"No user found for subscription {subscription.get('id')}")
            return

    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    user_ref.set({
        'tier': 'free',
        'subscriptionStatus': 'canceled',
        'stripeSubscriptionId': None,
        'canceledAt': datetime.now(timezone.utc).isoformat(),
    }, merge=True)

    logger.info(f"User {uid} subscription canceled, downgraded to free")


def handle_invoice_payment_failed(invoice: dict) -> None:
    """
    Handle failed invoice payment.
    Updates subscription status but doesn't immediately downgrade.

    Args:
        invoice: Stripe invoice object
    """
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return

    subscription = stripe.Subscription.retrieve(subscription_id)
    handle_subscription_updated(subscription)

    logger.warning(f"Invoice payment failed for subscription {subscription_id}")


def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """
    Verify Stripe webhook signature and return the event.

    Args:
        payload: Raw request body bytes
        signature: Stripe-Signature header value

    Returns:
        Verified Stripe event object

    Raises:
        ValueError: If verification fails
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise ValueError("Invalid webhook signature")
