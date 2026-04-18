'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import type { ComparisonPair } from '@/lib/types';

// ─── SVG Icons (no emojis) ───────────────────────────────────────────────────
function Icon({ name, size = 16, color = 'currentColor' }: { name: string; size?: number; color?: string }) {
  const p: React.SVGProps<SVGSVGElement> = {
    width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
    stroke: color, strokeWidth: 1.75, strokeLinecap: 'round', strokeLinejoin: 'round',
  } as React.SVGProps<SVGSVGElement>;
  switch (name) {
    case 'check': return <svg {...p}><path d="M20 6L9 17l-5-5"/></svg>;
    case 'x': return <svg {...p}><path d="M18 6L6 18M6 6l12 12"/></svg>;
    case 'chevL': return <svg {...p}><path d="M15 18l-6-6 6-6"/></svg>;
    case 'chevR': return <svg {...p}><path d="M9 18l6-6-6-6"/></svg>;
    case 'layers': return <svg {...p}><path d="M12 2l10 6-10 6L2 8l10-6z"/><path d="M2 17l10 6 10-6"/><path d="M2 12l10 6 10-6"/></svg>;
    case 'bolt': return <svg {...p}><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>;
    case 'scan': return <svg {...p}><path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2M3 12h18"/></svg>;
    default: return null;
  }
}

// ─── Heatmap ─────────────────────────────────────────────────────────────────
// The heatmap needs actual raster images — we receive base64 image URLs from
// the parent (already converted by convertPdfToImage). PDF blob URLs cannot
// be loaded as <img> elements, so we accept optional image URLs separately.
// HeatmapCanvas — draws base image + diff overlay on a single canvas so
// everything is pixel-perfect aligned. No separate <img> needed.
function HeatmapCanvas({
  image1Url,
  image2Url,
  opacity,
}: {
  image1Url: string;
  image2Url: string;
  opacity: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!image1Url || !image2Url) return;
    let cancelled = false;

    const draw = async () => {
      try {
        const [img1, img2] = await Promise.all([loadImg(image1Url), loadImg(image2Url)]);
        if (cancelled || !canvasRef.current) return;

        // Use the natural dimensions of img2 (printer) as canvas size
        const W = img2.naturalWidth || img2.width;
        const H = img2.naturalHeight || img2.height;

        const canvas = canvasRef.current;
        canvas.width = W;
        canvas.height = H;
        const ctx = canvas.getContext('2d')!;

        // Step 1: draw printer image as base
        ctx.drawImage(img2, 0, 0, W, H);
        const d2 = ctx.getImageData(0, 0, W, H);

        // Step 2: get orig image pixels at same size
        const off = document.createElement('canvas');
        off.width = W; off.height = H;
        const offCtx = off.getContext('2d')!;
        offCtx.drawImage(img1, 0, 0, W, H);
        const d1 = offCtx.getImageData(0, 0, W, H);

        // Step 3: build diff overlay
        const overlay = ctx.createImageData(W, H);
        for (let i = 0; i < d1.data.length; i += 4) {
          const diff = (
            Math.abs(d1.data[i]   - d2.data[i])   +
            Math.abs(d1.data[i+1] - d2.data[i+1]) +
            Math.abs(d1.data[i+2] - d2.data[i+2])
          ) / 3;
          overlay.data[i]   = 255;
          overlay.data[i+1] = Math.max(0, 60 - diff * 1.5);
          overlay.data[i+2] = 0;
          overlay.data[i+3] = Math.min(255, diff * 4);
        }

        // Step 4: composite — printer image first, then diff overlay
        ctx.drawImage(img2, 0, 0, W, H);
        const tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = W; tmpCanvas.height = H;
        tmpCanvas.getContext('2d')!.putImageData(overlay, 0, 0);
        ctx.globalAlpha = opacity;
        ctx.drawImage(tmpCanvas, 0, 0);
        ctx.globalAlpha = 1;

        setReady(true);
      } catch (e) {
        console.error('[Heatmap] failed to draw:', e);
      }
    };

    setReady(false);
    draw();
    return () => { cancelled = true; };
  }, [image1Url, image2Url, opacity]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
        opacity: ready ? 1 : 0, transition: 'opacity .3s',
        pointerEvents: 'none',
        objectFit: 'contain',
      }}
    />
  );
}

function loadImg(src: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => res(img);
    img.onerror = rej;
    img.src = src;
  });
}

