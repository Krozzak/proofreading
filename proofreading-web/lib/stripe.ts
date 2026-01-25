/**
 * Stripe client-side utilities.
 * Handles checkout sessions and customer portal redirects.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type BillingPeriod = 'monthly' | 'yearly';

/**
 * Subscription information from the backend.
 */
export interface SubscriptionInfo {
  status: string;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
  tier: string;
  billingPeriod: string | null;
}

/**
 * Create a checkout session and redirect to Stripe.
 *
 * @param token - Firebase auth token
 * @param billingPeriod - 'monthly' or 'yearly'
 */
export async function redirectToCheckout(
  token: string,
  billingPeriod: BillingPeriod = 'monthly'
): Promise<void> {
  const response = await fetch(`${API_URL}/api/stripe/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      billingPeriod,
      successUrl: `${window.location.origin}/dashboard?upgraded=true`,
      cancelUrl: `${window.location.origin}/pricing?canceled=true`,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create checkout session');
  }

  const { url } = await response.json();
  window.location.href = url;
}

/**
 * Redirect to Stripe Customer Portal for subscription management.
 *
 * @param token - Firebase auth token
 */
export async function redirectToCustomerPortal(token: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/stripe/portal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      returnUrl: `${window.location.origin}/dashboard`,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create portal session');
  }

  const { url } = await response.json();
  window.location.href = url;
}

/**
 * Fetch subscription information from the backend.
 *
 * @param token - Firebase auth token
 * @returns Subscription info including status, period end, and tier
 */
export async function getSubscription(token: string): Promise<SubscriptionInfo> {
  const response = await fetch(`${API_URL}/api/subscription`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch subscription');
  }

  return response.json();
}

/**
 * Format subscription period end date for display.
 *
 * @param dateString - ISO date string
 * @returns Formatted date string in French locale
 */
export function formatPeriodEnd(dateString: string | null): string {
  if (!dateString) return '-';

  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Get human-readable subscription status.
 *
 * @param status - Stripe subscription status
 * @returns French translation of the status
 */
export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: 'Actif',
    canceled: 'Annulé',
    past_due: 'Paiement en retard',
    trialing: 'Essai',
    incomplete: 'Incomplet',
    incomplete_expired: 'Expiré',
    unpaid: 'Impayé',
    none: 'Aucun',
  };

  return labels[status] || status;
}

/**
 * Get status color class for display.
 *
 * @param status - Stripe subscription status
 * @returns Tailwind color class
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
    case 'trialing':
      return 'text-green-600';
    case 'past_due':
    case 'incomplete':
      return 'text-yellow-600';
    case 'canceled':
    case 'unpaid':
    case 'incomplete_expired':
      return 'text-red-600';
    default:
      return 'text-muted-foreground';
  }
}
