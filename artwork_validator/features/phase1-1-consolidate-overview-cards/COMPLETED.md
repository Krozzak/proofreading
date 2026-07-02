# Feature: Phase 1.1 - Consolider Overview + Cards

**Feature ID**: phase1-1-consolidate-overview-cards
**Status**: ✅ COMPLETED
**Priority**: High
**Effort Estimate**: 6-8h
**Actual Effort**: 6h
**Created**: 2025-11-24
**Completed**: 2025-11-24

---

## ✅ Completion Summary

**Implementation**: All 4 phases completed successfully
- ✅ Phase 1: Toggle UI created in OverviewView
- ✅ Phase 2: Grid layout integrated with PDFCardWidget
- ✅ Phase 3: CardsView and ViewModeSwitcher deprecated
- ✅ Phase 4: Menu restructured (3 views, shortcuts updated)

**Results**:
- 4 views consolidated to 3 (Overview, Validation, Settings)
- 451 lines of code deprecated (cards_view.py + view_mode_switcher.py)
- Toggle between List/Grid modes functional
- No regressions on existing features
- User tested and approved

**Files Modified**:
- [ui/overview_view.py](../../ui/overview_view.py) - 473 lines (toggle + grid integration)
- [ui/main_window.py](../../ui/main_window.py) - Menu simplified, shortcuts updated
- [ui/cards_view.py.deprecated](../../ui/cards_view.py.deprecated) - 361 lines deprecated
- [ui/view_mode_switcher.py.deprecated](../../ui/view_mode_switcher.py.deprecated) - 90 lines deprecated

**Documentation**:
- [IMPLEMENTATION_LOG.md](./IMPLEMENTATION_LOG.md) - Technical journal
- [TEST_CHECKLIST.md](./TEST_CHECKLIST.md) - Manual test checklist
- [PROJECT_ROADMAP.md](../../PROJECT_ROADMAP.md) - Phase 1.1 marked complete
- [CHANGELOG.md](../../CHANGELOG.md) - v2.1.0 entry added

---

## Objectif

Fusionner les vues **Overview** (liste) et **Cards** (grille) en une seule vue **Overview** avec un toggle permettant de basculer entre mode liste et mode grille.

**Bénéfices**:
- ✅ Réduction redondance (2 vues → 1 vue)
- ✅ Interface simplifiée (3 vues au lieu de 4)
- ✅ Meilleure UX (toggle rapide list/grid)
- ✅ Code plus maintenable

---

## État Actuel

### Architecture
```
main_window.py
├── ViewModeSwitcher (top band)
│   ├── Overview button
│   ├── Validation button
│   ├── Cards button
│   └── Settings button
├── QStackedWidget
│   ├── OverviewView (liste avec LithoRowCard)
│   ├── ValidationPanel
│   ├── CardsView (grille avec PDFCardWidget)
│   └── SettingsDialog
```

### Composants Réutilisables
- **LithoRowCard** (`ui/litho_row_card.py`) - Card compacte pour liste
- **PDFCardWidget** (`ui/pdf_card_widget.py`) - Card large pour grille

### Fichiers Impactés
- ✅ `ui/overview_view.py` (474 lignes) - **À MODIFIER**
- ❌ `ui/cards_view.py` (361 lignes) - **À DÉPRÉCIER**
- ✅ `ui/main_window.py` (1804 lignes) - **À MODIFIER**
- ❌ `ui/view_mode_switcher.py` (90 lignes) - **À DÉPRÉCIER**
- ✅ `ui/pdf_card_widget.py` - **À RÉUTILISER** (inchangé)
- ✅ `ui/litho_row_card.py` - **À RÉUTILISER** (inchangé)

---

## Phases d'Implémentation

### PHASE 1 🎨: Créer toggle dans OverviewView
**Type**: Frontend (UI) - **Test visuel requis**
**Effort**: 1-2h

**Tâches**:
1. Ajouter boutons toggle en haut d'OverviewView:
   ```
   [ 📋 Liste ] [ 🎴 Grille ]
   ```
2. Créer QStackedWidget interne pour switcher layouts
3. Conserver header stats + toolbar actuel
4. Signaux: `view_mode_changed = pyqtSignal(str)  # 'list' ou 'grid'`

**Fichiers modifiés**:
- `ui/overview_view.py:26-61` - Ajout toggle + stacked widget

