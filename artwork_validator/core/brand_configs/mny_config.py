# core/brand_configs/mny_config.py

import re
from typing import List, Dict, Any, Optional
from .base_config import BaseBrandConfig


class MNYBrandConfig(BaseBrandConfig):
    """
    Configuration de validation pour Maybelline New York (MNY).

    Format des codes:
        - Pattern: YCA + 5 chiffres
        - Exemples: YCA12345, YCA98765
        - Longueur: 8 caractères

    Colonnes spécifiques:
        - SHADE NUMBER: numeric
        - 4 DIGITS: numeric (validation activée)

    Validations:
        - UPC: Désactivée (UPC n'apparaît pas dans les PDFs)
        - 4 DIGITS: Activée (colonne existe dans Excel MNY)
    """

    def get_brand_code(self) -> str:
        """Code de la marque: MNY"""
        return "MNY"

    def get_brand_display_name(self) -> str:
        """Nom complet: Maybelline New York"""
        return "Maybelline New York"

    def get_required_columns(self) -> List[str]:
        """
        Colonnes Excel obligatoires pour MNY.

        Returns:
            List[str]: Liste des colonnes requises
        """
        return [
            'LITHO',                # Code litho (YCA12345)
            'DECRIPTION',           # Description du produit
            'UPC SEQUENCE',         # Séquence UPC
            'UPC POSITION',         # Position dans la séquence
            'UPC',                  # Code UPC du produit
            'PRODUCT DESCRIPTION',  # Description détaillée
            'SHADE NAME',           # Nom de la teinte
            'SHADE NUMBER',         # Numéro de teinte (numeric pour MNY)
            'PRODUCT FACING SL',    # Nombre de facings
            '4 DIGITS'              # 4 derniers chiffres UPC (spécifique MNY)
        ]

    def get_optional_columns(self) -> List[str]:
        """
        Colonnes Excel optionnelles pour MNY.

        Returns:
            List[str]: Liste des colonnes optionnelles
        """
        return [
            'NEW',      # Nouveau produit (flag)
            'STATUS',   # Statut du produit
            'PRODUCT',  # Code produit
            'TIER',     # Niveau du tier
            'SEASON'    # Saison (S26, etc.)
        ]

    def get_column_types(self) -> Dict[str, Any]:
        """
        Types attendus pour chaque colonne MNY.

        Returns:
            Dict[str, Any]: Mapping colonne -> type
        """
        return {
            # Colonnes requises
            'LITHO': str,
            'DECRIPTION': str,
            'UPC SEQUENCE': str,
            'UPC POSITION': str,
            'UPC': str,
            'PRODUCT DESCRIPTION': str,
            'SHADE NAME': str,
            'SHADE NUMBER': 'numeric',      # ⚠️ Numeric pour MNY
            'PRODUCT FACING SL': 'numeric',
            '4 DIGITS': 'numeric',          # ⚠️ Numeric pour MNY

            # Colonnes optionnelles
            'NEW': str,
            'STATUS': str,
            'PRODUCT': str,
            'TIER': str,
            'SEASON': str,
        }

    def is_valid_filename(self, filename: str) -> bool:
        """
        Vérifie si le nom de fichier PDF respecte le format MNY.

        Format: YCA + 5 chiffres (8 caractères au début du nom)

        Args:
            filename (str): Nom du fichier à valider

        Returns:
            bool: True si format valide, False sinon

        Example:
            >>> config = MNYBrandConfig()
            >>> config.is_valid_filename('YCA12345_version.pdf')
            True
            >>> config.is_valid_filename('CARE_S26_1_3.pdf')
            False
        """
        if len(filename) < 8:
            return False

        # Extraire les 8 premiers caractères
        code = filename[:8]

        # Vérifier: commence par 'YCA' et 5 chiffres suivent
        return code.startswith('YCA') and code[3:].isdigit()

    def extract_litho_code(self, filename: str) -> Optional[str]:
        """
        Extrait le code litho YCA du nom de fichier.

        Args:
            filename (str): Nom du fichier PDF

        Returns:
            Optional[str]: Code litho (8 caractères), ou None si extraction impossible

        Example:
            >>> config = MNYBrandConfig()
            >>> config.extract_litho_code('YCA12345_version2.pdf')
            'YCA12345'
            >>> config.extract_litho_code('invalid.pdf')
            None
        """
        if len(filename) < 8:
            return None

        # Extraire les 8 premiers caractères
        code = filename[:8]

        # Valider le format et retourner
        return code if self.is_valid_litho_code(code) else None

    def is_valid_litho_code(self, code: str) -> bool:
        """
        Vérifie si un code litho respecte le format MNY.

        Format: YCA + 5 chiffres (exactement 8 caractères)

        Args:
            code (str): Code litho à valider

        Returns:
            bool: True si format valide, False sinon

        Example:
            >>> config = MNYBrandConfig()
            >>> config.is_valid_litho_code('YCA12345')
            True
            >>> config.is_valid_litho_code('YCA123')
            False
            >>> config.is_valid_litho_code('CARE_S26_1_3')
            False
        """
        if len(code) != 8:
            return False

        # Vérifier: commence par 'YCA' et 5 chiffres suivent
        return code.startswith('YCA') and code[3:].isdigit()

    def requires_upc_validation(self) -> bool:
        """
        MNY: UPC validation désactivée.

        Les codes UPC n'apparaissent généralement pas dans les PDFs (lithos).

        Returns:
            bool: False (validation UPC désactivée)
        """
        return False

    def requires_digits_validation(self) -> bool:
        """
        MNY: Validation 4 DIGITS activée.

        La colonne '4 DIGITS' existe dans les fichiers Excel MNY et peut être
        validée si l'option est activée dans les settings.

        Returns:
            bool: True (validation 4 DIGITS possible)
        """
        return True

    def get_validation_description(self) -> str:
        """
        Description des règles de validation MNY.

        Returns:
            str: Description formatée (multi-lignes)
        """
        return (
            "Format Maybelline New York (MNY):\n"
            "\n"
            "📄 Fichiers PDF:\n"
            "  • Pattern: YCA + 5 chiffres\n"
            "  • Exemples: YCA12345.pdf, YCA98765_v2.pdf\n"
            "  • Longueur code: 8 caractères\n"
            "\n"
            "📊 Colonnes Excel spécifiques:\n"
            "  • SHADE NUMBER: Numérique (ex: 110, 120)\n"
            "  • 4 DIGITS: Numérique (4 derniers chiffres UPC)\n"
            "\n"
            "✅ Validations:\n"
            "  • SHADE NUMBER: Validé dans PDF\n"
            "  • SHADE NAME: Validé dans PDF\n"
            "  • UPC: ❌ Désactivé (pas dans PDFs)\n"
            "  • 4 DIGITS: ✓ Activable (selon settings)"
        )

    def __repr__(self) -> str:
        """Représentation string de la configuration MNY"""
        return f"<MNYBrandConfig: {self.get_brand_display_name()} ({self.get_brand_code()})>"
