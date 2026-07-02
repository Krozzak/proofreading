# Litho Validator - Project Roadmap

**Application**: L'Oréal Litho Validator
**Current Version**: v2.1.0 (PyQt6 Desktop) | v1.0.0-alpha (Web)
**Last Updated**: 2025-11-24
**Status**: Desktop production-ready, Web in development

---

## 📊 Current State

### ✅ Desktop App (PyQt6) - v2.1.0 Production Ready

**Core Features**:
- ✅ Multi-brand support (MNY, ESSIE) with extensible pattern
- ✅ PDF/Excel automatic matching and validation
- ✅ Special type handling (CUBBY, MIXED, SPACE_SAVER, FRAME)
- ✅ YCA code extraction and validation
- ✅ Shade validation with equivalences
- ✅ BaseCamp integration (v2.0 modular - 5 file matching strategies)
- ✅ Session management with auto-recovery
- ✅ PDF viewer with zoom/annotation
- ✅ Real-time progress tracking
- ✅ Error assistance with suggestions
- ✅ Multiple view modes (overview, cards, table)
- ✅ Excel report generation

**Architecture**:
- ✅ Modular core/ui separation (v2.0 refactoring complete)
- ✅ Brand configuration system (Abstract Factory pattern)
- ✅ PyQt6 signals/slots architecture
- ✅ Comprehensive logging and error handling

### 🚧 Web App (React + FastAPI) - v1.0.0-alpha In Development

**Location**: `litho_validator_prod/`

**Completed**:
- ✅ Backend FastAPI with all routes (`backend/`)
- ✅ Core validation modules copied from desktop (`backend/core/`)
- ✅ React + TypeScript + Tailwind frontend (`frontend/`)
- ✅ L'Oréal design system (colors, components)
- ✅ Dashboard view (stats cards, quick actions)
- ✅ Basic layout (sidebar, header)
- ✅ API client with React Query

**In Progress** (from PLAN_SUITE.md):
- 🚧 Validation View (PDF viewer, table, error panel)
- 🚧 Session manager persistent (critical)
- 🚧 Upload workflow (PDF + Excel)
- 🚧 Batch validation

---

## 🎯 Roadmap Strategy

### Philosophy
- **No unit tests** - Manual testing with real use cases only
- **Keep it simple** - Consolidate redundant views, focus on UX
- **Iterative approach** - Small improvements, test frequently
- **Code quality** - Review best practices, clean code
- **Web migration** - Desktop → Web transition (reuse existing web foundation)

---

## Phase 1: Desktop App UX Improvements (⏳ CURRENT - 2-3 weeks)

**Priority**: 🟠 High
**Goal**: Polish desktop app UX before web migration

### 1.1 Consolidate Views ✅
**Status**: ✅ COMPLETED (2025-11-24)
**Effort**: 6h (actual)
**Feature Folder**: `features/phase1-1-consolidate-overview-cards/`

**Problem**: Overview and Cards views were redundant

**Solution Implemented**: Merged into single "Overview" with view toggle
- ✅ Add toggle button in Overview: List view / Card view
- ✅ Integrate card visualization into Overview (QGridLayout with PDFCardWidget)
- ✅ Remove separate Cards view (deprecated)
- ✅ Final views: **Overview**, **Validation**, **Settings**

**Updated Menu Structure**:
```
Menu Bar:
├── Fichier (File)
├── Sessions
├── Export
├── Affichage (View)  → Top band view switcher REMOVED
│   ├── Overview (Ctrl+1)
│   ├── Validation (Ctrl+2)
│   └── Paramètres (Ctrl+3) ← Updated from Ctrl+4
└── Aide (Help)
```

**Implementation Details**:
- **Toggle UI**: QPushButton toggle bar (📋 Liste | 🎴 Grille) with QStackedWidget
- **List Mode**: Existing LithoRowCard layout (unchanged)
- **Grid Mode**: Responsive QGridLayout (2-4 columns) with PDFCardWidget
- **Filters**: Search and filters work in both modes
- **Signals**: `view_mode_changed = pyqtSignal(str)` for extensibility

