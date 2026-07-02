# ui/layout_config_tab.py
"""
Onglet de configuration du layout OCR dans les paramètres.
Permet d'ajuster visuellement les zones de détection des erreurs.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QDoubleSpinBox, QRadioButton, QButtonGroup,
                             QGroupBox, QPushButton, QComboBox, QCheckBox,
                             QScrollArea, QFrame, QFileDialog, QMessageBox,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from ..core.layout_config import LayoutConfig, ZoneConfig, LayoutConfigManager
from ..utils.styles import LorealStyles
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LayoutPreviewCanvas(QWidget):
    """Canvas pour prévisualiser le layout de litho"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_config = None
        self.facing = 6
        self.num_tiers = 1
        self.setMinimumSize(500, 350)
        self.setStyleSheet("background-color: white; border: 1px solid #ddd;")

    def set_config(self, config: LayoutConfig, facing: int = 6, num_tiers: int = 1):
        """
        Définit la configuration à prévisualiser.

        Args:
            config: Configuration du layout
            facing: Nombre de colonnes (FACING)
            num_tiers: Nombre de TIERS (lignes horizontales)
        """
        self.layout_config = config
        self.facing = facing
        self.num_tiers = num_tiers
        self.update()

    def paintEvent(self, event):
        """Dessine le preview du layout"""
        if not self.layout_config:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        column_width = width / self.facing

        # Fond blanc
        painter.fillRect(0, 0, width, height, Qt.GlobalColor.white)

        # Dessiner les colonnes verticales (lignes de séparation)
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        for i in range(1, self.facing):
            x = int(i * column_width)
            painter.drawLine(x, 0, x, height)

        # Dessiner les labels de colonnes en haut
        font_col = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font_col)
        painter.setPen(QColor(100, 100, 100))
        for i in range(self.facing):
            x_center = int(i * column_width + column_width / 2)
            painter.drawText(QRect(x_center - 40, 5, 80, 25),
                           Qt.AlignmentFlag.AlignCenter,
                           f"Col {i + 1}")

        # Couleurs par zone
        zone_colors = {
            'shade_number': QColor(76, 175, 80, 80),      # Vert
            'shade_name': QColor(33, 150, 243, 80),       # Bleu
            '4_digits': QColor(255, 193, 7, 80),          # Jaune
            'description': QColor(158, 158, 158, 40),     # Gris clair
            'franchise': QColor(158, 158, 158, 40)        # Gris clair
        }

        # Dessiner les TIERS horizontalement si > 1
        if self.num_tiers > 1:
            # Diviser la zone shade (0-30%) en num_tiers lignes
            tier_height_fraction = 0.30 / self.num_tiers
            pen_tier = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_tier)

            for tier_idx in range(1, self.num_tiers):
                y_tier = int(height * tier_idx * tier_height_fraction)
                painter.drawLine(0, y_tier, width, y_tier)

            # Dessiner labels TIER sur le côté gauche
            font_tier = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font_tier)
            painter.setPen(QColor(255, 0, 0))

            for tier_idx in range(self.num_tiers):
                y_tier_start = int(height * tier_idx * tier_height_fraction)
                y_tier_end = int(height * (tier_idx + 1) * tier_height_fraction)
                y_tier_center = (y_tier_start + y_tier_end) // 2
                painter.drawText(QRect(5, y_tier_center - 10, 50, 20),
                               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                               f"T{tier_idx + 1}")

        # Dessiner les zones horizontales avec ajustement pour tiers
        for zone_name, zone_config in self.layout_config.zones.items():
            if not zone_config.enabled and zone_name not in ['shade_number', 'shade_name', '4_digits']:
                # Zones désactivées : dessiner en grisé
                continue

            # Calculer les positions Y avec ajustement pour multi-tiers
            if self.num_tiers > 1 and zone_name in ['shade_number', 'shade_name', '4_digits']:
                # Zones shade divisées en tiers
                tier_height_fraction = 0.30 / self.num_tiers

                # Dessiner pour chaque tier
                for tier_idx in range(self.num_tiers):
                    tier_y_start_fraction = tier_idx * tier_height_fraction

                    # Mapper zone dans l'espace du tier
                    y_start = int(height * (tier_y_start_fraction + zone_config.y_start * tier_height_fraction))
                    y_end = int(height * (tier_y_start_fraction + zone_config.y_end * tier_height_fraction))
                    zone_height = y_end - y_start

                    self._draw_zone(painter, zone_name, zone_config, zone_colors,
                                  y_start, zone_height, width, column_width, tier_idx)
            else:
                # Zones normales (single tier ou zones non-shade)
                y_start = int(height * zone_config.y_start)
                y_end = int(height * zone_config.y_end)
                zone_height = y_end - y_start

                self._draw_zone(painter, zone_name, zone_config, zone_colors,
                              y_start, zone_height, width, column_width)

    def _draw_zone(self, painter, zone_name, zone_config, zone_colors,
                   y_start, zone_height, width, column_width, tier_idx=None):
        """Dessine une zone avec sa couleur et son label"""
        color = zone_colors.get(zone_name, QColor(200, 200, 200, 80))
        painter.setBrush(color)
        painter.setPen(QPen(color.darker(150), 2))

        # Dessiner selon la position horizontale
        if zone_name == '4_digits' and zone_config.horizontal == 'right':
            # 4 DIGITS : dessiner dans chaque colonne, à droite
            facing = int(width / column_width)
            for i in range(facing):
                x_col = int(i * column_width)
                x_zone = int(x_col + column_width * zone_config.x_offset)
                w_zone = int(column_width * zone_config.width)
                painter.drawRect(x_zone, y_start, w_zone, zone_height)

        elif zone_config.horizontal == 'centered':
            # Centré : dessiner pleine largeur avec indication des marges
            painter.drawRect(0, y_start, width, zone_height)

            # Dessiner indication des marges en pointillés
            if zone_config.margin_x > 0:
                pen_margin = QPen(color.darker(200), 1, Qt.PenStyle.DotLine)
                painter.setPen(pen_margin)
                facing = int(width / column_width)
                for i in range(facing):
                    x_col = int(i * column_width)
                    x_margin_left = int(x_col + column_width * zone_config.margin_x)
                    x_margin_right = int(x_col + column_width * (1 - zone_config.margin_x))
                    painter.drawLine(x_margin_left, y_start, x_margin_left, y_start + zone_height)
                    painter.drawLine(x_margin_right, y_start, x_margin_right, y_start + zone_height)

        elif zone_config.horizontal == 'left':
            # Gauche : dessiner pleine largeur
            painter.drawRect(0, y_start, width, zone_height)

        else:  # right
            # Droite : dessiner pleine largeur
            painter.drawRect(0, y_start, width, zone_height)

        # Label de zone
        font_zone = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font_zone)
        painter.setPen(QColor(0, 0, 0))

        label_text = zone_name.replace('_', ' ').upper()
        if not zone_config.enabled:
            label_text += " (désactivée)"
        if tier_idx is not None:
            label_text += f" T{tier_idx + 1}"

        x_label = 60 if tier_idx is not None else 10
        painter.drawText(QRect(x_label, y_start + 5, 200, 20),
                           Qt.AlignmentFlag.AlignLeft,
                           label_text)


