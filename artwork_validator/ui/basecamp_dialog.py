# ui/basecamp_dialog.py
import sys
import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTextEdit, QProgressBar, QListWidget,
                           QListWidgetItem, QGroupBox, QCheckBox, QFrame,
                           QRadioButton, QButtonGroup, QMessageBox, QSpinBox,
                           QLineEdit, QComboBox, QTabWidget, QWidget, QStackedWidget)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap
from ..utils.styles import LorealStyles
from ..core.basecamp import BaseCampProcessor

class BasecampConfigurationDialog(QDialog):
    """Dialogue de configuration initiale pour l'intégration Basecamp"""

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.config = {
            'processing_mode': 'approved_only',  # approved_only, rejected_only, all_validated
            'test_mode': True,
            'test_count': 3,
            'auto_continue': False,
            'project_url': 'https://3.basecamp.com/3800757/buckets/40281741/vaults/8726020777',
            'force_comments': False,
            'comment_format': 'standard'  # standard, detailed, custom
        }

        self.setup_ui()
        self.update_summary()

    def setup_ui(self):
        self.setWindowTitle("Configuration de l'intégration Basecamp")
        self.setModal(True)
        self.setMinimumSize(650, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # En-tête
        header = self.create_header()
        layout.addWidget(header)

        # Configuration par onglets
        tabs = QTabWidget()

        # Onglet 1: Sélection des fichiers
        tab1 = self.create_files_selection_tab()
        tabs.addTab(tab1, "📁 Fichiers à traiter")

        # Onglet 2: Options de traitement
        tab2 = self.create_processing_options_tab()
        tabs.addTab(tab2, "⚙️ Options")

        # Onglet 3: Instructions
        tab3 = self.create_instructions_tab()
        tabs.addTab(tab3, "📋 Instructions")

        layout.addWidget(tabs)

        # Résumé de configuration
        summary_group = self.create_summary_section()
        layout.addWidget(summary_group)

        # Boutons
        buttons = self.create_buttons()
        layout.addWidget(buttons)

        self.setStyleSheet(LorealStyles.get_main_stylesheet())

    def create_header(self):
        """En-tête avec titre et informations de session"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title = QLabel("🚀 Configuration Intégration Basecamp")
        title.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
            margin: 0px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Informations de session
        session_name = self.session_manager.current_session.get('session_name', 'Session sans nom')
        total_files = len(self.session_manager.current_session.get('validations', {}))
        approved_files = len(self.session_manager.get_approved_lithos())

        session_info = QLabel(f"Session: {session_name} | {approved_files}/{total_files} fichiers approuvés")
        session_info.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 11px;
            margin: 2px;
        """)
        session_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(session_info)

        return frame

    def create_files_selection_tab(self):
        """Onglet de sélection des fichiers à traiter"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Groupe de sélection du mode
        mode_group = QGroupBox("Quels fichiers traiter ?")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_group = QButtonGroup()

        # Options de traitement
        approved_radio = QRadioButton("Seulement les fichiers approuvés")
        approved_radio.setChecked(True)
        approved_radio.setObjectName('approved_only')

        rejected_radio = QRadioButton("Seulement les fichiers rejetés")
        rejected_radio.setObjectName('rejected_only')

        all_radio = QRadioButton("Tous les fichiers validés (approuvés + rejetés)")
        all_radio.setObjectName('all_validated')

        self.mode_group.addButton(approved_radio, 0)
        self.mode_group.addButton(rejected_radio, 1)
        self.mode_group.addButton(all_radio, 2)

        mode_layout.addWidget(approved_radio)
        mode_layout.addWidget(rejected_radio)
        mode_layout.addWidget(all_radio)

        # Descriptions des options
        desc_label = QLabel("""
        <b>Approuvés</b>: Ajoute "APPROVED" + commentaires sur Basecamp<br/>
        <b>Rejetés</b>: Ajoute "REJECTED: [raison]" + commentaires détaillés<br/>
        <b>Tous validés</b>: Traite à la fois les approuvés et les rejetés
        """)
        desc_label.setStyleSheet("font-size: 10px; color: #666; margin: 8px;")
        desc_label.setWordWrap(True)

        mode_layout.addWidget(desc_label)
        layout.addWidget(mode_group)

        # Statistiques des fichiers
        stats_group = self.create_files_stats()
        layout.addWidget(stats_group)

        # Connexions
        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        layout.addStretch()
        return widget

    def create_files_stats(self):
        """Groupe avec statistiques des fichiers"""
        group = QGroupBox("Aperçu des fichiers")
        layout = QVBoxLayout(group)

        validations = self.session_manager.current_session.get('validations', {})

        approved_count = len([v for v in validations.values() if v.get('status') == 'approved'])
        rejected_count = len([v for v in validations.values() if v.get('status') == 'rejected'])
        pending_count = len([v for v in validations.values() if v.get('status') == 'pending'])

        stats_text = f"""
        ✅ <b>{approved_count} fichiers approuvés</b><br/>
        ❌ <b>{rejected_count} fichiers rejetés</b><br/>
        ⏳ <b>{pending_count} fichiers en attente</b><br/><br/>

        <i>Note: Les fichiers en attente ne seront jamais traités par cette intégration.</i>
        """

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 11px; padding: 8px;")
        stats_label.setWordWrap(True)

        layout.addWidget(stats_label)

        # Liste des fichiers (échantillon)
        if approved_count > 0:
            sample_list = QListWidget()
            sample_list.setMaximumHeight(80)

            approved_codes = [code for code, data in validations.items() if data.get('status') == 'approved']
            for i, code in enumerate(approved_codes[:5]):
                sample_list.addItem(f"{code}.pdf")

            if len(approved_codes) > 5:
                sample_list.addItem(f"... et {len(approved_codes) - 5} autres fichiers")

            layout.addWidget(QLabel("Échantillon de fichiers approuvés:"))
            layout.addWidget(sample_list)

        return group

    def create_processing_options_tab(self):
        """Onglet des options de traitement"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Mode test
        test_group = QGroupBox("Mode test")
        test_layout = QVBoxLayout(test_group)

        self.test_checkbox = QCheckBox("Activer le mode test")
        self.test_checkbox.setChecked(True)
        self.test_checkbox.toggled.connect(self.on_test_mode_changed)

        test_desc = QLabel("Le mode test traite seulement quelques fichiers avant de demander confirmation.")
        test_desc.setStyleSheet("font-size: 10px; color: #666; margin: 4px;")
        test_desc.setWordWrap(True)

        # Nombre de fichiers de test
        test_count_layout = QHBoxLayout()
        test_count_layout.addWidget(QLabel("Nombre de fichiers à tester:"))

        self.test_count_spin = QSpinBox()
        self.test_count_spin.setRange(1, 10)
        self.test_count_spin.setValue(3)
        self.test_count_spin.valueChanged.connect(self.on_test_count_changed)

        test_count_layout.addWidget(self.test_count_spin)
        test_count_layout.addStretch()

        test_layout.addWidget(self.test_checkbox)
        test_layout.addWidget(test_desc)
        test_layout.addLayout(test_count_layout)

        layout.addWidget(test_group)

        # Options de commentaires
        comment_group = QGroupBox("Options des commentaires")
        comment_layout = QVBoxLayout(comment_group)

        self.force_comments_checkbox = QCheckBox("Forcer l'ajout même si déjà commenté par quelqu'un d'autre")
        self.force_comments_checkbox.toggled.connect(self.on_force_comments_changed)

        force_desc = QLabel("Par défaut, les fichiers déjà commentés sont ignorés.")
        force_desc.setStyleSheet("font-size: 10px; color: #666; margin: 4px;")

        comment_layout.addWidget(self.force_comments_checkbox)
        comment_layout.addWidget(force_desc)

        # Format des commentaires
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format des commentaires:"))

        self.comment_format_combo = QComboBox()
        self.comment_format_combo.addItems([
            "Standard (APPROVED/REJECTED)",
            "Détaillé (avec métadonnées)",
            "Personnalisé"
        ])
        self.comment_format_combo.currentTextChanged.connect(self.on_comment_format_changed)

        format_layout.addWidget(self.comment_format_combo)
        format_layout.addStretch()

        comment_layout.addLayout(format_layout)
        layout.addWidget(comment_group)

        # URL du projet
        url_group = QGroupBox("Projet Basecamp")
        url_layout = QVBoxLayout(url_group)

        self.project_url_edit = QLineEdit(self.config['project_url'])
        self.project_url_edit.textChanged.connect(self.on_project_url_changed)

        url_desc = QLabel("URL du dossier Basecamp (optionnel - navigation automatique)")
        url_desc.setStyleSheet("font-size: 10px; color: #666; margin: 4px;")

        url_layout.addWidget(url_desc)
        url_layout.addWidget(self.project_url_edit)

        layout.addWidget(url_group)

        layout.addStretch()
        return widget

    def create_instructions_tab(self):
        """Onglet avec instructions détaillées"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        instructions_group = QGroupBox("Instructions étape par étape")
        instructions_layout = QVBoxLayout(instructions_group)

        instructions_text = """
        <h3>🚀 Processus d'intégration Basecamp</h3>

        <h4>📋 Étapes à suivre:</h4>
        <ol>
        <li><b>Cliquez sur "Démarrer"</b> - Un navigateur Edge s'ouvrira automatiquement</li>
        <li><b>Connectez-vous à Basecamp</b> si ce n'est pas déjà fait</li>
        <li><b>Naviguez vers le dossier projet</b> contenant les fichiers PDF
            <br/><i>⚠️ Important: Ce doit être le même dossier que celui téléchargé localement</i></li>
        <li><b>Confirmez dans l'interface</b> quand vous êtes sur la bonne page</li>
        <li><b>L'automatisation démarre</b> - Restez près de l'ordinateur pour les confirmations</li>
        </ol>

        <h4>🔍 Correspondance des fichiers:</h4>
        <ul>
        <li><b>Recherche exacte</b>: Par nom de fichier complet (YCA12345.pdf)</li>
        <li><b>Recherche par code YCA</b>: Extraction du code depuis les descriptions Basecamp</li>
        <li><b>Recherche flexible</b>: Par les 8 premiers caractères si nécessaire</li>
        <li><b>Intervention manuelle</b>: Si aucune correspondance n'est trouvée</li>
        </ul>

        <h4>💬 Types de commentaires:</h4>
        <ul>
        <li><b>Fichiers approuvés</b>: "APPROVED" + votre commentaire optionnel</li>
        <li><b>Fichiers rejetés</b>: "REJECTED: [raison]" + détails du problème</li>
        <li><b>Détection des doublons</b>: Évite les commentaires multiples du même utilisateur</li>
        </ul>

        <h4>⚠️ Points d'attention:</h4>
        <ul>
        <li>Gardez la fenêtre Basecamp ouverte pendant le processus</li>
        <li>Ne naviguez pas dans Basecamp pendant l'automatisation</li>
        <li>Répondez aux dialogues de confirmation quand ils apparaissent</li>
        <li>En cas d'erreur, vous pourrez choisir de continuer ou arrêter</li>
        </ul>
        """

        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("font-size: 11px; line-height: 1.4;")

        instructions_layout.addWidget(instructions_label)
        layout.addWidget(instructions_group)

        return widget

    def create_summary_section(self):
        """Section résumé de la configuration"""
        group = QGroupBox("Résumé de configuration")
        layout = QVBoxLayout(group)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            font-size: 11px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px;
        """)
        self.summary_label.setWordWrap(True)

        layout.addWidget(self.summary_label)
        return group

    def create_buttons(self):
        """Boutons d'action"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.start_btn = QPushButton("🚀 Démarrer l'intégration")
        self.start_btn.setObjectName("approveButton")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_integration)

        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)

        layout.addWidget(cancel_btn)
        layout.addStretch()
        layout.addWidget(self.start_btn)

        return frame

    def update_summary(self):
        """Met à jour le résumé de configuration"""
        mode_text = {
            'approved_only': 'Fichiers approuvés seulement',
            'rejected_only': 'Fichiers rejetés seulement',
            'all_validated': 'Tous les fichiers validés'
        }[self.config['processing_mode']]

        test_text = f"Mode test: {self.config['test_count']} fichiers" if self.config['test_mode'] else "Mode complet"
        force_text = "Forcer les commentaires" if self.config['force_comments'] else "Ignorer si déjà commenté"

        # Calculer le nombre de fichiers à traiter
        validations = self.session_manager.current_session.get('validations', {})
        if self.config['processing_mode'] == 'approved_only':
            count = len([v for v in validations.values() if v.get('status') == 'approved'])
        elif self.config['processing_mode'] == 'rejected_only':
            count = len([v for v in validations.values() if v.get('status') == 'rejected'])
        else:
            count = len([v for v in validations.values() if v.get('status') in ['approved', 'rejected']])

        actual_count = min(count, self.config['test_count']) if self.config['test_mode'] else count

        summary = f"""
        <b>Configuration actuelle:</b><br/>
        📁 <b>Fichiers:</b> {mode_text} ({actual_count} fichiers à traiter)<br/>
        🧪 <b>Mode:</b> {test_text}<br/>
        💬 <b>Commentaires:</b> {force_text}<br/>
        🌐 <b>URL:</b> {self.config['project_url'][:50]}{'...' if len(self.config['project_url']) > 50 else ''}
        """

        self.summary_label.setText(summary)

        # Activer/désactiver le bouton start selon le nombre de fichiers
        self.start_btn.setEnabled(count > 0)

    def on_mode_changed(self):
        """Gestionnaire de changement de mode"""
        checked_button = self.mode_group.checkedButton()
        if checked_button:
            self.config['processing_mode'] = checked_button.objectName()
            self.update_summary()

    def on_test_mode_changed(self, checked):
        """Gestionnaire de changement du mode test"""
        self.config['test_mode'] = checked
        self.test_count_spin.setEnabled(checked)
        self.update_summary()

    def on_test_count_changed(self, value):
        """Gestionnaire de changement du nombre de tests"""
        self.config['test_count'] = value
        self.update_summary()

    def on_force_comments_changed(self, checked):
        """Gestionnaire de l'option forcer commentaires"""
        self.config['force_comments'] = checked
        self.update_summary()

    def on_comment_format_changed(self, text):
        """Gestionnaire du format de commentaires"""
        format_map = {
            "Standard (APPROVED/REJECTED)": "standard",
            "Détaillé (avec métadonnées)": "detailed",
            "Personnalisé": "custom"
        }
        self.config['comment_format'] = format_map.get(text, "standard")

    def on_project_url_changed(self, text):
        """Gestionnaire de changement d'URL"""
        self.config['project_url'] = text.strip()
        self.update_summary()

    def start_integration(self):
        """Lance l'intégration avec la configuration actuelle"""
        # Vérifier la configuration
        validations = self.session_manager.current_session.get('validations', {})

        if self.config['processing_mode'] == 'approved_only':
            files_to_process = [code for code, data in validations.items() if data.get('status') == 'approved']
        elif self.config['processing_mode'] == 'rejected_only':
            files_to_process = [code for code, data in validations.items() if data.get('status') == 'rejected']
        else:
            files_to_process = [code for code, data in validations.items() if data.get('status') in ['approved', 'rejected']]

        if not files_to_process:
            QMessageBox.information(
                self,
                "Aucun fichier à traiter",
                f"Aucun fichier ne correspond au mode sélectionné ({self.config['processing_mode']}).\n\n"
                "Veuillez modifier la configuration ou valider des fichiers dans l'application principale."
            )
            return

        # Confirmer avec l'utilisateur
        actual_count = min(len(files_to_process), self.config['test_count']) if self.config['test_mode'] else len(files_to_process)

        reply = QMessageBox.question(
            self,
            "Confirmer l'intégration",
            f"Prêt à traiter {actual_count} fichier(s).\n\n"
            f"Le navigateur va s'ouvrir et vous devrez:\n"
            f"1. Vous connecter à Basecamp\n"
            f"2. Naviguer vers le dossier projet\n"
            f"3. Confirmer quand vous êtes prêt\n\n"
            f"Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Fermer le dialogue de configuration et ouvrir le dialogue de progression
            self.accept()

    def get_configuration(self):
        """Retourne la configuration actuelle"""
        return self.config.copy()


class BasecampProgressDialog(QDialog):
    """Dialogue de progression pour l'intégration Basecamp"""

    def __init__(self, session_manager, config, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.config = config
        self.basecamp_processor = None
        self.worker_thread = None
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("Intégration Basecamp - Progression")
        self.setModal(True)
        self.setMinimumSize(900, 700)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # En-tête avec informations de configuration
        header = self.create_header()
        layout.addWidget(header)

        # Interface par étapes
        self.steps_widget = QStackedWidget()

        # Étape 1: Instructions de connexion
        step1 = self.create_connection_step()
        self.steps_widget.addWidget(step1)

        # Étape 2: Attente navigation dossier
        step2 = self.create_navigation_step()
        self.steps_widget.addWidget(step2)

        # Étape 3: Pré-analyse du dossier
        step3 = self.create_analysis_step()
        self.steps_widget.addWidget(step3)

        # Étape 4: Traitement en cours
        step4 = self.create_processing_step()
        self.steps_widget.addWidget(step4)

        layout.addWidget(self.steps_widget)

        # Contrôles adaptatifs
        controls = self.create_adaptive_controls()
        layout.addWidget(controls)

        # Initialiser à l'étape 1
        self.current_step = 0
        self.steps_widget.setCurrentIndex(0)
        
        self.setStyleSheet(LorealStyles.get_main_stylesheet())
        
    def create_header(self):
        """Crée l'en-tête avec informations de configuration"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title = QLabel("🚀 Intégration Basecamp en cours")
        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin: 0px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Affichage de la configuration
        mode_text = {
            'approved_only': 'Fichiers approuvés',
            'rejected_only': 'Fichiers rejetés',
            'all_validated': 'Tous fichiers validés'
        }[self.config['processing_mode']]

        test_info = f" (Test: {self.config['test_count']} fichiers)" if self.config['test_mode'] else ""

        config_info = QLabel(f"Mode: {mode_text}{test_info}")
        config_info.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 12px;
            margin: 0px;
        """)
        config_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(config_info)

        return frame

    def create_connection_step(self):
        """Étape 1: Instructions de connexion"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        step_title = QLabel("🔑 Étape 1: Connexion à Basecamp")
        step_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")

        instructions = QLabel("""
        <h3>Instructions:</h3>
        <ol>
        <li><b>Un navigateur Edge va s'ouvrir automatiquement</b></li>
        <li><b>Connectez-vous à Basecamp</b> si vous n'êtes pas déjà connecté</li>
        <li><b>Laissez cette fenêtre ouverte</b> pendant toute la durée du processus</li>
        </ol>

        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin: 10px 0;">
        <b>⚠️ Important:</b> Ne fermez pas le navigateur pendant le processus d'intégration.
        </div>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 12px; line-height: 1.4;")

        self.connection_status = QLabel("🔄 En attente du démarrage...")
        self.connection_status.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ff6b35;
            background-color: #fff5f5;
            border: 1px solid #ff6b35;
            border-radius: 4px;
            padding: 8px;
            margin: 10px 0;
        """)
        self.connection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(step_title)
        layout.addWidget(instructions)
        layout.addWidget(self.connection_status)
        layout.addStretch()

        return widget

    def create_navigation_step(self):
        """Étape 2: Navigation vers le dossier"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        step_title = QLabel("📁 Étape 2: Navigation vers le dossier projet")
        step_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")

        instructions = QLabel("""
        <h3>Maintenant, vous devez naviguer vers le dossier contenant les fichiers PDF:</h3>
        <ol>
        <li><b>Allez dans votre projet Basecamp</b></li>
        <li><b>Ouvrez le dossier "Campsite" ou "Files"</b></li>
        <li><b>Naviguez vers le dossier contenant les fichiers PDF</b>
            <br/><i>👉 C'est le même dossier que celui téléchargé sur votre ordinateur</i></li>
        <li><b>Assurez-vous de voir la liste des fichiers PDF</b></li>
        </ol>

        <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; padding: 10px; margin: 10px 0;">
        <b>💡 Astuce:</b> Les noms des fichiers dans Basecamp doivent correspondre à ceux analysés
        dans le Litho Validator (ex: YCA12345.pdf).
        </div>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 12px; line-height: 1.4;")

        self.navigation_status = QLabel("⏳ En attente que vous naviguiez vers le dossier...")
        self.navigation_status.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ff6b35;
            background-color: #fff5f5;
            border: 1px solid #ff6b35;
            border-radius: 4px;
            padding: 8px;
            margin: 10px 0;
        """)
        self.navigation_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # URL automatique si configurée
        if self.config.get('project_url'):
            auto_nav_btn = QPushButton("🌐 Navigation automatique")
            auto_nav_btn.clicked.connect(self.auto_navigate)
            auto_nav_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)

            auto_layout = QHBoxLayout()
            auto_layout.addStretch()
            auto_layout.addWidget(auto_nav_btn)
            auto_layout.addStretch()

        layout.addWidget(step_title)
        layout.addWidget(instructions)
        if self.config.get('project_url'):
            layout.addLayout(auto_layout)
        layout.addWidget(self.navigation_status)
        layout.addStretch()

        return widget

    def create_analysis_step(self):
        """Étape 3: Pré-analyse du dossier"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        step_title = QLabel("🔍 Étape 3: Analyse du dossier Basecamp")
        step_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")

        self.analysis_status = QLabel("🔄 Analyse en cours...")
        self.analysis_status.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ff6b35;
            background-color: #fff5f5;
            border: 1px solid #ff6b35;
            border-radius: 4px;
            padding: 8px;
            margin: 10px 0;
        """)
        self.analysis_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Résultats de l'analyse
        analysis_group = QGroupBox("Résultats de l'analyse")
        analysis_layout = QVBoxLayout(analysis_group)

        self.files_found_label = QLabel("Fichiers trouvés: -")
        self.files_matched_label = QLabel("Correspondances: -")
        self.files_missing_label = QLabel("Fichiers manquants: -")

        analysis_layout.addWidget(self.files_found_label)
        analysis_layout.addWidget(self.files_matched_label)
        analysis_layout.addWidget(self.files_missing_label)

        # Liste des fichiers manquants
        self.missing_files_list = QListWidget()
        self.missing_files_list.setMaximumHeight(100)
        self.missing_files_list.setVisible(False)

        missing_label = QLabel("Fichiers non trouvés dans Basecamp:")
        missing_label.setVisible(False)
        self.missing_label = missing_label

        layout.addWidget(step_title)
        layout.addWidget(self.analysis_status)
        layout.addWidget(analysis_group)
        layout.addWidget(missing_label)
        layout.addWidget(self.missing_files_list)
        layout.addStretch()

        return widget

    def create_processing_step(self):
        """Étape 4: Traitement en cours"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        step_title = QLabel("⚙️ Étape 4: Traitement des fichiers")
        step_title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")

        # Progression globale
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        self.current_file_label = QLabel("📁 Fichier: En attente...")
        self.time_label = QLabel("⏱️ Temps: 00:00")

        stats_layout = QHBoxLayout()
        self.success_label = QLabel("✅ Réussis: 0")
        self.success_label.setStyleSheet(f"color: {LorealStyles.COLORS['success']};")

        self.skip_label = QLabel("⏭️ Ignorés: 0")
        self.skip_label.setStyleSheet(f"color: {LorealStyles.COLORS['warning']};")

        self.error_label = QLabel("❌ Erreurs: 0")
        self.error_label.setStyleSheet(f"color: {LorealStyles.COLORS['error']};")

        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.skip_label)
        stats_layout.addWidget(self.error_label)
        stats_layout.addStretch()

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.current_file_label)
        progress_layout.addWidget(self.time_label)
        progress_layout.addLayout(stats_layout)

        # Logs en temps réel
        logs_group = QGroupBox("Logs en temps réel")
        logs_layout = QVBoxLayout(logs_group)

        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(200)
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #666;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Lucida Console', monospace;
                font-size: 9px;
            }
        """)

        logs_layout.addWidget(self.logs_text)

        layout.addWidget(step_title)
        layout.addWidget(progress_group)
        layout.addWidget(logs_group)
        layout.addStretch()

        return widget

    def create_adaptive_controls(self):
        """Contrôles qui s'adaptent selon l'étape"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        # Bouton principal (change selon l'étape)
        self.main_btn = QPushButton("🚀 Démarrer")
        self.main_btn.setObjectName("approveButton")
        self.main_btn.setMinimumHeight(40)
        self.main_btn.clicked.connect(self.main_action)

        # Bouton secondaire
        self.secondary_btn = QPushButton("Annuler")
        self.secondary_btn.setMinimumHeight(40)
        self.secondary_btn.clicked.connect(self.secondary_action)

        # Bouton d'aide/instructions
        help_btn = QPushButton("❓ Aide")
        help_btn.setMinimumHeight(40)
        help_btn.clicked.connect(self.show_help)

        layout.addWidget(help_btn)
        layout.addStretch()
        layout.addWidget(self.secondary_btn)
        layout.addWidget(self.main_btn)

        return frame

    def auto_navigate(self):
        """Navigation automatique vers l'URL configurée"""
        if self.basecamp_processor and self.config.get('project_url'):
            try:
                self.navigation_status.setText("🌐 Navigation automatique en cours...")
                self.basecamp_processor.driver.get(self.config['project_url'])
                self.basecamp_processor.wait_for_page_load()
                time.sleep(2)
                self.navigation_status.setText("✅ Navigation terminée - Vérifiez que vous êtes sur la bonne page")
            except Exception as e:
                self.navigation_status.setText(f"❌ Erreur de navigation: {str(e)}")

    def main_action(self):
        """Action principale selon l'étape courante"""
        if self.current_step == 0:  # Démarrer
            self.start_processing()
        elif self.current_step == 1:  # Confirmer navigation
            self.confirm_navigation()
        elif self.current_step == 2:  # Confirmer analyse
            self.confirm_analysis()
        elif self.current_step == 3:  # Arrêter traitement
            self.stop_processing()

    def secondary_action(self):
        """Action secondaire selon l'étape"""
        if self.current_step < 3:
            reply = QMessageBox.question(
                self,
                "Annuler l'intégration",
                "Êtes-vous sûr de vouloir annuler l'intégration Basecamp ?\n\n"
                "Le processus sera interrompu et le navigateur fermé.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cleanup_and_close()
        else:
            self.cleanup_and_close()

    def show_help(self):
        """Affiche l'aide contextuelle"""
        help_texts = {
            0: "Cette étape initialise la connexion à Basecamp. Un navigateur va s'ouvrir automatiquement.",
            1: "Naviguez dans Basecamp vers le dossier contenant vos fichiers PDF. Ils doivent avoir les mêmes noms que ceux analysés dans le Litho Validator.",
            2: "L'application analyse le dossier Basecamp pour identifier les correspondances avec vos fichiers validés.",
            3: "L'application traite automatiquement chaque fichier. Vous pouvez surveiller la progression en temps réel."
        }

        QMessageBox.information(
            self,
            "Aide - Étape courante",
            help_texts.get(self.current_step, "Aide non disponible pour cette étape.")
        )

    def next_step(self):
        """Passe à l'étape suivante"""
        if self.current_step < 3:
            self.current_step += 1
            self.steps_widget.setCurrentIndex(self.current_step)
            self.update_controls()

    def update_controls(self):
        """Met à jour les contrôles selon l'étape"""
        button_configs = {
            0: {"main": "🚀 Démarrer", "secondary": "Annuler"},
            1: {"main": "✅ Je suis sur la bonne page", "secondary": "Annuler"},
            2: {"main": "▶️ Commencer le traitement", "secondary": "Annuler"},
            3: {"main": "⏹️ Arrêter", "secondary": "Fermer"}
        }

        config = button_configs.get(self.current_step, button_configs[0])
        self.main_btn.setText(config["main"])
        self.secondary_btn.setText(config["secondary"])

    def cleanup_and_close(self):
        """Nettoie les ressources et ferme le dialogue"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait(1000)

        if self.basecamp_processor:
            self.basecamp_processor.cleanup()

        self.reject()

    def start_processing(self):
        """Démarre le processus d'intégration"""
        try:
            # Initialiser le processeur Basecamp
            self.basecamp_processor = BaseCampProcessor(
                session_manager=self.session_manager,
                logger=self.logger
            )

            self.connection_status.setText("🔄 Initialisation du navigateur...")
            self.connection_status.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #007bff;
                background-color: #e7f3ff;
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 8px;
                margin: 10px 0;
            """)

            if not self.basecamp_processor.setup_driver(headless=False):
                self.connection_status.setText("❌ Impossible d'initialiser le navigateur")
                return

            self.connection_status.setText("✅ Navigateur ouvert - Connectez-vous à Basecamp")
            self.connection_status.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #28a745;
                background-color: #d4edda;
                border: 1px solid #28a745;
                border-radius: 4px;
                padding: 8px;
                margin: 10px 0;
            """)

            # Ouvrir Basecamp
            login_urls = [
                "https://launchpad.37signals.com/signin",
                "https://3.basecamp.com/signin",
                "https://basecamp.com/signin"
            ]

            for url in login_urls:
                try:
                    self.basecamp_processor.driver.get(url)
                    time.sleep(2)
                    break
                except:
                    continue

            # Passer à l'étape suivante
            self.next_step()

        except Exception as e:
            self.connection_status.setText(f"❌ Erreur: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'initialisation:\n{str(e)}")

    def confirm_navigation(self):
        """L'utilisateur confirme qu'il est sur la bonne page"""
        self.navigation_status.setText("🔄 Analyse du dossier en cours...")

        # Passer à l'étape d'analyse
        self.next_step()

        # Lancer l'analyse en arrière-plan
        self.analyze_folder()

    def analyze_folder(self):
        """Analyse le dossier Basecamp pour trouver les correspondances"""
        try:
            if not self.basecamp_processor:
                return

            # Charger tous les fichiers de la page
            self.basecamp_processor.optimized_scroll_to_load_more_files()

            # Récupérer tous les liens PDF
            all_links = self.basecamp_processor.driver.find_elements(By.TAG_NAME, "a")
            basecamp_files = []

            for link in all_links:
                if not link.is_displayed():
                    continue

                link_text = link.text.strip()
                link_href = link.get_attribute('href') or ""

                if '.pdf' in link_text.lower() or '.pdf' in link_href.lower():
                    basecamp_files.append({
                        'text': link_text,
                        'href': link_href,
                        'element': link
                    })

            # Récupérer les fichiers à traiter selon la configuration
            validations = self.session_manager.current_session.get('validations', {})

            if self.config['processing_mode'] == 'approved_only':
                files_to_process = [code for code, data in validations.items() if data.get('status') == 'approved']
            elif self.config['processing_mode'] == 'rejected_only':
                files_to_process = [code for code, data in validations.items() if data.get('status') == 'rejected']
            else:
                files_to_process = [code for code, data in validations.items() if data.get('status') in ['approved', 'rejected']]

            # Analyser les correspondances
            matches = []
            missing = []

            for litho_code in files_to_process:
                filename = f"{litho_code}.pdf"
                match_found = False

                # Recherche par nom exact
                for bc_file in basecamp_files:
                    if filename.lower() in bc_file['text'].lower() or litho_code in bc_file['text']:
                        matches.append((litho_code, bc_file))
                        match_found = True
                        break

                if not match_found:
                    missing.append(litho_code)

            # Mettre à jour l'interface
            self.files_found_label.setText(f"Fichiers trouvés dans Basecamp: {len(basecamp_files)}")
            self.files_matched_label.setText(f"Correspondances identifiées: {len(matches)}")
            self.files_missing_label.setText(f"Fichiers manquants: {len(missing)}")

            if missing:
                self.missing_label.setVisible(True)
                self.missing_files_list.setVisible(True)

                for litho_code in missing:
                    self.missing_files_list.addItem(f"{litho_code}.pdf")

            # Mettre à jour le statut
            if len(matches) == 0:
                self.analysis_status.setText("❌ Aucune correspondance trouvée")
                self.analysis_status.setStyleSheet("""
                    font-size: 14px; font-weight: bold; color: #dc3545;
                    background-color: #f8d7da; border: 1px solid #dc3545;
                    border-radius: 4px; padding: 8px; margin: 10px 0;
                """)
            elif len(missing) > 0:
                self.analysis_status.setText(f"⚠️ {len(matches)} correspondances trouvées, {len(missing)} manquantes")
                self.analysis_status.setStyleSheet("""
                    font-size: 14px; font-weight: bold; color: #ff6b35;
                    background-color: #fff5f5; border: 1px solid #ff6b35;
                    border-radius: 4px; padding: 8px; margin: 10px 0;
                """)
            else:
                self.analysis_status.setText(f"✅ Toutes les correspondances trouvées ({len(matches)})")
                self.analysis_status.setStyleSheet("""
                    font-size: 14px; font-weight: bold; color: #28a745;
                    background-color: #d4edda; border: 1px solid #28a745;
                    border-radius: 4px; padding: 8px; margin: 10px 0;
                """)

            # Stocker les résultats pour le traitement
            self.analysis_results = {
                'matches': matches,
                'missing': missing,
                'basecamp_files': basecamp_files
            }

        except Exception as e:
            self.analysis_status.setText(f"❌ Erreur d'analyse: {str(e)}")
            self.analysis_status.setStyleSheet("""
                font-size: 14px; font-weight: bold; color: #dc3545;
                background-color: #f8d7da; border: 1px solid #dc3545;
                border-radius: 4px; padding: 8px; margin: 10px 0;
            """)

    def confirm_analysis(self):
        """L'utilisateur confirme de commencer le traitement"""
        if not hasattr(self, 'analysis_results'):
            QMessageBox.warning(self, "Erreur", "L'analyse n'a pas encore été effectuée.")
            return

        matches = self.analysis_results['matches']
        missing = self.analysis_results['missing']

        if len(matches) == 0:
            QMessageBox.warning(
                self,
                "Aucune correspondance",
                "Aucun fichier n'a pu être associé. Vérifiez que vous êtes dans le bon dossier."
            )
            return

        # Confirmer avec l'utilisateur
        message = f"Prêt à traiter {len(matches)} fichier(s)."
        if missing:
            message += f"\n\n⚠️ Attention: {len(missing)} fichier(s) ne seront pas traités car non trouvés dans Basecamp."

        reply = QMessageBox.question(
            self,
            "Confirmer le traitement",
            f"{message}\n\nVoulez-vous continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.next_step()
            self.start_file_processing()

    def start_file_processing(self):
        """Démarre le traitement des fichiers avec contrôle temps réel"""
        try:
            matches = self.analysis_results['matches']

            # Filtrer selon le mode test
            if self.config['test_mode']:
                matches = matches[:self.config['test_count']]
                self.add_log(f"🧪 Mode test: traitement de {len(matches)} fichiers seulement", "info")

            # Préparer les données pour le worker thread
            files_data = []
            for litho_code, basecamp_file in matches:
                # Récupérer les informations de validation
                status_info = self.session_manager.get_litho_status(litho_code)

                files_data.append({
                    'litho_code': litho_code,
                    'file_name': f"{litho_code}.pdf",
                    'comment': status_info.get('comment', '') if status_info else '',
                    'status': status_info.get('status', 'approved') if status_info else 'approved',
                    'basecamp_file': basecamp_file
                })

            # Configurer la progression
            self.progress_bar.setMaximum(len(files_data))
            self.progress_bar.setValue(0)

            # Démarrer le worker thread intelligent
            self.worker_thread = IntelligentBasecampWorkerThread(
                files_data,
                self.basecamp_processor,
                self.config
            )

            # Connexions des signaux
            self.worker_thread.progress_updated.connect(self.update_progress)
            self.worker_thread.log_message.connect(self.add_log)
            self.worker_thread.file_started.connect(self.update_current_file)
            self.worker_thread.stats_updated.connect(self.update_stats)
            self.worker_thread.user_input_required.connect(self.handle_user_input)
            self.worker_thread.test_completed.connect(self.handle_test_completion)
            self.worker_thread.finished.connect(self.processing_finished)

            # Démarrer le traitement
            self.worker_thread.start()

            # Démarrer le timer
            self.start_time = datetime.now()
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)

            # Mettre à jour les contrôles
            self.main_btn.setText("⏹️ Arrêter")
            self.secondary_btn.setText("Minimiser")

            self.add_log("🚀 Démarrage du traitement automatique", "success")

        except Exception as e:
            self.add_log(f"❌ Erreur démarrage traitement: {str(e)}", "error")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage:\n{str(e)}")

    def handle_user_input(self, input_data):
        """Gère les demandes d'intervention utilisateur"""
        input_type = input_data.get('type')
        message = input_data.get('message', '')
        options = input_data.get('options', [])
        context = input_data.get('context', {})

        if input_type == 'file_not_found':
            self.handle_file_not_found(message, options, context)
        elif input_type == 'connection_error':
            self.handle_connection_error(message, options, context)
        elif input_type == 'comment_conflict':
            self.handle_comment_conflict(message, options, context)
        elif input_type == 'general_error':
            self.handle_general_error(message, options, context)
        else:
            # Dialogue générique
            self.handle_generic_input(message, options, context)

    def handle_file_not_found(self, message, options, context):
        """Gère le cas où un fichier n'est pas trouvé"""
        file_name = context.get('file_name', 'Fichier inconnu')
        litho_code = context.get('litho_code', '')

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Fichier non trouvé")
        dialog.setText(f"Le fichier {file_name} n'a pas été trouvé dans Basecamp.")
        dialog.setDetailedText(f"Code litho: {litho_code}\n\n{message}")
        dialog.setIcon(QMessageBox.Icon.Warning)

        # Boutons personnalisés
        continue_btn = dialog.addButton("Continuer", QMessageBox.ButtonRole.AcceptRole)
        stop_btn = dialog.addButton("Arrêter", QMessageBox.ButtonRole.RejectRole)
        search_btn = dialog.addButton("Recherche manuelle", QMessageBox.ButtonRole.ActionRole)

        result = dialog.exec()

        if dialog.clickedButton() == continue_btn:
            self.worker_thread.user_response = {'action': 'continue'}
        elif dialog.clickedButton() == search_btn:
            self.worker_thread.user_response = {'action': 'manual_search'}
        else:
            self.worker_thread.user_response = {'action': 'stop'}

    def handle_connection_error(self, message, options, context):
        """Gère les erreurs de connexion"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Erreur de connexion")
        dialog.setText("Problème de connexion avec Basecamp.")
        dialog.setDetailedText(message)
        dialog.setIcon(QMessageBox.Icon.Critical)

        retry_btn = dialog.addButton("Réessayer", QMessageBox.ButtonRole.AcceptRole)
        continue_btn = dialog.addButton("Continuer", QMessageBox.ButtonRole.ActionRole)
        stop_btn = dialog.addButton("Arrêter", QMessageBox.ButtonRole.RejectRole)

        result = dialog.exec()

        if dialog.clickedButton() == retry_btn:
            self.worker_thread.user_response = {'action': 'retry'}
        elif dialog.clickedButton() == continue_btn:
            self.worker_thread.user_response = {'action': 'continue'}
        else:
            self.worker_thread.user_response = {'action': 'stop'}

    def handle_comment_conflict(self, message, options, context):
        """Gère les conflits de commentaires"""
        file_name = context.get('file_name', 'Fichier inconnu')
        existing_author = context.get('existing_author', 'Utilisateur inconnu')

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Fichier déjà commenté")
        dialog.setText(f"Le fichier {file_name} a déjà été commenté par {existing_author}.")
        dialog.setDetailedText(message)
        dialog.setIcon(QMessageBox.Icon.Question)

        ignore_btn = dialog.addButton("Ignorer", QMessageBox.ButtonRole.AcceptRole)
        force_btn = dialog.addButton("Forcer l'ajout", QMessageBox.ButtonRole.ActionRole)
        stop_btn = dialog.addButton("Arrêter", QMessageBox.ButtonRole.RejectRole)

        result = dialog.exec()

        if dialog.clickedButton() == ignore_btn:
            self.worker_thread.user_response = {'action': 'ignore'}
        elif dialog.clickedButton() == force_btn:
            self.worker_thread.user_response = {'action': 'force'}
        else:
            self.worker_thread.user_response = {'action': 'stop'}

    def handle_general_error(self, message, options, context):
        """Gère les erreurs générales"""
        file_name = context.get('file_name', 'Fichier inconnu')
        error_type = context.get('error_type', 'Erreur inconnue')

        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Erreur: {error_type}")
        dialog.setText(f"Erreur lors du traitement de {file_name}.")
        dialog.setDetailedText(message)
        dialog.setIcon(QMessageBox.Icon.Warning)

        continue_btn = dialog.addButton("Continuer", QMessageBox.ButtonRole.AcceptRole)
        retry_btn = dialog.addButton("Réessayer", QMessageBox.ButtonRole.ActionRole)
        stop_btn = dialog.addButton("Arrêter", QMessageBox.ButtonRole.RejectRole)

        result = dialog.exec()

        if dialog.clickedButton() == continue_btn:
            self.worker_thread.user_response = {'action': 'continue'}
        elif dialog.clickedButton() == retry_btn:
            self.worker_thread.user_response = {'action': 'retry'}
        else:
            self.worker_thread.user_response = {'action': 'stop'}

    def handle_generic_input(self, message, options, context):
        """Gère les demandes d'entrée génériques"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Intervention requise")
        dialog.setText(message)
        dialog.setIcon(QMessageBox.Icon.Information)

        # Ajouter les options dynamiquement
        buttons = []
        for option in options:
            btn = dialog.addButton(option['text'], QMessageBox.ButtonRole.ActionRole)
            buttons.append((btn, option['value']))

        result = dialog.exec()

        # Trouver quelle option a été cliquée
        clicked_value = 'cancel'
        for btn, value in buttons:
            if dialog.clickedButton() == btn:
                clicked_value = value
                break

        self.worker_thread.user_response = {'action': clicked_value}

    def handle_test_completion(self, test_results):
        """Gère la fin du mode test"""
        success_count = test_results.get('success', 0)
        error_count = test_results.get('errors', 0)
        total_count = test_results.get('total', 0)

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Mode test terminé")
        dialog.setText(f"Test terminé sur {total_count} fichiers.")
        dialog.setDetailedText(
            f"Résultats du test:\n"
            f"✅ Réussis: {success_count}\n"
            f"❌ Erreurs: {error_count}\n\n"
            f"Voulez-vous continuer avec tous les fichiers restants ?"
        )
        dialog.setIcon(QMessageBox.Icon.Question)

        continue_btn = dialog.addButton("Continuer avec tous", QMessageBox.ButtonRole.AcceptRole)
        stop_btn = dialog.addButton("Arrêter ici", QMessageBox.ButtonRole.RejectRole)

        result = dialog.exec()

        if dialog.clickedButton() == continue_btn:
            self.worker_thread.user_response = {'action': 'continue_all'}
        else:
            self.worker_thread.user_response = {'action': 'stop'}

    def update_progress(self, current, total):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(current)
        percentage = (current / total * 100) if total > 0 else 0
        self.progress_bar.setFormat(f"{current}/{total} ({percentage:.1f}%)")

    def update_current_file(self, file_name):
        """Met à jour le fichier en cours"""
        self.current_file_label.setText(f"📁 Fichier: {file_name}")

    def update_stats(self, stats):
        """Met à jour les statistiques"""
        self.success_label.setText(f"✅ Réussis: {stats.get('success', 0)}")
        self.skip_label.setText(f"⏭️ Ignorés: {stats.get('skipped', 0)}")
        self.error_label.setText(f"❌ Erreurs: {stats.get('errors', 0)}")

    def update_time(self):
        """Met à jour le temps écoulé"""
        if hasattr(self, 'start_time') and self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # Supprimer les microsecondes
            self.time_label.setText(f"⏱️ Temps: {elapsed_str}")

    def add_log(self, message, level="info"):
        """Ajoute un message aux logs avec couleurs"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#ffffff",
            "success": "#90EE90",
            "warning": "#FFD700",
            "error": "#FF6B6B"
        }

        color = colors.get(level, "#ffffff")
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'

        self.logs_text.append(formatted_message)

        # Auto-scroll vers le bas
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.logs_text.setTextCursor(cursor)

    def processing_finished(self):
        """Traitement terminé"""
        if hasattr(self, 'timer'):
            self.timer.stop()

        self.main_btn.setText("✅ Terminé")
        self.main_btn.setEnabled(False)
        self.secondary_btn.setText("Fermer")

        self.add_log("🎉 Traitement terminé avec succès", "success")

    def setup_connections(self):
        """Configure les connexions des signaux"""
        try:
            # Timer pour le temps écoulé
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_time)
            self.start_time = None

            # Initialiser les variables nécessaires
            self.files_list = None  # Sera initialisé dans create_processing_step si nécessaire

        except Exception as e:
            # Logger pour debugging si nécessaire
            print(f"Erreur setup_connections: {e}")

    def update_time(self):
        """Met à jour l'affichage du temps écoulé"""
        try:
            if self.start_time and hasattr(self, 'time_label'):
                elapsed = datetime.now() - self.start_time
                minutes = int(elapsed.total_seconds() // 60)
                seconds = int(elapsed.total_seconds() % 60)
                self.time_label.setText(f"⏱️ Temps: {minutes:02d}:{seconds:02d}")
        except Exception as e:
            print(f"Erreur update_time: {e}")


class IntelligentBasecampWorkerThread(QThread):
    """Worker thread intelligent avec gestion des erreurs et intervention utilisateur"""

    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str, str)
    file_started = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)
    user_input_required = pyqtSignal(dict)
    test_completed = pyqtSignal(dict)

    def __init__(self, files_data, basecamp_processor, config):
        super().__init__()
        self.files_data = files_data
        self.basecamp_processor = basecamp_processor
        self.config = config
        self.should_stop = False
        self.user_response = None

        self.stats = {
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'not_found': 0
        }

    def stop(self):
        self.should_stop = True

    def wait_for_user_response(self):
        """Attend la réponse de l'utilisateur"""
        self.user_response = None
        while self.user_response is None and not self.should_stop:
            self.msleep(100)
        return self.user_response

    def run(self):
        """Exécute le traitement intelligent"""
        try:
            total_files = len(self.files_data)
            test_mode = self.config.get('test_mode', False)
            test_count = self.config.get('test_count', 3)

            self.log_message.emit(f"🚀 Début du traitement de {total_files} fichiers", "info")

            for index, file_data in enumerate(self.files_data):
                if self.should_stop:
                    self.log_message.emit("⏹️ Traitement arrêté par l'utilisateur", "warning")
                    break

                # Utiliser le code litho seul pour correspondance BaseCamp (sans .pdf)
                file_name = file_data['litho_code']  # Ex: YCA28654 au lieu de YCA28654.pdf
                litho_code = file_data['litho_code']
                comment = file_data.get('comment', '')
                status = file_data.get('status', 'approved')

                # Logging pour debug
                original_file_name = file_data.get('file_name', 'N/A')
                self.log_message.emit(f"🔍 Recherche: {file_name} (original: {original_file_name})", "debug")

                self.file_started.emit(file_name)
                self.log_message.emit(f"📁 [{index + 1}/{total_files}] Traitement de {file_name}", "info")

                # Traitement avec gestion d'erreurs intelligente
                max_retries = 3
                current_retry = 0

                while current_retry < max_retries and not self.should_stop:
                    try:
                        result = self.basecamp_processor.process_file(
                            file_name, litho_code, comment, status,
                            force_comment=self.config.get('force_comments', False)
                        )

                        if result == "success":
                            self.stats['success'] += 1
                            self.log_message.emit(f"✅ {file_name} - Traité avec succès", "success")
                            break

                        elif result == "skipped":
                            self.stats['skipped'] += 1
                            self.log_message.emit(f"⏭️ {file_name} - Ignoré (déjà traité)", "warning")
                            break

                        elif result == "not_found":
                            # Demander à l'utilisateur que faire
                            self.user_input_required.emit({
                                'type': 'file_not_found',
                                'message': f"Le fichier {file_name} n'a pas pu être localisé dans Basecamp malgré plusieurs stratégies de recherche.",
                                'context': {
                                    'file_name': file_name,
                                    'litho_code': litho_code
                                }
                            })

                            response = self.wait_for_user_response()
                            if response and response.get('action') == 'continue':
                                self.stats['not_found'] += 1
                                self.log_message.emit(f"❓ {file_name} - Non trouvé, continue", "warning")
                                break
                            elif response and response.get('action') == 'stop':
                                self.should_stop = True
                                break
                            # Pour manual_search, on pourrait implémenter une logique spéciale

                        else:  # error
                            current_retry += 1
                            if current_retry < max_retries:
                                self.log_message.emit(f"⚠️ {file_name} - Erreur (tentative {current_retry}/{max_retries})", "warning")
                                self.msleep(2000)  # Attendre 2 secondes avant retry
                            else:
                                # Demander à l'utilisateur que faire
                                self.user_input_required.emit({
                                    'type': 'general_error',
                                    'message': f"Erreur persistante lors du traitement de {file_name} après {max_retries} tentatives.",
                                    'context': {
                                        'file_name': file_name,
                                        'litho_code': litho_code,
                                        'error_type': 'Erreur de traitement'
                                    }
                                })

                                response = self.wait_for_user_response()
                                if response and response.get('action') == 'continue':
                                    self.stats['errors'] += 1
                                    self.log_message.emit(f"❌ {file_name} - Erreur, continue", "error")
                                    break
                                elif response and response.get('action') == 'stop':
                                    self.should_stop = True
                                    break
                                elif response and response.get('action') == 'retry':
                                    current_retry = 0  # Reset retry counter
                                    self.log_message.emit(f"🔄 {file_name} - Nouvelle tentative", "info")

                    except Exception as e:
                        current_retry += 1
                        self.log_message.emit(f"❌ Erreur inattendue pour {file_name}: {str(e)}", "error")

                        if current_retry >= max_retries:
                            self.stats['errors'] += 1
                            break

                self.stats_updated.emit(self.stats)
                self.progress_updated.emit(index + 1, total_files)

                # Gérer le mode test
                if test_mode and index + 1 == test_count and index + 1 < total_files:
                    # Test terminé, demander à l'utilisateur
                    test_results = {
                        'total': test_count,
                        'success': self.stats['success'],
                        'errors': self.stats['errors'] + self.stats['not_found']
                    }

                    self.test_completed.emit(test_results)
                    response = self.wait_for_user_response()

                    if response and response.get('action') == 'continue_all':
                        self.log_message.emit("🚀 Continuation avec tous les fichiers restants", "info")
                        # Continuer avec tous les fichiers
                    else:
                        self.log_message.emit("⏹️ Arrêt après le mode test", "info")
                        break

                # Navigation retour pour le fichier suivant
                if index < total_files - 1 and not self.should_stop:
                    try:
                        self.basecamp_processor.navigate_back_to_files()
                        self.basecamp_processor.optimized_scroll_to_load_more_files()
                    except Exception as e:
                        self.log_message.emit(f"⚠️ Erreur navigation: {str(e)}", "warning")

                    self.msleep(1500)  # Pause entre fichiers

            # Rapport final
            total_processed = self.stats['success'] + self.stats['skipped'] + self.stats['errors'] + self.stats['not_found']
            success_rate = (self.stats['success'] / total_processed * 100) if total_processed > 0 else 0

            self.log_message.emit(
                f"🎉 Traitement terminé! {self.stats['success']}/{total_processed} réussis ({success_rate:.1f}%)",
                "success"
            )

        except Exception as e:
            self.log_message.emit(f"❌ Erreur critique: {str(e)}", "error")
        finally:
            if self.basecamp_processor:
                self.basecamp_processor.cleanup()

    def stop_processing(self):
        """Arrête le traitement en cours"""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Arrêter le traitement",
                "Voulez-vous vraiment arrêter le traitement en cours ?\n\n"
                "Les fichiers déjà traités ne seront pas affectés.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.stop()
                self.add_log("⏹️ Arrêt demandé par l'utilisateur", "warning")

    def create_config_section(self):
        """Section de configuration et aperçu des fichiers"""
        group = QGroupBox("Configuration & Aperçu")
        layout = QVBoxLayout(group)
        
        # Informations sur la session
        session_info = self.create_session_info()
        layout.addWidget(session_info)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.test_mode_check = QCheckBox("Mode test (3 premiers fichiers)")
        self.test_mode_check.setStyleSheet("font-size: 11px; font-weight: 500;")
        
        self.auto_navigate_check = QCheckBox("Navigation automatique entre fichiers")
        self.auto_navigate_check.setChecked(True)
        self.auto_navigate_check.setStyleSheet("font-size: 11px; font-weight: 500;")
        
        options_layout.addWidget(self.test_mode_check)
        options_layout.addWidget(self.auto_navigate_check)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Liste des fichiers à traiter
        files_label = QLabel("📁 Fichiers à traiter:")
        files_label.setStyleSheet("font-size: 12px; font-weight: 600; margin-top: 8px;")
        layout.addWidget(files_label)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        self.files_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
            }}
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }}
        """)
        layout.addWidget(self.files_list)
        
        self.update_files_list()
        
        return group
        
    def create_session_info(self):
        """Informations sur la session courante"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        
        # Récupérer les informations de session
        approved_lithos = self.session_manager.get_approved_lithos()
        session_name = self.session_manager.current_session.get('session_name', 'Session sans nom')
        
        info_layout = QHBoxLayout()
        
        session_label = QLabel(f"📋 Session: {session_name}")
        session_label.setStyleSheet("font-size: 11px; font-weight: 600;")
        
        files_count_label = QLabel(f"✅ Fichiers approuvés: {len(approved_lithos)}")
        files_count_label.setStyleSheet(f"font-size: 11px; color: {LorealStyles.COLORS['success']}; font-weight: 600;")
        
        info_layout.addWidget(session_label)
        info_layout.addStretch()
        info_layout.addWidget(files_count_label)
        
        layout.addLayout(info_layout)
        
        # Instructions
        instructions = QLabel(
            "⚠️  Assurez-vous d'être connecté à Basecamp et d'être sur la page du dossier de fichiers avant de démarrer."
        )
        instructions.setStyleSheet(f"""
            font-size: 10px; 
            color: {LorealStyles.COLORS['warning']}; 
            font-style: italic;
            background-color: #fff8dc;
            padding: 6px;
            border-radius: 4px;
            border: 1px solid {LorealStyles.COLORS['warning']};
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        return frame
        
    def create_progress_section(self):
        """Section de progression"""
        group = QGroupBox("Progression")
        layout = QVBoxLayout(group)
        
        # Barre de progression principale
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                text-align: center;
                background-color: {LorealStyles.COLORS['background']};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {LorealStyles.COLORS['primary']};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Labels de statut
        status_layout = QHBoxLayout()
        
        self.current_file_label = QLabel("📁 Fichier: En attente...")
        self.current_file_label.setStyleSheet("font-size: 11px; font-weight: 500;")
        
        self.time_label = QLabel("⏱️ Temps: 00:00")
        self.time_label.setStyleSheet("font-size: 11px; color: #666;")
        
        status_layout.addWidget(self.current_file_label)
        status_layout.addStretch()
        status_layout.addWidget(self.time_label)
        
        layout.addLayout(status_layout)
        
        # Statistiques en temps réel
        stats_layout = QHBoxLayout()
        
        self.success_label = QLabel("✅ Réussis: 0")
        self.success_label.setStyleSheet(f"font-size: 10px; color: {LorealStyles.COLORS['success']};")
        
        self.skip_label = QLabel("⏭️ Déjà approuvés: 0")
        self.skip_label.setStyleSheet(f"font-size: 10px; color: {LorealStyles.COLORS['warning']};")
        
        self.error_label = QLabel("❌ Erreurs: 0")
        self.error_label.setStyleSheet(f"font-size: 10px; color: {LorealStyles.COLORS['error']};")
        
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.skip_label)
        stats_layout.addWidget(self.error_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        return group
        
    def create_logs_section(self):
        """Section des logs en temps réel"""
        group = QGroupBox("Logs en temps réel")
        layout = QVBoxLayout(group)
        
        self.logs_text = QTextEdit()
        self.logs_text.setMaximumHeight(200)
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Lucida Console', monospace;
                font-size: 9px;
            }}
        """)
        layout.addWidget(self.logs_text)
        
        return group
        
    def create_controls(self):
        """Boutons de contrôle"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        self.start_btn = QPushButton("🚀 Démarrer l'ajout automatique")
        self.start_btn.setObjectName("approveButton")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_processing)
        
        self.stop_btn = QPushButton("⏹️ Arrêter")
        self.stop_btn.setObjectName("rejectButton")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        
        self.close_btn = QPushButton("✕ Fermer")
        self.close_btn.setMinimumHeight(40)
        self.close_btn.clicked.connect(self.accept)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()
        layout.addWidget(self.close_btn)
        
        return frame
        
    def setup_connections(self):
        """Configure les connexions des signaux"""
        # Timer pour le temps écoulé
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.start_time = None
        
    def update_files_list(self):
        """Met à jour la liste des fichiers à traiter"""
        approved_lithos = self.session_manager.get_approved_lithos()
        
        # ✅ Vérifier que files_list existe avant de l'utiliser
        if self.files_list is None:
            return  # Pas encore initialisé
        
        self.files_list.clear()
        
        if not approved_lithos:
            item = QListWidgetItem("Aucun fichier approuvé à traiter")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.files_list.addItem(item)
        else:
            for i, litho_code in enumerate(approved_lithos, 1):
                # Convertir le code litho en nom de fichier PDF
                file_name = f"{litho_code}.pdf"
                
                item = QListWidgetItem(f"{i:2d}. {file_name}")
                item.setData(Qt.ItemDataRole.UserRole, litho_code)
                
                # Style selon le statut
                item.setIcon(QIcon())  # Vous pouvez ajouter une icône ici
                
                self.files_list.addItem(item)
                
        # ✅ Vérifier que start_btn existe avant de l'utiliser
        if self.start_btn is not None:
            self.start_btn.setEnabled(len(approved_lithos) > 0)
        
    def start_processing(self):
        """Démarre le traitement des fichiers"""
        approved_lithos = self.session_manager.get_approved_lithos()
        
        if not approved_lithos:
            self.add_log("❌ Aucun fichier approuvé à traiter", "error")
            return
        
        # Préparer les données
        files_data = []
        for litho_code in approved_lithos:
            # Récupérer les informations de validation
            status_info = self.session_manager.get_litho_status(litho_code)
            comment = status_info.get('comment', '') if status_info else ''
            
            files_data.append({
                'litho_code': litho_code,
                'file_name': f"{litho_code}.pdf",
                'comment': comment
            })
        
        # Mode test
        if self.test_mode_check.isChecked():
            files_data = files_data[:3]
            self.add_log(f"🧪 Mode test activé: {len(files_data)} fichiers", "info")
        
        # Initialiser la progression
        self.progress_bar.setMaximum(len(files_data))
        self.progress_bar.setValue(0)
        
        # Démarrer le worker thread
        self.worker_thread = BasecampWorkerThread(files_data, self.auto_navigate_check.isChecked())
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.log_message.connect(self.add_log)
        self.worker_thread.file_started.connect(self.update_current_file)
        self.worker_thread.stats_updated.connect(self.update_stats)
        self.worker_thread.finished.connect(self.processing_finished)
        
        # Démarrer
        self.worker_thread.start()
        
        # Mettre à jour l'interface
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        
        # Démarrer le timer
        self.start_time = datetime.now()
        self.timer.start(1000)  # Update every second
        
        self.add_log("🚀 Démarrage du traitement automatique", "success")
        
    def stop_processing(self):
        """Arrête le traitement"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.add_log("⏹️ Arrêt demandé par l'utilisateur", "warning")
        
    def processing_finished(self):
        """Traitement terminé"""
        # Arrêter le timer
        self.timer.stop()
        
        # Remettre à jour l'interface
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        
        self.add_log("🎉 Traitement terminé", "success")
        
    def update_progress(self, current, total):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(current)
        percentage = (current / total * 100) if total > 0 else 0
        
    def update_current_file(self, file_name):
        """Met à jour le fichier en cours"""
        self.current_file_label.setText(f"📁 Fichier: {file_name}")
        
    def update_stats(self, stats):
        """Met à jour les statistiques"""
        self.success_label.setText(f"✅ Réussis: {stats.get('success', 0)}")
        self.skip_label.setText(f"⏭️ Déjà approuvés: {stats.get('skipped', 0)}")
        self.error_label.setText(f"❌ Erreurs: {stats.get('errors', 0)}")
        
    def update_time(self):
        """Met à jour le temps écoulé"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            self.time_label.setText(f"⏱️ Temps: {elapsed_str}")
            
    def add_log(self, message, level="info"):
        """Ajoute un message aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Couleurs selon le niveau
        colors = {
            "info": "#ffffff",
            "success": "#90EE90",
            "warning": "#FFD700", 
            "error": "#FF6B6B"
        }
        
        color = colors.get(level, "#ffffff")
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        self.logs_text.append(formatted_message)
        
        # Auto-scroll vers le bas
        cursor = self.logs_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.logs_text.setTextCursor(cursor)


