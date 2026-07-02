# ui/excel_validator_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QTextEdit, QFrame, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ..utils.styles import LorealStyles

class ExcelValidatorDialog(QDialog):
    def __init__(self, validation_result, parent=None):
        super().__init__(parent)
        self.validation_result = validation_result
        self.setWindowTitle("Vérification du fichier Excel")
        self.setMinimumSize(600, 540)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # En-tête
        header = self.create_header()
        layout.addWidget(header)

        # Tableau des colonnes obligatoires
        table_label = QLabel("📋 Vérification des colonnes obligatoires :")
        table_label.setStyleSheet("font-size: 12px; font-weight: 600; margin-top: 8px;")
        layout.addWidget(table_label)

        self.columns_table = self.create_columns_table()
        layout.addWidget(self.columns_table)

        # Info colonnes optionnelles
        optional_info = self.create_optional_info()
        layout.addWidget(optional_info)

        # Aide / format attendu
        help_label = QLabel("📖 Format attendu :")
        help_label.setStyleSheet("font-size: 12px; font-weight: 600; margin-top: 12px;")
        layout.addWidget(help_label)

        help_text = self.create_help_text()
        layout.addWidget(help_text)

        # Boutons
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)

    def create_header(self):
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        header_layout = QHBoxLayout()
        header_frame.setLayout(header_layout)
        header_layout.setContentsMargins(8, 8, 8, 8)

        is_valid = self.validation_result.get('is_valid', False)
        missing_required = self.validation_result.get('missing_columns', [])
        missing_optional = self.validation_result.get('missing_optional_columns', [])

        if is_valid:
            icon = QLabel("✅")
            title = "Fichier Excel valide"
            subtitle = "Toutes les colonnes obligatoires sont présentes"
            title_color = LorealStyles.COLORS['success']
        else:
            icon = QLabel("❌")
            title = "Fichier Excel invalide"
            subtitle = f"{len(missing_required)} colonne(s) obligatoire(s) manquante(s)"
            title_color = LorealStyles.COLORS['error']

        icon.setStyleSheet("font-size: 24px;")
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {title_color};")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"font-size: 11px; color: {LorealStyles.COLORS['text_secondary']};")

        # Ajout d’une ligne d’info non bloquante pour les optionnelles
        if missing_optional:
            opt_label = QLabel(f"ℹ️  {len(missing_optional)} colonne(s) optionnelle(s) manquante(s) (non bloquant).")
            opt_label.setStyleSheet(f"font-size: 11px; color: {LorealStyles.COLORS['text_secondary']};")
            text_layout.addWidget(title_label)
            text_layout.addWidget(subtitle_label)
            text_layout.addWidget(opt_label)
        else:
            text_layout.addWidget(title_label)
            text_layout.addWidget(subtitle_label)

        header_layout.addWidget(icon)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        return header_frame

    def create_columns_table(self):
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Statut", "Colonne Obligatoire", "Description"])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setMaximumHeight(240)

        # ✅ Colonnes OBLIGATOIRES
        required_columns = [
            ('LITHO', 'Code de la litho (ex: 12345)'),
            ('DECRIPTION', 'Description de la litho'),
            ('UPC SEQUENCE', 'Séquence UPC'),
            ('UPC POSITION', 'Position de l\'UPC'),
            ('UPC', 'Code UPC du produit'),
            ('PRODUCT DESCRIPTION', 'Description du produit'),
            ('SHADE NAME', 'Nom de la teinte'),
            ('SHADE NUMBER', 'Numéro de la teinte'),
            ('PRODUCT FACING SL', 'Nombre de facings ou type (FRAME, SPACE_SAVER)'),
            ('4 DIGITS', 'Code 4 chiffres (pour Walmart)'),
        ]

        table.setRowCount(len(required_columns))
        found = set(self.validation_result.get('found_columns', []))

        for row, (name, desc) in enumerate(required_columns):
            present = name in found
            status_item = QTableWidgetItem("✅ Présente" if present else "❌ Manquante")
            status_item.setBackground(QColor(LorealStyles.COLORS['success'] if present else LorealStyles.COLORS['error']))
            status_item.setForeground(QColor("white"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("Consolas", 10))
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            desc_item = QTableWidgetItem(desc)
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            table.setItem(row, 0, status_item)
            table.setItem(row, 1, name_item)
            table.setItem(row, 2, desc_item)

        return table

    def create_optional_info(self):
        """Encart listant l'état des colonnes optionnelles (non bloquant)."""
        optional = ['NEW', 'STATUS', 'PRODUCT', 'TIER', 'SEASON']
        found = set(self.validation_result.get('found_columns', []))
        missing_opt = [c for c in optional if c not in found]
        present_opt = [c for c in optional if c in found]

        text = "🔧 Colonnes optionnelles (recommandées mais non obligatoires):\n"
        text += f"• Présentes : {', '.join(present_opt) if present_opt else 'Aucune'}\n"
        text += f"• Manquantes : {', '.join(missing_opt) if missing_opt else 'Aucune'}\n"
        text += "Ces colonnes améliorent les statistiques et certains rapports, mais leur absence ne bloque pas l’import."

        box = QTextEdit()
        box.setReadOnly(True)
        box.setMaximumHeight(90)
        box.setText(text)
        box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
                padding: 8px;
            }}
        """)
        return box

    def create_help_text(self):
        help_text = QTextEdit()
        help_text.setMaximumHeight(140)
        help_text.setReadOnly(True)

        help_content = """
