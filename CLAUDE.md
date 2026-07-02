# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This monorepo contains four projects around printed-artwork validation:

1. **proofreading-web** - "ProofsLab" SaaS: Next.js frontend + FastAPI backend (production, proofslab.com). SSIM comparison of design vs printer PDFs.
2. **PROOFREADING** - Desktop Tkinter SSIM comparison tool (`proofreading_v3.py` current; v1/v2 archived in `PROOFREADING/legacy/`).
3. **artwork_validator** - Desktop PyQt6 "L'Oréal Litho Validator": validates litho PDFs against an Excel brief with per-brand rules (MNY, ESSIE). ~22k lines, French README.
4. **artwork-validator-web** - Browser port of artwork_validator (Vite + React + TS). Builds to ONE self-contained `dist/index.html` that works via `file://`. `src/core/` is a 1:1 port of `artwork_validator/core/` with a Python↔TS parity test suite.

## Project Structure

```
proofreading/
├── proofreading-web/                # ProofsLab SaaS (Next.js 16 + FastAPI)
│   ├── app/                         # App Router pages (home, compare, dashboard,
│   │                                #   history, workspace, pricing, contact, legal…)
│   ├── components/                  # React components (+ components/ui shadcn)
│   ├── lib/                         # auth-context, firebase, pdf-utils, store…
│   └── backend/                     # FastAPI on Cloud Run
│       ├── main.py                  # API endpoints
│       └── services/                # firebase_admin, auth, quota, pdf, ssim,
│                                    #   ai_analyzer, stripe, history
├── PROOFREADING/                    # Desktop SSIM tool (Tkinter)
│   ├── proofreading_v3.py           # Current version
│   ├── PrinterProofreading_v3.spec  # PyInstaller spec
│   └── legacy/                      # v1, v2, old spec
├── artwork_validator/               # Desktop litho validator (PyQt6)
│   ├── core/                        # excel_processor, validator (legacy engine),
│   │   │                            #   enhanced_validator, pdf_processor,
│   │   │                            #   report_generator, data_collector,
│   │   │                            #   error_templates, ocr_processor (optional)
│   │   ├── brand_configs/           # MNY + ESSIE rules (Abstract Factory)
│   │   └── basecamp/                # Selenium Basecamp automation (desktop-only)
│   ├── ui/                          # PyQt6 UI
│   ├── utils/                       # session_manager (JSON sessions)
│   └── scripts/gen_parity_vectors.py# Generates web-port parity test vectors
├── artwork-validator-web/           # Web litho validator (single-file build)
│   ├── src/core/                    # 1:1 TS port of artwork_validator/core
│   ├── src/lib/                     # pdfEngine (pdf.js inline worker), excelIO
│   │                                #   (exceljs), sessionStore (localStorage)
│   ├── src/ui/ + src/state/         # French React UI + Zustand store
│   ├── tests/                       # vitest; fixtures/parity/vectors.json
│   └── scripts/                     # gen_fixtures.py, e2e.mjs (Playwright file://)
└── docs/DOCUMENTATION.md            # Monorepo technical overview
```

### artwork-validator-web — critical invariants

- **Parity with Python**: `src/core/` must behave exactly like `artwork_validator/core/`. Regenerate vectors with `python3 artwork_validator/scripts/gen_parity_vectors.py` and run `npm test` after touching either side. Comments marked `PARITY:` reproduce Python bugs ON PURPOSE (enhanced-validator duplicate allowance for rows ≥ 2; cross-row token position never advancing) — do not fix them unilaterally.
- The Excel column `DECRIPTION` is **intentionally misspelled** (real briefs use it).
- Basecamp and OCR are excluded from the web port; PDFs with < 50 extractable chars get `needsManualReview` (extension point: `TextRecoveryProvider`; the AI panel is the practical fallback).
- Build must stay single-file and `file://`-compatible: no lazy `import()`, pdf.js worker inlined via `?worker&inline`.
- E2E: `npm run build && python3 scripts/gen_fixtures.py && node scripts/e2e.mjs` (uses `/opt/pw-browsers/chromium`).
- **Brands are JSON definitions** (`src/core/brandConfigs/brandSchema.ts`, `BrandDefinition` schema v1): built-ins MNY/ESSIE in `builtinBrands.ts`, custom brands in localStorage `avw:brands` via `src/lib/brandStore.ts`, created through the wizard (`src/ui/BrandWizard.tsx`), JSON import, or AI generation. Never hardcode a new brand as a class — add a definition. The internal-GPT companion prompt lives in `artwork-validator-web/docs/COMPAGNON_PROMPT.md` and embeds this schema: update it whenever the schema or the UI wording changes.
- **AI layer** (`src/lib/ai/`): provider-agnostic (Anthropic Messages / OpenAI chat-completions), settings in localStorage `avw:ai:settings`, key never leaves the browser. `aiValidator.ts` returns rule-engine-shaped verdicts; `brandGenerator.ts` outputs `BrandDefinition` validated by `validateBrandDefinition`.

