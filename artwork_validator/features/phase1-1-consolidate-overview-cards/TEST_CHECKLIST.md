# Test Checklist - Phase 1.1 Consolidate Overview + Cards

**Feature**: Phase 1.1 - Consolider Overview + Cards
**Test Strategy**: Manual testing after each phase (visual + functional)

---

## PHASE 1 Tests - Toggle UI ✅

### Visual Tests
- [ ] Toggle buttons visible at top of Overview
- [ ] Toggle button "Liste" has proper icon 📋
- [ ] Toggle button "Grille" has proper icon 🎴
- [ ] Toggle buttons have proper styling (active state distinct)
- [ ] Default mode is "Liste" (active)

### Functional Tests
- [ ] Click "Liste" → No change (already active)
- [ ] Click "Grille" → Shows placeholder/empty grid container
- [ ] Click "Liste" again → Returns to list view
- [ ] Stats header remains visible during toggle
- [ ] Toolbar (search/filters) remains visible during toggle

### Edge Cases
- [ ] Toggle works with 0 lithos loaded
- [ ] Toggle works with 50+ lithos loaded
- [ ] Toggle preserves search text
- [ ] Toggle preserves filter selection

---

## PHASE 2 Tests - Grid Integration ✅

### Visual Tests
- [ ] Grid view displays PDFCardWidget instances
- [ ] Cards arranged in responsive grid (2-5 columns depending on width)
- [ ] Cards have proper spacing (consistent gaps)
- [ ] Cards show thumbnail + code + description
- [ ] Status badge visible on cards (✅/❌/⏳)

### Functional Tests
- [ ] Click card → Emits `validation_requested` signal
- [ ] Click "Validate" quick action → Approves litho
- [ ] Click "Reject" quick action → Rejects litho
- [ ] Search text filters grid cards
- [ ] Filter dropdown filters grid cards
- [ ] Sort dropdown sorts grid cards
- [ ] Toggle List → Grid preserves filters
- [ ] Toggle Grid → List preserves filters

### Grid Responsiveness
- [ ] Window resize → Grid reflows columns
- [ ] Narrow window (800px) → 2 columns
- [ ] Medium window (1200px) → 3 columns
- [ ] Wide window (1600px+) → 4-5 columns

### Stats Update
- [ ] Stats header updates when litho approved in grid mode
- [ ] Stats header updates when litho rejected in grid mode
- [ ] Stats match between list and grid modes

---

## PHASE 3 Tests - Cleanup ✅

### Compilation Tests
- [ ] App starts without errors
- [ ] No import errors for CardsView
- [ ] No import errors for ViewModeSwitcher
- [ ] No warnings in console about missing classes

### Regression Tests
- [ ] Overview view still loads correctly
- [ ] Validation view still loads correctly
- [ ] Settings view still loads correctly
- [ ] Session manager still works
- [ ] PDF processor still works
- [ ] Excel processor still works

### File Cleanup
- [ ] `ui/cards_view.py` renamed to `.deprecated`
- [ ] `ui/view_mode_switcher.py` renamed to `.deprecated`
- [ ] No references to CardsView in logs
- [ ] No references to ViewModeSwitcher in logs

---

## PHASE 4 Tests - Menu/Navigation ✅

### Menu Tests
- [ ] Menu "Affichage" has exactly 3 items
- [ ] Menu items: "Overview", "Validation", "Paramètres"
- [ ] No "Cards" menu item visible
- [ ] Menu items trigger correct views

### Keyboard Shortcuts
- [ ] `Ctrl+1` → Opens Overview
- [ ] `Ctrl+2` → Opens Validation
- [ ] `Ctrl+3` → Opens Paramètres
- [ ] `Ctrl+4` → Does nothing (removed)
- [ ] Shortcuts work from any view

### Command Palette
- [ ] Open palette (Ctrl+K)
- [ ] Type "overview" → Shows "Go to Overview"
- [ ] Type "validation" → Shows "Go to Validation"
- [ ] Type "cards" → No results (removed)
- [ ] Execute command → Switches to correct view

### Navigation Flow
- [ ] Start app → Defaults to Validation view
- [ ] Switch to Overview → Toggle defaults to List mode
- [ ] Switch to Validation → Click litho → Opens validation
- [ ] Click Overview from any view → Preserves last toggle state
- [ ] Reload session → Restores last view mode

---

## Integration Tests (Full Feature)

### End-to-End Workflow
- [ ] Load session with 20 PDFs
- [ ] Navigate to Overview
- [ ] Switch to Grid mode
- [ ] Filter "En attente" → Shows only pending
- [ ] Search "YCA2" → Shows matching lithos
- [ ] Click card → Opens Validation view
- [ ] Approve litho → Return to Overview
- [ ] Grid card shows ✅ status
- [ ] Switch to List mode
- [ ] List card shows ✅ status
- [ ] Stats header shows 1 approved

### Performance Tests
- [ ] Load 100 PDFs → Overview loads in <2s
- [ ] Toggle List→Grid with 100 PDFs → <1s
- [ ] Toggle Grid→List with 100 PDFs → <1s
- [ ] Search in grid with 100 PDFs → Instant filter
- [ ] No memory leaks after 10 toggles

### Error Handling
- [ ] No PDFs loaded → Overview shows empty state
- [ ] No Excel loaded → Cards show "No data"
- [ ] Missing thumbnail → Shows placeholder icon
- [ ] Invalid litho code → Doesn't crash

---

## Regression Tests (Critical Features)

### Session Management
- [ ] Save session → Reload → Overview shows correct data
- [ ] Approve litho → Save → Reload → Status preserved
- [ ] Reject litho → Save → Reload → Status preserved

### Validation View
- [ ] Open litho from Overview list → Validation opens
- [ ] Open litho from Overview grid → Validation opens
- [ ] Validate in Validation view → Overview updates

### BaseCamp Integration
- [ ] Process approved lithos → Integration works
- [ ] Approved lithos from Overview → Show in integration list

---

## Acceptance Criteria

### Must Have ✅
- [ ] Overview has toggle List/Grid
- [ ] List mode shows LithoRowCard (existing)
- [ ] Grid mode shows PDFCardWidget
- [ ] CardsView removed/deprecated
- [ ] ViewModeSwitcher removed/deprecated
- [ ] Menu has 3 items (Overview, Validation, Settings)
- [ ] Shortcuts updated (Ctrl+1/2/3)
- [ ] No regressions on existing features

### Nice to Have 🎯
- [ ] Toggle state persists in session
- [ ] Smooth transition animation between modes
- [ ] Grid columns user-configurable

---

**Test Strategy**: Manual testing only (no automated tests per project guidelines)
**Test Frequency**: After EACH phase before continuing
**Tester**: Developer + User validation

---

**Last Updated**: 2025-11-24
