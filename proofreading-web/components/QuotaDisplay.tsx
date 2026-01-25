'use client';

/**
 * Displays the user's remaining quota.
 */

import { useAuth } from '@/lib/auth-context';
import { Progress } from '@/components/ui/progress';

export function QuotaDisplay() {
  const { quota, user } = useAuth();

  // Show nothing if not logged in
  if (!user) {
    return (
      <div className="text-sm text-white/70">
        1 comparaison gratuite/jour
      </div>
    );
  }

  // Loading state
  if (!quota) {
    return (
      <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
        <div className="w-16 h-2 bg-white/20 animate-pulse rounded" />
      </div>
    );
  }

  const percentage = (quota.used / quota.limit) * 100;
  const isLow = quota.remaining <= 1;
  const isEmpty = quota.remaining === 0;

  return (
    <div className="flex items-center gap-3 bg-white/10 rounded-lg px-3 py-1.5">
      <div className="text-sm">
        <span
          className={
            isEmpty
              ? 'text-red-400 font-bold'
              : isLow
              ? 'text-yellow-400 font-medium'
              : 'text-white'
          }
        >
          {quota.remaining}
        </span>
        <span className="text-white/70">/{quota.limit}</span>
        <span className="text-white/50 ml-1 hidden sm:inline">comparaisons</span>
      </div>
      <Progress
        value={percentage}
        className="w-16 h-2"
      />
    </div>
  );
}
