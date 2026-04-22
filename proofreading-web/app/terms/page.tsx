'use client';

import { NavBar } from '@/components/NavBar';
import { SiteFooter } from '@/components/SiteFooter';
import { LegalNav } from '@/app/legal/page';

export default function TermsPage() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--background)', color: 'var(--foreground)' }}>
      <NavBar />

      <div style={{ flex: 1, maxWidth: 760, margin: '0 auto', width: '100%', padding: '64px 32px', boxSizing: 'border-box' }}>

        <div style={{ marginBottom: 56 }}>
          <div style={{ fontSize: 12, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: 16 }}>
            Dernière mise à jour · Avril 2026
          </div>
          <h1 style={{ fontSize: 'clamp(36px, 5vw, 56px)', margin: 0, lineHeight: 1, letterSpacing: '-0.03em', fontWeight: 500 }}>
            Conditions{' '}
            <em style={{ fontFamily: 'var(--font-instrument-serif)', fontStyle: 'italic', fontWeight: 400, color: 'var(--c4)' }}>
              d'utilisation.
            </em>
          </h1>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 48 }}>

          <Section title="1. Acceptation des conditions">
            <p>En accédant à Proofslab et en utilisant ses services, vous acceptez sans réserve les présentes Conditions Générales d'Utilisation (CGU). Si vous n'acceptez pas ces conditions, veuillez ne pas utiliser le service.</p>
          </Section>

          <Section title="2. Description du service">
            <p>Proofslab est un outil SaaS de comparaison de fichiers PDF. Il permet aux utilisateurs de comparer des fichiers design originaux avec des épreuves d'imprimeur en calculant un score de similarité SSIM (Structural Similarity Index), d'afficher une heatmap des différences, et d'approuver ou rejeter des fichiers.</p>
          </Section>

          <Section title="3. Création de compte">
            <p>Pour accéder à certaines fonctionnalités, vous devez créer un compte avec une adresse email valide. Vous êtes responsable de la confidentialité de vos identifiants et de toutes les activités effectuées depuis votre compte.</p>
            <p>Vous vous engagez à fournir des informations exactes et à notifier immédiatement Proofslab de toute utilisation non autorisée de votre compte.</p>
          </Section>

          <Section title="4. Plans et paiements">
            <p><strong>Plan Gratuit</strong> — Accès gratuit incluant les comparaisons SSIM illimitées et 10 analyses IA offertes à vie.</p>
            <p><strong>Plan Pro</strong> — Abonnement mensuel ou annuel donnant accès aux comparaisons SSIM illimitées, 100 analyses IA par mois et au support prioritaire. Les paiements sont traités par Stripe. En souscrivant, vous autorisez Proofslab à débiter votre moyen de paiement selon la fréquence choisie.</p>
            <p><strong>Annulation</strong> — Vous pouvez annuler votre abonnement à tout moment depuis votre tableau de bord. L'accès Pro est maintenu jusqu'à la fin de la période de facturation en cours. Aucun remboursement partiel n'est accordé, sauf dans les 14 jours suivant le premier achat.</p>
          </Section>

          <Section title="5. Utilisation acceptable">
            <p>Vous vous engagez à ne pas :</p>
            <ul style={{ paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <li>Utiliser le service à des fins illégales ou non autorisées</li>
              <li>Tenter de contourner les mécanismes de quota ou de sécurité</li>
              <li>Uploader des fichiers contenant des logiciels malveillants</li>
              <li>Reproduire, vendre ou revendre l'accès au service sans autorisation</li>
              <li>Utiliser des systèmes automatisés pour accéder au service au-delà des limites de l'API documentée</li>
            </ul>
          </Section>

          <Section title="6. Propriété des données">
            <p>Vos fichiers PDF uploadés vous appartiennent. Proofslab ne conserve pas vos fichiers PDF après traitement — seuls les métadonnées (scores, noms de fichiers, validations) sont enregistrées dans votre historique si vous êtes connecté.</p>
            <p>Proofslab ne cède, ne vend et n'exploite pas vos données à des fins commerciales.</p>
          </Section>

          <Section title="7. Disponibilité du service">
            <p>Proofslab s'efforce d'assurer une disponibilité maximale du service mais ne garantit pas un accès ininterrompu. Des maintenances programmées ou des interruptions imprévues peuvent survenir. Proofslab ne saurait être tenu responsable des pertes résultant d'une indisponibilité du service.</p>
          </Section>

          <Section title="8. Limitation de responsabilité">
            <p>Le service est fourni « en l'état », sans garantie d'aucune sorte. Les scores de similarité sont fournis à titre indicatif. Proofslab ne saurait être tenu responsable de décisions prises sur la base des résultats fournis par le service.</p>
            <p>En aucun cas la responsabilité de Proofslab ne pourra excéder le montant total payé par l'utilisateur au cours des 12 derniers mois.</p>
          </Section>

          <Section title="9. Modifications des CGU">
            <p>Proofslab se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs seront notifiés par email en cas de changements substantiels. La poursuite de l'utilisation du service après notification vaut acceptation des nouvelles conditions.</p>
          </Section>

          <Section title="10. Droit applicable">
            <p>Les présentes CGU sont régies par le droit canadien (province de Québec). Tout litige sera soumis à la compétence exclusive des tribunaux compétents du Québec.</p>
          </Section>

          <Section title="Contact">
            <p>Pour toute question : <a href="mailto:silliard.thomas@ekenor.com" style={{ color: 'var(--c4)', textDecoration: 'none' }}>silliard.thomas@ekenor.com</a></p>
          </Section>

        </div>

        <LegalNav current="/terms" />
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
