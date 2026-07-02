# ui/command_palette.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QListWidget,
                             QListWidgetItem, QLabel, QHBoxLayout, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ..core.command_registry import CommandRegistry
from ..utils.styles import LorealStyles


class CommandPaletteItem(QWidget):
    """Widget custom pour afficher une commande dans la liste"""

    def __init__(self, command, query=""):
        super().__init__()
        self.command = command
        self.setup_ui(query)

    def setup_ui(self, query):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Icône
        if self.command.icon:
            icon_label = QLabel(self.command.icon)
            icon_label.setStyleSheet("font-size: 16px;")
            layout.addWidget(icon_label)

        # Nom et description
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # Nom avec highlight
        name_label = QLabel()
        name_html = self.highlight_query(self.command.name, query)
        name_label.setText(f"<b>{name_html}</b>")
        name_label.setStyleSheet("font-size: 13px; color: #1a1a1a;")
        text_layout.addWidget(name_label)

        # Description
        desc_label = QLabel(self.command.description)
        desc_label.setStyleSheet("font-size: 10px; color: #666;")
        text_layout.addWidget(desc_label)

        layout.addWidget(text_container, stretch=1)

        # Catégorie badge
        category_label = QLabel(self.command.category)
        category_label.setStyleSheet(f"""
            background: {LorealStyles.COLORS['background']};
            color: {LorealStyles.COLORS['text_secondary']};
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
        """)
        layout.addWidget(category_label)

        # Raccourci
        if self.command.shortcut:
            shortcut_label = QLabel(self.command.shortcut)
            shortcut_label.setStyleSheet(f"""
                background: {LorealStyles.COLORS['primary']};
                color: white;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                font-family: monospace;
            """)
            layout.addWidget(shortcut_label)

    def highlight_query(self, text, query):
        """Surligne les termes de recherche dans le texte"""
        if not query:
            return text

        # Simple highlighting - peut être amélioré
        query_lower = query.lower()
        text_lower = text.lower()
        index = text_lower.find(query_lower)

        if index >= 0:
            before = text[:index]
            match = text[index:index + len(query)]
            after = text[index + len(query):]
            return f'{before}<span style="background-color: #fef08a; color: #000;">{match}</span>{after}'

        return text


class CommandPalette(QDialog):
    """
    Palette de commandes style VS Code / Sublime Text
    Ctrl+K pour ouvrir, recherche fuzzy, exécution instantanée
    """

    def __init__(self, command_registry: CommandRegistry, parent=None):
        super().__init__(parent)
        self.command_registry = command_registry
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.setWindowTitle("Palette de Commandes")
        self.setModal(True)
        self.setMinimumSize(700, 500)

        # Pas de bordure de fenêtre pour effet moderne
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container principal avec border radius
        main_container = QWidget()
        main_container.setObjectName("paletteContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tapez une commande ou un raccourci...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 14px;
                padding: 8px 12px;
                border: 2px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                background: white;
            }}
            QLineEdit:focus {{
                border-color: {LorealStyles.COLORS['primary']};
            }}
        """)
        main_layout.addWidget(self.search_input)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                background: white;
                font-size: 12px;
            }}
            QListWidget::item {{
                border: none;
                padding: 0;
            }}
            QListWidget::item:selected {{
                background: {LorealStyles.COLORS['primary']};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {LorealStyles.COLORS['background']};
            }}
        """)
        self.results_list.itemActivated.connect(self.execute_selected_command)
        main_layout.addWidget(self.results_list)

        # Footer avec aide
        footer = QLabel("↑↓ Naviguer  •  Enter Exécuter  •  Esc Fermer")
        footer.setStyleSheet(f"""
            color: {LorealStyles.COLORS['text_secondary']};
            font-size: 10px;
            padding: 4px;
        """)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        layout.addWidget(main_container)

    def create_header(self):
        """Crée le header de la palette"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)

        title = QLabel("⚡ Palette de Commandes")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {LorealStyles.COLORS['text_primary']};
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Compteur de résultats
        self.results_count_label = QLabel("0 commandes")
        self.results_count_label.setStyleSheet(f"""
            font-size: 11px;
            color: {LorealStyles.COLORS['text_secondary']};
        """)
        header_layout.addWidget(self.results_count_label)

        return header

    def setup_styles(self):
        """Applique les styles glassmorphism"""
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(255, 255, 255, 0.98);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
            #paletteContainer {{
                background: transparent;
            }}
        """)

        # Effet d'ombre (simulé avec bordure)
        self.setGraphicsEffect(None)  # On pourrait ajouter QGraphicsDropShadowEffect

    def showEvent(self, event):
        """Appelé quand le dialogue s'affiche"""
        super().showEvent(event)
        # Focus sur l'input
        self.search_input.setFocus()
        self.search_input.clear()
        # Charger toutes les commandes par défaut
        self.perform_search()

    def on_search_changed(self, text):
        """Callback quand le texte de recherche change"""
        # Debounce de 300ms
        self.search_timer.stop()
        self.search_timer.start(300)

    def perform_search(self):
        """Effectue la recherche dans le registre de commandes"""
        query = self.search_input.text()
        results = self.command_registry.search(query)

        # Clear la liste
        self.results_list.clear()

        # Ajouter les résultats
        for command in results[:50]:  # Limiter à 50 résultats
            item = QListWidgetItem(self.results_list)
            widget = CommandPaletteItem(command, query)

            item.setSizeHint(widget.sizeHint())
            self.results_list.setItemWidget(item, widget)

            # Stocker la commande dans l'item pour exécution
            item.setData(Qt.ItemDataRole.UserRole, command)

        # Sélectionner le premier résultat
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

        # Mettre à jour le compteur
        count = len(results)
        self.results_count_label.setText(f"{count} commande{'s' if count > 1 else ''}")

    def execute_selected_command(self, item):
        """Exécute la commande sélectionnée"""
        command = item.data(Qt.ItemDataRole.UserRole)
        if command:
            self.accept()  # Fermer le dialogue
            command.execute()

    def keyPressEvent(self, event):
        """Gère les événements clavier"""
        # Escape → Fermer
        if event.key() == Qt.Key.Key_Escape:
            self.reject()

        # Enter → Exécuter commande sélectionnée
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = self.results_list.currentItem()
            if current_item:
                self.execute_selected_command(current_item)

        # Up/Down → Navigation (géré automatiquement par QListWidget)
        else:
            super().keyPressEvent(event)
