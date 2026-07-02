# Contributing

Thank you for your interest in contributing! This repository is a monorepo —
see [README.md](README.md) for the project map. These guidelines apply to all
projects; project-specific commands are listed below.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and
inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title and the **project concerned** (`proofreading-web`,
     `PROOFREADING`, `artwork_validator`, `artwork-validator-web`)
   - Steps to reproduce, expected vs actual behavior
   - Your environment (OS, Python/Node version, browser for the web apps)
   - Screenshots and anonymized sample files if applicable

### Suggesting Features

Create an issue describing the feature, the use case it solves, and (optional)
a proposed implementation or mockups.

## Development Setup

### Python projects (`PROOFREADING/`, `artwork_validator/`)

```bash
python -m venv venv
source venv/bin/activate            # or venv\Scripts\activate on Windows

# Desktop proofreading tool
pip install -r requirements.txt
cd PROOFREADING && python proofreading_v3.py

# Artwork validator (desktop)
pip install PyQt6 pandas openpyxl PyMuPDF
cd artwork_validator && python main.py

# Formatting / linting
pip install black flake8
black <changed files> && flake8 <changed files>
```

### proofreading-web (Next.js + FastAPI)

```bash
cd proofreading-web
npm install
npm run dev                          # frontend on :3000
npm run lint && npm run build        # must pass before a PR

cd backend
pip install -r requirements.txt
python main.py                       # API on :8000
```

### artwork-validator-web (Vite + React + TypeScript)

```bash
cd artwork-validator-web
npm install
npm run dev                          # dev server
npm test                             # vitest — unit + Python-parity suite
npm run build                        # must emit a working single dist/index.html
```

**Parity rule**: `src/core/` must stay behaviorally identical to
`artwork_validator/core/`. If you change validation logic on either side,
regenerate the vectors and keep the suite green:

```bash
python3 artwork_validator/scripts/gen_parity_vectors.py
cd artwork-validator-web && npm test
```

Comments marked `PARITY:` flag Python quirks reproduced on purpose — do not
"fix" them unilaterally on the web side.

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes (follow the existing code style of the project you touch)
3. Test: run the relevant app + test suite from the setup section above
4. Commit using conventional commits and open a Pull Request

### Commit Message Format

```
type(scope): description
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
Examples:

```
feat(artwork-web): add ESSIE strip-type badge to overview cards
fix(pdf): handle corrupted PDF files gracefully
docs(readme): update installation instructions
```

## Code Style Guidelines

### Python

- PEP 8, type hints where helpful, max line length 100
- Docstrings for public methods; comment the "why", not the "what"

### TypeScript / React

- Strict TypeScript (`tsc -b` must pass with no errors)
- Functional components, hooks, Zustand for shared state
- Tailwind for styling; French copy in the UI, English in code

## Testing Checklists

### Desktop proofreading tool

- [ ] Application starts without errors; folder selection works
- [ ] Multi-page PDFs navigate properly; content detection overlay shows
- [ ] Validation updates the list; CSV export contains correct data

### artwork-validator-web

- [ ] `npm test` green (including parity suite)
- [ ] `npm run build` then open `dist/index.html` via `file://` — loads with
      no console errors
- [ ] Optional full E2E: `python3 scripts/gen_fixtures.py && node scripts/e2e.mjs`

### proofreading-web

- [ ] `npm run lint` and `npm run build` pass
- [ ] Auth, compare and quota flows still work locally

## Documentation

- Update `README.md` (root or project) for user-facing changes
- Update `docs/DOCUMENTATION.md` for cross-project technical changes

## Questions?

Open an issue or start a discussion. Thank you for contributing!
