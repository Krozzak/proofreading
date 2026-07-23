# Artwork types — design document

> Status: **planned** (v1.2 target). Nothing in this document is implemented
> yet; it defines the model so new code converges on it. Written 2026-07.

## Context

Today the app validates **one artwork type**: **bullnose graphics** — shelf
lithos driven by an Excel brief with UPC rows: shade name/number presence,
4-DIGITS (Walmart), UPC sequences, CUBBY matrices, MIXED facings,
FRAME/SPACE_SAVER rows. The whole pipeline (brief columns → rule engines →
results grid) silently assumes this type.

Coming next, at least: **hotspot visuals** — promotional displays with **no
UPC sequence**: mostly images, free text placement, claims. What needs
checking there is different: presence and exact wording of text blocks,
typography/spelling, image presence/placement, dimensions. Other types will
follow (totems, tester units, vitrine elements…).

The goal: the app must **detect the artwork type** (or let the user pick it)
and run **the checks that belong to that type**, without hardcoding each new
type as code — same philosophy as brands (JSON definitions, wizard, AI
generation).

## Guiding principles

1. **Type × brand are orthogonal.** A brand (MNY, ESSIE, NYX…) can produce
   several artwork types. The brand keeps owning filename rules and brief
   columns; the type owns *which checks run*.
2. **The parity core stays untouched.** `src/core/` mirrors
   `artwork_validator/core/` (Python). The existing legacy/enhanced engines
   become *one check implementation* ("shade grid") that the BULLNOSE type
   references — they are not modified.
3. **Types are JSON definitions**, exactly like `BrandDefinition`: built-ins
   shipped in code, custom ones in localStorage, importable/exportable,
   AI-generatable via the companion.
4. **Explicit beats inferred.** Auto-detection is a convenience with a
   confidence score; the user can always override, and the report records
   which type was used.

## Data model (schema v1 proposal)

```ts
// src/core/artworkTypes/typeSchema.ts (future)
export interface ArtworkTypeDefinition {
  schema_version: 1
  type_code: string            // 'BULLNOSE' | 'HOTSPOT' | custom
  display_name: string         // 'Bullnose graphics', 'Visuel hotspot'…
  description?: string

  /** Signals used by auto-detection, all optional. */
  detection: {
    /** Case-insensitive regexes matched against the PDF filename. */
    filename_patterns?: string[]
    /** Type wins if ANY of these brief columns is present… */
    brief_columns_any?: string[]
    /** …and loses if ANY of these is present (e.g. HOTSPOT has no 'UPC SEQUENCE'). */
    brief_columns_none?: string[]
    /** Uppercase markers searched in the extracted PDF text. */
    text_markers?: string[]
    /** Tie-breaker; higher wins. Built-ins use 0. */
    priority?: number
  }

  /** Ordered checks to run for this type. */
  checks: CheckSpec[]
}

export type CheckSpec =
  /** The existing legacy/enhanced engines (bullnose only). */
  | { kind: 'shade_grid'; params?: { allow_enhanced?: boolean } }
  /** Every value of a brief column must appear in the extracted text. */
  | { kind: 'text_presence'; params: { columns: string[]; whitespace_insensitive?: boolean } }
  /** Spelling/typography pass on the extracted text (dictionary + AI). */
  | { kind: 'typography'; params?: { languages?: string[]; ai_assisted?: boolean } }
  /** Page size vs expected size (reuses the v1.1 dimensions feature). */
  | { kind: 'dimensions'; params?: { expected_from_brief_columns?: [string, string] } }
  /** Free visual check delegated to the AI panel (images, placement, logos). */
  | { kind: 'ai_visual'; params: { instructions: string } }
```

### Built-in definitions (illustrative)

