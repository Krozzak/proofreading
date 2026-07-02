# ui/settings_view.py
"""
Vue de paramètres et configuration de l'application (onglet principal)
Permet de gérer les templates de messages, les infos de session, et les paramètres globaux
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QTextEdit, QPushButton, QGroupBox,
                             QListWidget, QMessageBox, QLineEdit, QScrollArea,
                             QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from ..utils.styles import LorealStyles
from ..core.error_templates import ERROR_TEMPLATES, ErrorTemplate
import json


class SettingsView(QWidget):
    """Vue de paramètres et configuration pour l'onglet principal"""

    templates_updated = pyqtSignal()  # Signal émis quand les templates sont modifiés

    def __init__(self, session_manager=None, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.modified_templates = {}  # Stockage temporaire des modifications
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface de la vue"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tête
        header = self.create_header()
        layout.addWidget(header)

        # Onglets internes
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {LorealStyles.COLORS['border']};
                background: white;
            }}
            QTabBar::tab {{
                background: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: white;
                border-bottom: none;
                font-weight: 600;
            }}
        """)

        # Onglet 1: Informations de session
        session_tab = self.create_session_tab()
        tabs.addTab(session_tab, "📋 Session")

        # Onglet 2: Templates de messages
        templates_tab = self.create_templates_tab()
        tabs.addTab(templates_tab, "💬 Templates de Messages")

        # Onglet 2.5: Layout OCR Configuration
        from .layout_config_tab import LayoutConfigTab
        layout_tab = LayoutConfigTab(self)
        layout_tab.layout_config_changed.connect(self.on_layout_config_changed)
        tabs.addTab(layout_tab, "🎯 Layout OCR")
        self.layout_tab = layout_tab

        # Onglet 3: Paramètres généraux (futur)
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "⚙️ Paramètres Généraux")

        # 🆕 Onglet 4: Règles de validation par marque
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info("🔄 Loading BrandRulesTab...")
            from .brand_rules_tab import BrandRulesTab
            logger.info("✅ BrandRulesTab imported successfully")

            brand_rules_tab = BrandRulesTab()
            logger.info("✅ BrandRulesTab instance created")

            tabs.addTab(brand_rules_tab, "🏷️ Règles de Marques")
            logger.info("✅ BrandRulesTab tab added to settings")

        except Exception as e:
            import traceback
            logger.error(f"❌ Erreur lors du chargement de l'onglet Règles de Marques: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Ajouter un onglet placeholder en cas d'erreur
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)

            error_label = QLabel(f"Erreur de chargement:\n\n{str(e)}\n\nVoir les logs pour plus de détails.")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: red; padding: 10px;")
            placeholder_layout.addWidget(error_label)

            tabs.addTab(placeholder, "🏷️ Règles de Marques (Erreur)")
            logger.info("⚠️ Placeholder tab added due to error")

        layout.addWidget(tabs)

    def create_header(self):
        """Crée l'en-tête de la vue"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout()
        header.setLayout(layout)

        title = QLabel("⚙️ Paramètres & Configuration")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Gérez vos templates, paramètres de session et configuration globale")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px;")
        layout.addWidget(subtitle)

        return header

    def create_session_tab(self):
        """Crée l'onglet d'informations de session"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titre
        title = QLabel("📋 Informations de la Session Courante")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {LorealStyles.COLORS['primary']};")
        layout.addWidget(title)

        if not self.session_manager:
            no_session = QLabel("Aucune session active")
            no_session.setStyleSheet("color: #999; font-style: italic;")
            layout.addWidget(no_session)
            layout.addStretch()
            return tab

        # Récupérer les informations de session
        session_info = self.session_manager.get_session_info()

        # Groupe: Informations générales
        general_group = QGroupBox("Informations Générales")
        general_layout = QVBoxLayout()
        general_group.setLayout(general_layout)

        info_items = [
            ("🏷️ Nom de la session", session_info.get('name', 'Non défini')),
            ("📅 Date de création", session_info.get('created', 'Non définie')[:19] if session_info.get('created') else 'N/A'),
            ("🔄 Dernière modification", session_info.get('updated', 'Non définie')[:19] if session_info.get('updated') else 'N/A'),
            ("💾 Fichier de session", session_info.get('file_path', 'Non sauvegardé') or 'Non sauvegardé'),
            ("📂 Dossier de sessions", session_info.get('sessions_folder', 'Non défini')),
        ]

        for label_text, value_text in info_items:
            item_layout = QHBoxLayout()

            label = QLabel(label_text)
            label.setStyleSheet("font-weight: 600; min-width: 200px;")

            value = QLabel(str(value_text))
            value.setStyleSheet("color: #666;")
            value.setWordWrap(True)

            item_layout.addWidget(label)
            item_layout.addWidget(value, 1)
            general_layout.addLayout(item_layout)

        layout.addWidget(general_group)

        # Groupe: Fichiers chargés
        files_group = QGroupBox("Fichiers Chargés")
        files_layout = QVBoxLayout()
        files_group.setLayout(files_layout)

        pdf_folder = session_info.get('pdf_folder', 'Non défini')
        excel_file = session_info.get('excel_file', 'Non défini')

        pdf_label = QLabel(f"📁 Dossier PDF: {pdf_folder}")
        pdf_label.setWordWrap(True)
        files_layout.addWidget(pdf_label)

        excel_label = QLabel(f"📊 Fichier Excel: {excel_file}")
        excel_label.setWordWrap(True)
        files_layout.addWidget(excel_label)

        layout.addWidget(files_group)

        # Groupe: Statistiques
        stats_group = QGroupBox("Statistiques de Validation")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)

        validations_count = session_info.get('validations_count', 0)
        approved = len(self.session_manager.get_approved_lithos())
        rejected = len(self.session_manager.get_rejected_lithos())

        stats_text = f"""
        ✅ Approuvées: {approved}
        ❌ Refusées: {rejected}
        📊 Total des validations: {validations_count}
        """

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 13px; line-height: 1.6;")
        stats_layout.addWidget(stats_label)

        layout.addWidget(stats_group)

        layout.addStretch()

        return tab

    def create_templates_tab(self):
        """Crée l'onglet de gestion des templates"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Titre
        title = QLabel("💬 Templates de Messages de Validation")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {LorealStyles.COLORS['primary']};")
        main_layout.addWidget(title)

        description = QLabel("Personnalisez les messages de validation automatiques utilisés pour les réponses rapides.")
        description.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        # Layout horizontal: liste + éditeur
        content_layout = QHBoxLayout()

        # Liste des templates (gauche)
        list_container = QWidget()
        list_layout = QVBoxLayout()
        list_container.setLayout(list_layout)
        list_container.setMaximumWidth(300)

        list_label = QLabel("📝 Templates disponibles:")
        list_label.setStyleSheet("font-weight: 600; font-size: 11px;")
        list_layout.addWidget(list_label)

        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
                font-size: 10px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {LorealStyles.COLORS['surface']};
            }}
        """)

        # Remplir la liste
        for code, template in ERROR_TEMPLATES.items():
            self.templates_list.addItem(f"{template.title} ({template.severity.value})")

        self.templates_list.currentRowChanged.connect(self.on_template_selected)
        list_layout.addWidget(self.templates_list)

        content_layout.addWidget(list_container)

        # Éditeur de template (droite)
        editor_container = QWidget()
        editor_layout = QVBoxLayout()
        editor_container.setLayout(editor_layout)

        editor_label = QLabel("✏️ Détails du template:")
        editor_label.setStyleSheet("font-weight: 600; font-size: 11px;")
        editor_layout.addWidget(editor_label)

        # Champs d'édition
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: 1px solid {LorealStyles.COLORS['border']}; border-radius: 4px;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)

        # Titre
        scroll_layout.addWidget(QLabel("Titre:"))
        self.template_title_edit = QLineEdit()
        self.template_title_edit.setReadOnly(True)
        scroll_layout.addWidget(self.template_title_edit)

        # Message template
        scroll_layout.addWidget(QLabel("Message template:"))
        self.template_message_edit = QTextEdit()
        self.template_message_edit.setMaximumHeight(80)
        scroll_layout.addWidget(self.template_message_edit)

        # Suggestions
        scroll_layout.addWidget(QLabel("Suggestions (une par ligne):"))
        self.template_suggestions_edit = QTextEdit()
        self.template_suggestions_edit.setMaximumHeight(100)
        scroll_layout.addWidget(self.template_suggestions_edit)

        # Réponses rapides
        scroll_layout.addWidget(QLabel("Réponses rapides (une par ligne):"))
        self.template_quick_responses_edit = QTextEdit()
        self.template_quick_responses_edit.setMaximumHeight(100)
        scroll_layout.addWidget(self.template_quick_responses_edit)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        editor_layout.addWidget(scroll)

        # Boutons d'action
        buttons_layout = QHBoxLayout()

        save_template_btn = QPushButton("💾 Sauvegarder les modifications")
        save_template_btn.clicked.connect(self.save_current_template)
        save_template_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {LorealStyles.COLORS['primary_dark']};
            }}
        """)

        reset_template_btn = QPushButton("🔄 Réinitialiser")
        reset_template_btn.clicked.connect(self.reset_current_template)

        buttons_layout.addWidget(save_template_btn)
        buttons_layout.addWidget(reset_template_btn)
        buttons_layout.addStretch()

        editor_layout.addLayout(buttons_layout)

        content_layout.addWidget(editor_container, 1)

        main_layout.addLayout(content_layout)

        return tab

    def create_general_tab(self):
        """Crée l'onglet de paramètres généraux (futur)"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("⚙️ Paramètres Généraux")
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {LorealStyles.COLORS['primary']};")
        layout.addWidget(title)

        placeholder = QLabel("Cette section contiendra les paramètres généraux de l'application :\n\n"
                           "• Préférences d'affichage\n"
                           "• Options de validation par défaut\n"
                           "• Chemins de sauvegarde\n"
                           "• Intégrations externes\n"
                           "• Etc.")
        placeholder.setStyleSheet("color: #999; font-style: italic; margin-top: 20px;")
        layout.addWidget(placeholder)

        layout.addStretch()

        return tab

    def on_template_selected(self, index):
        """Gère la sélection d'un template dans la liste"""
        if index < 0:
            return

        template_codes = list(ERROR_TEMPLATES.keys())
        if index >= len(template_codes):
            return

        code = template_codes[index]
        template = ERROR_TEMPLATES[code]

        # Remplir les champs
        self.template_title_edit.setText(template.title)
        self.template_message_edit.setText(template.template)
        self.template_suggestions_edit.setText("\n".join(template.suggestions))
        self.template_quick_responses_edit.setText("\n".join(template.quick_responses))

        # Stocker le code actuel
        self.current_template_code = code

    def save_current_template(self):
        """Sauvegarde les modifications du template actuel"""
        if not hasattr(self, 'current_template_code'):
            return

        code = self.current_template_code

        # Récupérer les modifications
        new_message = self.template_message_edit.toPlainText()
        new_suggestions = [s.strip() for s in self.template_suggestions_edit.toPlainText().split('\n') if s.strip()]
        new_quick_responses = [r.strip() for r in self.template_quick_responses_edit.toPlainText().split('\n') if r.strip()]

        # Stocker temporairement (dans la vraie version, on sauvegarderait dans un fichier JSON)
        self.modified_templates[code] = {
            'template': new_message,
            'suggestions': new_suggestions,
            'quick_responses': new_quick_responses
        }

        QMessageBox.information(
            self,
            "Succès",
            f"Template '{ERROR_TEMPLATES[code].title}' modifié avec succès!\n\n"
            "Note: Les modifications seront appliquées à la prochaine utilisation."
        )

        self.templates_updated.emit()

    def reset_current_template(self):
        """Réinitialise le template actuel aux valeurs par défaut"""
        if not hasattr(self, 'current_template_code'):
            return

        reply = QMessageBox.question(
            self,
            "Confirmer la réinitialisation",
            "Êtes-vous sûr de vouloir réinitialiser ce template aux valeurs par défaut?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Recharger les valeurs par défaut
            self.on_template_selected(self.templates_list.currentRow())

            # Supprimer les modifications stockées
            if self.current_template_code in self.modified_templates:
                del self.modified_templates[self.current_template_code]

            QMessageBox.information(self, "Succès", "Template réinitialisé aux valeurs par défaut!")

    def refresh_session_info(self):
        """Rafraîchit les informations de session affichées"""
        # Cette méthode peut être appelée pour rafraîchir les données
        # On pourrait recréer l'onglet session ici si nécessaire
        pass

    def on_layout_config_changed(self, config):
        """Appelé quand la configuration du layout change"""
        # Propager le signal au parent (main_window) si nécessaire
        # Pour l'instant, la config est déjà sauvegardée par LayoutConfigManager
        from ..core.layout_config import LayoutConfig
        logger = __import__('logging').getLogger(__name__)
        logger.info(f"Configuration layout '{config.name}' appliquée")
