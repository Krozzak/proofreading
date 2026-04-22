'use client';

import { SpectrumLogo } from '@/components/SpectrumLogo';
import { NavBar } from '@/components/NavBar';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col" style={{ background: 'var(--background)', color: 'var(--foreground)' }}>
      {/* ============ HEADER ============ */}
      <NavBar />

      {/* ============ HERO ============ */}
      <section className="home-hero" style={{ position: 'relative', padding: '80px 32px 100px', overflow: 'hidden' }}>
        {/* Decorative blobs */}
        <div className="blob-drift" style={{
          position: 'absolute', top: -100, right: -80, width: 380, height: 380,
          background: 'var(--c5)', borderRadius: '50%', filter: 'blur(60px)', opacity: 0.3, zIndex: 0, pointerEvents: 'none',
        }} />
        <div className="blob-drift-slow" style={{
          position: 'absolute', bottom: 40, left: -120, width: 440, height: 440,
          background: 'var(--c3)', borderRadius: '50%', filter: 'blur(80px)', opacity: 0.25, zIndex: 0, pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: '30%', left: '40%', width: 300, height: 300,
          background: 'var(--c4)', borderRadius: '50%', filter: 'blur(90px)', opacity: 0.12, zIndex: 0, pointerEvents: 'none',
        }} />

        <div style={{ maxWidth: 1280, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          {/* Eyebrow badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '6px 14px', background: 'var(--card)',
            border: '1px solid var(--border)', borderRadius: 999,
            fontSize: 13, marginBottom: 40,
          }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--c3)', flexShrink: 0 }} />
            <span style={{ color: 'var(--muted-foreground)' }}>2 studios équipés dans 1 pays</span>
          </div>

          {/* Main headline */}
          <h1 style={{
            fontSize: 'clamp(40px, 9vw, 120px)', lineHeight: 0.92, letterSpacing: '-0.05em',
            margin: '0 0 32px', color: 'var(--foreground)', fontWeight: 500, maxWidth: 1100,
            fontFamily: 'var(--font-geist-sans)',
          }}>
            Approuvez vos{' '}
            <em style={{
              fontStyle: 'italic',
              fontFamily: 'var(--font-instrument-serif)',
              fontWeight: 400,
              color: 'var(--c4)',
            }}>PDF</em>{' '}
            <br />
            à la{' '}
            <span style={{
              display: 'inline-block',
              background: 'linear-gradient(120deg, var(--c1), var(--c2), var(--c3), var(--c4))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>vitesse du pixel.</span>
          </h1>

          {/* Subtitle */}
          <p style={{
            fontSize: 20, lineHeight: 1.5, color: 'var(--muted-foreground)',
            maxWidth: 620, marginBottom: 40,
          }}>
            Comparez vos fichiers design aux épreuves imprimeur pixel par pixel. Score de similarité, heatmap des écarts, approbation en un clic. Créé pour les designers qui en ont marre d&apos;éplucher des PDF à la loupe.
          </p>

          {/* CTAs */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <a href="/workspace" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '14px 28px', fontSize: 15, fontWeight: 600,
              background: 'var(--foreground)', color: 'var(--background)',
              borderRadius: 14, textDecoration: 'none',
              transition: 'transform .15s, box-shadow .15s',
            }}
              onMouseEnter={e => { (e.target as HTMLAnchorElement).style.transform = 'translateY(-2px)'; (e.target as HTMLAnchorElement).style.boxShadow = '0 8px 24px rgba(0,0,0,.15)'; }}
              onMouseLeave={e => { (e.target as HTMLAnchorElement).style.transform = ''; (e.target as HTMLAnchorElement).style.boxShadow = ''; }}
            >
              Lancer une comparaison
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 5l7 7-7 7" />
              </svg>
            </a>
            <a href="#comment" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '14px 28px', fontSize: 15, fontWeight: 500,
              background: 'transparent', color: 'var(--foreground)',
              border: '1px solid var(--border-strong)', borderRadius: 14, textDecoration: 'none',
              transition: 'background .15s',
            }}
              onMouseEnter={e => { (e.target as HTMLElement).style.background = 'var(--muted)'; }}
              onMouseLeave={e => { (e.target as HTMLElement).style.background = 'transparent'; }}
            >
              Voir comment ça marche
            </a>
          </div>

          {/* Metric tiles mosaic */}
          <div className="home-metric-tiles" style={{
            marginTop: 80,
            display: 'grid',
            gridTemplateColumns: 'repeat(12, 1fr)',
            gridAutoRows: '90px',
            gap: 14,
          }}>
            <MetricTile color="var(--c1)" gridArea="1 / 1 / 3 / 4" label="Fichier en cours" value="98.2%" sub="approuvé" />
            <MetricTile color="var(--c2)" gridArea="1 / 4 / 2 / 6" label="En attente" value="76.4%" sub="revue requise" dark />
            <MetricTile color="var(--c4)" gridArea="1 / 6 / 4 / 10" large />
            <MetricTile color="var(--c3)" gridArea="1 / 10 / 2 / 13" label="Lot 3" value="94.7%" sub="approuvé" />
            <MetricTile color="var(--c5)" gridArea="2 / 4 / 4 / 6" label="Batch en cours" value="24/32" sub="fichiers" />
            <MetricTile color="var(--foreground)" gridArea="2 / 10 / 4 / 13" inverted label="Rejetés" value="3" sub="cette session" />
            <MetricTile color="var(--c2)" gridArea="3 / 1 / 4 / 4" label="Temps moyen" value="27s" sub="par paire" />
          </div>
        </div>
      </section>

      {/* ============ FEATURES BENTO ============ */}
      <section id="comment" className="home-features-section" style={{ padding: '80px 32px', maxWidth: 1280, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        <div className="home-features-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16 }}>
          {/* Big feature — SSIM */}
          <div className="home-bento-span4" style={{
            gridColumn: 'span 4',
            background: 'var(--foreground)', color: 'var(--background)',
            borderRadius: 28, padding: 48,
            minHeight: 360,
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ fontSize: 13, fontWeight: 500, opacity: 0.55, marginBottom: 20 }}>01 — Précision SSIM</div>
            <h3 style={{ fontSize: 'clamp(32px, 3.5vw, 48px)', margin: 0, lineHeight: 1.05, letterSpacing: '-0.03em', fontWeight: 500 }}>
              Pixel par pixel. Littéralement.
            </h3>
            <p style={{ fontSize: 16, lineHeight: 1.5, opacity: 0.65, maxWidth: 460, marginTop: 20 }}>
              Score SSIM calibré pour le print. Détecte ce que l&apos;œil manque : teintes décalées de 2%, texte rogné d&apos;1mm, éléments manquants.
            </p>
            {/* Ring score */}
            <div className="home-ring-score" style={{ position: 'absolute', right: 48, bottom: 48, width: 120, height: 120 }}>
              <RingScore score={97.4} color="var(--c3)" size={120} trackColor="rgba(255,255,255,0.1)" textColor="var(--background)" />
            </div>
          </div>

          {/* Gain de temps */}
          <div className="home-bento-span2" style={{
            gridColumn: 'span 2',
            background: 'var(--c2)', color: '#0a0a0a',
            borderRadius: 28, padding: 32, minHeight: 360,
          }}>
            <div style={{ fontSize: 13, fontWeight: 500, opacity: 0.6, marginBottom: 20 }}>02 — Temps</div>
            <h3 style={{ fontSize: 36, margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>3h →</h3>
            <h3 style={{ fontSize: 72, margin: 0, lineHeight: 1, letterSpacing: '-0.04em', fontWeight: 700 }}>8min</h3>
            <p style={{ fontSize: 14, marginTop: 16, opacity: 0.75, lineHeight: 1.5 }}>
              Un batch de 32 PDF, validé en 8 minutes au lieu d&apos;un après-midi entier.
            </p>
          </div>

          {/* Auto-approve */}
          <div className="home-bento-span2" style={{
            gridColumn: 'span 2',
            background: 'var(--card)', border: '1px solid var(--border)',
            borderRadius: 28, padding: 32, minHeight: 280,
          }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--muted-foreground)', marginBottom: 20 }}>03 — Auto-approve</div>
            <h3 style={{ fontSize: 28, margin: 0, lineHeight: 1.15, color: 'var(--foreground)', letterSpacing: '-0.02em', fontWeight: 500 }}>
              Tout ce qui passe le seuil, passe.
            </h3>
            <div style={{ marginTop: 20, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {[92, 98, 76, 94, 99, 88, 96, 81, 95].map((v, i) => (
                <div key={i} style={{
                  padding: '4px 10px', fontSize: 12, fontWeight: 600,
                  background: v >= 85 ? 'var(--c3)' : 'var(--c1)',
                  color: '#0a0a0a', borderRadius: 6,
                  fontFamily: 'var(--font-geist-mono)',
                }}>
                  {v}%
                </div>
              ))}
            </div>
          </div>

          {/* Heatmap */}
          <div className="home-bento-span2" style={{
            gridColumn: 'span 2',
            background: 'var(--c4)', color: '#fff',
            borderRadius: 28, padding: 32, minHeight: 280,
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ fontSize: 13, fontWeight: 500, opacity: 0.6, marginBottom: 20 }}>04 — Heatmap</div>
            <h3 style={{ fontSize: 28, margin: 0, lineHeight: 1.15, letterSpacing: '-0.02em', fontWeight: 500 }}>
              Voyez les écarts comme sur une carte thermique.
            </h3>
            <div style={{ position: 'absolute', bottom: 24, right: 24, width: 120, height: 90 }}>
              <HeatmapGrid />
            </div>
          </div>

          {/* AI coming soon */}
          <div className="home-bento-span2" style={{
            gridColumn: 'span 2',
            background: 'var(--muted)', border: '1px dashed var(--border-strong, var(--border))',
            borderRadius: 28, padding: 32, minHeight: 280,
          }}>
            <span style={{
              display: 'inline-block', padding: '4px 12px', fontSize: 11, fontWeight: 600,
              background: 'var(--accent-soft, #E6E2FF)', color: 'var(--accent)', borderRadius: 999,
              marginBottom: 16,
            }}>
              Bientôt ✦
            </span>
            <h3 style={{ fontSize: 26, margin: 0, lineHeight: 1.15, color: 'var(--foreground)', letterSpacing: '-0.02em', fontWeight: 500 }}>
              Debrief IA des erreurs
            </h3>
            <p style={{ fontSize: 14, marginTop: 12, color: 'var(--muted-foreground)', lineHeight: 1.5 }}>
              Une explication lisible pour chaque écart : &quot;Teinte décalée de 4%, mention légale absente p.2&quot;.
            </p>
          </div>
        </div>
      </section>


      {/* ============ STATS ============ */}
      {/* TODO: remplacer ces valeurs fictives (issues du design) par de vraies données */}
      <section className="home-stats-section" style={{
        padding: '80px 32px', maxWidth: 1280, margin: '0 auto', width: '100%',
        borderTop: '1px solid var(--border)', boxSizing: 'border-box',
      }}>
        <div className="home-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 48 }}>
          {[
            { num: '2', label: 'Studios équipés', sub: 'dans 1 pays' },
            { num: '99.2%', label: 'Précision SSIM', sub: 'calibré pour le print' },
            { num: '< 30s', label: 'Par paire en moyenne', sub: 'sur un batch de 32 PDF' },
          ].map(s => (
            <div key={s.label}>
              <div style={{
                fontFamily: 'var(--font-instrument-serif)', fontSize: 'clamp(48px, 6vw, 72px)',
                letterSpacing: '-0.04em', lineHeight: 1,
                color: 'var(--foreground)', marginBottom: 8, fontWeight: 400,
              }}>
                {s.num}
              </div>
              <div style={{ fontSize: 15, color: 'var(--foreground)', fontWeight: 500 }}>{s.label}</div>
              <div style={{ fontSize: 12, color: 'var(--muted-foreground)', fontFamily: 'var(--font-geist-mono)', marginTop: 4 }}>{s.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="home-footer" style={{
        borderTop: '1px solid var(--border)', padding: '20px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontSize: 13, color: 'var(--muted-foreground)',
      }}>
        <SpectrumLogo size={22} wordmark />
        <span style={{ fontFamily: 'var(--font-geist-mono)', fontSize: 11 }}>v1.3.0 · PDF Comparison Laboratory</span>
      </footer>
      <style>{`
        @media (max-width: 640px) {
          .home-hero { padding: 48px 20px 56px !important; }
          .home-metric-tiles { display: none !important; }
          .home-features-section { padding: 48px 20px !important; }
          .home-features-grid { grid-template-columns: 1fr !important; }
          .home-bento-span4 { grid-column: span 1 !important; min-height: auto !important; padding: 28px !important; }
          .home-bento-span2 { grid-column: span 1 !important; min-height: auto !important; }
          .home-ring-score { display: none !important; }
          .home-stats-section { padding: 48px 20px !important; }
          .home-stats-grid { grid-template-columns: 1fr !important; gap: 32px !important; }
          .home-footer { flex-direction: column !important; gap: 8px !important; text-align: center; padding: 20px !important; }
        }
      `}</style>
    </main>
  );
}

/* ---- Sub-components ---- */

function MetricTile({ color, gridArea, label, value, sub, large, inverted, dark }: {
  color: string; gridArea: string; label?: string; value?: string; sub?: string;
  large?: boolean; inverted?: boolean; dark?: boolean;
}) {
  const textColor = inverted ? 'var(--background)' : '#0a0a0a';
  return (
    <div style={{
      gridArea, background: color, borderRadius: 20, padding: 20,
      color: textColor, display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      minHeight: 90, position: 'relative', overflow: 'hidden',
    }}>
      {large ? (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{
            fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic',
            fontSize: 72, color: '#fff', fontWeight: 400, letterSpacing: '-0.02em',
          }}>
            proofs.
          </span>
        </div>
      ) : (
        <>
          <div style={{ fontSize: 11, fontWeight: 500, opacity: 0.75 }}>{label}</div>
          <div>
            <div style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1 }}>{value}</div>
            <div style={{ fontSize: 11, marginTop: 4, opacity: 0.75 }}>{sub}</div>
          </div>
        </>
      )}
    </div>
  );
}

function RingScore({ score, color, size = 100, trackColor, textColor }: {
  score: number; color: string; size?: number; trackColor?: string; textColor?: string;
}) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={radius} stroke={trackColor || '#e5e5e5'} strokeWidth={6} fill="none" />
      <circle cx={size / 2} cy={size / 2} r={radius} stroke={color} strokeWidth={6} fill="none"
        strokeDasharray={circumference} strokeDashoffset={offset}
        strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }}
      />
      <text x="50%" y="50%" textAnchor="middle" dy="0.35em"
        style={{ transform: 'rotate(90deg)', transformOrigin: 'center', fontFamily: 'var(--font-geist-sans)', fontWeight: 700, fontSize: size * 0.2 }}
        fill={textColor || 'var(--foreground)'}
      >
        {score.toFixed(1)}%
      </text>
    </svg>
  );
}

function HeatmapGrid() {
  const cols = 8, rows = 6;
  const cells = [];
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const v = Math.abs((Math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1);
      const hot = v > 0.82;
      cells.push({ key: `${x}-${y}`, hot, opacity: hot ? v : v * 0.15 });
    }
  }
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`,
      gridTemplateRows: `repeat(${rows}, 1fr)`, width: '100%', height: '100%',
    }}>
      {cells.map(c => (
        <div key={c.key} style={{
          background: c.hot ? `rgba(232, 57, 70, ${c.opacity * 0.9})` : 'transparent',
        }} />
      ))}
    </div>
  );
}
