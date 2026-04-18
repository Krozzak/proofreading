'use client';

import { useEffect, useState } from 'react';

interface SpectrumLogoProps {
  size?: number;
  wordmark?: boolean;
}

export function SpectrumLogo({ size = 28, wordmark = true }: SpectrumLogoProps) {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const update = () => setIsDark(document.documentElement.classList.contains('dark'));
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  const blendMode = isDark ? 'screen' : 'multiply';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.35 }}>
      {/* Four overlapping color dots — pigment mixing in light, screen in dark */}
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none" style={{ display: 'block', flexShrink: 0 }}>
        <circle cx="14" cy="14" r="9" fill="var(--c1)" style={{ mixBlendMode: blendMode }} />
        <circle cx="26" cy="14" r="9" fill="var(--c2)" style={{ mixBlendMode: blendMode }} />
        <circle cx="14" cy="26" r="9" fill="var(--c3)" style={{ mixBlendMode: blendMode }} />
        <circle cx="26" cy="26" r="9" fill="var(--c4)" style={{ mixBlendMode: blendMode }} />
      </svg>
      {wordmark && (
        <span style={{
          fontFamily: 'var(--font-geist-sans)',
          fontWeight: 700,
          fontSize: size * 0.7,
          letterSpacing: '-0.04em',
          color: 'var(--foreground)',
          lineHeight: 1,
        }}>
          Proofslab
        </span>
      )}
    </div>
  );
}
