'use client';

/**
 * User dashboard page.
 * Shows quota usage, account info, upgrade options, and subscription management.
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useAuth } from '@/lib/auth-context';
import {
  redirectToCheckout,
  redirectToCustomerPortal,
  getSubscription,
  formatPeriodEnd,
  getStatusLabel,
  getStatusColor,
  type SubscriptionInfo,
} from '@/lib/stripe';

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading, quota, refreshQuota, signOut, getIdToken } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
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

  const handleUpgrade = async () => {
    setUpgradeLoading(true);
    try {
      const token = await getIdToken();
      if (token) {
        await redirectToCheckout(token, 'yearly');
      }
    } catch (e) {
      console.error('Upgrade failed:', e);
    }
    setUpgradeLoading(false);
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
      <main className="min-h-screen flex flex-col">
        <header className="bg-primary text-white py-6 px-8">
          <div className="max-w-4xl mx-auto">
            <div className="w-48 h-8 bg-white/10 animate-pulse rounded" />
          </div>
        </header>
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </main>
    );
  }

  const quotaPercentage = quota ? (quota.used / quota.limit) * 100 : 0;
  const isQuotaLow = quota && quota.remaining <= 1;
  const isQuotaEmpty = quota && quota.remaining === 0;

  // Determine plan type based on quota limit
  const getPlanName = (limit: number) => {
    if (limit >= 999999) return 'Enterprise';
    if (limit >= 100) return 'Pro';
    if (limit >= 5) return 'Gratuit';
    return 'Anonyme';
  };

  const planName = quota ? getPlanName(quota.limit) : 'Gratuit';
  const isPro = planName === 'Pro' || planName === 'Enterprise';

  return (
    <main className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-primary text-white py-6 px-8">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
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
              <p className="text-primary-foreground/80 text-sm">Mon compte</p>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="secondary" size="sm">
                Retour
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Success message after upgrade */}
      {upgraded && (
        <div className="max-w-4xl mx-auto w-full px-8 pt-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <p className="text-green-800 font-medium">
              Bienvenue dans le plan Pro ! Vous avez maintenant 100 comparaisons/jour.
            </p>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 max-w-4xl mx-auto w-full px-8 py-12">
        <div className="grid gap-8">
          {/* Account Info */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Informations du compte</h2>
            <div className="grid gap-4">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-muted-foreground">Email</span>
                <span className="font-medium">{user.email}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-muted-foreground">Plan actuel</span>
                <span className={`font-medium ${isPro ? 'text-primary' : ''}`}>
                  {planName}
                  {isPro && ' ⭐'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-muted-foreground">Membre depuis</span>
                <span className="font-medium">
                  {user.metadata.creationTime
                    ? new Date(user.metadata.creationTime).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                      })
                    : '-'}
                </span>
              </div>
            </div>
          </Card>

          {/* Quota Usage */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Utilisation quotidienne</h2>
            {quota ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <span
                      className={`text-4xl font-bold ${
                        isQuotaEmpty
                          ? 'text-destructive'
                          : isQuotaLow
                          ? 'text-yellow-500'
                          : 'text-primary'
                      }`}
                    >
                      {quota.remaining}
                    </span>
                    <span className="text-2xl text-muted-foreground">
                      /{quota.limit}
                    </span>
                    <p className="text-sm text-muted-foreground mt-1">
                      comparaisons restantes
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">
                      Réinitialisation à minuit
                    </p>
                    <p className="text-xs text-muted-foreground/70">
                      {quota.resetsAt}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Utilisé aujourd&apos;hui</span>
                    <span>{quota.used} comparaisons</span>
                  </div>
                  <Progress
                    value={quotaPercentage}
                    className={`h-3 ${
                      isQuotaEmpty
                        ? '[&>div]:bg-destructive'
                        : isQuotaLow
                        ? '[&>div]:bg-yellow-500'
                        : ''
                    }`}
                  />
                </div>

                {isQuotaEmpty && (
                  <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                    <p className="text-destructive font-medium">
                      Quota épuisé pour aujourd&apos;hui
                    </p>
                    <p className="text-sm text-destructive/80 mt-1">
                      Passez au plan Pro pour 100 comparaisons/jour ou attendez demain.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </Card>

          {/* Upgrade CTA (if not Pro) */}
          {!isPro && (
            <Card className="p-6 bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Passez au Plan Pro</h2>
                  <p className="text-muted-foreground mt-1">
                    100 comparaisons/jour + fonctionnalités IA avancées
                  </p>
                  <ul className="mt-3 space-y-1 text-sm">
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      100 comparaisons par jour
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      Analyse IA des différences (bientôt)
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      Rapports automatiques (bientôt)
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      Support prioritaire
                    </li>
                  </ul>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">
                    $4.99
                    <span className="text-sm font-normal text-muted-foreground">
                      /mois
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    ou $47.90/an (-20%)
                  </p>
                  <Button
                    className="mt-4"
                    size="lg"
                    disabled={upgradeLoading}
                    onClick={handleUpgrade}
                  >
                    {upgradeLoading ? 'Redirection...' : 'Passer au Pro'}
                  </Button>
                  <Link href="/pricing" className="block mt-2 text-sm text-primary hover:underline">
                    Voir tous les plans
                  </Link>
                </div>
              </div>
            </Card>
          )}

          {/* Subscription Management (if Pro) */}
          {isPro && subscription && subscription.status !== 'none' && (
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Gestion de l&apos;abonnement</h2>
              <div className="grid gap-4">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-muted-foreground">Statut</span>
                  <span className={`font-medium ${getStatusColor(subscription.status)}`}>
                    {getStatusLabel(subscription.status)}
                  </span>
                </div>
                {subscription.billingPeriod && (
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-muted-foreground">Facturation</span>
                    <span className="font-medium">
                      {subscription.billingPeriod === 'yearly' ? 'Annuelle' : 'Mensuelle'}
                    </span>
                  </div>
                )}
                {subscription.currentPeriodEnd && (
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-muted-foreground">
                      {subscription.cancelAtPeriodEnd
                        ? 'Accès jusqu\'au'
                        : 'Prochain renouvellement'}
                    </span>
                    <span className="font-medium">
                      {formatPeriodEnd(subscription.currentPeriodEnd)}
                    </span>
                  </div>
                )}
                {subscription.cancelAtPeriodEnd && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-800">
                      Votre abonnement ne sera pas renouvelé. Vous conserverez l&apos;accès Pro
                      jusqu&apos;à la date indiquée.
                    </p>
                  </div>
                )}
              </div>
              <Button
                variant="outline"
                className="mt-4"
                disabled={portalLoading}
                onClick={handleManageSubscription}
              >
                {portalLoading ? 'Redirection...' : 'Gérer mon abonnement'}
              </Button>
            </Card>
          )}

          {/* Danger zone */}
          <Card className="p-6 border-destructive/20">
            <h2 className="text-xl font-semibold text-destructive mb-4">
              Zone de danger
            </h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Déconnexion</p>
                <p className="text-sm text-muted-foreground">
                  Vous serez déconnecté de votre compte
                </p>
              </div>
              <Button
                variant="outline"
                className="border-destructive text-destructive hover:bg-destructive hover:text-white"
                onClick={signOut}
              >
                Se déconnecter
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-muted-foreground border-t">
        <p>ProofsLab v1.2.0 - PDF Comparison Laboratory</p>
      </footer>
    </main>
  );
}
