# Artwork Validator — Web

A **100% client-side** web port of the L'Oréal desktop litho validator app
(`../artwork_validator/`, PyQt6). It validates lithographic artwork PDFs
against an Excel brief: shade names/numbers, 4-DIGITS codes (Walmart), CUBBY
matrix layouts, MIXED facings, FRAME/SPACE_SAVER rows — with per-brand rules
(Maybelline New York and ESSIE built in, any other brand addable without code).

The build produces **one self-contained HTML file** that runs entirely in the
browser: no server, no Python, no network calls. PDFs and Excel files never
leave the user's machine.

> The UI is intentionally in **French** (it targets French-speaking
> colleagues); code and docs are in English.

## Using the app (no npm / Node / install required)

The application is the single HTML file **[`release/ArtworkValidator.html`](release/ArtworkValidator.html)**,
committed here so locked-down work machines can get it straight from GitHub:

1. Open the file on GitHub → click the **⬇ Download raw file** button
   (top-right of the file view).
2. Double-click the downloaded `ArtworkValidator.html` — it opens in
   Chrome/Edge and works fully offline. No admin rights, no installation.

npm is only needed to **develop** the app (below). After a code change, run
`npm run build` and refresh `release/ArtworkValidator.html` with the new
`dist/index.html`.

## Development quick start

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

The official internal distribution channel is a **SharePoint direct-download
share link** (share link + `?download=1`, or `&download=1` if the URL already
has a query string) embedded in the GPT companion prompt
(`docs/COMPAGNON_PROMPT.md`) — the companion hands the link to anyone who
needs the app. After each release, replace the file in SharePoint
("Replace" keeps the link stable) so the companion always serves the latest
version without touching the prompt.

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

### Dynamic brands (v1.1)

Brands are **JSON definitions**, not code (`src/core/brandConfigs/brandSchema.ts`):
brand code/name, a filename rule (`prefix` = literal + N digits, or `regex`
with three patterns), the brief columns (name/required/type) and validation
flags. MNY and ESSIE are built-in definitions; users add new brands (NYX,
L'Oréal Paris, Garnier…) three ways:

1. **Wizard** (Paramètres → Marques → "+ Nouvelle marque"): guided steps with
   a live tester — paste real filenames, see ✓/✗ and the extracted code.
2. **JSON import**: drop a `brand_X.json` produced by a colleague or by the
   internal GPT companion (prompt in `docs/COMPAGNON_PROMPT.md`).
3. **AI generation**: describe the brand in the wizard; the configured AI
   model produces the definition (validated by the same schema).

Custom brands persist in localStorage, export/import as JSON, and are embedded
in exported sessions so they travel with the work. Each brand has a
downloadable **Excel brief template** (BRIEF sheet with the exact headers +
French INSTRUCTIONS sheet) — Paramètres → Marques → "📄 Template Excel".

### AI validation (v1.1, optional)

Paramètres → Intelligence artificielle configures a **provider-agnostic**
multimodal API (Anthropic Messages or OpenAI-compatible chat/completions —
base URL, key and model are stored in the browser only; Anthropic works
directly from the browser via `anthropic-dangerous-direct-browser-access`).
Once configured, each litho gets an "🤖 Analyse IA" panel: the model receives
the page images + the brief rows + the brand rules and returns per-row
verdicts (same shape as the rule engines) plus an answer to an optional
free-form check ("le logo Walmart est-il présent ?"). This is the
recommended path for scanned/vectorized PDFs and out-of-format checks — more
capable than the rule engines, but each call costs API credits.

### OCR / AI extension point

The desktop app fell back to PaddleOCR when a PDF had fewer than 50
extractable characters. The web app **flags** those PDFs ("⚠️ Revue manuelle
requise") instead — the AI panel is suggested automatically for them — and
exposes a `TextRecoveryProvider` interface (`src/core/pdfCatalog.ts`) where a
dedicated OCR provider can still plug in.

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

## Vision & roadmap

**Target state**: this app is meant to be embedded as an **application inside
the internal L'Oréal GPT** — our validation interface for the visual work, the
GPT chat for questions, guidance and brand creation. The current standalone
single-file build exists to **prove the concept** internally first.

The architecture already anticipates that integration:

- the validation UI is self-contained and server-free (embeds anywhere);
- the AI layer is provider-agnostic (`src/lib/ai/client.ts`) — swapping the
  direct API calls for the host GPT's runtime is a single adapter;
- the free-form check channel (AiPanel question) and the brand-JSON contract
  (`BrandDefinition`) are exactly the interfaces a host chat would drive;
- `docs/COMPAGNON_PROMPT.md` already defines the GPT-side behavior — today as
  a copy-paste prompt, tomorrow as the embedded app's system instructions.

**Artwork types**: today the app validates one artwork type (bullnose
graphics — UPC-driven shelf lithos). Support for other types (hotspot
visuals: no UPC sequence, text/typography/image checks) is designed in
[`docs/ARTWORK_TYPES.md`](docs/ARTWORK_TYPES.md) — JSON type definitions with
auto-detection and a per-type check registry, mirroring the dynamic-brands
approach.

Separately, a ProofsLab integration (dedicated page on proofslab.com) is
planned as Phase 2 of the monorepo roadmap.

## Sessions

- Autosaved to localStorage on every change (a few KB — statuses + comments).
- Files can't persist across reloads (browser security): after a reload the
  app shows the remembered folder/Excel names and asks to re-drop them.
- **Desktop compatibility**: session `.json` files from the PyQt6 app import
  cleanly; exports use the same schema (`session_version: "2.0-web"`, and the
  web schema also keeps `brand_code`, which the desktop migration dropped).
