import Image from 'next/image';

interface SpectrumLogoProps {
  size?: number;
  wordmark?: boolean;
}

export function SpectrumLogo({ size = 28, wordmark = true }: SpectrumLogoProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size * 0.35 }}>
      <Image
        src="/logo.svg"
        alt="Proofslab"
        width={size}
        height={size}
        style={{ display: 'block', flexShrink: 0 }}
      />
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
