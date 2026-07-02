"""
Vue en grille de cartes PDF.
Affiche toutes les lithos sous forme de cartes avec filtres et recherche.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                              QLabel, QPushButton, QLineEdit, QComboBox,
                              QFrame, QButtonGroup, QRadioButton, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap

from .pdf_card_widget import PDFCardWidget


class CardsView(QWidget):
    """
    Vue affichant les lithos en grille de cartes.

    Features:
    - Grille responsive avec scroll
    - Filtres par statut
    - Recherche par code YCA ou description
    - Mode compact/large
    - Quick actions sur les cartes
    """

    # Signaux
    validation_requested = pyqtSignal(str)  # Code YCA à valider
    card_approved = pyqtSignal(str)  # Code YCA approuvé
    card_rejected = pyqtSignal(str)  # Code YCA rejeté

    def __init__(self, session_manager, pdf_processor, excel_processor, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.pdf_processor = pdf_processor
        self.excel_processor = excel_processor

        self.cards = []  # Liste des widgets de cartes
        self.lithos_data = []  # Données brutes
        self.current_filter = "all"  # all, approved, rejected, pending
        self.compact_mode = False

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # === En-tête ===
        header_layout = QHBoxLayout()

        # Titre
        title = QLabel("📚 Bibliothèque de Lithos")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #000;
            }
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Bouton Mode compact/large
        self.mode_toggle_btn = QPushButton("🔲 Compact")
        self.mode_toggle_btn.setFixedSize(120, 36)
        self.mode_toggle_btn.setCheckable(True)
        self.mode_toggle_btn.clicked.connect(self.toggle_compact_mode)
        self.mode_toggle_btn.setStyleSheet("""
            QPushButton {
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
                padding: 8px 12px;
            }
            QPushButton:checked {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
            QPushButton:checked:hover {
                background: #0056b3;
            }
        """)
        header_layout.addWidget(self.mode_toggle_btn)

        layout.addLayout(header_layout)

        # === Barre de recherche et filtres ===
        filters_layout = QHBoxLayout()

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher par code YCA ou description...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        filters_layout.addWidget(self.search_input, stretch=3)

        # Filtre par statut
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "✓ Approuvés", "✗ Rejetés", "⋯ En cours"])
        self.status_filter.setFixedHeight(40)
        self.status_filter.currentIndexChanged.connect(self.on_filter_changed)
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 10px;
            }
        """)
        filters_layout.addWidget(self.status_filter, stretch=1)

        layout.addLayout(filters_layout)

        # === Statistiques rapides ===
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 8px 0;
            }
        """)
        layout.addWidget(self.stats_label)

        # === Zone de scroll avec grille ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Conteneur de la grille
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area.setWidget(self.grid_container)
        layout.addWidget(scroll_area)

        # Debounce timer pour la recherche
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_filters)

    def load_lithos(self):
        """Charge toutes les lithos depuis les données"""
        self.lithos_data = []

        if not self.pdf_processor or not self.pdf_processor.pdf_files:
            return

        # Construire les données
        for pdf_file in self.pdf_processor.pdf_files:
            # Extraire le code YCA du nom de fichier (commence par YCA...)
            yca_code = pdf_file.split('_')[0] if '_' in pdf_file else pdf_file.replace('.pdf', '')
            if not yca_code or not yca_code.startswith('YCA'):
                continue

            # Récupérer les données Excel
            excel_data = self.excel_processor.get_data_for_litho(yca_code)
            description = excel_data[0].get('DESCRIPTION', 'Sans description') if excel_data else 'Sans description'
            row_count = len(excel_data)

            # Récupérer le statut depuis la session
            status = "pending"
            if self.session_manager:
                if yca_code in self.session_manager.current_session.get('validations', {}):
                    litho_status = self.session_manager.get_litho_status(yca_code)
                    status = litho_status.get('status', 'pending')

            # Récupérer le thumbnail
            pixmap = self.pdf_processor.get_thumbnail(pdf_file, size=(260, 350))

            self.lithos_data.append({
                'yca_code': yca_code,
                'pdf_file': pdf_file,
                'description': description,
                'row_count': row_count,
                'status': status,
                'pixmap': pixmap
            })

        # Afficher toutes les cartes
        self.apply_filters()

    def apply_filters(self):
        """Applique les filtres de recherche et statut"""
        # Effacer les cartes existantes
        self.clear_grid()

        # Récupérer les critères de filtrage
        search_text = self.search_input.text().lower().strip()
        filter_index = self.status_filter.currentIndex()
        status_map = {0: "all", 1: "approved", 2: "rejected", 3: "pending"}
        status_filter = status_map.get(filter_index, "all")

        # Filtrer les données
        filtered_data = []
        for litho in self.lithos_data:
            # Filtre par statut
            if status_filter != "all" and litho['status'] != status_filter:
                continue

            # Filtre par recherche
            if search_text:
                if search_text not in litho['yca_code'].lower() and \
                   search_text not in litho['description'].lower():
                    continue

            filtered_data.append(litho)

        # Mettre à jour les statistiques
        self.update_stats(len(filtered_data), len(self.lithos_data))

        # Afficher les cartes filtrées
        self.display_cards(filtered_data)

    def display_cards(self, lithos):
        """Affiche les cartes dans la grille"""
        # Calculer le nombre de colonnes selon la largeur et le mode
        card_width = 220 if self.compact_mode else 300
        container_width = self.grid_container.width() if self.grid_container.width() > 0 else 1200
        cols = max(1, (container_width - 20) // (card_width + 20))

        row, col = 0, 0

        for litho in lithos:
            card = PDFCardWidget(
                yca_code=litho['yca_code'],
                description=litho['description'],
                pixmap=litho['pixmap'],
                status=litho['status'],
                row_count=litho['row_count'],
                compact_mode=self.compact_mode
            )

            # Connecter les signaux
            card.card_clicked.connect(self.on_card_clicked)
            card.validate_clicked.connect(self.on_card_approved)
            card.reject_clicked.connect(self.on_card_rejected)

            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def clear_grid(self):
        """Efface toutes les cartes de la grille"""
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

    def update_stats(self, filtered_count, total_count):
        """Met à jour les statistiques affichées"""
        if filtered_count == total_count:
            self.stats_label.setText(f"📊 {total_count} litho{'s' if total_count > 1 else ''}")
        else:
            self.stats_label.setText(
                f"📊 {filtered_count} sur {total_count} litho{'s' if total_count > 1 else ''}"
            )

    def on_search_changed(self):
        """Déclenche la recherche avec debounce"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms de délai

    def on_filter_changed(self):
        """Filtre changé"""
        self.apply_filters()

    def toggle_compact_mode(self):
        """Bascule entre mode compact et large"""
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.mode_toggle_btn.setText("🔳 Large")
        else:
            self.mode_toggle_btn.setText("🔲 Compact")

        # Recharger les cartes avec le nouveau mode
        self.apply_filters()

    def on_card_clicked(self, yca_code):
        """Une carte a été cliquée - ouvrir la validation"""
        self.validation_requested.emit(yca_code)

    def on_card_approved(self, yca_code):
        """Approuver rapidement depuis la carte"""
        self.card_approved.emit(yca_code)
        # Mettre à jour le statut de la carte
        self.update_card_status(yca_code, "approved")

    def on_card_rejected(self, yca_code):
        """Rejeter rapidement depuis la carte"""
        self.card_rejected.emit(yca_code)
        # Mettre à jour le statut de la carte
        self.update_card_status(yca_code, "rejected")

    def update_card_status(self, yca_code, new_status):
        """Met à jour le statut d'une carte spécifique"""
        # Mettre à jour dans les données
        for litho in self.lithos_data:
            if litho['yca_code'] == yca_code:
                litho['status'] = new_status
                break

        # Mettre à jour la carte affichée
        for card in self.cards:
            if card.yca_code == yca_code:
                card.set_status(new_status)
                break

    def refresh(self):
        """Rafraîchit la vue"""
        self.load_lithos()
