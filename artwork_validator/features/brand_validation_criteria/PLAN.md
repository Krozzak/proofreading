# PLAN - Brand Validation Criteria Feature

**Feature Name**: Brand Validation Criteria
**Created**: 2025-11-21
**Estimated Duration**: 12-16h
**Status**: 📝 Planning

---

## 🎯 Objectif

Rendre le Litho Validator compatible avec plusieurs marques (MNY, ESSIE, etc.) en implémentant un système de configuration par marque extensible. Actuellement, le validateur est hardcodé pour Maybelline New York (MNY) uniquement.

---

## 📋 Contexte & Requis

### Problème Actuel
- Validateur hardcodé pour **MNY uniquement**
- Format codes: `YCA + 5 chiffres` (ex: `YCA12345`)
- Colonnes Excel hardcodées
- Validation PDF spécifique MNY

### Nouvelle Marque: ESSIE
- **Format codes différent**: `[GAMME]_S[SEASON]_[INDEX]_[TOTAL]`
- **Exemples**: `CARE_S26_1_3`, `GEL_S26_2_6`, `ESSIE_S26_4_6`
- **Gammes supportées**: CARE, GEL, NSTUDIO, ESSIE, EXPRESS
- **Suffix optionnel**: `_SHADESTRIPS` (ex: `CARE_S26_1_3_SHADESTRIPS`)
- **Colonnes Excel**: Structure différente (SHADE NUMBER = texte, pas de 4 DIGITS)
- **Validation UPC**: Désactivée (UPC pas dans les PDFs)

### Requis Fonctionnels
1. ✅ **Structure extensible** pour ajouter facilement de nouvelles marques
2. ✅ **Configuration par marque**:
   - Format nom de fichier PDF
   - Extraction code litho
   - Colonnes Excel requises/optionnelles
   - Types de données colonnes
   - Règles de validation spécifiques
3. ✅ **Sélection marque** dans UI de démarrage
4. ✅ **Visualisation règles** dans Settings
5. ✅ **Validation UPC désactivable** par marque
6. ✅ **Validation 4 DIGITS désactivable** par marque

### Règles Communes (Conservées)
- Validation SHADE NUMBER (adapté par marque)
- Validation SHADE NAME
- Gestion équivalences (WTP/WATERPROOF)
- Gestion texte normalisé (retours à ligne, espaces)
- Gestion CUBBY/FRAME/SPACE_SAVER

---

## 🏗️ Architecture Proposée

### Structure Fichiers

```
litho_validator/
├─ core/
│  ├─ brand_configs/              # 🆕 Nouveau package
│  │  ├─ __init__.py
│  │  ├─ base_config.py           # BaseBrandConfig (abstract)
│  │  ├─ brand_registry.py        # BrandRegistry (factory)
│  │  ├─ mny_config.py            # MNY configuration
│  │  └─ essie_config.py          # ESSIE configuration
│  │
│  ├─ excel_processor.py          # 🔧 Modifié (accept brand_config)
│  ├─ pdf_processor.py            # 🔧 Modifié (accept brand_config)
│  └─ validator.py                # 🔧 Modifié (brand-specific validation)
│
├─ ui/
│  ├─ startup_dialog.py           # 🔧 Modifié (brand selection)
│  ├─ settings_dialog.py          # 🔧 Modifié (brand rules tab)
│  └─ main_window.py              # 🔧 Modifié (pass brand_config)
│
└─ utils/
   └─ session_manager.py          # 🔧 Modifié (store brand_code)
```

---

## 📊 Phases d'Implémentation

### **Phase 1: 🔧 Brand Configuration System** (Backend)
**Durée**: 3-4h
**Type**: Backend (schemas + business logic)
**Test**: Compilation uniquement

#### Livrables:
1. `core/brand_configs/__init__.py` (package initialization)
2. `core/brand_configs/base_config.py` (abstract class)
3. `core/brand_configs/brand_registry.py` (factory + registry)
4. `core/brand_configs/mny_config.py` (MNY implementation)
5. `core/brand_configs/essie_config.py` (ESSIE implementation)

