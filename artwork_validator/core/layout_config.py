# core/layout_config.py
"""
Configuration du layout des lithos pour le positionnement précis des erreurs.
Permet de configurer les zones verticales et horizontales de chaque élément.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Literal
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ZoneConfig:
    """Configuration d'une zone de litho"""
    y_start: float  # Position verticale début (0.0 à 1.0, ratio de la hauteur)
    y_end: float    # Position verticale fin (0.0 à 1.0)
    horizontal: Literal['centered', 'left', 'right'] = 'centered'
    margin_x: float = 0.10  # Marge horizontale pour 'centered' (0.0 à 0.5)
    x_offset: float = 0.0   # Offset horizontal pour 'right' ou 'left' (0.0 à 1.0)
    width: float = 1.0      # Largeur relative (0.0 à 1.0, 1.0 = toute la colonne)
    enabled: bool = True    # Si False, cette zone est ignorée

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'y_start': self.y_start,
            'y_end': self.y_end,
            'horizontal': self.horizontal,
            'margin_x': self.margin_x,
            'x_offset': self.x_offset,
            'width': self.width,
            'enabled': self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Crée depuis un dictionnaire"""
        return cls(
            y_start=data.get('y_start', 0.0),
            y_end=data.get('y_end', 1.0),
            horizontal=data.get('horizontal', 'centered'),
            margin_x=data.get('margin_x', 0.10),
            x_offset=data.get('x_offset', 0.0),
            width=data.get('width', 1.0),
            enabled=data.get('enabled', True)
        )


@dataclass
class LayoutConfig:
    """Configuration complète du layout d'une litho"""
    name: str
    version: str
    zones: Dict[str, ZoneConfig] = field(default_factory=dict)

    @classmethod
    def get_default(cls):
        """
        Retourne la configuration par défaut basée sur le format standard des lithos.

        Structure verticale :
        - 0-15% : SHADE NUMBER (en haut)
        - 15-30% : SHADE NAME + 4 DIGITS (même ligne, 4D à droite)
        - 30-70% : DESCRIPTION PRODUIT (ignorée pour l'instant)
        - 70-100% : FRANCHISE NAME (ignorée pour l'instant)
        """
        return cls(
            name='Default Layout',
            version='1.0',
            zones={
                'shade_number': ZoneConfig(
                    y_start=0.00,
                    y_end=0.15,
                    horizontal='centered',
                    margin_x=0.10,
                    enabled=True
                ),
                'shade_name': ZoneConfig(
                    y_start=0.15,
                    y_end=0.30,
                    horizontal='centered',
                    margin_x=0.10,
                    enabled=True
                ),
                '4_digits': ZoneConfig(
                    y_start=0.15,      # Même ligne que shade_name
                    y_end=0.30,
                    horizontal='right',
                    x_offset=0.60,     # Commence à 60% de la colonne
                    width=0.35,        # Occupe 35% de la largeur
                    enabled=True
                ),
                'description': ZoneConfig(
                    y_start=0.30,
                    y_end=0.70,
                    horizontal='centered',
                    enabled=False      # Ignorée pour l'instant
                ),
                'franchise': ZoneConfig(
                    y_start=0.70,
                    y_end=1.00,
                    horizontal='centered',
                    enabled=False      # Ignorée pour l'instant
                )
            }
        )

    def to_dict(self):
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'name': self.name,
            'version': self.version,
            'zones': {
                zone_name: zone.to_dict()
                for zone_name, zone in self.zones.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Crée depuis un dictionnaire"""
        zones = {}
        for zone_name, zone_data in data.get('zones', {}).items():
            zones[zone_name] = ZoneConfig.from_dict(zone_data)

        return cls(
            name=data.get('name', 'Custom Layout'),
            version=data.get('version', '1.0'),
            zones=zones
        )

    def save(self, filepath: Path):
        """Sauvegarde dans un fichier JSON"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration sauvegardée : {filepath}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration : {e}")
            raise

    @classmethod
    def load(cls, filepath: Path):
        """Charge depuis un fichier JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Configuration chargée : {filepath}")
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Erreur chargement configuration : {e}")
            raise

    def get_adjusted_zones(self, has_shade_number: bool, has_shade_name: bool) -> Dict[str, ZoneConfig]:
        """
        Retourne les zones ajustées selon la présence/absence de shade number et name.

        Règles :
        - Si les deux présents : zones normales
        - Si seulement number : number prend place de name aussi
        - Si seulement name : name monte en zone 1

        Args:
            has_shade_number: Présence de SHADE NUMBER
            has_shade_name: Présence de SHADE NAME

        Returns:
            Dictionnaire de zones ajustées
        """
        adjusted_zones = dict(self.zones)

        if has_shade_number and has_shade_name:
            # Cas normal : pas d'ajustement
            return adjusted_zones

        elif has_shade_number and not has_shade_name:
            # Seulement number : étendre sur les 2 zones
            adjusted_zones['shade_number'] = ZoneConfig(
                y_start=0.00,
                y_end=0.30,  # Prend place de name aussi
                horizontal=self.zones['shade_number'].horizontal,
                margin_x=self.zones['shade_number'].margin_x,
                enabled=True
            )
            # 4 DIGITS reste en place mais plus bas
            adjusted_zones['4_digits'] = ZoneConfig(
                y_start=0.20,
                y_end=0.30,
                horizontal=self.zones['4_digits'].horizontal,
                x_offset=self.zones['4_digits'].x_offset,
                width=self.zones['4_digits'].width,
                enabled=self.zones['4_digits'].enabled
            )

        elif not has_shade_number and has_shade_name:
            # Seulement name : monte en zone 1
            adjusted_zones['shade_name'] = ZoneConfig(
                y_start=0.00,  # Monte à la place du number
                y_end=0.15,
                horizontal=self.zones['shade_name'].horizontal,
                margin_x=self.zones['shade_name'].margin_x,
                enabled=True
            )
            # 4 DIGITS suit
            adjusted_zones['4_digits'] = ZoneConfig(
                y_start=0.00,
                y_end=0.15,
                horizontal=self.zones['4_digits'].horizontal,
                x_offset=self.zones['4_digits'].x_offset,
                width=self.zones['4_digits'].width,
                enabled=self.zones['4_digits'].enabled
            )

        return adjusted_zones


class LayoutConfigManager:
    """Gestionnaire de configurations de layout"""

    def __init__(self, config_dir: Path = None):
        """
        Initialise le gestionnaire.

        Args:
            config_dir: Répertoire de stockage des configs (défaut: ~/.litho_validator/layouts)
        """
        if config_dir is None:
            config_dir = Path.home() / '.litho_validator' / 'layouts'

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.current_config = LayoutConfig.get_default()
        self._load_last_config()

    def _load_last_config(self):
        """Charge la dernière configuration utilisée"""
        last_config_file = self.config_dir / 'last_used.json'

        if last_config_file.exists():
            try:
                self.current_config = LayoutConfig.load(last_config_file)
                logger.info("Dernière configuration chargée")
            except Exception as e:
                logger.warning(f"Impossible de charger dernière config, utilisation par défaut : {e}")
                self.current_config = LayoutConfig.get_default()
        else:
            logger.info("Aucune config précédente, utilisation par défaut")

    def save_current_config(self):
        """Sauvegarde la configuration actuelle comme 'last_used'"""
        try:
            last_config_file = self.config_dir / 'last_used.json'
            self.current_config.save(last_config_file)
            logger.info("Configuration actuelle sauvegardée")
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration : {e}")

    def get_zone_config(self, zone_name: str) -> ZoneConfig:
        """
        Retourne la configuration d'une zone.

        Args:
            zone_name: Nom de la zone ('shade_number', 'shade_name', '4_digits', etc.)

        Returns:
            ZoneConfig ou None si zone inexistante
        """
        return self.current_config.zones.get(zone_name)

    def update_zone_config(self, zone_name: str, config: ZoneConfig):
        """
        Met à jour la configuration d'une zone.

        Args:
            zone_name: Nom de la zone
            config: Nouvelle configuration
        """
        self.current_config.zones[zone_name] = config
        logger.info(f"Zone '{zone_name}' mise à jour")

    def set_config(self, config: LayoutConfig):
        """
        Définit une nouvelle configuration complète.

        Args:
            config: Nouvelle configuration
        """
        self.current_config = config
        self.save_current_config()
        logger.info(f"Configuration '{config.name}' appliquée")

    def reset_to_default(self):
        """Réinitialise à la configuration par défaut"""
        self.current_config = LayoutConfig.get_default()
        self.save_current_config()
        logger.info("Configuration réinitialisée aux valeurs par défaut")

    def export_config(self, filepath: Path):
        """
        Exporte la configuration actuelle vers un fichier.

        Args:
            filepath: Chemin du fichier de destination
        """
        self.current_config.save(filepath)

    def import_config(self, filepath: Path):
        """
        Importe une configuration depuis un fichier.

        Args:
            filepath: Chemin du fichier source
        """
        config = LayoutConfig.load(filepath)
        self.set_config(config)

    def list_saved_configs(self) -> list:
        """
        Liste toutes les configurations sauvegardées.

        Returns:
            Liste des chemins de fichiers .json dans config_dir
        """
        return list(self.config_dir.glob('*.json'))