**Test Checklist**:
- [ ] Toggle visible en haut de la vue
- [ ] Click toggle Liste → Affiche liste (existante)
- [ ] Click toggle Grille → Affiche placeholder (vide pour l'instant)
- [ ] Stats header + toolbar toujours visibles

---

### PHASE 2 🎨: Intégrer grid layout dans OverviewView
**Type**: Frontend (UI) - **Test visuel requis**
**Effort**: 2-3h

**Tâches**:
1. Copier logique grid de `cards_view.py:172-180` (QGridLayout)
2. Réutiliser `PDFCardWidget` (import existant)
3. Méthode `display_grid_view()`:
   - Créer PDFCardWidget pour chaque litho
   - Organiser en grille responsive (cols dynamiques)
   - Connecter signaux: `card_clicked`, `validate_clicked`, `reject_clicked`
4. Méthode `display_list_view()` (code existant, renommer)
5. Toggle switch entre list/grid

**Fichiers modifiés**:
- `ui/overview_view.py:1-6` - Ajouter import `PDFCardWidget`
- `ui/overview_view.py:26-61` - Ajout grid container + logic
- `ui/overview_view.py:302-323` - Refactor `load_lithos()` pour supporter 2 modes

**Test Checklist**:
- [ ] Toggle Grille → Affiche cartes PDFCardWidget
- [ ] Grille responsive (adapte colonnes selon largeur)
- [ ] Click carte → Émet signal `validation_requested`
- [ ] Quick actions sur cartes fonctionnent
- [ ] Toggle Liste → Retour liste LithoRowCard
- [ ] Filtres + search fonctionnent en mode grille

---

### PHASE 3 🔧: Supprimer CardsView + ViewModeSwitcher
**Type**: Backend (cleanup) - **Test compilation**
**Effort**: 1h

**Tâches**:
1. `main_window.py:16` - Supprimer `from .cards_view import CardsView`
2. `main_window.py:14` - Supprimer `from .view_mode_switcher import ViewModeSwitcher`
3. `main_window.py:104` - Supprimer `self.cards_view = None`
4. `main_window.py:389` - Supprimer `self.view_switcher.view_changed.connect(...)`
5. `main_window.py:615-633` - Supprimer bloc `if mode == 'cards':`
6. `main_window.py:681-696` - Supprimer références `self.cards_view`
7. Supprimer fichiers:
   - `ui/cards_view.py` → Renommer en `ui/cards_view.py.deprecated`
   - `ui/view_mode_switcher.py` → Renommer en `ui/view_mode_switcher.py.deprecated`

**Fichiers modifiés**:
- `ui/main_window.py:14-16,104,389,615-696` - Suppressions
- `ui/cards_view.py` → **DEPRECATED**
- `ui/view_mode_switcher.py` → **DEPRECATED**

**Test Checklist**:
- [ ] App démarre sans erreur
- [ ] Aucune référence à CardsView dans logs
- [ ] Aucune référence à ViewModeSwitcher

---

### PHASE 4 ⚙️: Restructurer menu et navigation
**Type**: Mixed (UI + navigation) - **Test navigation**
**Effort**: 1-2h

**Tâches**:
1. Simplifier menu "Affichage" (3 items):
   ```python
   # Ancien (4 items)
   - Overview
   - Validation
   - Cards        ← SUPPRIMER
   - Paramètres

   # Nouveau (3 items)
   - Overview
   - Validation
   - Paramètres
   ```
2. Update shortcuts:
   - `Ctrl+1` → Overview
   - `Ctrl+2` → Validation
   - `Ctrl+3` → Paramètres (ancien Ctrl+4)
   - ~~`Ctrl+4` → Cards~~ SUPPRIMER
3. Cleanup `switch_view_mode()` - Supprimer case 'cards'
4. Cleanup Command Palette - Supprimer "Go to Cards"

**Fichiers modifiés**:
- `ui/main_window.py:344-359` - Menu actions (supprimer cards_action)
- `ui/main_window.py:551-559` - Shortcuts (update + supprimer cards shortcut)
- `ui/main_window.py:588-645` - `switch_view_mode()` (supprimer case 'cards')
- `ui/main_window.py:724` - Command registry (supprimer "Go to Cards")

**Test Checklist**:
- [ ] Menu "Affichage" a 3 items (Overview, Validation, Paramètres)
- [ ] Ctrl+1 → Overview
- [ ] Ctrl+2 → Validation
- [ ] Ctrl+3 → Paramètres
- [ ] Ctrl+4 ne fait rien (supprimé)
- [ ] Command Palette n'affiche plus "Go to Cards"

---

## Test Checklist Global

### Après PHASE 1+2 (Toggle intégré)
- [ ] Vue Overview charge correctement
- [ ] Toggle Liste/Grille visible et fonctionnel
- [ ] Mode Liste affiche LithoRowCard
- [ ] Mode Grille affiche PDFCardWidget
- [ ] Stats header mis à jour dans les 2 modes
- [ ] Filtres + search fonctionnent dans les 2 modes
- [ ] Click litho → Ouvre validation

### Après PHASE 3+4 (Cleanup)
- [ ] CardsView supprimée (aucune erreur)
- [ ] ViewModeSwitcher supprimé (aucune erreur)
- [ ] Menu simplifié (3 vues)
- [ ] Navigation shortcuts mis à jour
- [ ] Aucune régression sur Overview, Validation, Settings

---

## Success Metrics

- ✅ 2 vues fusionnées en 1 (Overview + Cards → Overview avec toggle)
- ✅ 4 modes réduits à 3 (Overview, Validation, Settings)
- ✅ Toggle list/grid fonctionnel
- ✅ Aucune régression fonctionnelle
- ✅ Code simplifié (2 fichiers dépréciés)

---

## Risques & Mitigations

### Risque 1: Complexité OverviewView
- **Impact**: Fichier devient trop gros (>600 lignes)
- **Mitigation**: Extraire grid logic dans méthodes séparées, bien commentées

### Risque 2: Signaux cassés
- **Impact**: Validation ne s'ouvre plus au click
- **Mitigation**: Tester signaux après CHAQUE phase

### Risque 3: Régressions stats/filters
- **Impact**: Stats ou filtres ne fonctionnent plus
- **Mitigation**: Tester filtres + stats en mode liste ET grille

---

## Documentation à Mettre à Jour

Après feature complétée:
- ✅ `PROJECT_ROADMAP.md:71-109` - Marquer Phase 1.1 comme complétée
- ✅ `README.md` - Update section "Utilisation" (3 vues au lieu de 4)
- ✅ `CHANGELOG.md` - Ajouter entrée v2.2.0 avec changements

---

**Maintenu par**: Development Team
**Dernière mise à jour**: 2025-11-24
