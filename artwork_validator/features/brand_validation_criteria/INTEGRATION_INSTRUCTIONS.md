# Instructions d'Intégration - Brand Validation Criteria

**Date**: 2025-11-21
**Status**: Phase 7 - Integration finale

---

## 📝 Changements à Appliquer

### 1. **main.py** - Initialiser le BrandRegistry

Au début de `main()`, après les imports, ajouter:

```python
# Imports à ajouter
from core.brand_configs.brand_registry import BrandRegistry
from core.brand_configs.mny_config import MNYBrandConfig
from core.brand_configs.essie_config import ESSIEBrandConfig

def main():
    # 🆕 Initialiser le registry des marques
    registry = BrandRegistry()
    registry.register(MNYBrandConfig())
    registry.register(ESSIEBrandConfig())

    print("✅ Brand Registry initialized:")
    for brand in registry.get_all_brands():
        print(f"  - {brand.get_brand_display_name()} ({brand.get_brand_code()})")

    # ... reste du code main existant
```

---

### 2. **ui/main_window.py** - Passer brand_config aux processors

#### Étape 2.1: Ajouter attribut current_brand_code

Dans `__init__` de MainWindow:

```python
def __init__(self):
    super().__init__()

    # 🆕 Brand configuration
    self.current_brand_code = 'MNY'  # Par défaut
    self.current_brand_config = None

    # ... reste du code
```

#### Étape 2.2: Modifier init_processors()

Chercher la méthode `init_processors()` et modifier:

```python
def init_processors(self):
    """Initialise les processeurs avec la configuration de marque"""
    from core.brand_configs.brand_registry import BrandRegistry

    # 🆕 Récupérer la config de marque
    self.current_brand_config = BrandRegistry.get_brand(self.current_brand_code)

    if self.current_brand_config is None:
        # Fallback
        from core.brand_configs.mny_config import MNYBrandConfig
        self.current_brand_config = MNYBrandConfig()

    # 🆕 Passer brand_config aux processors
    self.pdf_processor = PDFProcessor(brand_config=self.current_brand_config)
    self.excel_processor = ExcelProcessor(brand_config=self.current_brand_config)
    self.validator = LithoValidator(brand_config=self.current_brand_config)

    # Reste des initialisations...
    self.report_generator = ReportGenerator(pdf_processor=self.pdf_processor)
    self.session_manager = SessionManager()
```

#### Étape 2.3: Ajouter méthode set_brand_config()

Ajouter cette nouvelle méthode dans MainWindow:

```python
def set_brand_config(self, brand_code: str):
    """
    Change la configuration de marque pour tous les processeurs

    Args:
        brand_code (str): Code de la marque (MNY, ESSIE, etc.)
    """
    from core.brand_configs.brand_registry import BrandRegistry

    brand_config = BrandRegistry.get_brand(brand_code)

    if brand_config:
        old_brand = self.current_brand_code
        self.current_brand_code = brand_code
        self.current_brand_config = brand_config

        # Mettre à jour tous les processors
        if hasattr(self, 'pdf_processor'):
            self.pdf_processor.set_brand_config(brand_config)

        if hasattr(self, 'excel_processor'):
            self.excel_processor.set_brand_config(brand_config)

        if hasattr(self, 'validator'):
            self.validator.brand_config = brand_config

        self.logger.info(f"✅ Brand configuration changed: {old_brand} → {brand_code}")

        # Optionnel: Afficher un message à l'utilisateur
        self.statusBar().showMessage(
            f"Marque changée: {brand_config.get_brand_display_name()}",
            3000
        )
```

---

### 3. **ui/main_window.py** - Récupérer brand_code depuis StartupDialog

Chercher où `StartupDialog` est créé et connecté, puis modifier:

```python
# Dans la méthode qui gère la nouvelle session (chercher new_session_requested.connect)

def on_new_session_requested(self):
    """Gère la création d'une nouvelle session"""

    # 🆕 Récupérer le brand_code depuis le dialog
    if hasattr(self, 'startup_dialog'):
        brand_code = self.startup_dialog.get_selected_brand_code()
        self.current_brand_code = brand_code

        # Réinitialiser les processors avec la nouvelle marque
        self.init_processors()

        self.logger.info(f"🆕 Nouvelle session avec marque: {brand_code}")

    # ... reste du code existant (sélection dossier PDFs, Excel, etc.)
```

