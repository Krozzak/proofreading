# Artwork Validator — Web

A **100% client-side** web port of the L'Oréal Litho Validator desktop app
(`../artwork_validator/`, PyQt6). It validates lithographic artwork PDFs
against an Excel brief: shade names/numbers, 4-DIGITS codes (Walmart), CUBBY
matrix layouts, MIXED facings, FRAME/SPACE_SAVER rows — with per-brand rules
(Maybelline New York, ESSIE).

The build produces **one self-contained HTML file** that runs entirely in the
browser: no server, no Python, no network calls. PDFs and Excel files never
leave the user's machine.

> The UI is intentionally in **French** (it targets French-speaking
> colleagues); code and docs are in English.

## Quick start

```bash
npm install
npm run dev        # dev server on http://localhost:5173
npm test           # vitest unit + parity suite
npm run build      # emits dist/index.html (single ~3 MB file)
```

Open `dist/index.html` directly in Chrome/Edge (double-click works — the app
is fully functional under `file://`).

## Sharing at work

`dist/index.html` is the whole application:

- put it on a network share, or
- send it by email (zip it first — some mail gateways block bare .html), or
- host it on any static server / intranet page.

No installation, no admin rights, no dependencies required on the target
machine. Recent Chrome or Edge recommended.

## How it works

| Layer | Location | Notes |
|---|---|---|
| Core validation logic | `src/core/` | Pure TypeScript, zero DOM/React imports — a 1:1 port of the Python `core/` modules, liftable as-is into another app (e.g. ProofsLab) |
| PDF engine | `src/lib/pdfEngine.ts` | pdf.js with an **inlined worker** (Blob URL, works offline/`file://`), text extraction + canvas rendering |
| Excel I/O | `src/lib/excelIO.ts` | exceljs: reads the brief with pandas-like semantics, writes the 8-sheet styled report |
| Sessions | `src/lib/sessionStore.ts` | Autosaved to localStorage; JSON export/import **compatible with desktop session files** |
| State | `src/state/appStore.ts` | Zustand |
| UI | `src/ui/` | React + Tailwind v4, French |

### Validation engines

Both desktop engines are ported and toggleable in the UI:

- **Legacy** (default): uppercase substring matching over the whole document
  text, WTP ↔ WATERPROOF equivalence, CUBBY dimension parsing (`10F2T`), UPC
  sequence sorting, matrix layout with tier rollover.
- **Enhanced**: token-based sequential matching with progressive token
  consumption (1:1 matching), orphan-token stats.

Parity with Python is enforced by tests: `artwork_validator/scripts/gen_parity_vectors.py`
runs the *real* Python engines on synthetic briefs and dumps expected outputs
to `tests/fixtures/parity/vectors.json`; `tests/core/parity.test.ts` asserts
deep equality. Two known Python quirks are **reproduced on purpose** (and
pinned by tests, marked `PARITY:` in the code):

1. `EnhancedValidator._check_duplicate_allowance` receives padded empty rows,
   so every row with index ≥ 2 is treated as a legitimate duplicate.
2. `validate_enhanced` reads `last_token_position` at the wrong dict level, so
   the cross-row search position never advances.

### OCR / AI extension point

The desktop app fell back to PaddleOCR when a PDF had fewer than 50
extractable characters. The web app **flags** those PDFs ("⚠️ Revue manuelle
requise") instead, and exposes a `TextRecoveryProvider` interface
(`src/core/pdfCatalog.ts`) where a future AI/OCR API can plug in.

### Known upstream quirks (inherited by design)

- The required Excel column **`DECRIPTION` is intentionally misspelled** —
  real brief files use that header.
- Numeric Excel columns lose leading zeros (`0450` → `450`), exactly like the
  desktop app (pandas numeric coercion).
- pdf.js and PyMuPDF can extract text in slightly different order/spacing;
  the legacy engine (substring over the whole document) is robust to this,
  the Enhanced engine may differ marginally from desktop on complex PDFs.

## End-to-end check

```bash
npm run build
python3 scripts/gen_fixtures.py       # writes tests/fixtures/e2e/ (brief + PDFs)
node scripts/e2e.mjs                  # drives the file:// build in Chromium
```

The E2E covers: ingestion (valid/invalid filenames), Excel column validation,
standard/CUBBY/MIXED/scanned lithos, approve/reject with auto-advance, report
export (8 sheets), session export, and brand switching.

## Sessions

- Autosaved to localStorage on every change (a few KB — statuses + comments).
- Files can't persist across reloads (browser security): after a reload the
  app shows the remembered folder/Excel names and asks to re-drop them.
- **Desktop compatibility**: session `.json` files from the PyQt6 app import
  cleanly; exports use the same schema (`session_version: "2.0-web"`, and the
  web schema also keeps `brand_code`, which the desktop migration dropped).