**Deliverables**:
- ✅ `ui/overview_view.py` - Integrated list/card toggle (473 lines)
- ✅ `ui/main_window.py` - Updated menu structure (simplified to 3 views)
- ✅ `ui/cards_view.py.deprecated` - Deprecated (361 lines)
- ✅ `ui/view_mode_switcher.py.deprecated` - Deprecated (90 lines)
- ✅ `features/phase1-1-consolidate-overview-cards/PLAN.md` - Implementation plan
- ✅ `features/phase1-1-consolidate-overview-cards/IMPLEMENTATION_LOG.md` - Technical log
- ✅ `features/phase1-1-consolidate-overview-cards/TEST_CHECKLIST.md` - Manual test checklist

**User Feedback**:
- ✅ Grid view displays correctly
- ✅ Toggle works between list/grid
- ✅ All functionality working
- ⚠️ Minor issues noted (blurry thumbnails, loading time, max columns) - non-blocking for MVP

---

### 1.2 Simplify Error Templates ✅

**Status**: ✅ COMPLETED (2025-11-25)
**Effort**: 1h (actual)
**Feature Folder**: `features/phase1-2-simplify-error-templates/`

**Problem**: Initial assessment showed file was already clean (14 templates, 529 lines)

- ROADMAP description was outdated (claimed "30+ templates with duplicates")
- Analysis revealed only 4 templates could be safely removed

**Solution Implemented**: Minor cleanup - removed 4 undetectable templates

- ✅ **Removed templates**:
  - `poor_quality` - Visual quality (not auto-detectable)
  - `color_mismatch` - Brand colors (validation not implemented)
  - `pdf_extraction_failed` - Internal error (not user-facing)
  - `excel_data_missing` - Cannot detect reliably
- ✅ **Removed categories**: QUALITY, TECHNICAL (empty after template removal)

**Results**:

- **Templates**: 14 → 10 (-4 templates, -29%)
- **Categories**: 6 → 4 (removed QUALITY, TECHNICAL)
- **File size**: 529 lines → 442 lines (-87 lines, -16%)

**Templates Remaining (10)**:

- Shade Validation (4): name/number mismatch/missing
- Walmart Specific (2): 4 DIGITS missing/invalid
- Layout (3): facing, mixed facings, space saver
- Content (2): wrong product, missing info

**Deliverables**:

- ✅ `core/error_templates.py` - Cleaned (442 lines, 10 templates)
- ✅ `features/phase1-2-simplify-error-templates/ASSESSMENT.md` - Analysis
- ✅ `features/phase1-2-simplify-error-templates/PLAN.md` - Implementation plan
- ✅ `features/phase1-2-simplify-error-templates/IMPLEMENTATION_LOG.md` - Technical log

---

### 1.3 Modern UI Polish ✅
**Status**: ✅ COMPLETED (2025-11-25)
**Effort**: 1h 15min (actual) vs 8-10h (estimated)
**Feature Folder**: `features/phase1-3-modern-ui-polish/`

**Solution Implemented**: Modernized layout with reduced clutter

**Completed**:
- ✅ **Overview improvements**:
  - Modern card design with shadows (QGraphicsDropShadowEffect)
  - Hover states (shadow increases on hover)
  - Better spacing (8px grid: 8, 12, 16, 24px)
  - Cleaner status badges (48px, rounded, shadowed)
- ✅ **Validation view cleanup**:
  - Reduced Quick Chat suggestions (top 3 only, was 5-6 before)
  - Kept search panel (NOT redundant - searches all tabs vs table search)
  - Consistent 8px grid spacing
  - Cleaner layout achieved
- ✅ **Error assistance polish**:
  - Modern error cards with shadows
  - Better spacing and visual hierarchy
  - Suggestions already limited to top 3
- ✅ **General polish**:
  - Icons already excellent (255 emoji uses across 21 files)
  - Consistent spacing (8px grid system documented)
  - Better contrast and readability
  - Modern button styling (6px radius, 32px min-height)

**Decision Made**:
- ✅ PyQt6 polish successful (shadows work perfectly with QGraphicsDropShadowEffect)
- No need to accelerate web migration yet
- Desktop app now modern and polished