**IMPORTANT**: Si le StartupDialog est créé puis détruit, sauvegarder le brand_code avant de fermer le dialog:

```python
# Avant que le dialog soit fermé/accepté
self.selected_brand_code = startup_dialog.get_selected_brand_code()

# Puis utiliser après
self.current_brand_code = self.selected_brand_code
```

---

### 4. **utils/session_manager.py** - Sauvegarder/Restaurer brand_code

#### Étape 4.1: Dans save_session()

Chercher la méthode `save_session()` et ajouter:

```python
def save_session(self, session_data: dict):
    """Sauvegarde une session"""

    # 🆕 Ajouter brand_code à la session
    if 'brand_code' not in session_data:
        session_data['brand_code'] = 'MNY'  # Default

    # ... reste du code save existant
```

#### Étape 4.2: Dans load_session()

Chercher la méthode `load_session()` et ajouter:

```python
def load_session(self, session_file: str):
    """Charge une session"""

    # ... code load existant qui lit session_data

    # 🆕 Récupérer brand_code de la session
    brand_code = session_data.get('brand_code', 'MNY')

    # Retourner le brand_code avec les autres données
    return {
        'brand_code': brand_code,
        # ... autres champs session
    }
```

#### Étape 4.3: Dans MainWindow, après load_session()

```python
def load_session_from_file(self, session_file):
    """Charge une session depuis un fichier"""

    session_data = self.session_manager.load_session(session_file)

    # 🆕 Restaurer la marque
    if 'brand_code' in session_data:
        self.set_brand_config(session_data['brand_code'])

    # ... reste du code load existant
```

---

### 5. **ui/settings_dialog.py** - Ajouter onglet Brand Rules

Chercher où les tabs sont ajoutés (chercher `QTabWidget` ou `addTab`):

```python
# Dans la méthode qui crée les tabs du settings dialog

from .brand_rules_tab import BrandRulesTab

# 🆕 Ajouter l'onglet Brand Rules
brand_rules_tab = BrandRulesTab(self)
self.tabs.addTab(brand_rules_tab, "🏷️  Règles de Marques")

# ... autres tabs existants
```

---

## ✅ Checklist d'Intégration

### Fichiers à Modifier

- [ ] `main.py` - Initialiser BrandRegistry
- [ ] `ui/main_window.py` - Modifier `init_processors()`, ajouter `set_brand_config()`
- [ ] `ui/main_window.py` - Récupérer brand_code depuis StartupDialog
- [ ] `utils/session_manager.py` - Save/Load brand_code
- [ ] `ui/settings_dialog.py` - Ajouter BrandRulesTab

### Tests à Effectuer

1. **Démarrage**:
   - [ ] App démarre sans erreur
   - [ ] BrandRegistry affiche 2 marques (MNY, ESSIE)

2. **Startup Dialog**:
   - [ ] Dropdown affiche "Maybelline New York (MNY)" et "ESSIE (ESSIE)"
   - [ ] Changement de marque → update des règles de validation
   - [ ] Sélection MNY → Règles affichent "YCA + 5 chiffres"
   - [ ] Sélection ESSIE → Règles affichent gammes CARE, GEL, etc.

3. **Validation MNY**:
   - [ ] Charger PDFs format YCA (ex: YCA12345.pdf)
   - [ ] Fichiers valides reconnus
   - [ ] Charger Excel MNY avec SHADE NUMBER numeric
   - [ ] Validation 4 DIGITS possible (si option activée)
   - [ ] UPC validation désactivée

