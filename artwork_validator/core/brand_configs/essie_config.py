# core/brand_configs/essie_config.py

import re
from typing import List, Dict, Any, Optional
from .base_config import BaseBrandConfig


class ESSIEBrandConfig(BaseBrandConfig):
    """
    Configuration de validation pour ESSIE.

    Format des codes:
        - Pattern: [GAMME]_S[SEASON]_[INDEX]_[TOTAL]
        - Exemples: CARE_S26_1_3, GEL_S26_2_6, ESSIE_S26_4_6
        - Suffix optionnel: _SHADESTRIPS

    Gammes supportées:
        - CARE, GEL, NSTUDIO, ESSIE, EXPRESS

    Colonnes spécifiques:
        - SHADE NUMBER: texte (pas numeric!)
        - 4 DIGITS: n'existe pas pour ESSIE

    Validations:
        - UPC: Désactivée (UPC n'apparaît pas dans les PDFs)
        - 4 DIGITS: Désactivée (colonne n'existe pas)
    """

    # Gammes supportées par ESSIE
    SUPPORTED_GAMMES = ['CARE', 'GEL', 'NSTUDIO', 'ESSIE', 'EXPRESS']

    def get_brand_code(self) -> str:
        """Code de la marque: ESSIE"""
        return "ESSIE"

    def get_brand_display_name(self) -> str:
        """Nom complet: ESSIE"""
        return "ESSIE"

    def get_required_columns(self) -> List[str]:
        """
        Colonnes Excel obligatoires pour ESSIE.

        Note: Pas de colonne '4 DIGITS' pour ESSIE.

        Returns:
            List[str]: Liste des colonnes requises
        """
        return [
            'LITHO',                # Code litho (CARE_S26_1_3)
            'DECRIPTION',           # Description du produit
            'UPC SEQUENCE',         # Séquence UPC
            'UPC POSITION',         # Position dans la séquence
            'UPC',                  # Code UPC du produit
            'PRODUCT DESCRIPTION',  # Description détaillée
            'SHADE NAME',           # Nom de la teinte
            'SHADE NUMBER',         # Numéro de teinte (TEXTE pour ESSIE!)
            'PRODUCT FACING SL'     # Nombre de facings
            # Note: Pas de '4 DIGITS' pour ESSIE
        ]

    def get_optional_columns(self) -> List[str]:
        """
        Colonnes Excel optionnelles pour ESSIE.

        Returns:
            List[str]: Liste des colonnes optionnelles
        """
        return [
            'NEW',          # Nouveau produit (flag)
            'STATUS',       # Statut du produit
            'PRODUCT',      # Code produit
            'TIER',         # Niveau du tier
            'SEASON',       # Saison (S26, etc.)
            'STRIP TYPE'    # Type de strip (spécifique ESSIE)
        ]

    def get_column_types(self) -> Dict[str, Any]:
        """
        Types attendus pour chaque colonne ESSIE.

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
            'SHADE NUMBER': str,            # ⚠️ STRING pour ESSIE (pas numeric!)
            'PRODUCT FACING SL': 'numeric',

            # Colonnes optionnelles
            'NEW': str,
            'STATUS': str,
            'PRODUCT': str,
            'TIER': str,
            'SEASON': str,
            'STRIP TYPE': str,
        }

    def is_valid_filename(self, filename: str) -> bool:
        """
        Vérifie si le nom de fichier PDF respecte le format ESSIE.

        Format: [GAMME]_S[DIGITS]_[DIGITS]_[DIGITS] (avec suffix _SHADESTRIPS optionnel)

        Args:
            filename (str): Nom du fichier à valider

        Returns:
            bool: True si format valide, False sinon

        Example:
            >>> config = ESSIEBrandConfig()
            >>> config.is_valid_filename('CARE_S26_1_3.pdf')
            True
            >>> config.is_valid_filename('GEL_S26_2_6_SHADESTRIPS.pdf')
            True
            >>> config.is_valid_filename('YCA12345.pdf')
            False
        """
        # Pattern regex: [GAMME]_S[DIGITS]_[DIGITS]_[DIGITS] avec suffix optionnel
        gammes_pattern = '|'.join(self.SUPPORTED_GAMMES)
        pattern = rf'^({gammes_pattern})_S\d+_\d+_\d+(_SHADESTRIPS)?'

        return bool(re.match(pattern, filename, re.IGNORECASE))

    def extract_litho_code(self, filename: str) -> Optional[str]:
        """
        Extrait le code litho ESSIE du nom de fichier.

        Le code extrait ne contient PAS le suffix _SHADESTRIPS ni l'extension.

        Args:
            filename (str): Nom du fichier PDF

        Returns:
            Optional[str]: Code litho, ou None si extraction impossible

        Example:
            >>> config = ESSIEBrandConfig()
            >>> config.extract_litho_code('CARE_S26_1_3_SHADESTRIPS.pdf')
            'CARE_S26_1_3'
            >>> config.extract_litho_code('GEL_S26_2_6.pdf')
            'GEL_S26_2_6'
            >>> config.extract_litho_code('YCA12345.pdf')
            None
        """
        # Pattern pour extraire le code (sans suffix _SHADESTRIPS et extension)
        gammes_pattern = '|'.join(self.SUPPORTED_GAMMES)
        pattern = rf'^(({gammes_pattern})_S\d+_\d+_\d+)'

        match = re.match(pattern, filename, re.IGNORECASE)

        if match:
            code = match.group(1)
            # Valider le code extrait
            return code if self.is_valid_litho_code(code) else None

        return None

    def is_valid_litho_code(self, code: str) -> bool:
        """
        Vérifie si un code litho respecte le format ESSIE.

        Format: [GAMME]_S[DIGITS]_[DIGITS]_[DIGITS] (sans suffix _SHADESTRIPS)

        Args:
            code (str): Code litho à valider

        Returns:
            bool: True si format valide, False sinon

        Example:
            >>> config = ESSIEBrandConfig()
            >>> config.is_valid_litho_code('CARE_S26_1_3')
            True
            >>> config.is_valid_litho_code('GEL_S26_2_6')
            True
            >>> config.is_valid_litho_code('INVALID_S26_1_3')
            False
            >>> config.is_valid_litho_code('YCA12345')
            False
        """
        # Pattern regex strict (sans suffix)
        gammes_pattern = '|'.join(self.SUPPORTED_GAMMES)
        pattern = rf'^({gammes_pattern})_S\d+_\d+_\d+$'

        return bool(re.match(pattern, code, re.IGNORECASE))

    def requires_upc_validation(self) -> bool:
        """
        ESSIE: UPC validation désactivée.

        Les codes UPC n'apparaissent généralement pas dans les PDFs (lithos).

        Returns:
            bool: False (validation UPC désactivée)
        """
        return False

    def requires_digits_validation(self) -> bool:
        """
        ESSIE: Validation 4 DIGITS désactivée.

        La colonne '4 DIGITS' n'existe pas dans les fichiers Excel ESSIE.

        Returns:
            bool: False (validation 4 DIGITS désactivée)
        """
        return False

    def get_validation_description(self) -> str:
        """
        Description des règles de validation ESSIE.

        Returns:
            str: Description formatée (multi-lignes)
        """
        gammes_str = ', '.join(self.SUPPORTED_GAMMES)

        return (
            "Format ESSIE:\n"
            "\n"
            "📄 Fichiers PDF:\n"
            "  • Pattern: [GAMME]_S[SEASON]_[INDEX]_[TOTAL]\n"
            "  • Exemples: CARE_S26_1_3.pdf, GEL_S26_2_6.pdf\n"
            f"  • Gammes supportées: {gammes_str}\n"
            "  • Suffix optionnel: _SHADESTRIPS\n"
            "\n"
            "📊 Colonnes Excel spécifiques:\n"
            "  • SHADE NUMBER: Texte (ex: '2-IN-1 BASE & TOP COAT')\n"
            "  • 4 DIGITS: ❌ N'existe pas pour ESSIE\n"
            "\n"
            "✅ Validations:\n"
            "  • SHADE NUMBER: Validé dans PDF\n"
            "  • SHADE NAME: Validé dans PDF\n"
            "  • UPC: ❌ Désactivé (pas dans PDFs)\n"
            "  • 4 DIGITS: ❌ Désactivé (colonne absente)"
        )

    def get_supported_gammes(self) -> List[str]:
        """
        Retourne la liste des gammes supportées pour ESSIE.

        Returns:
            List[str]: Liste des gammes
        """
        return self.SUPPORTED_GAMMES.copy()

    def __repr__(self) -> str:
        """Représentation string de la configuration ESSIE"""
        return f"<ESSIEBrandConfig: {self.get_brand_display_name()} ({self.get_brand_code()})>"
