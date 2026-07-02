# ui/main_window.py
from datetime import datetime
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                        QPushButton, QFileDialog, QSplitter, QMessageBox,
                        QProgressBar, QLabel, QApplication, QInputDialog, QCheckBox,
                        QGroupBox, QFrame, QDialog, QStackedWidget, QToolBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence
from ..utils.session_manager import SessionManager
from .validation_panel import ValidationPanel
from .litho_viewer import LithoViewer
from .overview_view import OverviewView
from .command_palette import CommandPalette
from .shortcuts_help_dialog import ShortcutsHelpDialog
from ..core.pdf_processor import PDFProcessor
from ..core.excel_processor import ExcelProcessor
from ..core.validator import LithoValidator
from ..core.report_generator import ReportGenerator
from ..core.command_registry import CommandRegistry, Command
from ..utils.styles import LorealStyles

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            # Initialiser le logger
            self.logger = logging.getLogger(__name__)

            # Configuration de base de la fenêtre
            self.setWindowTitle("L'Oréal Litho Validator")
            self.setMinimumSize(1200, 700)
            
            # Appliquer le style moderne
            self.setStyleSheet(LorealStyles.get_main_stylesheet())
        
            # Initialisation des processeurs et gestionnaires
            self.init_processors()
            
            # Configuration de l'interface
            self.setup_ui()

            # Connexion des signaux
            self.connect_signals()

            # Importer ici pour éviter les imports circulaires
            from .basecamp_dialog import BasecampProgressDialog
            
            # Configuration responsive
            self.setup_responsive_layout()
            
            # Chargement de la session et vérification initiale
            QApplication.processEvents()
            self.handle_startup()
            
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de MainWindow: {str(e)}")
            QMessageBox.critical(
                self,
                "Erreur de démarrage",
                f"Une erreur est survenue lors du démarrage de l'application:\n{str(e)}"
            )
            raise
        
    def init_processors(self, brand_code: str = None):
        """Initialise les processeurs et gestionnaires

        Args:
            brand_code: Code de la marque à utiliser (MNY, ESSIE, etc.)
                       Si None, utilise MNY par défaut
        """
        # 🆕 Récupérer la configuration de marque depuis le registry
        from ..core.brand_configs import BrandRegistry

        if brand_code:
            brand_config = BrandRegistry.get_brand(brand_code)
            if not brand_config:
                self.logger.warning(f"⚠️ Brand '{brand_code}' not found, using MNY")
                brand_config = BrandRegistry.get_brand('MNY')
        else:
            # Par défaut, MNY
            brand_config = BrandRegistry.get_brand('MNY')

        # Stocker la config actuelle
        self.current_brand_config = brand_config
        self.logger.info(f"📊 Initializing processors for: {brand_config.get_brand_display_name()}")

        # Initialiser les processeurs avec la configuration de marque
        self.pdf_processor = PDFProcessor(brand_config=brand_config)
        self.excel_processor = ExcelProcessor(brand_config=brand_config)
        self.validator = LithoValidator(brand_config=brand_config)
        self.report_generator = ReportGenerator(pdf_processor=self.pdf_processor)
        self.session_manager = SessionManager()

        # Command Registry pour la palette de commandes
        self.command_registry = CommandRegistry()

        # Vues de l'application
        self.overview_view = None  # Lazy loading
        self.validation_view_widget = None  # La vue validation actuelle
        self.current_view_mode = 'validation'
        
    def handle_startup(self):
        """Gère la logique de démarrage de l'application"""
        # Essayer de charger la dernière session
        if self.session_manager.load_last_session():
            # Session chargée avec succès
            self.load_session_data()
            self.show_session_loaded_message()
        else:
            # Aucune session précédente ou erreur de chargement
            self.show_startup_dialog()

    def show_session_loaded_message(self):
        """Affiche un message discret indiquant que la session a été chargée"""
        session_name = self.session_manager.current_session.get('session_name', 'Session sans nom')
        
        # Message dans la barre de statut (si vous en avez une) ou notification discrète
        QMessageBox.information(
            self,
            "Session chargée",
            f"Session '{session_name}' chargée automatiquement.\n\n"
            f"📁 PDFs: {os.path.basename(self.session_manager.current_session.get('pdf_folder', 'Non défini'))}\n"
            f"📊 Excel: {os.path.basename(self.session_manager.current_session.get('excel_file', 'Non défini'))}\n"
            f"✅ Validations: {len(self.session_manager.current_session.get('validations', {}))}"
        )

    def show_startup_dialog(self):
        """Affiche le dialogue de démarrage pour choisir une session"""
        current_folder = self.session_manager.get_sessions_folder()
        available_sessions = self.session_manager.get_available_sessions(current_folder)

        from .startup_dialog import StartupDialog
        startup_dialog = StartupDialog(available_sessions, current_folder, self)

        # Connexion des signaux
        startup_dialog.load_session_requested.connect(self.load_session_from_path)
        startup_dialog.new_session_requested.connect(self.start_initial_session)
        startup_dialog.browse_folder_requested.connect(self.change_sessions_folder)

        if startup_dialog.exec() == QDialog.DialogCode.Accepted:
            # 🆕 Récupérer le code de marque sélectionné
            selected_brand_code = startup_dialog.get_selected_brand_code()
            self.logger.info(f"📊 Brand selected from dialog: {selected_brand_code}")

            # 🆕 Réinitialiser les processeurs avec la marque sélectionnée
            self.init_processors(brand_code=selected_brand_code)

            # 🆕 Sauvegarder la marque dans la session
            self.session_manager.current_session['brand_code'] = selected_brand_code
        else:
            # L'utilisateur a annulé - fermer l'application
            self.close()
        
    def on_brand_changed(self, index):
        """🆕 Appelé quand l'utilisateur change de marque dans la toolbar"""
        if index < 0:
            return

        brand_code = self.brand_selector.itemData(index)
        if brand_code and brand_code != self.current_brand_config.get_brand_code():
            # Demander confirmation
            reply = QMessageBox.question(
                self,
                "Changement de marque",
                f"Voulez-vous changer la marque vers {self.brand_selector.currentText()}?\n\n"
                "Les fichiers Excel et PDF seront rechargés avec les nouvelles règles.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.set_brand_config(brand_code)
                QMessageBox.information(
                    self,
                    "Marque changée",
                    f"La marque a été changée vers {self.brand_selector.currentText()}.\n\n"
                    "Les données ont été rechargées avec les nouvelles règles de validation."
                )
            else:
                # Restaurer la sélection précédente
                current_brand_code = self.current_brand_config.get_brand_code()
                for i in range(self.brand_selector.count()):
                    if self.brand_selector.itemData(i) == current_brand_code:
                        self.brand_selector.blockSignals(True)
                        self.brand_selector.setCurrentIndex(i)
                        self.brand_selector.blockSignals(False)
                        break

    def set_brand_config(self, brand_code: str):
        """Change la configuration de marque et recharge les données

        Args:
            brand_code: Code de la marque (MNY, ESSIE, etc.)
        """
        from ..core.brand_configs import BrandRegistry

        # Récupérer la nouvelle config
        brand_config = BrandRegistry.get_brand(brand_code)
        if not brand_config:
            self.logger.error(f"❌ Brand '{brand_code}' not found in registry")
            return

        # Mettre à jour la config actuelle
        self.current_brand_config = brand_config
        self.logger.info(f"🔄 Changing brand configuration to: {brand_config.get_brand_display_name()}")

        # Mettre à jour tous les processeurs
        self.pdf_processor.set_brand_config(brand_config)
        self.excel_processor.set_brand_config(brand_config)
        self.validator.brand_config = brand_config

        # Mettre à jour la session
        self.session_manager.current_session['brand_code'] = brand_code
        self.session_manager.save_session()

        self.logger.info(f"✅ Brand configuration changed successfully to {brand_code}")

    def change_sessions_folder(self, folder_path):
        """Change le dossier de sessions et relance le dialogue"""
        if self.session_manager.set_sessions_folder(folder_path):
            QMessageBox.information(
                self,
                "Dossier de sessions changé",
                f"Nouveau dossier de sessions :\n{folder_path}"
            )
            # Relancer le dialogue de démarrage avec le nouveau dossier
            self.show_startup_dialog()
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'accéder au dossier :\n{folder_path}"
            )
            self.show_startup_dialog()

    def load_session_from_path(self, session_path):
        """Charge une session depuis un chemin spécifique"""
        if self.session_manager.load_session_from_file(session_path):
            self.load_session_data()
            session_name = self.session_manager.current_session.get('session_name', 'Session')
            QMessageBox.information(
                self,
                "Session chargée",
                f"Session '{session_name}' chargée avec succès!"
            )
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de charger la session sélectionnée."
            )
            # Réafficher le dialogue de démarrage
            self.show_startup_dialog()

    def start_initial_session(self):
        """Démarre une session initiale avec configuration guidée"""
        session_name, ok = QInputDialog.getText(
            self,
            "Nouvelle Session",
            "Nom de la nouvelle session:",
            text="Ma Session"
        )
        
        if ok and session_name.strip():
            # Créer la nouvelle session
            self.session_manager.start_new_session(session_name.strip())
            
            # Auto-activation des 4 DIGITS pour les sessions WM
            if session_name.upper() == "WM":
                self.litho_viewer.check_4digits.setChecked(True)
                self.validator.check_digits = True
                self.session_manager.current_session['check_digits'] = True
            
            # Configuration guidée des fichiers
            self.show_initial_setup_dialog()
        else:
            # L'utilisateur a annulé - réafficher le dialogue de démarrage
            self.show_startup_dialog()

    # Modifier aussi la méthode check_initial_setup pour ne pas s'exécuter automatiquement
    def check_initial_setup(self):
        """Vérifie si une configuration initiale est nécessaire - VERSION SIMPLIFIÉE"""
        # Cette méthode est maintenant appelée manuellement depuis handle_startup
        pass
        
    def setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('&Fichier')
        
        # Actions pour les fichiers
        load_pdf_action = file_menu.addAction('📄 Charger PDFs')
        load_pdf_action.triggered.connect(lambda: self.load_pdfs(False))
        
        load_excel_action = file_menu.addAction('📊 Charger Excel')
        load_excel_action.triggered.connect(lambda: self.load_excel(False))
        
        file_menu.addSeparator()
        
        # Menu Session
        session_menu = menubar.addMenu('&Session')
        
        # Actions pour les sessions
        new_session_action = session_menu.addAction('🆕 Nouvelle Session')
        new_session_action.triggered.connect(self.start_new_session)
        
        save_session_action = session_menu.addAction('💾 Sauvegarder Session Sous...')
        save_session_action.triggered.connect(self.save_session_as)
        
        load_session_action = session_menu.addAction('📂 Charger Session')
        load_session_action.triggered.connect(self.load_session_from_file)
        
        session_menu.addSeparator()
        
        session_info_action = session_menu.addAction('ℹ️ Infos Session')
        session_info_action.triggered.connect(self.show_session_info)
        
        # Menu Export
        export_menu = menubar.addMenu('&Export')

        self.export_action = export_menu.addAction('📋 Exporter Résultats')
        self.export_action.triggered.connect(self.export_results)
        self.export_action.setEnabled(False)

        export_menu.addSeparator()

        self.basecamp_action = export_menu.addAction('🚀 Intégration Basecamp')
        self.basecamp_action.triggered.connect(self.open_basecamp_integration)
        self.basecamp_action.setEnabled(False)
        self.basecamp_action.setToolTip("Ajouter automatiquement les commentaires d'approbation sur Basecamp")

        # Menu Affichage (3 vues: Overview, Validation, Paramètres)
        view_menu = menubar.addMenu('&Affichage')

        overview_action = view_menu.addAction('📋 Vue Overview')
        overview_action.setShortcut('Ctrl+1')
        overview_action.triggered.connect(lambda: self.switch_view_mode('overview'))
        overview_action.setToolTip("Vue d'ensemble de toutes les lithos (Liste/Grille)")

        validation_action = view_menu.addAction('🔍 Vue Validation')
        validation_action.setShortcut('Ctrl+2')
        validation_action.triggered.connect(lambda: self.switch_view_mode('validation'))
        validation_action.setToolTip("Vue détaillée de validation")

        settings_action = view_menu.addAction('⚙️ Paramètres')
        settings_action.setShortcut('Ctrl+3')
        settings_action.triggered.connect(lambda: self.switch_view_mode('settings'))
        settings_action.setToolTip("Paramètres et configuration")

        # Menu Aide
        help_menu = menubar.addMenu('&Aide')

        palette_action = help_menu.addAction('⚡ Palette de Commandes')
        palette_action.setShortcut('Ctrl+K')
        palette_action.triggered.connect(self.show_command_palette)
        palette_action.setToolTip("Ouvrir la palette de commandes (recherche rapide)")

        shortcuts_action = help_menu.addAction('⌨️ Raccourcis Clavier')
        shortcuts_action.setShortcut('Ctrl+/')
        shortcuts_action.triggered.connect(self.show_shortcuts_help)
        shortcuts_action.setToolTip("Afficher tous les raccourcis clavier disponibles")

        help_menu.addSeparator()

        quit_action = help_menu.addAction('❌ Quitter')
        quit_action.triggered.connect(self.close)

    def setup_ui(self):
        self.setup_menu()

        # Toolbar avec sélecteur de marque
        toolbar = QToolBar("Options")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 🆕 Ajouter le sélecteur de marque
        from PyQt6.QtWidgets import QComboBox
        from ..core.brand_configs import BrandRegistry

        toolbar.addWidget(QLabel("  Marque:"))
        self.brand_selector = QComboBox()
        self.brand_selector.setMinimumWidth(200)
        self.brand_selector.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background: white;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 1px solid #000;
            }
        """)

        # Peupler avec les marques disponibles
        brands = BrandRegistry.get_all_brands()
        for brand in brands:
            display_text = f"{brand.get_brand_display_name()} ({brand.get_brand_code()})"
            self.brand_selector.addItem(display_text, brand.get_brand_code())

        # Sélectionner la marque actuelle
        current_brand_code = self.current_brand_config.get_brand_code()
        for i in range(self.brand_selector.count()):
            if self.brand_selector.itemData(i) == current_brand_code:
                self.brand_selector.setCurrentIndex(i)
                break

        # Connecter le signal de changement
        self.brand_selector.currentIndexChanged.connect(self.on_brand_changed)

        toolbar.addWidget(self.brand_selector)

        # QStackedWidget pour alterner entre les vues
        self.views_stack = QStackedWidget()
        self.setCentralWidget(self.views_stack)

        # Vue validation (actuelle) - créée immédiatement
        self.validation_view_widget = self.create_validation_view()
        self.views_stack.addWidget(self.validation_view_widget)

        # Overview et Cards seront créées en lazy loading

        # Configuration CSS pour le bouton Basecamp
        self.setup_basecamp_styles()

        # Setup raccourcis clavier
        self.setup_shortcuts()

    def create_validation_view(self):
        """Crée la vue validation (interface actuelle)"""
        central_widget = QWidget()

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Splitter principal pour redimensionnement flexible
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Panel gauche compact avec infos contextuelles
        left_panel = self.create_compact_left_panel()
        splitter.addWidget(left_panel)

        # Viewer principal
        self.litho_viewer = LithoViewer(self.session_manager)
        self.litho_viewer.set_pdf_processor(self.pdf_processor)  # Connecter le PDFProcessor
        splitter.addWidget(self.litho_viewer)

        # Proportions optimales pour 14"
        splitter.setSizes([320, 880])
        splitter.setCollapsible(0, True)  # Panel gauche rétractable

        return central_widget

    def create_compact_left_panel(self):
        """Crée un panel gauche compact et moderne - AVEC infos contextuelles"""
        panel = QWidget()
        panel.setMaximumWidth(350)
        panel.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # En-tête L'Oréal
        header = self.create_loreal_header()
        layout.addWidget(header)
        
        
        # Options de validation compactes
        options_group = self.create_validation_options()
        layout.addWidget(options_group)
        
        # Navigation compacte
        nav_group = self.create_compact_navigation()
        layout.addWidget(nav_group)
        
        # Panel de validation compact
        self.validation_panel = ValidationPanel(self.session_manager)
        layout.addWidget(self.validation_panel)

        # Section BaseCamp retirée - maintenant dans ValidationPanel uniquement

        layout.addStretch()
        return panel

    def setup_basecamp_styles(self):
        """Configure les styles CSS pour les éléments Basecamp"""
        basecamp_styles = """
            QPushButton#basecampButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #2E7D32);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton#basecampButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #3E8D42);
            }
            QPushButton#basecampButton:pressed {
                background: #2E7D32;
            }
            QPushButton#basecampButton:disabled {
                background: #CCCCCC;
                color: #666666;
            }
        """

        # Ajouter les styles à la feuille de style existante
        existing_styles = self.styleSheet()
        self.setStyleSheet(existing_styles + basecamp_styles)

    def setup_shortcuts(self):
        """Configure les raccourcis clavier globaux"""
        # Ctrl+K → Command Palette
        shortcut_palette = QShortcut(QKeySequence("Ctrl+K"), self)
        shortcut_palette.activated.connect(self.show_command_palette)

        # Ctrl+/ → Shortcuts Help
        shortcut_help = QShortcut(QKeySequence("Ctrl+/"), self)
        shortcut_help.activated.connect(self.show_shortcuts_help)

        # Ctrl+1 → Overview
        shortcut_overview = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_overview.activated.connect(lambda: self.switch_view_mode('overview'))

        # Ctrl+2 → Validation
        shortcut_validation = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_validation.activated.connect(lambda: self.switch_view_mode('validation'))

        # Ctrl+3 → Paramètres
        shortcut_settings = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut_settings.activated.connect(lambda: self.switch_view_mode('settings'))

        # Ctrl+Left → PDF Précédent
        shortcut_prev_pdf = QShortcut(QKeySequence("Ctrl+Left"), self)
        shortcut_prev_pdf.activated.connect(self.previous_pdf)

        # Ctrl+Right → PDF Suivant
        shortcut_next_pdf = QShortcut(QKeySequence("Ctrl+Right"), self)
        shortcut_next_pdf.activated.connect(self.next_pdf)

        # Ctrl+Enter → Approuver
        shortcut_approve = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_approve.activated.connect(lambda: self.validation_panel.approve_btn.click() if hasattr(self, 'validation_panel') and hasattr(self.validation_panel, 'approve_btn') else None)

        # Ctrl+R → Rejeter
        shortcut_reject = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_reject.activated.connect(lambda: self.validation_panel.reject_btn.click() if hasattr(self, 'validation_panel') and hasattr(self.validation_panel, 'reject_btn') else None)

        # Ctrl+S → Sauvegarder session
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.save_session_as)

        # Ctrl+E → Exporter
        shortcut_export = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_export.activated.connect(self.export_results)

        # Enregistrer toutes les commandes
        self.register_all_commands()

    def switch_view_mode(self, mode):
        """Bascule entre les modes de vue"""
        if mode == 'overview':
            if self.overview_view is None:
                # Lazy create
                self.overview_view = OverviewView(
                    self.session_manager,
                    self.pdf_processor,
                    self.excel_processor,
                    self
                )
                self.overview_view.validation_requested.connect(self.open_validation_for_litho)
                self.views_stack.addWidget(self.overview_view)

            # Charger les données
            self.overview_view.load_lithos()

            self.views_stack.setCurrentWidget(self.overview_view)
            self.current_view_mode = 'overview'

        elif mode == 'validation':
            self.views_stack.setCurrentWidget(self.validation_view_widget)
            self.current_view_mode = 'validation'

        elif mode == 'settings':
            if not hasattr(self, 'settings_view') or self.settings_view is None:
                # Lazy create settings view
                from .settings_view import SettingsView
                self.settings_view = SettingsView(self.session_manager, self)
                self.settings_view.templates_updated.connect(self.on_templates_updated)
                self.views_stack.addWidget(self.settings_view)

            self.views_stack.setCurrentWidget(self.settings_view)
            self.current_view_mode = 'settings'

    def open_validation_for_litho(self, litho_code):
        """
        Ouvre la vue validation pour une litho spécifique
        Appelé depuis overview ou cards
        """
        # Trouver l'index du PDF
        for index, pdf_file in enumerate(self.pdf_processor.pdf_files):
            if pdf_file.startswith(litho_code):
                # Naviguer vers ce PDF
                self.pdf_processor.current_index = index
                self.pdf_processor.load_pdf(os.path.join(
                    self.pdf_processor.folder_path,
                    self.pdf_processor.pdf_files[index]
                ))

                # Basculer vers vue validation
                self.switch_view_mode('validation')

                # Mettre à jour l'affichage
                self.update_viewer()
                self.update_navigation_buttons()
                break

    def quick_approve_litho(self, litho_code):
        """
        Approuve rapidement une litho depuis la vue overview
        Sans naviguer vers la vue validation
        """
        # Sauvegarder dans la session
        self.session_manager.add_validation(litho_code, approved=True)

        # Rafraîchir la vue actuelle si c'est overview
        if self.current_view_mode == 'overview' and self.overview_view:
            self.overview_view.load_lithos()

    def quick_reject_litho(self, litho_code):
        """
        Rejette rapidement une litho depuis la vue overview
        Sans naviguer vers la vue validation
        """
        # Sauvegarder dans la session
        self.session_manager.add_validation(litho_code, rejected=True)

        # Rafraîchir la vue actuelle si c'est overview
        if self.current_view_mode == 'overview' and self.overview_view:
            self.overview_view.load_lithos()

    def register_all_commands(self):
        """Enregistre toutes les commandes disponibles dans le registre"""
        commands = [
            # Navigation
            Command(
                id="nav_overview",
                name="Vue Overview",
                description="Afficher la vue d'ensemble de toutes les lithos",
                callback=lambda: self.switch_view_mode('overview'),
                category="Navigation",
                shortcut="Ctrl+1",
                icon="📋"
            ),
            Command(
                id="nav_validation",
                name="Vue Validation",
                description="Afficher la vue détaillée de validation",
                callback=lambda: self.switch_view_mode('validation'),
                category="Navigation",
                shortcut="Ctrl+2",
                icon="🔍"
            ),
            Command(
                id="nav_settings",
                name="Paramètres",
                description="Ouvrir les paramètres de l'application",
                callback=lambda: self.switch_view_mode('settings'),
                category="Navigation",
                shortcut="Ctrl+3",
                icon="⚙️"
            ),
            Command(
                id="nav_prev_pdf",
                name="PDF Précédent",
                description="Naviguer vers le PDF précédent",
                callback=self.previous_pdf,
                category="Navigation",
                shortcut="Ctrl+Left",
                icon="◀"
            ),
            Command(
                id="nav_next_pdf",
                name="PDF Suivant",
                description="Naviguer vers le PDF suivant",
                callback=self.next_pdf,
                category="Navigation",
                shortcut="Ctrl+Right",
                icon="▶"
            ),

            # Validation
            Command(
                id="validate_approve",
                name="Approuver Litho",
                description="Approuver la litho courante",
                callback=lambda: self.validation_panel.approve_btn.click() if hasattr(self, 'validation_panel') and hasattr(self.validation_panel, 'approve_btn') else None,
                category="Validation",
                shortcut="Ctrl+Enter",
                icon="✅"
            ),
            Command(
                id="validate_reject",
                name="Rejeter Litho",
                description="Rejeter la litho courante",
                callback=lambda: self.validation_panel.reject_btn.click() if hasattr(self, 'validation_panel') and hasattr(self.validation_panel, 'reject_btn') else None,
                category="Validation",
                shortcut="Ctrl+R",
                icon="❌"
            ),

            # Session
            Command(
                id="session_new",
                name="Nouvelle Session",
                description="Créer une nouvelle session de validation",
                callback=self.start_new_session,
                category="Session",
                shortcut="Ctrl+N",
                icon="🆕"
            ),
            Command(
                id="session_save",
                name="Sauvegarder Session",
                description="Sauvegarder la session courante",
                callback=self.save_session_as,
                category="Session",
                shortcut="Ctrl+S",
                icon="💾"
            ),
            Command(
                id="session_load",
                name="Charger Session",
                description="Charger une session existante",
                callback=self.load_session_from_file,
                category="Session",
                shortcut="Ctrl+O",
                icon="📂"
            ),
            Command(
                id="session_info",
                name="Informations Session",
                description="Afficher les informations de la session courante",
                callback=self.show_session_info,
                category="Session",
                shortcut="",
                icon="ℹ️"
            ),

            # Export
            Command(
                id="export_results",
                name="Exporter Résultats",
                description="Exporter les résultats de validation",
                callback=self.export_results,
                category="Export",
                shortcut="Ctrl+E",
                icon="📋"
            ),
            Command(
                id="export_basecamp",
                name="Intégration Basecamp",
                description="Intégrer les commentaires sur Basecamp",
                callback=self.open_basecamp_integration,
                category="Export",
                shortcut="Ctrl+B",
                icon="🚀"
            ),

            # Aide
            Command(
                id="help_palette",
                name="Palette de Commandes",
                description="Ouvrir la palette de commandes",
                callback=self.show_command_palette,
                category="Aide",
                shortcut="Ctrl+K",
                icon="⚡"
            ),
            Command(
                id="help_shortcuts",
                name="Raccourcis Clavier",
                description="Afficher la liste des raccourcis clavier",
                callback=self.show_shortcuts_help,
                category="Aide",
                shortcut="Ctrl+/",
                icon="⌨️"
            ),
        ]

        self.command_registry.register_batch(commands)

    def show_command_palette(self):
        """Affiche la palette de commandes"""
        palette = CommandPalette(self.command_registry, self)
        palette.exec()

    def show_shortcuts_help(self):
        """Affiche le dialogue d'aide des raccourcis"""
        help_dialog = ShortcutsHelpDialog(self.command_registry, self)
        help_dialog.exec()

    def create_loreal_header(self):
        """Crée l'en-tête moderne L'Oréal"""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 6px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout()
        header.setLayout(layout)
        layout.setContentsMargins(8, 4, 8, 4)
        
        title = QLabel("LITHO VALIDATOR")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("L'Oréal Canada")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 8px;
                font-style: italic;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
        
    def create_validation_options(self):
        """Options de validation déplacées dans litho_viewer"""
        # Cette section a été déplacée dans litho_viewer au-dessus du tableau
        # pour gagner de la place dans le panneau gauche
        return None


    def create_compact_navigation(self):
        """Navigation compacte avec progression"""
        group = QGroupBox("Navigation")
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Boutons de navigation en ligne
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Précédent")
        self.next_btn = QPushButton("Suivant ▶")
        
        self.prev_btn.setObjectName("navigationButton")
        self.next_btn.setObjectName("navigationButton")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        
        # Progression compacte
        self.progress_label = QLabel("0 / 0 PDFs")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 9px; font-weight: 600;")
        
        self.progress_bar = QProgressBar()
        
        layout.addLayout(nav_layout)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        
        return group

    def setup_responsive_layout(self):
        """Configure le layout pour s'adapter aux petits écrans"""
        font = QFont("Segoe UI", 10)
        self.setFont(font)

    def save_session_as(self):
        """Sauvegarde la session avec dialogue de sélection"""
        # Dialogue pour le nom de session
        session_name, ok = QInputDialog.getText(
            self,
            "Sauvegarder Session",
            "Nom de la session:",
            text=self.session_manager.current_session.get('session_name', '')
        )
        
        if not ok or not session_name.strip():
            return
        
        # Proposer le dossier de sessions actuel par défaut
        default_folder = self.session_manager.get_sessions_folder()
        
        # Dialogue pour le dossier de destination
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de sauvegarde",
            default_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            if self.session_manager.save_session_as(folder, session_name.strip()):
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Session '{session_name}' sauvegardée avec succès dans:\n{folder}\n\n"
                    f"Ce dossier est maintenant votre dossier de sessions par défaut."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors de la sauvegarde de la session."
                )

    def load_session_from_file(self):
        """Charge une session depuis un fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger une session",
            "",
            "Fichiers de session (*.json);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            # Sauvegarder la session courante si elle a été modifiée
            if self.session_manager.current_session_file:
                reply = QMessageBox.question(
                    self,
                    "Sauvegarder la session courante?",
                    "Voulez-vous sauvegarder la session courante avant de charger la nouvelle?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    self.session_manager.save_session()
            
            # Charger la nouvelle session
            if self.session_manager.load_session_from_file(file_path):
                self.load_session_data()
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Session '{self.session_manager.current_session['session_name']}' chargée avec succès!"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors du chargement de la session."
                )

    def load_session_data(self):
        """Charge les données de la session courante dans l'interface"""
        session = self.session_manager.current_session

        # 🆕 Restaurer la marque depuis la session
        brand_code = session.get('brand_code', 'MNY')
        if brand_code != self.current_brand_config.get_brand_code():
            self.logger.info(f"🔄 Restoring brand from session: {brand_code}")
            self.set_brand_config(brand_code)

        # Charger les fichiers PDF
        if session['pdf_folder'] and os.path.exists(session['pdf_folder']):
            self.pdf_processor.load_folder(session['pdf_folder'])
            # 🔧 MODIFICATION: Synchroniser avec le ReportGenerator
            self.report_generator.pdf_processor = self.pdf_processor
        else:
            from ..core.brand_configs import BrandRegistry
            brand_config = BrandRegistry.get_brand(brand_code)
            self.pdf_processor = PDFProcessor(brand_config=brand_config)  # Reset si le dossier n'existe plus
            self.report_generator.pdf_processor = self.pdf_processor

        # Charger le fichier Excel
        if session['excel_file'] and os.path.exists(session['excel_file']):
            self.excel_processor.load_file(session['excel_file'])
        else:
            from ..core.brand_configs import BrandRegistry
            brand_config = BrandRegistry.get_brand(brand_code)
            self.excel_processor = ExcelProcessor(brand_config=brand_config)  # Reset si le fichier n'existe plus

        # Restaurer l'index de la litho
        if self.pdf_processor.pdf_files and session['last_litho_index'] < len(self.pdf_processor.pdf_files):
            self.pdf_processor.current_index = session['last_litho_index']
            self.pdf_processor.load_pdf(os.path.join(
                self.pdf_processor.folder_path,
                self.pdf_processor.pdf_files[self.pdf_processor.current_index]
            ))

        # Restaurer l'option check_digits
        self.litho_viewer.check_4digits.setChecked(session.get('check_digits', False))
        self.validator.check_digits = session.get('check_digits', False)

        # Restaurer la méthode de validation
        validation_method = session.get('validation_method', 0)
        self.litho_viewer.validation_method_combo.setCurrentIndex(validation_method)
        if validation_method == 1:
            self.validator.use_enhanced_validation = True
        else:
            self.validator.use_enhanced_validation = False

        # Mettre à jour l'interface
        self.update_viewer()
        self.update_navigation_buttons()
        self.validation_panel.update_lists()

    def show_session_info(self):
        """Affiche les informations de la session courante"""
        info = self.session_manager.get_session_info()
            
        message = f"""📋 Informations de la Session

        🏷️ Nom: {info['name']}
        📅 Créée: {info['created'][:19] if info['created'] else 'Non définie'}
        🔄 Modifiée: {info['updated'][:19] if info['updated'] else 'Non définie'}

        📁 Dossier PDFs: {info['pdf_folder'] or 'Non défini'}
        📊 Fichier Excel: {os.path.basename(info['excel_file']) if info['excel_file'] else 'Non défini'}

        ✅ Validations: {info['validations_count']}
        💾 Fichier: {info['file_path'] or 'Non sauvegardé'}
        📂 Dossier de sessions: {info['sessions_folder']}"""
            
        QMessageBox.information(
            self,
            "Informations de la Session",                
            message
        )

    def start_new_session(self):
        """Démarre une nouvelle session"""
        session_name, ok = QInputDialog.getText(
            self,
            "Nouvelle Session",
            "Nom de la nouvelle session:"
        )
        
        if ok and session_name.strip():
            # Demander s'il faut sauvegarder la session courante
            if self.session_manager.current_session_file or self.session_manager.current_session['validations']:
                reply = QMessageBox.question(
                    self,
                    "Sauvegarder la session courante?",
                    "Voulez-vous sauvegarder la session courante avant de créer la nouvelle?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    self.save_session_as()
            
            # Créer la nouvelle session
            self.session_manager.start_new_session(session_name.strip())
            
            # Auto-activation des 4 DIGITS pour les sessions WM
            if session_name.upper() == "WM":
                self.litho_viewer.check_4digits.setChecked(True)
                self.validator.check_digits = True
                self.session_manager.current_session['check_digits'] = True
            
            # Reset de l'interface
            self.reset_interface()
            QMessageBox.information(
                self,
                "Nouvelle Session",
                f"Nouvelle session '{session_name}' créée!"
            )

    def on_templates_updated(self):
        """Gestionnaire appelé quand les templates sont modifiés"""
        # Pour l'instant, juste un log - plus tard on pourrait recharger les templates
        self.logger.info("Templates de messages mis à jour")

    def closeEvent(self, event):
        """Gère la fermeture de l'application - SAUVEGARDE AUTOMATIQUE"""
        try:
            # Toujours sauvegarder la session courante avant de fermer
            if self.session_manager.current_session_file:
                # Si la session a déjà un fichier, la sauvegarder
                if self.session_manager.save_session():
                    print(f"Session sauvegardée automatiquement : {self.session_manager.current_session_file}")
                else:
                    print("Erreur lors de la sauvegarde automatique")
            elif self.session_manager.current_session['validations']:
                # Si la session a des validations mais pas de fichier, proposer de sauvegarder
                reply = QMessageBox.question(
                    self,
                    "Sauvegarder avant de quitter?",
                    "Voulez-vous sauvegarder la session courante avant de quitter?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    self.save_session_as()
            
            # Sauvegarder les paramètres de l'application
            self.session_manager.save_app_settings()
            
        except Exception as e:
            print(f"Erreur lors de la fermeture : {e}")
        
        event.accept()

    def reset_interface(self):
        """Réinitialise l'interface"""
        self.pdf_processor = PDFProcessor()
        self.excel_processor = ExcelProcessor()
        
        # 🔧 MODIFICATION: Maintenir la synchronisation avec le ReportGenerator
        self.report_generator.pdf_processor = self.pdf_processor
        
        self.litho_viewer.clear()
        self.validation_panel.clear()
        
        self.update_navigation_buttons()
    
    def load_new_files(self):
        """Charge de nouveaux fichiers PDF et Excel"""
        if self.load_pdfs(initial_setup=True):
            self.load_excel(initial_setup=True)
        self.update_viewer()
        self.update_navigation_buttons()

    def toggle_digits_validation(self, state):
        """Active ou désactive la vérification des 4 DIGITS"""
        self.validator.check_digits = bool(state)
        self.session_manager.current_session['check_digits'] = bool(state)
        self.session_manager.save_session()
        self.update_viewer()

    def on_validation_method_changed(self, method_index):
        """Gère le changement de méthode de validation"""
        # 0=legacy, 1=enhanced
        if method_index == 0:
            self.validator.use_enhanced_validation = False
            self.logger.info("Méthode de validation changée: Legacy")
        elif method_index == 1:
            self.validator.use_enhanced_validation = True
            self.logger.info("Méthode de validation changée: Enhanced")

        # Sauvegarder la méthode dans la session
        self.session_manager.current_session['validation_method'] = method_index
        self.session_manager.save_session()

        # Mettre à jour immédiatement le tableau avec la nouvelle méthode
        self.update_viewer()
    
    def connect_signals(self):
        """Connecte tous les signaux aux slots"""
        self.litho_viewer.check_4digits.stateChanged.connect(self.toggle_digits_validation)
        self.prev_btn.clicked.connect(self.previous_pdf)
        self.next_btn.clicked.connect(self.next_pdf)
        self.validation_panel.litho_validated.connect(self.on_litho_validated)
        self.validation_panel.pending_litho_selected.connect(self.on_pending_litho_selected)
        self.validation_panel.rejected_litho_selected.connect(self.on_rejected_litho_selected)
        self.validation_panel.validated_litho_selected.connect(self.on_validated_litho_selected)
        self.validation_panel.next_requested.connect(self.next_pdf)
        self.validation_panel.status_changed.connect(self.on_validation_status_changed)

        # Connexion pour le changement de méthode de validation
        self.litho_viewer.validation_method_changed.connect(self.on_validation_method_changed)

        # Connexions des gestionnaires de session
        self.session_manager.session_updated.connect(self.update_ui_state)
        self.session_manager.session_updated.connect(self.update_basecamp_status)
    
    def check_initial_setup(self):
        """Vérifie si une configuration initiale est nécessaire"""
        needs_setup = (not self.pdf_processor.pdf_files or 
                      self.excel_processor.data is None)
        
        if needs_setup:
            self.show_initial_setup_dialog()

    def show_initial_setup_dialog(self):
        """Affiche le dialogue de configuration initiale"""
        msg = QMessageBox()
        msg.setWindowTitle("Configuration initiale")
        msg.setText("Bienvenue dans L'Oréal Litho Validator!\n\n"
                "Pour commencer, vous devez sélectionner :\n"
                "1. Le dossier contenant les PDFs des lithos\n"
                "2. Le fichier Excel contenant les données")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
        if not self.load_pdfs(initial_setup=True):
            self.close()
            return
            
        if not self.load_excel(initial_setup=True):
            self.close()
            return
            
        self.update_viewer()
        self.update_navigation_buttons()
        
    def load_session(self):
        """Charge la session existante si elle existe"""
        if (self.session_manager.current_session['pdf_folder'] and 
            os.path.exists(self.session_manager.current_session['pdf_folder'])):
            self.pdf_processor.load_folder(self.session_manager.current_session['pdf_folder'])
            
        if (self.session_manager.current_session['excel_file'] and 
            os.path.exists(self.session_manager.current_session['excel_file'])):
            self.excel_processor.load_file(self.session_manager.current_session['excel_file'])
            
        if self.pdf_processor.pdf_files:
            self.pdf_processor.current_index = self.session_manager.current_session['last_litho_index']
            self.update_viewer()
            
        self.update_rejected_list()
        self.update_navigation_buttons()

    def load_pdfs(self, initial_setup=False):
        """Charge le dossier des PDFs"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier des PDFs",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            try:
                self.pdf_processor.load_folder(folder)
                
                self.report_generator.pdf_processor = self.pdf_processor
                
                self.session_manager.update_paths(pdf_folder=folder)
                self.update_viewer()
                self.update_navigation_buttons()
                
                if not initial_setup:
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Chargement réussi de {len(self.pdf_processor.pdf_files)} PDFs"
                    )
                return True
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors du chargement des PDFs: {str(e)}"
                )
        
        return False if initial_setup else True

    def load_excel(self, initial_setup=False):
        """Charge le fichier Excel avec aide et validation"""
        
        # Afficher l'aide sur le format requis avant de sélectionner le fichier
        if not initial_setup:
            from .excel_validator_dialog import ExcelFormatHelpDialog
            help_dialog = ExcelFormatHelpDialog(self)
            if help_dialog.exec() != QDialog.DialogCode.Accepted:
                return False
        
        # Sélection du fichier
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier Excel",
            "",
            "Excel files (*.xlsx *.xls);;Tous les fichiers (*.*)"
        )
        
        if not file_name:
            return False if initial_setup else True
        
        try:
            # Validation du format Excel
            validation_result = self.excel_processor.validate_excel_format(file_name)
            
            # Afficher le dialogue de validation
            from .excel_validator_dialog import ExcelValidatorDialog
            validator_dialog = ExcelValidatorDialog(validation_result, self)
            
            if not validation_result['is_valid']:
                # Si le fichier n'est pas valide, montrer le dialogue et arrêter
                validator_dialog.exec()
                return self.load_excel(initial_setup)  # Redemander un fichier
            else:
                # Si le fichier est valide, montrer le dialogue de confirmation
                if validator_dialog.exec() != QDialog.DialogCode.Accepted:
                    return False if initial_setup else True
            
            # Charger le fichier validé
            if self.excel_processor.load_file(file_name):
                self.session_manager.update_paths(excel_file=file_name)
                self.update_viewer()
                
                if not initial_setup:
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Fichier Excel chargé avec succès!\n"
                        f"• {validation_result['total_rows']} lignes chargées\n"
                        f"• Toutes les colonnes requises présentes"
                    )
                return True
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Erreur lors du chargement du fichier Excel validé."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du traitement du fichier Excel: {str(e)}"
            )
        
        return False if initial_setup else True
                
    def on_litho_validated(self, litho_code, status, comment):
        """Gère la validation d'une litho"""
        self.session_manager.update_litho_status(litho_code, status, comment)
        self.update_rejected_list()
        self.update_viewer()

    def update_rejected_list(self):
        """Met à jour les listes de lithos"""
        self.validation_panel.update_lists()
    
    def on_pending_litho_selected(self, litho_code):
        """Gestion du double-clic sur une litho en attente"""
        for index, pdf_file in enumerate(self.pdf_processor.pdf_files):
            if pdf_file.startswith(litho_code):
                self.pdf_processor.current_index = index
                self.pdf_processor.load_pdf(os.path.join(
                    self.pdf_processor.folder_path,
                    self.pdf_processor.pdf_files[index]
                ))
                self.update_viewer()
                self.update_navigation_buttons()
                break
        
    def on_rejected_litho_selected(self, litho_code):
        """Gestion du double-clic sur une litho rejetée"""
        for index, pdf_file in enumerate(self.pdf_processor.pdf_files):
            if pdf_file.startswith(litho_code):
                self.pdf_processor.current_index = index
                self.pdf_processor.load_pdf(os.path.join(
                    self.pdf_processor.folder_path,
                    self.pdf_processor.pdf_files[index]
                ))
                self.update_viewer()
                self.update_navigation_buttons()
                break
            
    def on_validated_litho_selected(self, litho_code):
        """Gestion du double-clic sur une litho validée"""
        for index, pdf_file in enumerate(self.pdf_processor.pdf_files):
            file_litho_code = self.pdf_processor._extract_litho_code(pdf_file)
            if file_litho_code == litho_code:
                self.pdf_processor.current_index = index
                self.pdf_processor.load_pdf(os.path.join(
                    self.pdf_processor.folder_path,
                    self.pdf_processor.pdf_files[index]
                ))
                self.update_viewer()
                self.update_navigation_buttons()
                break

    def update_litho_context_info(self, litho_code, validation_results):
        """Met à jour les informations contextuelles dans le validation panel"""

        # Analyse du type de litho
        if validation_results:
            is_cubby = validation_results[0].get('is_cubby', False)
            is_mixed = validation_results[0].get('is_mixed', False)
            has_space_savers = any(v.get('is_space_saver', False) for v in validation_results)

            # Type de litho avec icônes
            litho_types = []
            if is_cubby:
                litho_types.append("🏗️ CUBBY")
            if is_mixed:
                litho_types.append("⚠️ MIXED")
            if has_space_savers:
                litho_types.append("📦 SPACE SAVER")

            litho_type = " + ".join(litho_types) if litho_types else "📋 Standard"

            # Mise à jour du validation panel avec le type
            self.validation_panel.set_current_litho(litho_code, litho_type)

            # Résumé de validation détaillé
            if not is_cubby:
                valid_items = len([v for v in validation_results
                                 if not v.get('is_frame') and not v.get('is_space_saver')])
                passed_items = sum(1 for v in validation_results if v.get('overall', False))

                if valid_items > 0:
                    success_rate = (passed_items / valid_items) * 100

                    # Détails par type de validation
                    shade_numbers = sum(1 for v in validation_results if v.get('shade_number', False))
                    shade_names = sum(1 for v in validation_results if v.get('shade_name', False))
                    digits = sum(1 for v in validation_results if v.get('digits', False))

                    summary_text = f"Validation: {passed_items}/{valid_items} ({success_rate:.0f}%)\n"
                    summary_text += f"Teintes: {shade_numbers}/{valid_items} | "
                    summary_text += f"Noms: {shade_names}/{valid_items}"

                    if self.litho_viewer.check_4digits.isChecked():
                        summary_text += f" | Digits: {digits}/{valid_items}"

                    # Style selon le succès
                    if success_rate == 100:
                        style = f"background-color: {LorealStyles.COLORS['success']}; color: white;"
                    elif success_rate >= 80:
                        style = f"background-color: {LorealStyles.COLORS['warning']}; color: white;"
                    else:
                        style = f"background-color: {LorealStyles.COLORS['error']}; color: white;"

                else:
                    summary_text = "Aucun produit à valider"
                    style = "background-color: #f0f0f0; color: #666;"
            else:
                # Pour les CUBBY
                dimensions = validation_results[0].get('cubby_dimensions', (0, 0))
                faces, tiers = dimensions
                summary_text = f"CUBBY: {faces}F × {tiers}T ({faces * tiers} positions)"
                style = f"background-color: {LorealStyles.COLORS['accent']}; color: white;"

            # Mettre à jour le résumé dans le validation panel
            self.validation_panel.update_validation_summary(summary_text, style)
        else:
            # Mise à jour simple sans résultats
            self.validation_panel.set_current_litho(litho_code)
                
    def update_viewer(self):
        """Mise à jour de l'affichage"""
        try:
            if self.pdf_processor.current_pdf and self.excel_processor.data is not None:
                litho_code = self.pdf_processor.get_current_litho_code()
                if litho_code:
                    excel_data = self.excel_processor.get_data_for_litho(litho_code)
                    if excel_data:
                        # Afficher indicateur de chargement OCR
                        self.litho_viewer.update_ocr_status('loading')

                        # Extraire le texte avec méthode
                        text, extraction_method = self.pdf_processor.get_text_for_litho(
                            litho_code,
                            return_method=True
                        )

                        # Mettre à jour le statut OCR
                        self.litho_viewer.update_ocr_status(extraction_method)

                        # Appeler la validation (la méthode est déjà configurée via use_enhanced_validation)
                        validation_results = self.validator.validate(text, excel_data)

                        current_pdf_info = {
                            'total': len(self.pdf_processor.pdf_files),
                            'current': self.pdf_processor.current_index
                        }

                        session_stats = {
                            'approved': self.session_manager.get_approved_lithos(),
                            'rejected': self.session_manager.get_rejected_lithos()
                        }

                        # Mettre à jour les infos contextuelles dans le panneau gauche
                        self.update_litho_context_info(litho_code, validation_results)

                        # Mettre à jour le LithoViewer SANS les infos contextuelles
                        self.litho_viewer.update_content(
                            self.pdf_processor.get_current_pdf_image(),
                            excel_data,
                            validation_results,
                            check_digits=self.litho_viewer.check_4digits.isChecked(),
                            session_stats=session_stats,
                            current_pdf_info=current_pdf_info
                        )

                        self.validation_panel.set_current_litho(litho_code)
                        status_info = self.session_manager.get_litho_status(litho_code)
                        self.validation_panel.update_status(status_info)

                        # Mettre à jour les suggestions intelligentes basées sur les erreurs du tableau
                        self.validation_panel.update_quick_responses(validation_results, excel_data)

                        self.validation_panel.update_lists()
                        self.update_navigation_buttons()

        except Exception as e:
            self.litho_viewer.update_ocr_status('error')
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la mise à jour de l'affichage : {str(e)}\n"
                "Essayez de recharger le fichier Excel."
            )
        
    def update_navigation_buttons(self):
        has_pdfs = len(self.pdf_processor.pdf_files) > 0
        current_index = self.pdf_processor.current_index
        total_pdfs = len(self.pdf_processor.pdf_files)
        
        self.prev_btn.setEnabled(has_pdfs and current_index > 0)
        self.next_btn.setEnabled(has_pdfs and current_index < total_pdfs - 1)
        self.export_action.setEnabled(has_pdfs)

        # Mettre à jour le statut Basecamp
        self.update_basecamp_status()
        
        self.progress_label.setText(f"{current_index + 1 if has_pdfs else 0} / {total_pdfs} PDFs")
        self.progress_bar.setMaximum(total_pdfs)
        self.progress_bar.setValue(current_index + 1 if has_pdfs else 0)
        
    def previous_pdf(self):
        if self.pdf_processor.previous_pdf():
            self.session_manager.current_session['last_litho_index'] = self.pdf_processor.current_index
            self.session_manager.save_session()
            self.update_viewer()
            self.update_navigation_buttons()
            
    def next_pdf(self):
        if self.pdf_processor.next_pdf():
            self.session_manager.current_session['last_litho_index'] = self.pdf_processor.current_index
            self.session_manager.save_session()
            self.update_viewer()
            self.update_navigation_buttons()

    def export_results(self):
        """Exporte les résultats de validation avec toutes les données"""
        
        # Vérifier qu'on a des données à exporter
        if not self.pdf_processor.pdf_files or self.excel_processor.data is None:
            QMessageBox.warning(
                self,
                "Aucune donnée à exporter",
                "Veuillez charger des PDFs et un fichier Excel avant d'exporter."
            )
            return
        
        # Dialogue de sélection du fichier
        session_name = self.session_manager.current_session.get('session_name', 'rapport')
        default_filename = f"Rapport_{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le rapport de validation",
            default_filename,
            "Excel files (*.xlsx);;PDF files (*.pdf)"
        )
        
        if not file_name:
            return
        
        try:
            # Afficher une barre de progression
            progress = QMessageBox(self)
            progress.setWindowTitle("Export en cours")
            progress.setText("Collecte des données de validation en cours...\nVeuillez patienter.")
            progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
            progress.show()
            QApplication.processEvents()
            
            # Collecter toutes les données de validation
            from core.data_collector import ValidationDataCollector
            data_collector = ValidationDataCollector(
                self.session_manager,
                self.pdf_processor,
                self.excel_processor,
                self.validator
            )
            
            progress.setText("Analyse des résultats de validation...\nCela peut prendre quelques instants.")
            QApplication.processEvents()
            
            # Collecter toutes les données
            collected_data = data_collector.collect_all_validation_data()
            
            progress.setText("Génération du fichier de rapport avec analyse PDF...")
            QApplication.processEvents()
            
            # Générer le rapport
            self.report_generator.generate_report(file_name, collected_data)
            
            progress.close()
            
            # Afficher le résumé de l'export avec les nouvelles statistiques PDF
            total_lithos = collected_data['global_statistics']['total_lithos']
            approved = collected_data['global_statistics']['approved_lithos']
            rejected = collected_data['global_statistics']['rejected_lithos']
            pending = collected_data['global_statistics']['pending_lithos']
            
            # 🔧 MODIFICATION: Ajouter les statistiques PDF au message
            pdf_stats = self.report_generator._get_pdf_statistics(collected_data)
            valid_pdfs = pdf_stats.get('valid_pdfs', 0)
            invalid_pdfs = pdf_stats.get('invalid_pdfs', 0)
            
            QMessageBox.information(
                self,
                "Export réussi",
                f"Rapport exporté avec succès!\n\n"
                f"📁 Fichier: {os.path.basename(file_name)}\n"
                f"📊 Contenu:\n"
                f"  • {total_lithos} litho(s) analysée(s)\n"
                f"  • {approved} approuvée(s)\n"
                f"  • {rejected} rejetée(s)\n"
                f"  • {pending} en attente\n\n"
                f"📄 Analyse PDF:\n"
                f"  • {valid_pdfs} PDFs valides\n"
                f"  • {invalid_pdfs} PDFs invalides\n\n"
                f"Le rapport contient plusieurs feuilles avec :\n"
                f"  ✅ Descriptions des PDFs\n"
                f"  ✅ Statuts de validation\n"
                f"  ✅ Analyse détaillée du contenu\n"
                f"  ✅ Statistiques complètes"
            )

        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Erreur lors de la génération du rapport:\n{str(e)}\n\n"
                f"Vérifiez que le fichier n'est pas ouvert dans Excel."
            )

    def update_basecamp_status(self):
        """Met à jour le statut de l'intégration Basecamp"""
        approved_lithos = self.session_manager.get_approved_lithos()
        total_validations = len(self.session_manager.current_session.get('validations', {}))

        # Mettre à jour l'action du menu seulement
        if not approved_lithos:
            self.basecamp_action.setEnabled(False)
        else:
            self.basecamp_action.setEnabled(True)

        # Mettre à jour le tooltip avec plus d'infos
        tooltip_text = (
            f"Intégration Basecamp\n"
            f"Fichiers approuvés: {len(approved_lithos)}\n"
            f"Total validations: {total_validations}\n\n"
            f"Cette fonction ajoute automatiquement les commentaires\n"
            f"d'approbation sur Basecamp pour tous les fichiers approuvés."
        )
        self.basecamp_action.setToolTip(tooltip_text)

        # Notifier le validation panel pour qu'il mette à jour son interface
        if hasattr(self.validation_panel, 'update_basecamp_status'):
            self.validation_panel.update_basecamp_status(approved_lithos)

    def open_basecamp_integration(self):
        """Ouvre le dialogue d'intégration Basecamp"""
        try:
            # Vérifier qu'il y a des fichiers approuvés
            approved_lithos = self.session_manager.get_approved_lithos()

            if not approved_lithos:
                QMessageBox.information(
                    self,
                    "Aucun fichier approuvé",
                    "Aucun fichier n'a été approuvé dans cette session.\n\n"
                    "Veuillez d'abord valider et approuver des fichiers avant "
                    "d'utiliser l'intégration Basecamp."
                )
                return

            # Étape 1: Dialogue de configuration
            from .basecamp_dialog import BasecampConfigurationDialog, BasecampProgressDialog

            config_dialog = BasecampConfigurationDialog(self.session_manager, self)
            config_result = config_dialog.exec()

            if config_result == QDialog.DialogCode.Accepted:
                # Récupérer la configuration
                config = config_dialog.get_configuration()

                # Étape 2: Dialogue de progression avec la configuration
                progress_dialog = BasecampProgressDialog(self.session_manager, config, self)
                progress_result = progress_dialog.exec()

                if progress_result == QDialog.DialogCode.Accepted:
                    # Actions post-traitement
                    QMessageBox.information(
                        self,
                        "Intégration Basecamp",
                        "Intégration Basecamp terminée avec succès!\n\n"
                        "Vérifiez les logs pour les détails des opérations."
                    )

        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture de l'intégration Basecamp: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'ouverture de l'intégration Basecamp:\n{str(e)}"
            )

    def on_validation_status_changed(self):
        """Gère les changements de statut de validation"""
        # Sauvegarder la session
        self.session_manager.save_session()
        # Mettre à jour l'interface
        self.update_ui_state()

    def update_ui_state(self):
        """Met à jour l'état de l'interface utilisateur"""
        try:
            # Mettre à jour le panneau de validation si disponible
            if hasattr(self, 'validation_panel') and self.validation_panel:
                self.validation_panel.update_lists()

            # Mettre à jour les boutons et menus selon l'état de la session
            if hasattr(self, 'session_manager') and self.session_manager:
                has_session = bool(self.session_manager.current_session_file)

                # Activer/désactiver les boutons selon l'état
                if hasattr(self, 'generate_report_btn'):
                    self.generate_report_btn.setEnabled(has_session)

                # Mettre à jour le titre de la fenêtre
                if has_session:
                    session_name = self.session_manager.get_session_name()
                    self.setWindowTitle(f"L'Oréal Litho Validator - {session_name}")
                else:
                    self.setWindowTitle("L'Oréal Litho Validator")

        except Exception as e:
            self.logger.debug(f"Erreur mise à jour UI: {e}")