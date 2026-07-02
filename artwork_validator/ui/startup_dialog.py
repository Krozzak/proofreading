# ui/startup_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QListWidget, QListWidgetItem, QFrame,
                            QTextEdit, QGroupBox, QFileDialog, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..utils.styles import LorealStyles
from datetime import datetime

class StartupDialog(QDialog):
    """Dialogue de démarrage pour choisir une session ou commencer une nouvelle"""
    
    load_session_requested = pyqtSignal(str)  # Chemin du fichier de session
    new_session_requested = pyqtSignal()
    browse_folder_requested = pyqtSignal(str)  # Nouveau signal pour parcourir un dossier
    
    def __init__(self, available_sessions, current_sessions_folder, parent=None):
        super().__init__(parent)
        self.available_sessions = available_sessions
        self.current_sessions_folder = current_sessions_folder
        self.selected_session = None
        self.setWindowTitle("L'Oréal Litho Validator - Démarrage")
        self.setMinimumSize(700, 600)  # Plus large pour accommoder les nouveaux boutons
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # En-tête avec logo/titre
        header = self.create_header()
        layout.addWidget(header)
        
        # Affichage du dossier actuel
        folder_info = self.create_folder_info()
        layout.addWidget(folder_info)
        
        # Message de bienvenue
        welcome_msg = QLabel("Choisissez comment démarrer votre session de validation :")
        welcome_msg.setStyleSheet("font-size: 12px; margin-bottom: 8px; font-weight: 500;")
        welcome_msg.setWordWrap(True)
        layout.addWidget(welcome_msg)
        
        # Section sessions existantes
        sessions_group = self.create_sessions_group()
        layout.addWidget(sessions_group)
        
        # Section nouvelle session
        new_session_group = self.create_new_session_group()
        layout.addWidget(new_session_group)
        
        # Boutons
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)

    def create_folder_info(self):
        """Affiche les informations sur le dossier de sessions actuel"""
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout()
        info_frame.setLayout(layout)
        layout.setContentsMargins(8, 6, 8, 6)
        
        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet("font-size: 16px;")
        
        folder_text = QLabel(f"Dossier de sessions: {self.current_sessions_folder}")
        folder_text.setStyleSheet("font-size: 10px; font-weight: 500;")
        folder_text.setWordWrap(True)
        
        # Bouton pour changer de dossier
        change_folder_btn = QPushButton("📂 Parcourir...")
        change_folder_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 8px;
                font-size: 9px;
                min-height: 16px;
            }
        """)
        change_folder_btn.clicked.connect(self.browse_sessions_folder)
        
        layout.addWidget(folder_icon)
        layout.addWidget(folder_text)
        layout.addStretch()
        layout.addWidget(change_folder_btn)
        
        return info_frame
        
    def create_header(self):
        """Crée l'en-tête du dialogue"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        header_layout = QVBoxLayout()
        header.setLayout(header_layout)
        header_layout.setContentsMargins(8, 8, 8, 8)
        
        title = QLabel("🧪 LITHO VALIDATOR")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("L'Oréal Canada - Validation des Lithos")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                font-style: italic;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        return header
        
    def create_sessions_group(self):
        """Crée le groupe des sessions existantes"""
        group = QGroupBox(f"📂 Sessions disponibles ({len(self.available_sessions)} trouvée(s))")
        group.setStyleSheet("QGroupBox { font-weight: 600; font-size: 11px; }")
        
        layout = QVBoxLayout()
        group.setLayout(layout)
        layout.setContentsMargins(8, 12, 8, 8)
        
        if self.available_sessions:
            info_label = QLabel("Double-cliquez sur une session pour la charger :")
            info_label.setStyleSheet("font-size: 10px; color: #666; margin-bottom: 4px;")
            layout.addWidget(info_label)
            
            self.sessions_list = QListWidget()
            self.sessions_list.setMaximumHeight(150)
            self.sessions_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {LorealStyles.COLORS['background']};
                    border: 1px solid {LorealStyles.COLORS['border']};
                    border-radius: 4px;
                    font-size: 10px;
                }}
                QListWidget::item {{
                    padding: 8px;
                    margin: 1px;
                    border-radius: 3px;
                }}
                QListWidget::item:selected {{
                    background-color: {LorealStyles.COLORS['primary']};
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {LorealStyles.COLORS['background']};
                    border: 1px solid {LorealStyles.COLORS['primary']};
                }}
            """)
            
            # Remplir la liste des sessions
            for session in self.available_sessions:
                item_text = f"📁 {session['name']}"
                if session['updated']:
                    try:
                        updated_date = datetime.fromisoformat(session['updated'][:19])
                        item_text += f"\n   📅 Modifiée: {updated_date.strftime('%d/%m/%Y %H:%M')}"
                    except:
                        item_text += f"\n   📅 Modifiée: {session['updated'][:10]}"
                
                validations_count = session.get('validations_count', 0)
                if validations_count > 0:
                    item_text += f"\n   ✅ {validations_count} validation(s)"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, session['file_path'])
                self.sessions_list.addItem(item)
            
            # Connexion des signaux
            self.sessions_list.itemDoubleClicked.connect(self.on_session_double_clicked)
            self.sessions_list.itemSelectionChanged.connect(self.on_session_selection_changed)
            
            layout.addWidget(self.sessions_list)
        else:
            no_sessions_label = QLabel("Aucune session trouvée dans ce dossier.")
            no_sessions_label.setStyleSheet(f"""
                QLabel {{
                    color: {LorealStyles.COLORS['text_secondary']};
                    font-style: italic;
                    padding: 20px;
                    text-align: center;
                }}
            """)
            no_sessions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_sessions_label)
        
        return group
        
    def create_new_session_group(self):
        """Crée le groupe pour nouvelle session"""
        group = QGroupBox("🆕 Nouvelle session")
        group.setStyleSheet("QGroupBox { font-weight: 600; font-size: 11px; }")

        layout = QVBoxLayout()
        group.setLayout(layout)
        layout.setContentsMargins(8, 12, 8, 8)

        description = QTextEdit()
        description.setMaximumHeight(80)
        description.setReadOnly(True)
        description.setText(
            "Créer une nouvelle session de validation :\n"
            "• Sélectionner une marque\n"
            "• Choisir un dossier de PDFs à valider\n"
            "• Sélectionner un fichier Excel avec les données\n"
            "• Commencer la validation des lithos"
        )
        description.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
                padding: 8px;
            }}
        """)
        layout.addWidget(description)

        # 🆕 Brand selection section
        brand_section = QGroupBox("🏷️  Sélection de la marque")
        brand_section.setStyleSheet(f"""
            QGroupBox {{
                font-size: 11px;
                font-weight: 600;
                border: 1px solid {LorealStyles.COLORS['primary']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
        """)
        brand_layout = QVBoxLayout()
        brand_section.setLayout(brand_layout)
        brand_layout.setContentsMargins(8, 8, 8, 8)

        # Brand combo
        brand_select_layout = QHBoxLayout()
        brand_label = QLabel("Marque:")
        brand_label.setStyleSheet("font-weight: 600; font-size: 10px;")

        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                background-color: white;
                font-size: 10px;
                min-width: 200px;
            }}
            QComboBox:hover {{
                border: 1px solid {LorealStyles.COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)

        # 🆕 Populate brands from registry
        from ..core.brand_configs.brand_registry import BrandRegistry
        brands = BrandRegistry.get_all_brands()

        if brands:
            for brand in brands:
                display_text = f"{brand.get_brand_display_name()} ({brand.get_brand_code()})"
                self.brand_combo.addItem(display_text, brand.get_brand_code())
        else:
            # Fallback si registry vide
            self.brand_combo.addItem("Maybelline New York (MNY)", "MNY")

        brand_select_layout.addWidget(brand_label)
        brand_select_layout.addWidget(self.brand_combo, 1)
        brand_layout.addLayout(brand_select_layout)

        # Brand rules description
        rules_label = QLabel("Règles de validation:")
        rules_label.setStyleSheet("font-weight: 600; font-size: 10px; margin-top: 4px;")
        brand_layout.addWidget(rules_label)

        self.brand_rules_text = QTextEdit()
        self.brand_rules_text.setReadOnly(True)
        self.brand_rules_text.setMaximumHeight(120)
        self.brand_rules_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 6px;
                font-size: 9px;
                font-family: 'Consolas', 'Courier New', monospace;
                line-height: 1.3;
            }}
        """)
        brand_layout.addWidget(self.brand_rules_text)

        layout.addWidget(brand_section)

        # Connect signal to update rules when brand changes
        self.brand_combo.currentIndexChanged.connect(self.update_brand_rules_display)

        # Initial display of rules
        self.update_brand_rules_display()

        return group

    def browse_sessions_folder(self):
        """Permet de parcourir un autre dossier pour les sessions"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier contenant les sessions",
            self.current_sessions_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.browse_folder_requested.emit(folder)
            self.accept()  # Fermer le dialogue pour le rouvrir avec le nouveau dossier
        
    def create_buttons(self):
        """Crée les boutons du dialogue"""
        buttons_layout = QHBoxLayout()
        
        # Bouton pour parcourir un autre dossier
        browse_btn = QPushButton("📁 Parcourir un autre dossier...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 6px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        browse_btn.clicked.connect(self.browse_sessions_folder)
        buttons_layout.addWidget(browse_btn)
        
        buttons_layout.addStretch()
        
        # Bouton pour charger session sélectionnée
        if self.available_sessions:
            self.load_session_btn = QPushButton("📂 Charger la session sélectionnée")
            self.load_session_btn.setObjectName("primaryButton")
            self.load_session_btn.setEnabled(False)  # Désactivé tant qu'aucune session n'est sélectionnée
            self.load_session_btn.clicked.connect(self.load_selected_session)
            buttons_layout.addWidget(self.load_session_btn)
        
        # Bouton pour nouvelle session
        new_session_btn = QPushButton("🆕 Créer une nouvelle session")
        new_session_btn.setObjectName("approveButton")
        new_session_btn.clicked.connect(self.create_new_session)
        buttons_layout.addWidget(new_session_btn)
        
        # Bouton quitter
        quit_btn = QPushButton("❌ Quitter")
        quit_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(quit_btn)
        
        return buttons_layout
        
    def on_session_double_clicked(self, item):
        """Gère le double-clic sur une session"""
        self.selected_session = item.data(Qt.ItemDataRole.UserRole)
        self.load_selected_session()
        
    def on_session_selection_changed(self):
        """Gère le changement de sélection"""
        current_item = self.sessions_list.currentItem() if self.available_sessions else None
        if current_item and hasattr(self, 'load_session_btn'):
            self.selected_session = current_item.data(Qt.ItemDataRole.UserRole)
            self.load_session_btn.setEnabled(True)
        elif hasattr(self, 'load_session_btn'):
            self.load_session_btn.setEnabled(False)

    def update_brand_rules_display(self):
        """🆕 Met à jour l'affichage des règles quand la marque change"""
        brand_code = self.brand_combo.currentData()
        if brand_code:
            from ..core.brand_configs.brand_registry import BrandRegistry
            brand = BrandRegistry.get_brand(brand_code)
            if brand:
                self.brand_rules_text.setText(brand.get_validation_description())

    def get_selected_brand_code(self) -> str:
        """🆕 Retourne le code de la marque sélectionnée"""
        return self.brand_combo.currentData() if hasattr(self, 'brand_combo') else 'MNY'

    def load_selected_session(self):
        """Charge la session sélectionnée"""
        if self.selected_session:
            self.load_session_requested.emit(self.selected_session)
            self.accept()
            
    def create_new_session(self):
        """Crée une nouvelle session"""
        self.new_session_requested.emit()
        self.accept()