#### Schema: `BaseBrandConfig` (Abstract)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseBrandConfig(ABC):
    """Base configuration class for brand-specific validation rules"""

    @abstractmethod
    def get_brand_code(self) -> str:
        """Return brand code (MNY, ESSIE, etc.)"""
        pass

    @abstractmethod
    def get_brand_display_name(self) -> str:
        """Return display name (Maybelline New York, ESSIE, etc.)"""
        pass

    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Return list of required Excel columns"""
        pass

    @abstractmethod
    def get_optional_columns(self) -> List[str]:
        """Return list of optional Excel columns"""
        pass

    @abstractmethod
    def get_column_types(self) -> Dict[str, Any]:
        """Return expected column types (str, 'numeric', etc.)"""
        pass

    @abstractmethod
    def is_valid_filename(self, filename: str) -> bool:
        """Validate PDF filename format"""
        pass

    @abstractmethod
    def extract_litho_code(self, filename: str) -> Optional[str]:
        """Extract litho code from filename"""
        pass

    @abstractmethod
    def is_valid_litho_code(self, code: str) -> bool:
        """Validate litho code format"""
        pass

    @abstractmethod
    def requires_upc_validation(self) -> bool:
        """Return True if UPC validation is required for this brand"""
        pass

    @abstractmethod
    def requires_digits_validation(self) -> bool:
        """Return True if 4 DIGITS validation is required for this brand"""
        pass

    @abstractmethod
    def get_validation_description(self) -> str:
        """Return human-readable validation rules description"""
        pass

    # Méthode non-abstraite (commune à toutes les marques)
    def get_validation_rules(self) -> Dict[str, Any]:
        """Return dict of validation rules for display"""
        return {
            'brand_code': self.get_brand_code(),
            'brand_name': self.get_brand_display_name(),
            'filename_pattern': self.get_validation_description(),
            'required_columns': self.get_required_columns(),
            'optional_columns': self.get_optional_columns(),
            'requires_upc': self.requires_upc_validation(),
            'requires_digits': self.requires_digits_validation()
        }
```

#### Schema: `BrandRegistry` (Factory Pattern)

```python
from typing import Dict, List, Optional
from .base_config import BaseBrandConfig

class BrandRegistry:
    """Registry for managing brand configurations"""

    _brands: Dict[str, BaseBrandConfig] = {}

    @classmethod
    def register(cls, brand_config: BaseBrandConfig):
        """Register a brand configuration"""
        brand_code = brand_config.get_brand_code()
        cls._brands[brand_code] = brand_config
        print(f"✅ Brand registered: {brand_config.get_brand_display_name()} ({brand_code})")

    @classmethod
    def get_brand(cls, brand_code: str) -> Optional[BaseBrandConfig]:
        """Get brand configuration by code"""
        return cls._brands.get(brand_code)

    @classmethod
    def get_all_brands(cls) -> List[BaseBrandConfig]:
        """Get all registered brands"""
        return list(cls._brands.values())

    @classmethod
    def get_brand_codes(cls) -> List[str]:
        """Get all brand codes"""
        return list(cls._brands.keys())

    @classmethod
    def get_brand_names(cls) -> List[str]:
        """Get all brand display names"""
        return [brand.get_brand_display_name() for brand in cls._brands.values()]
```

#### Implementation: `MNYBrandConfig`

```python
import re
from typing import List, Dict, Any, Optional
from .base_config import BaseBrandConfig

class MNYBrandConfig(BaseBrandConfig):
    """Configuration for Maybelline New York (MNY)"""

    def get_brand_code(self) -> str:
        return "MNY"

    def get_brand_display_name(self) -> str:
        return "Maybelline New York"

    def get_required_columns(self) -> List[str]:
        return [
            'LITHO', 'DECRIPTION', 'UPC SEQUENCE', 'UPC POSITION', 'UPC',
            'PRODUCT DESCRIPTION', 'SHADE NAME', 'SHADE NUMBER',
            'PRODUCT FACING SL', '4 DIGITS'
        ]

    def get_optional_columns(self) -> List[str]:
        return ['NEW', 'STATUS', 'PRODUCT', 'TIER', 'SEASON']

    def get_column_types(self) -> Dict[str, Any]:
        return {
            'LITHO': str,
            'DECRIPTION': str,
            'UPC SEQUENCE': str,
            'UPC POSITION': str,
            'UPC': str,
            'PRODUCT DESCRIPTION': str,
            'SHADE NAME': str,
            'SHADE NUMBER': 'numeric',  # MNY: numeric
            'PRODUCT FACING SL': 'numeric',
            '4 DIGITS': 'numeric',
            'NEW': str,
            'STATUS': str,
            'PRODUCT': str,
            'TIER': str,
            'SEASON': str,
        }

    def is_valid_filename(self, filename: str) -> bool:
        """Validate MNY filename format: YCA + 5 digits"""
        if len(filename) < 8:
            return False
        code = filename[:8]
        return code.startswith('YCA') and code[3:].isdigit()

    def extract_litho_code(self, filename: str) -> Optional[str]:
        """Extract YCA code from filename (first 8 characters)"""
        if len(filename) < 8:
            return None
        code = filename[:8]
        return code if self.is_valid_litho_code(code) else None

    def is_valid_litho_code(self, code: str) -> bool:
        """Validate YCA code format"""
        if len(code) != 8:
            return False
        return code.startswith('YCA') and code[3:].isdigit()

    def requires_upc_validation(self) -> bool:
        """MNY: UPC validation désactivée (pas dans PDFs)"""
        return False  # ⚠️ DÉSACTIVÉ selon conversation finale

    def requires_digits_validation(self) -> bool:
        """MNY: 4 DIGITS validation activée (optionnelle selon settings)"""
        return True

    def get_validation_description(self) -> str:
        return (
            "Format MNY:\n"
            "• Pattern: YCA + 5 chiffres\n"
            "• Exemples: YCA12345, YCA98765\n"
            "• Longueur: 8 caractères\n"
            "• Colonnes spéciales: 4 DIGITS (numeric), SHADE NUMBER (numeric)"
        )
```

#### Implementation: `ESSIEBrandConfig`

```python
import re
from typing import List, Dict, Any, Optional
from .base_config import BaseBrandConfig

class ESSIEBrandConfig(BaseBrandConfig):
    """Configuration for ESSIE"""

    # Gammes supportées par ESSIE
    SUPPORTED_GAMMES = ['CARE', 'GEL', 'NSTUDIO', 'ESSIE', 'EXPRESS']

    def get_brand_code(self) -> str:
        return "ESSIE"

    def get_brand_display_name(self) -> str:
        return "ESSIE"

    def get_required_columns(self) -> List[str]:
        return [
            'LITHO', 'DECRIPTION', 'UPC SEQUENCE', 'UPC POSITION', 'UPC',
            'PRODUCT DESCRIPTION', 'SHADE NAME', 'SHADE NUMBER',
            'PRODUCT FACING SL'
            # Note: Pas de '4 DIGITS' pour ESSIE
        ]

    def get_optional_columns(self) -> List[str]:
        return ['NEW', 'STATUS', 'PRODUCT', 'TIER', 'SEASON', 'STRIP TYPE']

    def get_column_types(self) -> Dict[str, Any]:
        return {
            'LITHO': str,
            'DECRIPTION': str,
            'UPC SEQUENCE': str,
            'UPC POSITION': str,
            'UPC': str,
            'PRODUCT DESCRIPTION': str,
            'SHADE NAME': str,
            'SHADE NUMBER': str,  # ESSIE: texte, pas numeric!
            'PRODUCT FACING SL': 'numeric',
            # Optionnelles
            'NEW': str,
            'STATUS': str,
            'PRODUCT': str,
            'TIER': str,
            'SEASON': str,
            'STRIP TYPE': str,
        }

    def is_valid_filename(self, filename: str) -> bool:
        """
        Validate ESSIE filename format: [GAMME]_S[DIGITS]_[DIGITS]_[DIGITS]
        Exemples: CARE_S26_1_3, GEL_S26_2_6_SHADESTRIPS
        """
        # Pattern: [GAMME]_S[DIGITS]_[DIGITS]_[DIGITS] (avec suffix optionnel)
        pattern = r'^(' + '|'.join(self.SUPPORTED_GAMMES) + r')_S\d+_\d+_\d+(_SHADESTRIPS)?'
        return bool(re.match(pattern, filename, re.IGNORECASE))

    def extract_litho_code(self, filename: str) -> Optional[str]:
        """
        Extract ESSIE litho code from filename
        CARE_S26_1_3_SHADESTRIPS.pdf → CARE_S26_1_3
        """
        # Pattern pour extraire le code (sans suffix SHADESTRIPS et extension)
        pattern = r'^((' + '|'.join(self.SUPPORTED_GAMMES) + r')_S\d+_\d+_\d+)'
        match = re.match(pattern, filename, re.IGNORECASE)

        if match:
            code = match.group(1)
            return code if self.is_valid_litho_code(code) else None

        return None

    def is_valid_litho_code(self, code: str) -> bool:
        """
        Validate ESSIE litho code format
        Exemples valides: CARE_S26_1_3, GEL_S26_2_6, ESSIE_S26_4_6
        """
        pattern = r'^(' + '|'.join(self.SUPPORTED_GAMMES) + r')_S\d+_\d+_\d+$'
        return bool(re.match(pattern, code, re.IGNORECASE))

    def requires_upc_validation(self) -> bool:
        """ESSIE: UPC validation désactivée (pas dans PDFs)"""
        return False

    def requires_digits_validation(self) -> bool:
        """ESSIE: Pas de colonne 4 DIGITS"""
        return False

    def get_validation_description(self) -> str:
        return (
            "Format ESSIE:\n"
            "• Pattern: [GAMME]_S[SEASON]_[INDEX]_[TOTAL]\n"
            "• Exemples: CARE_S26_1_3, GEL_S26_2_6, ESSIE_S26_4_6\n"
            f"• Gammes supportées: {', '.join(self.SUPPORTED_GAMMES)}\n"
            "• Suffix optionnel: _SHADESTRIPS\n"
            "• Colonnes spéciales: SHADE NUMBER (texte, pas numeric)"
        )

    def get_supported_gammes(self) -> List[str]:
        """Return list of supported gammes for ESSIE"""
        return self.SUPPORTED_GAMMES.copy()
```

---

### **Phase 2: 🔧 Update Excel Processor** (Backend)
**Durée**: 2-3h
**Type**: Backend (refactoring)
**Test**: Compilation + Relecture code

#### Modifications `core/excel_processor.py`:

**Changements principaux**:
1. Ajouter paramètre `brand_config` au `__init__`
2. Stocker `_current_file_path` pour reload automatique
3. Méthode `set_brand_config()` pour changer marque dynamiquement
4. Utiliser `brand_config.get_required_columns()`
5. Utiliser `brand_config.get_column_types()`
6. Utiliser `brand_config.is_valid_litho_code()` dans `_validate_data_quality()`

**Code clé**:
```python
def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
    self.data: Optional[pd.DataFrame] = None
    self.logger = logging.getLogger(__name__)
    self._current_file_path: Optional[str] = None

    # Brand configuration
    if brand_config is None:
        # Default to MNY
        from .brand_configs.brand_registry import BrandRegistry
        brand_config = BrandRegistry().get_brand('MNY')

    self.brand_config = brand_config
    self.required_columns = brand_config.get_required_columns()
    self.column_types = brand_config.get_column_types()

    self.logger.info(f"📊 ExcelProcessor initialized for: {self.brand_config.get_brand_display_name()}")

def set_brand_config(self, brand_config: BaseBrandConfig):
    """Change brand configuration and reload data if file was loaded"""
    old_brand = self.brand_config.get_brand_display_name()

    # Save current file path
    current_file = self._current_file_path

    # Update configuration
    self.brand_config = brand_config
    self.required_columns = brand_config.get_required_columns()
    self.column_types = brand_config.get_column_types()

    new_brand = brand_config.get_brand_display_name()
    self.logger.info(f"🔄 Configuration changed from {old_brand} to {new_brand}")

    # Reload file with new configuration
    if current_file and os.path.exists(current_file):
        self.logger.info(f"🔄 Reloading Excel file with {new_brand} configuration...")
        success = self.load_file(current_file)
        if success:
            self.logger.info(f"✅ File reloaded successfully for {new_brand}")
```

---

### **Phase 3: 🔧 Update PDF Processor** (Backend)
**Durée**: 2-3h
**Type**: Backend (refactoring)
**Test**: Compilation + Relecture code

#### Modifications `core/pdf_processor.py`:

**Changements principaux**:
1. Ajouter paramètre `brand_config` au `__init__`
2. Méthode `set_brand_config()` pour changer marque dynamiquement
3. Remplacer `_is_valid_filename()` par `brand_config.is_valid_filename()`
4. Remplacer `_extract_litho_code()` par `brand_config.extract_litho_code()`
5. Supprimer `_is_valid_code_format()` (maintenant dans brand_config)
6. Update logging pour afficher marque

**Code clé**:
```python
def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
    self.current_pdf = None
    self.pdf_files = []
    self.current_index = 0
    self.folder_path = ""
    self.invalid_files = []

    # Brand configuration
    if brand_config is None:
        from .brand_configs.brand_registry import BrandRegistry
        brand_config = BrandRegistry().get_brand('MNY')

    self.brand_config = brand_config
    self.logger = logging.getLogger(__name__)

    self.logger.info(f"📄 PDFProcessor initialized for: {self.brand_config.get_brand_display_name()}")

def _is_valid_filename(self, filename):
    """Validate filename using brand configuration"""
    return self.brand_config.is_valid_filename(filename)

def _extract_litho_code(self, filename):
    """Extract litho code using brand configuration"""
    return self.brand_config.extract_litho_code(filename)
```

---

### **Phase 4: 🔧 Update Validator** (Backend)
**Durée**: 2-3h
**Type**: Backend (refactoring)
**Test**: Compilation + Relecture code

#### Modifications `core/validator.py`:

**Changements principaux**:
1. Ajouter paramètre `brand_config` au `__init__`
2. Désactiver UPC validation (toujours True)
3. Validation 4 DIGITS conditionnelle selon marque
4. Update `validate()` pour respecter `requires_upc_validation()` et `requires_digits_validation()`

**Code clé**:
```python
def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
    self.equivalences = {
        'WTP': 'WATERPROOF',
        'WATERPROOF': 'WTP'
    }
    self.check_digits = False  # Controllé via settings UI
    self.text_normalizer = TextNormalizer()
    self.brand_config = brand_config

def validate(self, pdf_text: str, excel_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # ... existing code ...

    for row in excel_data:
        validation_details = {
            'upc_validation': True,  # ⚠️ TOUJOURS True (UPC pas validé)
            # ... autres champs
        }

        if not (is_frame or is_space_saver):
            # Validation SHADE NUMBER
            shade_number = row.get('SHADE NUMBER')
            has_shade_number = shade_number is not None and self._safe_str(shade_number)
            if has_shade_number:
                validation_details['shade_number'] = self.validate_shade_number(pdf_text, shade_number)

            # Validation SHADE NAME
            shade_name = row.get('SHADE NAME')
            has_shade_name = shade_name is not None and self._safe_str(shade_name)
            if has_shade_name:
                validation_details['shade_name'] = self.validate_shade_name(pdf_text, shade_name)

            # ❌ UPC: Toujours valide (pas vérifié)
            validation_details['upc_validation'] = True

            # Validation 4 DIGITS (conditionnelle selon marque)
            digits = row.get('4 DIGITS')
            has_digits = digits is not None and self._safe_str(digits) and self._safe_str(digits).upper() != 'NAN'

            # Vérifier si la marque requiert validation des 4 DIGITS
            should_validate_digits = True
            if self.brand_config:
                should_validate_digits = self.brand_config.requires_digits_validation()

            if self.check_digits and should_validate_digits and has_digits:
                validation_details['digits'] = self.validate_digits(pdf_text, digits)
            else:
                validation_details['digits'] = True

            # VALIDATION GLOBALE (exclut UPC, inclut DIGITS si marque le requiert)
            validation_criteria = []
            if has_shade_number:
                validation_criteria.append(validation_details['shade_number'])
            if has_shade_name:
                validation_criteria.append(validation_details['shade_name'])
            if self.check_digits and should_validate_digits and has_digits:
                validation_criteria.append(validation_details['digits'])

            validation_details['overall'] = all(validation_criteria) if validation_criteria else True
```

---

### **Phase 5: 🎨 Update Startup Dialog UI** (Frontend)
**Durée**: 3-4h
**Type**: Frontend (UI modification)
**Test**: Test visuel immédiat

#### Modifications `ui/startup_dialog.py`:

**Ajouts UI**:
1. Dropdown "Select Brand" dans `create_new_session_group()`
2. Section "Brand Validation Rules" (read-only QTextEdit)
3. Signal `new_session_requested` modifié pour inclure `brand_code`
4. Méthode `update_brand_rules_display()` pour afficher règles

**Code clé**:
```python
def create_new_session_group(self):
    # ... existing code ...

    # Brand selection section
    brand_section = QGroupBox("🏷️  Brand Selection")
    brand_layout = QVBoxLayout()

    # Brand combo
    brand_select_layout = QHBoxLayout()
    brand_label = QLabel("Select Brand:")
    brand_label.setStyleSheet("font-weight: 600;")

    self.brand_combo = QComboBox()
    self.brand_combo.setStyleSheet(f"""
        QComboBox {{
            padding: 6px;
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            background-color: white;
        }}
    """)

    # Populate brands from registry
    from core.brand_configs.brand_registry import BrandRegistry
    for brand in BrandRegistry.get_all_brands():
        display_text = f"{brand.get_brand_display_name()} ({brand.get_brand_code()})"
        self.brand_combo.addItem(display_text, brand.get_brand_code())

    brand_select_layout.addWidget(brand_label)
    brand_select_layout.addWidget(self.brand_combo)
    brand_layout.addLayout(brand_select_layout)

    # Brand rules description
    rules_label = QLabel("Validation Rules:")
    rules_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
    brand_layout.addWidget(rules_label)

    self.brand_rules_text = QTextEdit()
    self.brand_rules_text.setReadOnly(True)
    self.brand_rules_text.setMaximumHeight(120)
    self.brand_rules_text.setStyleSheet(f"""
        QTextEdit {{
            background-color: {LorealStyles.COLORS['background']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            padding: 8px;
            font-size: 10px;
            font-family: 'Consolas', 'Courier New', monospace;
        }}
    """)
    brand_layout.addWidget(self.brand_rules_text)

    brand_section.setLayout(brand_layout)
    layout.addWidget(brand_section)

    # Connect signal
    self.brand_combo.currentIndexChanged.connect(self.update_brand_rules_display)

    # Initial display
    self.update_brand_rules_display()

def update_brand_rules_display(self):
    """Update brand rules text when brand selection changes"""
    brand_code = self.brand_combo.currentData()
    if brand_code:
        from core.brand_configs.brand_registry import BrandRegistry
        brand = BrandRegistry.get_brand(brand_code)
        if brand:
            self.brand_rules_text.setText(brand.get_validation_description())

def get_selected_brand_code(self) -> str:
    """Return currently selected brand code"""
    return self.brand_combo.currentData()
```

---

### **Phase 6: 🎨 Settings Page - Brand Rules Tab** (Frontend)
**Durée**: 2-3h
**Type**: Frontend (new tab)
**Test**: Test visuel immédiat

#### Nouveau fichier: `ui/brand_rules_tab.py`

**UI Components**:
- Liste de toutes les marques configurées
- Cards expandables par marque
- Affichage règles complètes
- Colonnes requises/optionnelles
- Flags (UPC validation, 4 DIGITS)

**Code clé**:
```python
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                            QTextEdit, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from core.brand_configs.brand_registry import BrandRegistry
from utils.styles import LorealStyles

class BrandRulesTab(QWidget):
    """Tab for displaying brand validation rules"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("Brand Validation Rules")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(header)

        # Description
        desc = QLabel("View validation rules and column requirements for each configured brand.")
        desc.setStyleSheet("color: gray; margin-bottom: 8px;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Scroll area for brands
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Add card for each brand
        for brand in BrandRegistry.get_all_brands():
            card = self.create_brand_card(brand)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def create_brand_card(self, brand):
        """Create a card widget for a brand"""
        card = QGroupBox(f"{brand.get_brand_display_name()} ({brand.get_brand_code()})")
        card.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                border: 2px solid {LorealStyles.COLORS['primary']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                border-radius: 3px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Validation rules
        rules_section = self.create_section("📋 Validation Rules",
                                           brand.get_validation_description(),
                                           is_code=True)
        layout.addWidget(rules_section)

        # Required columns
        req_cols = ', '.join(brand.get_required_columns())
        req_section = self.create_section("✅ Required Columns", req_cols,
                                         color=LorealStyles.COLORS['success'])
        layout.addWidget(req_section)

        # Optional columns
        opt_cols = ', '.join(brand.get_optional_columns())
        opt_section = self.create_section("⚪ Optional Columns", opt_cols,
                                         color="gray", italic=True)
        layout.addWidget(opt_section)

        # Validation flags
        flags_text = f"UPC Validation: {'✅ Enabled' if brand.requires_upc_validation() else '❌ Disabled'}\n"
        flags_text += f"4 DIGITS Validation: {'✅ Enabled' if brand.requires_digits_validation() else '❌ Disabled'}"
        flags_section = self.create_section("🚩 Validation Flags", flags_text)
        layout.addWidget(flags_section)

        card.setLayout(layout)
        return card

    def create_section(self, title, content, color=None, italic=False, is_code=False):
        """Create a section with title and content"""
        section = QFrame()
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)

        # Title
        title_label = QLabel(title)
        title_style = "font-weight: 600; font-size: 11px;"
        if color:
            title_style += f" color: {color};"
        title_label.setStyleSheet(title_style)
        section_layout.addWidget(title_label)

        # Content
        if is_code:
            content_widget = QTextEdit()
            content_widget.setReadOnly(True)
            content_widget.setPlainText(content)
            content_widget.setMaximumHeight(100)
            content_widget.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {LorealStyles.COLORS['background']};
                    border: 1px solid {LorealStyles.COLORS['border']};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 10px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
            """)
        else:
            content_widget = QLabel(content)
            content_widget.setWordWrap(True)
            style = "font-size: 10px; padding: 4px;"
            if color:
                style += f" color: {color};"
            if italic:
                style += " font-style: italic;"
            content_widget.setStyleSheet(style)

        section_layout.addWidget(content_widget)
        section.setLayout(section_layout)
        return section
```

#### Modification `ui/settings_dialog.py`:

```python
from .brand_rules_tab import BrandRulesTab

def __init__(self, parent=None):
    # ... existing code ...

    # Add Brand Rules tab
    brand_rules_tab = BrandRulesTab(self)
    self.tabs.addTab(brand_rules_tab, "🏷️  Brand Rules")
```

---

### **Phase 7: ⚙️ Integration & Main Window Update** (Mixed)
**Durée**: 2-3h
**Type**: Integration (backend + frontend)
**Test**: Test fonctionnel complet

#### Modifications `main.py`:

```python
from core.brand_configs.brand_registry import BrandRegistry
from core.brand_configs.mny_config import MNYBrandConfig
from core.brand_configs.essie_config import ESSIEBrandConfig

def main():
    # Initialize brand registry
    registry = BrandRegistry()
    registry.register(MNYBrandConfig())
    registry.register(ESSIEBrandConfig())

    # ... rest of main
```

#### Modifications `ui/main_window.py`:

```python
def init_processors(self):
    """Initialize processors with brand configuration"""
    self.current_brand_config = self.brand_registry.get_brand(self.current_brand_name)

    self.pdf_processor = PDFProcessor(brand_config=self.current_brand_config)
    self.excel_processor = ExcelProcessor(brand_config=self.current_brand_config)
    self.validator = LithoValidator(brand_config=self.current_brand_config)

    self.report_generator = ReportGenerator(pdf_processor=self.pdf_processor)
    self.session_manager = SessionManager()

def set_brand_config(self, brand_name: str):
    """Change brand configuration for all processors"""
    brand_config = self.brand_registry.get_brand(brand_name)

    if brand_config:
        self.current_brand_name = brand_name
        self.current_brand_config = brand_config

        # Update all processors
        self.pdf_processor.set_brand_config(brand_config)
        self.excel_processor.set_brand_config(brand_config)
        self.validator.brand_config = brand_config

        self.logger.info(f"✅ Brand configuration changed to: {brand_name}")
```

#### Modifications `utils/session_manager.py`:

```python
def save_session(self, session_data):
    # Add brand_code to session data
    session_data['brand_code'] = self.current_brand_code
    # ... existing save logic

def load_session(self, session_file):
    # Load brand_code from session
    brand_code = session_data.get('brand_code', 'MNY')  # Default to MNY
    self.current_brand_code = brand_code
    # ... existing load logic
```

---

## ✅ Test Checklist

### Phase 1 Tests (Backend)
- [ ] Compilation sans erreurs
- [ ] `MNYBrandConfig` instanciable
- [ ] `ESSIEBrandConfig` instanciable
- [ ] `BrandRegistry.register()` fonctionne
- [ ] `BrandRegistry.get_brand()` retourne bonne config

### Phase 2-3-4 Tests (Backend Processors)
- [ ] ExcelProcessor accepte brand_config
- [ ] PDFProcessor accepte brand_config
- [ ] Validator accepte brand_config
- [ ] `set_brand_config()` fonctionne sans crash

### Phase 5 Tests (Startup Dialog)
- [ ] Dropdown marques visible
- [ ] Marques MNY + ESSIE affichées
- [ ] Changement marque → update rules text
- [ ] Rules text affiche bon format
- [ ] Bouton "New Session" passe brand_code

### Phase 6 Tests (Settings Tab)
- [ ] Onglet "Brand Rules" visible
- [ ] Cards MNY + ESSIE affichées
- [ ] Required columns affichées
- [ ] Optional columns affichées
- [ ] Flags UPC/DIGITS corrects

### Phase 7 Tests (Integration)
- [ ] App démarre sans crash
- [ ] Brand registry initialisé au startup
- [ ] Sélection MNY → load PDFs MNY format (YCA)
- [ ] Sélection ESSIE → load PDFs ESSIE format (CARE_, GEL_, etc.)
- [ ] Excel MNY → SHADE NUMBER = numeric
- [ ] Excel ESSIE → SHADE NUMBER = texte
- [ ] Validation UPC désactivée pour les 2 marques
- [ ] Validation 4 DIGITS → seulement pour MNY
- [ ] Session save → brand_code sauvegardé
- [ ] Session load → brand_code restauré

---

## 📈 Métriques de Succès

1. ✅ **Extensibilité**: Ajouter nouvelle marque = créer 1 classe config uniquement
2. ✅ **Backward Compatibility**: MNY fonctionne comme avant
3. ✅ **ESSIE Support**: Tous formats ESSIE reconnus et validés
4. ✅ **UX**: User peut switcher marques sans restart app
5. ✅ **Documentation**: Settings affiche règles claires par marque

---

## 🚨 Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Breaking changes MNY | HAUT | Tests exhaustifs backward compatibility |
| Performance (reload Excel/PDF) | MOYEN | Optimiser set_brand_config() |
| UI freeze (reload) | MOYEN | Threading/async si nécessaire |
| Session corruption | MOYEN | Migration script pour anciennes sessions |
| Colonnes Excel manquantes | MOYEN | Validation robuste + messages clairs |

---

## 📝 Notes Implementation

- **Priorité**: Phase 1-2-3-4 (Backend) avant Phase 5-6 (Frontend)
- **Tests**: User teste après chaque phase frontend (5, 6)
- **Commit strategy**: 1 commit par phase complétée
- **Documentation**: Update ARCHITECTURE.md après Phase 7

---

**Next Step**: Valider ce plan avec l'utilisateur avant de commencer implémentation Phase 1.
