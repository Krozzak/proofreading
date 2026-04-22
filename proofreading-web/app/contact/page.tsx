'use client';

import { useState } from 'react';
import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import { LegalNav } from '@/app/legal/page';

export default function ContactPage() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText('silliard.thomas@ekenor.com');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)', color: 'var(--foreground)' }}>
      <NavBar />

      <div style={{ flex: 1, maxWidth: 760, margin: '0 auto', width: '100%', padding: '64px 32px', boxSizing: 'border-box' }}>

        <div style={{ marginBottom: 56 }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 16 }}>
            On est là
          </div>
          <h1 style={{ fontSize: 'clamp(36px, 5vw, 56px)', margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
            Nous{' '}
            <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              contacter.
            </em>
          </h1>
          <p style={{ fontSize: 17, color: 'var(--muted-foreground)', marginTop: 20, lineHeight: 1.6, maxWidth: 520 }}>
            Une question, un bug, une idée de feature ou un devis Enterprise ? Écrivez-nous directement.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Email principal */}
          <div style={{
            background: 'var(--foreground)', color: 'var(--background)',
            borderRadius: 20, padding: '28px 32px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ fontSize: 12, opacity: 0.5, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Email</div>
              <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', fontFamily: 'var(--font-geist-mono)' }}>
                silliard.thomas@ekenor.com
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={handleCopy}
                style={{
                  padding: '10px 20px', fontSize: 13, fontWeight: 600,
                  background: copied ? 'var(--c3)' : 'rgba(255,255,255,.15)',
                  color: copied ? '#0a0a0a' : 'var(--background)',
                  border: 'none', borderRadius: 10, cursor: 'pointer', transition: 'all .2s',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                {copied ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                    Copié
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    Copier
                  </>
                )}
              </button>
              <a
                href="mailto:silliard.thomas@ekenor.com"
                style={{
                  padding: '10px 20px', fontSize: 13, fontWeight: 600,
                  background: 'var(--background)', color: 'var(--foreground)',
                  border: 'none', borderRadius: 10, cursor: 'pointer', textDecoration: 'none',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                Écrire
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M13 5l7 7-7 7"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Topics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {[
              { color: 'var(--c3)', icon: '🐛', title: 'Bug ou problème', desc: 'Quelque chose ne fonctionne pas comme prévu ? Décrivez le problème et on répond sous 24h.' },
              { color: 'var(--c4)', icon: '✦', title: 'Enterprise & démo', desc: 'Vous êtes une agence ou une grande équipe ? On peut vous préparer une démo et un devis personnalisé.' },
              { color: 'var(--c2)', icon: '💡', title: 'Idée ou suggestion', desc: 'Proofslab évolue vite. Vos retours terrain sont la meilleure source d\'idées.' },
              { color: 'var(--c1)', icon: '💳', title: 'Facturation', desc: 'Question sur votre abonnement, une facture ou un remboursement ? On gère ça rapidement.' },
            ].map(card => (
              <a
                key={card.title}
                href={`mailto:silliard.thomas@ekenor.com?subject=${encodeURIComponent(card.title)}`}
                style={{ textDecoration: 'none' }}
              >
                <div style={{
                  background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: '20px 22px',
                  height: '100%', cursor: 'pointer', transition: 'border-color .15s',
                }}>
                  <div style={{ fontSize: 22, marginBottom: 10 }}>{card.icon}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>{card.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--muted-foreground)', lineHeight: 1.5 }}>{card.desc}</div>
                </div>
              </a>
            ))}
          </div>

          {/* Response time */}
          <div style={{
            background: 'var(--muted)', border: '1px solid var(--border)', borderRadius: 14, padding: '16px 20px',
            display: 'flex', alignItems: 'center', gap: 12, fontSize: 14, color: 'var(--muted-foreground)',
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--c3)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
            Délai de réponse habituel : <strong style={{ color: 'var(--foreground)' }}>moins de 24h</strong> en jours ouvrés (heure de Montréal, EST).
          </div>

        </div>

        <LegalNav current="/contact" />
      </div>

      <SiteFooter />

      <style>{`
        @media (max-width: 900px) {
          .contact-cards { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </main>
  );
}
