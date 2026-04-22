'use client';

import Link from 'next/link';
import { SpectrumLogo } from './SpectrumLogo';

export function SiteFooter() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      padding: '28px 32px',
      background: 'var(--background)',
    }}>
      <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>

        {/* Left: logo + version */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <SpectrumLogo size={20} wordmark />
          <span style={{ fontFamily: 'var(--font-geist-mono)', fontSize: 11, color: 'var(--muted-foreground)', opacity: 0.6 }}>
            v1.3.0
          </span>
        </div>

        {/* Right: legal links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
          {[
            { href: '/legal', label: 'Mentions légales' },
            { href: '/terms', label: 'CGU' },
            { href: '/privacy', label: 'Confidentialité' },
            { href: '/contact', label: 'Contact' },
          ].map((link, i, arr) => (
            <span key={link.href} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Link href={link.href} style={{
                fontSize: 13, color: 'var(--muted-foreground)', textDecoration: 'none',
                padding: '4px 8px', borderRadius: 6, transition: 'color .15s',
              }}
                onMouseEnter={e => { (e.target as HTMLElement).style.color = 'var(--foreground)'; }}
                onMouseLeave={e => { (e.target as HTMLElement).style.color = 'var(--muted-foreground)'; }}
              >
                {link.label}
              </Link>
              {i < arr.length - 1 && (
                <span style={{ color: 'var(--border-strong)', fontSize: 12 }}>·</span>
              )}
            </span>
          ))}
        </nav>

      </div>

      <style>{`
        @media (max-width: 640px) {
          .site-footer-inner { flex-direction: column; align-items: flex-start !important; }
        }
      `}</style>
    </footer>
  );
}