4. **Validation ESSIE**:
   - [ ] Charger PDFs format ESSIE (ex: CARE_S26_1_3.pdf)
   - [ ] Fichiers valides reconnus (5 gammes + suffix SHADESTRIPS)
   - [ ] Charger Excel ESSIE avec SHADE NUMBER texte
   - [ ] SHADE NUMBER texte (ex: "2-IN-1 BASE & TOP COAT") validé
   - [ ] 4 DIGITS désactivé (colonne absente)
   - [ ] UPC validation désactivée

5. **Changement de Marque**:
   - [ ] Changer MNY → ESSIE pendant session
   - [ ] PDFs rechargés avec nouveau format
   - [ ] Excel rechargé avec nouvelles règles
   - [ ] Validation fonctionne correctement

6. **Sessions**:
   - [ ] Sauvegarder session avec brand_code
   - [ ] Charger session → brand_code restauré
   - [ ] Processors réinitialisés avec bonne marque

7. **Settings Tab**:
   - [ ] Onglet "Règles de Marques" visible
   - [ ] Cards MNY et ESSIE affichées
   - [ ] Colonnes requises/optionnelles correctes
   - [ ] Flags UPC/DIGITS corrects

---

## 🐛 Résolution de Problèmes Potentiels

### Erreur: "BrandRegistry not initialized"

**Cause**: BrandRegistry.register() pas appelé dans main.py

**Solution**: Vérifier que main.py initialise le registry au démarrage

---

### Erreur: "Module brand_configs not found"

**Cause**: Imports relatifs incorrects

**Solution**:
- Dans `main.py`: `from core.brand_configs.brand_registry import ...`
- Dans `ui/*.py`: `from ..core.brand_configs.brand_registry import ...`

---

### Excel: SHADE NUMBER converti en NaN pour ESSIE

**Cause**: Brand config pas passé à ExcelProcessor

**Solution**: Vérifier que `ExcelProcessor(brand_config=...)` reçoit bien la config ESSIE

---

### PDFs ESSIE marqués comme "invalides"

**Cause**: Brand config pas passé à PDFProcessor

**Solution**: Vérifier que `PDFProcessor(brand_config=...)` reçoit bien la config ESSIE

---

### Validation 4 DIGITS toujours active pour ESSIE

**Cause**: Validator ne vérifie pas `brand_config.requires_digits_validation()`

**Solution**: Déjà corrigé dans Phase 4, vérifier que validator reçoit brand_config

---

## 📊 Exemple de Flux Complet

```
1. User lance app
   → main.py initialise BrandRegistry (MNY + ESSIE)

2. StartupDialog s'ouvre
   → User sélectionne "ESSIE (ESSIE)"
   → Rules text affiche format ESSIE

3. User clique "Créer nouvelle session"
   → MainWindow.on_new_session_requested()
   → brand_code = 'ESSIE' récupéré
   → init_processors() avec ESSIEBrandConfig

4. User sélectionne dossier PDFs
   → PDFProcessor.load_folder()
   → is_valid_filename() utilise ESSIE regex
   → CARE_S26_1_3.pdf → VALIDE ✅
   → YCA12345.pdf → INVALIDE ❌

5. User sélectionne Excel ESSIE
   → ExcelProcessor.load_file()
   → column_types: SHADE NUMBER = str (texte)
   → "2-IN-1 BASE & TOP COAT" reste texte ✅

6. Validation
   → Validator.validate()
   → SHADE NUMBER texte validé dans PDF
   → 4 DIGITS skip (requires_digits_validation() = False)
   → Overall = True si SHADE NUMBER + SHADE NAME OK

7. User sauvegarde session
   → session_data['brand_code'] = 'ESSIE'
   → Fichier session.json créé

8. User recharge session plus tard
   → load_session() lit brand_code = 'ESSIE'
   → set_brand_config('ESSIE') appelé
   → Tous processors réinitialisés avec ESSIE
```

---

## 🎉 Feature Complétée !

Une fois tous les changements appliqués et testés, la feature Brand Validation Criteria sera entièrement fonctionnelle.

**Prochaines étapes suggérées**:
1. Tester avec vraies données MNY
2. Tester avec vraies données ESSIE
3. Ajouter d'autres marques si besoin (créer nouvelle classe config)
4. Documenter dans README.md
