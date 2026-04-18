'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 50,
      backdropFilter: 'blur(12px)',
      background: 'color-mix(in oklab, var(--background) 90%, transparent)',
      borderBottom: '1px solid var(--border)',
      padding: '0 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      height: 56,
    }}>
      {/* Left: logo + nav */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 2, minWidth: 0 }}>
        <Link href="/" style={{ textDecoration: 'none', marginRight: 8, flexShrink: 0 }}>
          <SpectrumLogo size={24} />
        </Link>
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
      </div>

      {/* Right: slot for page-specific controls + user */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
        {children}
        <UserMenu />
      </div>
    </header>
  );
}
