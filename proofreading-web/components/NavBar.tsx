'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { SpectrumLogo } from './SpectrumLogo';
import { UserMenu } from './UserMenu';

const NAV_LINKS = [
  { href: '/', label: 'Accueil', match: (p: string) => p === '/' },
  { href: '/workspace', label: 'Workspace', match: (p: string) => p === '/workspace' },
  { href: '/compare', label: 'Comparer', match: (p: string) => p === '/compare' },
  { href: '/pricing', label: 'Tarifs', match: (p: string) => p === '/pricing' },
];

export function NavBar({ children }: { children?: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        backdropFilter: 'blur(12px)',
        background: 'color-mix(in oklab, var(--background) 90%, transparent)',
        borderBottom: '1px solid var(--border)',
        padding: '0 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
        height: 56,
      }}>
        {/* Left: logo + nav (desktop) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 2, minWidth: 0 }}>
          <Link href="/" style={{ textDecoration: 'none', marginRight: 8, flexShrink: 0 }}>
            <SpectrumLogo size={24} />
          </Link>
          {/* Desktop nav links */}
          <nav className="nav-desktop">
            {NAV_LINKS.map(link => {
              const active = link.match(pathname);
              return (
                <Link key={link.label + link.href} href={link.href} style={{ textDecoration: 'none' }}>
                  <span style={{
                    fontSize: 13, fontWeight: active ? 600 : 400,
                    color: active ? 'var(--foreground)' : 'var(--muted-foreground)',
                    padding: '5px 14px', borderRadius: 999,
                    background: active ? 'var(--muted)' : 'transparent',
                    border: active ? '1px solid var(--border)' : '1px solid transparent',
                    display: 'inline-block', whiteSpace: 'nowrap', transition: 'all .15s',
                  }}>
                    {link.label}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right: page controls + user + hamburger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          {children}
          <UserMenu />
          {/* Hamburger — mobile only */}
          <button
            className="nav-hamburger"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Menu"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: 6, borderRadius: 6, color: 'var(--foreground)',
              display: 'none',
            }}
          >
            {menuOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 12h18M3 6h18M3 18h18"/>
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* Mobile dropdown menu */}
      {menuOpen && (
        <div className="nav-mobile-menu" style={{
          position: 'sticky', top: 56, zIndex: 49,
          background: 'var(--background)',
          borderBottom: '1px solid var(--border)',
          padding: '8px 16px 12px',
          display: 'none',
          flexDirection: 'column',
          gap: 4,
        }}>
          {NAV_LINKS.map(link => {
            const active = link.match(pathname);
            return (
              <Link
                key={link.label + link.href}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                style={{ textDecoration: 'none' }}
              >
                <span style={{
                  display: 'block',
                  fontSize: 14, fontWeight: active ? 600 : 400,
                  color: active ? 'var(--foreground)' : 'var(--muted-foreground)',
                  padding: '8px 12px', borderRadius: 8,
                  background: active ? 'var(--muted)' : 'transparent',
                }}>
                  {link.label}
                </span>
              </Link>
            );
          })}
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .nav-desktop { display: none !important; }
          .nav-hamburger { display: flex !important; }
          .nav-mobile-menu { display: flex !important; }
        }
      `}</style>
    </>
  );
}