**Deliverables**:
- ✅ `ui/litho_row_card.py` - Modern shadows, hover effects, better badges
- ✅ `ui/pdf_card_widget.py` - Modern shadows, hover effects
- ✅ `ui/overview_view.py` - 8px grid spacing
- ✅ `ui/validation_panel.py` - Reduced suggestions (top 3), 8px grid
- ✅ `ui/error_assistance_panel.py` - Modern shadows, 8px grid
- ✅ `utils/styles.py` - Design system (SPACING, SHADOWS), modern buttons
- ✅ `features/phase1-3-modern-ui-polish/PLAN.md` - Implementation plan
- ✅ `features/phase1-3-modern-ui-polish/IMPLEMENTATION_LOG.md` - Technical log
- ✅ `features/phase1-3-modern-ui-polish/TEST_CHECKLIST.md` - Manual test checklist

**User Feedback**: ⏳ Pending testing

---

### 1.4 UX Analysis & Recommendations 🟢
**Status**: Not started
**Effort**: 2-4h

**Goal**: Document UX pain points before web migration

**Tasks**:
- [ ] User testing session (manual walkthrough)
- [ ] List UX pain points (navigation, clicks, readability)
- [ ] Prioritize improvements (quick wins vs major changes)
- [ ] Decision: Continue PyQt6 polish OR migrate to web

**Deliverables**:
- [ ] `UX_ANALYSIS.md` - Pain points and recommendations
- [ ] Decision document: PyQt6 polish vs web migration

---

## Phase 2: Multi-Brand Expansion (⏳ PLANNED - 2-3 weeks)

**Priority**: 🟠 High
**Goal**: Add support for NYX, L'Oréal Paris, Garnier

### 2.1 Brand Research 🟡
**Status**: Not started
**Effort**: 4-6h
**Dependencies**: Brand team input

**Current Brands**:
- ✅ Maybelline New York (MNY)
- ✅ ESSIE

**New Brands**:
- [ ] NYX - Research validation rules
- [ ] L'Oréal Paris - Research validation rules
- [ ] Garnier - Research validation rules

**Tasks**:
- [ ] Interview brand teams (validation requirements)
- [ ] Document brand-specific rules (4 DIGITS, shade formats, etc.)
- [ ] Identify differences from MNY/ESSIE

**Deliverables**:
- [ ] `docs/BRAND_REQUIREMENTS.md` - Brand-specific validation rules

---

### 2.2 Brand Implementation 🟡
**Status**: Not started
**Effort**: 8-10h
**Dependencies**: 2.1 complete

**Tasks**:
- [ ] Create brand config classes (subclass `BaseBrandConfig`)
- [ ] Implement brand-specific validation logic
- [ ] Register brands in `BrandRegistry`
- [ ] Add brand selection in startup dialog
- [ ] Test with brand-specific datasets

**Deliverables**:
- [ ] `core/brand_configs/nyx_config.py` (if applicable)
- [ ] `core/brand_configs/loreal_paris_config.py` (if applicable)
- [ ] `core/brand_configs/garnier_config.py` (if applicable)
- [ ] Updated `core/brand_configs/brand_registry.py`
- [ ] Brand-specific manual test cases

---

## Phase 3: Reset Manager Integration (⏳ PLANNED - 2-3 weeks)

**Priority**: 🟠 High
**Goal**: Launch Litho Validator from Reset Manager with CLI arguments

**Context**: Reset Manager (React + Tauri app) needs to launch validation tools

### 3.1 CLI Arguments Support 🟠
**Status**: Not started
**Effort**: 8-10h
**Dependencies**: None

**Current State**:
- `main.py` launches GUI with no arguments
- No CLI mode

**Solution**: Add CLI argument support
```bash
python litho_validator/main.py \
  --brief "path/to/brief.xlsx" \
  --design "path/to/design.pdf" \
  --output-json "path/to/result.json" \
  --brand "MNY" \
  --headless
```

**Arguments**:
- `--brief <path>` - Path to Excel brief
- `--design <path>` - Path to design PDF
- `--output-json <path>` - Output validation result as JSON
- `--brand <code>` - Brand code (MNY, ESSIE, NYX, etc.)
- `--headless` - Run without GUI (CLI mode only)

**JSON Output Format**:
```json
{
  "artworkCode": "ART-500001",
  "validationScore": 95,
  "confidence": 98,
  "status": "approved",
  "errors": [],
  "warnings": [
    {
      "type": "SHADE_MISMATCH",
      "message": "Shade number mismatch: found '123' expected '124'",
      "severity": "low",
      "location": "page 1"
    }
  ],
  "validatedAt": "2025-11-24T10:30:00Z",
  "tool": "litho_validator",
  "version": "2.2.0"
}
```

