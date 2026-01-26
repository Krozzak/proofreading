'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/lib/auth-context';
import { redirectToCheckout, type BillingPeriod } from '@/lib/stripe';
import { AuthModal } from '@/components/AuthModal';

const MONTHLY_PRICE = 4.99;
const YEARLY_PRICE = 47.90;
const YEARLY_SAVINGS = Math.round((MONTHLY_PRICE * 12 - YEARLY_PRICE) * 100) / 100;

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PricingModal({ isOpen, onClose }: PricingModalProps) {
  const { user, getIdToken, quota } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('yearly');

  if (!isOpen) return null;

  const currentPlan = quota
    ? quota.limit >= 100
      ? 'Pro'
      : 'Gratuit'
    : null;

  const handleUpgrade = async () => {
    if (!user) {
      setShowAuth(true);
      return;
    }

    setCheckoutLoading(true);
    setError(null);

    try {
      const token = await getIdToken();
      if (!token) throw new Error('Not authenticated');
      await redirectToCheckout(token, billingPeriod);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue. Veuillez réessayer.');
      setCheckoutLoading(false);
    }
  };

  const plans = [
    {
      name: 'Gratuit',
      price: '0',
      period: '/mois',
      description: 'Pour essayer ProofsLab',
      features: [
        '5 comparaisons par jour',
        'Comparaison SSIM standard',
        'Export CSV des résultats',
      ],
      highlighted: false,
    },
    {
      name: 'Pro',
      price: billingPeriod === 'monthly' ? MONTHLY_PRICE.toFixed(2) : (YEARLY_PRICE / 12).toFixed(2),
      period: '/mois',
      yearlyTotal: billingPeriod === 'yearly' ? `$${YEARLY_PRICE}/an` : null,
      description: 'Pour les professionnels',
      features: [
        '100 comparaisons par jour',
        'Comparaison SSIM haute précision',
        'Support prioritaire',
      ],
      highlighted: true,
    },
  ];

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        onClick={onClose}
      >
        <Card
          className="w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Passer au plan Pro</h2>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground text-xl"
            >
              ✕
            </button>
          </div>

          {/* Billing toggle */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-4 bg-muted rounded-full p-1">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  billingPeriod === 'monthly'
                    ? 'bg-background shadow-sm'
                    : 'hover:bg-background/50'
                }`}
              >
                Mensuel
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ${
                  billingPeriod === 'yearly'
                    ? 'bg-background shadow-sm'
                    : 'hover:bg-background/50'
                }`}
              >
                Annuel
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">
                  -20%
                </span>
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Plans comparison */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`p-4 rounded-lg border-2 ${
                  plan.highlighted
                    ? 'border-primary bg-primary/5'
                    : 'border-muted'
                }`}
              >
                <div className="text-center mb-4">
                  <h3 className="text-lg font-bold">{plan.name}</h3>
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-sm">$</span>
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground text-sm">{plan.period}</span>
                  </div>
                  {plan.yearlyTotal && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Facturé {plan.yearlyTotal}
                      <span className="text-green-600 ml-1">
                        (économisez ${YEARLY_SAVINGS})
                      </span>
                    </p>
                  )}
                </div>

                <ul className="space-y-2">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <span className="text-green-500">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex gap-4">
            <Button
              variant="outline"
              className="flex-1"
              onClick={onClose}
            >
              Annuler
            </Button>
            <Button
              className="flex-1"
              disabled={currentPlan === 'Pro' || checkoutLoading}
              onClick={handleUpgrade}
            >
              {checkoutLoading
                ? 'Redirection...'
                : currentPlan === 'Pro'
                ? 'Déjà Pro'
                : 'Passer au Pro'}
            </Button>
          </div>
        </Card>
      </div>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </>
  );
}
