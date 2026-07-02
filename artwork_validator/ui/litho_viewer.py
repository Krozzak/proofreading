# ui/litho_viewer.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                        QTableWidgetItem, QScrollArea, QAbstractScrollArea,
                        QHeaderView, QFrame, QHBoxLayout, QSplitter, QGridLayout,
                        QApplication, QPushButton, QComboBox, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor
from ..utils.styles import LorealStyles
from .smart_table import SmartTable
from ..core.table_state_manager import TableStateManager
from .pdf_error_viewer import PDFErrorViewer, ErrorOverlay, create_overlays_from_validation
from .layout_debug_overlay import LayoutDebugOverlay
from PyQt6.QtCore import QRect

class ClickableLabel(QLabel):
    """Label cliquable pour copier le texte"""
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class LithoViewer(QWidget):
    # Signal pour notifier le changement de méthode de validation
    validation_method_changed = pyqtSignal(int)  # 0=legacy, 1=enhanced

    def __init__(self, session_manager=None):
        super().__init__()
        self.session_manager = session_manager
        self.current_litho_code = None
        self.mixed_label = None
        self.current_page = 0
        self.total_pages = 1
        self.pdf_processor = None  # Référence au PDFProcessor pour navigation des pages

        # Layout configuration manager pour positionnement précis
        from ..core.layout_config import LayoutConfigManager
        self.layout_config_manager = LayoutConfigManager()

        # Stocker facing et zones courantes
        self.current_facing = 1
        self.current_zones = {}

        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # En-tête séparé en 2 sections
        header = self.create_separated_header()
        layout.addWidget(header)
        
        # Splitter vertical pour optimiser l'espace
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Zone PDF compacte
        pdf_container = self.create_pdf_container()
        content_splitter.addWidget(pdf_container)
        
        # Tableau compact
        table_container = self.create_table_container()
        content_splitter.addWidget(table_container)
        
        # Proportions optimales pour 14"
        content_splitter.setSizes([350, 350])
        
        layout.addWidget(content_splitter)

    def create_separated_header(self):
        """En-tête avec statistiques et status séparés"""
        header = QFrame()
        header.setFixedHeight(90)  # Plus haut pour accommoder les 2 sections
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {LorealStyles.COLORS['surface']},
                    stop:1 {LorealStyles.COLORS['background']});
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout()
        header.setLayout(layout)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        
        # SECTION 1: Statistiques avec labels explicites
        stats_section = self.create_statistics_section()
        layout.addWidget(stats_section)
        
        # Séparateur subtil
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {LorealStyles.COLORS['border']};")
        layout.addWidget(separator)
        
        # SECTION 2: Status de validation + code litho cliquable
        status_section = self.create_status_section()
        layout.addWidget(status_section)
        
        return header

    def set_pdf_processor(self, pdf_processor):
        """Définit la référence au PDFProcessor pour la navigation des pages"""
        self.pdf_processor = pdf_processor

    def create_statistics_section(self):
        """Section des statistiques avec labels explicites - SANS BORDURES"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")  # Supprime les bordures
        
        stats_layout = QHBoxLayout()
        stats_frame.setLayout(stats_layout)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)
        
        # Groupe 1: Progression - SANS BORDURES
        progress_group = QHBoxLayout()
        progress_group.setSpacing(8)
        
        self.total_pdfs_label = self.create_labeled_stat("📄", "0", "Total")
        self.current_pdf_label = self.create_labeled_stat("👁️", "0", "Actuel")
        self.progress_percentage = self.create_labeled_stat("📊", "0%", "Traitement")
        self.validation_percentage = self.create_labeled_stat("✔️", "0%", "Validation")

        progress_group.addWidget(self.total_pdfs_label)
        progress_group.addWidget(self.create_stat_separator())
        progress_group.addWidget(self.current_pdf_label)
        progress_group.addWidget(self.create_stat_separator())
        progress_group.addWidget(self.progress_percentage)
        progress_group.addWidget(self.create_stat_separator())
        progress_group.addWidget(self.validation_percentage)
        
        # Groupe 2: Validation - SANS BORDURES
        validation_group = QHBoxLayout()
        validation_group.setSpacing(8)
        
        self.pdfs_validated_label = self.create_labeled_stat("✅", "0", "Validées", LorealStyles.COLORS['success'])
        self.pdfs_rejected_label = self.create_labeled_stat("❌", "0", "Rejetées", LorealStyles.COLORS['error'])
        self.pdfs_pending_label = self.create_labeled_stat("⏳", "0", "En attente", LorealStyles.COLORS['warning'])
        
        validation_group.addWidget(self.pdfs_validated_label)
        validation_group.addWidget(self.create_stat_separator())
        validation_group.addWidget(self.pdfs_rejected_label)
        validation_group.addWidget(self.create_stat_separator())
        validation_group.addWidget(self.pdfs_pending_label)
        
        # Assemblage - SANS BORDURES
        stats_layout.addLayout(progress_group)
        stats_layout.addWidget(self.create_main_separator())
        stats_layout.addLayout(validation_group)
        stats_layout.addStretch()
        
        return stats_frame

    def create_labeled_stat(self, icon, value, label, color=None):
        """Crée une statistique avec icône, valeur et label - SANS BORDURES"""
        container = QFrame()
        container.setStyleSheet("border: none; background: transparent;")  # Supprime les bordures du container
        
        layout = QHBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        
        # Icône - SANS BORDURES
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 12px; 
            border: none; 
            background: transparent; 
            margin: 0; 
            padding: 0;
        """)
        icon_label.setFixedWidth(24)
        
        # Container pour valeur + label - SANS BORDURES
        text_container = QWidget()
        text_container.setStyleSheet("border: none; background: transparent;")
        text_layout = QVBoxLayout()
        text_container.setLayout(text_layout)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        # Valeur - SANS BORDURES
        value_label = QLabel(value)
        value_style = """
            font-size: 14px; 
            font-weight: 600; 
            margin: 0; 
            padding: 0; 
            border: none; 
            background: transparent;
        """
        if color:
            value_style += f" color: {color};"
        value_label.setStyleSheet(value_style)
        
        # Description - SANS BORDURES
        desc_label = QLabel(label)
        desc_label.setStyleSheet(f"""
            font-size: 10px; 
            color: {LorealStyles.COLORS['text_secondary']}; 
            margin: 0; 
            padding: 0; 
            border: none; 
            background: transparent;
        """)
        
        text_layout.addWidget(value_label)
        text_layout.addWidget(desc_label)
        
        layout.addWidget(icon_label)
        layout.addWidget(text_container)
        
        # Stocker la référence pour les mises à jour
        container.value_label = value_label
        
        return container

    def create_stat_separator(self):
        """Séparateur léger entre stats - SANS BORDURES"""
        sep = QLabel("•")
        sep.setStyleSheet(f"""
            color: {LorealStyles.COLORS['border']}; 
            font-size: 8px; 
            border: none; 
            background: transparent; 
            margin: 0; 
            padding: 0;
        """)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sep

    def create_main_separator(self):
        """Séparateur principal entre groupes - SANS BORDURES"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"""
            background-color: {LorealStyles.COLORS['border']}; 
            border: none; 
            margin: 0; 
            padding: 0;
        """)
        return sep

    def create_status_section(self):
        """Section du status avec code litho cliquable"""
        status_frame = QFrame()
        status_frame.setStyleSheet("border: none; background: transparent;") 
        status_layout = QHBoxLayout()
        status_frame.setLayout(status_layout)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        # Icône de statut plus grande
        self.status_icon = QLabel("⏳")
        self.status_icon.setFixedSize(30, 30)
        self.status_icon.setStyleSheet("""
            font-size: 16px; 
            border: none; 
            background: transparent; 
            margin: 0; 
            padding: 0;
        """)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status plus grand - SANS BORDURES
        self.status_label = QLabel("Status: En attente de validation")
        self.status_label.setStyleSheet("""
            font-weight: 600; 
            font-size: 16px; 
            border: none; 
            background: transparent; 
            margin: 0; 
            padding: 0;
        """)
        
        # Code litho cliquable avec tooltip - SANS BORDURES (sauf effet hover)
        self.litho_code_label = ClickableLabel("Litho: -")
        self.litho_code_label.setStyleSheet(f"""
            color: {LorealStyles.COLORS['primary']};
            font-size: 16px;
            font-weight: 600;
            text-decoration: underline;
            padding: 2px 4px;
            border: none;
            background: transparent;
            border-radius: 3px;
            margin: 0;
        """)
        self.litho_code_label.setToolTip("🖱️ Cliquer pour copier le code litho")
        
        # Connexion du signal de clic
        self.litho_code_label.clicked.connect(self.copy_litho_code)
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.litho_code_label)
        
        return status_frame

    def copy_litho_code(self):
        """Copie le code litho dans le presse-papier"""
        if self.current_litho_code:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_litho_code)
            
            # Feedback visuel temporaire
            original_style = self.litho_code_label.styleSheet()
            self.litho_code_label.setStyleSheet(f"""
                color: white;
                background-color: {LorealStyles.COLORS['success']};
                font-size: 12px;
                font-weight: 600;
                padding: 2px 4px;
                border-radius: 3px;
            """)
            self.litho_code_label.setText(f"✓ Copié: {self.current_litho_code}")
            
            # Retour au style normal après 1.5 secondes
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.reset_litho_label_style(original_style))

    def reset_litho_label_style(self, original_style):
        """Remet le style original du label litho"""
        self.litho_code_label.setStyleSheet(original_style)
        if self.current_litho_code:
            self.litho_code_label.setText(f"Litho: {self.current_litho_code}")
        
    def create_pdf_container(self):
        """Crée le conteneur PDF optimisé avec navigation des pages et highlighting d'erreurs"""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(2, 2, 2, 2)

        # ScrollArea pour le PDF
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(250)

        # Utiliser PDFErrorViewer au lieu de QLabel simple
        self.pdf_label = PDFErrorViewer()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setStyleSheet(f"""
            PDFErrorViewer {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
            }}
        """)
        self.scroll_area.setWidget(self.pdf_label)

        # Créer debug overlay qui se superpose au PDF
        self.debug_overlay = LayoutDebugOverlay(self.pdf_label)
        self.debug_overlay.hide()

        layout.addWidget(self.scroll_area)

        # Barre de navigation des pages
        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        nav_layout = QHBoxLayout()
        nav_frame.setLayout(nav_layout)
        nav_layout.setContentsMargins(6, 4, 6, 4)
        nav_layout.setSpacing(8)

        # Bouton page précédente
        self.prev_page_btn = QPushButton("◀ Précédente")
        self.prev_page_btn.setFixedHeight(28)
        self.prev_page_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: #1a1a1a;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #999999;
            }}
        """)
        self.prev_page_btn.clicked.connect(self.previous_page)
        nav_layout.addWidget(self.prev_page_btn)

        # Label page courante
        self.page_label = QLabel("Page 1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #333;
            padding: 4px 12px;
        """)
        nav_layout.addWidget(self.page_label)

        # Bouton page suivante
        self.next_page_btn = QPushButton("Suivante ▶")
        self.next_page_btn.setFixedHeight(28)
        self.next_page_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: #1a1a1a;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #999999;
            }}
        """)
        self.next_page_btn.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_page_btn)

        # Séparateur
        nav_layout.addSpacing(20)

        # Checkbox pour toggle les overlays d'erreurs
        self.show_errors_checkbox = QCheckBox("👁️ Afficher erreurs")
        self.show_errors_checkbox.setChecked(True)
        self.show_errors_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 10px;
                font-weight: 600;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.show_errors_checkbox.setToolTip("Activer/désactiver l'affichage visuel des erreurs sur l'image")
        self.show_errors_checkbox.toggled.connect(self._toggle_error_overlays)
        nav_layout.addWidget(self.show_errors_checkbox)

        # Séparateur
        nav_layout.addSpacing(8)

        # Checkbox pour toggle le mode debug layout
        self.show_debug_checkbox = QCheckBox("🔍 Debug Layout")
        self.show_debug_checkbox.setChecked(False)
        self.show_debug_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 10px;
                font-weight: 600;
                color: #333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.show_debug_checkbox.setToolTip("Afficher les zones de layout OCR et colonnes")
        self.show_debug_checkbox.toggled.connect(self._toggle_debug_layout)
        nav_layout.addWidget(self.show_debug_checkbox)

        layout.addWidget(nav_frame)

        # Initialiser l'état des boutons
        self.update_navigation_buttons()

        return container

    def _toggle_error_overlays(self, checked):
        """Toggle l'affichage des overlays d'erreurs"""
        self.pdf_label.toggle_overlays(checked)

    def _toggle_debug_layout(self, checked):
        """Toggle le mode debug layout"""
        if checked:
            facing = self.current_facing if hasattr(self, 'current_facing') else 1
            zones = self.current_zones if hasattr(self, 'current_zones') else {}
            self.debug_overlay.resize(self.pdf_label.size())
            self.debug_overlay.set_layout_info(facing, zones, True)
            self.debug_overlay.show()
        else:
            self.debug_overlay.hide()
        
    def create_table_container(self):
        """Crée le conteneur tableau optimisé"""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(2, 2, 2, 2)

        # OPTIONS DE VALIDATION - Juste au-dessus du tableau
        validation_options = self.create_validation_options_section()
        layout.addWidget(validation_options)

        self.table = SmartTable()
        self.table_state_manager = TableStateManager()
        self.setup_table()
        layout.addWidget(self.table)

        # Restaurer l'état de la table si disponible
        saved_state = self.table_state_manager.get_table_state('litho_validation_table')
        if saved_state:
            self.table.restore_state(saved_state)

        return container

    def create_validation_options_section(self):
        """Crée la section d'options de validation compacte avec indicateur OCR"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        layout = QHBoxLayout()
        frame.setLayout(layout)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Label
        method_label = QLabel("⚙️ Méthode:")
        method_label.setStyleSheet("font-size: 9px; font-weight: bold; color: #333;")
        layout.addWidget(method_label)

        # ComboBox pour la méthode
        self.validation_method_combo = QComboBox()
        self.validation_method_combo.addItems([
            "Legacy (classique)",
            "Enhanced (améliorée)"
        ])
        self.validation_method_combo.setStyleSheet("""
            QComboBox {
                font-size: 9px;
                padding: 3px 6px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
                min-width: 140px;
            }
        """)
        self.validation_method_combo.currentIndexChanged.connect(self._on_validation_method_changed)
        layout.addWidget(self.validation_method_combo)

        # Indicateur OCR status
        self.ocr_status_label = QLabel("📄 Texte standard")
        self.ocr_status_label.setStyleSheet("""
            QLabel {
                font-size: 9px;
                padding: 3px 8px;
                border: 1px solid #4CAF50;
                border-radius: 3px;
                background-color: #E8F5E9;
                color: #2E7D32;
                font-weight: 600;
            }
        """)
        self.ocr_status_label.setToolTip("Méthode d'extraction de texte utilisée")
        layout.addWidget(self.ocr_status_label)

        # Séparateur vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #ddd;")
        layout.addWidget(separator)

        # Checkbox pour 4 DIGITS (Walmart)
        self.check_4digits = QCheckBox("🔢 4 DIGITS")
        self.check_4digits.setStyleSheet("""
            QCheckBox {
                font-size: 9px;
                color: #333;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
        """)
        self.check_4digits.setToolTip("Activer la vérification des codes 4 DIGITS pour les lithos Walmart")
        layout.addWidget(self.check_4digits)

        # Label de statut
        self.validation_status_label = QLabel("💡 Mode legacy actif")
        self.validation_status_label.setStyleSheet("""
            font-size: 8px;
            color: #999;
            padding: 2px;
            font-style: italic;
        """)
        layout.addWidget(self.validation_status_label)

        layout.addStretch()

        return frame

    def _on_validation_method_changed(self, index):
        """Gère le changement de méthode de validation"""
        # Mettre à jour le label de statut
        status_messages = {
            0: "💡 Mode legacy actif (validation classique)",
            1: "🚀 Mode enhanced actif (validation améliorée)"
        }
        self.validation_status_label.setText(status_messages.get(index, ""))

        # Émettre le signal pour notifier le changement
        self.validation_method_changed.emit(index)

    def update_ocr_status(self, method: str, is_loading: bool = False):
        """
        Met à jour l'indicateur de statut OCR.

        Args:
            method: 'pymupdf', 'ocr', 'loading', 'error'
            is_loading: Si True, affiche un indicateur de chargement
        """
        if is_loading or method == 'loading':
            self.ocr_status_label.setText("⏳ Analyse OCR...")
            self.ocr_status_label.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    padding: 3px 8px;
                    border: 1px solid #FF9800;
                    border-radius: 3px;
                    background-color: #FFF3E0;
                    color: #E65100;
                    font-weight: 600;
                }
            """)
            self.ocr_status_label.setToolTip("Extraction OCR en cours...")
            QApplication.processEvents()  # Forcer le rafraîchissement

        elif method == 'ocr':
            self.ocr_status_label.setText("🔍 OCR activé")
            self.ocr_status_label.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    padding: 3px 8px;
                    border: 1px solid #2196F3;
                    border-radius: 3px;
                    background-color: #E3F2FD;
                    color: #1565C0;
                    font-weight: 600;
                }
            """)
            self.ocr_status_label.setToolTip("Texte extrait via OCR (PDF scanné détecté)")

        elif method == 'pymupdf':
            self.ocr_status_label.setText("📄 Texte standard")
            self.ocr_status_label.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    padding: 3px 8px;
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    background-color: #E8F5E9;
                    color: #2E7D32;
                    font-weight: 600;
                }
            """)
            self.ocr_status_label.setToolTip("Texte extrait directement du PDF")

        elif method == 'error':
            self.ocr_status_label.setText("⚠️ Erreur")
            self.ocr_status_label.setStyleSheet("""
                QLabel {
                    font-size: 9px;
                    padding: 3px 8px;
                    border: 1px solid #F44336;
                    border-radius: 3px;
                    background-color: #FFEBEE;
                    color: #C62828;
                    font-weight: 600;
                }
            """)
            self.ocr_status_label.setToolTip("Erreur lors de l'extraction du texte")

    def get_validation_settings(self):
        """Retourne les paramètres de validation actuels"""
        method_index = self.validation_method_combo.currentIndex()
        return {
            'method': ['legacy', 'enhanced'][method_index],
            'method_index': method_index,
            'debug_mode': self.debug_mode_checkbox.isChecked()
        }

    def _create_error_overlays(self, validation_results, excel_data, image_size):
        """
        Crée les overlays d'erreurs basés sur FACING et configuration des zones.
        Gère les colonnes de largeurs variables selon le FACING de chaque produit.

        Args:
            validation_results: Résultats de validation
            excel_data: Données Excel correspondantes
            image_size: Taille de l'image scaled

        Returns:
            Liste d'ErrorOverlay
        """
        overlays = []

        if not validation_results or not excel_data:
            return overlays

        # Pas d'overlays pour CUBBY: les shades sont sur le FRAME, pas sur la litho
        if validation_results[0].get('is_cubby'):
            return overlays

        # Dimensions de l'image
        image_width = image_size.width()
        image_height = image_size.height()

        # Calculer les FACINGs individuels et gérer les SPACE SAVERs
        facings = self._extract_facings_with_space_savers(excel_data, validation_results)

        # Détecter les TIERS (lignes multiples)
        tier_info = self._detect_tiers(facings, excel_data)
        num_tiers = tier_info['num_tiers']
        products_per_tier = tier_info['products_per_tier']

        # Stocker pour le debug overlay
        self.current_facing = max(facings) if facings else 1
        self.current_tier_info = tier_info

        # Calculer les positions et largeurs de colonnes avec support multi-tiers
        column_info = self._calculate_column_positions_with_tiers(
            facings, image_width, image_height, num_tiers, products_per_tier
        )

        # Vérification de sécurité: column_info doit correspondre au nombre de produits
        if len(column_info) != len(validation_results):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Erreur dimensionnement column_info: {len(column_info)} entrées "
                f"pour {len(validation_results)} produits. Tiers: {num_tiers}, "
                f"Produits/tier: {products_per_tier}"
            )
            return overlays

        # Détecter la structure (présence de shade number/name)
        has_shade_numbers = any(d.get('SHADE NUMBER') for d in excel_data if d)
        has_shade_names = any(d.get('SHADE NAME') for d in excel_data if d)

        # Obtenir zones ajustées
        zones = self.layout_config_manager.current_config.get_adjusted_zones(
            has_shade_numbers, has_shade_names
        )
        self.current_zones = zones  # Stocker pour le mode debug

        # Créer overlays pour chaque produit avec erreur
        for idx, (validation, data) in enumerate(zip(validation_results, excel_data)):
            # Ignorer frames et space savers
            if validation.get('is_frame') or validation.get('is_space_saver'):
                continue

            # Récupérer les infos de colonne pour ce produit
            if idx >= len(column_info):
                continue

            column_x, column_y, column_width, column_height = column_info[idx]

            # Créer rectangles pour chaque type d'erreur détecté

            # SHADE NUMBER
            if not validation.get('shade_number', True) and 'shade_number' in zones:
                zone_config = zones['shade_number']
                if zone_config.enabled:
                    rect = self._create_rect_from_zone_config(
                        zone_config, column_x, column_width, image_height,
                        column_y, column_height
                    )
                    overlays.append(ErrorOverlay(
                        rect,
                        'shade_number',
                        f"Numéro incorrect (Produit {idx + 1})",
                        'high'
                    ))

            # SHADE NAME
            if not validation.get('shade_name', True) and 'shade_name' in zones:
                zone_config = zones['shade_name']
                if zone_config.enabled:
                    rect = self._create_rect_from_zone_config(
                        zone_config, column_x, column_width, image_height,
                        column_y, column_height
                    )
                    overlays.append(ErrorOverlay(
                        rect,
                        'shade_name',
                        f"Nom incorrect (Produit {idx + 1})",
                        'high'
                    ))

            # 4 DIGITS
            if not validation.get('4_digits', True) and '4_digits' in zones:
                zone_config = zones['4_digits']
                if zone_config.enabled:
                    rect = self._create_rect_from_zone_config(
                        zone_config, column_x, column_width, image_height,
                        column_y, column_height
                    )
                    overlays.append(ErrorOverlay(
                        rect,
                        '4_digits',
                        f"4 DIGITS manquant (Produit {idx + 1})",
                        'medium'
                    ))

        return overlays

    def _extract_facings_with_space_savers(self, excel_data, validation_results):
        """
        Extrait les FACINGs de chaque produit en gérant les SPACE SAVERs.
        Les SPACE SAVERs héritent du FACING du produit suivant non-SPACE SAVER.

        Args:
            excel_data: Données Excel
            validation_results: Résultats de validation

        Returns:
            Liste des FACINGs pour chaque produit
        """
        facings = []

        for idx, (data, validation) in enumerate(zip(excel_data, validation_results)):
            # Essayer d'extraire le FACING
            facing_value = data.get('PRODUCT FACING SL')

            if validation.get('is_space_saver') or not facing_value:
                # SPACE SAVER ou pas de facing: chercher le facing du produit suivant
                next_facing = None
                for next_idx in range(idx + 1, len(excel_data)):
                    next_data = excel_data[next_idx]
                    next_validation = validation_results[next_idx]

                    if not next_validation.get('is_space_saver'):
                        next_facing_value = next_data.get('PRODUCT FACING SL')
                        if next_facing_value:
                            try:
                                next_facing = int(next_facing_value)
                                break
                            except (ValueError, TypeError):
                                pass

                # Si on n'a pas trouvé de facing suivant, utiliser 1
                facings.append(next_facing if next_facing else 1)
            else:
                # Produit normal avec FACING
                try:
                    facings.append(int(facing_value))
                except (ValueError, TypeError):
                    facings.append(1)

        return facings

    def _calculate_column_positions(self, facings, image_width):
        """
        Calcule les positions X et largeurs de chaque colonne selon les FACINGs.

        Les colonnes ont des largeurs proportionnelles à leur FACING.
        Ex: [4, 4, 6, 6, 6] → largeurs proportionnelles où total = image_width

        Args:
            facings: Liste des FACINGs pour chaque produit
            image_width: Largeur totale de l'image

        Returns:
            Liste de tuples (x_position, width) pour chaque colonne
        """
        if not facings:
            return []

        # Calculer le total des facings pour normaliser
        total_facing = sum(facings)

        if total_facing == 0:
            # Fallback: colonnes de largeur égale
            column_width = image_width / len(facings)
            return [(i * column_width, column_width) for i in range(len(facings))]

        # Calculer les positions et largeurs proportionnelles
        column_info = []
        current_x = 0

        for facing in facings:
            # Largeur proportionnelle au facing
            width = (facing / total_facing) * image_width
            column_info.append((current_x, width))
            current_x += width

        return column_info

    def _detect_tiers(self, facings, excel_data):
        """
        Détecte les TIERS en analysant les UPC positions (UPC.1, UPC.2, etc.).
        Un pattern répétitif d'UPC indique des TIERS multiples.

        Exemples:
        - [UPC.1, UPC.2, UPC.3, UPC.4, UPC.1, UPC.2, UPC.3, UPC.4] → 2 TIERS
        - [UPC.1, UPC.2, UPC.3, UPC.4, UPC.5, UPC.6] → 1 TIER

        Supporte aussi la colonne TIER si présente dans Excel.

        Args:
            facings: Liste des FACINGs
            excel_data: Données Excel

        Returns:
            dict avec 'num_tiers', 'products_per_tier', 'tier_assignments'
        """
        # Vérifier si la colonne TIER existe dans Excel
        has_tier_column = any('TIER' in data for data in excel_data)

        if has_tier_column:
            # Utiliser la colonne TIER si disponible
            tier_values = []
            for data in excel_data:
                tier_val = data.get('TIER', 1)
                try:
                    tier_values.append(int(tier_val))
                except (ValueError, TypeError):
                    tier_values.append(1)

            num_tiers = max(tier_values) if tier_values else 1
            # Compter produits par tier
            from collections import Counter
            tier_counts = Counter(tier_values)
            products_per_tier = tier_counts.get(1, len(facings) // num_tiers if num_tiers > 0 else len(facings))

            return {
                'num_tiers': num_tiers,
                'products_per_tier': products_per_tier,
                'tier_assignments': tier_values,
                'detection_method': 'column'
            }

        # Sinon, détecter automatiquement via UPC positions
        if not excel_data or len(excel_data) == 0:
            return {
                'num_tiers': 1,
                'products_per_tier': len(facings),
                'tier_assignments': [1] * len(facings),
                'detection_method': 'auto'
            }

        # Extraire les positions UPC (ex: "UPC.1" → 1)
        upc_positions = []
        for data in excel_data:
            upc = data.get('UPC', '')
            if isinstance(upc, str) and 'UPC.' in upc:
                try:
                    # Extraire le numéro après "UPC."
                    position = int(upc.split('UPC.')[1].split()[0])
                    upc_positions.append(position)
                except (ValueError, IndexError):
                    # Si parsing échoue, considérer comme position unique
                    upc_positions.append(len(upc_positions) + 1)
            else:
                # Pas de format UPC.X, considérer comme position unique
                upc_positions.append(len(upc_positions) + 1)

        if not upc_positions:
            return {
                'num_tiers': 1,
                'products_per_tier': len(facings),
                'tier_assignments': [1] * len(facings),
                'detection_method': 'auto'
            }

        # Détecter le pattern répétitif dans les UPC positions
        # Ex: [1,2,3,4, 1,2,3,4] → pattern de longueur 4 répété 2 fois
        n = len(upc_positions)
        max_position = max(upc_positions)

        # Tester si le pattern se répète (longueur = max_position)
        # Ex: si max=4, vérifier si positions sont [1,2,3,4, 1,2,3,4, ...]
        products_per_tier = max_position

        if n > products_per_tier and n % products_per_tier == 0:
            # Vérifier si le pattern se répète exactement
            num_potential_tiers = n // products_per_tier
            is_pattern = True

            expected_pattern = list(range(1, products_per_tier + 1))

            for tier_idx in range(num_potential_tiers):
                start = tier_idx * products_per_tier
                end = start + products_per_tier
                current_tier_positions = upc_positions[start:end]

                if current_tier_positions != expected_pattern:
                    is_pattern = False
                    break

            if is_pattern and num_potential_tiers > 1:
                # Pattern trouvé!
                tier_assignments = []
                for tier_idx in range(num_potential_tiers):
                    tier_assignments.extend([tier_idx + 1] * products_per_tier)

                return {
                    'num_tiers': num_potential_tiers,
                    'products_per_tier': products_per_tier,
                    'tier_assignments': tier_assignments,
                    'detection_method': 'auto_upc'
                }

        # Pas de pattern répétitif trouvé → 1 seul tier
        return {
            'num_tiers': 1,
            'products_per_tier': len(facings),
            'tier_assignments': [1] * len(facings),
            'detection_method': 'auto'
        }

    def _calculate_column_positions_with_tiers(self, facings, image_width, image_height,
                                                num_tiers, products_per_tier):
        """
        Calcule positions et dimensions de chaque colonne avec support multi-tiers.

        Les zones de shade sont divisées verticalement en fonction du nombre de TIERS.
        Ex: 2 tiers → première ligne dans top 50% des zones shade, deuxième ligne dans bottom 50%

        Args:
            facings: Liste des FACINGs
            image_width: Largeur totale
            image_height: Hauteur totale
            num_tiers: Nombre de tiers détectés
            products_per_tier: Nombre de produits par tier

        Returns:
            Liste de tuples (x, y, width, height) pour chaque produit
        """
        if not facings:
            return []

        column_info = []

        for tier_idx in range(num_tiers):
            # Indices des produits de ce tier
            start_idx = tier_idx * products_per_tier
            end_idx = min(start_idx + products_per_tier, len(facings))
            tier_facings = facings[start_idx:end_idx]

            if not tier_facings:
                continue

            # Calculer largeurs proportionnelles pour ce tier
            total_facing = sum(tier_facings)
            current_x = 0

            # Calculer la hauteur Y de ce tier (vertical subdivision)
            # Les zones shade occupent ~30% du haut (0-30%)
            # On divise cette zone en num_tiers lignes
            tier_height_fraction = 0.30 / num_tiers
            tier_y_start = tier_idx * tier_height_fraction

            for facing in tier_facings:
                if total_facing > 0:
                    width = (facing / total_facing) * image_width
                else:
                    width = image_width / len(tier_facings)

                # Retourner (x, y_offset, width, height_fraction)
                # y_offset et height_fraction sont relatifs à image_height
                column_info.append((
                    current_x,              # x position
                    tier_y_start,           # y offset (fraction de hauteur)
                    width,                  # largeur
                    tier_height_fraction    # hauteur (fraction)
                ))

                current_x += width

        return column_info

    def _create_rect_from_zone_config(self, zone_config, column_x, column_width, image_height,
                                       column_y_fraction=0, column_height_fraction=1.0):
        """
        Crée un QRect depuis une ZoneConfig avec support multi-tiers.

        Args:
            zone_config: Configuration de la zone
            column_x: Position X de la colonne
            column_width: Largeur de la colonne
            image_height: Hauteur totale de l'image
            column_y_fraction: Offset vertical du tier (0.0-1.0)
            column_height_fraction: Hauteur du tier en fraction (0.0-1.0)

        Returns:
            QRect positionné
        """
        from ..core.layout_config import ZoneConfig

        # Calcul vertical avec ajustement pour multi-tiers
        # Ajuster les zones selon le tier
        zone_y_start = zone_config.y_start
        zone_y_end = zone_config.y_end

        # Si multi-tiers, ajuster la position verticale dans la zone du tier
        if column_height_fraction < 1.0:
            # Multi-tiers: les zones doivent être compressées dans l'espace du tier
            #
            # Exemple avec 2 tiers (column_height_fraction = 0.15):
            # - Tier 1: column_y_fraction = 0.00 (début à 0%)
            # - Tier 2: column_y_fraction = 0.15 (début à 15%)
            #
            # Zone shade_number (y_start=0.00, y_end=0.15):
            #   - Normalement occupe 0-15% de la hauteur
            #   - Avec 2 tiers, doit être compressée dans le tier (0-15% de hauteur de tier)
            #   - Tier 1: 0 + (0.00 * 0.15) à 0 + (0.15 * 0.15) = 0% à 2.25%  ❌ FAUX!
            #
            # Correction: les zones shade occupent normalement 0-30% (0.30 de hauteur)
            # Avec 2 tiers, chaque tier occupe 0.15 (30% / 2)
            # Les zones doivent être remappées dans cet espace 0.15
            #
            # shade_number va de 0% à 15% = 50% de la zone 30%
            # Dans le tier: 50% de 0.15 = 0.075 = 7.5% de hauteur totale
            #
            # Normalisation: zone_span / total_shade_zone_height
            # shade_number: (0.15 - 0.00) / 0.30 = 0.5 (50% de l'espace shade)
            # Dans le tier: column_y_fraction + (relative_position * column_height_fraction)

            # Zones shade totales: 0.00 à 0.30
            shade_zone_total_height = 0.30

            # Position relative de la zone dans l'espace shade (0-1)
            relative_start = (zone_y_start - 0.00) / shade_zone_total_height
            relative_end = (zone_y_end - 0.00) / shade_zone_total_height

            # Mapper dans l'espace du tier
            y_start = int(image_height * (column_y_fraction + relative_start * column_height_fraction))
            y_end = int(image_height * (column_y_fraction + relative_end * column_height_fraction))
        else:
            # Single tier: utiliser les zones normales
            y_start = int(image_height * zone_y_start)
            y_end = int(image_height * zone_y_end)

        height = y_end - y_start

        # Calcul horizontal selon le type de positionnement
        if zone_config.horizontal == 'centered':
            # Centré avec marges
            margin = column_width * zone_config.margin_x
            x = int(column_x + margin)
            width = int(column_width - 2 * margin)

        elif zone_config.horizontal == 'right':
            # À droite avec offset
            x = int(column_x + column_width * zone_config.x_offset)
            width = int(column_width * zone_config.width)

        elif zone_config.horizontal == 'left':
            # À gauche
            x = int(column_x)
            width = int(column_width * zone_config.width)

        else:
            # Fallback: centered
            margin = column_width * 0.10
            x = int(column_x + margin)
            width = int(column_width - 2 * margin)

        return QRect(x, y_start, width, height)

    def setup_table(self):
        """Configure le tableau avec headers dynamiques"""
        self.base_headers = [
            "LITHO", "DESCRIPTION", "UPC", "PRODUCT DESCRIPTION", 
            "SHADE NAME", "SHADE NUMBER", "FACING"
        ]
        
        self.digits_header = ["4 DIGITS"]
        
        self.validation_headers = [
            "Val. Teinte", "Val. Nom", "Val. Global"
        ]
        
        # Configuration initiale avec tous les headers
        all_headers = self.base_headers + self.digits_header + ["Val. Digits"] + self.validation_headers
        self.table.setColumnCount(len(all_headers))
        self.table.setHorizontalHeaderLabels(all_headers)
        self.table.horizontalHeader().setStretchLastSection(True)

    def update_content(self, pdf_pixmap, excel_data, validation_results, check_digits=False, 
                      session_stats=None, current_pdf_info=None):
        """Met à jour le contenu ET les statistiques"""
        
        # Supprimer l'ancien label MIXED/CUBBY s'il existe
        if self.mixed_label:
            self.mixed_label.deleteLater()
            self.mixed_label = None
            
        # Mise à jour des statistiques d'abord
        self.update_statistics(validation_results, session_stats, current_pdf_info)
            
        # Mise à jour du code litho courant
        if excel_data and len(excel_data) > 0:
            self.current_litho_code = str(excel_data[0].get('LITHO', ''))
            self.litho_code_label.setText(f"Litho: {self.current_litho_code}")

        # Mise à jour de l'image avec overlays d'erreurs
        if pdf_pixmap:
            scaled_pixmap = pdf_pixmap.scaled(
                self.scroll_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.pdf_label.set_pixmap(scaled_pixmap)

            # Créer les overlays d'erreurs visuelles
            error_overlays = self._create_error_overlays(validation_results, excel_data, scaled_pixmap.size())
            self.pdf_label.set_error_overlays(error_overlays)

            # Mettre à jour le debug overlay si activé
            if self.show_debug_checkbox.isChecked():
                self.debug_overlay.resize(self.pdf_label.size())
                self.debug_overlay.set_layout_info(self.current_facing, self.current_zones, True)

        # Mettre à jour les boutons de navigation des pages
        self.update_navigation_buttons()

        # Vérifier si c'est un CUBBY
        if validation_results and validation_results[0].get('is_cubby'):
            self.display_cubby_view(validation_results[0], pdf_pixmap)
            return

        # Pour les lithos non-CUBBY
        self.table.show()
        if hasattr(self, 'cubby_table'):
            self.cubby_table.hide()
        
        # Mise à jour des en-têtes selon check_digits
        headers = self.base_headers.copy()
        if check_digits:
            headers.extend(self.digits_header)
        
        val_headers = ["Val. Teinte", "Val. Nom"]
        if check_digits:
            val_headers.append("Val. Digits")
        val_headers.append("Val. Global")
        
        headers.extend(val_headers)
        
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Vérifier le type de tray
        if validation_results:
            is_mixed = validation_results[0].get('is_mixed', False)
            has_space_savers = any(v.get('is_space_saver', False) for v in validation_results)
            
            # Ajouter les labels d'information
            self.add_info_labels(is_mixed, has_space_savers)
        
        # Mise à jour du tableau standard
        self.table.setRowCount(len(excel_data))
        for row, (data, validation) in enumerate(zip(excel_data, validation_results)):
            self.set_row_data(row, data, validation, check_digits)
        
        # Mise à jour du statut et ajustement colonnes
        self.update_status()
        self.adjust_column_sizes()

    def update_statistics(self, validation_results, session_stats=None, current_pdf_info=None):
        """Met à jour les statistiques avec labels"""
        
        # Mise à jour des statistiques globales
        if current_pdf_info:
            total_pdfs = current_pdf_info.get('total', 0)
            current_index = current_pdf_info.get('current', 0)
            self.total_pdfs_label.value_label.setText(str(total_pdfs))
            self.current_pdf_label.value_label.setText(str(current_index + 1))
            
            # Calcul des pourcentages améliorés
            if total_pdfs > 0:
                # Pourcentage de traitement = (approuvées + rejetées) / total
                validated = len(session_stats.get('approved', [])) if session_stats else 0
                rejected = len(session_stats.get('rejected', [])) if session_stats else 0
                processed = validated + rejected
                treatment_progress = (processed / total_pdfs) * 100

                # Pourcentage de validation = approuvées / total
                validation_progress = (validated / total_pdfs) * 100

                self.progress_percentage.value_label.setText(f"{treatment_progress:.0f}%")
                self.validation_percentage.value_label.setText(f"{validation_progress:.0f}%")

        if session_stats:
            validated = len(session_stats.get('approved', []))
            rejected = len(session_stats.get('rejected', []))
            pending = current_pdf_info.get('total', 0) - (validated + rejected) if current_pdf_info else 0
            
            self.pdfs_validated_label.value_label.setText(str(validated))
            self.pdfs_rejected_label.value_label.setText(str(rejected))
            self.pdfs_pending_label.value_label.setText(str(pending))
        
    def add_info_labels(self, is_mixed, has_space_savers):
        """Ajoute les labels d'information si nécessaire"""
        labels_to_add = []
        
        if is_mixed:
            mixed_label = QLabel("⚠️ MIXED FACINGS DETECTED")
            mixed_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {LorealStyles.COLORS['warning']};
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 10px;
                    margin: 2px;
                }}
            """)
            labels_to_add.append(mixed_label)
        
        if has_space_savers:
            space_saver_label = QLabel("📦 SPACE SAVERS PRESENT")
            space_saver_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {LorealStyles.COLORS['secondary_light']};
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 10px;
                    margin: 2px;
                }}
            """)
            labels_to_add.append(space_saver_label)
        
        if labels_to_add:
            info_container = QWidget(self)
            info_layout = QHBoxLayout(info_container)
            info_layout.setSpacing(4)
            info_layout.setContentsMargins(0, 0, 0, 0)
            
            for label in labels_to_add:
                info_layout.addWidget(label)
            info_layout.addStretch()
            
            self.mixed_label = info_container
            self.layout().insertWidget(1, info_container)

    def display_cubby_view(self, cubby_data, pdf_pixmap):
        """Affiche la vue spéciale pour les CUBBY"""
        # Mise à jour de l'image
        if pdf_pixmap:
            scaled_pixmap = pdf_pixmap.scaled(
                self.scroll_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.pdf_label.setPixmap(scaled_pixmap)

        # Cacher le tableau normal
        self.table.hide()

        # Vérifier que les données nécessaires existent
        if not cubby_data.get('matrix_data') or not cubby_data.get('cubby_dimensions'):
            print(f"Données CUBBY manquantes - matrix_data: {cubby_data.get('matrix_data') is not None}, dimensions: {cubby_data.get('cubby_dimensions')}")
            # Créer données par défaut
            dimensions = cubby_data.get('cubby_dimensions', (10, 2))
            matrix_data = self._create_default_matrix(dimensions)
        else:
            matrix_data = cubby_data['matrix_data']
            dimensions = cubby_data['cubby_dimensions']

        # Créer et afficher le tableau CUBBY
        cubby_table = self._create_cubby_table(matrix_data, dimensions)
        
        if hasattr(self, 'cubby_table'):
            self.layout().removeWidget(self.cubby_table)
            self.cubby_table.deleteLater()
        
        self.cubby_table = cubby_table
        self.layout().addWidget(self.cubby_table)
        
        # Label CUBBY avec information sur la validation
        dimensions = cubby_data.get('cubby_dimensions', (10, 2))
        faces, tiers = dimensions
        description = cubby_data.get('description', 'Dimensions détectées')

        cubby_label = QLabel(f"🏗️ CUBBY LITHO - {description}\n📋 {faces} faces × {tiers} tiers | ⚠️ Validation PDF désactivée (pas de shades)")
        cubby_label.setStyleSheet(f"""
            QLabel {{
                background-color: {LorealStyles.COLORS['accent']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
                margin: 4px;
                text-align: center;
            }}
        """)
        cubby_label.setWordWrap(True)
        self.mixed_label = cubby_label
        self.layout().insertWidget(1, cubby_label)
        
        self.update_status()
                
    def set_row_data(self, row, data, validation, check_digits=False):
        """Remplit une ligne du tableau avec les données"""
        # Colonnes de données de base
        columns = self.base_headers.copy()
        
        # Ajouter 4 DIGITS si nécessaire
        if check_digits:
            columns.extend(["4 DIGITS"])
        
        # Remplir les données
        for col, field in enumerate(columns):
            # Mapper les noms de colonnes aux clés de données
            field_map = {
                "DESCRIPTION": "DECRIPTION",
                "FACING": "PRODUCT FACING SL",
                "4 DIGITS": "4 DIGITS"
            }
            data_key = field_map.get(field, field)
            value = str(data.get(data_key, ""))
            item = QTableWidgetItem(value)
            
            # Style pour FRAME/SPACE_SAVER
            if validation.get('is_frame') or validation.get('is_space_saver'):
                item.setBackground(QColor(LorealStyles.COLORS['border']))
                if field == "FACING":
                    item.setToolTip("Frame/Space Saver - Pas de validation")
            # Style pour MIXED FACINGS
            elif field == "FACING" and validation.get('is_mixed'):
                item.setBackground(QColor(LorealStyles.COLORS['warning']))
                item.setToolTip("Mixed facings detected!")
            elif not value:
                item.setBackground(QColor(LorealStyles.COLORS['border']))
                
            self.table.setItem(row, col, item)
        
        # Colonnes de validation
        start_col = len(columns)
        
        if validation.get('is_frame') or validation.get('is_space_saver'):
            # Pas de validation pour FRAME et SPACE_SAVER
            for col in range(start_col, self.table.columnCount()):
                item = QTableWidgetItem("N/A")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QColor(LorealStyles.COLORS['border']))
                self.table.setItem(row, col, item)
        else:
            # Préparer les validations
            validations = [
                ("Teinte", validation['shade_number'], bool(data.get('SHADE NUMBER'))),
                ("Nom", validation['shade_name'], bool(data.get('SHADE NAME')))
            ]
            
            if check_digits:
                validations.append(
                    ("Digits", validation['digits'], bool(data.get('4 DIGITS')))
                )
            
            validations.append(
                ("Global", validation['overall'], True)
            )
            
            # Remplir les colonnes de validation
            for i, (name, is_valid, should_validate) in enumerate(validations):
                col = start_col + i
                if should_validate:
                    item = QTableWidgetItem("✓" if is_valid else "✗")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if is_valid:
                        item.setBackground(QColor(LorealStyles.COLORS['success']))
                        item.setForeground(QColor("white"))
                    else:
                        item.setBackground(QColor(LorealStyles.COLORS['error']))
                        item.setForeground(QColor("white"))
                else:
                    item = QTableWidgetItem("N/A")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(LorealStyles.COLORS['border']))
                
                self.table.setItem(row, col, item)

    def update_status(self):
        """Met à jour le statut de validation de la litho courante - SANS BORDURES"""
        if not self.session_manager or not self.current_litho_code:
            self.status_label.setText("Status: En attente de validation")
            self.status_icon.setText("⏳")
            return
            
        if self.current_litho_code in self.session_manager.current_session['validations']:
            status = self.session_manager.get_litho_status(self.current_litho_code)
            if status['status'] == 'approved':
                self.status_label.setText("Status: Approuvé")
                self.status_icon.setText("✅")
                self.status_label.setStyleSheet(f"""
                    color: {LorealStyles.COLORS['success']}; 
                    font-weight: 600; 
                    font-size: 14px; 
                    border: none; 
                    background: transparent; 
                    margin: 0; 
                    padding: 0;
                """)
            else:
                self.status_label.setText("Status: Refusé")
                self.status_icon.setText("❌")
                self.status_label.setStyleSheet(f"""
                    color: {LorealStyles.COLORS['error']}; 
                    font-weight: 600; 
                    font-size: 14x; 
                    border: none; 
                    background: transparent; 
                    margin: 0; 
                    padding: 0;
                """)
        else:
            self.status_label.setText("Status: En attente de validation")
            self.status_icon.setText("⏳")
            self.status_label.setStyleSheet("""
                font-weight: 600; 
                font-size: 14px; 
                border: none; 
                background: transparent; 
                margin: 0; 
                padding: 0;
            """)
            
    def adjust_column_sizes(self):
        """Ajuste la taille des colonnes pour l'écran 14"""
        self.table.resizeColumnsToContents()
        # Limiter la largeur pour les écrans plus petits
        for i in range(self.table.columnCount()):
            if self.table.columnWidth(i) > 150:
                self.table.setColumnWidth(i, 150)
            
    def _create_default_matrix(self, dimensions):
        """Crée une matrice par défaut quand les données sont manquantes"""
        faces, tiers = dimensions
        matrix = []
        for tier in range(tiers):
            row = []
            for face in range(faces):
                row.append({
                    'upc': f'UPC.{face + 1}',
                    'shade_name': 'Données manquantes',
                    'shade_number': '',
                    'is_frame': False
                })
            matrix.append(row)
        return matrix

    def _create_cubby_table(self, matrix_data, dimensions):
        """Crée un tableau spécial pour afficher les données CUBBY"""
        faces, tiers = dimensions
        table = QTableWidget(tiers, faces)
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                font-size: 8px;
            }}
            QTableWidget::item {{
                padding: 3px;
                border: 1px solid {LorealStyles.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {LorealStyles.COLORS['accent']};
                color: white;
                border: 2px solid {LorealStyles.COLORS['primary']};
            }}
        """)
        
        # Configuration du tableau avec sélection active
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)  # Sélection simple
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)  # Sélection par case

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setMinimumSectionSize(80)
        table.verticalHeader().setMinimumSectionSize(40)
        
        table.setHorizontalHeaderLabels([f"Pos {i+1}" for i in range(faces)])
        # Inverser l'ordre des TIER : T4 en haut, T1 en bas (ordre physique d'empilement)
        tier_labels = [f"T{tiers-i}" for i in range(tiers)]
        print(f"🏗️ TIER LABELS: {tier_labels} (de haut en bas)")
        table.setVerticalHeaderLabels(tier_labels)
        
        for row in range(tiers):
            for col in range(faces):
                data = matrix_data[row][col]
                # Log de debug pour voir l'ordre final d'affichage
                actual_tier = tiers - row  # Calculer TIER physique
                print(f"📍 Tableau[{row}][{col}] = TIER {actual_tier}, Pos {col+1}: UPC='{data['upc']}')")

                if data['is_frame']:
                    # Case FRAME - rouge bien visible avec icône
                    item = QTableWidgetItem("🚫 FRAME")
                    item.setBackground(QColor("#ff4444"))
                    item.setForeground(QColor("white"))
                    item.setToolTip("Position occupée par un FRAME")
                elif data['upc'] == 'EMPTY':
                    # Case vide - grisée avec icône
                    item = QTableWidgetItem("⬜ VIDE")
                    item.setBackground(QColor("#f0f0f0"))
                    item.setForeground(QColor("#999999"))
                    item.setToolTip("Position vide")
                else:
                    # UPC normal - affichage amélioré avec UPC visible
                    upc_text = f"{data['upc']}"
                    if data['shade_name']:
                        upc_text += f"\n{data['shade_name']}"
                    if data['shade_number']:
                        upc_text += f"\n#{data['shade_number']}"

                    item = QTableWidgetItem(upc_text)
                    # Fond clair + texte noir pour lisibilité
                    item.setData(Qt.ItemDataRole.BackgroundRole, QColor("#E8F4FD"))  # Bleu très clair
                    item.setData(Qt.ItemDataRole.ForegroundRole, QColor("#000000"))  # Noir
                    print(f"🎨 Couleur UPC '{data['upc']}': fond=#E8F4FD, texte=#000000 (lisible)")

                    # Tooltip avec informations complètes
                    tooltip = f"UPC: {data['upc']}"
                    if data['shade_name']:
                        tooltip += f"\nNom: {data['shade_name']}"
                    if data['shade_number']:
                        tooltip += f"\nNuméro: {data['shade_number']}"
                    # Calculer le numéro TIER correct (inversé pour ordre physique)
                    actual_tier = tiers - row  # row=0 → TIER 4, row=1 → TIER 3, etc.
                    tooltip += f"\nPosition: TIER {actual_tier}, Face {col + 1}"
                    item.setToolTip(tooltip)

                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                font = item.font()
                font.setBold(True)
                font.setPointSize(7)
                item.setFont(font)

                table.setItem(row, col, item)
        
        return table
    
    def clear(self):
        """Réinitialise le viewer"""
        self.pdf_label.clear()
        self.table.setRowCount(0)
        self.status_label.setText("Status: En attente de validation")
        self.litho_code_label.setText("Litho: -")
        self.status_icon.setText("⏳")
        
        # Reset des statistiques
        self.total_pdfs_label.value_label.setText("0")
        self.current_pdf_label.value_label.setText("0")
        self.progress_percentage.value_label.setText("0%")
        self.validation_percentage.value_label.setText("0%")

    def previous_page(self):
        """Navigue vers la page précédente du PDF"""
        if not self.pdf_processor:
            return

        if self.pdf_processor.previous_page():
            self.current_page = self.pdf_processor.get_current_page_index()
            self.update_pdf_display()
            self.update_navigation_buttons()

    def next_page(self):
        """Navigue vers la page suivante du PDF"""
        if not self.pdf_processor:
            return

        if self.pdf_processor.next_page():
            self.current_page = self.pdf_processor.get_current_page_index()
            self.update_pdf_display()
            self.update_navigation_buttons()

    def update_pdf_display(self):
        """Met à jour l'affichage du PDF avec la page courante"""
        if not self.pdf_processor:
            return

        pdf_pixmap = self.pdf_processor.get_current_pdf_image()
        if pdf_pixmap:
            scaled_pixmap = pdf_pixmap.scaled(
                self.scroll_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.pdf_label.setPixmap(scaled_pixmap)

    def update_navigation_buttons(self):
        """Met à jour l'état des boutons de navigation et le label de page"""
        if not self.pdf_processor:
            # Désactiver tous les boutons si pas de PDF processor
            self.prev_page_btn.setEnabled(False)
            self.next_page_btn.setEnabled(False)
            self.page_label.setText("Page 1 / 1")
            return

        self.total_pages = self.pdf_processor.get_page_count()
        self.current_page = self.pdf_processor.get_current_page_index()

        # Mettre à jour le label
        self.page_label.setText(f"Page {self.current_page + 1} / {self.total_pages}")

        # Activer/désactiver les boutons selon la position
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages - 1)

    def save_table_state(self):
        """Sauvegarde l'état actuel de la table"""
        if hasattr(self, 'table') and hasattr(self, 'table_state_manager'):
            state = self.table.get_state()
            self.table_state_manager.save_table_state('litho_validation_table', state)