// ─── PDF Panel ───────────────────────────────────────────────────────────────
function PDFPanel({
  label, filename, pdfUrl, tone,
  showHeatmap, heatmapOpacity, origImageUrl, printImageUrl,
  page, totalPages,
}: {
  label: string;
  filename: string;
  pdfUrl: string | null;
  tone: 'primary' | 'success' | 'danger';
  showHeatmap?: boolean;
  heatmapOpacity?: number;
  origImageUrl?: string | null;
  printImageUrl?: string | null;
  page: number;
  totalPages: number;
}) {
  const toneColor = tone === 'success' ? 'var(--c3)' : tone === 'danger' ? 'var(--c1)' : 'var(--muted-foreground)';
  const canHeatmap = tone !== 'primary' && showHeatmap && origImageUrl && printImageUrl;

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      borderRadius: 14, background: 'var(--card)',
      border: `1px solid var(--border)`,
      borderTop: `3px solid ${toneColor}`,
    }}>
      {/* Label bar */}
      <div style={{
        padding: '8px 14px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontSize: 11, fontFamily: 'var(--font-geist-mono)', letterSpacing: '0.08em',
        borderBottom: '1px solid var(--border)',
        background: 'var(--muted)',
      }}>
        <span style={{ color: toneColor, fontWeight: 700 }}>{label}</span>
        <span style={{ color: 'var(--muted-foreground)' }}>
          page {page + 1}/{totalPages}
        </span>
      </div>

      {/* PDF content — aspect ratio 1/1.2 like the design */}
      <div style={{ position: 'relative', aspectRatio: '1 / 1.2', overflow: 'hidden', background: 'var(--muted)' }}>
        {/* When heatmap is active, the canvas renders both the base image and the diff overlay */}
        {canHeatmap ? (
          <HeatmapCanvas
            image1Url={origImageUrl!}
            image2Url={printImageUrl!}
            opacity={heatmapOpacity ?? 0.65}
          />
        ) : pdfUrl ? (
          <iframe
            src={pdfUrl}
            title={label}
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0 }}
          />
        ) : (
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            gap: 8, color: 'var(--muted-foreground)',
          }}>
            <Icon name="scan" size={32} color="var(--muted-foreground)" />
            <span style={{ fontSize: 12 }}>Pas de fichier</span>
          </div>
        )}
      </div>

      {/* Filename */}
      <div style={{
        padding: '6px 14px', fontSize: 11,
        color: 'var(--muted-foreground)', borderTop: '1px solid var(--border)',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        background: 'var(--muted)',
      }}>
        {filename || 'Aucun fichier'}
      </div>
    </div>
  );
}

// ─── Props ────────────────────────────────────────────────────────────────────
interface ComparisonViewProps {
  pair: ComparisonPair;
  originalPdfUrl: string | null;
  printerPdfUrl: string | null;
  // Base64 image URLs for heatmap (result of convertPdfToImage)
  origImageUrl?: string | null;
  printImageUrl?: string | null;
  currentPage: number;
  threshold: number;
  autoCalculate: boolean;
  onAutoCalculateChange: (v: boolean) => void;
  onThresholdChange: (v: number) => void;
  onApprove: () => void;
  onReject: (comment: string) => void;
  onPrevPage: () => void;
  onNextPage: () => void;
  onPrevPair: () => void;
  onNextPair: () => void;
  hasPrevPair: boolean;
  hasNextPair: boolean;
  onCalculateSimilarity: () => void;
  isCalculating: boolean;
}

