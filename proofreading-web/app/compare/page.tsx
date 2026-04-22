'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ComparisonView } from '@/components/ComparisonView';
import { NavBar } from '@/components/NavBar';
import { PricingModal } from '@/components/PricingModal';
import { HistoryBanner } from '@/components/HistoryBanner';
import { useAppStore } from '@/lib/store';
import { useAuth } from '@/lib/auth-context';
import { useHistorySync } from '@/lib/useHistorySync';
import {
  fileToBase64,
  convertPdfToImage,
  compareImages,
  analyzeWithAI,
  exportToCSV,
  downloadFile,
  copyToClipboard,
} from '@/lib/pdf-utils';
import type { AIAnalyzeResult } from '@/lib/pdf-utils';
import type { ComparisonPair } from '@/lib/types';

// ─── SVG Icons ────────────────────────────────────────────────────────────────
function Icon({ name, size = 16 }: { name: string; size?: number }) {
  const p: React.SVGProps<SVGSVGElement> = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round' } as React.SVGProps<SVGSVGElement>;
  switch (name) {
    case 'check': return <svg {...p}><path d="M20 6L9 17l-5-5"/></svg>;
    case 'x': return <svg {...p}><path d="M18 6L6 18M6 6l12 12"/></svg>;
    case 'download': return <svg {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/></svg>;
    case 'bolt': return <svg {...p}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>;
    case 'search': return <svg {...p}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>;
    default: return null;
  }
}

// ─── Results sidebar ──────────────────────────────────────────────────────────
function ResultsSidebar({
  pairs, currentIndex, onSelectPair, onExportCSV,
  onCalculateAll, isBatchCalculating, batchProgress,
  onAutoApprove, threshold, restoredIndices,
  searchQuery, onSearchChange, showMatchedOnly, onToggleFilter,
}: {
  pairs: ComparisonPair[];
  currentIndex: number;
  onSelectPair: (i: number) => void;
  onExportCSV: () => void;
  onCalculateAll?: () => void;
  isBatchCalculating?: boolean;
  batchProgress?: { current: number; total: number };
  onAutoApprove?: () => void;
  threshold?: number;
  restoredIndices?: Set<number>;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  showMatchedOnly: boolean;
  onToggleFilter: () => void;
}) {
  const filtered = useMemo(() => {
    let r = showMatchedOnly ? pairs.filter(p => p.originalFile && p.printerFile) : pairs;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      r = r.filter(p => p.code.toLowerCase().includes(q) || p.originalFile?.name.toLowerCase().includes(q) || p.printerFile?.name.toLowerCase().includes(q));
    }
    return r;
  }, [pairs, showMatchedOnly, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 18 }}>
      {/* Header */}
      <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexShrink: 0 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted-foreground)' }}>
          RÉSULTATS · {pairs.length}
        </span>
        <div style={{ display: 'flex', gap: 6 }}>
          {onCalculateAll && (
            <button onClick={onCalculateAll} disabled={isBatchCalculating} style={sBtn(false)}
              title="Calculer la similarité pour toutes les paires">
              {isBatchCalculating ? `${batchProgress?.current}/${batchProgress?.total}` : <><Icon name="bolt" size={11} /> Calc.</>}
            </button>
          )}
          {onAutoApprove && (
            <button onClick={onAutoApprove} style={sBtn(false)}
              title="Approuver automatiquement les paires au-dessus du seuil">
              <Icon name="check" size={11} /> Auto
            </button>
          )}
          <button onClick={onExportCSV} style={sBtn(false)}
            title="Exporter les résultats en CSV">
            <Icon name="download" size={11} /> CSV
          </button>
        </div>
      </div>

      {/* Search + filter */}
      <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 6, flexShrink: 0 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted-foreground)', display: 'flex' }}>
            <Icon name="search" size={12} />
          </span>
          <input
            type="text" placeholder="Rechercher…" value={searchQuery}
            onChange={e => onSearchChange(e.target.value)}
            style={{
              width: '100%', paddingLeft: 26, paddingRight: 8, paddingTop: 6, paddingBottom: 6,
              fontSize: 12, border: '1px solid var(--border)', borderRadius: 8,
              background: 'var(--muted)', color: 'var(--foreground)', outline: 'none', boxSizing: 'border-box',
            }}
          />
        </div>
        <button onClick={onToggleFilter} style={sBtn(showMatchedOnly)}
          title="Filtrer pour afficher uniquement les paires matchées (Original + Imprimeur)">
          {showMatchedOnly ? 'Matchés' : 'Tous'}
        </button>
      </div>

      {/* List — scrollable */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filtered.map(pair => {
          const di = pairs.indexOf(pair);
          const active = di === currentIndex;
          const col = pair.validation === 'approved' ? 'var(--c3)'
            : pair.validation === 'rejected' ? 'var(--c1)'
            : pair.similarity !== null && threshold && pair.similarity < threshold ? 'var(--c2)'
            : 'var(--border)';
          return (
            <button
              key={pair.index}
              onClick={() => onSelectPair(di)}
              style={{
                width: '100%', textAlign: 'left',
                padding: '11px 14px',
                background: active ? 'color-mix(in oklab, var(--c4) 8%, transparent)' : 'transparent',
                borderLeft: `3px solid ${active ? 'var(--c4)' : 'transparent'}`,
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                transition: 'all .1s',
              }}
            >
              <div style={{ width: 3, height: 30, background: col, borderRadius: 2, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-geist-mono)', fontSize: 12, fontWeight: 700, color: 'var(--foreground)', display: 'flex', gap: 4, alignItems: 'center' }}>
                  {pair.code}
                  {restoredIndices?.has(di) && <span style={{ fontSize: 9, color: 'var(--c4)', fontWeight: 400 }}>HIST</span>}
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted-foreground)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {pair.originalFile?.name || pair.printerFile?.name || '—'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
                {pair.similarity !== null && (
                  <span style={{ fontFamily: 'var(--font-geist-mono)', fontSize: 12, fontWeight: 700, color: col }}>
                    {pair.similarity.toFixed(1)}%
                  </span>
                )}
                {pair.validation === 'approved' && <Icon name="check" size={13} />}
                {pair.validation === 'rejected' && <Icon name="x" size={13} />}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function sBtn(active: boolean): React.CSSProperties {
  return {
    padding: '5px 9px', fontSize: 11, fontWeight: 600,
    background: active ? 'var(--foreground)' : 'var(--muted)',
    color: active ? 'var(--background)' : 'var(--muted-foreground)',
    border: '1px solid var(--border)', borderRadius: 7, cursor: 'pointer',
    display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
  };
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function ComparePage() {
  const router = useRouter();
  const { getIdToken, refreshQuota, quota, user } = useAuth();
  const {
    pairs, currentIndex, currentPage, threshold,
    showMatchedOnly, searchQuery, autoCalculate, restoredIndices,
    setCurrentIndex, setCurrentPage, setThreshold,
    setShowMatchedOnly, setSearchQuery, setAutoCalculate,
    validateCurrentPage, updatePairSimilarity, autoApprovePair,
    goToNextPair, goToPrevPair, goToNextPage, goToPrevPage,
    reset, setIsAnalyzing,
  } = useAppStore();

  const { matchedCount, showRestorePrompt, restoreFromHistory, dismissRestorePrompt, forceNewVersion } = useHistorySync();

  const [isCalculating, setIsCalculating] = useState(false);
  const [quotaError, setQuotaError] = useState<string | null>(null);
  const [isBatchCalculating, setIsBatchCalculating] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [showPricingModal, setShowPricingModal] = useState(false);
  // Store converted images for heatmap (keyed by pair index + page)
  const [convertedImages, setConvertedImages] = useState<Record<string, { orig: string; print: string }>>({});
  // AI analysis state (keyed by pair index)
  const [aiResults, setAiResults] = useState<Record<number, AIAnalyzeResult>>({});
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false);;

  useEffect(() => {
    if (pairs.length > 0) {
      setIsAnalyzing(false);
      sessionStorage.setItem('prooflab-session-active', 'true');
    }
  }, [pairs, setIsAnalyzing]);

  useEffect(() => {
    if (localStorage.getItem('prooflab-auto-calculate') === 'true') setAutoCalculate(true);
  }, [setAutoCalculate]);

  const currentPair = pairs[currentIndex];
  const imageKey = `${currentIndex}-${currentPage}`;
  const currentImages = convertedImages[imageKey];

  const originalPdfUrl = useMemo(() => {
    const f = currentPair?.originalFile?.file;
    return f ? URL.createObjectURL(f) : null;
  }, [currentPair?.originalFile?.file]);

  const printerPdfUrl = useMemo(() => {
    const f = currentPair?.printerFile?.file;
    return f ? URL.createObjectURL(f) : null;
  }, [currentPair?.printerFile?.file]);

  useEffect(() => {
    return () => {
      if (originalPdfUrl) URL.revokeObjectURL(originalPdfUrl);
      if (printerPdfUrl) URL.revokeObjectURL(printerPdfUrl);
    };
  }, [originalPdfUrl, printerPdfUrl]);

  const handleCalculateSimilarity = useCallback(async () => {
    if (!currentPair?.originalFile?.file || !currentPair?.printerFile?.file) return;
    setIsCalculating(true);
    setQuotaError(null);
    try {
      const token = await getIdToken();
      const [ob, pb] = await Promise.all([
        fileToBase64(currentPair.originalFile.file),
        fileToBase64(currentPair.printerFile.file),
      ]);
      const [or, pr] = await Promise.all([
        convertPdfToImage(ob, currentPage, token),
        convertPdfToImage(pb, currentPage, token),
      ]);
      if (or && pr) {
        // Store image data-URLs for heatmap (or.image already contains the data:... prefix)
        setConvertedImages(prev => ({ ...prev, [imageKey]: { orig: or.image, print: pr.image } }));

        const cmp = await compareImages(or.image, pr.image, true, token);
        if (cmp) {
          updatePairSimilarity(currentIndex, cmp.similarity);
          await refreshQuota();
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : '';
      if (msg.includes('429') || msg.toLowerCase().includes('quota')) setQuotaError(msg);
    } finally {
      setIsCalculating(false);
    }
  }, [currentPair, currentPage, currentIndex, imageKey, getIdToken, updatePairSimilarity, refreshQuota]);

  useEffect(() => {
    if (autoCalculate && currentPair?.originalFile?.file && currentPair?.printerFile?.file &&
      currentPair.similarity === null && !isCalculating && !isBatchCalculating &&
      quota && quota.remaining > 0) {
      handleCalculateSimilarity();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoCalculate, currentIndex, currentPair?.similarity]);

  const handleAnalyzeWithAI = useCallback(async () => {
    if (!currentImages?.orig || !currentImages?.print) return;
    setIsAiAnalyzing(true);
    setQuotaError(null);
    try {
      const token = await getIdToken();
      if (!token) throw new Error('Non authentifié');
      const result = await analyzeWithAI(currentImages.orig, currentImages.print, token);
      if (result) {
        setAiResults(prev => ({ ...prev, [currentIndex]: result }));
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : '';
      if (msg.includes('quota') || msg.includes('Quota') || msg.includes('10 analyses') || msg.includes('100 analyses')) {
        setQuotaError(msg);
      }
    } finally {
      setIsAiAnalyzing(false);
    }
  }, [currentImages, currentIndex, getIdToken]);

  const handleCalculateAll = async () => {
    const toCalc = pairs.map((p, i) => ({ p, i })).filter(({ p }) => p.originalFile?.file && p.printerFile?.file && p.similarity === null);
    if (!toCalc.length) { alert('Tout est déjà calculé !'); return; }
    await refreshQuota();
    if (!quota || quota.remaining < 1) { setQuotaError('Quota insuffisant'); return; }
    setIsBatchCalculating(true);
    setBatchProgress({ current: 0, total: toCalc.length });
    const token = await getIdToken();
    for (let j = 0; j < toCalc.length; j++) {
      const { p, i } = toCalc[j];
      try {
        const [ob, pb] = await Promise.all([fileToBase64(p.originalFile!.file!), fileToBase64(p.printerFile!.file!)]);
        const [or, pr] = await Promise.all([convertPdfToImage(ob, 0, token), convertPdfToImage(pb, 0, token)]);
        if (or && pr) {
          setConvertedImages(prev => ({ ...prev, [`${i}-0`]: { orig: or.image, print: pr.image } }));
          const cmp = await compareImages(or.image, pr.image, true, token);
          if (cmp) updatePairSimilarity(i, cmp.similarity);
        }
        setBatchProgress({ current: j + 1, total: toCalc.length });
      } catch (e) {
        const msg = e instanceof Error ? e.message : '';
        if (msg.includes('429') || msg.toLowerCase().includes('quota')) { setQuotaError(`Quota épuisé après ${j} calcul(s)`); break; }
      }
    }
    setIsBatchCalculating(false);
    await refreshQuota();
  };

  const handleAutoApprove = () => {
    const el = pairs.filter(p => p.similarity !== null && p.similarity >= threshold && p.validation !== 'approved');
    if (!el.length) { alert('Aucun fichier éligible'); return; }
    if (window.confirm(`Approuver ${el.length} fichier(s) >= ${threshold}% ?`))
      el.forEach(p => autoApprovePair(pairs.indexOf(p)));
  };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === 'ArrowLeft') e.shiftKey ? goToPrevPair() : goToPrevPage();
      if (e.key === 'ArrowRight') e.shiftKey ? goToNextPair() : goToNextPage();
      if (e.key === 'a' || e.key === 'A') validateCurrentPage('approved');
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [goToPrevPair, goToNextPair, goToPrevPage, goToNextPage, validateCurrentPage]);

  const handleExportCSV = () => {
    const data = pairs.map(p => ({
      code: p.code,
      filename: p.originalFile?.name || p.printerFile?.name || '',
      matching: p.originalFile && p.printerFile ? 'Les deux' : p.originalFile ? 'Original seul' : 'Imprimeur seul',
      similarity: p.similarity !== null ? `${Math.round(p.similarity)}%` : 'N/A',
      validation: p.validation === 'approved' ? 'Approuvé' : p.validation === 'rejected' ? 'Rejeté' : 'En attente',
      comment: p.comment, date: p.validatedAt || '',
    }));
    downloadFile(exportToCSV(data), `proofreading_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  const approvedCount = pairs.filter(p => p.validation === 'approved').length;
  const rejectedCount = pairs.filter(p => p.validation === 'rejected').length;
  const pendingCount = pairs.length - approvedCount - rejectedCount;

  if (pairs.length === 0) {
    const had = typeof window !== 'undefined' && sessionStorage.getItem('prooflab-session-active');
    return (
      <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
        <NavBar>
          <button onClick={() => { sessionStorage.removeItem('prooflab-session-active'); router.push('/workspace'); }} style={{
            padding: '6px 12px', fontSize: 12, fontWeight: 500,
            background: 'transparent', color: 'var(--muted-foreground)',
            border: '1px solid var(--border)', borderRadius: 999, cursor: 'pointer',
          }}>
            ← Workspace
          </button>
        </NavBar>
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          gap: 24, padding: '48px 32px', textAlign: 'center',
        }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: 'color-mix(in oklab, var(--c4) 12%, transparent)',
            border: '1px solid color-mix(in oklab, var(--c4) 25%, transparent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--c4)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>
            </svg>
          </div>
          <div>
            <h2 style={{ fontSize: 28, fontWeight: 500, letterSpacing: '-0.03em', margin: '0 0 10px' }}>
              {had ? 'Session expirée' : 'Aucune session en cours'}
            </h2>
            <p style={{ fontSize: 15, color: 'var(--muted-foreground)', margin: 0, maxWidth: 380 }}>
              {had
                ? 'Votre session a expiré. Rechargez vos fichiers dans le Workspace pour relancer une comparaison.'
                : 'Déposez vos fichiers dans le Workspace pour lancer une comparaison.'}
            </p>
          </div>
          <button
            onClick={() => { sessionStorage.removeItem('prooflab-session-active'); router.push('/workspace'); }}
            style={{
              padding: '13px 28px', fontSize: 15, fontWeight: 600,
              background: 'var(--foreground)', color: 'var(--background)',
              border: 'none', borderRadius: 14, cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 10,
              transition: 'opacity .15s',
            }}
          >
            Aller au Workspace
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M13 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>

      {/* ── Full navigation bar ── */}
      <NavBar>
        <button onClick={() => { sessionStorage.removeItem('prooflab-session-active'); reset(); router.push('/'); }} style={{
          padding: '6px 12px', fontSize: 12, fontWeight: 500,
          background: 'transparent', color: 'var(--muted-foreground)',
          border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer',
        }}>
          ← Retour
        </button>
      </NavBar>

      {/* ── Banners ── */}
      {quotaError && (
        <div style={{ background: 'color-mix(in oklab, var(--destructive) 10%, var(--background))', borderBottom: '1px solid color-mix(in oklab, var(--destructive) 30%, transparent)', padding: '8px 24px', textAlign: 'center' }}>
          <p style={{ color: 'var(--destructive)', fontWeight: 500, fontSize: 13, margin: 0 }}>
            {quotaError} —{' '}
            <button onClick={() => setShowPricingModal(true)} style={{ background: 'none', border: 'none', color: 'var(--destructive)', fontWeight: 700, textDecoration: 'underline', cursor: 'pointer' }}>
              Passer au Pro
            </button>
          </p>
        </div>
      )}
      {user && showRestorePrompt && (
        <HistoryBanner matchedCount={matchedCount} onRestore={restoreFromHistory} onNewVersion={forceNewVersion} onDismiss={dismissRestorePrompt} />
      )}

      {/* ── Stats strip ── */}
      <div className="compare-stats-strip" style={{ padding: '12px 20px 0', display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 10 }}>
        {/* Batch progress */}
        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '12px 18px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>Batch · {pairs.length} paires</div>
          <div style={{ display: 'flex', gap: 2, height: 8 }}>
            {pairs.map((p, i) => {
              const col = p.validation === 'approved' ? 'var(--c3)' : p.validation === 'rejected' ? 'var(--c1)' : 'var(--border)';
              return (
                <button key={i} onClick={() => setCurrentIndex(i)} title={p.code} style={{
                  flex: 1, height: '100%', background: col, border: 'none', cursor: 'pointer', borderRadius: 2,
                  outline: i === currentIndex ? '2px solid var(--foreground)' : 'none', outlineOffset: 1,
                }} />
              );
            })}
          </div>
          <div style={{ fontSize: 11, fontFamily: 'var(--font-geist-mono)', color: 'var(--muted-foreground)' }}>
            Paire <strong style={{ color: 'var(--foreground)' }}>{currentIndex + 1}</strong> / {pairs.length}
          </div>
        </div>
        {[
          { label: 'Approuvés', value: approvedCount, bg: 'var(--c3)', color: '#0a0a0a' },
          { label: 'Rejetés', value: rejectedCount, bg: 'var(--c1)', color: '#fff' },
          { label: 'En attente', value: pendingCount, bg: 'var(--c2)', color: '#0a0a0a' },
        ].map(s => (
          <div key={s.label} style={{ background: s.bg, color: s.color, borderRadius: 14, padding: '12px 16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, fontWeight: 600, opacity: 0.75 }}>{s.label}</span>
            <span style={{ fontSize: 36, fontWeight: 700, lineHeight: 1, letterSpacing: '-0.03em', fontFamily: 'var(--font-geist-mono)' }}>{s.value}</span>
          </div>
        ))}
      </div>

      {/* ── Main: comparison + sidebar ── */}
      <div style={{ flex: 1, padding: '12px 20px 100px', display: 'flex', gap: 12, minHeight: 0 }}>
        {/* Comparison */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {currentPair && (
            <ComparisonView
              pair={currentPair}
              originalPdfUrl={originalPdfUrl}
              printerPdfUrl={printerPdfUrl}
              origImageUrl={currentImages?.orig ?? null}
              printImageUrl={currentImages?.print ?? null}
              currentPage={currentPage}
              threshold={threshold}
              autoCalculate={autoCalculate}
              onAutoCalculateChange={v => { setAutoCalculate(v); localStorage.setItem('prooflab-auto-calculate', String(v)); }}
              onThresholdChange={setThreshold}
              onApprove={() => validateCurrentPage('approved')}
              onReject={comment => validateCurrentPage('rejected', comment)}
              onPrevPage={goToPrevPage}
              onNextPage={goToNextPage}
              onPrevPair={goToPrevPair}
              onNextPair={goToNextPair}
              hasPrevPair={currentIndex > 0}
              hasNextPair={currentIndex < pairs.length - 1}
              onCalculateSimilarity={handleCalculateSimilarity}
              isCalculating={isCalculating}
              onAnalyzeWithAI={handleAnalyzeWithAI}
              isAnalyzing={isAiAnalyzing}
              aiResult={aiResults[currentIndex] ?? null}
              canUseAI={!!user}
            />
          )}
        </div>

        {/* Sidebar (right, responsive) */}
        <>
          <style>{`
            .results-sidebar { display: flex; width: 300px; flex-shrink: 0; }
            @media (max-width: 1099px) { .results-sidebar { display: none; } }
          `}</style>
          <div className="results-sidebar" style={{ height: 'calc(100vh - 200px)', position: 'sticky', top: 68 }}>
            <ResultsSidebar
              pairs={pairs} currentIndex={currentIndex} onSelectPair={setCurrentIndex}
              onExportCSV={handleExportCSV} onCalculateAll={handleCalculateAll}
              isBatchCalculating={isBatchCalculating} batchProgress={batchProgress}
              onAutoApprove={handleAutoApprove} threshold={threshold}
              restoredIndices={restoredIndices} searchQuery={searchQuery}
              onSearchChange={setSearchQuery} showMatchedOnly={showMatchedOnly}
              onToggleFilter={() => setShowMatchedOnly(!showMatchedOnly)}
            />
          </div>
        </>
      </div>

      {/* Sidebar below on small screens */}
      <>
        <style>{`
          .results-below { display: none; }
          @media (max-width: 1099px) { .results-below { display: block; } }
        `}</style>
        <div className="results-below" style={{ padding: '0 20px 100px', height: 280 }}>
          <ResultsSidebar
            pairs={pairs} currentIndex={currentIndex} onSelectPair={setCurrentIndex}
            onExportCSV={handleExportCSV} onCalculateAll={handleCalculateAll}
            isBatchCalculating={isBatchCalculating} batchProgress={batchProgress}
            onAutoApprove={handleAutoApprove} threshold={threshold}
            restoredIndices={restoredIndices} searchQuery={searchQuery}
            onSearchChange={setSearchQuery} showMatchedOnly={showMatchedOnly}
            onToggleFilter={() => setShowMatchedOnly(!showMatchedOnly)}
          />
        </div>
      </>

      <PricingModal isOpen={showPricingModal} onClose={() => setShowPricingModal(false)} />

      <style>{`
        @media (max-width: 900px) {
          .compare-stats-strip { grid-template-columns: 1fr 1fr !important; padding: 8px 12px 0 !important; }
        }
      `}</style>
    </main>
  );
}
