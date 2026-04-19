'use client';

import { useAuth } from '@/lib/auth-context';

export function QuotaDisplay() {
  const { quota, user } = useAuth();

  if (!user) {
    return (
      <span style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>
        1 comparaison gratuite/jour
      </span>
    );
  }

  if (!quota) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 12px', background: 'var(--muted)', borderRadius: 8,
      }}>
        <div style={{ width: 56, height: 6, background: 'var(--border)', borderRadius: 3, animation: 'pulse 1.5s ease-in-out infinite' }} />
      </div>
    );
  }

  const tier = quota.tier;

  // Enterprise: unlimited AI
  if (tier === 'enterprise') {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 12px', background: 'var(--muted)',
        border: '1px solid var(--border)', borderRadius: 8,
      }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--c4)', fontFamily: 'var(--font-geist-mono)' }}>
          ∞
        </span>
        <span style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>IA</span>
      </div>
    );
  }

  // Pro: show monthly AI quota
  if (tier === 'pro') {
    const isEmpty = quota.aiRemaining === 0;
    const isLow = quota.aiRemaining <= 5;
    const percentage = Math.min(100, (quota.aiUsed / quota.aiLimit) * 100);
    const barColor = isEmpty ? 'var(--destructive)' : isLow ? 'var(--c2)' : 'var(--c4)';
    const textColor = isEmpty ? 'var(--destructive)' : isLow ? 'var(--c2)' : 'var(--foreground)';

    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '6px 12px', background: 'var(--muted)',
        border: '1px solid var(--border)', borderRadius: 8,
      }}>
        <div style={{ fontSize: 13 }}>
          <span style={{ fontWeight: 600, color: textColor, fontFamily: 'var(--font-geist-mono)' }}>
            {quota.aiRemaining}
          </span>
          <span style={{ color: 'var(--muted-foreground)' }}>/{quota.aiLimit} IA</span>
        </div>
        <div style={{ width: 48, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            width: `${percentage}%`, height: '100%',
            background: barColor, borderRadius: 2,
            transition: 'width 300ms ease',
          }} />
        </div>
      </div>
    );
  }

  // Free (connected): show daily SSIM quota
  const isEmpty = quota.remaining === 0;
  const isLow = quota.remaining <= 1;
  const percentage = Math.min(100, (quota.used / quota.limit) * 100);
  const barColor = isEmpty ? 'var(--destructive)' : isLow ? 'var(--c2)' : 'var(--c4)';
  const textColor = isEmpty ? 'var(--destructive)' : isLow ? 'var(--c2)' : 'var(--foreground)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '6px 12px', background: 'var(--muted)',
      border: '1px solid var(--border)', borderRadius: 8,
    }}>
      <div style={{ fontSize: 13 }}>
        <span style={{ fontWeight: 600, color: textColor, fontFamily: 'var(--font-geist-mono)' }}>
          {quota.remaining}
        </span>
        <span style={{ color: 'var(--muted-foreground)' }}>/{quota.limit} SSIM</span>
      </div>
      <div style={{ width: 48, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          width: `${percentage}%`, height: '100%',
          background: barColor, borderRadius: 2,
          transition: 'width 300ms ease',
        }} />
      </div>
    </div>
  );
}