// ─── Main ────────────────────────────────────────────────────────────────────
export function ComparisonView({
  pair, originalPdfUrl, printerPdfUrl,
  origImageUrl, printImageUrl,
  currentPage, threshold, autoCalculate,
  onAutoCalculateChange, onThresholdChange,
  onApprove, onReject,
  onPrevPage, onNextPage, onPrevPair, onNextPair,
  hasPrevPair, hasNextPair,
  onCalculateSimilarity, isCalculating,
}: ComparisonViewProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapOpacity, setHeatmapOpacity] = useState(0.65);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectComment, setRejectComment] = useState('');

  const maxPages = Math.max(pair.totalPagesOriginal, pair.totalPagesPrinter);
  const ok = pair.similarity !== null && pair.similarity >= threshold;
  const hasScore = pair.similarity !== null;
  const heroBg = !hasScore ? 'var(--muted)' : ok ? 'var(--c3)' : 'var(--c1)';
  const heroFg = !hasScore ? 'var(--foreground)' : '#0a0a0a';

  const canHeatmap = !!(origImageUrl && printImageUrl);
  const canCalculate = !!(originalPdfUrl && printerPdfUrl);

  const handleRejectConfirm = () => {
    onReject(rejectComment);
    setRejectComment('');
    setShowRejectDialog(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* ── Pair hero (colored card) ── */}
      <div style={{
        background: heroBg, color: heroFg,
        borderRadius: 18, padding: '20px 28px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20,
        transition: 'background .4s',
      }}>
        <div>
          <div style={{
            fontSize: 11, opacity: 0.65,
            fontFamily: 'var(--font-geist-mono)', letterSpacing: '0.1em', marginBottom: 6,
          }}>
            PAIR {String(currentPage + 1).padStart(2, '0')}
          </div>
          <div style={{
            fontSize: 28, fontWeight: 600, lineHeight: 1, letterSpacing: '-0.03em',
            fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic',
          }}>
            {pair.code}
          </div>
          <div style={{ fontSize: 13, opacity: 0.75, marginTop: 6 }}>
            {pair.originalFile?.name || pair.printerFile?.name || '—'}
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          {isCalculating ? (
            <div style={{
              width: 80, height: 80, border: `4px solid ${heroFg}30`,
              borderTop: `4px solid ${heroFg}`,
              borderRadius: '50%', animation: 'spin 1s linear infinite',
              margin: '0 auto 4px',
            }} />
          ) : hasScore ? (
            <>
              <div style={{
                fontSize: 80, fontWeight: 700, lineHeight: 1,
                letterSpacing: '-0.05em', fontFamily: 'var(--font-geist-mono)',
              }}>
                {Math.round(pair.similarity!)}
              </div>
              <div style={{ fontSize: 12, opacity: 0.65, marginTop: 4 }}>
                SSIM · seuil {threshold}%
              </div>
            </>
          ) : canCalculate ? (
            <button
              onClick={onCalculateSimilarity}
              style={{
                padding: '10px 20px', fontSize: 13, fontWeight: 600,
                background: 'rgba(0,0,0,.12)', color: heroFg,
                border: '1px solid rgba(0,0,0,.18)', borderRadius: 10, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              <Icon name="scan" size={14} />
              Calculer
            </button>
          ) : (
            <span style={{ fontSize: 12, opacity: 0.5 }}>Fichier manquant</span>
          )}
        </div>
      </div>

      {/* ── PDFs side by side ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <PDFPanel
          label="ORIGINAL"
          filename={pair.originalFile?.name || ''}
          pdfUrl={originalPdfUrl}
          tone="primary"
          page={currentPage}
          totalPages={Math.max(pair.totalPagesOriginal, 1)}
        />
        <PDFPanel
          label="IMPRIMEUR"
          filename={pair.printerFile?.name || ''}
          pdfUrl={printerPdfUrl}
          tone={!hasScore ? 'primary' : ok ? 'success' : 'danger'}
          showHeatmap={showHeatmap}
          heatmapOpacity={heatmapOpacity}
          origImageUrl={origImageUrl}
          printImageUrl={printImageUrl}
          page={currentPage}
          totalPages={Math.max(pair.totalPagesPrinter, 1)}
        />
      </div>

      {/* ── Page navigation (if multi-page) ── */}
      {maxPages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <button
            onClick={onPrevPage}
            disabled={currentPage === 0}
            style={ghostBtn(currentPage === 0)}
          >
            <Icon name="chevL" size={14} /> Préc.
          </button>
          <span style={{ fontSize: 13, fontWeight: 600 }}>
            Page {currentPage + 1} / {maxPages}
          </span>
          <button
            onClick={onNextPage}
            disabled={currentPage >= maxPages - 1}
            style={ghostBtn(currentPage >= maxPages - 1)}
          >
            Suiv. <Icon name="chevR" size={14} />
          </button>
        </div>
      )}

      {/* ── Reject dialog ── */}
      {showRejectDialog && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 300,
        }}>
          <div style={{
            width: '100%', maxWidth: 440,
            background: 'var(--card)', border: '1px solid var(--border)',
            borderRadius: 20, padding: 28,
            display: 'flex', flexDirection: 'column', gap: 16,
          }}>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Commentaire de rejet</h3>
            <textarea
              style={{
                width: '100%', height: 96, padding: '10px 12px',
                border: '1px solid var(--border)', borderRadius: 10,
                fontSize: 14, resize: 'none',
                background: 'var(--muted)', color: 'var(--foreground)',
                boxSizing: 'border-box',
              }}
              placeholder="Optionnel…"
              value={rejectComment}
              onChange={e => setRejectComment(e.target.value)}
              autoFocus
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setShowRejectDialog(false)} style={ghostBtn(false)}>Annuler</button>
              <button
                onClick={handleRejectConfirm}
                style={{
                  padding: '9px 20px', fontSize: 14, fontWeight: 600,
                  background: 'var(--c1)', color: '#fff',
                  border: 'none', borderRadius: 10, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                <Icon name="x" size={14} color="#fff" /> Confirmer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Floating action bar (fixed bottom) ── */}
      <FloatingBar
        pair={pair}
        threshold={threshold}
        autoCalculate={autoCalculate}
        showHeatmap={showHeatmap}
        heatmapOpacity={heatmapOpacity}
        canHeatmap={canHeatmap}
        hasScore={hasScore}
        hasPrevPair={hasPrevPair}
        hasNextPair={hasNextPair}
        onThresholdChange={onThresholdChange}
        onAutoCalculateChange={onAutoCalculateChange}
        onShowHeatmapChange={setShowHeatmap}
        onHeatmapOpacityChange={setHeatmapOpacity}
        onPrevPair={onPrevPair}
        onNextPair={onNextPair}
        onReject={() => setShowRejectDialog(true)}
        onApprove={onApprove}
      />
    </div>
  );
}

