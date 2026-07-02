# ui/brand_rules_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel,
                            QTextEdit, QScrollArea, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
from ..core.brand_configs.brand_registry import BrandRegistry
from ..utils.styles import LorealStyles


class BrandRulesTab(QWidget):
    """Tab pour afficher les règles de validation de toutes les marques configurées"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("Règles de Validation par Marque")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        main_layout.addWidget(header)

        # Description
        desc = QLabel(
            "Visualisez les règles de validation et les colonnes Excel requises "
            "pour chaque marque configurée dans le système."
        )
        desc.setStyleSheet("color: gray; margin-bottom: 8px;")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Scroll area pour les marques
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Ajouter une card pour chaque marque
        brands = BrandRegistry.get_all_brands()

        if brands:
            for brand in brands:
                card = self.create_brand_card(brand)
                scroll_layout.addWidget(card)
        else:
            no_brands_label = QLabel("Aucune marque configurée dans le système.")
            no_brands_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            no_brands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(no_brands_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def create_brand_card(self, brand):
        """Crée une card pour afficher les règles d'une marque"""
        card = QGroupBox(f"{brand.get_brand_display_name()} ({brand.get_brand_code()})")
        card.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                border: 2px solid {LorealStyles.COLORS['primary']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                border-radius: 3px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Validation rules
        rules_section = self.create_section(
            "📋 Règles de Validation",
            brand.get_validation_description(),
            is_code=True
        )
        layout.addWidget(rules_section)

        # Required columns
        req_cols = ', '.join(brand.get_required_columns())
        req_section = self.create_section(
            "✅ Colonnes Obligatoires",
            req_cols,
            color=LorealStyles.COLORS['success']
        )
        layout.addWidget(req_section)

        # Optional columns
        opt_cols = ', '.join(brand.get_optional_columns())
        if opt_cols:
            opt_section = self.create_section(
                "⚪ Colonnes Optionnelles",
                opt_cols,
                color="gray",
                italic=True
            )
            layout.addWidget(opt_section)

        # Validation flags
        flags_text = f"UPC Validation: {'✅ Activée' if brand.requires_upc_validation() else '❌ Désactivée'}\n"
        flags_text += f"4 DIGITS Validation: {'✅ Activée' if brand.requires_digits_validation() else '❌ Désactivée'}"
        flags_section = self.create_section("🚩 Options de Validation", flags_text)
        layout.addWidget(flags_section)

        card.setLayout(layout)
        return card

    def create_section(self, title, content, color=None, italic=False, is_code=False):
        """Crée une section avec titre et contenu"""
        section = QFrame()
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)

        # Title
        title_label = QLabel(title)
        title_style = "font-weight: 600; font-size: 11px;"
        if color:
            title_style += f" color: {color};"
        title_label.setStyleSheet(title_style)
        section_layout.addWidget(title_label)

        # Content
        if is_code:
            content_widget = QTextEdit()
            content_widget.setReadOnly(True)
            content_widget.setPlainText(content)
            content_widget.setMaximumHeight(120)
            content_widget.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {LorealStyles.COLORS['background']};
                    border: 1px solid {LorealStyles.COLORS['border']};
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 9px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
            """)
        else:
            content_widget = QLabel(content)
            content_widget.setWordWrap(True)
            style = "font-size: 10px; padding: 4px;"
            if color:
                style += f" color: {color};"
            if italic:
                style += " font-style: italic;"
            content_widget.setStyleSheet(style)

        section_layout.addWidget(content_widget)
        section.setLayout(section_layout)
        return section
