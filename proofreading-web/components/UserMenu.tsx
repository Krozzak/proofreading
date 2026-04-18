'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { AuthModal } from './AuthModal';
import { QuotaDisplay } from './QuotaDisplay';
import { ThemeToggle } from './ThemeToggle';

export function UserMenu() {
  const { user, loading, signOut } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <ThemeToggle />
        <div style={{ width: 80, height: 32, background: 'var(--muted)', borderRadius: 8, animation: 'pulse 1.5s ease-in-out infinite' }} />
      </div>
    );
  }

  if (!user) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <ThemeToggle />
        <QuotaDisplay />
        <button
          onClick={() => setShowAuth(true)}
          style={{
            padding: '7px 16px', fontSize: 13, fontWeight: 500,
            background: 'transparent', color: 'var(--muted-foreground)',
            border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer',
            transition: 'all .15s',
          }}
        >
          Se connecter
        </button>
        <button
          onClick={() => setShowAuth(true)}
          style={{
            padding: '7px 16px', fontSize: 13, fontWeight: 600,
            background: 'var(--foreground)', color: 'var(--background)',
            border: 'none', borderRadius: 8, cursor: 'pointer',
            transition: 'all .15s',
          }}
        >
          Essayer
        </button>
        <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <ThemeToggle />
      <QuotaDisplay />

      <div style={{ position: 'relative' }} ref={dropdownRef}>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '7px 14px', fontSize: 13, fontWeight: 500,
            background: showDropdown ? 'var(--muted)' : 'transparent',
            color: 'var(--foreground)',
            border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer',
            transition: 'all .15s',
          }}
        >
          <span style={{
            width: 24, height: 24, borderRadius: '50%',
            background: 'var(--c4)', color: '#fff',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, flexShrink: 0,
          }}>
            {user.email?.[0]?.toUpperCase() ?? '?'}
          </span>
          <span style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user.email?.split('@')[0]}
          </span>
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round"
            style={{ transform: showDropdown ? 'rotate(180deg)' : '', transition: 'transform .15s', flexShrink: 0 }}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>

        {showDropdown && (
          <div style={{
            position: 'absolute', right: 0, top: 'calc(100% + 8px)',
            width: 200, background: 'var(--card)',
            border: '1px solid var(--border)', borderRadius: 14,
            boxShadow: '0 8px 32px rgba(0,0,0,.12)',
            padding: 6, zIndex: 100,
          }}>
            {[
              {
                href: '/dashboard', label: 'Tableau de bord',
                icon: (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                    <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                  </svg>
                ),
              },
              {
                href: '/history', label: 'Historique',
                icon: (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                  </svg>
                ),
              },
            ].map(item => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setShowDropdown(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 12px', fontSize: 14, color: 'var(--foreground)',
                  borderRadius: 8, textDecoration: 'none',
                  transition: 'background .12s',
                }}
                onMouseEnter={e => { (e.target as HTMLElement).closest('a')!.style.background = 'var(--muted)'; }}
                onMouseLeave={e => { (e.target as HTMLElement).closest('a')!.style.background = 'transparent'; }}
              >
                <span style={{ width: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted-foreground)' }}>{item.icon}</span>
                {item.label}
              </Link>
            ))}
            <div style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />
            <button
              onClick={() => { setShowDropdown(false); signOut(); }}
              style={{
                display: 'flex', width: '100%', alignItems: 'center', gap: 10,
                padding: '9px 12px', fontSize: 14, color: 'var(--destructive)',
                background: 'transparent', border: 'none', borderRadius: 8,
                cursor: 'pointer', textAlign: 'left', transition: 'background .12s',
              }}
              onMouseEnter={e => { (e.target as HTMLElement).style.background = 'color-mix(in oklab, var(--destructive) 8%, transparent)'; }}
              onMouseLeave={e => { (e.target as HTMLElement).style.background = 'transparent'; }}
            >
              <span style={{ width: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--destructive)' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
              </span>
              Déconnexion
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
