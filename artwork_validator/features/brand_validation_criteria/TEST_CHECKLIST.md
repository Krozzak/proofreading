# Test Checklist - Brand Validation Criteria

**Feature**: Brand Validation Criteria
**Date**: 2025-11-21
**Version**: 1.0

---

## 🎯 Vue d'Ensemble

Cette checklist couvre tous les tests nécessaires pour valider que la feature Brand Validation Criteria fonctionne correctement.

**Ordre recommandé**:
1. Tests Backend (sans UI)
2. Tests Frontend (UI uniquement)
3. Tests Intégration (workflow complet)

---

## 📦 Phase 1: Tests Backend - Brand Configuration System

### Test 1.1: BaseBrandConfig (Abstract Class)

```python
# Test d'import
from core.brand_configs.base_config import BaseBrandConfig

# ✅ Import réussit
```

**Résultat attendu**: Pas d'erreur d'import

---

### Test 1.2: MNYBrandConfig

```python
from core.brand_configs.mny_config import MNYBrandConfig

# Instanciation
mny = MNYBrandConfig()

# Tests méthodes
assert mny.get_brand_code() == 'MNY'
assert mny.get_brand_display_name() == 'Maybelline New York'

# Test validation filename
assert mny.is_valid_filename('YCA12345.pdf') == True
assert mny.is_valid_filename('YCA12345_version2.pdf') == True
assert mny.is_valid_filename('CARE_S26_1_3.pdf') == False
assert mny.is_valid_filename('invalid.pdf') == False

# Test extraction code
assert mny.extract_litho_code('YCA12345_v2.pdf') == 'YCA12345'
assert mny.extract_litho_code('YCA98765.pdf') == 'YCA98765'
assert mny.extract_litho_code('CARE_S26_1_3.pdf') == None

# Test validation code
assert mny.is_valid_litho_code('YCA12345') == True
assert mny.is_valid_litho_code('YCA98765') == True
assert mny.is_valid_litho_code('CARE_S26_1_3') == False

# Test flags
assert mny.requires_upc_validation() == False
assert mny.requires_digits_validation() == True

# Test colonnes
assert 'LITHO' in mny.get_required_columns()
assert '4 DIGITS' in mny.get_required_columns()
assert 'NEW' in mny.get_optional_columns()

# Test column types
assert mny.get_column_types()['SHADE NUMBER'] == 'numeric'
assert mny.get_column_types()['4 DIGITS'] == 'numeric'
```

**Résultats**:
- [ ] Tous les asserts passent
- [ ] Aucune erreur levée

---

### Test 1.3: ESSIEBrandConfig

```python
from core.brand_configs.essie_config import ESSIEBrandConfig

# Instanciation
essie = ESSIEBrandConfig()

# Tests méthodes
assert essie.get_brand_code() == 'ESSIE'
assert essie.get_brand_display_name() == 'ESSIE'

# Test validation filename
assert essie.is_valid_filename('CARE_S26_1_3.pdf') == True
assert essie.is_valid_filename('GEL_S26_2_6.pdf') == True
assert essie.is_valid_filename('ESSIE_S26_4_6_SHADESTRIPS.pdf') == True
assert essie.is_valid_filename('NSTUDIO_S26_1_3.pdf') == True
assert essie.is_valid_filename('EXPRESS_S26_2_4.pdf') == True
assert essie.is_valid_filename('YCA12345.pdf') == False
assert essie.is_valid_filename('invalid.pdf') == False

# Test extraction code
assert essie.extract_litho_code('CARE_S26_1_3.pdf') == 'CARE_S26_1_3'
assert essie.extract_litho_code('GEL_S26_2_6_SHADESTRIPS.pdf') == 'GEL_S26_2_6'
assert essie.extract_litho_code('ESSIE_S26_4_6.pdf') == 'ESSIE_S26_4_6'
assert essie.extract_litho_code('YCA12345.pdf') == None

# Test validation code
assert essie.is_valid_litho_code('CARE_S26_1_3') == True
assert essie.is_valid_litho_code('GEL_S26_2_6') == True
assert essie.is_valid_litho_code('YCA12345') == False

# Test flags
assert essie.requires_upc_validation() == False
assert essie.requires_digits_validation() == False

# Test colonnes
assert 'LITHO' in essie.get_required_columns()
assert '4 DIGITS' not in essie.get_required_columns()
assert 'STRIP TYPE' in essie.get_optional_columns()

# Test column types
assert essie.get_column_types()['SHADE NUMBER'] == str  # ⚠️ TEXTE, pas numeric!
```

