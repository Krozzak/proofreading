# core/brand_configs/base_config.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseBrandConfig(ABC):
    """
    Classe de base abstraite pour les configurations de marque.

    Chaque marque (MNY, ESSIE, etc.) doit hériter de cette classe et implémenter
    toutes les méthodes abstraites pour définir ses règles de validation spécifiques.
    """

    @abstractmethod
    def get_brand_code(self) -> str:
        """
        Retourne le code de la marque (identifiant unique).

        Returns:
            str: Code de la marque (ex: 'MNY', 'ESSIE')
        """
        pass

    @abstractmethod
    def get_brand_display_name(self) -> str:
        """
        Retourne le nom d'affichage de la marque.

        Returns:
            str: Nom complet de la marque (ex: 'Maybelline New York', 'ESSIE')
        """
        pass

    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """
        Retourne la liste des colonnes Excel obligatoires pour cette marque.

        Returns:
            List[str]: Liste des noms de colonnes requises
        """
        pass

    @abstractmethod
    def get_optional_columns(self) -> List[str]:
        """
        Retourne la liste des colonnes Excel optionnelles pour cette marque.

        Returns:
            List[str]: Liste des noms de colonnes optionnelles
        """
        pass

    @abstractmethod
    def get_column_types(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire définissant les types attendus pour chaque colonne.

        Returns:
            Dict[str, Any]: Mapping colonne -> type (str, 'numeric', etc.)

        Example:
            {
                'LITHO': str,
                'SHADE NUMBER': 'numeric',  # ou str pour ESSIE
                'PRODUCT FACING SL': 'numeric',
            }
        """
        pass

    @abstractmethod
    def is_valid_filename(self, filename: str) -> bool:
        """
        Vérifie si le nom de fichier PDF respecte le format de la marque.

        Args:
            filename (str): Nom du fichier PDF à valider

        Returns:
            bool: True si le format est valide, False sinon

        Example:
            MNY: 'YCA12345_version.pdf' -> True
            ESSIE: 'CARE_S26_1_3.pdf' -> True
        """
        pass

    @abstractmethod
    def extract_litho_code(self, filename: str) -> Optional[str]:
        """
        Extrait le code litho du nom de fichier PDF.

        Args:
            filename (str): Nom du fichier PDF

        Returns:
            Optional[str]: Code litho extrait, ou None si extraction impossible

        Example:
            MNY: 'YCA12345_version.pdf' -> 'YCA12345'
            ESSIE: 'CARE_S26_1_3_SHADESTRIPS.pdf' -> 'CARE_S26_1_3'
        """
        pass

    @abstractmethod
    def is_valid_litho_code(self, code: str) -> bool:
        """
        Vérifie si un code litho respecte le format de la marque.

        Args:
            code (str): Code litho à valider

        Returns:
            bool: True si le format est valide, False sinon

        Example:
            MNY: 'YCA12345' -> True
            ESSIE: 'CARE_S26_1_3' -> True
        """
        pass

    @abstractmethod
    def requires_upc_validation(self) -> bool:
        """
        Indique si la marque requiert la validation des codes UPC dans les PDFs.

        Returns:
            bool: True si validation UPC requise, False sinon

        Note:
            Actuellement, UPC validation est désactivée pour toutes les marques
            car les codes UPC n'apparaissent généralement pas dans les lithos.
        """
        pass

    @abstractmethod
    def requires_digits_validation(self) -> bool:
        """
        Indique si la marque requiert la validation de la colonne '4 DIGITS'.

        Returns:
            bool: True si validation 4 DIGITS requise, False sinon

        Note:
            MNY: True (colonne '4 DIGITS' existe)
            ESSIE: False (colonne '4 DIGITS' n'existe pas)
        """
        pass

    @abstractmethod
    def get_validation_description(self) -> str:
        """
        Retourne une description lisible des règles de validation de la marque.

        Returns:
            str: Description formatée des règles (multi-lignes)

        Example:
            "Format MNY:\n"
            "• Pattern: YCA + 5 chiffres\n"
            "• Exemples: YCA12345, YCA98765\n"
            "• Colonnes spéciales: 4 DIGITS (numeric)"
        """
        pass

    # Méthode non-abstraite (implémentation commune)
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire complet des règles de validation pour affichage UI.

        Cette méthode n'est pas abstraite car elle utilise les autres méthodes
        abstraites pour construire un dictionnaire standardisé.

        Returns:
            Dict[str, Any]: Dictionnaire des règles de validation
        """
        return {
            'brand_code': self.get_brand_code(),
            'brand_name': self.get_brand_display_name(),
            'filename_pattern': self.get_validation_description(),
            'required_columns': self.get_required_columns(),
            'optional_columns': self.get_optional_columns(),
            'requires_upc': self.requires_upc_validation(),
            'requires_digits': self.requires_digits_validation()
        }

    def __repr__(self) -> str:
        """Représentation string de la configuration"""
        return f"<{self.__class__.__name__}: {self.get_brand_display_name()} ({self.get_brand_code()})>"
