'use client';

import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  // Initialize from localStorage or system preference
  useEffect(() => {
    const stored = localStorage.getItem('proofslab-theme');
    if (stored === 'dark') {
      setDark(true);
      document.documentElement.classList.add('dark');
    } else if (stored === 'light') {
      setDark(false);
      document.documentElement.classList.remove('dark');
    } else {
      // Use system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setDark(prefersDark);
      if (prefersDark) document.documentElement.classList.add('dark');
    }
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    if (next) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('proofslab-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('proofslab-theme', 'light');
    }
  };

  return (
    <button
      onClick={toggle}
      aria-label={dark ? 'Passer en mode clair' : 'Passer en mode sombre'}
      style={{
        width: 36, height: 36,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--muted)', color: 'var(--foreground)',
        border: '1px solid var(--border)', borderRadius: 10,
        cursor: 'pointer', fontSize: 16,
        transition: 'all .15s',
        flexShrink: 0,
      }}
    >
      {dark ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      )}
    </button>
  );
}
