# Stripe Integration - ProofsLab

Documentation technique de l'intégration Stripe pour la monétisation de ProofsLab.

## Configuration

### Prérequis

- Compte Stripe (test ou production)
- Projet GCP avec Secret Manager activé
- Backend déployé sur Cloud Run

### Variables d'environnement

**Frontend (Vercel):**
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx ou pk_live_xxx
```

**Backend (GCP Secret Manager):**
```
stripe-secret-key        # sk_test_xxx ou sk_live_xxx
stripe-webhook-secret    # whsec_xxx
stripe-price-monthly     # price_xxx (ID du prix mensuel)
stripe-price-yearly      # price_xxx (ID du prix annuel)
```

### Création des secrets GCP

```bash
# Clé secrète Stripe (IMPORTANT: utiliser printf pour éviter les \r\n)
printf '%s' "sk_test_xxx" | gcloud secrets create stripe-secret-key --data-file=- --project=proofslab-3f8fe

# Webhook secret (obtenu après création du webhook dans Stripe)
printf '%s' "whsec_xxx" | gcloud secrets create stripe-webhook-secret --data-file=- --project=proofslab-3f8fe

# Price IDs
printf '%s' "price_xxx" | gcloud secrets create stripe-price-monthly --data-file=- --project=proofslab-3f8fe
printf '%s' "price_xxx" | gcloud secrets create stripe-price-yearly --data-file=- --project=proofslab-3f8fe
```

**⚠️ Important:** Toujours utiliser `printf '%s'` au lieu de `echo -n` pour éviter les caractères `\r\n` qui causent des erreurs Stripe.

### Mise à jour d'un secret

```bash
printf '%s' "nouvelle_valeur" | gcloud secrets versions add stripe-secret-key --data-file=- --project=proofslab-3f8fe
```

### Permissions Cloud Run

```bash
gcloud secrets add-iam-policy-binding stripe-secret-key \
  --member="serviceAccount:851358345702-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=proofslab-3f8fe
```

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │    Backend      │     │     Stripe      │
│   (Next.js)     │     │   (FastAPI)     │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ 1. Click "Passer Pro" │                       │
         │──────────────────────>│                       │
         │                       │ 2. Create checkout    │
         │                       │──────────────────────>│
         │                       │<──────────────────────│
         │ 3. Redirect URL       │  checkout.url         │
         │<──────────────────────│                       │
         │                       │                       │
         │ 4. User pays on Stripe│                       │
         │─────────────────────────────────────────────->│
         │                       │                       │
         │                       │ 5. Webhook event      │
         │                       │<──────────────────────│
         │                       │ 6. Update Firestore   │
         │                       │                       │
         │ 7. Redirect success   │                       │
         │<─────────────────────────────────────────────│
         │                       │                       │
```

---

## Endpoints API

### POST /api/stripe/checkout

Crée une session Stripe Checkout.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
```

**Body:**
```json
{
  "billing_period": "monthly" | "yearly"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_xxx"
}
```

### POST /api/stripe/portal

Redirige vers le Customer Portal Stripe pour gérer l'abonnement.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
```

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/xxx"
}
```

### GET /api/subscription

Récupère les informations d'abonnement de l'utilisateur.

**Headers:**
```
Authorization: Bearer <firebase_id_token>
```

**Response:**
```json
{
  "status": "active" | "canceled" | "past_due" | "none",
  "current_period_end": "2026-02-25T00:00:00Z",
  "cancel_at_period_end": false,
  "billing_period": "monthly" | "yearly"
}
```

### POST /api/stripe/webhook

Endpoint pour les webhooks Stripe (appelé par Stripe).

**Headers:**
```
Stripe-Signature: <signature>
```

**Events gérés:**
- `checkout.session.completed` - Paiement réussi
- `customer.subscription.updated` - Abonnement modifié
- `customer.subscription.deleted` - Abonnement annulé
- `invoice.payment_failed` - Paiement échoué

---

## Produits Stripe

### Configuration actuelle (Test)

| Produit | Price ID | Prix |
|---------|----------|------|
| ProofsLab Pro Mensuel | `price_1StYbuDHtayMbPTRJ32Mehmt` | $4.99/mois |
| ProofsLab Pro Annuel | `price_1StYcLDHtayMbPTRrf0Lc156` | $47.90/an |

### Création des produits (Dashboard Stripe)

1. Aller dans **Products** > **Add product**
2. Nom: "ProofsLab Pro"
3. Créer 2 prix:
   - Recurring, $4.99 USD, Monthly
   - Recurring, $47.90 USD, Yearly
4. Copier les Price IDs (`price_xxx`)

---

## Webhooks

### Configuration

1. Stripe Dashboard > Developers > Webhooks
2. Add endpoint:
   - URL: `https://proofslab-api-851358345702.europe-west1.run.app/api/stripe/webhook`
   - Events:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`
3. Copier le Signing secret (`whsec_xxx`)
4. Mettre à jour le secret GCP

### Test local avec Stripe CLI

```bash
# Installer Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks vers localhost
stripe listen --forward-to localhost:8000/api/stripe/webhook

