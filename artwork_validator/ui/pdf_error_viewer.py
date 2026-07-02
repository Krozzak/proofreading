# ui/pdf_error_viewer.py
"""
Widget personnalisé pour afficher le PDF avec highlighting des erreurs.
Dessine des bounding boxes colorées autour des zones où des erreurs sont détectées.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QScrollArea
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QFont, QPainterPath
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorOverlay:
    """Représente une erreur avec sa position et son type"""

    def __init__(self, rect: QRect, error_type: str, message: str, severity: str = "high"):
        """
        Args:
            rect: Rectangle de la zone d'erreur (x, y, width, height)
            error_type: Type d'erreur ('shade_name', 'shade_number', '4_digits', etc.)
            message: Message d'erreur descriptif
            severity: 'high', 'medium', 'low'
        """
        self.rect = rect
        self.error_type = error_type
        self.message = message
        self.severity = severity


class PDFErrorViewer(QLabel):
    """
    QLabel amélioré qui affiche un PDF avec des overlays d'erreurs.
    Dessine des bounding boxes colorées autour des zones problématiques.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_pixmap = None  # Image PDF de base
        self.error_overlays: List[ErrorOverlay] = []
        self.show_overlays = True

        # Configuration du widget
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")

        # Couleurs par sévérité
        self.severity_colors = {
            'high': QColor(244, 67, 54, 180),      # Rouge semi-transparent
            'medium': QColor(255, 152, 0, 180),    # Orange semi-transparent
            'low': QColor(255, 235, 59, 180)       # Jaune semi-transparent
        }

    def set_pixmap(self, pixmap: QPixmap):
        """
        Définit l'image PDF à afficher.

        Args:
            pixmap: L'image PDF à afficher
        """
        self.base_pixmap = pixmap
        self._redraw()

    def set_error_overlays(self, overlays: List[ErrorOverlay]):
        """
        Définit les overlays d'erreurs à afficher.

        Args:
            overlays: Liste des overlays d'erreur
        """
        self.error_overlays = overlays
        logger.info(f"Affichage de {len(overlays)} erreurs visuelles")
        self._redraw()

    def clear_overlays(self):
        """Efface tous les overlays d'erreurs"""
        self.error_overlays = []
        self._redraw()

    def toggle_overlays(self, show: bool):
        """Active/désactive l'affichage des overlays"""
        self.show_overlays = show
        self._redraw()

    def _redraw(self):
        """Redessine l'image avec les overlays"""
        if not self.base_pixmap:
            return

        # Créer une copie de l'image de base
        result_pixmap = QPixmap(self.base_pixmap.size())
        result_pixmap.fill(Qt.GlobalColor.transparent)

        # Dessiner l'image de base
        painter = QPainter(result_pixmap)
        painter.drawPixmap(0, 0, self.base_pixmap)

        # Dessiner les overlays si activés
        if self.show_overlays and self.error_overlays:
            self._draw_error_overlays(painter)

        painter.end()

        # Afficher le résultat
        self.setPixmap(result_pixmap)

    def _draw_error_overlays(self, painter: QPainter):
        """
        Dessine les overlays d'erreurs sur l'image.

        Args:
            painter: QPainter actif
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for overlay in self.error_overlays:
            # Couleur selon la sévérité
            color = self.severity_colors.get(overlay.severity, self.severity_colors['high'])

            # Dessiner le rectangle de fond semi-transparent
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(overlay.rect)

            # Dessiner le contour épais
            pen = QPen(color.darker(150), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(overlay.rect)

            # Dessiner l'icône d'erreur en haut à gauche du rectangle
            self._draw_error_icon(painter, overlay.rect.topLeft(), overlay.severity)

            # Dessiner le label d'erreur si l'espace le permet
            if overlay.rect.height() > 30:
                self._draw_error_label(painter, overlay.rect, overlay.error_type)

    def _draw_error_icon(self, painter: QPainter, position: QPoint, severity: str):
        """
        Dessine une icône d'erreur à la position donnée.

        Args:
            painter: QPainter actif
            position: Position de l'icône
            severity: Sévérité de l'erreur
        """
        icon_size = 24
        icon_rect = QRect(position.x() - 12, position.y() - 12, icon_size, icon_size)

        # Fond du badge
        color = self.severity_colors.get(severity, self.severity_colors['high'])
        painter.setBrush(color.darker(120))
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawEllipse(icon_rect)

        # Symbole d'erreur (X ou !)
        painter.setPen(QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.SolidLine))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)

        symbol = "✗" if severity == "high" else "⚠"
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, symbol)

    def _draw_error_label(self, painter: QPainter, rect: QRect, error_type: str):
        """
        Dessine un label descriptif de l'erreur.

        Args:
            painter: QPainter actif
            rect: Rectangle de l'overlay
            error_type: Type d'erreur
        """
        # Label textuel en bas du rectangle
        label_rect = QRect(
            rect.x(),
            rect.y() + rect.height() - 25,
            rect.width(),
            25
        )

        # Fond semi-transparent
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(label_rect)

        # Texte
        painter.setPen(Qt.GlobalColor.white)
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)

        # Labels court selon le type
        labels = {
            'shade_name': 'Nom incorrect',
            'shade_number': 'Numéro incorrect',
            '4_digits': '4 DIGITS manquant',
            'upc': 'UPC incorrect',
            'missing': 'Donnée manquante'
        }

        label_text = labels.get(error_type, 'Erreur')
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label_text)

    def paintEvent(self, event):
        """Override pour custom painting si nécessaire"""
        super().paintEvent(event)


def create_error_overlay_from_ocr(ocr_result: Dict, error_message: str, error_type: str) -> Optional[ErrorOverlay]:
    """
    Crée un ErrorOverlay à partir d'un résultat OCR.

    Args:
        ocr_result: Résultat OCR avec bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        error_message: Message d'erreur
        error_type: Type d'erreur

    Returns:
        ErrorOverlay ou None si bbox invalide
    """
    try:
        bbox = ocr_result.get('bbox')
        if not bbox or len(bbox) < 4:
            return None

        # Convertir bbox OCR [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] en QRect
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]

        x = int(min(x_coords))
        y = int(min(y_coords))
        width = int(max(x_coords) - x)
        height = int(max(y_coords) - y)

        rect = QRect(x, y, width, height)

        # Déterminer la sévérité selon le type
        severity = "high" if error_type in ['shade_name', 'shade_number', 'upc'] else "medium"

        return ErrorOverlay(rect, error_type, error_message, severity)

    except Exception as e:
        logger.error(f"Erreur lors de la création d'overlay: {e}")
        return None


def create_overlays_from_validation(validation_results: List[Dict], ocr_data: List[Dict]) -> List[ErrorOverlay]:
    """
    Crée des overlays d'erreurs en combinant résultats de validation et données OCR.

    Args:
        validation_results: Résultats de validation du validator
        ocr_data: Données OCR avec positions (de ocr_processor.extract_text_with_positions)

    Returns:
        Liste d'ErrorOverlay
    """
    overlays = []

    # Pour chaque entrée avec erreur de validation
    for idx, validation in enumerate(validation_results):
        if validation.get('is_frame') or validation.get('is_space_saver'):
            continue

        # Vérifier chaque type d'erreur
        errors_to_check = [
            ('shade_name', "Nom de teinte incorrect"),
            ('shade_number', "Numéro de teinte incorrect"),
            ('4_digits', "4 DIGITS manquant ou incorrect")
        ]

        for field, message in errors_to_check:
            if not validation.get(field, True):  # False = erreur détectée
                # Chercher la position dans les données OCR (Phase 3 avancée)
                # Pour l'instant, créer un overlay basique sans position exacte
                # Dans une version future, on matchera le texte avec OCR data

                logger.info(f"Erreur détectée: {field} pour entrée {idx}")

    logger.info(f"Création de {len(overlays)} overlays visuels")
    return overlays
