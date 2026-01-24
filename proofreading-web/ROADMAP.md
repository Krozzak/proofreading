# 🗺️ PDF Proofreading - Roadmap

## Vision du produit

Application SaaS de comparaison de PDF pour l'industrie de l'impression, similaire à Remove.bg ou iLovePDF.

**Modèle économique**: Freemium
- **Free**: 5 comparaisons/jour
- **Pro** (~$9.99/mois): 100 comparaisons/jour + fonctionnalités IA
- **Enterprise** (sur devis): Illimité + API + support dédié

---

## 📊 État actuel

### ✅ Phase 1: MVP Fonctionnel (EN COURS)

| Tâche | Status | Date |
|-------|--------|------|
| Backend FastAPI créé | ✅ Fait | 24/01/2026 |
| Dockerfile pour Cloud Run | ✅ Fait | 24/01/2026 |
| cloudbuild.yaml configuré | ✅ Fait | 24/01/2026 |
| Frontend connecté à l'API externe | ✅ Fait | 24/01/2026 |
| Configuration Vercel mise à jour | ✅ Fait | 24/01/2026 |
| .env.example créé | ✅ Fait | 24/01/2026 |
| Ancien code Python supprimé | ✅ Fait | 24/01/2026 |
| Déployer backend sur Cloud Run | 🔲 À faire | - |
| Déployer frontend sur Vercel | 🔲 À faire | - |
| Tests end-to-end | 🔲 À faire | - |

---

## 🚀 Phases futures

### 📋 Phase 2: Authentification & Quotas

**Objectif**: Permettre aux utilisateurs de créer un compte et limiter l'usage gratuit.

| Tâche | Status |
|-------|--------|
| Configurer Firebase Auth | 🔲 À faire |
| Créer pages login/register | 🔲 À faire |
| Configurer Firestore | 🔲 À faire |
| Implémenter système de quotas | 🔲 À faire |
| Middleware de vérification quota | 🔲 À faire |
| Dashboard utilisateur (historique) | 🔲 À faire |

**Services utilisés**:
- Firebase Auth (gratuit jusqu'à 50k users/mois)
- Firestore (gratuit jusqu'à 50k lectures/jour)

---

### 💳 Phase 3: Monétisation (Stripe)

**Objectif**: Permettre les abonnements payants.

| Tâche | Status |
|-------|--------|
| Configurer Stripe | 🔲 À faire |
| Créer page pricing | 🔲 À faire |
| Checkout session | 🔲 À faire |
| Webhooks Stripe | 🔲 À faire |
| Gestion des abonnements | 🔲 À faire |
| Emails de confirmation | 🔲 À faire |

**Plans tarifaires**:
| Plan | Prix | Quotas | Fonctionnalités |
|------|------|--------|-----------------|
| Free | $0 | 5/jour | SSIM basique |
| Pro | $9.99/mois | 100/jour | + IA, + historique |
| Enterprise | Sur devis | Illimité | + API, + support |

---

### 🤖 Phase 4: Fonctionnalités IA

**Objectif**: Améliorer la précision avec des modèles multimodaux.

| Tâche | Status |
|-------|--------|
| Intégrer Claude 3 Haiku | 🔲 À faire |
| Comparaison intelligente | 🔲 À faire |
| Détection des différences | 🔲 À faire |
| Rapport automatique | 🔲 À faire |
| Feature flag (Pro only) | 🔲 À faire |

**Modèles envisagés**:
- Claude 3 Haiku (~$0.001/comparaison) - Recommandé
- GPT-4 Vision (~$0.02/comparaison)
- Gemini Pro Vision (~$0.001/comparaison)

---

### 🌐 Phase 5: Landing Page & Marketing

**Objectif**: Attirer des utilisateurs.

| Tâche | Status |
|-------|--------|
| Landing page professionnelle | 🔲 À faire |
| SEO optimisé | 🔲 À faire |
| Blog / tutoriels | 🔲 À faire |
| Intégration analytics | 🔲 À faire |
| Nom de domaine personnalisé | 🔲 À faire |

---

### 🏢 Phase 6: Offre Enterprise

**Objectif**: Monétiser les grandes entreprises.

| Tâche | Status |
|-------|--------|
| API publique documentée | 🔲 À faire |
| Clés API par client | 🔲 À faire |
| Dashboard admin | 🔲 À faire |
| Support prioritaire | 🔲 À faire |
| Contrats personnalisés | 🔲 À faire |

---

## 🏗️ Architecture technique

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND - Vercel (Gratuit)                │
│                    Next.js 16                           │
│            votre-app.vercel.app                         │
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

## 💰 Estimation des coûts

| Phase | Services | Coût mensuel |
|-------|----------|--------------|
| MVP (tests) | Vercel + Cloud Run | **$0** |
| Lancement | + Firebase Auth/Firestore | **$0-5** |
| Croissance | + Stripe + domaine | **~$10-20 + 2.9% transactions** |
| Scale | Tout en Pro | **$50-100+** |

---

## 📁 Structure du projet

```
proofreading-web/
├── app/                    # Pages Next.js
│   ├── page.tsx           # Home (upload)
│   ├── compare/           # Comparison view
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── backend/               # API Python (Cloud Run)
│   ├── main.py           # FastAPI app
│   ├── Dockerfile        # Container config
│   ├── requirements.txt  # Python deps
│   ├── cloudbuild.yaml   # Deployment config
│   └── services/         # Business logic
│       ├── pdf_converter.py
│       └── ssim_calculator.py
├── components/            # React components
│   ├── ComparisonView.tsx
│   ├── DropZone.tsx
│   ├── ResultsTable.tsx
│   └── ui/               # Shadcn components
├── lib/                   # Utilities
│   ├── pdf-utils.ts      # API calls
│   ├── store.ts          # Zustand state
│   └── types.ts          # TypeScript types
├── .env.example          # Environment template
├── vercel.json           # Vercel config
├── ROADMAP.md            # This file
└── package.json          # Node dependencies
```

---

## 🔗 Liens utiles

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Google Cloud Console**: https://console.cloud.google.com
- **Firebase Console**: https://console.firebase.google.com
- **Stripe Dashboard**: https://dashboard.stripe.com

---

## 📝 Notes

### Prochaines étapes immédiates

1. **Créer un projet Google Cloud**
   ```bash
   gcloud projects create proofreading-app
   gcloud config set project proofreading-app
   ```

2. **Déployer le backend sur Cloud Run**
   ```bash
   cd backend
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Récupérer l'URL du backend** et la mettre dans Vercel

4. **Déployer le frontend sur Vercel**
   - Connecter le repo GitHub
   - Ajouter `NEXT_PUBLIC_API_URL` dans les variables d'environnement

5. **Tester l'application** de bout en bout

---

*Dernière mise à jour: 24 janvier 2026*
