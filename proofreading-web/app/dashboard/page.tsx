'use client';

/**
 * User dashboard page.
 * Shows quota usage, account info, upgrade options, and subscription management.
 */

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import { useAuth } from '@/lib/auth-context';
import {
  redirectToCustomerPortal,
  getSubscription,
  formatPeriodEnd,
  getStatusLabel,
  getStatusColor,
  type SubscriptionInfo,
} from '@/lib/stripe';

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, quota, refreshQuota, signOut, getIdToken } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  // Check for successful upgrade
  const upgraded = searchParams.get('upgraded');

  // Redirect if not logged in
  useEffect(() => {
    if (!loading && !user) {
      router.push('/');
    }
  }, [loading, user, router]);

  // Refresh quota and subscription on mount
  useEffect(() => {
    if (user) {
      refreshQuota();

      // Fetch subscription info
      const fetchSubscription = async () => {
        try {
          const token = await getIdToken();
          if (token) {
            const sub = await getSubscription(token);
            setSubscription(sub);
          }
        } catch (e) {
          // Subscription fetch failed, not critical
          console.error('Failed to fetch subscription:', e);
        }
      };
      fetchSubscription();
    }
  }, [user, refreshQuota, getIdToken]);

  const handleUpgrade = () => {
    router.push('/pricing');
  };

  const handleManageSubscription = async () => {
    setPortalLoading(true);
    try {
      const token = await getIdToken();
      if (token) {
        await redirectToCustomerPortal(token);
      }
    } catch (e) {
      console.error('Portal redirect failed:', e);
    }
    setPortalLoading(false);
  };

  // Loading state
  if (loading || !user) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid var(--accent)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        </div>
      </main>
    );
  }

  // Derive plan from tier field returned by backend
  const planName = quota?.tier === 'enterprise' ? 'Enterprise'
                 : quota?.tier === 'pro' ? 'Pro'
                 : 'Gratuit';
  const isPro = planName === 'Pro' || planName === 'Enterprise';

  const isUnlimited = isPro; // Pro/Enterprise have unlimited SSIM
  const quotaPercentage = quota && !isUnlimited ? (quota.used / quota.limit) * 100 : 0;
  const isQuotaLow = quota && !isUnlimited && quota.remaining <= 1;
  const isQuotaEmpty = quota && !isUnlimited && quota.remaining === 0;

  const quotaColor = isQuotaEmpty ? 'var(--destructive)' : isQuotaLow ? 'var(--c2)' : 'var(--c4)';

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
      {/* ===== HEADER ===== */}
      <NavBar />

      {/* ===== SUCCESS BANNER ===== */}
      {upgraded && (
        <div style={{
          background: 'var(--foreground)',
          borderBottom: '1px solid var(--border)',
          padding: '20px 32px',
        }}>
          <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
            <img src="/logo.svg" alt="" width={28} height={28} style={{ flexShrink: 0 }} />
            <p style={{ margin: 0, fontWeight: 500, fontSize: 17, color: 'var(--background)', fontFamily: 'var(--font-geist-sans)', letterSpacing: '-0.01em' }}>
              Bienvenue dans le plan{' '}
              <span style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, fontSize: 20, color: 'var(--c4)' }}>
                Pro
              </span>
              {' '}— vous avez maintenant{' '}
              <span style={{ fontWeight: 700, color: 'var(--c3)' }}>SSIM illimité + 100 analyses IA/mois</span>.
            </p>
          </div>
        </div>
      )}

      {/* ===== MAIN CONTENT ===== */}
      <div className="dashboard-main" style={{ flex: 1, maxWidth: 1100, margin: '0 auto', width: '100%', padding: '48px 32px' }}>
        {/* Page title */}
        <div style={{ marginBottom: 40 }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 12 }}>
            Compte
          </div>
          <h1 style={{
            fontSize: 64, margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500,
            fontFamily: 'var(--font-geist-sans)',
          }}>
            Votre{' '}
            <span style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              atelier.
            </span>
          </h1>
        </div>

        {/* Quota hero cards — SSIM + IA */}
        <div className="dashboard-hero-cards" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>

          {/* SSIM card */}
          <div style={{
            background: 'var(--c4)', color: '#fff',
            borderRadius: 24, padding: 28,
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div style={{ fontSize: 12, opacity: 0.65, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Comparaisons SSIM
              </div>
              <span style={{
                fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 999,
                background: 'var(--c2)', color: '#0a0a0a',
              }}>
                Plan {planName}
              </span>
            </div>
            <div className="dashboard-hero-number" style={{ fontSize: 72, fontWeight: 600, lineHeight: 1, letterSpacing: '-0.04em', marginBottom: 8 }}>
              {isUnlimited ? '∞' : (
                <>
                  {quota?.remaining ?? '—'}
                  <span style={{ fontSize: 28, opacity: 0.5 }}> / {quota?.limit ?? '—'}</span>
                </>
              )}
            </div>
            <div style={{ fontSize: 12, opacity: 0.65 }}>
              {isUnlimited ? 'Illimitées' : 'restantes · reset à minuit'}
            </div>
            {!isUnlimited && (
              <div style={{ height: 4, background: 'rgba(255,255,255,.15)', borderRadius: 4, overflow: 'hidden', marginTop: 16 }}>
                <div style={{
                  width: `${quotaPercentage}%`, height: '100%',
                  background: '#fff', borderRadius: 4, transition: 'width 500ms ease',
                }} />
              </div>
            )}
          </div>

          {/* IA card */}
          <div style={{
            background: 'var(--foreground)', color: 'var(--background)',
            borderRadius: 24, padding: 28,
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div style={{ fontSize: 12, opacity: 0.5, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Analyses IA
              </div>
              {!isPro && (
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 999,
                  background: 'var(--c2)', color: '#0a0a0a',
                }}>
                  {quota?.aiLimit ?? 10} offertes
                </span>
              )}
            </div>
            {planName === 'Enterprise' ? (
              <div className="dashboard-hero-number" style={{ fontSize: 72, fontWeight: 600, lineHeight: 1, letterSpacing: '-0.04em', marginBottom: 8 }}>
                ∞
              </div>
            ) : (
              <div className="dashboard-hero-number" style={{ fontSize: 72, fontWeight: 600, lineHeight: 1, letterSpacing: '-0.04em', marginBottom: 8 }}>
                {quota?.aiRemaining ?? '—'}
                <span style={{ fontSize: 28, opacity: 0.4, fontWeight: 400 }}>
                  {' '}/ {quota?.aiLimit ?? '—'}{isPro ? ' / mois' : ' à vie'}
                </span>
              </div>
            )}
            <div style={{ fontSize: 12, opacity: 0.5 }}>
              {planName === 'Enterprise' ? 'Illimitées' : isPro ? 'reset le 1er du mois' : 'trial · créez un compte Pro pour plus'}
            </div>
            {planName !== 'Enterprise' && quota && (
              <div style={{ height: 4, background: 'rgba(255,255,255,.15)', borderRadius: 4, overflow: 'hidden', marginTop: 16 }}>
                <div style={{
                  width: `${Math.min(100, (quota.aiUsed / quota.aiLimit) * 100)}%`, height: '100%',
                  background: quota.aiRemaining === 0 ? 'var(--destructive)' : 'var(--c2)', borderRadius: 4,
                  transition: 'width 500ms ease',
                }} />
              </div>
            )}
          </div>

        </div>

        {/* Info cards */}
        <div className="dashboard-info-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 20 }}>
          {[
            {
              label: 'Email', value: user.email ?? '—',
              icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
            },
            {
              label: 'Membre depuis',
              value: user.metadata.creationTime
                ? new Date(user.metadata.creationTime).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
                : '—',
              icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
            },
            {
              label: 'Utilisé aujourd\'hui', value: `${quota?.used ?? 0} comparaisons`,
              icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>,
            },
          ].map(stat => (
            <div key={stat.label} style={{
              background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 20, padding: 24,
            }}>
              <div style={{ color: 'var(--c4)', marginBottom: 14 }}>{stat.icon}</div>
              <div style={{ fontSize: 12, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 8 }}>
                {stat.label}
              </div>
              <div style={{ fontSize: 18, fontWeight: 500, color: 'var(--foreground)', letterSpacing: '-0.01em' }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Quota empty warning */}
        {isQuotaEmpty && (
          <div style={{
            background: 'color-mix(in oklab, var(--destructive) 10%, var(--background))',
            border: '1px solid color-mix(in oklab, var(--destructive) 25%, transparent)',
            borderRadius: 16, padding: '16px 20px', marginBottom: 20,
          }}>
            <p style={{ color: 'var(--destructive)', fontWeight: 500 }}>Quota épuisé pour aujourd&apos;hui</p>
            <p style={{ fontSize: 13, color: 'var(--destructive)', opacity: 0.8, marginTop: 4 }}>
              Passez au plan Pro pour des comparaisons SSIM illimitées et 100 analyses IA/mois.
            </p>
          </div>
        )}

        {/* Upgrade CTA */}
        {!isPro && (
          <div style={{
            background: 'var(--foreground)', color: 'var(--background)',
            borderRadius: 24, padding: 32, marginBottom: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 32, flexWrap: 'wrap',
          }}>
            <div>
              <h3 style={{ fontSize: 28, margin: '0 0 12px', letterSpacing: '-0.02em', fontWeight: 500 }}>Passez au Plan Pro</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['SSIM illimité', '100 analyses IA / mois', 'Rapport IA détaillé par zone', 'Heatmap diff', 'Support prioritaire'].map(f => (
                  <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, opacity: 0.85 }}>
                    <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--c3)', color: '#0a0a0a', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
            <div style={{ textAlign: 'center', flexShrink: 0 }}>
              <div className="dashboard-upgrade-price" style={{ fontSize: 72, fontWeight: 600, letterSpacing: '-0.04em', lineHeight: 1 }}>
                $20<span style={{ fontSize: 16, fontWeight: 400, opacity: 0.6, marginLeft: 6 }}>/ mois</span>
              </div>
              <p style={{ fontSize: 12, opacity: 0.5, marginTop: 6, marginBottom: 20 }}>ou $192/an (-20%)</p>
              <button onClick={handleUpgrade} style={{
                padding: '14px 32px', fontSize: 15, fontWeight: 600,
                background: 'var(--c2)', color: '#0a0a0a',
                border: 'none', borderRadius: 12, cursor: 'pointer',
              }}>
                Voir les plans →
              </button>
            </div>
          </div>
        )}

        {/* Subscription management */}
        {isPro && subscription && subscription.status !== 'none' && (
          <div style={{
            background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 20, padding: 28, marginBottom: 20,
          }}>
            <h3 style={{ fontSize: 20, margin: '0 0 20px', fontWeight: 500 }}>Gestion de l&apos;abonnement</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[
                { label: 'Statut', value: getStatusLabel(subscription.status) },
                subscription.billingPeriod && { label: 'Facturation', value: subscription.billingPeriod === 'yearly' ? 'Annuelle' : 'Mensuelle' },
                subscription.currentPeriodEnd && {
                  label: subscription.cancelAtPeriodEnd ? 'Accès jusqu\'au' : 'Prochain renouvellement',
                  value: formatPeriodEnd(subscription.currentPeriodEnd),
                },
              ].filter(Boolean).map((row: any) => (
                <div key={row.label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 0', borderBottom: '1px solid var(--border)', fontSize: 14,
                }}>
                  <span style={{ color: 'var(--muted-foreground)' }}>{row.label}</span>
                  <span style={{ fontWeight: 500, color: 'var(--foreground)' }}>{row.value}</span>
                </div>
              ))}
            </div>
            {subscription.cancelAtPeriodEnd && (
              <div style={{
                marginTop: 16, padding: '12px 16px',
                background: 'color-mix(in oklab, var(--c2) 15%, var(--background))',
                border: '1px solid color-mix(in oklab, var(--c2) 40%, transparent)',
                borderRadius: 10, fontSize: 13, color: 'var(--foreground)',
              }}>
                Votre abonnement ne sera pas renouvelé. Vous conserverez l&apos;accès Pro jusqu&apos;à la date indiquée.
              </div>
            )}
            <button
              disabled={portalLoading}
              onClick={handleManageSubscription}
              style={{
                marginTop: 20, padding: '10px 20px', fontSize: 14, fontWeight: 500,
                background: 'transparent', color: 'var(--foreground)',
                border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer',
                opacity: portalLoading ? 0.5 : 1,
              }}
            >
              {portalLoading ? 'Redirection...' : 'Gérer mon abonnement →'}
            </button>
          </div>
        )}

        {/* Enterprise CTA — visible uniquement pour les plans Pro */}
        {isPro && planName !== 'Enterprise' && (
          <div style={{
            background: 'var(--muted)', border: '1px solid var(--border)', borderRadius: 20, padding: 28, marginBottom: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24, flexWrap: 'wrap',
          }}>
            <div>
              <h3 style={{ fontSize: 20, margin: '0 0 6px', fontWeight: 500, letterSpacing: '-0.02em' }}>Passez à Enterprise</h3>
              <p style={{ color: 'var(--muted-foreground)', margin: 0, fontSize: 14 }}>
                Comparaisons illimitées, SSO, API dédiée, support 24/7.
              </p>
            </div>
            <button
              onClick={() => { window.location.href = 'mailto:silliard.thomas@ekenor.com'; }}
              style={{
                padding: '10px 22px', fontSize: 14, fontWeight: 600,
                background: 'transparent', color: 'var(--foreground)',
                border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8, transition: 'all .15s', whiteSpace: 'nowrap',
              }}
            >
              Nous contacter
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        )}

        {/* Sign out */}
        <div style={{
          background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 20, padding: 24,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24, flexWrap: 'wrap',
        }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0 }}>Déconnexion</p>
            <p style={{ fontSize: 13, color: 'var(--muted-foreground)', margin: '4px 0 0' }}>
              Vous serez déconnecté de votre compte
            </p>
          </div>
          <button onClick={signOut} style={{
            padding: '10px 20px', fontSize: 14, fontWeight: 500,
            background: 'transparent', color: 'var(--destructive)',
            border: '1px solid var(--destructive)', borderRadius: 10, cursor: 'pointer',
          }}>
            Se déconnecter
          </button>
        </div>
      </div>

      <SiteFooter />

      <style>{`
        @media (max-width: 900px) {
          .dashboard-main { padding: 32px 20px !important; }
          .dashboard-hero-cards { grid-template-columns: 1fr !important; }
          .dashboard-info-cards { grid-template-columns: 1fr !important; }
          .dashboard-hero-number { font-size: 48px !important; }
          .dashboard-upgrade-price { font-size: 48px !important; }
        }
      `}</style>
    </main>
  );
}

function DashboardLoading() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--background)' }}>
      <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid var(--accent)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
    </main>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardLoading />}>
      <DashboardContent />
    </Suspense>
  );
}
