# Technical Documentation — ProofsLab Monorepo

This document gives a technical overview of the four projects in this
repository and points to their dedicated documentation. Project-specific
details live next to each project.

## 1. ProofsLab (web) — `proofreading-web/`

**Purpose**: SaaS PDF proof comparison (original design vs printer proof).

**Architecture**:

- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS
  v4, shadcn/ui, Zustand. Deployed on Vercel. UI language: French.
- **Backend**: FastAPI on Google Cloud Run (region
  `northamerica-northeast1`). Endpoints for PDF→image conversion, SSIM
  comparison, AI analysis (Claude), quotas, Stripe billing, history.
- **Auth**: Firebase Authentication (email/password). The client sends a
  Firebase ID token as `Authorization: Bearer`; the backend verifies it with
  the Firebase Admin SDK.
- **Data**: Firestore (quotas, users, history). Direct client access is
  blocked by security rules; all access goes through the backend.

**Comparison pipeline**: PDF → image (PyMuPDF, 2× matrix) → resize to a
common bounding box → grayscale → SSIM (scikit-image) → 0–100 score.

Further reading: [`proofreading-web/README.md`](../proofreading-web/README.md),
[`proofreading-web/ROADMAP.md`](../proofreading-web/ROADMAP.md),
[`proofreading-web/docs/STRIPE.md`](../proofreading-web/docs/STRIPE.md),
and the security notes in [`CLAUDE.md`](../CLAUDE.md).

## 2. Printer Proofreading (desktop) — `PROOFREADING/`

**Purpose**: batch QA of printed proofs against original designs on a
workstation (Windows-first).

**Current version**: `proofreading_v3.py` (Tkinter). Older versions are
archived in `PROOFREADING/legacy/`.

**Key mechanics**:

- Files from an "Original" folder and a "Printer" folder are matched by the
  **first 8 characters** of their filenames. All files from both folders are
  processed; printer files without an original counterpart are listed too.
- Automatic **content detection** (threshold + edge analysis) crops margins,
  bleeds and crop marks before comparison; manual crop adjustment available.
- **SSIM scoring** with a configurable threshold, side-by-side manual review
  (approve/reject), multi-page navigation, CSV export.

**Build**: `pyinstaller PrinterProofreading_v3.spec` produces a single-file
Windows executable.

**Dependencies** (root `requirements.txt`): PyMuPDF, Pillow, numpy,
scikit-image, scipy, tkinterdnd2.

## 3. Artwork Validator (desktop) — `artwork_validator/`

**Purpose**: validate lithographic artwork PDFs against an Excel brief
(L'Oréal workflow), brand-aware (Maybelline New York, ESSIE).

**Architecture** (see [`artwork_validator/README.md`](../artwork_validator/README.md), French):

- `core/excel_processor.py` — brief loading with per-brand required/optional
  column contracts (note: the required column `DECRIPTION` is intentionally
  misspelled to match real brief files) and type coercion.
- `core/validator.py` — **legacy engine** (default): uppercase substring
  matching, WTP ↔ WATERPROOF equivalence, 4-DIGITS (Walmart) validation,
  CUBBY matrix layouts (`10F2T` parsing, UPC-sequence sorting, tier
  rollover), MIXED facings, FRAME/SPACE_SAVER handling.
- `core/enhanced_validator.py` — **enhanced engine** (toggleable):
  token-based sequential matching with progressive token consumption.
- `core/pdf_processor.py` — PyMuPDF text extraction and rendering; falls
  back to PaddleOCR (`core/ocr_processor.py`, optional dependency) when a
  PDF yields fewer than 50 characters.
- `core/report_generator.py` — 8-sheet Excel report (session summary, global
  stats, per-litho summary, full details, pending/rejected, PDF analysis,
  validation statuses).
- `core/basecamp/` — optional Selenium automation posting approvals to
  Basecamp (Edge WebDriver; desktop-only by design).
- `ui/` — PyQt6 interface; `utils/session_manager.py` — JSON session files.

## 4. Artwork Validator (web) — `artwork-validator-web/`

**Purpose**: browser version of the desktop validator for easy internal
sharing — a **single self-contained HTML file**, fully client-side.

**Key points**:

- `src/core/` is a 1:1 TypeScript port of `artwork_validator/core/`
  (excluding Basecamp and OCR). Cross-language parity is enforced by test
  vectors generated from the real Python engines
  (`artwork_validator/scripts/gen_parity_vectors.py` →
  `tests/core/parity.test.ts`). Two known Python quirks are reproduced on
  purpose and pinned by tests (see the project README).
- PDF handling uses pdf.js with an inlined worker (works under `file://`);
  Excel I/O uses exceljs; sessions autosave to localStorage and
  export/import as JSON files compatible with desktop sessions.
- The OCR fallback is replaced by a "manual review required" flag plus a
  `TextRecoveryProvider` extension point for a future AI/OCR API.

Full details: [`artwork-validator-web/README.md`](../artwork-validator-web/README.md).

## Cross-project conventions

- **UI language**: French (both web apps and the desktop tools target
  French-speaking users). Code and documentation: English (legacy Python
  code contains French comments).
- **Filename-code matching**: Printer Proofreading uses fixed 8-character
  prefixes; Artwork Validator uses per-brand patterns (`YCA#####` for MNY,
  `GAMME_S##_#_#` for ESSIE).
- **Windows-first desktop tools**: paths, executables and the Basecamp/Edge
  integration assume Windows; the web apps are cross-platform.

## Repository hygiene

- Runtime artifacts are not tracked: logs, `__pycache__`,
  `artwork_validator/app_settings.json` (contains user-local paths),
  `artwork-validator-web/dist/` and `node_modules/` are all gitignored.
- Test fixtures under `artwork-validator-web/tests/fixtures/` are tracked
  (including small PDFs, exempted from the global `*.pdf` ignore).
