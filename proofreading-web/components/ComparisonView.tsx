'use client';

import { useState, useRef, useEffect } from 'react';
import type { ComparisonPair } from '@/lib/types';
import type { AIAnalyzeResult } from '@/lib/pdf-utils';

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

// ─── Heatmap v2 ──────────────────────────────────────────────────────────────
// Instead of coloring every different pixel red (which turns the whole image
// red on slight shifts), we cluster diff pixels into bounding boxes and draw
// labeled red rectangles. Border pixels (5% margin) are ignored to avoid
// false positives from crop marks / bleeds.
//
// Algorithm:
//  1. Pixel diff → mark cells in a 16×16 grid as "error" if avg diff > 30
//  2. Flood-fill adjacent error cells into clusters
//  3. Compute bounding box per cluster, merge boxes closer than 20px
//  4. Draw printer image + red semi-transparent rects + numbered labels

const CELL_SIZE = 16;
const DIFF_THRESHOLD = 30;   // avg RGB diff to flag a pixel
const MERGE_GAP = 20;        // px — merge bboxes closer than this
const BORDER_RATIO = 0.05;   // ignore outer 5% as potential crop marks

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

        const W = img2.naturalWidth || img2.width;
        const H = img2.naturalHeight || img2.height;

        const canvas = canvasRef.current;
        canvas.width = W;
        canvas.height = H;
        const ctx = canvas.getContext('2d')!;

        // Get pixel data for both images at printer dimensions
        ctx.drawImage(img2, 0, 0, W, H);
        const d2 = ctx.getImageData(0, 0, W, H).data;

        const off = document.createElement('canvas');
        off.width = W; off.height = H;
        const offCtx = off.getContext('2d')!;
        offCtx.drawImage(img1, 0, 0, W, H);
        const d1 = offCtx.getImageData(0, 0, W, H).data;

        // Border exclusion zone (5% of each edge)
        const bLeft   = Math.round(W * BORDER_RATIO);
        const bRight  = Math.round(W * (1 - BORDER_RATIO));
        const bTop    = Math.round(H * BORDER_RATIO);
        const bBottom = Math.round(H * (1 - BORDER_RATIO));

        // Build grid of error cells
        const cols = Math.ceil(W / CELL_SIZE);
        const rows = Math.ceil(H / CELL_SIZE);
        const grid = new Uint8Array(cols * rows); // 1 = error cell

        for (let y = 0; y < H; y++) {
          for (let x = 0; x < W; x++) {
            if (x < bLeft || x >= bRight || y < bTop || y >= bBottom) continue;
            const i = (y * W + x) * 4;
            const diff = (
              Math.abs(d1[i]   - d2[i])   +
              Math.abs(d1[i+1] - d2[i+1]) +
              Math.abs(d1[i+2] - d2[i+2])
            ) / 3;
            if (diff > DIFF_THRESHOLD) {
              const cx = Math.floor(x / CELL_SIZE);
              const cy = Math.floor(y / CELL_SIZE);
              grid[cy * cols + cx] = 1;
            }
          }
        }

        // Flood-fill to find clusters, compute bounding boxes
        const visited = new Uint8Array(cols * rows);
        type BBox = { x1: number; y1: number; x2: number; y2: number };
        const bboxes: BBox[] = [];

        for (let cy = 0; cy < rows; cy++) {
          for (let cx = 0; cx < cols; cx++) {
            if (!grid[cy * cols + cx] || visited[cy * cols + cx]) continue;
            // BFS flood fill
            const stack = [[cx, cy]];
            let minCx = cx, maxCx = cx, minCy = cy, maxCy = cy;
            while (stack.length) {
              const [x, y] = stack.pop()!;
              if (x < 0 || x >= cols || y < 0 || y >= rows) continue;
              if (visited[y * cols + x] || !grid[y * cols + x]) continue;
              visited[y * cols + x] = 1;
              if (x < minCx) minCx = x;
              if (x > maxCx) maxCx = x;
              if (y < minCy) minCy = y;
              if (y > maxCy) maxCy = y;
              stack.push([x+1,y],[x-1,y],[x,y+1],[x,y-1]);
            }
            bboxes.push({
              x1: minCx * CELL_SIZE,
              y1: minCy * CELL_SIZE,
              x2: (maxCx + 1) * CELL_SIZE,
              y2: (maxCy + 1) * CELL_SIZE,
            });
          }
        }

        // Merge overlapping / nearby bboxes
        const merged: BBox[] = [];
        const used = new Uint8Array(bboxes.length);
        for (let i = 0; i < bboxes.length; i++) {
          if (used[i]) continue;
          let b = { ...bboxes[i] };
          let didMerge = true;
          while (didMerge) {
            didMerge = false;
            for (let j = i + 1; j < bboxes.length; j++) {
              if (used[j]) continue;
              const o = bboxes[j];
              const overlap =
                o.x1 - MERGE_GAP <= b.x2 && o.x2 + MERGE_GAP >= b.x1 &&
                o.y1 - MERGE_GAP <= b.y2 && o.y2 + MERGE_GAP >= b.y1;
              if (overlap) {
                b = {
                  x1: Math.min(b.x1, o.x1), y1: Math.min(b.y1, o.y1),
                  x2: Math.max(b.x2, o.x2), y2: Math.max(b.y2, o.y2),
                };
                used[j] = 1;
                didMerge = true;
              }
            }
          }
          merged.push(b);
        }

        // Draw: printer image base + error rectangles
        ctx.drawImage(img2, 0, 0, W, H);

        merged.forEach((b, idx) => {
          const bw = b.x2 - b.x1;
          const bh = b.y2 - b.y1;

          // Semi-transparent fill
          ctx.globalAlpha = opacity * 0.25;
          ctx.fillStyle = '#ff2020';
          ctx.fillRect(b.x1, b.y1, bw, bh);

          // Solid border
          ctx.globalAlpha = opacity;
          ctx.strokeStyle = '#ff2020';
          ctx.lineWidth = Math.max(2, Math.round(W / 400));
          ctx.strokeRect(b.x1, b.y1, bw, bh);

          // Zone number badge
          const badgeSize = Math.max(18, Math.round(W / 40));
          const fontSize  = Math.max(10, Math.round(badgeSize * 0.55));
          ctx.globalAlpha = opacity;
          ctx.fillStyle = '#ff2020';
          ctx.beginPath();
          ctx.arc(b.x1 + badgeSize / 2, b.y1 + badgeSize / 2, badgeSize / 2, 0, Math.PI * 2);
          ctx.fill();
          ctx.globalAlpha = 1;
          ctx.fillStyle = '#fff';
          ctx.font = `bold ${fontSize}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(String(idx + 1), b.x1 + badgeSize / 2, b.y1 + badgeSize / 2);
        });

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
  // AI Analysis
  onAnalyzeWithAI?: () => void;
  isAnalyzing?: boolean;
  aiResult?: AIAnalyzeResult | null;
  canUseAI?: boolean;  // true if user is logged in (free or pro)
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
  onAnalyzeWithAI, isAnalyzing, aiResult, canUseAI,
}: ComparisonViewProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapOpacity, setHeatmapOpacity] = useState(0.65);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectComment, setRejectComment] = useState('');
  const [showAIPanel, setShowAIPanel] = useState(false);

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
      <div className="comparison-panels" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
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

      {/* ── AI Results panel ── */}
      {showAIPanel && aiResult && (
        <div style={{
          background: 'var(--card)', border: '1px solid var(--border)',
          borderRadius: 16, padding: 20, display: 'flex', flexDirection: 'column', gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Icon name="bolt" size={16} color="var(--c4)" />
              <span style={{ fontWeight: 600, fontSize: 14 }}>Analyse IA</span>
              <span style={{
                fontSize: 11, padding: '2px 8px', borderRadius: 999,
                background: 'var(--muted)', color: 'var(--muted-foreground)',
              }}>
                {aiResult.model_used.includes('haiku') ? 'Haiku' : aiResult.model_used}
              </span>
            </div>
            <button onClick={() => setShowAIPanel(false)} style={ghostBtn(false)}>
              <Icon name="x" size={12} /> Fermer
            </button>
          </div>

          {/* Summary */}
          <p style={{
            margin: 0, fontSize: 13, color: 'var(--foreground)',
            padding: '10px 14px', background: 'var(--muted)', borderRadius: 10,
          }}>
            {aiResult.summary}
          </p>

          {/* Issues list */}
          {aiResult.issues.length === 0 ? (
            <p style={{ margin: 0, fontSize: 13, color: 'var(--muted-foreground)' }}>
              Aucune anomalie détectée.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {aiResult.issues.map((issue, i) => {
                const severityColor = issue.severity === 'critical' ? 'var(--c1)'
                  : issue.severity === 'high' ? '#f97316'
                  : issue.severity === 'medium' ? 'var(--c2)'
                  : 'var(--muted-foreground)';
                return (
                  <div key={i} style={{
                    padding: '10px 14px', borderRadius: 10,
                    border: `1px solid ${issue.false_positive ? 'var(--border)' : severityColor}44`,
                    background: issue.false_positive ? 'var(--muted)' : `color-mix(in oklab, ${severityColor} 8%, var(--background))`,
                    opacity: issue.false_positive ? 0.6 : 1,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 999,
                        background: severityColor, color: '#fff',
                        textTransform: 'uppercase', letterSpacing: '0.06em',
                      }}>
                        {issue.severity}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'var(--font-geist-mono)' }}>
                        {issue.type.replace(/_/g, ' ')}
                      </span>
                      {issue.false_positive && (
                        <span style={{ fontSize: 11, color: 'var(--muted-foreground)', marginLeft: 'auto' }}>
                          faux positif
                        </span>
                      )}
                    </div>
                    <p style={{ margin: 0, fontSize: 13 }}>{issue.description}</p>
                  </div>
                );
              })}
            </div>
          )}

          {/* AI quota remaining */}
          {aiResult.ai_quota && (
            <p style={{ margin: 0, fontSize: 11, color: 'var(--muted-foreground)', textAlign: 'right' }}>
              {aiResult.ai_quota.remaining} analyse{aiResult.ai_quota.remaining !== 1 ? 's' : ''} IA restante{aiResult.ai_quota.remaining !== 1 ? 's' : ''}
              {aiResult.ai_quota.resetsAt !== 'never' ? ` · reset ${new Date(aiResult.ai_quota.resetsAt).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}` : ' (à vie)'}
            </p>
          )}
        </div>
      )}

      <style>{`
        @media (max-width: 640px) {
          .comparison-panels { grid-template-columns: 1fr !important; }
        }
      `}</style>

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
        canUseAI={canUseAI}
        canHeatmapForAI={canHeatmap}
        isAnalyzing={isAnalyzing}
        onAnalyzeWithAI={onAnalyzeWithAI ? () => { onAnalyzeWithAI(); setShowAIPanel(true); } : undefined}
        hasAIResult={!!aiResult}
        onShowAIPanel={() => setShowAIPanel(v => !v)}
        showAIPanel={showAIPanel}
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
  canUseAI, canHeatmapForAI, isAnalyzing, onAnalyzeWithAI,
  hasAIResult, onShowAIPanel, showAIPanel,
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
  canUseAI?: boolean;
  canHeatmapForAI?: boolean;
  isAnalyzing?: boolean;
  onAnalyzeWithAI?: () => void;
  hasAIResult?: boolean;
  onShowAIPanel?: () => void;
  showAIPanel?: boolean;
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

      {/* AI Analysis button */}
      {canUseAI !== false && (
        <>
          <button
            onClick={onAnalyzeWithAI ?? onShowAIPanel}
            disabled={!canHeatmapForAI || isAnalyzing}
            title={!canHeatmapForAI ? 'Calculez la similarité d\'abord' : 'Analyser avec l\'IA'}
            style={{
              padding: '9px 14px', fontSize: 13, fontWeight: 600,
              background: hasAIResult && showAIPanel ? 'var(--c4)' : 'var(--muted)',
              color: hasAIResult && showAIPanel ? '#fff' : (!canHeatmapForAI ? 'var(--muted-foreground)' : 'var(--foreground)'),
              border: '1px solid var(--border)', borderRadius: 10,
              cursor: !canHeatmapForAI || isAnalyzing ? 'not-allowed' : 'pointer',
              opacity: !canHeatmapForAI ? 0.4 : 1,
              display: 'flex', alignItems: 'center', gap: 7, transition: 'all .15s',
            }}
          >
            {isAnalyzing ? (
              <>
                <div style={{ width: 12, height: 12, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                Analyse…
              </>
            ) : (
              <>
                <Icon name="bolt" size={13} />
                {hasAIResult ? 'Résultats IA' : 'Analyse IA'}
              </>
            )}
          </button>
          <div style={{ width: 1, height: 28, background: 'var(--border)' }} />
        </>
      )}

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