**Résultats**:
- [ ] Tous les asserts passent
- [ ] Aucune erreur levée

---

### Test 1.4: BrandRegistry

```python
from core.brand_configs.brand_registry import BrandRegistry
from core.brand_configs.mny_config import MNYBrandConfig
from core.brand_configs.essie_config import ESSIEBrandConfig

# Clear registry (pour test propre)
BrandRegistry.clear()

# Register marques
mny = MNYBrandConfig()
essie = ESSIEBrandConfig()

BrandRegistry.register(mny)
BrandRegistry.register(essie)

# Tests
assert len(BrandRegistry.get_all_brands()) == 2
assert BrandRegistry.is_registered('MNY') == True
assert BrandRegistry.is_registered('ESSIE') == True
assert BrandRegistry.is_registered('UNKNOWN') == False

# Get brand
retrieved_mny = BrandRegistry.get_brand('MNY')
assert retrieved_mny is not None
assert retrieved_mny.get_brand_code() == 'MNY'

retrieved_essie = BrandRegistry.get_brand('ESSIE')
assert retrieved_essie is not None
assert retrieved_essie.get_brand_code() == 'ESSIE'

# Get all codes
codes = BrandRegistry.get_brand_codes()
assert 'MNY' in codes
assert 'ESSIE' in codes

# Unregister
BrandRegistry.unregister('MNY')
assert BrandRegistry.is_registered('MNY') == False
assert BrandRegistry.is_registered('ESSIE') == True
```

**Résultats**:
- [ ] Tous les asserts passent
- [ ] Aucune erreur levée

---

## 📊 Phase 2: Tests Processors

### Test 2.1: ExcelProcessor avec MNY

```python
from core.excel_processor import ExcelProcessor
from core.brand_configs.mny_config import MNYBrandConfig

# Initialiser avec MNY config
mny_config = MNYBrandConfig()
excel_proc = ExcelProcessor(brand_config=mny_config)

# Vérifier attributs
assert excel_proc.brand_config.get_brand_code() == 'MNY'
assert '4 DIGITS' in excel_proc.required_columns
assert excel_proc.column_types['SHADE NUMBER'] == 'numeric'

# Load fichier Excel MNY (si disponible)
# success = excel_proc.load_file('path/to/mny_excel.xlsx')
# assert success == True
```

**Résultats**:
- [ ] ExcelProcessor initialise correctement
- [ ] Colonnes MNY configurées
- [ ] Load fichier réussit (si testé)

---

### Test 2.2: ExcelProcessor avec ESSIE

```python
from core.excel_processor import ExcelProcessor
from core.brand_configs.essie_config import ESSIEBrandConfig

# Initialiser avec ESSIE config
essie_config = ESSIEBrandConfig()
excel_proc = ExcelProcessor(brand_config=essie_config)

# Vérifier attributs
assert excel_proc.brand_config.get_brand_code() == 'ESSIE'
assert '4 DIGITS' not in excel_proc.required_columns
assert excel_proc.column_types['SHADE NUMBER'] == str  # ⚠️ STRING!

# Load fichier Excel ESSIE (si disponible)
# success = excel_proc.load_file('path/to/essie_excel.xlsx')
# assert success == True
```

