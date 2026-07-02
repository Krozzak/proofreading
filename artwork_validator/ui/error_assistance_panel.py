# ui/error_assistance_panel.py
"""
Panneau d'assistance pour afficher les erreurs détectées avec suggestions
et actions rapides pour améliorer la productivité de validation
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QGroupBox,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from ..utils.styles import LorealStyles
from ..core.error_templates import ErrorAnalyzer, ErrorSeverity


class ErrorCard(QFrame):
    """Carte individuelle affichant une erreur avec ses détails"""

    def __init__(self, error_data: dict, parent=None):
        super().__init__(parent)
        self.error_data = error_data
        self.template = error_data['template']
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface de la carte d'erreur"""
        # Style selon la sévérité
        severity_colors = {
            ErrorSeverity.CRITICAL: ('#ff4444', '#ffeeee'),
            ErrorSeverity.HIGH: ('#ff8800', '#fff5ee'),
            ErrorSeverity.MEDIUM: ('#ffcc00', '#fffaee'),
            ErrorSeverity.LOW: ('#4CAF50', '#f0fff4')
        }

        border_color, bg_color = severity_colors.get(
            self.template.severity,
            ('#cccccc', '#ffffff')
        )

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 6px;
                padding: 8px;
                margin: 4px 0;
            }}
        """)

        # Add modern shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(12, 12, 12, 12)  # 8px grid: 12px padding
        layout.setSpacing(8)  # 8px grid spacing

        # En-tête avec icône de sévérité et titre
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Icône selon sévérité
        severity_icons = {
            ErrorSeverity.CRITICAL: '🚨',
            ErrorSeverity.HIGH: '❌',
            ErrorSeverity.MEDIUM: '⚠️',
            ErrorSeverity.LOW: 'ℹ️'
        }
        icon = severity_icons.get(self.template.severity, '•')

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)

        # Titre
        title_label = QLabel(self.template.title)
        title_label.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #333;
        """)
        header_layout.addWidget(title_label)

        # Badge de sévérité
        severity_badge = QLabel(self.template.severity.value.upper())
        severity_badge.setStyleSheet(f"""
            background-color: {border_color};
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 8px;
            font-weight: bold;
        """)
        header_layout.addWidget(severity_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Message d'erreur formaté
        analyzer = ErrorAnalyzer()
        message = analyzer.format_error_message(self.error_data)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            font-size: 10px;
            color: #555;
            padding: 4px;
        """)
        layout.addWidget(message_label)

        # Suggestions (collapsible)
        if self.template.suggestions:
            suggestions_label = QLabel("💡 Suggestions:")
            suggestions_label.setStyleSheet("""
                font-size: 9px;
                font-weight: bold;
                color: #666;
                margin-top: 4px;
            """)
            layout.addWidget(suggestions_label)

            for suggestion in self.template.suggestions[:3]:  # Limiter à 3 suggestions
                suggestion_item = QLabel(f"  • {suggestion}")
                suggestion_item.setWordWrap(True)
                suggestion_item.setStyleSheet("""
                    font-size: 9px;
                    color: #666;
                    padding-left: 8px;
                """)
                layout.addWidget(suggestion_item)

        # Badge "Rejet recommandé" si applicable
        if self.template.auto_reject:
            reject_badge = QLabel("⚠️ REJET RECOMMANDÉ")
            reject_badge.setStyleSheet("""
                background-color: #ff4444;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 9px;
                font-weight: bold;
                margin-top: 4px;
            """)
            reject_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(reject_badge)


class ErrorAssistancePanel(QWidget):
    """
    Panneau d'assistance affichant les erreurs détectées avec suggestions
    et proposant des actions rapides
    """

    quick_response_selected = pyqtSignal(str)  # Signal émis quand une réponse rapide est sélectionnée

    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_analyzer = ErrorAnalyzer()
        self.current_errors = []
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface du panneau"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(8, 8, 8, 8)  # 8px grid
        layout.setSpacing(12)  # 8px grid: 12px between sections

        # En-tête
        header = self.create_header()
        layout.addWidget(header)

        # Zone scrollable pour les erreurs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                background-color: white;
            }}
        """)

        # Container pour les cartes d'erreur
        self.errors_container = QWidget()
        self.errors_layout = QVBoxLayout()
        self.errors_container.setLayout(self.errors_layout)
        self.errors_layout.setContentsMargins(8, 8, 8, 8)  # 8px grid
        self.errors_layout.setSpacing(8)  # 8px grid: 8px between error cards
        self.errors_layout.addStretch()

        scroll_area.setWidget(self.errors_container)
        layout.addWidget(scroll_area)

        # Section réponses rapides
        quick_responses_section = self.create_quick_responses_section()
        layout.addWidget(quick_responses_section)

        # Afficher le message par défaut
        self.show_no_errors_message()

    def create_header(self):
        """Crée l'en-tête du panneau"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout()
        header.setLayout(layout)
        layout.setContentsMargins(8, 6, 8, 6)

        # Titre
        title = QLabel("🔍 Assistant de Validation")
        title.setStyleSheet("""
            color: white;
            font-size: 12px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        # Résumé des erreurs
        self.summary_label = QLabel("Aucune erreur détectée")
        self.summary_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 9px;
        """)
        layout.addWidget(self.summary_label)

        return header

    def create_quick_responses_section(self):
        """Crée la section des réponses rapides"""
        group = QGroupBox("⚡ Réponses Rapides")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 10px;
                color: {LorealStyles.COLORS['primary']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                margin-top: 4px;
                padding-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                background-color: white;
            }}
        """)

        layout = QVBoxLayout()
        group.setLayout(layout)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Container pour les boutons (sera rempli dynamiquement)
        self.quick_responses_container = QWidget()
        self.quick_responses_layout = QVBoxLayout()
        self.quick_responses_container.setLayout(self.quick_responses_layout)
        self.quick_responses_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_responses_layout.setSpacing(4)

        layout.addWidget(self.quick_responses_container)

        return group

    def update_errors(self, validation_results, excel_data, check_digits=False):
        """
        Met à jour l'affichage avec les nouvelles erreurs détectées

        Args:
            validation_results: Résultats de validation
            excel_data: Données Excel
            check_digits: Si True, vérifier les 4 DIGITS
        """
        # Analyser les erreurs
        self.current_errors = self.error_analyzer.analyze_validation_results(
            validation_results,
            excel_data,
            check_digits
        )

        # Clear les anciennes cartes d'erreur
        self.clear_errors()

        if not self.current_errors:
            self.show_no_errors_message()
            self.update_summary(None)
            self.clear_quick_responses()
            return

        # Générer le résumé
        summary = self.error_analyzer.get_error_summary(self.current_errors)
        self.update_summary(summary)

        # Afficher les cartes d'erreur (limiter à 10 pour ne pas surcharger)
        for error in self.current_errors[:10]:
            card = ErrorCard(error)
            self.errors_layout.insertWidget(self.errors_layout.count() - 1, card)

        # Si plus de 10 erreurs, afficher un message
        if len(self.current_errors) > 10:
            more_label = QLabel(f"... et {len(self.current_errors) - 10} autres erreurs")
            more_label.setStyleSheet("""
                font-size: 9px;
                color: #999;
                font-style: italic;
                padding: 8px;
            """)
            more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.errors_layout.insertWidget(self.errors_layout.count() - 1, more_label)

        # Mettre à jour les réponses rapides
        self.update_quick_responses()

    def update_summary(self, summary):
        """Met à jour le résumé des erreurs dans l'en-tête"""
        if not summary:
            self.summary_label.setText("✅ Aucune erreur détectée")
            self.summary_label.setStyleSheet("""
                color: #4CAF50;
                font-size: 9px;
                font-weight: bold;
            """)
            return

        total = summary['total_errors']
        critical = summary['critical_errors']
        high = summary['high_errors']

        text = f"{total} erreur(s): "
        parts = []
        if critical > 0:
            parts.append(f"🚨 {critical} critique(s)")
        if high > 0:
            parts.append(f"❌ {high} haute(s)")

        text += ", ".join(parts) if parts else f"{total} détectée(s)"

        if summary['auto_reject_recommended']:
            text += " • ⚠️ REJET RECOMMANDÉ"

        self.summary_label.setText(text)
        self.summary_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            font-size: 9px;
            font-weight: bold;
        """)

    def update_quick_responses(self):
        """Met à jour les boutons de réponses rapides"""
        self.clear_quick_responses()

        if not self.current_errors:
            return

        # Obtenir les suggestions de réponses rapides
        suggestions = self.error_analyzer.get_quick_response_suggestions(self.current_errors)

        for response in suggestions[:5]:  # Limiter à 5 réponses rapides
            btn = QPushButton(response)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 1px solid {LorealStyles.COLORS['border']};
                    border-radius: 3px;
                    padding: 6px 8px;
                    text-align: left;
                    font-size: 9px;
                    color: #333;
                }}
                QPushButton:hover {{
                    background-color: {LorealStyles.COLORS['surface']};
                    border: 1px solid {LorealStyles.COLORS['primary']};
                }}
                QPushButton:pressed {{
                    background-color: {LorealStyles.COLORS['primary']};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, r=response: self.on_quick_response_clicked(r))
            self.quick_responses_layout.addWidget(btn)

    def on_quick_response_clicked(self, response: str):
        """Gère le clic sur un bouton de réponse rapide"""
        self.quick_response_selected.emit(response)

    def clear_errors(self):
        """Efface toutes les cartes d'erreur affichées"""
        while self.errors_layout.count() > 1:  # Garder le stretch
            item = self.errors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear_quick_responses(self):
        """Efface tous les boutons de réponses rapides"""
        while self.quick_responses_layout.count() > 0:
            item = self.quick_responses_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_no_errors_message(self):
        """Affiche un message quand aucune erreur n'est détectée"""
        self.clear_errors()

        message = QLabel("✅ Aucune erreur détectée\n\nToutes les validations sont passées avec succès!")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet(f"""
            font-size: 11px;
            color: {LorealStyles.COLORS['success']};
            padding: 20px;
            font-weight: 600;
        """)
        message.setWordWrap(True)
        self.errors_layout.insertWidget(0, message)

    def clear(self):
        """Réinitialise le panneau"""
        self.current_errors = []
        self.clear_errors()
        self.clear_quick_responses()
        self.show_no_errors_message()
        self.update_summary(None)