class ZoneConfigWidget(QGroupBox):
    """Widget pour configurer une zone"""

    config_changed = pyqtSignal(str, ZoneConfig)  # zone_name, new_config

    def __init__(self, zone_name: str, zone_config: ZoneConfig, parent=None):
        super().__init__(f"📍 {zone_name.replace('_', ' ').upper()}", parent)
        self.zone_name = zone_name
        self.zone_config = zone_config
        self._updating = False  # Flag pour éviter boucles de signaux
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(8)

        # Ligne 1 : Y start/end
        pos_layout = QHBoxLayout()

        pos_layout.addWidget(QLabel("Début (Y):"))
        self.y_start_spin = QDoubleSpinBox()
        self.y_start_spin.setRange(0.0, 1.0)
        self.y_start_spin.setSingleStep(0.01)
        self.y_start_spin.setDecimals(2)
        self.y_start_spin.setValue(self.zone_config.y_start)
        self.y_start_spin.valueChanged.connect(self._on_value_changed)
        pos_layout.addWidget(self.y_start_spin)

        pos_layout.addWidget(QLabel("Fin (Y):"))
        self.y_end_spin = QDoubleSpinBox()
        self.y_end_spin.setRange(0.0, 1.0)
        self.y_end_spin.setSingleStep(0.01)
        self.y_end_spin.setDecimals(2)
        self.y_end_spin.setValue(self.zone_config.y_end)
        self.y_end_spin.valueChanged.connect(self._on_value_changed)
        pos_layout.addWidget(self.y_end_spin)

        layout.addLayout(pos_layout)

        # Ligne 2 : Position horizontale (radio buttons)
        horiz_layout = QHBoxLayout()
        horiz_layout.addWidget(QLabel("Position horizontale:"))

        self.horiz_group = QButtonGroup(self)
        self.centered_radio = QRadioButton("Centré")
        self.left_radio = QRadioButton("Gauche")
        self.right_radio = QRadioButton("Droite")

        self.horiz_group.addButton(self.centered_radio, 0)
        self.horiz_group.addButton(self.left_radio, 1)
        self.horiz_group.addButton(self.right_radio, 2)

        if self.zone_config.horizontal == 'centered':
            self.centered_radio.setChecked(True)
        elif self.zone_config.horizontal == 'left':
            self.left_radio.setChecked(True)
        else:
            self.right_radio.setChecked(True)

        self.horiz_group.buttonClicked.connect(self._on_value_changed)

        horiz_layout.addWidget(self.centered_radio)
        horiz_layout.addWidget(self.left_radio)
        horiz_layout.addWidget(self.right_radio)
        horiz_layout.addStretch()
        layout.addLayout(horiz_layout)

        # Ligne 3 : Paramètres supplémentaires
        params_layout = QHBoxLayout()

        # Marge X (pour centered)
        params_layout.addWidget(QLabel("Marge X:"))
        self.margin_x_spin = QDoubleSpinBox()
        self.margin_x_spin.setRange(0.0, 0.5)
        self.margin_x_spin.setSingleStep(0.01)
        self.margin_x_spin.setDecimals(2)
        self.margin_x_spin.setValue(self.zone_config.margin_x)
        self.margin_x_spin.setToolTip("Marge horizontale pour position 'Centré'")
        self.margin_x_spin.valueChanged.connect(self._on_value_changed)
        params_layout.addWidget(self.margin_x_spin)

        # X Offset (pour right/left)
        params_layout.addWidget(QLabel("Offset X:"))
        self.x_offset_spin = QDoubleSpinBox()
        self.x_offset_spin.setRange(0.0, 1.0)
        self.x_offset_spin.setSingleStep(0.01)
        self.x_offset_spin.setDecimals(2)
        self.x_offset_spin.setValue(self.zone_config.x_offset)
        self.x_offset_spin.setToolTip("Offset horizontal pour position 'Droite' ou 'Gauche'")
        self.x_offset_spin.valueChanged.connect(self._on_value_changed)
        params_layout.addWidget(self.x_offset_spin)

        # Width
        params_layout.addWidget(QLabel("Largeur:"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 1.0)
        self.width_spin.setSingleStep(0.01)
        self.width_spin.setDecimals(2)
        self.width_spin.setValue(self.zone_config.width)
        self.width_spin.setToolTip("Largeur relative (1.0 = toute la colonne)")
        self.width_spin.valueChanged.connect(self._on_value_changed)
        params_layout.addWidget(self.width_spin)

        params_layout.addStretch()
        layout.addLayout(params_layout)

        # Checkbox enabled (pour zones optionnelles)
        if self.zone_name in ['description', 'franchise']:
            self.enabled_checkbox = QCheckBox("Activer validation dans cette zone")
            self.enabled_checkbox.setChecked(self.zone_config.enabled)
            self.enabled_checkbox.toggled.connect(self._on_value_changed)
            layout.addWidget(self.enabled_checkbox)

    def _on_value_changed(self):
        """Appelé quand une valeur change"""
        if self._updating:
            return

        # Créer nouvelle config
        horizontal_map = {0: 'centered', 1: 'left', 2: 'right'}
        new_config = ZoneConfig(
            y_start=self.y_start_spin.value(),
            y_end=self.y_end_spin.value(),
            horizontal=horizontal_map[self.horiz_group.checkedId()],
            margin_x=self.margin_x_spin.value(),
            x_offset=self.x_offset_spin.value(),
            width=self.width_spin.value(),
            enabled=self.enabled_checkbox.isChecked() if hasattr(self, 'enabled_checkbox') else True
        )

        self.zone_config = new_config
        self.config_changed.emit(self.zone_name, new_config)

    def set_config(self, config: ZoneConfig):
        """Met à jour le widget avec une nouvelle config"""
        self._updating = True
        self.zone_config = config

        self.y_start_spin.setValue(config.y_start)
        self.y_end_spin.setValue(config.y_end)

        if config.horizontal == 'centered':
            self.centered_radio.setChecked(True)
        elif config.horizontal == 'left':
            self.left_radio.setChecked(True)
        else:
            self.right_radio.setChecked(True)

        self.margin_x_spin.setValue(config.margin_x)
        self.x_offset_spin.setValue(config.x_offset)
        self.width_spin.setValue(config.width)

        if hasattr(self, 'enabled_checkbox'):
            self.enabled_checkbox.setChecked(config.enabled)

        self._updating = False


class LayoutConfigTab(QWidget):
    """Onglet de configuration du layout OCR dans les paramètres"""

    layout_config_changed = pyqtSignal(LayoutConfig)  # Émis quand config appliquée

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = LayoutConfigManager()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # En-tête
        header = QLabel("🎯 Configuration du Layout de Litho")
        header.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {LorealStyles.COLORS['primary']};")
        main_layout.addWidget(header)

        description = QLabel(
            "Configurez les zones de détection pour un positionnement précis des erreurs visuelles."
        )
        description.setStyleSheet("color: #666; font-size: 11px;")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        # Barre de préréglages et actions
        presets_layout = QHBoxLayout()

        presets_layout.addWidget(QLabel("Préréglages:"))

        self.presets_combo = QComboBox()
        self.presets_combo.addItem("Default Layout")
        self.presets_combo.setFixedWidth(200)
        presets_layout.addWidget(self.presets_combo)

        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setToolTip("Sauvegarder la configuration actuelle")
        save_btn.clicked.connect(self.save_config)
        presets_layout.addWidget(save_btn)

        import_btn = QPushButton("📥 Importer")
        import_btn.setToolTip("Importer une configuration depuis un fichier JSON")
        import_btn.clicked.connect(self.import_config)
        presets_layout.addWidget(import_btn)

        presets_layout.addStretch()
        main_layout.addLayout(presets_layout)

        # Split layout : zones à gauche, preview à droite
        content_layout = QHBoxLayout()

        # Scroll area pour les zones (gauche)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumWidth(500)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)

        # Créer widgets pour chaque zone
        self.zone_widgets = {}
        zone_order = ['shade_number', 'shade_name', '4_digits', 'description', 'franchise']

        for zone_name in zone_order:
            zone_config = self.config_manager.get_zone_config(zone_name)
            if zone_config:
                widget = ZoneConfigWidget(zone_name, zone_config, self)
                widget.config_changed.connect(self.on_zone_config_changed)
                self.zone_widgets[zone_name] = widget
                scroll_layout.addWidget(widget)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        content_layout.addWidget(scroll)

        # Preview canvas (droite)
        preview_group = QGroupBox("🔍 Aperçu Visuel")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)

        facing_layout = QHBoxLayout()
        facing_layout.addWidget(QLabel("FACING (colonnes):"))
        self.facing_spin = QDoubleSpinBox()
        self.facing_spin.setRange(1, 12)
        self.facing_spin.setDecimals(0)
        self.facing_spin.setValue(6)
        self.facing_spin.valueChanged.connect(self.update_preview)
        facing_layout.addWidget(self.facing_spin)

        facing_layout.addSpacing(20)

        facing_layout.addWidget(QLabel("TIERS (lignes):"))
        self.tiers_spin = QDoubleSpinBox()
        self.tiers_spin.setRange(1, 4)
        self.tiers_spin.setDecimals(0)
        self.tiers_spin.setValue(1)
        self.tiers_spin.valueChanged.connect(self.update_preview)
        facing_layout.addWidget(self.tiers_spin)

        facing_layout.addStretch()
        preview_layout.addLayout(facing_layout)

        self.preview_canvas = LayoutPreviewCanvas()
        self.preview_canvas.set_config(self.config_manager.current_config, 6, 1)
        preview_layout.addWidget(self.preview_canvas)

        content_layout.addWidget(preview_group)

        main_layout.addLayout(content_layout)

        # Boutons d'actions en bas
        actions_layout = QHBoxLayout()

        reset_btn = QPushButton("🔄 Réinitialiser aux valeurs par défaut")
        reset_btn.clicked.connect(self.reset_to_default)
        actions_layout.addWidget(reset_btn)

        apply_btn = QPushButton("✅ Appliquer la configuration")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {LorealStyles.COLORS['primary_dark']};
            }}
        """)
        apply_btn.clicked.connect(self.apply_config)
        actions_layout.addWidget(apply_btn)

        export_btn = QPushButton("📤 Exporter...")
        export_btn.clicked.connect(self.export_config)
        actions_layout.addWidget(export_btn)

        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

    def on_zone_config_changed(self, zone_name: str, new_config: ZoneConfig):
        """Appelé quand une zone est modifiée"""
        self.config_manager.update_zone_config(zone_name, new_config)
        self.update_preview()

    def update_preview(self):
        """Met à jour le preview canvas"""
        facing = int(self.facing_spin.value())
        num_tiers = int(self.tiers_spin.value())
        self.preview_canvas.set_config(self.config_manager.current_config, facing, num_tiers)

    def apply_config(self):
        """Applique la configuration"""
        self.config_manager.save_current_config()
        self.layout_config_changed.emit(self.config_manager.current_config)
        QMessageBox.information(
            self,
            "Configuration appliquée",
            "La configuration du layout a été appliquée avec succès!\n\n"
            "Les rectangles d'erreur seront repositionnés lors du prochain chargement de litho."
        )

    def reset_to_default(self):
        """Réinitialise aux valeurs par défaut"""
        reply = QMessageBox.question(
            self,
            "Confirmer la réinitialisation",
            "Êtes-vous sûr de vouloir réinitialiser aux valeurs par défaut?\n"
            "Les modifications non sauvegardées seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_to_default()

            # Mettre à jour tous les widgets
            for zone_name, widget in self.zone_widgets.items():
                zone_config = self.config_manager.get_zone_config(zone_name)
                if zone_config:
                    widget.set_config(zone_config)

            self.update_preview()
            QMessageBox.information(self, "Réinitialisation", "Configuration réinitialisée aux valeurs par défaut!")

    def save_config(self):
        """Sauvegarde la configuration actuelle"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder configuration",
            str(self.config_manager.config_dir / "my_layout.json"),
            "JSON Files (*.json)"
        )

        if filename:
            try:
                self.config_manager.current_config.save(Path(filename))
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Configuration sauvegardée :\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors de la sauvegarde :\n{str(e)}"
                )

    def import_config(self):
        """Importe une configuration"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Importer configuration",
            str(self.config_manager.config_dir),
            "JSON Files (*.json)"
        )

        if filename:
            try:
                config = LayoutConfig.load(Path(filename))
                self.config_manager.set_config(config)

                # Mettre à jour tous les widgets
                for zone_name, widget in self.zone_widgets.items():
                    zone_config = self.config_manager.get_zone_config(zone_name)
                    if zone_config:
                        widget.set_config(zone_config)

                self.update_preview()
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Configuration importée :\n{config.name}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors de l'import :\n{str(e)}"
                )

    def export_config(self):
        """Exporte la configuration"""
        self.save_config()

    def refresh_config(self):
        """Rafraîchit l'affichage avec la config actuelle"""
        for zone_name, widget in self.zone_widgets.items():
            zone_config = self.config_manager.get_zone_config(zone_name)
            if zone_config:
                widget.set_config(zone_config)
        self.update_preview()
