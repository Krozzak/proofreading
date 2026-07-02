# ui/table_presets_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QInputDialog,
                             QMessageBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from ..utils.styles import LorealStyles
import json


class TablePreset:
    """Représente une configuration de table sauvegardée"""

    def __init__(self, name, visible_columns=None, column_order=None,
                 column_widths=None, frozen_columns=None):
        self.name = name
        self.visible_columns = visible_columns or []
        self.column_order = column_order or []
        self.column_widths = column_widths or {}
        self.frozen_columns = frozen_columns or []

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'name': self.name,
            'visible_columns': self.visible_columns,
            'column_order': self.column_order,
            'column_widths': self.column_widths,
            'frozen_columns': self.frozen_columns
        }

    @staticmethod
    def from_dict(data):
        """Crée depuis un dictionnaire"""
        return TablePreset(
            name=data.get('name', 'Preset'),
            visible_columns=data.get('visible_columns', []),
            column_order=data.get('column_order', []),
            column_widths=data.get('column_widths', {}),
            frozen_columns=data.get('frozen_columns', [])
        )


class TablePresetsDialog(QDialog):
    """Dialogue pour gérer les presets de table"""

    preset_selected = pyqtSignal(TablePreset)  # Émis quand un preset est sélectionné

    def __init__(self, current_presets=None, parent=None):
        super().__init__(parent)
        self.presets = current_presets or self.get_default_presets()
        self.selected_preset = None
        self.setup_ui()
        self.load_presets()

    def get_default_presets(self):
        """Retourne les presets par défaut"""
        return [
            TablePreset(
                name="Vue Complète",
                visible_columns=["LITHO", "DESCRIPTION", "UPC", "PRODUCT DESCRIPTION",
                               "SHADE NAME", "SHADE NUMBER", "FACING", "4 DIGITS",
                               "Val. Teinte", "Val. Nom", "Val. Digits", "Val. Global"],
                column_order=list(range(12)),
                column_widths={},
                frozen_columns=[]
            ),
            TablePreset(
                name="Vue Validation",
                visible_columns=["LITHO", "UPC", "SHADE NAME", "SHADE NUMBER",
                               "Val. Teinte", "Val. Nom", "Val. Global"],
                column_order=[0, 2, 4, 5, 8, 9, 11],
                column_widths={},
                frozen_columns=[0]
            ),
            TablePreset(
                name="Vue Compact",
                visible_columns=["LITHO", "SHADE NAME", "SHADE NUMBER", "Val. Global"],
                column_order=[0, 4, 5, 11],
                column_widths={},
                frozen_columns=[]
            ),
            TablePreset(
                name="Vue Export",
                visible_columns=["LITHO", "DESCRIPTION", "UPC", "SHADE NAME",
                               "SHADE NUMBER", "FACING"],
                column_order=[0, 1, 2, 4, 5, 6],
                column_widths={},
                frozen_columns=[]
            ),
        ]

    def setup_ui(self):
        self.setWindowTitle("Gestion des Presets de Table")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Main content
        content_layout = QHBoxLayout()

        # Liste des presets
        presets_layout = QVBoxLayout()
        presets_label = QLabel("📋 Presets disponibles:")
        presets_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        presets_layout.addWidget(presets_label)

        self.presets_list = QListWidget()
        self.presets_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                background: white;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background: {LorealStyles.COLORS['primary']};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {LorealStyles.COLORS['background']};
            }}
        """)
        self.presets_list.itemDoubleClicked.connect(self.apply_preset)
        self.presets_list.itemSelectionChanged.connect(self.on_selection_changed)
        presets_layout.addWidget(self.presets_list)

        content_layout.addLayout(presets_layout, stretch=2)

        # Boutons d'action
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.apply_btn = QPushButton("✅ Appliquer")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_preset)
        self.apply_btn.setEnabled(False)
        actions_layout.addWidget(self.apply_btn)

        self.new_btn = QPushButton("➕ Nouveau")
        self.new_btn.clicked.connect(self.create_new_preset)
        actions_layout.addWidget(self.new_btn)

        self.rename_btn = QPushButton("✏️ Renommer")
        self.rename_btn.clicked.connect(self.rename_preset)
        self.rename_btn.setEnabled(False)
        actions_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("rejectButton")
        self.delete_btn.clicked.connect(self.delete_preset)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)

        actions_layout.addStretch()

        content_layout.addLayout(actions_layout, stretch=1)

        layout.addLayout(content_layout)

        # Footer
        footer = self.create_footer()
        layout.addWidget(footer)

    def create_header(self):
        """Crée le header"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(4)

        title = QLabel("⚙️ Gestion des Presets de Table")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {LorealStyles.COLORS['text_primary']};
        """)
        header_layout.addWidget(title)

        subtitle = QLabel("Sauvegardez et chargez différentes configurations de colonnes")
        subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {LorealStyles.COLORS['text_secondary']};
        """)
        header_layout.addWidget(subtitle)

        return header

    def create_footer(self):
        """Crée le footer"""
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)

        info_label = QLabel("💡 Double-cliquez sur un preset pour l'appliquer")
        info_label.setStyleSheet(f"""
            color: {LorealStyles.COLORS['text_secondary']};
            font-size: 10px;
            font-style: italic;
        """)
        footer_layout.addWidget(info_label)

        footer_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.reject)
        footer_layout.addWidget(close_btn)

        return footer

    def load_presets(self):
        """Charge les presets dans la liste"""
        self.presets_list.clear()

        for preset in self.presets:
            item = QListWidgetItem()

            # Icône selon le type
            icon = "📌" if preset.name in ["Vue Complète", "Vue Validation", "Vue Compact", "Vue Export"] else "📄"

            item.setText(f"{icon} {preset.name}")
            item.setData(Qt.ItemDataRole.UserRole, preset)

            self.presets_list.addItem(item)

    def on_selection_changed(self):
        """Callback quand la sélection change"""
        has_selection = len(self.presets_list.selectedItems()) > 0
        self.apply_btn.setEnabled(has_selection)
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def apply_preset(self):
        """Applique le preset sélectionné"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            return

        preset = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.selected_preset = preset
        self.preset_selected.emit(preset)
        self.accept()

    def create_new_preset(self):
        """Crée un nouveau preset"""
        name, ok = QInputDialog.getText(
            self,
            "Nouveau Preset",
            "Nom du preset:"
        )

        if ok and name:
            # Vérifier que le nom n'existe pas déjà
            if any(p.name == name for p in self.presets):
                QMessageBox.warning(self, "Erreur", f"Un preset nommé '{name}' existe déjà.")
                return

            # Créer un preset vide
            new_preset = TablePreset(name=name)
            self.presets.append(new_preset)
            self.load_presets()

            QMessageBox.information(
                self,
                "Preset créé",
                f"Le preset '{name}' a été créé.\n\n"
                "Configurez votre table comme souhaité, puis sauvegardez la configuration."
            )

    def rename_preset(self):
        """Renomme le preset sélectionné"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            return

        preset = selected_items[0].data(Qt.ItemDataRole.UserRole)

        new_name, ok = QInputDialog.getText(
            self,
            "Renommer Preset",
            "Nouveau nom:",
            text=preset.name
        )

        if ok and new_name and new_name != preset.name:
            # Vérifier que le nom n'existe pas déjà
            if any(p.name == new_name for p in self.presets if p != preset):
                QMessageBox.warning(self, "Erreur", f"Un preset nommé '{new_name}' existe déjà.")
                return

            preset.name = new_name
            self.load_presets()

    def delete_preset(self):
        """Supprime le preset sélectionné"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            return

        preset = selected_items[0].data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer le preset '{preset.name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.presets.remove(preset)
            self.load_presets()

    def get_presets(self):
        """Retourne la liste des presets"""
        return self.presets
