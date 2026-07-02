# ui/overview_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QLineEdit, QComboBox,
                             QPushButton, QStackedWidget, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from ..utils.styles import LorealStyles
from .litho_row_card import LithoRowCard
from .pdf_card_widget import PDFCardWidget


class OverviewView(QWidget):
    """
    Vue d'ensemble de toutes les lithos avec toggle Liste/Grille
    Fusionne les anciennes vues Overview et Cards
    """

    validation_requested = pyqtSignal(str)  # litho_code à valider
    view_mode_changed = pyqtSignal(str)  # 'list' ou 'grid'

    def __init__(self, session_manager, pdf_processor, excel_processor, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.pdf_processor = pdf_processor
        self.excel_processor = excel_processor
        self.litho_cards = []  # Cards pour la vue liste
        self.grid_cards = []  # Cards pour la vue grille
        self.all_litho_data = []  # Stocker toutes les données pour filtrage
        self.current_view_mode = 'list'  # 'list' ou 'grid'
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)  # 8px grid: 16px margins
        layout.setSpacing(16)  # 8px grid: 16px spacing between major sections

        # Header avec statistiques globales
        header = self.create_header()
        layout.addWidget(header)

        # Section statistiques détaillées (comme dans validation)
        stats_section = self.create_detailed_stats_section()
        layout.addWidget(stats_section)

        # Toolbar (filters, sort, search) + Toggle view mode
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Toggle Liste/Grille
        toggle_bar = self.create_view_toggle()
        layout.addWidget(toggle_bar)

        # Stacked widget pour switcher entre liste et grille
        self.views_stack = QStackedWidget()
        layout.addWidget(self.views_stack)

        # Vue Liste (existante)
        self.list_view = self.create_list_view()
        self.views_stack.addWidget(self.list_view)

        # Vue Grille
        self.grid_view = self.create_grid_view()
        self.views_stack.addWidget(self.grid_view)

        # Démarrer en mode liste
        self.views_stack.setCurrentWidget(self.list_view)

    def create_view_toggle(self):
        """Barre de toggle Liste/Grille"""
        toggle_frame = QFrame()
        toggle_frame.setFixedHeight(45)
        toggle_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(toggle_frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Label
        label = QLabel("Mode d'affichage:")
        label.setStyleSheet("font-weight: 600; font-size: 12px; color: #666;")
        layout.addWidget(label)

        # Bouton Liste
        self.list_btn = QPushButton("📋 Liste")
        self.list_btn.setCheckable(True)
        self.list_btn.setChecked(True)
        self.list_btn.setFixedHeight(32)
        self.list_btn.clicked.connect(lambda: self.switch_view_mode('list'))
        layout.addWidget(self.list_btn)

        # Bouton Grille
        self.grid_btn = QPushButton("🎴 Grille")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setFixedHeight(32)
        self.grid_btn.clicked.connect(lambda: self.switch_view_mode('grid'))
        layout.addWidget(self.grid_btn)

        # Style des boutons toggle
        toggle_style = f"""
            QPushButton {{
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px 16px;
                background: white;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:checked {{
                background: {LorealStyles.COLORS['primary']};
                color: white;
                border-color: {LorealStyles.COLORS['primary']};
            }}
            QPushButton:hover:!checked {{
                background: {LorealStyles.COLORS['background']};
            }}
        """
        self.list_btn.setStyleSheet(toggle_style)
        self.grid_btn.setStyleSheet(toggle_style)

        layout.addStretch()

        return toggle_frame

    def create_list_view(self):
        """Crée la vue liste (scroll area avec LithoRowCard)"""
        # Scroll area avec liste
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {LorealStyles.COLORS['background']};
            }}
        """)

        # Container pour les cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)  # 8px grid: 12px between cards
        self.cards_layout.setContentsMargins(8, 8, 8, 8)  # 8px padding

        scroll.setWidget(self.cards_container)
        return scroll

    def create_grid_view(self):
        """Crée la vue grille (scroll area avec PDFCardWidget en grille)"""
        # Scroll area avec grille
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {LorealStyles.COLORS['background']};
            }}
        """)

        # Container pour la grille
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(24)  # 8px grid: 24px between cards in grid
        self.grid_layout.setContentsMargins(8, 8, 8, 8)  # 8px padding
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_container)
        return scroll

    def switch_view_mode(self, mode):
        """Switch entre mode liste et grille"""
        if mode == self.current_view_mode:
            return

        self.current_view_mode = mode

        # Update button states
        self.list_btn.setChecked(mode == 'list')
        self.grid_btn.setChecked(mode == 'grid')

        # Switch stacked widget
        if mode == 'list':
            self.views_stack.setCurrentWidget(self.list_view)
        elif mode == 'grid':
            self.views_stack.setCurrentWidget(self.grid_view)

        # 🆕 Réafficher les cards dans le nouveau mode
        self.sort_and_display_cards()

        # Emit signal
        self.view_mode_changed.emit(mode)

    def create_header(self):
        """Header avec stats globales façon dashboard"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {LorealStyles.COLORS['primary']},
                    stop:1 {LorealStyles.COLORS['primary_dark']});
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)

        # Titre
        title = QLabel("📊 VUE D'ENSEMBLE")
        title.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Stats boxes (seront mis à jour dynamiquement)
        self.total_box = self.create_stat_box("📄 Total", "0", "white")
        layout.addWidget(self.total_box)

        self.validated_box = self.create_stat_box("✅ Validées", "0", "#4ade80")
        layout.addWidget(self.validated_box)

        self.rejected_box = self.create_stat_box("❌ Rejetées", "0", "#f87171")
        layout.addWidget(self.rejected_box)

        self.pending_box = self.create_stat_box("⏳ En attente", "0", "#fbbf24")
        layout.addWidget(self.pending_box)

        return header

    def create_stat_box(self, label, value, color):
        """Mini stat box"""
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 8px 16px;
            }
        """)

        layout = QVBoxLayout(box)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: bold;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(label)
        desc_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 10px;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(desc_label)

        # Stocker référence pour mise à jour
        box.value_label = value_label

        return box

    def create_detailed_stats_section(self):
        """Section des statistiques détaillées style validation"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        stats_layout = QHBoxLayout()
        stats_frame.setLayout(stats_layout)
        stats_layout.setContentsMargins(12, 8, 12, 8)
        stats_layout.setSpacing(12)

        # Groupe 1: Progression
        progress_group = QHBoxLayout()
        progress_group.setSpacing(8)

        self.detail_total_pdfs = self.create_labeled_stat("📄", "0", "Total")
        self.detail_progress_pct = self.create_labeled_stat("📊", "0%", "Traitement")
        self.detail_validation_pct = self.create_labeled_stat("✔️", "0%", "Validation")

        progress_group.addWidget(self.detail_total_pdfs)
        progress_group.addWidget(self.create_stat_separator())
        progress_group.addWidget(self.detail_progress_pct)
        progress_group.addWidget(self.create_stat_separator())
        progress_group.addWidget(self.detail_validation_pct)

        # Groupe 2: Statuts
        status_group = QHBoxLayout()
        status_group.setSpacing(8)

        self.detail_validated = self.create_labeled_stat("✅", "0", "Validées", LorealStyles.COLORS['success'])
        self.detail_rejected = self.create_labeled_stat("❌", "0", "Rejetées", LorealStyles.COLORS['error'])
        self.detail_pending = self.create_labeled_stat("⏳", "0", "En attente", LorealStyles.COLORS['warning'])

        status_group.addWidget(self.detail_validated)
        status_group.addWidget(self.create_stat_separator())
        status_group.addWidget(self.detail_rejected)
        status_group.addWidget(self.create_stat_separator())
        status_group.addWidget(self.detail_pending)

        # Assemblage
        stats_layout.addLayout(progress_group)
        stats_layout.addWidget(self.create_main_separator())
        stats_layout.addLayout(status_group)
        stats_layout.addStretch()

        return stats_frame

    def create_labeled_stat(self, icon, value, label, color=None):
        """Crée une statistique avec icône, valeur et label"""
        container = QFrame()
        container.setStyleSheet("border: none; background: transparent;")

        layout = QHBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        # Icône
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon_label)

        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color if color else '#000'};
        """)
        layout.addWidget(value_label)

        # Label
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(text_label)

        # Stocker référence
        container.value_label = value_label

        return container

    def create_stat_separator(self):
        """Séparateur léger entre stats"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(20)
        sep.setStyleSheet(f"background-color: {LorealStyles.COLORS['border']};")
        return sep

    def create_main_separator(self):
        """Séparateur principal entre groupes"""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(30)
        sep.setFixedWidth(2)
        sep.setStyleSheet(f"background-color: {LorealStyles.COLORS['border']};")
        return sep

    def create_toolbar(self):
        """Toolbar avec filters, sort, search"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)

        # Search
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une litho...")
        self.search_input.textChanged.connect(self.filter_cards)
        layout.addWidget(self.search_input)

        # Filter combo
        filter_label = QLabel("Filtre:")
        layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Tous",
            "✅ Validées",
            "❌ Rejetées",
            "⏳ En attente"
        ])
        self.filter_combo.currentIndexChanged.connect(self.filter_cards)
        layout.addWidget(self.filter_combo)

        # Sort combo
        sort_label = QLabel("Trier par:")
        layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Statut",
            "Code (A-Z)",
            "Code (Z-A)",
            "% Validation",
            "Date"
        ])
        self.sort_combo.currentIndexChanged.connect(self.sort_and_display_cards)
        layout.addWidget(self.sort_combo)

        return toolbar

    def load_lithos(self):
        """Charge toutes les lithos et crée les cards"""
        # Clear existing
        for card in self.litho_cards:
            card.deleteLater()
        self.litho_cards.clear()
        self.all_litho_data.clear()

        # Créer cards pour chaque PDF
        for pdf_file in self.pdf_processor.pdf_files:
            litho_code = self.pdf_processor._extract_litho_code(pdf_file)

            # Agréger les données
            litho_data = self.aggregate_litho_data(litho_code, pdf_file)
            self.all_litho_data.append(litho_data)

        # Trier et afficher
        self.sort_and_display_cards()

        # Mettre à jour les stats
        self.update_stats()

    def aggregate_litho_data(self, litho_code, pdf_file):
        """Agrège toutes les données pour une litho"""
        data = {
            'code': litho_code,
            'pdf_file': pdf_file,
            'status': 'pending',
            'comment': '',
            'timestamp': '',
            'type': '',
            'description': '',
            'items_count': 0,
            'validation_percentage': 0,
            'thumbnail': None
        }

        # Status depuis session
        if litho_code in self.session_manager.current_session['validations']:
            status_info = self.session_manager.get_litho_status(litho_code)
            data['status'] = status_info['status']
            data['comment'] = status_info.get('comment', '')
            data['timestamp'] = status_info.get('timestamp', '')

        # Excel data pour metrics
        if self.excel_processor.data is not None:
            excel_data = self.excel_processor.get_data_for_litho(litho_code)
            if excel_data:
                data['items_count'] = len(excel_data)

                # Calcul du pourcentage de validation
                # On compte les lignes avec SHADE NAME et SHADE NUMBER non-vides
                valid_count = 0
                for item in excel_data:
                    shade_name = item.get('SHADE NAME')
                    shade_number = item.get('SHADE NUMBER')
                    # Vérifier que les valeurs existent et ne sont pas NaN
                    has_name = shade_name and str(shade_name).strip() and str(shade_name) != 'nan'
                    has_number = shade_number and str(shade_number).strip() and str(shade_number) != 'nan'
                    if has_name and has_number:
                        valid_count += 1

                data['validation_percentage'] = int((valid_count / len(excel_data)) * 100) if len(excel_data) > 0 else 0

        # 🆕 Thumbnail en lazy loading : ne pas charger maintenant, charger à l'affichage
        # Cache du pdf_processor gérera les requêtes répétées
        data['thumbnail'] = None

        return data

    def sort_and_display_cards(self):
        """Trie les données et affiche les cards selon le mode actuel"""
        # Trier les données
        sort_by = self.sort_combo.currentText()
        sorted_data = self.all_litho_data.copy()

        if sort_by == "Statut":
            # Ordre: pending, approved, rejected
            status_order = {'pending': 0, 'approved': 1, 'rejected': 2}
            sorted_data.sort(key=lambda x: status_order.get(x['status'], 3))
        elif sort_by == "Code (A-Z)":
            sorted_data.sort(key=lambda x: x['code'])
        elif sort_by == "Code (Z-A)":
            sorted_data.sort(key=lambda x: x['code'], reverse=True)
        elif sort_by == "% Validation":
            sorted_data.sort(key=lambda x: x['validation_percentage'], reverse=True)
        elif sort_by == "Date":
            sorted_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # Afficher selon le mode
        if self.current_view_mode == 'list':
            self.display_list_cards(sorted_data)
        else:
            self.display_grid_cards(sorted_data)

    def display_list_cards(self, sorted_data):
        """Affiche les lithos en mode liste"""
        # Clear current cards
        for card in self.litho_cards:
            card.deleteLater()
        self.litho_cards.clear()

        # Créer et afficher cards liste
        for litho_data in sorted_data:
            # 🆕 Lazy loading: charger thumbnail seulement maintenant
            if litho_data['thumbnail'] is None:
                litho_data['thumbnail'] = self.pdf_processor.get_thumbnail(litho_data['pdf_file'])

            card = LithoRowCard(litho_data, self)
            card.clicked.connect(self.on_litho_clicked)

            self.cards_layout.addWidget(card)
            self.litho_cards.append(card)

        # Stretch final
        self.cards_layout.addStretch()

        # Appliquer les filtres
        self.filter_cards()

    def display_grid_cards(self, sorted_data):
        """Affiche les lithos en mode grille"""
        # Clear current grid cards
        for card in self.grid_cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.grid_cards.clear()

        # Calculer nombre de colonnes (responsive 2-6 colonnes)
        card_width = 300
        container_width = self.grid_container.width() if self.grid_container.width() > 0 else 1200
        cols = max(2, min(6, (container_width - 20) // (card_width + 20)))  # 🆕 Max 6 colonnes au lieu de 4

        row, col = 0, 0

        # Créer et afficher cards grille
        for litho_data in sorted_data:
            # 🆕 Lazy loading: charger thumbnail seulement maintenant
            if litho_data['thumbnail'] is None:
                litho_data['thumbnail'] = self.pdf_processor.get_thumbnail(litho_data['pdf_file'])

            card = PDFCardWidget(
                yca_code=litho_data['code'],
                description=f"{litho_data['items_count']} items" if litho_data['items_count'] > 0 else "Sans données",
                pixmap=litho_data['thumbnail'],
                status=litho_data['status'],
                row_count=litho_data['items_count'],
                compact_mode=False
            )

            # Connecter les signaux
            card.card_clicked.connect(self.on_litho_clicked)
            # Note: PDFCardWidget n'a pas de quick actions validate/reject dans son code actuel
            # On connecte juste le click pour ouvrir la validation

            self.grid_layout.addWidget(card, row, col)
            self.grid_cards.append(card)

            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Appliquer les filtres
        self.filter_cards()

    def on_litho_clicked(self, litho_code):
        """Litho cliquée → basculer vers vue validation"""
        self.validation_requested.emit(litho_code)

    def filter_cards(self):
        """Filtre les cards selon search + filter combo (liste et grille)"""
        search_text = self.search_input.text().lower()
        filter_status = self.filter_combo.currentText()

        # Filtrer liste
        for card in self.litho_cards:
            # Search match
            search_match = search_text in card.litho_code.lower() or \
                          search_text in card.data.get('comment', '').lower()

            # Filter match
            filter_match = filter_status == "Tous" or \
                          (filter_status.startswith("✅") and card.data['status'] == 'approved') or \
                          (filter_status.startswith("❌") and card.data['status'] == 'rejected') or \
                          (filter_status.startswith("⏳") and card.data['status'] == 'pending')

            card.setVisible(search_match and filter_match)

        # Filtrer grille
        for card in self.grid_cards:
            # Search match (utilise yca_code au lieu de litho_code pour PDFCardWidget)
            search_match = search_text in card.yca_code.lower()

            # Filter match
            filter_match = filter_status == "Tous" or \
                          (filter_status.startswith("✅") and card.status == 'approved') or \
                          (filter_status.startswith("❌") and card.status == 'rejected') or \
                          (filter_status.startswith("⏳") and card.status == 'pending')

            card.setVisible(search_match and filter_match)

    def update_stats(self):
        """Met à jour les statistiques dans le header et la section détaillée"""
        stats = self.get_global_stats()

        # Header boxes
        self.total_box.value_label.setText(str(stats['total']))
        self.validated_box.value_label.setText(str(stats['approved']))
        self.rejected_box.value_label.setText(str(stats['rejected']))
        self.pending_box.value_label.setText(str(stats['pending']))

        # Section détaillée
        self.detail_total_pdfs.value_label.setText(str(stats['total']))
        self.detail_validated.value_label.setText(str(stats['approved']))
        self.detail_rejected.value_label.setText(str(stats['rejected']))
        self.detail_pending.value_label.setText(str(stats['pending']))

        # Calcul des pourcentages
        if stats['total'] > 0:
            # Pourcentage de traitement = (validées + rejetées) / total
            processed = stats['approved'] + stats['rejected']
            progress_pct = int((processed / stats['total']) * 100)
            self.detail_progress_pct.value_label.setText(f"{progress_pct}%")

            # Pourcentage de validation = validées / total
            validation_pct = int((stats['approved'] / stats['total']) * 100)
            self.detail_validation_pct.value_label.setText(f"{validation_pct}%")
        else:
            self.detail_progress_pct.value_label.setText("0%")
            self.detail_validation_pct.value_label.setText("0%")

    def get_global_stats(self):
        """Calcule les statistiques globales"""
        total = len(self.all_litho_data)
        approved = sum(1 for d in self.all_litho_data if d['status'] == 'approved')
        rejected = sum(1 for d in self.all_litho_data if d['status'] == 'rejected')
        pending = total - approved - rejected

        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending
        }
