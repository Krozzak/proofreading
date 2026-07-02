// First-visit guided tour: 5 steps walking the user through the workflow.
// Reopenable via the "❓ Aide" header button.
import { useState } from 'react'

export const ONBOARDING_KEY = 'avw:onboarding:done'

export function shouldShowOnboarding(): boolean {
  try {
    return localStorage.getItem(ONBOARDING_KEY) !== '1'
  } catch {
    return false
  }
}

export function markOnboardingDone(): void {
  try {
    localStorage.setItem(ONBOARDING_KEY, '1')
  } catch {
    // ignore
  }
}

const STEPS: { icon: string; title: string; body: string }[] = [
  {
    icon: '🏷️',
    title: '1. Choisissez votre marque',
    body:
      "Le menu « Marque » (en haut à droite) détermine les règles : format des noms de fichiers PDF et colonnes du brief. " +
      'MNY et ESSIE sont intégrées ; créez les autres (NYX, L\'Oréal Paris…) en 2 minutes dans Paramètres → Marques → « + Nouvelle marque », ' +
      'ou demandez le JSON au Compagnon GPT et importez-le.',
  },
  {
    icon: '📄',
    title: '2. Récupérez le template Excel',
    body:
      'Dans Paramètres → Marques, chaque marque a un bouton « 📄 Template Excel » : un classeur avec les bons en-têtes, deux lignes ' +
      "d'exemple et une feuille INSTRUCTIONS. Remplissez une ligne par produit — la colonne LITHO doit contenir le code du fichier PDF correspondant.",
  },
  {
    icon: '📁',
    title: '3. Déposez vos fichiers',
    body:
      "Glissez-déposez le dossier de lithos PDF et le brief Excel dans l'onglet Fichiers. " +
      "L'app vérifie les noms de fichiers et les colonnes, extrait le texte des PDFs, puis ouvre la vue Validation. " +
      'Les fichiers au nom invalide sont listés — rien n\'est perdu silencieusement.',
  },
  {
    icon: '✅',
    title: '4. Validez litho par litho',
    body:
      'PDF à gauche, vérifications à droite (vert = trouvé, rouge = introuvable). Approuvez (Ctrl+Entrée) ou refusez (Ctrl+R) avec un ' +
      "commentaire — l'app passe à la suivante. Les PDF sans texte extractible sont marqués « Revue manuelle requise » : " +
      "vérifiez visuellement ou utilisez l'Analyse IA 🤖 (à configurer dans Paramètres).",
  },
  {
    icon: '📊',
    title: '5. Exportez',
    body:
      '« 📊 Rapport » (Ctrl+E) génère le rapport Excel complet (8 feuilles). « 💾 Session » (Ctrl+S) exporte votre travail en JSON : ' +
      'ré-importable ici ou dans l\'app bureau, à archiver ou partager. Votre progression est aussi sauvegardée automatiquement dans le navigateur.',
  },
]

export function OnboardingTour({ open, onClose }: { open: boolean; onClose(): void }) {
  const [step, setStep] = useState(0)

  if (!open) return null

  const current = STEPS[step]

  function close() {
    markOnboardingDone()
    setStep(0)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
        <div className="mb-1 text-4xl">{current.icon}</div>
        <h2 className="mb-2 text-lg font-bold">{current.title}</h2>
        <p className="min-h-28 text-sm text-neutral-600">{current.body}</p>

        <div className="mt-4 flex items-center justify-between">
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={
                  'h-2 w-2 rounded-full ' + (i === step ? 'bg-red-600' : 'bg-neutral-300')
                }
                aria-label={`Étape ${i + 1}`}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <button onClick={close} className="rounded px-3 py-1.5 text-sm text-neutral-500">
              Passer
            </button>
            {step < STEPS.length - 1 ? (
              <button
                onClick={() => setStep(step + 1)}
                className="rounded bg-red-600 px-4 py-1.5 text-sm font-semibold text-white"
              >
                Suivant →
              </button>
            ) : (
              <button
                onClick={close}
                className="rounded bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white"
              >
                C'est parti !
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
