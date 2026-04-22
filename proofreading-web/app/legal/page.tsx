'use client';

import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import Link from 'next/link';

export default function LegalPage() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)', color: 'var(--foreground)' }}>
      <NavBar />

      <div style={{ flex: 1, maxWidth: 760, margin: '0 auto', width: '100%', padding: '64px 32px', boxSizing: 'border-box' }}>

        {/* Header */}
        <div style={{ marginBottom: 56 }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 16 }}>
            Informations légales
          </div>
          <h1 style={{ fontSize: 'clamp(36px, 5vw, 56px)', margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
            Mentions{' '}
            <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              légales.
            </em>
          </h1>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 48 }}>

          <Section title="Éditeur du site">
            <p>Le site <strong>Proofslab</strong> (accessible à l'adresse <strong>proofslab.com</strong>) est édité par :</p>
            <InfoBlock rows={[
              { label: 'Nom', value: 'Thomas Silliard' },
              { label: 'Statut', value: 'Entrepreneur individuel' },
              { label: 'Pays', value: 'Canada' },
              { label: 'Email', value: 'silliard.thomas@gmail.com' },
            ]} />
          </Section>

          <Section title="Hébergement">
            <InfoBlock rows={[
              { label: 'Frontend', value: 'Vercel Inc. — 340 Pine Street, Suite 701, San Francisco, CA 94104, États-Unis' },
              { label: 'Backend', value: 'Google Cloud Run — Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA 94043, États-Unis' },
              { label: 'Base de données', value: 'Google Firebase Firestore — Google LLC' },
            ]} />
          </Section>

          <Section title="Directeur de la publication">
            <p>Thomas Silliard — <a href="mailto:silliard.thomas@gmail.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@gmail.com</a></p>
          </Section>

          <Section title="Propriété intellectuelle">
            <p>L'ensemble des contenus présents sur Proofslab (textes, graphismes, logos, images, code source) est la propriété exclusive de Thomas Silliard et est protégé par les lois applicables en matière de propriété intellectuelle.</p>
            <p>Toute reproduction, distribution ou utilisation sans autorisation écrite préalable est strictement interdite.</p>
          </Section>

          <Section title="Limitation de responsabilité">
            <p>Proofslab fournit ses services « en l'état » et ne garantit pas l'exactitude absolue des scores de similarité calculés. Les résultats sont fournis à titre indicatif et ne remplacent pas un contrôle qualité humain.</p>
            <p>Proofslab ne saurait être tenu responsable des dommages directs ou indirects résultant de l'utilisation ou de l'impossibilité d'utiliser le service.</p>
          </Section>

          <Section title="Droit applicable">
            <p>Les présentes mentions légales sont soumises au droit canadien (province de Québec). Tout litige sera soumis à la compétence des tribunaux compétents.</p>
          </Section>

          <Section title="Contact">
            <p>Pour toute question relative aux présentes mentions légales : <a href="mailto:silliard.thomas@gmail.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@gmail.com</a></p>
          </Section>

        </div>

        <LegalNav current="/legal" />
      </div>

      <SiteFooter />
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 16px', letterSpacing: '-0.02em', color: 'var(--foreground)' }}>
        {title}
      </h2>
      <div style={{ fontSize: 15, lineHeight: 1.7, color: 'var(--muted-foreground)', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {children}
      </div>
    </section>
  );
}

function InfoBlock({ rows }: { rows: { label: string; value: string }[] }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', marginTop: 8 }}>
      {rows.map((row, i) => (
        <div key={row.label} style={{
          display: 'flex', gap: 16, padding: '12px 20px', fontSize: 14,
          borderBottom: i < rows.length - 1 ? '1px solid var(--border)' : 'none',
        }}>
          <span style={{ minWidth: 120, fontWeight: 500, color: 'var(--foreground)', flexShrink: 0 }}>{row.label}</span>
          <span style={{ color: 'var(--muted-foreground)' }}>{row.value}</span>
        </div>
      ))}
    </div>
  );
}

export function LegalNav({ current }: { current: string }) {
  const links = [
    { href: '/legal', label: 'Mentions légales' },
    { href: '/terms', label: 'CGU' },
    { href: '/privacy', label: 'Confidentialité' },
    { href: '/contact', label: 'Contact' },
  ];
  return (
    <div style={{ marginTop: 64, paddingTop: 32, borderTop: '1px solid var(--border)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {links.map(l => (
        <Link key={l.href} href={l.href} style={{
          padding: '7px 16px', fontSize: 13, borderRadius: 999, textDecoration: 'none',
          background: current === l.href ? 'var(--foreground)' : 'var(--muted)',
          color: current === l.href ? 'var(--background)' : 'var(--muted-foreground)',
          border: '1px solid var(--border)',
          fontWeight: current === l.href ? 600 : 400,
        }}>
          {l.label}
        </Link>
      ))}
    </div>
  );
}

