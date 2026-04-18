'use client';

interface HistoryBannerProps {
  matchedCount: number;
  onRestore: () => void;
  onNewVersion: () => void;
  onDismiss: () => void;
}

export function HistoryBanner({ matchedCount, onRestore, onNewVersion, onDismiss }: HistoryBannerProps) {
  return (
    <div style={{
      background: 'color-mix(in oklab, var(--c4) 8%, var(--background))',
      borderBottom: '1px solid color-mix(in oklab, var(--c4) 25%, transparent)',
      padding: '10px 24px',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        maxWidth: 960, margin: '0 auto', gap: 16, flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'color-mix(in oklab, var(--c4) 15%, transparent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--c4)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/>
            </svg>
          </div>
          <div>
            <p style={{ fontWeight: 600, margin: 0, fontSize: 14, color: 'var(--foreground)' }}>
              {matchedCount} fichier{matchedCount > 1 ? 's' : ''} trouvé{matchedCount > 1 ? 's' : ''} dans l&apos;historique
            </p>
            <p style={{ fontSize: 12, color: 'var(--muted-foreground)', margin: '2px 0 0' }}>
              Ces fichiers ont déjà été comparés. Restaurer les résultats précédents ?
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button onClick={onRestore} style={{
            padding: '7px 16px', fontSize: 13, fontWeight: 600,
            background: 'var(--c4)', color: '#fff',
            border: 'none', borderRadius: 9, cursor: 'pointer',
          }}>
            Restaurer
          </button>
          <button onClick={onNewVersion} style={{
            padding: '7px 14px', fontSize: 13, fontWeight: 500,
            background: 'transparent', color: 'var(--foreground)',
            border: '1px solid var(--border)', borderRadius: 9, cursor: 'pointer',
          }}>
            Nouvelle version
          </button>
          <button onClick={onDismiss} style={{
            width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'transparent', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer',
            color: 'var(--muted-foreground)', fontSize: 16,
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