// ─── Floating bar ─────────────────────────────────────────────────────────────
function FloatingBar({
  pair, threshold, autoCalculate,
  showHeatmap, heatmapOpacity, canHeatmap, hasScore,
  hasPrevPair, hasNextPair,
  onThresholdChange, onAutoCalculateChange,
  onShowHeatmapChange, onHeatmapOpacityChange,
  onPrevPair, onNextPair, onReject, onApprove,
}: {
  pair: ComparisonPair;
  threshold: number;
  autoCalculate: boolean;
  showHeatmap: boolean;
  heatmapOpacity: number;
  canHeatmap: boolean;
  hasScore: boolean;
  hasPrevPair: boolean;
  hasNextPair: boolean;
  onThresholdChange: (v: number) => void;
  onAutoCalculateChange: (v: boolean) => void;
  onShowHeatmapChange: (v: boolean) => void;
  onHeatmapOpacityChange: (v: number) => void;
  onPrevPair: () => void;
  onNextPair: () => void;
  onReject: () => void;
  onApprove: () => void;
}) {
  return (
    <div style={{
      position: 'fixed', bottom: 20, left: '50%', transform: 'translateX(-50%)',
      zIndex: 200,
      background: 'var(--card)',
      border: '1px solid var(--border)',
      borderRadius: 18,
      boxShadow: '0 8px 32px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.08)',
      padding: '12px 16px',
      display: 'flex', alignItems: 'center', gap: 12,
      backdropFilter: 'blur(12px)',
      maxWidth: 'calc(100vw - 40px)',
      flexWrap: 'wrap',
    }}>
      {/* Prev pair */}
      <button onClick={onPrevPair} disabled={!hasPrevPair} style={ghostBtn(!hasPrevPair)}>
        <Icon name="chevL" size={14} />
      </button>

      {/* Separator */}
      <div style={{ width: 1, height: 28, background: 'var(--border)' }} />

      {/* Heatmap controls — toujours visible, désactivé si images non disponibles */}
      <>
        <label
          title={canHeatmap ? 'Afficher/masquer la heatmap des différences' : 'Calculez la similarité d\'abord pour activer la heatmap'}
          style={{
            display: 'flex', alignItems: 'center', gap: 8, cursor: canHeatmap ? 'pointer' : 'not-allowed',
            fontSize: 13, fontWeight: 500, opacity: canHeatmap ? 1 : 0.4,
          }}
        >
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 28, height: 28, borderRadius: 8,
            background: showHeatmap && canHeatmap ? 'var(--c4)' : 'var(--muted)',
            color: showHeatmap && canHeatmap ? '#fff' : 'var(--muted-foreground)',
            cursor: canHeatmap ? 'pointer' : 'not-allowed', transition: 'all .15s', flexShrink: 0,
          }} onClick={() => canHeatmap && onShowHeatmapChange(!showHeatmap)}>
            <Icon name="layers" size={14} color={showHeatmap && canHeatmap ? '#fff' : 'var(--muted-foreground)'} />
          </span>
          Heatmap
        </label>
        {showHeatmap && canHeatmap && (
          <div style={{ position: 'relative', width: 80, height: 20, display: 'flex', alignItems: 'center' }}>
            <div style={{ position: 'relative', width: '100%', height: 4, borderRadius: 999, background: 'var(--muted)' }}>
              <div style={{
                position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 999,
                width: `${((heatmapOpacity - 0.1) / 0.9) * 100}%`,
                background: 'var(--c4)',
              }} />
              <div style={{
                position: 'absolute', top: '50%', borderRadius: '50%',
                left: `${((heatmapOpacity - 0.1) / 0.9) * 100}%`,
                transform: 'translate(-50%, -50%)',
                width: 14, height: 14,
                background: 'var(--card)', border: '2px solid var(--c4)',
                boxShadow: '0 1px 4px rgba(0,0,0,.2)',
                pointerEvents: 'none',
              }} />
            </div>
            <input
              type="range" min={0.1} max={1} step={0.05}
              value={heatmapOpacity}
              onChange={e => onHeatmapOpacityChange(Number(e.target.value))}
              style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%' }}
            />
          </div>
        )}
        <div style={{ width: 1, height: 28, background: 'var(--border)' }} />
      </>

      {/* Threshold */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 12, color: 'var(--muted-foreground)', whiteSpace: 'nowrap' }}>Seuil</span>
        <div style={{ position: 'relative', width: 72, height: 20, display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '100%', height: 4, borderRadius: 999, background: 'var(--muted)' }}>
            <div style={{
              position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 999,
              width: `${((threshold - 50) / 50) * 100}%`,
              background: 'var(--c4)',
            }} />
            <div style={{
              position: 'absolute', top: '50%', borderRadius: '50%',
              left: `${((threshold - 50) / 50) * 100}%`,
              transform: 'translate(-50%, -50%)',
              width: 14, height: 14,
              background: 'var(--card)', border: '2px solid var(--c4)',
              boxShadow: '0 1px 4px rgba(0,0,0,.2)',
              pointerEvents: 'none',
            }} />
          </div>
          <input
            type="range" min={50} max={100} step={1}
            value={threshold}
            onChange={e => onThresholdChange(Number(e.target.value))}
            style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%' }}
          />
        </div>
        <span style={{
          fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-geist-mono)',
          color: 'var(--c4)', minWidth: 32,
        }}>
          {threshold}%
        </span>
      </div>

      {/* Auto-calc */}
      <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 12 }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, borderRadius: 8,
          background: autoCalculate ? 'var(--c2)' : 'var(--muted)',
          color: autoCalculate ? '#0a0a0a' : 'var(--muted-foreground)',
          cursor: 'pointer', transition: 'all .15s', flexShrink: 0,
        }} onClick={() => onAutoCalculateChange(!autoCalculate)}>
          <Icon name="bolt" size={14} color={autoCalculate ? '#0a0a0a' : 'var(--muted-foreground)'} />
        </span>
        Auto
      </label>

      <div style={{ width: 1, height: 28, background: 'var(--border)' }} />

      {/* Approve / Reject */}
      <button
        onClick={onReject}
        style={{
          padding: '9px 18px', fontSize: 13, fontWeight: 700,
          background: 'var(--c1)', color: '#fff',
          border: 'none', borderRadius: 10, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 7,
        }}
      >
        <Icon name="x" size={14} color="#fff" /> Rejeter
      </button>

      <button
        onClick={onApprove}
        style={{
          padding: '9px 18px', fontSize: 13, fontWeight: 700,
          background: 'var(--c3)', color: '#0a0a0a',
          border: 'none', borderRadius: 10, cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 7,
        }}
      >
        <Icon name="check" size={14} color="#0a0a0a" /> Approuver & suivant
      </button>

      <div style={{ width: 1, height: 28, background: 'var(--border)' }} />

      {/* Next pair */}
      <button onClick={onNextPair} disabled={!hasNextPair} style={ghostBtn(!hasNextPair)}>
        <Icon name="chevR" size={14} />
      </button>
    </div>
  );
}

function ghostBtn(disabled: boolean): React.CSSProperties {
  return {
    padding: '7px 12px', fontSize: 12, fontWeight: 500,
    background: 'var(--muted)', color: disabled ? 'var(--muted-foreground)' : 'var(--foreground)',
    border: '1px solid var(--border)', borderRadius: 9, cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.4 : 1, display: 'flex', alignItems: 'center', gap: 6, transition: 'opacity .15s',
  };
}