```jsonc
// BULLNOSE — current behavior, expressed in the new model
{
  "schema_version": 1,
  "type_code": "BULLNOSE",
  "display_name": "Bullnose graphics",
  "detection": {
    "brief_columns_any": ["UPC SEQUENCE", "PRODUCT FACING SL"],
    "priority": 0
  },
  "checks": [
    { "kind": "shade_grid" },
    { "kind": "dimensions" }
  ]
}

// HOTSPOT — first new type
{
  "schema_version": 1,
  "type_code": "HOTSPOT",
  "display_name": "Visuel hotspot",
  "detection": {
    "filename_patterns": ["HOTSPOT", "\\bHS\\b"],
    "brief_columns_none": ["UPC SEQUENCE"],
    "brief_columns_any": ["TEXTE 1", "CLAIM"],
    "priority": 0
  },
  "checks": [
    { "kind": "text_presence", "params": { "columns": ["CLAIM", "TEXTE 1", "TEXTE 2"], "whitespace_insensitive": true } },
    { "kind": "typography", "params": { "languages": ["fr", "en"], "ai_assisted": true } },
    { "kind": "dimensions" },
    { "kind": "ai_visual", "params": { "instructions": "Vérifier la présence du logo marque, la lisibilité des textes et l'absence d'élément coupé par le bord." } }
  ]
}
```

The HOTSPOT brief format (column names above) is a placeholder — it must be
finalized with real hotspot briefs before implementation.

## Detection pipeline

Resolution order for each litho (first hit wins):

1. **User override** — a type selector next to the brand selector; a manual
   choice is stored in the session per litho and always wins.
2. **Brief columns** — `brief_columns_any` / `brief_columns_none` against the
   loaded sheet headers (cheap, reliable: a brief with `UPC SEQUENCE` is
   bullnose; without it and with `CLAIM` it is hotspot).
3. **Filename patterns**, then **text markers** on the extracted text.
4. **Fallback** — `BULLNOSE` (today's behavior), flagged in the UI as
   "type supposé" so the user confirms.

The detected/selected type and its confidence appear as a badge in the
validation view (like the 📐 size badge) and in the Excel report.

## Check runner

A thin dispatcher replaces the current direct call to `LithoValidator`:

```
runChecks(entry, excelData, typeDef) →
  typeDef.checks.map(spec => CHECK_REGISTRY[spec.kind](entry, excelData, spec.params))
```

- `shade_grid` wraps the existing `validateLitho()` unchanged — the results
  grid renders exactly as today.
- Each check returns a common envelope `{kind, status: 'pass'|'fail'|'manual',
  rows?, notes?}` so the UI can stack heterogeneous check results in the
  right-hand panel and the report can aggregate them.
- `typography` and `ai_visual` produce `manual`-or-AI results: without an API
  key they render as guided manual checklists (and the companion GPT can be
  delegated the check — see `COMPAGNON_PROMPT.md`, Mission 4).

## Phasing

| Phase | Content | Size |
|---|---|---|
| **1 — Scaffold** | `typeSchema.ts` + built-in BULLNOSE definition + type badge + manual selector (no behavior change: only BULLNOSE exists) | S |
| **2 — Hotspot MVP** | Finalize hotspot brief format with real briefs; `text_presence` + `dimensions` checks; HOTSPOT built-in; detection via brief columns | M |
| **3 — Assisted checks** | `typography` (dictionary + AI) and `ai_visual` checks wired to the existing AI layer; manual-checklist fallback | M |
| **4 — Full detection & custom types** | Filename/text-marker detection, per-litho override in session, type wizard + JSON import/export + companion generation (same UX as brands) | L |

## Open questions (to settle before Phase 2)

- Real hotspot brief: exact column names, one row per text block or one row
  per hotspot?
- Is the artwork type per **file**, per **litho code**, or per **brief
  sheet**? (Current assumption: per litho, overridable.)
- Typography check scope: strict spelling only, or also casing/accent rules
  per brand? Which dictionaries for FR/EN cosmetics vocabulary?
- Should the Excel report gain one sheet per check kind, or a single
  "checks" sheet with one row per (litho, check)?
