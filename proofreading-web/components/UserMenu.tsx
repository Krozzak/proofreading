'use client';

/**
 * User menu component for the header.
 * Shows login button when not authenticated, user info + quota when authenticated.
 */

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { AuthModal } from './AuthModal';
import { QuotaDisplay } from './QuotaDisplay';

export function UserMenu() {
  const { user, loading, signOut } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

  // Loading skeleton
  if (loading) {
    return (
      <div className="flex items-center gap-3">
        <div className="w-24 h-8 bg-white/10 animate-pulse rounded" />
      </div>
    );
  }

  // Not logged in
  if (!user) {
    return (
      <div className="flex items-center gap-3">
        <QuotaDisplay />
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowAuth(true)}
        >
          Connexion
        </Button>
        <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      </div>
    );
  }

  // Logged in
  return (
    <div className="flex items-center gap-4">
      <QuotaDisplay />
      <Link
        href="/dashboard"
        className="hidden sm:block text-sm text-white/80 max-w-[150px] truncate hover:text-white transition-colors"
        title="Mon compte"
      >
        {user.email}
      </Link>
      <Button
        variant="secondary"
        size="sm"
        onClick={signOut}
      >
        Déconnexion
      </Button>
    </div>
  );
}