class BasecampWorkerThread(QThread):
    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str, str)
    file_started = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, files_data, auto_navigate=True):
        super().__init__()
        self.files_data = files_data
        self.auto_navigate = auto_navigate
        self.should_stop = False
        self.stats = {
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'not_found': 0
        }
        
    def stop(self):
        self.should_stop = True
        
    def run(self):
        """Exécute le traitement dans un thread séparé"""
        try:
            # Initialiser le processeur Basecamp
            processor = BaseCampProcessor()
            
            self.log_message.emit("🔧 Initialisation du navigateur...", "info")
            if not processor.setup_driver():
                self.log_message.emit("❌ Impossible d'initialiser le navigateur", "error")
                return
            
            self.log_message.emit("✅ Navigateur initialisé", "success")
            self.log_message.emit("⚠️ Veuillez vous connecter à Basecamp et naviguer vers le dossier de fichiers", "warning")
            
            # Attendre que l'utilisateur soit prêt (dans l'interface principale)
            processor.wait_for_user_ready()
            
            total_files = len(self.files_data)
            
            for index, file_data in enumerate(self.files_data):
                if self.should_stop:
                    self.log_message.emit("⏹️ Traitement arrêté", "warning")
                    break
                
                file_name = file_data['file_name']
                comment = file_data['comment']
                litho_code = file_data['litho_code']
                
                self.file_started.emit(file_name)
                self.log_message.emit(f"🔍 Traitement de {file_name}...", "info")
                
                # Traitement du fichier avec logique YCA
                result = processor.process_file(file_name, litho_code, comment)

                # Mettre à jour les statistiques et logs
                if result == "success":
                    self.stats['success'] += 1
                    self.log_message.emit(f"✅ {file_name} - Commentaire APPROVED ajouté avec succès", "success")
                elif result == "skipped":
                    self.stats['skipped'] += 1
                    self.log_message.emit(f"⏭️ {file_name} - Déjà approuvé par vous", "warning")
                elif result == "not_found":
                    self.stats['not_found'] += 1
                    self.log_message.emit(f"❓ {file_name} - Fichier non trouvé dans Basecamp", "warning")
                else:  # error
                    self.stats['errors'] += 1
                    self.log_message.emit(f"❌ {file_name} - Erreur lors du traitement", "error")

                self.stats_updated.emit(self.stats)
                self.progress_updated.emit(index + 1, total_files)

                # Navigation vers le fichier suivant
                if index < total_files - 1 and not self.should_stop:
                    if result in ["success", "skipped", "error"]:
                        self.log_message.emit("🔄 Retour à la liste des fichiers...", "info")
                        processor.navigate_back_to_files()
                        # Recharger la page pour s'assurer que tous les fichiers sont visibles
                        processor.optimized_scroll_to_load_more_files()
                    time.sleep(1)  # Pause entre les fichiers

            # Rapport final
            success_rate = (self.stats['success'] / total_files * 100) if total_files > 0 else 0
            self.log_message.emit(
                f"🎉 Traitement terminé! Succès: {self.stats['success']}/{total_files} ({success_rate:.1f}%)",
                "success"
            )
            
        except Exception as e:
            self.log_message.emit(f"❌ Erreur critique: {str(e)}", "error")
            logging.exception("Erreur dans BasecampWorkerThread")
        finally:
            # Nettoyage
            if 'processor' in locals():
                processor.cleanup()
                self.log_message.emit("🧹 Nettoyage terminé", "info")