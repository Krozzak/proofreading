# ProofsLab Monorepo

Tools for validating printed artwork against reference material — from PDF
proof comparison (SSIM) to brief-driven artwork validation.

![Python](https://img.shields.io/badge/python-3.8+-green)
![TypeScript](https://img.shields.io/badge/typescript-5-blue)
![License](https://img.shields.io/badge/license-MIT-orange)

## Projects

| Project | Directory | Stack | Status |
|---|---|---|---|
| **ProofsLab** (web) | [`proofreading-web/`](proofreading-web/) | Next.js 16 + FastAPI (Cloud Run), Firebase, Stripe | Production — [proofslab.com](https://proofslab.com) |
| **Printer Proofreading** (desktop) | [`PROOFREADING/`](PROOFREADING/) | Python + Tkinter | Stable (v3) |
| **Artwork Validator** (desktop) | [`artwork_validator/`](artwork_validator/) | Python + PyQt6 | Stable (v2.1) |
| **Artwork Validator** (web) | [`artwork-validator-web/`](artwork-validator-web/) | Vite + React + TypeScript | New — single-file HTML build |

### ProofsLab — `proofreading-web/`

SaaS web app that compares two PDFs (original design vs printer proof) using
SSIM scoring, with AI-assisted analysis, user accounts, quotas and
subscriptions. Next.js frontend on Vercel, FastAPI backend on Google Cloud
Run. See [`proofreading-web/README.md`](proofreading-web/README.md).

```bash
cd proofreading-web && npm install && npm run dev     # frontend :3000
cd proofreading-web/backend && pip install -r requirements.txt && python main.py  # API :8000
```

### Printer Proofreading — `PROOFREADING/`

Desktop tool for print QA teams: compares folders of original vs printer
PDFs matched by an 8-character filename code, computes SSIM similarity with
automatic content detection (ignoring margins/crop marks), side-by-side
review, CSV export.

```bash
pip install -r requirements.txt
cd PROOFREADING && python proofreading_v3.py
# Build a Windows executable:
pyinstaller PrinterProofreading_v3.spec
```

Earlier versions (`proofreading.py`, `proofreading_v2.py`) are kept in
[`PROOFREADING/legacy/`](PROOFREADING/legacy/).

### Artwork Validator (desktop) — `artwork_validator/`

PyQt6 app that validates lithographic artwork PDFs against an Excel brief:
shade names/numbers, Walmart 4-DIGITS codes, CUBBY matrix layouts, MIXED
facings, with per-brand rules (Maybelline New York, ESSIE) and a multi-sheet
Excel report. Includes an optional Selenium-based Basecamp integration and an
optional PaddleOCR fallback for scanned PDFs.
See [`artwork_validator/README.md`](artwork_validator/README.md) (French).

```bash
cd artwork_validator
pip install PyQt6 pandas openpyxl PyMuPDF   # + selenium / paddleocr for optional features
python main.py
```

### Artwork Validator (web) — `artwork-validator-web/`

Browser port of the desktop validator: same validation logic (ported 1:1 to
TypeScript with a Python↔TS parity test suite), no server required. The
build emits **one self-contained HTML file** that runs offline via `file://`
— ideal for sharing internally. The heavy integrations were deliberately left
out (Basecamp automation) or replaced by an extension point (OCR → future AI
API). See [`artwork-validator-web/README.md`](artwork-validator-web/README.md).

```bash
cd artwork-validator-web
npm install
npm test              # unit + Python-parity suite
npm run build         # → dist/index.html (share this file)
```

## Repository layout

```
├── proofreading-web/        # ProofsLab SaaS (Next.js + FastAPI + Firebase + Stripe)
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Client utilities (auth, pdf, store)
│   └── backend/             # FastAPI service (Cloud Run)
├── PROOFREADING/            # Desktop SSIM proofreading tool (Tkinter)
│   ├── proofreading_v3.py   # Current version
│   ├── PrinterProofreading_v3.spec
│   └── legacy/              # v1/v2 + old spec
├── artwork_validator/       # Desktop litho validator (PyQt6)
│   ├── core/                # Validation engines, Excel/PDF processing, brand configs
│   ├── ui/                  # PyQt6 interface
│   ├── utils/               # Session manager, styles
│   └── scripts/             # incl. gen_parity_vectors.py (web-port parity)
├── artwork-validator-web/   # Web litho validator (Vite + React + TS, single-file build)
│   ├── src/core/            # 1:1 TypeScript port of artwork_validator/core
│   ├── src/lib/             # pdf.js engine, exceljs I/O, session store
│   ├── src/ui/              # French UI
│   └── tests/               # vitest + Python-parity vectors + E2E fixtures
├── docs/                    # Repository documentation
└── requirements.txt         # Desktop proofreading tool dependencies
```

## Documentation

- [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md) — technical overview of the monorepo
- [`CLAUDE.md`](CLAUDE.md) — AI-assistant working notes for this codebase
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines

## License

MIT — see [LICENSE](LICENSE).
