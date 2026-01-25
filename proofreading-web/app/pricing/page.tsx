'use client';

/**
 * Pricing page with plan comparison and checkout.
 */

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/lib/auth-context';
import { redirectToCheckout, type BillingPeriod } from '@/lib/stripe';
import { AuthModal } from '@/components/AuthModal';

const MONTHLY_PRICE = 4.99;
const YEARLY_PRICE = 47.90;
const YEARLY_SAVINGS = Math.round((MONTHLY_PRICE * 12 - YEARLY_PRICE) * 100) / 100;

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, getIdToken, quota } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('yearly');

  // Check for canceled checkout
  const canceled = searchParams.get('canceled');

  // Determine current plan based on quota
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
      price: billingPeriod === 'monthly' ? '0' : '0',
      period: '/mois',
      description: 'Pour essayer ProofsLab',
      features: [
        '5 comparaisons par jour',
        'Comparaison SSIM standard',
        'Export CSV des résultats',
        'Support par email',
      ],
      notIncluded: [
        'Analyse IA des différences',
        'Rapports automatiques',
        'Support prioritaire',
      ],
      cta: 'Commencer gratuitement',
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
        'Export CSV des résultats',
        'Analyse IA des différences (bientôt)',
        'Rapports automatiques (bientôt)',
        'Support prioritaire',
      ],
      notIncluded: [],
      cta: 'Passer au Pro',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Sur devis',
      period: '',
      description: 'Pour les grandes équipes',
      features: [
        'Comparaisons illimitées',
        'Toutes les fonctionnalités Pro',
        'SSO et gestion des équipes',
        'API dédiée',
        'Support dédié 24/7',
        'Formation personnalisée',
      ],
      notIncluded: [],
      cta: 'Nous contacter',
      highlighted: false,
    },
  ];

  return (
    <main className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-primary text-white py-6 px-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-4">
            <Image
              src="/logo.png"
              alt="ProofsLab Logo"
              width={48}
              height={48}
              className="drop-shadow-lg"
            />
            <div>
              <h1 className="text-2xl font-bold tracking-tight">ProofsLab</h1>
              <p className="text-primary-foreground/80 text-sm">Tarifs</p>
            </div>
          </Link>
          <Link href="/">
            <Button variant="secondary" size="sm">
              Retour
            </Button>
          </Link>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">
            Choisissez votre plan
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto mb-8">
            Commencez gratuitement et passez au Pro quand vous en avez besoin.
            Annulez à tout moment.
          </p>

          {/* Billing toggle */}
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

        {canceled && (
          <div className="max-w-md mx-auto mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
            <p className="text-yellow-800">
              Paiement annulé. Vous pouvez réessayer quand vous le souhaitez.
            </p>
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto mb-8 bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Plans grid */}
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`p-6 flex flex-col ${
                plan.highlighted
                  ? 'border-primary border-2 relative'
                  : ''
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-white text-xs font-bold px-3 py-1 rounded-full">
                  POPULAIRE
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="flex items-baseline justify-center gap-1">
                  {plan.name !== 'Enterprise' && <span className="text-lg">$</span>}
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                {plan.yearlyTotal && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Facturé {plan.yearlyTotal}
                    <span className="text-green-600 ml-1">
                      (économisez ${YEARLY_SAVINGS})
                    </span>
                  </p>
                )}
                <p className="text-sm text-muted-foreground mt-2">
                  {plan.description}
                </p>
              </div>

              <ul className="space-y-3 mb-6 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
                {plan.notIncluded.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-2 text-muted-foreground"
                  >
                    <span className="mt-0.5">✗</span>
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              {plan.name === 'Gratuit' && (
                <Button
                  variant={currentPlan === 'Gratuit' ? 'outline' : 'secondary'}
                  className="w-full"
                  disabled={currentPlan === 'Gratuit'}
                  onClick={() => (user ? router.push('/') : setShowAuth(true))}
                >
                  {currentPlan === 'Gratuit' ? 'Plan actuel' : plan.cta}
                </Button>
              )}

              {plan.name === 'Pro' && (
                <Button
                  className="w-full"
                  disabled={currentPlan === 'Pro' || checkoutLoading}
                  onClick={handleUpgrade}
                >
                  {checkoutLoading
                    ? 'Redirection...'
                    : currentPlan === 'Pro'
                    ? 'Plan actuel'
                    : plan.cta}
                </Button>
              )}

              {plan.name === 'Enterprise' && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() =>
                    (window.location.href = 'mailto:contact@proofslab.com')
                  }
                >
                  {plan.cta}
                </Button>
              )}
            </Card>
          ))}
        </div>

        {/* FAQ section */}
        <div className="mt-16 max-w-2xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-8">
            Questions fréquentes
          </h3>
          <div className="space-y-6">
            <div>
              <h4 className="font-semibold mb-2">
                Puis-je annuler à tout moment ?
              </h4>
              <p className="text-muted-foreground">
                Oui, vous pouvez annuler votre abonnement à tout moment depuis
                votre tableau de bord. Vous conserverez l&apos;accès Pro jusqu&apos;à la
                fin de votre période de facturation.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">
                Quels moyens de paiement acceptez-vous ?
              </h4>
              <p className="text-muted-foreground">
                Nous acceptons les cartes Visa, Mastercard et American Express
                via notre partenaire Stripe.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">
                Que se passe-t-il si j&apos;atteins ma limite ?
              </h4>
              <p className="text-muted-foreground">
                Votre quota est réinitialisé chaque jour à minuit (UTC). Si vous
                atteignez votre limite, vous pouvez passer au plan supérieur
                pour continuer immédiatement.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">
                L&apos;abonnement annuel est-il remboursable ?
              </h4>
              <p className="text-muted-foreground">
                Nous offrons un remboursement complet dans les 14 jours suivant
                votre achat si vous n&apos;êtes pas satisfait.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-muted-foreground border-t">
        <p>ProofsLab v1.2.0 - PDF Comparison Laboratory</p>
      </footer>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </main>
  );
}
