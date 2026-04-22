'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const STORAGE_KEY = 'proofslab_cookie_consent';

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setVisible(true);
    }
  }, []);

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, 'accepted');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
      background: 'var(--card)',
      borderTop: '1px solid var(--border)',
      padding: '14px 24px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 16, flexWrap: 'wrap',
    }}>
      <p style={{ fontSize: 13, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5, flex: 1, minWidth: 200 }}>
        Proofslab utilise uniquement des cookies strictement nécessaires à votre session d&apos;authentification.{' '}
        <Link href="/privacy" style={{ color: 'var(--foreground)', textDecoration: 'underline' }}>
          En savoir plus
        </Link>.
      </p>
      <button
        onClick={accept}
        style={{
          padding: '8px 20px', fontSize: 13, fontWeight: 600,
          background: 'var(--foreground)', color: 'var(--background)',
          border: 'none', borderRadius: 8, cursor: 'pointer', flexShrink: 0,
          transition: 'opacity .15s',
        }}
      >
        Compris
      </button>
    </div>
  );
}
