# ui/layout_debug_overlay.py
"""
Overlay de debug pour visualiser le découpage de la litho en zones.
Affiche les colonnes (FACING) et les zones verticales configurées.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class LayoutDebugOverlay(QWidget):
    """
    Widget transparent superposé sur le PDF pour afficher
    la grille de debug du layout (colonnes + zones).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Données du layout
        self.facing = 1
        self.zones = {}  # Dict[str, ZoneConfig]
        self.show_debug = False

        # Configuration du widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")

    def set_layout_info(self, facing: int, zones: Dict, show: bool = True):
        """
        Configure les informations de layout à afficher.

        Args:
            facing: Nombre de colonnes
            zones: Dictionnaire des zones {zone_name: ZoneConfig}
            show: Si True, affiche l'overlay
        """
        self.facing = facing
        self.zones = zones
        self.show_debug = show
        self.update()
        logger.info(f"Debug overlay: FACING={facing}, zones={len(zones)}, show={show}")

    def toggle_debug(self, show: bool):
        """Active/désactive l'affichage du debug"""
        self.show_debug = show
        self.setVisible(show)
        self.update()

    def paintEvent(self, event):
        """Dessine la grille de debug"""
        if not self.show_debug or not self.zones:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        if width == 0 or height == 0:
            return

        column_width = width / self.facing

        # 1. Dessiner les lignes de colonnes (verticales)
        self._draw_column_lines(painter, width, height, column_width)

        # 2. Dessiner les labels de colonnes
        self._draw_column_labels(painter, height, column_width)

        # 3. Dessiner les zones horizontales
        self._draw_horizontal_zones(painter, width, height)

    def _draw_column_lines(self, painter, width, height, column_width):
        """Dessine les lignes verticales de séparation des colonnes"""
        pen = QPen(QColor(0, 0, 255, 150), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        for i in range(1, self.facing):
            x = int(i * column_width)
            painter.drawLine(x, 0, x, height)

    def _draw_column_labels(self, painter, height, column_width):
        """Dessine les labels de colonnes en haut"""
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)

        # Fond semi-transparent pour labels
        bg_color = QColor(255, 255, 255, 200)
        text_color = QColor(0, 0, 0)

        for i in range(self.facing):
            x_center = int(i * column_width + column_width / 2)

            # Fond du label
            label_rect = QRect(x_center - 40, 5, 80, 30)
            painter.fillRect(label_rect, bg_color)

            # Bordure
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawRect(label_rect)

            # Texte
            painter.setPen(text_color)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"Col {i + 1}")

    def _draw_horizontal_zones(self, painter, width, height):
        """Dessine les zones horizontales configurées"""
        # Couleurs par zone
        zone_colors = {
            'shade_number': QColor(76, 175, 80, 60),      # Vert transparent
            'shade_name': QColor(33, 150, 243, 60),       # Bleu transparent
            '4_digits': QColor(255, 193, 7, 60),          # Jaune transparent
            'description': QColor(158, 158, 158, 30),     # Gris très transparent
            'franchise': QColor(158, 158, 158, 30)        # Gris très transparent
        }

        for zone_name, zone_config in self.zones.items():
            # Ignorer zones désactivées (sauf les 3 principales)
            if not zone_config.enabled and zone_name not in ['shade_number', 'shade_name', '4_digits']:
                continue

            y_start = int(height * zone_config.y_start)
            y_end = int(height * zone_config.y_end)
            zone_height = y_end - y_start

            color = zone_colors.get(zone_name, QColor(200, 200, 200, 60))

            # Fond de la zone
            painter.setBrush(color)
            painter.setPen(QPen(color.darker(150), 2, Qt.PenStyle.DashLine))
            painter.drawRect(0, y_start, width, zone_height)

            # Label de zone (en haut à gauche)
            self._draw_zone_label(painter, zone_name, zone_config, y_start, zone_height)

    def _draw_zone_label(self, painter, zone_name, zone_config, y_start, zone_height):
        """Dessine le label d'une zone"""
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)

        # Fond du label
        bg_color = QColor(255, 255, 255, 220)
        painter.fillRect(10, y_start + 5, 250, 25, bg_color)

        # Bordure
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawRect(10, y_start + 5, 250, 25)

        # Texte
        painter.setPen(QColor(0, 0, 0))
        label_text = zone_name.replace('_', ' ').upper()

        # Ajouter infos de positionnement
        percent_start = int(zone_config.y_start * 100)
        percent_end = int(zone_config.y_end * 100)
        label_text += f" ({percent_start}-{percent_end}%)"

        if not zone_config.enabled:
            label_text += " [DÉSACTIVÉE]"

        label_rect = QRect(15, y_start + 5, 240, 25)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label_text)

    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        if self.show_debug:
            self.update()