# Déclencher un événement test
stripe trigger checkout.session.completed
```

---

## Customer Portal

### Configuration

1. Stripe Dashboard > Settings > Billing > Customer portal
2. Activer les fonctionnalités:
   - ✅ Update payment methods
   - ✅ View invoice history
   - ✅ Cancel subscriptions
3. Sauvegarder

---

## Flux utilisateur

### Upgrade vers Pro

1. Utilisateur connecté clique "Passer au Pro" ou "Voir les plans"
2. Redirection vers `/pricing`
3. Choix mensuel/annuel
4. Click "Passer au Pro"
5. Redirection vers Stripe Checkout
6. Paiement avec carte test: `4242 4242 4242 4242`
7. Webhook `checkout.session.completed` reçu
8. Backend met à jour Firestore: `tier: "pro"`
9. Redirection vers `/dashboard?upgraded=true`
10. Quota passe de 5 à 100 comparaisons/jour

### Annulation

1. Utilisateur va dans Dashboard > "Gérer mon abonnement"
2. Redirection vers Stripe Customer Portal
3. Click "Cancel subscription"
4. Webhook `customer.subscription.updated` reçu (cancel_at_period_end: true)
5. Accès Pro maintenu jusqu'à fin de période
6. Webhook `customer.subscription.deleted` à la fin
7. Backend met à jour Firestore: `tier: "free"`

---

## Données Firestore

### Structure utilisateur

```
users/{uid}
├── email: "user@example.com"
├── tier: "free" | "pro" | "enterprise"
├── stripeCustomerId: "cus_xxx"
├── stripeSubscriptionId: "sub_xxx"
├── subscriptionStatus: "active" | "canceled" | "past_due"
├── currentPeriodEnd: Timestamp
├── cancelAtPeriodEnd: false
├── billingPeriod: "monthly" | "yearly"
├── dailyUsage: 3
├── lastUsageDate: "2026-01-25"
└── createdAt: Timestamp
```

---

## Cartes de test

| Numéro | Comportement |
|--------|--------------|
| `4242 4242 4242 4242` | Paiement réussi |
| `4000 0000 0000 0002` | Carte refusée |
| `4000 0000 0000 9995` | Fonds insuffisants |
| `4000 0027 6000 3184` | Requiert authentification 3D Secure |

Date d'expiration: n'importe quelle date future (ex: 12/34)
CVC: n'importe quel nombre à 3 chiffres (ex: 123)

---

## Passage en production

### Checklist

- [ ] Créer les produits en mode Live sur Stripe
- [ ] Mettre à jour les secrets GCP avec les clés Live
- [ ] Mettre à jour la variable Vercel avec la clé publique Live
- [ ] Configurer le webhook en mode Live
- [ ] Activer le Customer Portal en mode Live
- [ ] Tester un paiement réel avec une vraie carte

### Commandes

```bash
# Mettre à jour vers les clés production
printf '%s' "sk_live_xxx" | gcloud secrets versions add stripe-secret-key --data-file=- --project=proofslab-3f8fe
printf '%s' "whsec_live_xxx" | gcloud secrets versions add stripe-webhook-secret --data-file=- --project=proofslab-3f8fe
printf '%s' "price_live_xxx" | gcloud secrets versions add stripe-price-monthly --data-file=- --project=proofslab-3f8fe
printf '%s' "price_live_xxx" | gcloud secrets versions add stripe-price-yearly --data-file=- --project=proofslab-3f8fe

# Redéployer le backend
cd proofreading-web/backend
gcloud builds submit --config cloudbuild.yaml --project=proofslab-3f8fe
```

---

## Troubleshooting

### Erreur "Invalid header value" avec \r\n

**Cause:** Les secrets contiennent des caractères de retour chariot.

**Solution:**
```bash
# Recréer le secret avec printf
printf '%s' "valeur_sans_retour" | gcloud secrets versions add stripe-secret-key --data-file=- --project=proofslab-3f8fe

# Forcer le rechargement
gcloud run services update proofslab-api --region=europe-west1 --project=proofslab-3f8fe \
  --update-secrets="STRIPE_SECRET_KEY=stripe-secret-key:latest"
```

### Erreur "No such price"

**Cause:** Le Price ID est incorrect ou le produit est archivé.

**Solution:**
1. Vérifier le Price ID dans Stripe Dashboard > Products
2. S'assurer que le produit n'est pas archivé
3. Mettre à jour le secret GCP si nécessaire

### Webhook non reçu

**Vérifications:**
1. URL du webhook correcte dans Stripe Dashboard
2. Events sélectionnés correctement
3. Vérifier les logs: `gcloud run services logs read proofslab-api --project=proofslab-3f8fe --region=europe-west1 --limit=50`

### Customer Portal ne s'ouvre pas

**Cause:** Le Customer Portal n'est pas configuré.

**Solution:**
1. Stripe Dashboard > Settings > Billing > Customer portal
2. Activer et configurer les options
3. Sauvegarder

---

## Logs et monitoring

### Voir les logs backend

```bash
gcloud run services logs read proofslab-api \
  --project=proofslab-3f8fe \
  --region=europe-west1 \
  --limit=100
```

### Filtrer par erreur Stripe

```bash
gcloud run services logs read proofslab-api \
  --project=proofslab-3f8fe \
  --region=europe-west1 \
  --limit=100 | grep -i stripe
```

### Dashboard Stripe

- Paiements: https://dashboard.stripe.com/test/payments
- Webhooks: https://dashboard.stripe.com/test/webhooks
- Customers: https://dashboard.stripe.com/test/customers
- Subscriptions: https://dashboard.stripe.com/test/subscriptions

---

*Dernière mise à jour: 25 janvier 2026*