📝 Instructions pour préparer votre fichier Excel :

1) Colonnes OBLIGATOIRES (le chargement échoue si l’une manque) :
   LITHO, DECRIPTION, UPC SEQUENCE, UPC POSITION, UPC, PRODUCT DESCRIPTION,
   SHADE NAME, SHADE NUMBER, PRODUCT FACING SL, 4 DIGITS

2) Colonnes OPTIONNELLES (fortement recommandées) :
   NEW, STATUS, PRODUCT, TIER, SEASON

3) Les noms doivent être EXACTS (majuscules, espaces) et en première ligne.
4) Les colonnes supplémentaires sont ACCEPTÉES (le mappage se fait par nom).
        """.strip()

        help_text.setText(help_content)
        help_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
                padding: 8px;
            }}
        """)
        return help_text

    def create_buttons(self):
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        if self.validation_result.get('is_valid', False):
            continue_btn = QPushButton("✅ Continuer le chargement")
            continue_btn.setObjectName("approveButton")
            continue_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(continue_btn)
        else:
            retry_btn = QPushButton("📁 Choisir un autre fichier")
            retry_btn.setObjectName("primaryButton")
            retry_btn.clicked.connect(self.reject)

            cancel_btn = QPushButton("❌ Annuler")
            cancel_btn.clicked.connect(self.reject)

            buttons_layout.addWidget(retry_btn)
            buttons_layout.addWidget(cancel_btn)

        return buttons_layout


class ExcelFormatHelpDialog(QDialog):
    """Dialogue d'aide avant la sélection du fichier Excel"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Format de fichier Excel requis")
        self.setMinimumSize(500, 420)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("📊 Format de fichier Excel requis")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {LorealStyles.COLORS['primary']};
                padding: 8px;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(header)

        description = QLabel("Votre fichier Excel doit contenir les colonnes suivantes :")
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 11px; margin-bottom: 12px;")
        layout.addWidget(description)

        columns_text = QTextEdit()
        columns_text.setMaximumHeight(230)
        columns_text.setReadOnly(True)

        columns_content = """
📋 Colonnes OBLIGATOIRES :
• LITHO
• DECRIPTION
• UPC SEQUENCE
• UPC POSITION
• UPC
• PRODUCT DESCRIPTION
• SHADE NAME
• SHADE NUMBER
• PRODUCT FACING SL
• 4 DIGITS

🔧 Colonnes OPTIONNELLES (recommandées, non bloquantes) :
• NEW
• STATUS
• PRODUCT
• TIER
• SEASON
        """.strip()

        columns_text.setText(columns_content)
        columns_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }}
        """)
        layout.addWidget(columns_text)

        note = QLabel("⚠️ Les noms de colonnes doivent être EXACTS (majuscules et espaces). Les colonnes supplémentaires sont acceptées.")
        note.setWordWrap(True)
        note.setStyleSheet(f"""
            QLabel {{
                background-color: {LorealStyles.COLORS['warning']};
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }}
        """)
        layout.addWidget(note)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        continue_btn = QPushButton("📁 Sélectionner le fichier Excel")
        continue_btn.setObjectName("primaryButton")
        continue_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(continue_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)