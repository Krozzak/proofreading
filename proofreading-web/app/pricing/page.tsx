'use client';

/**
 * Pricing page with plan comparison and checkout.
 */

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { redirectToCheckout, type BillingPeriod } from '@/lib/stripe';
import { AuthModal } from '@/components/AuthModal';
import { SpectrumLogo } from '@/components/SpectrumLogo';
import { NavBar } from '@/components/NavBar';

const MONTHLY_PRICE = 20.00;
const YEARLY_PRICE = 192.00;
const YEARLY_SAVINGS = Math.round((MONTHLY_PRICE * 12 - YEARLY_PRICE) * 100) / 100;

function PricingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, getIdToken, quota } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('yearly');

  const canceled = searchParams.get('canceled');
  const currentPlan = quota ? (quota.limit >= 100 ? 'Pro' : 'Gratuit') : null;

  const handleUpgrade = async () => {
    if (!user) { setShowAuth(true); return; }
    setCheckoutLoading(true);
    setError(null);
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Not authenticated');
      await redirectToCheckout(token, billingPeriod);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue.');
      setCheckoutLoading(false);
    }
  };

  const plans = [
    {
      name: 'Gratuit',
      accent: 'var(--c3)',
      price: '0',
      period: '/mois',
      tagline: 'Pour essayer Proofslab',
      description: 'Pour essayer Proofslab',
      features: [
        'Comparaisons SSIM illimitées',
        '10 analyses IA offertes (à vie)',
        'Heatmap des différences',
        'Export CSV des résultats',
        'Support par email',
      ],
      locked: [
        '100 analyses IA / mois',
        'Support prioritaire',
      ],
      cta: 'Commencer gratuitement',
      highlighted: false,
    },
    {
      name: 'Pro',
      accent: 'var(--c4)',
      price: billingPeriod === 'monthly' ? MONTHLY_PRICE.toFixed(2) : (YEARLY_PRICE / 12).toFixed(2),
      period: '/mois',
      yearlyTotal: billingPeriod === 'yearly' ? `$${YEARLY_PRICE}/an` : null,
      description: 'Pour les professionnels',
      features: [
        'Comparaisons SSIM illimitées',
        '100 analyses IA / mois',
        'Heatmap des différences',
        'Rapport IA détaillé par zone',
        'Export CSV des résultats',
        'Support prioritaire',
      ],
      locked: [],
      cta: 'Passer au Pro',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      accent: 'var(--c5)',
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
      locked: [],
      cta: 'Nous contacter',
      highlighted: false,
    },
  ];

  const faq = [
    { q: 'Puis-je annuler à tout moment ?', a: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis votre tableau de bord. Vous conserverez l\'accès Pro jusqu\'à la fin de votre période de facturation.' },
    { q: 'Quels moyens de paiement acceptez-vous ?', a: 'Nous acceptons les cartes Visa, Mastercard et American Express via notre partenaire Stripe.' },
    { q: 'Que se passe-t-il si j\'atteins ma limite ?', a: 'Votre quota est réinitialisé chaque jour à minuit (UTC). Si vous atteignez votre limite, vous pouvez passer au plan supérieur pour continuer immédiatement.' },
    { q: 'L\'abonnement annuel est-il remboursable ?', a: 'Nous offrons un remboursement complet dans les 14 jours suivant votre achat si vous n\'êtes pas satisfait.' },
  ];

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>

      {/* ── Header ── */}
      <NavBar />

      {/* ── Main ── */}
      <div style={{ flex: 1, maxWidth: 1100, margin: '0 auto', width: '100%', padding: '48px 32px' }}>

        {/* Title */}
        <div style={{ marginBottom: 48, textAlign: 'center' }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 12 }}>
            Tarifs
          </div>
          <h1 style={{ fontSize: 64, margin: '0 0 16px', lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
            Choisissez votre{' '}
            <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              plan
            </em>
            .
          </h1>
          <p style={{ fontSize: 16, color: 'var(--muted-foreground)', maxWidth: 480, margin: '0 auto 28px' }}>
            Commencez gratuitement, passez au Pro quand vous en avez besoin. Annulez à tout moment.
          </p>

          {/* Billing toggle */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            background: 'var(--muted)', borderRadius: 999, padding: 4,
            border: '1px solid var(--border)',
          }}>
            {(['monthly', 'yearly'] as BillingPeriod[]).map(period => (
              <button
                key={period}
                onClick={() => setBillingPeriod(period)}
                style={{
                  padding: '7px 18px', fontSize: 13, fontWeight: 600,
                  background: billingPeriod === period ? 'var(--foreground)' : 'transparent',
                  color: billingPeriod === period ? 'var(--background)' : 'var(--muted-foreground)',
                  border: 'none', borderRadius: 999, cursor: 'pointer',
                  boxShadow: billingPeriod === period ? '0 1px 4px rgba(0,0,0,.15)' : 'none',
                  transition: 'all .15s',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                {period === 'monthly' ? 'Mensuel' : 'Annuel'}
                {period === 'yearly' && (
                  <span style={{
                    background: 'var(--c3)', color: '#0a0a0a',
                    fontSize: 10, fontWeight: 800, padding: '2px 7px', borderRadius: 999,
                  }}>
                    −20%
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Canceled banner */}
        {canceled && (
          <div style={{
            maxWidth: 480, margin: '0 auto 32px',
            background: 'color-mix(in oklab, var(--c2) 15%, var(--background))',
            border: '1px solid color-mix(in oklab, var(--c2) 40%, transparent)',
            borderRadius: 14, padding: '14px 20px', textAlign: 'center', fontSize: 14,
          }}>
            Paiement annulé. Vous pouvez réessayer quand vous le souhaitez.
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div style={{
            maxWidth: 480, margin: '0 auto 32px',
            background: 'color-mix(in oklab, var(--destructive) 10%, var(--background))',
            border: '1px solid color-mix(in oklab, var(--destructive) 25%, transparent)',
            borderRadius: 14, padding: '14px 20px', textAlign: 'center', fontSize: 14, color: 'var(--destructive)',
          }}>
            {error}
          </div>
        )}

        {/* Plans grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, marginBottom: 80 }}>
          {plans.map(plan => (
            <div
              key={plan.name}
              style={{
                background: plan.highlighted ? 'var(--c4)' : 'var(--card)',
                color: plan.highlighted ? '#fff' : 'var(--foreground)',
                border: plan.highlighted ? 'none' : '1px solid var(--border)',
                borderRadius: 24, padding: 28,
                display: 'flex', flexDirection: 'column',
                position: 'relative',
                transform: plan.highlighted ? 'translateY(-8px)' : 'none',
                boxShadow: plan.highlighted ? '0 24px 48px rgba(91,77,255,.25)' : 'none',
              }}
            >
              {plan.highlighted && (
                <div style={{
                  position: 'absolute', top: -12, left: 28,
                  background: 'var(--c2)', color: '#0a0a0a',
                  fontSize: 10, fontWeight: 800, letterSpacing: '0.08em', padding: '4px 14px', borderRadius: 999,
                }}>
                  ✦ Populaire
                </div>
              )}

              {/* Plan name + tagline */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, opacity: 0.65, marginBottom: 8 }}>{plan.description}</div>
                <h3 style={{ fontSize: 28, fontWeight: 500, margin: 0, letterSpacing: '-0.02em' }}>{plan.name}</h3>
              </div>

              {/* Price */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                  {plan.name !== 'Enterprise' && <span style={{ fontSize: 20, fontWeight: 500, opacity: 0.6 }}>$</span>}
                  <span style={{
                    fontSize: 56, fontWeight: 400, lineHeight: 1, letterSpacing: '-0.04em',
                    fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic',
                  }}>
                    {plan.price}
                  </span>
                  {plan.period && <span style={{ fontSize: 14, opacity: 0.5, marginLeft: 4 }}>{plan.period}</span>}
                </div>
                {plan.yearlyTotal && (
                  <p style={{ fontSize: 12, opacity: 0.55, margin: '6px 0 0' }}>
                    Facturé {plan.yearlyTotal}{' '}
                    <span style={{ color: plan.highlighted ? 'var(--c2)' : 'var(--c3)' }}>
                      (économisez ${YEARLY_SAVINGS})
                    </span>
                  </p>
                )}
              </div>

              {/* Features */}
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
                {plan.features.map(f => (
                  <li key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 14 }}>
                    <span style={{
                      width: 16, height: 16, borderRadius: '50%',
                      background: plan.highlighted ? 'rgba(255,255,255,.2)' : plan.accent + '44',
                      color: plan.highlighted ? '#fff' : plan.accent,
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginTop: 1,
                    }}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 6L9 17l-5-5"/>
                      </svg>
                    </span>
                    {f}
                  </li>
                ))}
                {plan.locked.map(f => (
                  <li key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 14, opacity: 0.35 }}>
                    <span style={{ width: 16, height: 16, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 6L6 18M6 6l12 12"/>
                      </svg>
                    </span>
                    {f}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              {plan.name === 'Gratuit' && (
                <button
                  disabled={currentPlan === 'Gratuit'}
                  onClick={() => (user ? router.push('/') : setShowAuth(true))}
                  style={ctaBtnStyle(false, currentPlan === 'Gratuit')}
                >
                  {currentPlan === 'Gratuit' ? 'Plan actuel' : plan.cta}
                </button>
              )}
              {plan.name === 'Pro' && (
                <button
                  disabled={currentPlan === 'Pro' || checkoutLoading}
                  onClick={handleUpgrade}
                  style={ctaBtnStyle(true, currentPlan === 'Pro' || checkoutLoading)}
                >
                  {checkoutLoading ? 'Redirection…' : currentPlan === 'Pro' ? 'Plan actuel' : plan.cta}
                </button>
              )}
              {plan.name === 'Enterprise' && (
                <button
                  onClick={() => { window.location.href = 'mailto:silliard.thomas@ekenor.com'; }}
                  style={ctaBtnStyle(false, false)}
                >
                  {plan.cta}
                </button>
              )}
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <h2 style={{ fontSize: 36, fontWeight: 500, textAlign: 'center', marginBottom: 40, letterSpacing: '-0.02em' }}>
            Questions{' '}
            <span style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              fréquentes.
            </span>
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {faq.map((item, i) => (
              <div key={item.q} style={{
                padding: '20px 0',
                borderBottom: i < faq.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <h4 style={{ fontWeight: 600, margin: '0 0 8px', fontSize: 15 }}>{item.q}</h4>
                <p style={{ color: 'var(--muted-foreground)', margin: 0, fontSize: 14, lineHeight: 1.6 }}>{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '16px 32px', display: 'flex', justifyContent: 'center' }}>
        <SpectrumLogo size={20} wordmark />
      </footer>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </main>
  );
}

function ctaBtnStyle(highlighted: boolean, disabled: boolean): React.CSSProperties {
  return {
    width: '100%', padding: '13px 20px', fontSize: 14, fontWeight: 600,
    background: disabled ? 'rgba(255,255,255,.1)' : highlighted ? 'var(--c2)' : 'transparent',
    color: disabled ? 'rgba(255,255,255,.4)' : highlighted ? '#0a0a0a' : 'var(--foreground)',
    border: highlighted ? 'none' : '1px solid var(--border)',
    borderRadius: 12, cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'opacity .15s', opacity: disabled ? 0.6 : 1,
  };
}

function PricingLoading() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid var(--c4)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
      </div>
    </main>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={<PricingLoading />}>
      <PricingContent />
    </Suspense>
  );
}