## Core Architecture

### File Matching Logic
All versions use an 8-character prefix matching system:
- Extract first 8 characters from filenames
- Match "Original/Design" files with "Imprimeur/Printer" files
- Example: `12345678_design.pdf` matches `12345678_print.pdf`
- **IMPORTANT**: Process ALL files from BOTH folders, not just matched pairs
  - First: Match all Original files with their Printer counterparts
  - Then: Add any Printer files that have no Original match
  - This ensures no files are missed in the comparison

### Image Comparison Pipeline
1. **PDF → Image**: Convert first page using PyMuPDF (fitz) at 2x resolution
2. **Preprocessing**:
   - Resize to common dimensions (800x800 max)
   - Convert to grayscale
   - Optional: Crop margins / content detection (desktop v3)
3. **Similarity Calculation**: Use scikit-image SSIM on grayscale arrays
4. **Scoring**: Convert SSIM index to 0-100 percentage scale

### Key Dependencies (SSIM tools)
- **PyMuPDF (fitz)**: PDF rendering
- **Pillow (PIL)**: Image manipulation
- **scikit-image**: SSIM calculation
- **NumPy**: Array operations
- **tkinterdnd2**: Drag-and-drop (desktop tool only)

## Development Commands

### proofreading-web (Next.js + FastAPI - Current Production)

**Frontend (Next.js):**
```bash
cd proofreading-web
npm install
npm run dev
```
Frontend runs on http://localhost:3000

**Backend (FastAPI) - Local:**
```bash
cd proofreading-web/backend
pip install -r requirements.txt
python main.py
```
Backend runs on http://localhost:8000

**Backend Deployment (Cloud Run):**
```bash
cd proofreading-web/backend
gcloud builds submit --config cloudbuild.yaml --project=proofslab-3f8fe
```

**Environment Variables:**
- Frontend (.env.local):
  - `NEXT_PUBLIC_API_URL` - Backend API URL
  - `NEXT_PUBLIC_FIREBASE_*` - Firebase client config
- Backend (Cloud Run secrets):
  - `FIREBASE_SERVICE_ACCOUNT` - Firebase Admin SDK credentials (JSON string)

### PROOFREADING (Tkinter Desktop)

**Run application:**
```bash
pip install -r requirements.txt
cd PROOFREADING
python proofreading_v3.py
```

**Build executable:**
```bash
cd PROOFREADING
pyinstaller PrinterProofreading_v3.spec
```
Creates a single-file Windows executable (no console, with icon).

Legacy v1/v2 live in `PROOFREADING/legacy/` (run `python legacy/proofreading_v2.py` if ever needed).

### artwork_validator (PyQt6 Desktop)

```bash
cd artwork_validator
pip install PyQt6 pandas openpyxl PyMuPDF   # + selenium / paddleocr for optional features
python main.py
```

### artwork-validator-web (Vite + React + TS)

```bash
cd artwork-validator-web
npm install
npm run dev        # dev server
npm test           # vitest unit + Python-parity suite
npm run build      # single self-contained dist/index.html
# E2E: python3 scripts/gen_fixtures.py && node scripts/e2e.mjs
```

## Key Implementation Details

### PROOFREADING v3 (desktop) Specifics
- **Drag-and-drop**: Uses tkinterdnd2 for folder selection
- **Content detection**: automatic crop of margins/bleeds/crop marks, manual adjustment
- **Adjustable threshold**: User can set similarity threshold (default 85%)
- **Manual review**: Side-by-side comparison with approve/reject workflow
- **CSV export**: Includes timestamp and user decisions

### Comparison Algorithm Tuning
- **Resolution**: 2x scale factor on PDF rendering balances quality vs performance
- **Thumbnail size**: 800x800 max prevents memory issues on large PDFs
- **SSIM parameters**: Uses default scikit-image settings, data_range auto-calculated
- **Score range**: Clamped 0-100 for display, but internal SSIM can be negative

## Common Patterns

### PDF Processing
```python
doc = fitz.open(pdf_path)
page = doc.load_page(0)  # First page only
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
doc.close()
```

### SSIM Comparison
```python
# Convert to grayscale, normalize
gray1 = np.mean(arr1, axis=2).astype(np.float32)
gray2 = np.mean(arr2, axis=2).astype(np.float32)

# Calculate SSIM
similarity_index = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
score = max(0, min(100, similarity_index * 100))  # Clamp to 0-100
```

### File Code Extraction
```python
def extract_code(filename):
    base_name = os.path.basename(filename)
    return base_name[:8] if len(base_name) >= 8 else base_name
```

## Building for Production

