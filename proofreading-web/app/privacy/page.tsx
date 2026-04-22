'use client';

import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import { LegalNav } from '@/app/legal/page';

export default function PrivacyPage() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)', color: 'var(--foreground)' }}>
      <NavBar />

      <div style={{ flex: 1, maxWidth: 760, margin: '0 auto', width: '100%', padding: '64px 32px', boxSizing: 'border-box' }}>

        <div style={{ marginBottom: 56 }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 16 }}>
            Dernière mise à jour · Avril 2026
          </div>
          <h1 style={{ fontSize: 'clamp(36px, 5vw, 56px)', margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
            Politique de{' '}
            <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              confidentialité.
            </em>
          </h1>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 48 }}>

          <Section title="1. Responsable du traitement">
            <p>Thomas Silliard, entrepreneur individuel basé au Canada, est responsable du traitement des données personnelles collectées via Proofslab (<a href="mailto:silliard.thomas@ekenor.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@ekenor.com</a>).</p>
          </Section>

          <Section title="2. Données collectées">
            <DataTable rows={[
              { category: 'Compte', data: 'Adresse email, date de création', purpose: 'Authentification et gestion du compte', basis: 'Exécution du contrat' },
              { category: 'Utilisation', data: 'Quotas utilisés, historique des comparaisons (noms de fichiers, scores, validations)', purpose: 'Fourniture du service et historique', basis: 'Exécution du contrat' },
              { category: 'Paiement', data: 'Informations de facturation traitées par Stripe (Proofslab ne stocke pas les numéros de carte)', purpose: 'Traitement des abonnements Pro', basis: 'Exécution du contrat' },
              { category: 'Technique', data: "Adresse IP (hachée), logs d'accès anonymisés", purpose: 'Sécurité, prévention des abus et quotas anonymes', basis: 'Intérêt légitime' },
            ]} />
            <p style={{ marginTop: 8 }}>Vos fichiers PDF sont traités en mémoire pour l&apos;analyse et <strong>ne sont pas conservés</strong> sur nos serveurs après traitement.</p>
          </Section>

          <Section title="3. Sous-traitants et transferts">
            <DataTable rows={[
              { category: 'Firebase Auth & Firestore', data: 'Google LLC (USA)', purpose: 'Authentification et stockage des données de compte', basis: 'Clauses contractuelles types UE' },
              { category: 'Google Cloud Run', data: 'Google LLC (Canada — Montréal)', purpose: 'Hébergement du backend', basis: 'Serveur en territoire canadien' },
              { category: 'Vercel', data: 'Vercel Inc. (USA)', purpose: 'Hébergement du frontend', basis: 'Clauses contractuelles types UE' },
              { category: 'Stripe', data: 'Stripe Inc. (USA)', purpose: 'Traitement des paiements', basis: 'Clauses contractuelles types UE' },
              { category: 'Anthropic', data: 'Anthropic PBC (USA)', purpose: 'Analyses IA (plan Pro)', basis: 'Clauses contractuelles types UE' },
            ]} />
          </Section>

          <Section title="4. Durée de conservation">
            <p><strong>Données de compte</strong> — Conservées jusqu'à la suppression du compte, puis 30 jours supplémentaires avant effacement définitif.</p>
            <p><strong>Historique des comparaisons</strong> — Conservé tant que le compte est actif. Supprimable à tout moment depuis la page Historique.</p>
            <p><strong>Données de paiement</strong> — Conservées par Stripe selon leurs propres politiques (généralement 7 ans pour les obligations légales).</p>
            <p><strong>Logs techniques</strong> — 90 jours maximum.</p>
          </Section>

          <Section title="5. Vos droits">
            <p>Vous disposez des droits suivants sur vos données personnelles :</p>
            <ul style={{ paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <li><strong>Accès</strong> — obtenir une copie de vos données</li>
              <li><strong>Rectification</strong> — corriger des données inexactes</li>
              <li><strong>Suppression</strong> — demander l'effacement de votre compte et de vos données</li>
              <li><strong>Portabilité</strong> — recevoir vos données dans un format structuré</li>
              <li><strong>Opposition</strong> — vous opposer à certains traitements</li>
            </ul>
            <p>Pour exercer ces droits : <a href="mailto:silliard.thomas@ekenor.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@ekenor.com</a>. Réponse sous 30 jours.</p>
          </Section>

          <Section title="6. Cookies">
            <p>Proofslab utilise uniquement les cookies strictement nécessaires au fonctionnement du service (session d'authentification Firebase). Aucun cookie publicitaire ou de tracking tiers n'est utilisé.</p>
          </Section>

          <Section title="7. Sécurité">
            <p>Proofslab met en œuvre des mesures techniques et organisationnelles appropriées pour protéger vos données : chiffrement en transit (HTTPS/TLS), accès base de données uniquement via API sécurisée, conteneurs non-root, secrets gérés via GCP Secret Manager.</p>
          </Section>

          <Section title="8. Modifications">
            <p>Toute modification substantielle de cette politique sera notifiée par email aux utilisateurs enregistrés au moins 7 jours avant son entrée en vigueur.</p>
          </Section>

          <Section title="Contact & réclamations">
            <p>Pour toute question relative à vos données : <a href="mailto:silliard.thomas@ekenor.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@ekenor.com</a></p>
            <p>Si vous estimez que vos droits ne sont pas respectés, vous avez le droit de déposer une plainte auprès de l'autorité compétente au Canada (Commissariat à la protection de la vie privée — <a href="https://www.priv.gc.ca" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--c4)', textDecoration: 'none' }}>priv.gc.ca</a>).</p>
          </Section>

        </div>

        <LegalNav current="/privacy" />
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

function DataTable({ rows }: { rows: { category: string; data: string; purpose: string; basis: string }[] }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', marginTop: 8, overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 480 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {['Catégorie', 'Données', 'Finalité', 'Base légale'].map(h => (
              <th key={h} style={{ padding: '10px 16px', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--muted-foreground)', textAlign: 'left', whiteSpace: 'nowrap' }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.category} style={{ borderBottom: i < rows.length - 1 ? '1px solid var(--border)' : 'none' }}>
              <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', whiteSpace: 'nowrap' }}>{row.category}</td>
              <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--muted-foreground)' }}>{row.data}</td>
              <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--muted-foreground)' }}>{row.purpose}</td>
              <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--muted-foreground)', whiteSpace: 'nowrap' }}>{row.basis}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
