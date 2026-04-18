'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { NavBar } from '@/components/NavBar';
import { useAppStore, createPairsFromFiles } from '@/lib/store';

// Drop zone tile inline — style Spectrum
function DropTile({
  label, description, color, files, onFilesChange,
}: {
  label: string;
  description: string;
  color: string;
  files: File[];
  onFilesChange: (files: File[]) => void;
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const hasFiles = files.length > 0;

  const processFiles = useCallback(async (items: DataTransferItemList | FileList) => {
    const newFiles: File[] = [];
    if ('length' in items && items[0] && 'webkitGetAsEntry' in items[0]) {
      const readEntry = async (entry: FileSystemEntry): Promise<File[]> => {
        if (entry.isFile) {
          return new Promise(resolve => {
            (entry as FileSystemFileEntry).file(f => {
              resolve(f.name.toLowerCase().endsWith('.pdf') ? [f] : []);
            });
          });
        } else if (entry.isDirectory) {
          const reader = (entry as FileSystemDirectoryEntry).createReader();
          return new Promise(resolve => {
            reader.readEntries(async entries => {
              const all: File[] = [];
              for (const e of entries) all.push(...await readEntry(e));
              resolve(all);
            });
          });
        }
        return [];
      };
      for (let i = 0; i < items.length; i++) {
        const entry = (items[i] as DataTransferItem).webkitGetAsEntry();
        if (entry) newFiles.push(...await readEntry(entry));
      }
    } else {
      for (let i = 0; i < items.length; i++) {
        const f = items[i] as File;
        if (f.name.toLowerCase().endsWith('.pdf')) newFiles.push(f);
      }
    }
    if (newFiles.length > 0) onFilesChange([...files, ...newFiles]);
  }, [files, onFilesChange]);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setIsDragOver(false);
    if (e.dataTransfer.items) await processFiles(e.dataTransfer.items);
  }, [processFiles]);

  const handleClick = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file'; input.multiple = true; input.accept = '.pdf';
    (input as HTMLInputElement & { webkitdirectory: boolean }).webkitdirectory = true;
    input.onchange = (e) => {
      const t = e.target as HTMLInputElement;
      if (t.files) processFiles(t.files);
    };
    input.click();
  }, [processFiles]);

  return (
    <div
      onClick={handleClick}
      onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={e => { e.preventDefault(); setIsDragOver(false); }}
      onDrop={handleDrop}
      style={{
        position: 'relative',
        background: hasFiles
          ? `color-mix(in oklab, ${color} 8%, var(--surface-alt))`
          : isDragOver
          ? `color-mix(in oklab, ${color} 6%, var(--surface-alt))`
          : 'var(--surface-alt)',
        border: `2px ${hasFiles || isDragOver ? 'solid' : 'dashed'} ${hasFiles || isDragOver ? color : 'var(--border-strong)'}`,
        borderRadius: 24,
        padding: '32px',
        cursor: 'pointer',
        minHeight: 260,
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        transition: 'all .2s',
      }}
    >
      {/* Top row: label + check circle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{
            fontSize: 13, fontWeight: 600, color,
            marginBottom: 4, letterSpacing: '-0.01em',
          }}>
            {label}
          </div>
          <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>{description}</div>
        </div>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: hasFiles ? color : `color-mix(in oklab, ${color} 15%, transparent)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, transition: 'all .2s',
        }}>
          {hasFiles ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          )}
        </div>
      </div>

      {/* Bottom: count or empty state */}
      {hasFiles ? (
        <div style={{ marginTop: 20 }}>
          <div style={{
            fontSize: 72, fontWeight: 600, lineHeight: 1,
            letterSpacing: '-0.04em', color: 'var(--foreground)',
          }}>
            {files.length}
          </div>
          <div style={{ fontSize: 14, color: 'var(--muted-foreground)', marginTop: 4 }}>
            fichier{files.length > 1 ? 's' : ''} PDF détecté{files.length > 1 ? 's' : ''}
          </div>
          <button
            onClick={e => { e.stopPropagation(); onFilesChange([]); }}
            style={{
              marginTop: 16, padding: '5px 12px', fontSize: 12,
              background: 'transparent', border: '1px solid var(--border)',
              borderRadius: 8, color: 'var(--muted-foreground)', cursor: 'pointer',
              transition: 'all .15s',
            }}
          >
            Effacer
          </button>
        </div>
      ) : (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', paddingTop: 24,
        }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--muted-foreground)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: 12, opacity: 0.5 }}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <div style={{ fontSize: 14, color: 'var(--muted-foreground)' }}>Glissez un dossier ici</div>
          <div style={{ fontSize: 12, color: 'var(--muted-foreground)', opacity: 0.6, marginTop: 4 }}>ou cliquez pour sélectionner</div>
        </div>
      )}
    </div>
  );
}