**Résultats**:
- [ ] ExcelProcessor initialise correctement
- [ ] Colonnes ESSIE configurées
- [ ] SHADE NUMBER = str (pas numeric)
- [ ] Load fichier réussit (si testé)

---

### Test 2.3: PDFProcessor avec MNY

```python
from core.pdf_processor import PDFProcessor
from core.brand_configs.mny_config import MNYBrandConfig

# Initialiser avec MNY config
mny_config = MNYBrandConfig()
pdf_proc = PDFProcessor(brand_config=mny_config)

# Vérifier attributs
assert pdf_proc.brand_config.get_brand_code() == 'MNY'

# Test validation filename
assert pdf_proc._is_valid_filename('YCA12345.pdf') == True
assert pdf_proc._is_valid_filename('CARE_S26_1_3.pdf') == False

# Test extraction
assert pdf_proc._extract_litho_code('YCA12345_v2.pdf') == 'YCA12345'
```

**Résultats**:
- [ ] PDFProcessor initialise correctement
- [ ] Validation filename MNY correcte
- [ ] Extraction code MNY correcte

---

### Test 2.4: PDFProcessor avec ESSIE

```python
from core.pdf_processor import PDFProcessor
from core.brand_configs.essie_config import ESSIEBrandConfig

# Initialiser avec ESSIE config
essie_config = ESSIEBrandConfig()
pdf_proc = PDFProcessor(brand_config=essie_config)

# Vérifier attributs
assert pdf_proc.brand_config.get_brand_code() == 'ESSIE'

# Test validation filename
assert pdf_proc._is_valid_filename('CARE_S26_1_3.pdf') == True
assert pdf_proc._is_valid_filename('GEL_S26_2_6_SHADESTRIPS.pdf') == True
assert pdf_proc._is_valid_filename('YCA12345.pdf') == False

# Test extraction
assert pdf_proc._extract_litho_code('CARE_S26_1_3.pdf') == 'CARE_S26_1_3'
assert pdf_proc._extract_litho_code('GEL_S26_2_6_SHADESTRIPS.pdf') == 'GEL_S26_2_6'
```

**Résultats**:
- [ ] PDFProcessor initialise correctement
- [ ] Validation filename ESSIE correcte
- [ ] Extraction code ESSIE correcte

---

### Test 2.5: Validator avec brand_config

```python
from core.validator import LithoValidator
from core.brand_configs.mny_config import MNYBrandConfig
from core.brand_configs.essie_config import ESSIEBrandConfig

# MNY Validator
mny_validator = LithoValidator(brand_config=MNYBrandConfig())
assert mny_validator.brand_config.get_brand_code() == 'MNY'

# ESSIE Validator
essie_validator = LithoValidator(brand_config=ESSIEBrandConfig())
assert essie_validator.brand_config.get_brand_code() == 'ESSIE'

# Test requires_digits_validation
assert mny_validator.brand_config.requires_digits_validation() == True
assert essie_validator.brand_config.requires_digits_validation() == False
```

**Résultats**:
- [ ] Validators initialisent correctement
- [ ] Brand configs correctes
- [ ] Flags validation corrects

---

## 🎨 Phase 3: Tests Frontend

### Test 3.1: StartupDialog - Brand Selection Visible

**Actions**:
1. Lancer l'app
2. StartupDialog s'ouvre
3. Chercher section "🏷️ Sélection de la marque"

**Résultats attendus**:
- [ ] Section visible
- [ ] Dropdown présent
- [ ] QTextEdit rules présent

---

### Test 3.2: StartupDialog - Dropdown Populated

**Actions**:
1. Cliquer sur dropdown
2. Vérifier options

**Résultats attendus**:
- [ ] "Maybelline New York (MNY)" présent
- [ ] "ESSIE (ESSIE)" présent
- [ ] Format correct: "Display Name (CODE)"

---

### Test 3.3: StartupDialog - Rules Update MNY

