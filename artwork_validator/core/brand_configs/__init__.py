"""
Brand Configuration System

Ce package contient les configurations de validation par marque pour le Litho Validator.
Chaque marque (MNY, ESSIE, etc.) a sa propre classe de configuration héritant de BaseBrandConfig.

Usage:
    from core.brand_configs.brand_registry import BrandRegistry
    from core.brand_configs.mny_config import MNYBrandConfig
    from core.brand_configs.essie_config import ESSIEBrandConfig

    # Enregistrer les marques
    registry = BrandRegistry()
    registry.register(MNYBrandConfig())
    registry.register(ESSIEBrandConfig())

    # Récupérer une configuration
    mny_config = registry.get_brand('MNY')
"""

from .base_config import BaseBrandConfig
from .brand_registry import BrandRegistry
from .mny_config import MNYBrandConfig
from .essie_config import ESSIEBrandConfig

__all__ = [
    'BaseBrandConfig',
    'BrandRegistry',
    'MNYBrandConfig',
    'ESSIEBrandConfig',
]
