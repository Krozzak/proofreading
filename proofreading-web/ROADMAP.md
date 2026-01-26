# ProofsLab - Roadmap

**Domaine**: [proofslab.com](https://proofslab.com)

## Vision du produit

**ProofsLab** - Application SaaS de comparaison de PDF pour l'industrie de l'impression, similaire à Remove.bg ou iLovePDF.

**Modèle économique**: Freemium

- **Anonymous** (non connecté): 1 comparaison/jour
- **Free** (compte gratuit): 5 comparaisons/jour
- **Pro** ($4.99/mois ou $47.90/an): 100 comparaisons/jour + fonctionnalités IA
- **Enterprise** (sur devis): Illimité + API + support dédié

---

## État actuel

### Phase 1: MVP Fonctionnel (TERMINÉ)

| Tâche | Status | Date |
|-------|--------|------|
| Backend FastAPI créé | Fait | 24/01/2026 |
| Dockerfile pour Cloud Run | Fait | 24/01/2026 |
| cloudbuild.yaml configuré | Fait | 24/01/2026 |
| Frontend connecté à l'API externe | Fait | 24/01/2026 |
| Configuration Vercel mise à jour | Fait | 24/01/2026 |
| .env.example créé | Fait | 24/01/2026 |
| Ancien code Python supprimé | Fait | 24/01/2026 |
| Déployer backend sur Cloud Run | Fait | 24/01/2026 |
| Déployer frontend sur Vercel | Fait | 24/01/2026 |
| Configurer domaine proofslab.com | Fait | 24/01/2026 |
| Tests end-to-end | Fait | 24/01/2026 |

**URLs de production:**

- Frontend: <https://proofslab.com>
- Backend API: <https://proofslab-api-851358345702.europe-west1.run.app>

**Projet GCP:** `proofslab-3f8fe` (Firebase + Cloud Run)

---

### Améliorations UI (à faire plus tard)

Ces améliorations ont été identifiées lors des tests et seront implémentées dans une phase ultérieure :

| Amélioration | Description |
|--------------|-------------|
| Calcul automatique au chargement | Lancer le calcul de similarité automatiquement à l'arrivée sur la page de comparaison |
| Barre de progression animée | La barre de similarité se remplit au fur et à mesure du calcul |
| Bouton "Calculer toutes les similarités" | Calculer tous les scores en séquence, afficher le chargement dans le tableau |
| Auto-approbation par seuil | Bouton pour approuver automatiquement tous les fichiers au-dessus du seuil |
| Barre de recherche dans le tableau | Filtrer le tableau par code ou nom de fichier (à droite du compteur "X fichiers") |

---

## Phases futures

### Phase 2: Authentification & Quotas (TERMINÉ)

**Objectif**: Permettre aux utilisateurs de créer un compte et limiter l'usage gratuit.

| Tâche | Status | Date |
|-------|--------|------|
| Configurer Firebase Auth | Fait | 25/01/2026 |
| Créer modal login/register | Fait | 25/01/2026 |
| Configurer Firestore | Fait | 25/01/2026 |
| Implémenter système de quotas backend | Fait | 25/01/2026 |
| Middleware de vérification auth/quota | Fait | 25/01/2026 |
| Affichage quota utilisateur (header) | Fait | 25/01/2026 |
| Secret Manager pour Firebase Admin | Fait | 25/01/2026 |
| Backend v2.1.0 déployé | Fait | 25/01/2026 |
| Dashboard utilisateur (/dashboard) | Fait | 25/01/2026 |
| CORS regex pour Vercel previews | Fait | 25/01/2026 |
| Création base Firestore europe-west1 | Fait | 25/01/2026 |

**Implémentation technique**:

- **Frontend**: Firebase Auth SDK, AuthContext React, modal login/register/reset password
- **Backend**: Firebase Admin SDK, vérification token, gestion quotas Firestore
- **Quotas**: Anonymous (1/jour par IP), Free (5/jour), Pro (100/jour), Enterprise (illimité)
- **Secret**: `firebase-service-account` dans Google Cloud Secret Manager

**Services utilisés**:

- Firebase Auth (gratuit jusqu'à 50k users/mois)
- Firestore (gratuit jusqu'à 50k lectures/jour) - Region: `europe-west1`
- Secret Manager (gratuit jusqu'à 10k accès/mois)

**Configuration CORS**:

Le backend accepte les origines suivantes :

- `http://localhost:3000` (développement local)
- `https://proofslab.vercel.app`
- `https://proofslab.com`
- `https://www.proofslab.com`
- `https://*.vercel.app` (regex pour les previews Vercel)

---

### Phase 3: Monétisation (Stripe) (TERMINÉ)

**Objectif**: Permettre les abonnements payants.

| Tâche | Status | Date |
|-------|--------|------|
| Configurer Stripe | Fait | 25/01/2026 |
| Créer page pricing | Fait | 25/01/2026 |
| Checkout session | Fait | 25/01/2026 |
| Webhooks Stripe | Fait | 25/01/2026 |
| Gestion des abonnements | Fait | 25/01/2026 |
| Customer Portal (gérer abonnement) | Fait | 25/01/2026 |
| Secrets GCP pour Stripe | Fait | 25/01/2026 |

**Plans tarifaires**:

| Plan | Prix | Quotas | Fonctionnalités |
|------|------|--------|-----------------|
| Anonyme | $0 | 1/jour | SSIM basique |
| Free | $0 | 5/jour | SSIM basique |
| Pro | $4.99/mois ou $47.90/an (-20%) | 100/jour | + IA (bientôt), + support prioritaire |
| Enterprise | Sur devis | Illimité | + API, + support dédié |

**Implémentation technique**:

- **Frontend**: Page `/pricing` avec choix mensuel/annuel, redirection vers Stripe Checkout
- **Backend**: `stripe_service.py` avec création checkout, webhooks, customer portal
- **Webhooks**: `checkout.session.completed`, `customer.subscription.updated/deleted`, `invoice.payment_failed`
- **Secrets GCP**: `stripe-secret-key`, `stripe-webhook-secret`, `stripe-price-monthly`, `stripe-price-yearly`

**URLs Stripe**:

- Dashboard: <https://dashboard.stripe.com>
- Webhook endpoint: `https://proofslab-api-851358345702.europe-west1.run.app/api/stripe/webhook`

---

### Phase 4: Fonctionnalités IA

**Objectif**: Améliorer la précision avec des modèles multimodaux.

| Tâche | Status |
|-------|--------|
| Intégrer Claude 3 Haiku | À faire |
| Comparaison intelligente | À faire |
| Détection des différences | À faire |
| Rapport automatique | À faire |
| Feature flag (Pro only) | À faire |

**Modèles envisagés**:

- Claude 3 Haiku (~$0.001/comparaison) - Recommandé
- GPT-4 Vision (~$0.02/comparaison)
- Gemini Pro Vision (~$0.001/comparaison)

---

### Phase 5: Landing Page & Marketing

**Objectif**: Attirer des utilisateurs.

| Tâche | Status |
|-------|--------|
| Landing page professionnelle | À faire |
| SEO optimisé | À faire |
| Blog / tutoriels | À faire |
| Intégration analytics | À faire |
| Nom de domaine personnalisé | Fait (proofslab.com) |

---

### Phase 6: Offre Enterprise

**Objectif**: Monétiser les grandes entreprises.

| Tâche | Status |
|-------|--------|
| API publique documentée | À faire |
| Clés API par client | À faire |
| Dashboard admin | À faire |
| Support prioritaire | À faire |
| Contrats personnalisés | À faire |

---

### Phase 7: Amélioration du Matching

**Objectif**: Rendre le système de matching plus flexible et user-friendly.

| Tâche | Status |
|-------|--------|
| Documentation du matching (UI tooltip/modal) | À faire |
| Améliorer la robustesse du matching | À faire |
| Wizard de matching manuel pour fichiers non matchés | À faire |
| IA matching automatique (noms différents) | À faire (futur) |

**Détails**:

- **Documentation UI**: Expliquer clairement aux utilisateurs le système de matching actuel (8 premiers caractères) via un tooltip ou une section d'aide sur la page d'upload
- **Matching robuste**: Ignorer les espaces, tirets, underscores ; matching insensible à la casse ; support de préfixes/suffixes communs
- **Wizard manuel**: Interface permettant à l'utilisateur d'associer manuellement les fichiers Original/Imprimeur qui n'ont pas pu être matchés automatiquement
- **IA matching (futur)**: Utiliser un modèle IA pour suggérer des correspondances basées sur le contenu des documents (même si les noms sont différents)

---

## Architecture technique

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND - Vercel (Gratuit)                │
│                    Next.js 16                           │
│               proofslab.com                             │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Firebase    │    │ Firestore   │    │   Stripe    │
│ Auth        │    │ (quotas,    │    │ (paiements) │
│ (gratuit)   │    │ historique) │    │ (2.9%+30¢)  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
              ┌───────────────────────────┐
              │   Google Cloud Run        │
              │   (Scale à 0 = $0 idle)   │
              │                           │
              │   - PDF → Image           │
              │   - SSIM calculation      │
              │   - IA multimodale (futur)│
              └───────────────────────────┘
```

---

## Estimation des coûts

| Phase | Services | Coût mensuel |
|-------|----------|--------------|
| MVP (tests) | Vercel + Cloud Run | **$0** |
| Lancement | + Firebase Auth/Firestore | **$0-5** |
| Croissance | + Stripe + domaine | **~$10-20 + 2.9% transactions** |
| Scale | Tout en Pro | **$50-100+** |

---

## Structure du projet

```
proofreading-web/
├── app/                    # Pages Next.js
│   ├── page.tsx           # Home (upload)
│   ├── compare/           # Comparison view
│   ├── dashboard/         # User dashboard
│   ├── pricing/           # Pricing & checkout
│   ├── layout.tsx         # Root layout (+ AuthProvider)
│   └── globals.css        # Global styles
├── backend/               # API Python (Cloud Run)
│   ├── main.py           # FastAPI app (v2.1.0 avec auth)
│   ├── Dockerfile        # Container config
│   ├── requirements.txt  # Python deps (+ firebase-admin)
│   ├── cloudbuild.yaml   # Deployment config (+ secrets)
│   └── services/         # Business logic
│       ├── pdf_converter.py
│       ├── ssim_calculator.py
│       ├── firebase_admin.py   # Firebase Admin SDK init
│       ├── quota_service.py    # Gestion quotas Firestore
│       ├── auth_dependency.py  # FastAPI auth dependency
│       └── stripe_service.py   # Stripe checkout, webhooks, portal
├── components/            # React components
│   ├── ComparisonView.tsx
│   ├── DropZone.tsx
│   ├── ResultsTable.tsx
│   ├── AuthModal.tsx      # Modal login/register
│   ├── UserMenu.tsx       # Menu utilisateur header
│   ├── QuotaDisplay.tsx   # Affichage quota restant
│   └── ui/               # Shadcn components
├── lib/                   # Utilities
│   ├── pdf-utils.ts      # API calls (+ token auth)
│   ├── store.ts          # Zustand state
│   ├── types.ts          # TypeScript types
│   ├── firebase.ts       # Firebase client config
│   ├── auth-context.tsx  # React auth context
│   └── stripe.ts         # Stripe client utilities
├── .env.example          # Environment template
├── .env.local            # Variables locales (non committé)
├── vercel.json           # Vercel config
├── ROADMAP.md            # This file
└── package.json          # Node dependencies (+ firebase)
```

---

## Liens utiles

- **Vercel Dashboard**: <https://vercel.com/dashboard>
- **Google Cloud Console**: <https://console.cloud.google.com>
- **Firebase Console**: <https://console.firebase.google.com>
- **Stripe Dashboard**: <https://dashboard.stripe.com>

---

*Dernière mise à jour: 25 janvier 2026 - Phase 3 Stripe terminée*