**Actions**:
1. Sélectionner "Maybelline New York (MNY)"
2. Observer QTextEdit rules

**Résultats attendus**:
- [ ] Rules affichées instantanément
- [ ] Contient "YCA + 5 chiffres"
- [ ] Contient "YCA12345"
- [ ] Contient "SHADE NUMBER: Numérique"
- [ ] Contient "4 DIGITS"

---

### Test 3.4: StartupDialog - Rules Update ESSIE

**Actions**:
1. Sélectionner "ESSIE (ESSIE)"
2. Observer QTextEdit rules

**Résultats attendus**:
- [ ] Rules affichées instantanément
- [ ] Contient "[GAMME]_S[SEASON]_[INDEX]_[TOTAL]"
- [ ] Contient "CARE, GEL, NSTUDIO, ESSIE, EXPRESS"
- [ ] Contient "CARE_S26_1_3"
- [ ] Contient "SHADE NUMBER: Texte"
- [ ] Contient "4 DIGITS: ❌ Désactivé"

---

### Test 3.5: Settings - Brand Rules Tab Visible

**Actions**:
1. Ouvrir Settings
2. Chercher onglet "🏷️ Règles de Marques"

**Résultats attendus**:
- [ ] Onglet visible
- [ ] Cliquable
- [ ] Pas d'erreur au clic

---

### Test 3.6: Settings - Brand Rules Content

**Actions**:
1. Cliquer sur onglet Brand Rules
2. Observer contenu

**Résultats attendus**:
- [ ] 2 cards affichées (MNY, ESSIE)
- [ ] MNY card:
  - [ ] Titre "Maybelline New York (MNY)"
  - [ ] Rules visibles
  - [ ] Colonnes obligatoires en vert
  - [ ] Colonnes optionnelles en gris italique
  - [ ] Flags: UPC=❌, Digits=✅
- [ ] ESSIE card:
  - [ ] Titre "ESSIE (ESSIE)"
  - [ ] Rules visibles
  - [ ] Colonnes obligatoires en vert
  - [ ] Colonnes optionnelles en gris italique
  - [ ] Flags: UPC=❌, Digits=❌

---

## 🔗 Phase 4: Tests Intégration (Workflow Complet)

### Test 4.1: Workflow MNY Complet

**Pré-requis**:
- Dossier PDFs MNY (ex: YCA12345.pdf, YCA98765.pdf)
- Fichier Excel MNY avec colonnes correctes

**Actions**:
1. Lancer app
2. StartupDialog → Sélectionner "Maybelline New York (MNY)"
3. Créer nouvelle session
4. Sélectionner dossier PDFs MNY
5. Sélectionner fichier Excel MNY
6. Observer chargement

**Résultats attendus**:
- [ ] PDFs valides reconnus (YCA format)
- [ ] PDFs invalides détectés
- [ ] Excel chargé sans erreur
- [ ] SHADE NUMBER converti en numeric
- [ ] 4 DIGITS column présente
- [ ] Validation fonctionne
- [ ] SHADE NUMBER validé dans PDF
- [ ] SHADE NAME validé dans PDF
- [ ] 4 DIGITS validable si option activée
- [ ] UPC validation skip

---

### Test 4.2: Workflow ESSIE Complet

**Pré-requis**:
- Dossier PDFs ESSIE (ex: CARE_S26_1_3.pdf, GEL_S26_2_6_SHADESTRIPS.pdf)
- Fichier Excel ESSIE avec colonnes correctes

**Actions**:
1. Lancer app
2. StartupDialog → Sélectionner "ESSIE (ESSIE)"
3. Créer nouvelle session
4. Sélectionner dossier PDFs ESSIE
5. Sélectionner fichier Excel ESSIE
6. Observer chargement