**Tasks**:
- [ ] Add `argparse` in `main.py`
- [ ] Create `core/cli_validator.py` - Headless validation runner
- [ ] Implement JSON output generator
- [ ] Test CLI mode (no GUI)
- [ ] Test with Reset Manager integration

**Deliverables**:
- [ ] `main.py` - CLI argument parsing
- [ ] `core/cli_validator.py` - Headless runner
- [ ] `docs/CLI_USAGE.md` - CLI documentation
- [ ] JSON schema documentation

---

### 3.2 Reset Manager Integration 🟢
**Status**: Documented in Reset Manager roadmap
**Effort**: 4-6h (Reset Manager side)
**Dependencies**: 3.1 complete

**Scope** (Reset Manager side):
- [ ] Button in Design step → Launch Litho Validator with arguments
- [ ] Parse JSON result
- [ ] Display validation score in UI
- [ ] Auto-approve if score > threshold (configurable)
- [ ] Flag for manual review if score < threshold

**Launch Method** (from Reset Manager):
```bash
..\.venv\Scripts\python.exe litho_validator\main.py \
  --brief "artworks/ART-500001/brief.xlsx" \
  --design "artworks/ART-500001/design.pdf" \
  --output-json "artworks/ART-500001/validation_result.json" \
  --brand "MNY" \
  --headless
```

**Deliverables**:
- [ ] Integration documentation
- [ ] Test with Reset Manager V1.3 (when ready)

---

## Phase 4: Web Migration (🔵 FUTURE - 2-3 months)

**Priority**: 🔵 Future
**Goal**: Migrate from PyQt6 desktop to React web app

**Context**: `litho_validator_prod/` already has foundation (React + FastAPI)

### Strategy: Reuse Existing Web Foundation

**Existing Web App** (`litho_validator_prod/`):
- ✅ Backend FastAPI with all routes
- ✅ Core validation modules copied from desktop
- ✅ React + TypeScript frontend
- ✅ L'Oréal design system
- ✅ Dashboard, layout, API client

**What's Missing** (from PLAN_SUITE.md):
- 🚧 Validation View (PDF viewer, table, error panel)
- 🚧 Session manager persistent
- 🚧 Upload workflow
- 🚧 Batch validation
- 🚧 BaseCamp integration UI
- 🚧 Settings page
- 🚧 Export reports

### 4.1 Complete Web App Foundation 🔵
**Status**: In progress (see litho_validator_prod/PLAN_SUITE.md)
**Effort**: 4-6 weeks
**Dependencies**: Phase 1 complete (desktop UX learnings)

**Follow existing plan**: `litho_validator_prod/PLAN_SUITE.md`

**Priority Order**:
1. **Phase 3** (PLAN_SUITE) - Session manager persistent (critical)
2. **Phase 4** (PLAN_SUITE) - Validation batch
3. **Phase 5** (PLAN_SUITE) - Exports and reports
4. **Phase 6** (PLAN_SUITE) - BaseCamp integration
5. **Phase 7** (PLAN_SUITE) - Settings page
6. **Phase 8** (PLAN_SUITE) - UI polish

**Deliverables**:
- [ ] See `litho_validator_prod/PLAN_SUITE.md` for detailed tasks

---

### 4.2 Web App Deployment 🔵
**Status**: Not started
**Effort**: 2-3 weeks
**Dependencies**: 4.1 complete

**Deployment Options**:

**Option A: Desktop App (Standalone)**
- PyInstaller for backend → .exe
- Frontend build → static files
- Embedded server (localhost:8000)
- User opens browser to localhost

**Option B: Web App (Server)**
- Deploy on L'Oréal internal server
- Centralized backend
- Multi-user access via browser

**Recommended**: Option A (desktop standalone) for easier distribution

**Tasks**:
- [ ] PyInstaller config for FastAPI backend
- [ ] Frontend production build (Vite)
- [ ] Embedded server with auto-open browser
- [ ] Installer creation (NSIS for Windows)
- [ ] Testing on clean machine