### Web Application Bundle
The `build_portable.py` script uses PyInstaller to create a self-contained executable:
- Bundles Flask, templates, static files
- Uses `--onedir` mode for easier updates
- Includes all hidden imports for Flask ecosystem
- Creates portable package that doesn't require Python installation

### Desktop Application Bundle
The `PrinterProofreading.spec` configures PyInstaller:
- Single-file executable (`--onefile` equivalent)
- No console window (`console=False`)
- UPX compression enabled
- Custom icon support

## Important Notes

### Platform Compatibility
- **Windows-focused**: Path handling and executable generation assume Windows
- **Font paths**: Hardcoded `arial.ttf` may fail on non-Windows systems
- **File paths**: Use `os.path.join()` and `os.path.expanduser()` for portability

### Performance Considerations
- **Memory**: Large PDFs at 2x resolution can consume significant memory
- **Processing time**: SSIM calculation is CPU-intensive, scales with image size
- **File limits**: Web app has 500MB upload limit configured

### Security Notes
- **Firestore Rules**: All client-side access is denied (`allow read, write: if false`). All data access goes through the backend API using Firebase Admin SDK which bypasses rules.
- **Quota atomicity**: Quota check+increment uses Firestore transactions to prevent race conditions from concurrent requests bypassing limits.
- **CORS**: Origins restricted to `proofslab.com`, `proofslab.vercel.app`, and project-specific Vercel preview URLs. Methods limited to `GET, POST, DELETE, OPTIONS`. Headers limited to `Authorization, Content-Type, Stripe-Signature`.
- **Stripe redirect validation**: All `successUrl`, `cancelUrl`, and `returnUrl` parameters are validated against allowed domains to prevent open redirect attacks.
- **Rate limiting**: `/api/convert` is rate limited to 60 requests/minute per IP (in-memory sliding window).
- **Payload limits**: Base64 fields (`pdf`, `image1`, `image2`) are capped at ~50MB via Pydantic `max_length`.
- **Error masking**: Internal exception details are never returned to clients. Generic messages are returned, details are logged server-side only.
- **Container security**: Docker container runs as non-root user (`appuser`, UID 1001).
- **Webhook resilience**: Stripe webhook handler returns 500 on processing errors so Stripe retries.
- **Pagination bounds**: History `limit` capped at 500, `offset` must be >= 0.
- **Pinned dependencies**: All Python dependencies use exact versions (`==`) in `requirements.txt` to prevent supply chain attacks.
- **Secrets management**: Backend secrets (Stripe keys, Firebase service account) stored in GCP Secret Manager, injected at deploy time.
- **File uploads (legacy)**: Original filenames are preserved for matching; subdirectories are created as needed.
- **Temporary files (legacy)**: Not automatically cleaned up, requires manual deletion.

## Recent Fixes (January 2026)

### Fixed Issues
1. **Filename Sanitization Bug**: Removed `secure_filename()` that was modifying file names and breaking the 8-character code matching
   - Files are now saved with their original names to preserve matching codes
   - Subdirectories are created as needed to support file.webkitRelativePath structure

2. **Incomplete File Processing**: Added logic to process ALL files from both folders
   - Previously only processed Original folder files
   - Now also processes Printer-only files that have no Original match
   - Prevents files from being silently ignored

3. **Web Interface**: Redesigned to match Tkinter desktop interface
   - Side-by-side image comparison (Original on left, Printer on right)
   - Navigation buttons (Previous/Next)
   - Validation buttons (Approve/Reject) with auto-navigation
   - Similarity bar with threshold line
   - Results table below for quick navigation

4. **Removed Unused Dependencies**: Cleaned up imports
   - Removed `imagehash` (was imported but never used)
   - Removed `cv2` / `opencv-python` (was imported but never used)

## Authentication & Quota System (v1.2.0+)

### Firebase Authentication
The proofreading-web app uses Firebase Authentication:
- **Client-side**: Firebase JS SDK in `lib/firebase.ts` and `lib/auth-context.tsx`
- **Server-side**: Firebase Admin SDK in `backend/services/firebase_admin.py`
- **Supported methods**: Email/password authentication
- **Token flow**: Client gets ID token → sends in `Authorization: Bearer` header → backend verifies

### Quota System
Usage quotas are managed per user tier, with two separate quota types:

**SSIM Comparisons** (daily, resets midnight UTC):
- **Anonymous**: 1 comparison/day (IP-based tracking)
- **Free account**: 10 comparisons/day
- **Pro account**: Unlimited
- **Enterprise**: Unlimited

**AI Analyses**:
- **Anonymous**: 0 (not available)
- **Free account**: 10 analyses lifetime (trial, never resets)
- **Pro account**: 100 analyses/month (resets 1st of month UTC)
- **Enterprise**: Unlimited

Quota data stored in Firestore (`quotas/{uid}` for SSIM, `ai_quota/{uid}` for AI, `users/{uid}` for tier).