**Résultats attendus**:
- [ ] PDFs valides reconnus (CARE, GEL, NSTUDIO, ESSIE, EXPRESS formats)
- [ ] PDFs avec suffix _SHADESTRIPS reconnus
- [ ] PDFs YCA rejetés comme invalides
- [ ] Excel chargé sans erreur
- [ ] SHADE NUMBER reste texte (pas converti en numeric)
- [ ] Valeurs texte dans SHADE NUMBER (ex: "2-IN-1 BASE & TOP COAT") préservées
- [ ] 4 DIGITS column absente (ou ignorée si présente)
- [ ] Validation fonctionne
- [ ] SHADE NUMBER texte validé dans PDF
- [ ] SHADE NAME validé dans PDF
- [ ] 4 DIGITS skip automatiquement
- [ ] UPC validation skip

---

### Test 4.3: Changement Marque Dynamique (MNY → ESSIE)

**Actions**:
1. Session active avec MNY
2. Changer marque vers ESSIE (via méthode set_brand_config ou UI si implémentée)
3. Observer rechargement

**Résultats attendus**:
- [ ] PDFs rechargés automatiquement
- [ ] Fichiers MNY maintenant invalides
- [ ] Excel rechargé automatiquement
- [ ] SHADE NUMBER converti de numeric → texte
- [ ] Validation mise à jour

---

### Test 4.4: Session Save/Load avec Brand Code

**Actions**:
1. Créer session avec ESSIE
2. Charger quelques PDFs/Excel
3. Sauvegarder session
4. Fermer app
5. Relancer app
6. Charger session sauvegardée

**Résultats attendus**:
- [ ] brand_code='ESSIE' sauvegardé dans fichier session
- [ ] brand_code restauré au chargement
- [ ] Processors réinitialisés avec ESSIE config
- [ ] PDFs/Excel chargés avec bonnes règles

---

## 📋 Résumé Tests

### Tests Backend
- [ ] Test 1.1: BaseBrandConfig import
- [ ] Test 1.2: MNYBrandConfig complet
- [ ] Test 1.3: ESSIEBrandConfig complet
- [ ] Test 1.4: BrandRegistry
- [ ] Test 2.1: ExcelProcessor MNY
- [ ] Test 2.2: ExcelProcessor ESSIE
- [ ] Test 2.3: PDFProcessor MNY
- [ ] Test 2.4: PDFProcessor ESSIE
- [ ] Test 2.5: Validator brand_config

**Total Backend**: 9 tests

### Tests Frontend
- [ ] Test 3.1: StartupDialog visible
- [ ] Test 3.2: Dropdown populated
- [ ] Test 3.3: Rules update MNY
- [ ] Test 3.4: Rules update ESSIE
- [ ] Test 3.5: Settings tab visible
- [ ] Test 3.6: Settings tab content

**Total Frontend**: 6 tests

### Tests Intégration
- [ ] Test 4.1: Workflow MNY complet
- [ ] Test 4.2: Workflow ESSIE complet
- [ ] Test 4.3: Changement marque dynamique
- [ ] Test 4.4: Session save/load

**Total Intégration**: 4 tests

---

## ✅ Critères de Succès

**Feature considérée complète si**:
- ✅ Tous tests backend passent (9/9)
- ✅ Tous tests frontend passent (6/6)
- ✅ Au moins 3/4 tests intégration passent
- ✅ Aucune régression sur workflow MNY existant
- ✅ Workflow ESSIE fonctionne end-to-end

**Total tests requis**: Au moins 18/19 tests (95% success rate)

---

## 🐛 Bugs à Reporter

Si tests échouent, utiliser ce template:

```
**Test échoué**: [Numéro test]
**Phase**: [Backend/Frontend/Intégration]
**Description**: [Description courte]
**Steps to reproduce**:
1. [Étape 1]
2. [Étape 2]

**Expected**: [Résultat attendu]
**Actual**: [Résultat actuel]
**Error message**: [Message d'erreur si applicable]

**Solution potentielle**: [Si identifiée]
```

---

Bonne chance avec les tests ! 🚀
