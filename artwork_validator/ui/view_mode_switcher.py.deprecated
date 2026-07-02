# ui/view_mode_switcher.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal
from ..utils.styles import LorealStyles


class ViewModeSwitcher(QWidget):
    """
    Toggle entre les 4 modes de vue:
    - Overview (liste compacte)
    - Validation (vue détaillée actuelle)
    - Cards (grid de cards - à venir)
    - Settings (paramètres et configuration)
    """

    view_changed = pyqtSignal(str)  # 'overview', 'validation', 'cards', 'settings'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_view = 'validation'
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        label = QLabel("Vue:")
        label.setStyleSheet("font-weight: 600; font-size: 11px;")
        layout.addWidget(label)

        # Boutons toggle
        self.overview_btn = self.create_view_button("📋", "Overview", "overview")
        self.validation_btn = self.create_view_button("🔍", "Validation", "validation")
        self.cards_btn = self.create_view_button("🎴", "Cards", "cards")
        self.settings_btn = self.create_view_button("⚙️", "Paramètres", "settings")

        # Validation active par défaut
        self.validation_btn.setChecked(True)

        layout.addWidget(self.overview_btn)
        layout.addWidget(self.validation_btn)
        layout.addWidget(self.cards_btn)
        layout.addWidget(self.settings_btn)

    def create_view_button(self, icon, text, view_name):
        """Crée un bouton toggle pour une vue"""
        btn = QPushButton(f"{icon} {text}")
        btn.setCheckable(True)
        btn.setFixedHeight(32)
        btn.clicked.connect(lambda: self.switch_view(view_name))

        btn.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background: white;
            }}
            QPushButton:checked {{
                background: {LorealStyles.COLORS['primary']};
                color: white;
                border-color: {LorealStyles.COLORS['primary']};
            }}
            QPushButton:hover:!checked {{
                background: {LorealStyles.COLORS['background']};
            }}
        """)

        return btn

    def switch_view(self, view_name):
        """Bascule vers une vue"""
        if view_name == self.current_view:
            return

        # Uncheck les autres
        self.overview_btn.setChecked(view_name == 'overview')
        self.validation_btn.setChecked(view_name == 'validation')
        self.cards_btn.setChecked(view_name == 'cards')
        self.settings_btn.setChecked(view_name == 'settings')

        self.current_view = view_name
        self.view_changed.emit(view_name)

    def set_current_view(self, view_name):
        """Définit la vue courante (appelé programmatiquement)"""
        self.switch_view(view_name)