**Deliverables**:
- [ ] `build/` - Build scripts and configs
- [ ] `Litho_Validator_Setup.exe` - Windows installer
- [ ] `docs/DEPLOYMENT.md` - Deployment guide

---

## Phase 5: AI-Powered Validation (🔵 FUTURE - 2-3 months)

**Priority**: 🔵 Future
**Goal**: Use AI/ML for enhanced validation

### 5.1 AI OCR Enhancement 🔵
**Status**: Concept
**Effort**: 15-20h
**Dependencies**: AI API access (Google Vision, OpenAI, Gemini)

**Current OCR**: Tesseract (basic)

**AI Enhancement**:
- [ ] Google Vision API integration (or Gemini)
- [ ] Better text extraction from low-quality PDFs
- [ ] Handwriting recognition (if applicable)
- [ ] Layout analysis (tables, columns)

**Tasks**:
- [ ] Research API costs (Google Vision vs OpenAI vs Gemini)
- [ ] Proof of concept with test PDFs
- [ ] Compare AI vs Tesseract accuracy
- [ ] Implement fallback (AI fails → Tesseract)
- [ ] Add settings toggle (AI on/off)

**Deliverables**:
- [ ] `core/ai_ocr_processor.py` - AI OCR integration
- [ ] Cost analysis report
- [ ] Accuracy comparison report

---

### 5.2 AI Error Detection 🔵
**Status**: Concept
**Effort**: 25-30h
**Dependencies**: Training data, ML expertise

**Vision**:
- Train ML model to predict errors before validation
- AI suggests corrections for common errors
- Fuzzy matching with AI (when exact match fails)

**Use Cases**:
- Predict "4 DIGITS error" likelihood before validation
- Suggest correct shade name when mismatch detected
- Auto-fix common typos (WTP → WATERPROOF)

**Challenges**:
- Need labeled training data (500+ examples)
- Model accuracy and reliability
- Cost (API calls or local model)

**Tasks**:
- [ ] Collect labeled training data
- [ ] Train ML model (scikit-learn or cloud ML)
- [ ] Proof of concept with test data
- [ ] Implement AI suggestions in UI
- [ ] A/B test (AI vs rule-based)

**Deliverables**:
- [ ] `core/ai_validator.py` - AI validation module
- [ ] Training notebook (Jupyter)
- [ ] Accuracy report

---

## 🐛 Code Quality & Best Practices (Ongoing)

**Priority**: 🟡 Medium
**Goal**: Clean code, maintainability, best practices

### Tasks
- [ ] **Code review** - Review core modules for best practices
- [ ] **Refactor large files** - Split files > 500 lines (if needed)
- [ ] **Type hints** - Add type hints consistently (Python 3.10+)
- [ ] **Docstrings** - Ensure all public methods have docstrings
- [ ] **Logging** - Consistent logging levels (DEBUG, INFO, WARNING, ERROR)
- [ ] **Error handling** - Graceful error handling with user-friendly messages
- [ ] **Path handling** - Use `pathlib.Path` consistently (Windows/Linux compatibility)

### Files to Review
1. `ui/main_window.py` (1,804 lines) - Can be split?
2. `ui/basecamp_dialog.py` (2,135 lines) - Can be split?
3. `ui/litho_viewer.py` (1,742 lines) - Can be split?
4. `core/basecamp_processor_legacy.py` (1,309 lines) - Remove (deprecated)

---

## 📈 Success Metrics

### Phase 1 (Desktop UX)
- [ ] Views consolidated (3 views: Overview, Validation, Settings)
- [ ] Error templates reduced to essentials (10-15 templates max)
- [ ] UI modernized (subjective - user feedback)

