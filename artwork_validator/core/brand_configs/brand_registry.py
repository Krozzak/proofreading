# core/brand_configs/brand_registry.py

import logging
from typing import Dict, List, Optional, Any
from .base_config import BaseBrandConfig


class BrandRegistry:
    """
    Registry pattern pour gérer les configurations de marque.

    Cette classe singleton permet d'enregistrer et de récupérer les configurations
    de marque de manière centralisée.

    Usage:
        # Enregistrer des marques
        registry = BrandRegistry()
        registry.register(MNYBrandConfig())
        registry.register(ESSIEBrandConfig())

        # Récupérer une configuration
        mny_config = registry.get_brand('MNY')

        # Lister toutes les marques
        all_brands = registry.get_all_brands()
    """

    _brands: Dict[str, BaseBrandConfig] = {}
    _logger = logging.getLogger(__name__)

    @classmethod
    def register(cls, brand_config: BaseBrandConfig) -> None:
        """
        Enregistre une configuration de marque dans le registry.

        Args:
            brand_config (BaseBrandConfig): Configuration de marque à enregistrer

        Raises:
            TypeError: Si brand_config n'est pas une instance de BaseBrandConfig
            ValueError: Si une marque avec le même code est déjà enregistrée

        Example:
            registry = BrandRegistry()
            registry.register(MNYBrandConfig())
        """
        if not isinstance(brand_config, BaseBrandConfig):
            raise TypeError(
                f"brand_config must be an instance of BaseBrandConfig, "
                f"got {type(brand_config).__name__}"
            )

        brand_code = brand_config.get_brand_code()

        # Vérifier si la marque existe déjà
        if brand_code in cls._brands:
            cls._logger.warning(
                f"⚠️  Brand '{brand_code}' is already registered. "
                f"Overwriting with new configuration."
            )

        cls._brands[brand_code] = brand_config
        cls._logger.info(
            f"✅ Brand registered: {brand_config.get_brand_display_name()} ({brand_code})"
        )

    @classmethod
    def get_brand(cls, brand_code: str) -> Optional[BaseBrandConfig]:
        """
        Récupère une configuration de marque par son code.

        Args:
            brand_code (str): Code de la marque (ex: 'MNY', 'ESSIE')

        Returns:
            Optional[BaseBrandConfig]: Configuration de marque, ou None si non trouvée

        Example:
            config = BrandRegistry.get_brand('MNY')
            if config:
                print(config.get_brand_display_name())
        """
        config = cls._brands.get(brand_code)

        if config is None:
            cls._logger.warning(
                f"⚠️  Brand '{brand_code}' not found in registry. "
                f"Available brands: {list(cls._brands.keys())}"
            )

        return config

    @classmethod
    def get_all_brands(cls) -> List[BaseBrandConfig]:
        """
        Retourne toutes les configurations de marque enregistrées.

        Returns:
            List[BaseBrandConfig]: Liste des configurations de marque

        Example:
            for brand in BrandRegistry.get_all_brands():
                print(f"- {brand.get_brand_display_name()}")
        """
        return list(cls._brands.values())

    @classmethod
    def get_brand_codes(cls) -> List[str]:
        """
        Retourne la liste de tous les codes de marque enregistrés.

        Returns:
            List[str]: Liste des codes de marque

        Example:
            codes = BrandRegistry.get_brand_codes()
            # ['MNY', 'ESSIE']
        """
        return list(cls._brands.keys())

    @classmethod
    def get_brand_names(cls) -> List[str]:
        """
        Retourne la liste de tous les noms d'affichage des marques.

        Returns:
            List[str]: Liste des noms complets de marque

        Example:
            names = BrandRegistry.get_brand_names()
            # ['Maybelline New York', 'ESSIE']
        """
        return [brand.get_brand_display_name() for brand in cls._brands.values()]

    @classmethod
    def is_registered(cls, brand_code: str) -> bool:
        """
        Vérifie si une marque est enregistrée dans le registry.

        Args:
            brand_code (str): Code de la marque à vérifier

        Returns:
            bool: True si la marque est enregistrée, False sinon

        Example:
            if BrandRegistry.is_registered('MNY'):
                config = BrandRegistry.get_brand('MNY')
        """
        return brand_code in cls._brands

    @classmethod
    def unregister(cls, brand_code: str) -> bool:
        """
        Désenregistre une marque du registry.

        Args:
            brand_code (str): Code de la marque à désenregistrer

        Returns:
            bool: True si la marque a été désenregistrée, False si non trouvée

        Example:
            success = BrandRegistry.unregister('MNY')
        """
        if brand_code in cls._brands:
            removed_brand = cls._brands.pop(brand_code)
            cls._logger.info(
                f"🗑️  Brand unregistered: {removed_brand.get_brand_display_name()} ({brand_code})"
            )
            return True
        else:
            cls._logger.warning(f"⚠️  Cannot unregister brand '{brand_code}': not found")
            return False

    @classmethod
    def clear(cls) -> None:
        """
        Vide complètement le registry (supprime toutes les marques).

        Attention: Cette méthode est principalement utilisée pour les tests.

        Example:
            BrandRegistry.clear()  # Supprime toutes les marques
        """
        count = len(cls._brands)
        cls._brands.clear()
        cls._logger.info(f"🗑️  Registry cleared: {count} brand(s) removed")

    @classmethod
    def get_registry_info(cls) -> Dict[str, Any]:
        """
        Retourne des informations sur l'état du registry.

        Returns:
            Dict[str, Any]: Informations sur le registry

        Example:
            info = BrandRegistry.get_registry_info()
            print(f"Total brands: {info['total_brands']}")
        """
        return {
            'total_brands': len(cls._brands),
            'brand_codes': cls.get_brand_codes(),
            'brand_names': cls.get_brand_names(),
            'brands': cls.get_all_brands()
        }

    @classmethod
    def __repr__(cls) -> str:
        """Représentation string du registry"""
        return f"<BrandRegistry: {len(cls._brands)} brand(s) registered>"
