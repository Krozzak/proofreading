# ui/validation_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                           QTextEdit, QGroupBox, QListWidget, QTabWidget, QFrame, QLineEdit,
                           QCheckBox, QComboBox, QScrollArea, QLayout, QWidgetItem)
from PyQt6.QtCore import pyqtSignal, Qt, QRect, QSize, QPoint
from PyQt6.QtGui import QIcon
from ..utils.styles import LorealStyles


class FlowLayout(QLayout):
    """Layout personnalisé qui arrange les widgets en lignes avec wrap automatique"""

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins().left()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            widget = item.widget()
            if widget is None:
                continue

            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x

            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

class ValidationPanel(QWidget):
    litho_validated = pyqtSignal(str, str, str)
    rejected_litho_selected = pyqtSignal(str)
    pending_litho_selected = pyqtSignal(str)
    validated_litho_selected = pyqtSignal(str)
    next_requested = pyqtSignal()
    status_changed = pyqtSignal()  # Signal pour notifier les changements de statut

    def __init__(self, session_manager=None):
        super().__init__()
        self.session_manager = session_manager
        self.current_litho_code = None
        
        # Données pour le filtrage
        self.all_pending_lithos = []
        self.all_rejected_lithos = []
        self.all_validated_lithos = []
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # 8px grid
        layout.setSpacing(12)  # 8px grid: 12px between major sections

        # 🔝 SECTION VALIDATION (toujours visible)
        validation_section = self.create_validation_section()
        layout.addWidget(validation_section)

        # 🔍 SEARCH BAR GLOBALE
        global_search_section = self.create_global_search_section()
        layout.addWidget(global_search_section)
        
        # 📋 ONGLETS DES LISTES
        self.tab_widget = QTabWidget()
        self.tab_widget.setMaximumHeight(260)
        
        # Onglet En attente
        pending_tab = self.create_pending_tab()
        self.tab_widget.addTab(pending_tab, "📝 En attente")
        
        # Onglet À revoir
        review_tab = self.create_review_tab()
        self.tab_widget.addTab(review_tab, "🔄 À revoir")
        
        # Onglet Validées
        validated_tab = self.create_validated_tab()
        self.tab_widget.addTab(validated_tab, "✅ Validées")
        
        layout.addWidget(self.tab_widget)

        # 🚀 SECTION INTÉGRATION BASECAMP
        basecamp_section = self.create_basecamp_section()
        layout.addWidget(basecamp_section)

        layout.addStretch()

    def create_global_search_section(self):
        """Crée la section de recherche simplifiée (sans titre)"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 2px;
            }}
        """)

        layout = QVBoxLayout()
        frame.setLayout(layout)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Search bar compacte (sans titre)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(4)

        # Icône de recherche
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 12px; color: #666;")

        # Champ de recherche principal
        self.global_search_edit = QLineEdit()
        self.global_search_edit.setPlaceholderText("Rechercher un code litho...")
        self.global_search_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 8px;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 10px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border: 2px solid {LorealStyles.COLORS['primary']};
                padding: 5px 7px;
            }}
        """)

        # Bouton clear compact
        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(20, 20)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                color: #999;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {LorealStyles.COLORS['error']};
            }}
        """)
        clear_btn.clicked.connect(self._clear_global_search)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.global_search_edit)
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # Label de résultats compact
        self.search_results_label = QLabel("")
        self.search_results_label.setStyleSheet(f"font-size: 8px; color: {LorealStyles.COLORS['text_secondary']}; font-style: italic;")
        layout.addWidget(self.search_results_label)

        # Connexion du signal
        self.global_search_edit.textChanged.connect(self._global_search)
        self.global_search_edit.returnPressed.connect(self._global_search_enter)

        return frame

    def create_validation_section(self):
        """Crée la section de validation (toujours visible)"""
        group = QGroupBox("📋 Validation")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 11px;
                color: {LorealStyles.COLORS['primary']};
                border: 2px solid {LorealStyles.COLORS['primary']};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background-color: white;
            }}
        """)
        
        layout = QVBoxLayout()
        group.setLayout(layout)
        layout.setContentsMargins(8, 8, 8, 8)  # 8px grid margins
        layout.setSpacing(8)  # 8px grid spacing

        # Header ultra-compact avec toutes les infos litho
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Code litho + Type + Status en une ligne
        self.litho_status_label = QLabel("📄 Litho: - | Status: En attente")
        self.litho_status_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #2B2B2B;")

        info_layout.addWidget(self.litho_status_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Résumé de validation détaillé (utilisé pour afficher les stats, pas de texte par défaut)
        self.validation_summary_label = QLabel("")
        self.validation_summary_label.setStyleSheet("""
            font-size: 9px;
            color: #666;
            padding: 2px;
            margin-bottom: 2px;
        """)
        self.validation_summary_label.setWordWrap(True)
        layout.addWidget(self.validation_summary_label)

        # Zone de commentaire
        comment_label = QLabel("💬 Commentaire:")
        comment_label.setStyleSheet("font-size: 10px; font-weight: 600; margin-top: 4px;")
        layout.addWidget(comment_label)

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Ajouter un commentaire de validation...")
        self.comment_edit.setMaximumHeight(38)  # Hauteur réduite
        self.comment_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
                font-size: 10px;
                background-color: white;
            }}
            QTextEdit:focus {{
                border: 2px solid {LorealStyles.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.comment_edit)

        # Section Réponses Rapides (sous le commentaire, en wrap)
        quick_responses_label = QLabel("⚡ Suggestions:")
        quick_responses_label.setStyleSheet("font-size: 9px; font-weight: 600; color: #666; margin-top: 2px;")
        layout.addWidget(quick_responses_label)

        # Conteneur avec FlowLayout pour wrap automatique des boutons
        self.quick_responses_widget = QWidget()
        self.quick_responses_layout = FlowLayout(spacing=4)  # 8px grid: 4px spacing
        self.quick_responses_widget.setLayout(self.quick_responses_layout)
        self.quick_responses_widget.setMaximumHeight(40)  # Réduit (top 3 only)
        self.quick_responses_widget.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.quick_responses_widget)

        # Initialiser avec des réponses par défaut
        self._init_default_quick_responses()

        # Boutons de validation principaux
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)  # 8px grid spacing
        
        self.approve_btn = QPushButton("✅ Approuver")
        self.approve_btn.setObjectName("approveButton")
        self.approve_btn.setMinimumHeight(28)  # Hauteur réduite
        
        self.reject_btn = QPushButton("❌ Refuser")
        self.reject_btn.setObjectName("rejectButton")
        self.reject_btn.setMinimumHeight(28)  # Hauteur réduite
        
        buttons_layout.addWidget(self.approve_btn)
        buttons_layout.addWidget(self.reject_btn)
        layout.addLayout(buttons_layout)  # ✅ AJOUTER AU LAYOUT PRINCIPAL

        # Connexion des signaux
        self.approve_btn.clicked.connect(lambda: self._validate('approved'))
        self.reject_btn.clicked.connect(lambda: self._validate('rejected'))

        return group

    def _global_search(self, search_text):
        """Recherche globale dans tous les onglets"""
        search_text = search_text.strip().upper()
        
        if not search_text:
            self.search_results_label.setText("")
            return
        
        # Rechercher dans toutes les listes
        found_in = []
        
        # Recherche dans les lithos en attente
        for litho in self.all_pending_lithos:
            if search_text in litho.upper():
                found_in.append(("📝 En attente", 0, litho))
        
        # Recherche dans les lithos à revoir
        for litho in self.all_rejected_lithos:
            if search_text in litho.upper():
                found_in.append(("🔄 À revoir", 1, litho))
        
        # Recherche dans les lithos validées
        for litho in self.all_validated_lithos:
            if search_text in litho.upper():
                found_in.append(("✅ Validées", 2, litho))
        
        # Mettre à jour le label de résultats
        if found_in:
            if len(found_in) == 1:
                tab_name, tab_index, litho_code = found_in[0]
                self.search_results_label.setText(f"Trouvé dans: {tab_name} • Appuyez sur Entrée pour ouvrir")
            else:
                tab_names = list(set([item[0] for item in found_in]))
                self.search_results_label.setText(f"{len(found_in)} résultats dans: {', '.join(tab_names)}")
        else:
            self.search_results_label.setText("Aucun résultat trouvé")

    def _global_search_enter(self):
        """Action lors de l'appui sur Entrée dans la recherche globale"""
        search_text = self.global_search_edit.text().strip().upper()
        
        if not search_text:
            return
        
        # Trouver la première correspondance exacte ou partielle
        target_litho = None
        target_tab_index = None
        
        # Ordre de priorité: En attente, À revoir, Validées
        search_order = [
            (self.all_pending_lithos, 0, self.pending_list, "📝"),
            (self.all_rejected_lithos, 1, self.rejected_list, "🔄"),
            (self.all_validated_lithos, 2, self.validated_list, "✅")
        ]
        
        for litho_list, tab_index, list_widget, icon in search_order:
            for litho in litho_list:
                if search_text in litho.upper():
                    target_litho = litho
                    target_tab_index = tab_index
                    target_list_widget = list_widget
                    target_icon = icon
                    break
            if target_litho:
                break
        
        if target_litho and target_tab_index is not None:
            # Changer d'onglet
            self.tab_widget.setCurrentIndex(target_tab_index)
            
            # Sélectionner l'item dans la liste
            for i in range(target_list_widget.count()):
                item = target_list_widget.item(i)
                if item.text() == f"{target_icon} {target_litho}":
                    target_list_widget.setCurrentItem(item)
                    target_list_widget.scrollToItem(item)
                    break
            
            # Émettre le signal approprié
            if target_tab_index == 0:  # En attente
                self.pending_litho_selected.emit(target_litho)
            elif target_tab_index == 1:  # À revoir
                self.rejected_litho_selected.emit(target_litho)
            elif target_tab_index == 2:  # Validées
                self.validated_litho_selected.emit(target_litho)

    def _clear_global_search(self):
        """Vide la recherche globale"""
        self.global_search_edit.clear()
        self.search_results_label.setText("")

    def create_search_bar(self, placeholder_text="Rechercher un code litho..."):
        """Crée une barre de recherche locale pour les onglets"""
        search_frame = QFrame()
        search_layout = QHBoxLayout()
        search_frame.setLayout(search_layout)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)
        
        # Icône de recherche
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 10px; color: #999;")
        
        # Champ de recherche local (plus petit)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText(placeholder_text)
        search_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 4px 6px;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 3px;
                font-size: 9px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border: 1px solid {LorealStyles.COLORS['primary']};
            }}
        """)
        
        # Bouton clear (plus petit)
        clear_btn = QPushButton("✕")
        clear_btn.setMaximumSize(16, 16)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: transparent;
                color: #999;
                font-size: 8px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {LorealStyles.COLORS['error']};
                color: white;
            }}
        """)
        clear_btn.clicked.connect(search_edit.clear)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(search_edit)
        search_layout.addWidget(clear_btn)
        
        return search_frame, search_edit

    def create_pending_tab(self):
        """Onglet dédié aux lithos en attente"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # En-tête avec compteur
        header_layout = QHBoxLayout()
        
        pending_title = QLabel("En attente de validation")
        pending_title.setStyleSheet("font-size: 10px; font-weight: 600; color: #2B2B2B;")
        
        self.pending_count_label = QLabel("(0)")
        self.pending_count_label.setStyleSheet(f"font-size: 9px; color: {LorealStyles.COLORS['text_secondary']};")
        
        header_layout.addWidget(pending_title)
        header_layout.addWidget(self.pending_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Barre de recherche locale retirée - utiliser la recherche globale à la place
        # Créer un dummy search edit pour compatibilité avec le code existant
        self.pending_search_edit = QLineEdit()
        self.pending_search_edit.hide()  # Masqué mais existe pour le code legacy
        
        # Liste des lithos en attente
        self.pending_list = QListWidget()
        self.pending_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {LorealStyles.COLORS['background']};
                border: 1px solid {LorealStyles.COLORS['border']};
                font-size: 10px;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
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
        layout.addWidget(self.pending_list)

        # Instruction
        instruction = QLabel("💡 Double-cliquez pour sélectionner")
        instruction.setStyleSheet(f"font-size: 8px; color: {LorealStyles.COLORS['text_secondary']}; font-style: italic;")
        layout.addWidget(instruction)

        # Connexion du signal
        self.pending_list.itemDoubleClicked.connect(self._on_pending_litho_selected)

        return tab

    def create_review_tab(self):
        """Onglet dédié aux lithos à revoir"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # En-tête avec compteur
        header_layout = QHBoxLayout()
        
        review_title = QLabel("À revoir")
        review_title.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {LorealStyles.COLORS['error']};")
        
        self.review_count_label = QLabel("(0)")
        self.review_count_label.setStyleSheet(f"font-size: 9px; color: {LorealStyles.COLORS['text_secondary']};")
        
        header_layout.addWidget(review_title)
        header_layout.addWidget(self.review_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Barre de recherche locale retirée - utiliser la recherche globale
        self.review_search_edit = QLineEdit()
        self.review_search_edit.hide()
        
        # Liste des lithos rejetées
        self.rejected_list = QListWidget()
        self.rejected_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #fff5f5;
                border: 1px solid {LorealStyles.COLORS['error']};
                font-size: 10px;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
                margin: 1px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {LorealStyles.COLORS['error']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: #fee;
                border: 1px solid {LorealStyles.COLORS['error']};
            }}
        """)
        layout.addWidget(self.rejected_list)

        # Instruction
        instruction = QLabel("💡 Double-cliquez pour réexaminer")
        instruction.setStyleSheet(f"font-size: 8px; color: {LorealStyles.COLORS['text_secondary']}; font-style: italic;")
        layout.addWidget(instruction)

        # Connexion du signal
        self.rejected_list.itemDoubleClicked.connect(self._on_rejected_litho_selected)

        return tab

    def create_validated_tab(self):
        """Onglet dédié aux lithos validées"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # En-tête avec compteur
        header_layout = QHBoxLayout()
        
        validated_title = QLabel("Validées")
        validated_title.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {LorealStyles.COLORS['success']};")
        
        self.validated_count_label = QLabel("(0)")
        self.validated_count_label.setStyleSheet(f"font-size: 9px; color: {LorealStyles.COLORS['text_secondary']};")
        
        header_layout.addWidget(validated_title)
        header_layout.addWidget(self.validated_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Barre de recherche locale retirée - utiliser la recherche globale
        self.validated_search_edit = QLineEdit()
        self.validated_search_edit.hide()
        
        # Liste des lithos validées
        self.validated_list = QListWidget()
        self.validated_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #f0fff4;
                border: 1px solid {LorealStyles.COLORS['success']};
                font-size: 10px;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
                margin: 1px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {LorealStyles.COLORS['success']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: #e8f5e8;
                border: 1px solid {LorealStyles.COLORS['success']};
            }}
        """)
        layout.addWidget(self.validated_list)

        # Instruction
        instruction = QLabel("💡 Double-cliquez pour consulter")
        instruction.setStyleSheet(f"font-size: 8px; color: {LorealStyles.COLORS['text_secondary']}; font-style: italic;")
        layout.addWidget(instruction)

        # Connexion du signal
        self.validated_list.itemDoubleClicked.connect(self._on_validated_litho_selected)

        return tab

    # [Le reste des méthodes reste identique...]
    
    def _filter_pending_list(self, search_text):
        """Filtre la liste des lithos en attente"""
        self.pending_list.clear()
        search_text = search_text.lower().strip()
        
        filtered_lithos = []
        for litho in self.all_pending_lithos:
            if not search_text or search_text in litho.lower():
                filtered_lithos.append(litho)
                self.pending_list.addItem(f"📝 {litho}")
        
        if search_text:
            self.pending_count_label.setText(f"({len(filtered_lithos)}/{len(self.all_pending_lithos)})")
        else:
            self.pending_count_label.setText(f"({len(self.all_pending_lithos)})")

    def _filter_review_list(self, search_text):
        """Filtre la liste des lithos à revoir"""
        self.rejected_list.clear()
        search_text = search_text.lower().strip()
        
        filtered_lithos = []
        for litho in self.all_rejected_lithos:
            if not search_text or search_text in litho.lower():
                filtered_lithos.append(litho)
                self.rejected_list.addItem(f"🔄 {litho}")
        
        if search_text:
            self.review_count_label.setText(f"({len(filtered_lithos)}/{len(self.all_rejected_lithos)})")
        else:
            self.review_count_label.setText(f"({len(self.all_rejected_lithos)})")

    def _filter_validated_list(self, search_text):
        """Filtre la liste des lithos validées"""
        self.validated_list.clear()
        search_text = search_text.lower().strip()
        
        filtered_lithos = []
        for litho in self.all_validated_lithos:
            if not search_text or search_text in litho.lower():
                filtered_lithos.append(litho)
                self.validated_list.addItem(f"✅ {litho}")
        
        if search_text:
            self.validated_count_label.setText(f"({len(filtered_lithos)}/{len(self.all_validated_lithos)})")
        else:
            self.validated_count_label.setText(f"({len(self.all_validated_lithos)})")

    def _validate(self, status):
        """Gère la validation d'une litho"""
        if not self.current_litho_code:
            return

        comment = self.comment_edit.toPlainText()
        self.litho_validated.emit(self.current_litho_code, status, comment)
        self.comment_edit.clear()

        if status == 'approved':
            self.litho_status_label.setText(f"📄 Litho: {self.current_litho_code} ({getattr(self, 'current_litho_type', '📋 Standard')}) | ✅ Status: Approuvée")
            self.litho_status_label.setStyleSheet(f"color: {LorealStyles.COLORS['success']}; font-weight: 600; font-size: 10px;")
            self.next_requested.emit()
        else:
            self.litho_status_label.setText(f"📄 Litho: {self.current_litho_code} ({getattr(self, 'current_litho_type', '📋 Standard')}) | ❌ Status: Refusée")
            self.litho_status_label.setStyleSheet(f"color: {LorealStyles.COLORS['error']}; font-weight: 600; font-size: 10px;")

        # Émettre le signal de changement de statut
        self.status_changed.emit()
        self.update_lists()

    def _on_rejected_litho_selected(self, item):
        if item is not None:
            litho_code = item.text().replace("🔄 ", "")
            self.rejected_litho_selected.emit(litho_code)

    def _on_pending_litho_selected(self, item):
        if item is not None:
            litho_code = item.text().replace("📝 ", "")
            self.pending_litho_selected.emit(litho_code)

    def _on_validated_litho_selected(self, item):
        if item is not None:
            litho_code = item.text().replace("✅ ", "")
            self.validated_litho_selected.emit(litho_code)

    def update_lists(self):
        if self.session_manager:
            self.all_rejected_lithos = self.session_manager.get_rejected_lithos()
            self.all_validated_lithos = self.session_manager.get_approved_lithos()
            
            all_lithos = set(self.session_manager.get_all_lithos())
            validated_lithos = set(self.all_validated_lithos + self.all_rejected_lithos)
            self.all_pending_lithos = sorted(list(all_lithos - validated_lithos))
            
            self._filter_pending_list(self.pending_search_edit.text())
            self._filter_review_list(self.review_search_edit.text())
            self._filter_validated_list(self.validated_search_edit.text())

    def set_current_litho(self, litho_code, litho_type="📋 Standard"):
        self.current_litho_code = litho_code
        self.current_litho_type = litho_type
        self.litho_status_label.setText(f"📄 Litho: {litho_code} ({litho_type}) | Status: En attente")
        self.validation_summary_label.setText("")  # Vide par défaut, sera rempli par update_validation_summary

        if self.session_manager and litho_code:
            status_info = self.session_manager.get_litho_status(litho_code)
            self.update_status(status_info)
        else:
            self.update_status(None)

    def clear(self):
        self.current_litho_code = None
        self.current_litho_type = "📋 Standard"
        self.litho_status_label.setText("📄 Litho: - | Status: En attente")
        self.litho_status_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #2B2B2B;")
        self.validation_summary_label.setText("")
        self.comment_edit.clear()
        self.approve_btn.setEnabled(False)
        self.reject_btn.setEnabled(False)
        
        # Clear toutes les recherches
        self.global_search_edit.clear()
        self.pending_search_edit.clear()
        self.review_search_edit.clear()
        self.validated_search_edit.clear()
        self.search_results_label.setText("")
        
        # Clear toutes les listes
        self.pending_list.clear()
        self.rejected_list.clear()
        self.validated_list.clear()
        
        # Réinitialiser les données et compteurs
        self.all_pending_lithos = []
        self.all_rejected_lithos = []
        self.all_validated_lithos = []
        self.pending_count_label.setText("(0)")
        self.review_count_label.setText("(0)")
        self.validated_count_label.setText("(0)")
        
    def update_status(self, status_info):
        if status_info:
            if status_info['status'] == 'approved':
                self.litho_status_label.setText(f"📄 Litho: {self.current_litho_code} ({getattr(self, 'current_litho_type', '📋 Standard')}) | ✅ Status: Approuvée")
                self.litho_status_label.setStyleSheet(f"color: {LorealStyles.COLORS['success']}; font-weight: 600; font-size: 10px;")
            else:
                self.litho_status_label.setText(f"📄 Litho: {self.current_litho_code} ({getattr(self, 'current_litho_type', '📋 Standard')}) | ❌ Status: Refusée")
                self.litho_status_label.setStyleSheet(f"color: {LorealStyles.COLORS['error']}; font-weight: 600; font-size: 10px;")
            
            if status_info.get('comment'):
                self.comment_edit.setText(status_info['comment'])
            else:
                self.comment_edit.clear()
            
            self.approve_btn.setEnabled(status_info['status'] != 'approved')
            self.reject_btn.setEnabled(status_info['status'] != 'rejected')
            
        else:
            self.litho_status_label.setText(f"📄 Litho: {self.current_litho_code} ({getattr(self, 'current_litho_type', '📋 Standard')}) | ⏳ Status: En attente")
            self.litho_status_label.setStyleSheet("font-size: 10px; font-weight: 600; color: #2B2B2B;")
            self.comment_edit.clear()
            self.approve_btn.setEnabled(True)
            self.reject_btn.setEnabled(True)
        
        self.update_lists()
        
    def create_basecamp_section(self):
        """Crée la section d'intégration BaseCamp"""
        group = QGroupBox("🚀 Intégration BaseCamp")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 11px;
                color: {LorealStyles.COLORS['primary']};
                border: 2px solid {LorealStyles.COLORS['primary']};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background-color: white;
            }}
        """)

        layout = QVBoxLayout()
        group.setLayout(layout)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Description
        desc_label = QLabel("Ajouter automatiquement les commentaires d'approbation sur BaseCamp")
        desc_label.setStyleSheet("font-size: 10px; color: #666; margin-bottom: 4px;")
        layout.addWidget(desc_label)

        # Bouton BaseCamp
        self.basecamp_btn = QPushButton("🚀 BaseCamp Approver")
        self.basecamp_btn.setObjectName("basecampButton")
        self.basecamp_btn.setMinimumHeight(32)
        self.basecamp_btn.clicked.connect(self.open_basecamp_dialog)
        self.basecamp_btn.setToolTip("Ajouter automatiquement les commentaires d'approbation sur Basecamp")
        self.basecamp_btn.setEnabled(False)
        layout.addWidget(self.basecamp_btn)

        # Statut des fichiers approuvés
        self.basecamp_status = QLabel("⏳ Aucun fichier approuvé")
        self.basecamp_status.setStyleSheet("""
            font-size: 9px;
            color: #666;
            padding: 2px;
            text-align: center;
        """)
        self.basecamp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.basecamp_status)

        return group

    def update_basecamp_status(self, approved_lithos):
        """Met à jour le statut de l'intégration Basecamp"""
        if not approved_lithos:
            self.basecamp_status.setText("⏳ Aucun fichier approuvé")
            self.basecamp_btn.setEnabled(False)
        else:
            self.basecamp_status.setText(f"✅ {len(approved_lithos)} fichier(s) prêt(s)")
            self.basecamp_btn.setEnabled(True)

        # Mettre à jour le tooltip avec les détails
        if approved_lithos:
            lithos_list = ", ".join(approved_lithos)
            tooltip_text = f"Fichiers prêts pour BaseCamp:\n{lithos_list}"
        else:
            tooltip_text = "Aucun fichier approuvé pour l'intégration BaseCamp"

        self.basecamp_btn.setToolTip(tooltip_text)

    def update_validation_summary(self, summary_text, style_class=""):
        """Met à jour le résumé de validation détaillé"""
        self.validation_summary_label.setText(summary_text)
        if style_class:
            self.validation_summary_label.setStyleSheet(f"""
                font-size: 9px;
                color: #666;
                padding: 2px;
                margin-bottom: 2px;
                {style_class}
            """)

    def open_basecamp_dialog(self):
        """Ouvre le dialog Basecamp"""
        from .basecamp_dialog import BasecampProgressDialog

        dialog = BasecampProgressDialog(self.session_manager, self)
        dialog.exec()

    def _init_default_quick_responses(self):
        """Initialise les boutons de réponses rapides par défaut (top 3 seulement)"""
        default_responses = [
            "✅ Conforme",
            "❌ Nom de teinte incorrect",
            "⚠️ Mixed facings",
        ]

        for response in default_responses:
            self._add_quick_response_button(response)

    def _add_quick_response_button(self, text: str):
        """Ajoute un bouton de réponse rapide style bulle"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 12px;
                padding: 4px 10px;
                text-align: center;
                font-size: 8px;
                color: #333;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {LorealStyles.COLORS['primary']};
                border: 1px solid {LorealStyles.COLORS['primary']};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {LorealStyles.COLORS['primary_dark']};
                color: white;
            }}
        """)
        btn.clicked.connect(lambda: self._on_quick_response_clicked(text))
        self.quick_responses_layout.addWidget(btn)

    def _on_quick_response_clicked(self, response_text: str):
        """Gère le clic sur un bouton de réponse rapide"""
        # Remplir le commentaire avec la réponse
        current_comment = self.comment_edit.toPlainText().strip()

        if current_comment:
            # Ajouter à la suite si un commentaire existe déjà
            self.comment_edit.setPlainText(f"{current_comment}\n{response_text}")
        else:
            # Remplacer si vide
            self.comment_edit.setPlainText(response_text)

        # Mettre le focus sur le commentaire
        self.comment_edit.setFocus()

    def update_quick_responses(self, validation_results=None, excel_data=None):
        """
        Met à jour les boutons de réponses rapides avec des suggestions intelligentes
        basées sur les erreurs détectées dans le tableau

        Args:
            validation_results: Résultats de validation
            excel_data: Données Excel correspondantes
        """
        # Clear les boutons existants
        while self.quick_responses_layout.count() > 0:
            item = self.quick_responses_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        suggested_responses = []

        # Si aucune donnée, afficher les réponses par défaut
        if not validation_results or not excel_data:
            self._init_default_quick_responses()
            return

        # Analyser les erreurs pour générer des suggestions précises
        errors_found = False
        for idx, (validation, data) in enumerate(zip(validation_results, excel_data)):
            # Ignorer FRAME et SPACE_SAVER
            if validation.get('is_frame') or validation.get('is_space_saver'):
                continue

            upc = self._safe_str(data.get('UPC', ''))
            row_num = idx + 1

            # Erreur de shade name
            if not validation.get('shade_name', True):
                expected = self._safe_str(data.get('SHADE NAME', ''))
                if expected:
                    suggested_responses.append(f"❌ Shade Name UPC {upc[-4:]}: '{expected}'")
                    errors_found = True

            # Erreur de shade number
            if not validation.get('shade_number', True):
                expected = self._safe_str(data.get('SHADE NUMBER', ''))
                if expected:
                    suggested_responses.append(f"❌ Shade # UPC {upc[-4:]}: '{expected}'")
                    errors_found = True

            # Erreur 4 DIGITS
            if not validation.get('digits', True):
                expected = self._safe_str(data.get('4 DIGITS', ''))
                if expected:
                    suggested_responses.append(f"❌ 4 DIGITS UPC {upc[-4:]}: '{expected}'")
                    errors_found = True

        # Si des erreurs spécifiques trouvées, les ajouter (top 3 seulement)
        if errors_found:
            # Limiter à 3 suggestions maximum (modern UI - less clutter)
            for response in suggested_responses[:3]:
                self._add_quick_response_button(response)
        else:
            # Aucune erreur = validation réussie (3 options max)
            self._add_quick_response_button("✅ Validation réussie - Conforme")
            self._add_quick_response_button("⚠️ OK avec réserves")
            self._add_quick_response_button("📞 Questions mineures")

    def _safe_str(self, value) -> str:
        """Convertit de manière sécurisée une valeur en string"""
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            if float(value).is_integer():
                return str(int(value))
            return str(value)
        return str(value).strip()