### Phase 2 (Multi-Brand)
- [ ] 3+ new brands supported (NYX, L'Oréal Paris, Garnier)
- [ ] Brand-specific validation rules documented

### Phase 3 (Reset Manager Integration)
- [ ] CLI mode works with Reset Manager
- [ ] JSON output validated
- [ ] Auto-approval workflow tested

### Phase 4 (Web Migration)
- [ ] Web app feature parity with desktop
- [ ] Session persistence works
- [ ] Deployment package created

### Phase 5 (AI Enhancement)
- [ ] AI OCR accuracy > Tesseract (measured)
- [ ] AI error prediction accuracy > 80%

---

## 🗓️ Timeline Estimates

### Short-term (1-2 months)
- ✅ Phase 1: Desktop UX improvements (2-3 weeks)
- ✅ Phase 2: Multi-brand expansion (2-3 weeks)
- ✅ Phase 3: Reset Manager integration (2-3 weeks)

### Medium-term (3-6 months)
- 🔵 Phase 4: Web migration (2-3 months)

### Long-term (6-12 months)
- 🔵 Phase 5: AI-powered validation (2-3 months)

---

## 🎯 Recommended Next Steps

### This Week
1. **Start Phase 1.1** - Consolidate Overview + Cards views
2. **Review Phase 1.4** - UX analysis (decide: PyQt6 polish vs web migration)

### This Month
1. **Complete Phase 1** - Desktop UX improvements
2. **Start Phase 2** - Multi-brand expansion (research)

### This Quarter
1. **Complete Phase 2** - Multi-brand expansion
2. **Complete Phase 3** - Reset Manager integration
3. **Decision**: Continue desktop OR migrate to web (Phase 4)

---

## 📚 Documentation

### Existing Documentation
- ✅ `README.md` - User guide, installation
- ✅ `CHANGELOG.md` - Version history
- ✅ `CORRECTIONS_V2.md` - Startup issues (v2.0)
- ✅ `features/brand_validation_criteria/` - Brand validation feature docs
- ✅ `core/basecamp/README.md` - BaseCamp integration docs

### Documentation to Create
- [ ] `UX_ANALYSIS.md` - UX pain points and recommendations (Phase 1.4)
- [ ] `docs/BRAND_REQUIREMENTS.md` - Brand validation rules (Phase 2.1)
- [ ] `docs/CLI_USAGE.md` - CLI mode documentation (Phase 3.1)
- [ ] `docs/DEPLOYMENT.md` - Web app deployment guide (Phase 4.2)

---

## 🔗 Related Projects

### litho_validator_prod (Web Version)
**Location**: `d:\Projets_Loreal\SCRIPT_PYTHON\litho_validator_prod\`
**Status**: Foundation complete (100%), validation view in progress
**Documentation**:
- `litho_validator_prod/STATUS.md` - Current state
- `litho_validator_prod/PLAN_SUITE.md` - Development plan
- `litho_validator_prod/README.md` - Setup instructions

**Relationship**:
- Web version reuses core modules from desktop (`backend/core/`)
- Desktop app is reference implementation
- Web app is future replacement (Phase 4)

### Reset Manager
**Location**: `d:\Projets_Loreal\SCRIPT_PYTHON\reset_manager\`
**Status**: V1 complete, Phase B in progress
**Documentation**: `reset_manager/PROJECT_ROADMAP.md`

**Integration**:
- Reset Manager V1.3: Launch Litho Validator (no arguments)
- Reset Manager V2.2: Launch with CLI arguments (Phase 3.1)
- Reset Manager V2.3+: Use web interface (Phase 4.2)

---

## 📝 Notes

### Design Decisions
- **PyQt6 over PySide6** - Better documentation, more stable
- **Selenium over Playwright** - Better BaseCamp compatibility
- **React over Angular/Vue** - Modern, large ecosystem, team familiarity
- **FastAPI over Flask** - Modern, async, auto-generated docs
- **Tailwind over CSS-in-JS** - Utility-first, fast development

### Lessons Learned (v2.0 Refactoring)
- ✅ Modular architecture significantly improved maintainability
- ✅ Signal/slot pattern essential for PyQt6 apps
- ✅ Comprehensive logging saved hours of debugging
- ⚠️ Should have written tests BEFORE refactoring (but we won't write tests per your request)

### Risk Register
- **PyQt6 complexity** - Risk: Hard to polish UI. Mitigation: Migrate to web (Phase 4).
- **Selenium brittleness** - Risk: BaseCamp UI changes break automation. Mitigation: Multiple navigation strategies, frequent updates.
- **Web app complexity** - Risk: Web migration takes longer than expected. Mitigation: Reuse existing foundation (`litho_validator_prod/`).

---

**Last Updated**: 2025-11-25 (Phase 1.3 completed)
**Next Review**: 2025-12-24 (1 month)
**Maintained By**: Development Team
