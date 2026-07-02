"""
Fichier de compatibilité pour l'ancien import basecamp_processor
Redirige vers le nouveau package modulaire basecamp/

DÉPRÉCIÉ: Utilisez plutôt:
    from core.basecamp import BaseCampProcessor
"""

import warnings
from .basecamp import BaseCampProcessor as _BaseCampProcessor

# Avertissement de dépréciation
warnings.warn(
    "L'import 'from core.basecamp_processor import BaseCampProcessor' est déprécié. "
    "Utilisez plutôt 'from core.basecamp import BaseCampProcessor'",
    DeprecationWarning,
    stacklevel=2
)

# Alias pour compatibilité
BaseCampProcessor = _BaseCampProcessor
BasecampProcessor = _BaseCampProcessor  # Pour l'ancien code qui utilise cette variante

# Export pour import *
__all__ = ['BaseCampProcessor', 'BasecampProcessor']