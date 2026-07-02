"""
Package BaseCamp pour L'Oréal Litho Validator
===========================================

Ce package contient tous les modules nécessaires pour l'intégration BaseCamp:

- processor: Module principal d'orchestration
- file_matcher: Stratégies de correspondance de fichiers
- comment_manager: Gestion intelligente des commentaires
- navigator: Navigation et retour aux listes
- reporter: Génération de rapports détaillés

Usage:
    from litho_validator.core.basecamp import BaseCampProcessor

    processor = BaseCampProcessor(session_manager)
    processor.setup_browser()
    processor.open_basecamp()
    results = processor.process_approved_lithos()
"""

from .processor import BaseCampProcessor, BaseCampProcessorLegacy
from .file_matcher import BaseCampFileMatcher
from .comment_manager import BaseCampCommentManager
from .navigator import BaseCampNavigator
from .reporter import BaseCampReporter

# Version du package
__version__ = "2.0.0"

# Export des classes principales
__all__ = [
    'BaseCampProcessor',
    'BaseCampProcessorLegacy',
    'BaseCampFileMatcher',
    'BaseCampCommentManager',
    'BaseCampNavigator',
    'BaseCampReporter'
]

# Compatibilité avec l'ancien import
# Permet d'importer avec: from core.basecamp_processor import BaseCampProcessor
BaseCampProcessor = BaseCampProcessor