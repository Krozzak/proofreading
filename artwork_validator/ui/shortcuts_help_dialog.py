# ui/shortcuts_help_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QLabel, QPushButton, QLineEdit,
                             QHeaderView, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..core.command_registry import CommandRegistry
from ..utils.styles import LorealStyles


class ShortcutsHelpDialog(QDialog):
    """
    Dialogue d'aide affichant tous les raccourcis clavier
    Organisés par catégorie, avec recherche
    """

    def __init__(self, command_registry: CommandRegistry, parent=None):
        super().__init__(parent)
        self.command_registry = command_registry
        self.all_commands = []
        self.setup_ui()
        self.load_shortcuts()

    def setup_ui(self):
        self.setWindowTitle("Raccourcis Clavier")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 14px;")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un raccourci ou une action...")
        self.search_input.textChanged.connect(self.filter_shortcuts)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Table des raccourcis
        self.shortcuts_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.shortcuts_table)

        # Footer avec boutons
        footer = self.create_footer()
        layout.addWidget(footer)

    def create_header(self):
        """Crée le header du dialogue"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(4)

        title = QLabel("⌨️ Référence des Raccourcis Clavier")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {LorealStyles.COLORS['text_primary']};
        """)
        header_layout.addWidget(title)

        subtitle = QLabel("Liste complète de tous les raccourcis disponibles")
        subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {LorealStyles.COLORS['text_secondary']};
        """)
        header_layout.addWidget(subtitle)

        return header

    def setup_table(self):
        """Configure la table des raccourcis"""
        self.shortcuts_table.setColumnCount(4)
        self.shortcuts_table.setHorizontalHeaderLabels([
            "Catégorie", "Action", "Description", "Raccourci"
        ])

        # Configuration colonnes
        header = self.shortcuts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Style de la table
        self.shortcuts_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                background: white;
                gridline-color: {LorealStyles.COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {LorealStyles.COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
        """)

        # Désactiver l'édition
        self.shortcuts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Sélection par ligne
        self.shortcuts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def load_shortcuts(self):
        """Charge tous les raccourcis depuis le registre"""
        self.all_commands = self.command_registry.get_all_commands()

        # Filtrer les commandes qui ont un raccourci
        commands_with_shortcuts = [cmd for cmd in self.all_commands if cmd.shortcut]

        # Trier par catégorie puis par nom
        commands_with_shortcuts.sort(key=lambda x: (x.category, x.name))

        # Remplir la table
        self.populate_table(commands_with_shortcuts)

    def populate_table(self, commands):
        """Remplit la table avec les commandes"""
        self.shortcuts_table.setRowCount(len(commands))

        for row, command in enumerate(commands):
            # Catégorie
            category_item = QTableWidgetItem(command.category)
            category_item.setFont(QFont("", 10, QFont.Weight.Bold))
            self.shortcuts_table.setItem(row, 0, category_item)

            # Action (avec icône si disponible)
            action_text = f"{command.icon} {command.name}" if command.icon else command.name
            action_item = QTableWidgetItem(action_text)
            self.shortcuts_table.setItem(row, 1, action_item)

            # Description
            desc_item = QTableWidgetItem(command.description)
            desc_item.setForeground(Qt.GlobalColor.darkGray)
            self.shortcuts_table.setItem(row, 2, desc_item)

            # Raccourci
            shortcut_item = QTableWidgetItem(command.shortcut)
            shortcut_item.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            shortcut_item.setForeground(Qt.GlobalColor.blue)
            shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.shortcuts_table.setItem(row, 3, shortcut_item)

    def filter_shortcuts(self):
        """Filtre les raccourcis selon la recherche"""
        query = self.search_input.text().lower()

        if not query:
            # Recharger tous les raccourcis
            self.load_shortcuts()
            return

        # Filtrer les commandes
        filtered_commands = []
        for command in self.all_commands:
            if not command.shortcut:
                continue

            # Recherche dans nom, description, raccourci ou catégorie
            if (query in command.name.lower() or
                query in command.description.lower() or
                query in command.shortcut.lower() or
                query in command.category.lower()):
                filtered_commands.append(command)

        # Trier
        filtered_commands.sort(key=lambda x: (x.category, x.name))

        # Remplir la table
        self.populate_table(filtered_commands)

    def create_footer(self):
        """Crée le footer avec boutons"""
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)

        # Info
        info_label = QLabel(f"💡 Conseil : Utilisez Ctrl+K pour ouvrir la palette de commandes")
        info_label.setStyleSheet(f"""
            color: {LorealStyles.COLORS['text_secondary']};
            font-size: 10px;
            font-style: italic;
        """)
        footer_layout.addWidget(info_label)

        footer_layout.addStretch()

        # Bouton Fermer
        close_btn = QPushButton("Fermer")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        return footer