export default function WorkspacePage() {
  const router = useRouter();
  const {
    originalFiles,
    printerFiles,
    threshold,
    isAnalyzing,
    setOriginalFiles,
    setPrinterFiles,
    setThreshold,
    setPairs,
    setIsAnalyzing,
  } = useAppStore();

  const canStart = originalFiles.length > 0 || printerFiles.length > 0;
  const pairsCount = Math.min(originalFiles.length, printerFiles.length);

  const handleStart = async () => {
    if (!canStart) return;
    setIsAnalyzing(true);
    const pairs = createPairsFromFiles(originalFiles, printerFiles);
    setPairs(pairs);
    router.push('/compare');
  };

  const thresholdPct = ((threshold - 50) / 50) * 100;

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
      <NavBar />

      <div style={{ flex: 1, maxWidth: 1280, margin: '0 auto', width: '100%', padding: '48px 32px' }}>

        {/* Header */}
        <div style={{ marginBottom: 48 }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center',
            padding: '5px 14px', borderRadius: 999, marginBottom: 20,
            background: 'color-mix(in oklab, var(--c4) 12%, transparent)',
            border: '1px solid color-mix(in oklab, var(--c4) 25%, transparent)',
            fontSize: 12, fontWeight: 600, color: 'var(--c4)',
            letterSpacing: '0.04em',
          }}>
            01 / 03 — Dépôt
          </div>

          {/* H1 avec gradient Spectrum */}
          <h1 style={{
            fontSize: 'clamp(48px, 5.5vw, 72px)', margin: 0,
            lineHeight: 0.95, letterSpacing: '-0.04em', fontWeight: 500,
            fontFamily: 'var(--font-geist-sans)',
          }}>
            Deux dossiers.{' '}
            <span style={{
              background: 'linear-gradient(120deg, var(--c1), var(--c4))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontStyle: 'italic',
              fontFamily: 'var(--font-instrument-serif)',
              fontWeight: 400,
            }}>
              C&apos;est parti.
            </span>
          </h1>
        </div>

        {/* Drop zones */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
          <DropTile
            label="Originaux"
            description="Vos PDF de design"
            color="var(--c4)"
            files={originalFiles}
            onFilesChange={setOriginalFiles}
          />
          <DropTile
            label="Imprimeur"
            description="Épreuves reçues"
            color="var(--c1)"
            files={printerFiles}
            onFilesChange={setPrinterFiles}
          />
        </div>

        {/* Run panel — 2 colonnes Spectrum */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

          {/* Colonne gauche : threshold */}
          <div style={{
            background: 'var(--surface-alt)', border: '1px solid var(--border-strong)',
            borderRadius: 24, padding: 32,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 13, color: 'var(--muted-foreground)', marginBottom: 4 }}>Seuil de conformité</div>
                <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Au-dessus = auto-approuvé</div>
              </div>
              <div style={{
                fontSize: 64, fontWeight: 600, color: 'var(--foreground)',
                letterSpacing: '-0.04em', lineHeight: 1,
              }}>
                {threshold}
                <span style={{ color: 'var(--muted-foreground)', fontSize: 32 }}>%</span>
              </div>
            </div>

            {/* Slider custom Spectrum */}
            <div style={{ position: 'relative', height: 24, display: 'flex', alignItems: 'center' }}>
              <div style={{ position: 'relative', width: '100%', height: 6, borderRadius: 999, background: 'var(--border-strong)' }}>
                <div style={{
                  position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 999,
                  width: `${thresholdPct}%`,
                  background: 'var(--c4)',
                }} />
                <div style={{
                  position: 'absolute', top: '50%',
                  left: `${thresholdPct}%`,
                  transform: 'translate(-50%, -50%)',
                  width: 18, height: 18, borderRadius: '50%',
                  background: 'var(--surface-alt)', border: '2px solid var(--c4)',
                  boxShadow: '0 2px 6px rgba(0,0,0,.18)',
                  pointerEvents: 'none',
                }} />
              </div>
              <input
                type="range" min={50} max={100} step={1}
                value={threshold}
                onChange={e => setThreshold(Number(e.target.value))}
                style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%' }}
              />
            </div>
          </div>

          {/* Colonne droite : launch */}
          <div style={{
            background: 'var(--foreground)', color: 'var(--background)',
            borderRadius: 24, padding: 32,
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          }}>
            <div>
              <div style={{ fontSize: 13, opacity: 0.6, marginBottom: 8 }}>Prêt à lancer</div>
              <div style={{
                fontSize: 56, fontWeight: 600, letterSpacing: '-0.04em', lineHeight: 1,
              }}>
                {pairsCount} <span style={{ opacity: 0.6, fontSize: 28, fontWeight: 400 }}>paires</span>
              </div>
              {pairsCount > 0 && (
                <div style={{ fontSize: 13, opacity: 0.5, marginTop: 8 }}>
                  ~{pairsCount * 27}s estimés
                </div>
              )}
            </div>

            <button
              onClick={handleStart}
              disabled={!canStart || isAnalyzing}
              style={{
                marginTop: 24,
                padding: '16px 24px', fontSize: 15, fontWeight: 600,
                background: canStart ? 'var(--c3)' : 'rgba(255,255,255,.15)',
                color: canStart ? '#0a0a0a' : 'rgba(255,255,255,.4)',
                border: 'none', borderRadius: 14,
                cursor: canStart ? 'pointer' : 'not-allowed',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                width: '100%', transition: 'all .15s',
                opacity: isAnalyzing ? 0.7 : 1,
              }}
            >
              {isAnalyzing ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{
                    width: 16, height: 16, border: '2px solid currentColor',
                    borderTopColor: 'transparent', borderRadius: '50%',
                    display: 'inline-block', animation: 'spin 1s linear infinite',
                  }} />
                  Analyse…
                </span>
              ) : (
                <>
                  Lancer l&apos;analyse
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 5l7 7-7 7"/>
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Matching rule */}
        <div style={{
          marginTop: 16,
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '14px 20px',
          background: 'var(--surface-alt)', border: '1px solid var(--border-strong)', borderRadius: 14,
          fontSize: 13, color: 'var(--muted-foreground)',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, color: 'var(--c4)' }}>
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
          </svg>
          <span>
            Association sur les{' '}
            <strong style={{ color: 'var(--foreground)' }}>8 premiers caractères</strong>{' '}
            du nom de fichier :{' '}
            <code style={{ fontFamily: 'var(--font-geist-mono)', background: 'var(--muted)', padding: '2px 7px', borderRadius: 5, fontSize: 12 }}>
              12345678_design.pdf
            </code>
            {' '}↔{' '}
            <code style={{ fontFamily: 'var(--font-geist-mono)', background: 'var(--muted)', padding: '2px 7px', borderRadius: 5, fontSize: 12 }}>
              12345678_print.pdf
            </code>
          </span>
        </div>

      </div>
    </main>
  );
}
