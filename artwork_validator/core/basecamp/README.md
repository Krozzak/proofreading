# BaseCamp Integration Package

Package modulaire pour l'intégration BaseCamp dans L'Oréal Litho Validator.

## Architecture

```
basecamp/
├── __init__.py                 # Point d'entrée du package
├── processor.py               # Orchestrateur principal
├── file_matcher.py           # Stratégies de correspondance de fichiers
├── comment_manager.py        # Gestion intelligente des commentaires
├── navigator.py              # Navigation et scroll optimisé
├── reporter.py               # Rapports détaillés et statistiques
└── README.md                 # Cette documentation
```

## Modules

### 1. `processor.py` - Orchestrateur Principal

**Classe**: `BaseCampProcessor`

Responsabilités:

- Configuration du navigateur Edge
- Orchestration du workflow global
- Coordination entre tous les modules
- Interface principale pour l'utilisateur

```python
from litho_validator.core.basecamp import BaseCampProcessor

processor = BaseCampProcessor(session_manager)
processor.setup_browser()
processor.open_basecamp()
results = processor.process_approved_lithos()
```

### 2. `file_matcher.py` - Correspondance de Fichiers

**Classe**: `BaseCampFileMatcher`

Responsabilités:

- 5 stratégies de correspondance de fichiers
- Recherche intelligente par YCA, similarité, etc.
- Comptage et détection des fichiers sur la page

Stratégies:

1. `exact_name` - Correspondance exacte
2. `yca_code` - Recherche par code YCA
3. `partial_8chars` - Correspondance partielle (8 chars)
4. `flexible_number` - Recherche par numéros
5. `similarity_matching` - Correspondance par similarité

### 3. `comment_manager.py` - Gestion des Commentaires

**Classe**: `BaseCampCommentManager`

Responsabilités:

- Vérification des commentaires existants
- Préparation des commentaires APPROVED/REJECTED
- Ajout intelligent avec 4 stratégies différentes
- Gestion des conflits et doublons

### 4. `navigator.py` - Navigation

**Classe**: `BaseCampNavigator`

Responsabilités:

- Scroll optimisé pour charger tous les fichiers
- 5 stratégies de retour aux listes de fichiers
- Gestion des timeouts et erreurs de navigation
- Détection intelligente du chargement de page

### 5. `reporter.py` - Rapports

**Classe**: `BaseCampReporter`

Responsabilités:

- Génération de rapports JSON détaillés
- Calcul de statistiques avancées
- Recommandations automatiques
- Sauvegarde de rapports HTML et texte

## Usage

### Import Simple

```python
from litho_validator.core.basecamp import BaseCampProcessor
```

### Import Modulaire

```python
from litho_validator.core.basecamp import (
    BaseCampProcessor,
    BaseCampFileMatcher,
    BaseCampCommentManager,
    BaseCampNavigator,
    BaseCampReporter
)
```

### Workflow Complet

```python
# 1. Initialisation
processor = BaseCampProcessor(session_manager, logger)

# 2. Configuration du navigateur
if not processor.setup_browser():
    print("Erreur configuration navigateur")
    return

# 3. Ouverture BaseCamp
if not processor.open_basecamp():
    print("Erreur ouverture BaseCamp")
    return

# 4. Configuration de la page (après navigation utilisateur)
if not processor.setup_basecamp_page():
    print("Erreur configuration page")
    return

# 5. Traitement des lithographies
results = processor.process_approved_lithos()

# 6. Nettoyage
processor.cleanup()
```

## Avantages de cette Architecture

### 1. **Séparation des Responsabilités**

- Chaque module a une responsabilité claire et unique
- Facilite les tests unitaires
- Maintenance plus simple

### 2. **Réutilisabilité**

- Modules peuvent être utilisés indépendamment
- Facilite l'extension avec de nouvelles fonctionnalités
- Code plus modulaire

### 3. **Maintenabilité**

- Fichiers plus petits et focalisés
- Bugs plus faciles à identifier et corriger
- Évolutions plus simples à implémenter

### 4. **Testabilité**

- Chaque module peut être testé isolément
- Mocks plus faciles à créer
- Tests plus rapides et fiables

## Migration depuis l'Ancienne Version

L'ancien `basecamp_processor.py` (1300+ lignes) a été refactorisé en 5 modules spécialisés:

```python
# Ancien import
from core.basecamp_processor import BaseCampProcessor

# Nouveau import (compatible)
from core.basecamp import BaseCampProcessor
```

La compatibilité est maintenue grâce au `__init__.py`.

## Bonnes Pratiques

### 1. **Gestion d'Erreurs**

Chaque module gère ses propres erreurs et les remonte proprement.

### 2. **Logging**

Utilisation cohérente du logger dans tous les modules.

### 3. **Configuration**

Configuration centralisée dans le processeur principal.

### 4. **Documentation**

Chaque classe et méthode importante est documentée.

## Extensibilité

Pour ajouter une nouvelle fonctionnalité:

1. Créer un nouveau module dans le dossier `basecamp/`
2. L'importer dans `__init__.py`
3. L'intégrer dans le `processor.py` si nécessaire

Exemple pour un nouveau module `validator.py`:

```python
# basecamp/validator.py
class BaseCampValidator:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def validate_file_format(self, file_element):
        # Logique de validation
        pass

# basecamp/__init__.py
from .validator import BaseCampValidator
__all__.append('BaseCampValidator')

# Usage
from litho_validator.core.basecamp import BaseCampValidator
```

## Support et Maintenance

- **Version**: 2.0.0
- **Compatibilité**: Python 3.10+
- **Dépendances**: Selenium, PyQt6
- **Tests**: À implémenter dans `tests/basecamp/`

Pour les questions ou problèmes, se référer aux logs détaillés générés par le module `reporter.py`.
