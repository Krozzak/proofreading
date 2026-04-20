# ProofsLab — Web Application

PDF comparison tool for validating printed materials against original designs.  
Stack: **Next.js 15** (frontend) + **FastAPI** (backend, Cloud Run) + **Firebase Auth** + **Stripe**.

---

## Plans & Quotas

| Plan       | SSIM comparisons       | AI analyses              | Price              |
|------------|------------------------|--------------------------|--------------------|
| Anonyme    | 1/day                  | —                        | Free               |
| Gratuit    | 10/day                 | 10 lifetime (trial)      | Free               |
| Pro        | Unlimited              | 100/month                | $20/month · $192/year |
| Enterprise | Unlimited              | Unlimited                | Custom             |

---

## Project Structure

```
proofreading-web/
├── app/                    # Next.js pages (App Router)
│   ├── page.tsx            # Home — PDF upload
│   ├── compare/page.tsx    # Comparison interface (SSIM + heatmap + AI)
│   ├── dashboard/page.tsx  # User dashboard (quota, subscription)
│   └── pricing/page.tsx    # Pricing page
├── components/             # React components
│   ├── AuthModal.tsx       # Login / signup modal
│   ├── NavBar.tsx          # Top navigation with QuotaDisplay
│   ├── QuotaDisplay.tsx    # Quota badge in navbar
│   └── ComparisonView.tsx  # Side-by-side PDF comparison + heatmap
├── lib/                    # Client utilities
│   ├── auth-context.tsx    # Firebase auth context + quota state
│   ├── firebase.ts         # Firebase client config
│   ├── pdf-utils.ts        # PDF → image conversion, SSIM, AI analysis
│   └── stripe.ts           # Stripe checkout / portal helpers
└── backend/                # FastAPI (deployed on Cloud Run)
    ├── main.py             # API endpoints (v2.3.0)
    ├── Dockerfile
    ├── cloudbuild.yaml     # GCP Cloud Build config
    └── services/
        ├── auth_dependency.py   # Firebase token verification
        ├── quota_service.py     # SSIM + AI quota management
        ├── ai_analyzer.py       # Claude AI analysis (heatmap zones)
        ├── pdf_converter.py     # PDF → PNG via PyMuPDF
        ├── ssim_calculator.py   # SSIM similarity score
        ├── stripe_service.py    # Stripe integration
        ├── history_service.py   # Comparison history (Firestore)
        └── firebase_admin.py    # Firebase Admin SDK
```

---

## Local Development

### Frontend (Next.js)

```bash
cd proofreading-web
npm install
npm run dev
# → http://localhost:3000
```

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=proofslab-3f8fe.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=proofslab-3f8fe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Backend (FastAPI)

```bash
cd proofreading-web/backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

Backend requires the following environment variable (or GCP Secret Manager in prod):

```env
FIREBASE_SERVICE_ACCOUNT=<JSON string of service account key>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_MONTHLY=price_...
STRIPE_PRICE_YEARLY=price_...
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | Public | Health check |
| GET | `/api/quota` | Required | SSIM + AI quota info + tier |
| POST | `/api/convert` | Optional | PDF page → PNG (rate limited 60/min) |
| POST | `/api/compare` | Optional | SSIM comparison (quota-limited) |
| POST | `/api/analyze` | Required | AI heatmap analysis (AI quota-limited) |
| GET | `/api/subscription` | Required | Stripe subscription status |
| POST | `/api/stripe/checkout` | Required | Create Stripe checkout session |
| POST | `/api/stripe/portal` | Required | Stripe customer portal redirect |
| POST | `/api/stripe/webhook` | Public | Stripe webhook (signature-verified) |
| POST | `/api/history/save` | Required | Save comparison batch |
| GET | `/api/history` | Required | List history (paginated) |
| DELETE | `/api/history/{sig}` | Required | Delete history entry |

---

## Deploy to Production

### Backend (Cloud Run)

```bash
cd proofreading-web/backend
gcloud builds submit --config cloudbuild.yaml --project=proofslab-3f8fe
```

Region: `northamerica-northeast1` (Montreal)  
Memory: 1Gi · CPU: 1 · Concurrency: 10 · Max instances: 10

### Frontend (Vercel)

Automatic deployment on push to `main` via Vercel GitHub integration.  
Set `NEXT_PUBLIC_API_URL` to the Cloud Run URL in Vercel environment variables.

---

## Key Technical Details

- **PDF rendering**: PyMuPDF (fitz) at 2× resolution → resized to 800×800 max
- **SSIM**: scikit-image, grayscale, score clamped 0–100
- **File matching**: 8-character prefix (e.g. `12345678_design.pdf` ↔ `12345678_print.pdf`)
- **AI analysis**: Claude Haiku via Anthropic API — identifies difference zones on heatmap
- **Quota atomicity**: Firestore transactions prevent race conditions
- **Auth**: Firebase ID token in `Authorization: Bearer` header
- **Firestore collections**: `users/{uid}` (tier), `quotas/{uid}` (SSIM), `ai_quota/{uid}` (AI)

---

## Version

- Frontend: **v1.4.0**
- Backend API: **v2.3.0**