### Backend API Endpoints

- `GET /api/health` - Health check (public)
- `GET /api/quota` - Get user's quota info (authenticated)
- `POST /api/convert` - Convert PDF to image (public, rate limited 60/min per IP)
- `POST /api/compare` - Compare two images (quota-limited)
- `POST /api/stripe/checkout` - Create Stripe checkout session (authenticated)
- `POST /api/stripe/portal` - Create Stripe customer portal session (authenticated)
- `GET /api/subscription` - Get subscription info (authenticated)
- `POST /api/stripe/webhook` - Stripe webhook handler (public, signature-verified)
- `POST /api/history/save` - Save comparison history (authenticated)
- `POST /api/history/match` - Match files from history (authenticated)
- `GET /api/history` - List comparison history (authenticated, paginated)
- `DELETE /api/history/{file_signature}` - Delete history entry (authenticated)

### Cloud Run Configuration

The backend deploys to Cloud Run with:

- Region: `northamerica-northeast1` (Montreal, Canada)
- Memory: 1Gi
- CPU: 1
- Concurrency: 10
- Max instances: 10
- Secrets from GCP Secret Manager:
  - `firebase-service-account` - Firebase Admin SDK credentials
  - `stripe-secret-key` - Stripe API secret key
  - `stripe-webhook-secret` - Stripe webhook signing secret
  - `stripe-price-monthly` - Stripe monthly price ID
  - `stripe-price-yearly` - Stripe yearly price ID

To set up a secret:

```bash
gcloud secrets create firebase-service-account \
  --data-file=path/to/serviceAccountKey.json \
  --project=proofslab-3f8fe
```

## Version Information

- **proofreading-web**: package.json 1.2.0 (frontend) / main.py docstring 2.2.0 (backend API)
- **PROOFREADING**: v3 (proofreading_v3.py)
- **artwork_validator**: v2.1 (desktop, see PROJECT_ROADMAP.md)
- **artwork-validator-web**: v1.0.0

## Security Audit (February 2026)

### Fixes Applied

1. **Firestore Security Rules**: Deployed rules blocking all direct client access. Data is only accessible through the backend API via Firebase Admin SDK.
2. **Atomic Quota Enforcement**: Replaced read-then-write quota logic with Firestore transactions (`@cloud_firestore.transactional`) to prevent concurrent requests from bypassing limits.
3. **Open Redirect Prevention**: Stripe redirect URLs (`successUrl`, `cancelUrl`, `returnUrl`) are validated against an allowlist of domains before being passed to Stripe.
4. **CORS Hardening**: Restricted `allow_origin_regex` from `.*\.vercel\.app` (any Vercel site) to only this project's preview URLs. Limited allowed methods and headers.
5. **Rate Limiting**: Added in-memory sliding window rate limiter on `/api/convert` (60 req/min per IP) to prevent abuse.
6. **Payload Size Limits**: Base64 fields capped at ~50MB via Pydantic `Field(max_length=70_000_000)`.
7. **Error Masking**: Internal exception details are no longer returned to clients. Generic error messages are sent, full details are logged server-side.
8. **Non-root Container**: Dockerfile now creates and runs as `appuser` (UID 1001) instead of root.
9. **Webhook Error Handling**: Stripe webhook handler now returns HTTP 500 on processing errors, allowing Stripe to retry failed events.
10. **Pagination Bounds**: History endpoint `limit` bounded to 1-500, `offset` bounded to >= 0 via `Query()` validators.
11. **Pinned Dependencies**: All Python dependencies use exact versions (`==`) in `requirements.txt`.
12. **IP Hash**: Anonymous quota now uses full SHA-256 hash (previously truncated to 16 chars).
13. **Region Migration**: Backend moved from `europe-west1` (Belgium) to `northamerica-northeast1` (Montreal) for lower latency from Canada.

### Future Security Improvements (Roadmap)

- **External rate limiter**: Replace in-memory rate limiter with Redis or Cloud Armor for persistence across Cloud Run instances.
- **Content Security Policy (CSP)**: Add CSP headers to the Next.js frontend to mitigate XSS.
- **HTTPS-only cookies**: Ensure all auth cookies use `Secure`, `HttpOnly`, and `SameSite=Strict` flags.
- **Dependency scanning**: Set up automated vulnerability scanning (e.g., Dependabot, Snyk) on GitHub.
- **Logging & monitoring**: Add Cloud Logging alerts for repeated 401/403/429 errors to detect brute force or abuse patterns.
- **PDF input sanitization**: Validate PDF structure before processing with PyMuPDF to mitigate crafted PDF exploits.
- **Email verification**: Require email verification before allowing comparisons on free accounts.
- **Stripe live keys**: Migrate from test mode (`pk_test_`) to live keys (`pk_live_`) for production payments.
