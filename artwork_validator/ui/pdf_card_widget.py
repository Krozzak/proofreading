"""
Widget de carte PDF pour la vue en grille.
Affiche une litho sous forme de carte avec thumbnail large et actions rapides.
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QWidget, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont


class PDFCardWidget(QFrame):
    """
    Carte représentant une litho avec:
    - Grand thumbnail du PDF
    - Code YCA
    - Description courte
    - Statut visuel (validé/en cours/rejeté)
    - Quick actions au hover
    """

    # Signaux
    card_clicked = pyqtSignal(str)  # Émis quand on clique sur la carte (code YCA)
    validate_clicked = pyqtSignal(str)  # Approuver
    reject_clicked = pyqtSignal(str)  # Rejeter

    def __init__(self, yca_code, description, pixmap=None, status="pending",
                 row_count=0, compact_mode=False, parent=None):
        super().__init__(parent)
        self.yca_code = yca_code
        self.description = description
        self.status = status  # "approved", "rejected", "pending"
        self.row_count = row_count
        self.compact_mode = compact_mode
        self.pixmap = pixmap

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface de la carte"""
        self.setObjectName("PDFCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Taille de la carte selon le mode
        if self.compact_mode:
            card_width, card_height = 200, 280
            thumb_width, thumb_height = 180, 240
        else:
            card_width, card_height = 280, 400
            thumb_width, thumb_height = 260, 350

        self.setFixedSize(card_width, card_height)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # === Thumbnail ===
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(thumb_width, thumb_height)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

        if self.pixmap:
            scaled_pixmap = self.pixmap.scaled(
                thumb_width, thumb_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            self.thumbnail_label.setText("📄")

        layout.addWidget(self.thumbnail_label)

        # === Badge de statut (coin supérieur droit du thumbnail) ===
        self.status_badge = QLabel(self.thumbnail_label)
        self.status_badge.setFixedSize(24, 24)
        self.status_badge.move(thumb_width - 30, 6)
        self.update_status_badge()

        # === Informations ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Code YCA
        self.code_label = QLabel(self.yca_code)
        self.code_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #000;
            }
        """)
        info_layout.addWidget(self.code_label)

        # Description
        desc_text = self.description if len(self.description) <= 40 else self.description[:37] + "..."
        self.desc_label = QLabel(desc_text)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
            }
        """)
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)

        # Nombre de lignes Excel
        if self.row_count > 0:
            self.count_label = QLabel(f"📊 {self.row_count} ligne{'s' if self.row_count > 1 else ''}")
            self.count_label.setStyleSheet("""
                QLabel {
                    font-size: 10px;
                    color: #999;
                }
            """)
            info_layout.addWidget(self.count_label)

        layout.addLayout(info_layout)

        # === Actions rapides (cachées par défaut, visibles au hover) ===
        self.actions_widget = QWidget(self)
        self.actions_widget.setFixedSize(card_width - 24, 50)
        self.actions_widget.move(12, card_height - 62)
        self.actions_widget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.85);
                border-radius: 6px;
            }
        """)
        self.actions_widget.hide()

        actions_layout = QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        # Bouton Approuver
        self.approve_btn = QPushButton("✓")
        self.approve_btn.setFixedSize(40, 32)
        self.approve_btn.setToolTip("Approuver (Ctrl+Enter)")
        self.approve_btn.clicked.connect(lambda: self.validate_clicked.emit(self.yca_code))
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)
        actions_layout.addWidget(self.approve_btn)

        # Bouton Rejeter
        self.reject_btn = QPushButton("✗")
        self.reject_btn.setFixedSize(40, 32)
        self.reject_btn.setToolTip("Rejeter (Ctrl+R)")
        self.reject_btn.clicked.connect(lambda: self.reject_clicked.emit(self.yca_code))
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        actions_layout.addWidget(self.reject_btn)

        actions_layout.addStretch()

        # Bouton Voir détails
        self.view_btn = QPushButton("Voir")
        self.view_btn.setFixedSize(60, 32)
        self.view_btn.setToolTip("Voir les détails")
        self.view_btn.clicked.connect(lambda: self.card_clicked.emit(self.yca_code))
        self.view_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        actions_layout.addWidget(self.view_btn)

        # Style de la carte selon le statut
        self.update_card_style()

        # Ajoute effet d'ombre
        self.setup_shadow_effect()

    def update_status_badge(self):
        """Met à jour le badge de statut"""
        badges = {
            "approved": ("✓", "#28a745", "#fff"),
            "rejected": ("✗", "#dc3545", "#fff"),
            "pending": ("⋯", "#ffc107", "#000"),
        }

        icon, bg_color, text_color = badges.get(self.status, ("?", "#6c757d", "#fff"))

        self.status_badge.setText(icon)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {text_color};
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)

    def update_card_style(self):
        """Met à jour le style de la carte selon le statut"""
        border_colors = {
            "approved": "#28a745",
            "rejected": "#dc3545",
            "pending": "#ddd",
        }

        border_color = border_colors.get(self.status, "#ddd")

        self.setStyleSheet(f"""
            #PDFCard {{
                background: white;
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #PDFCard:hover {{
                border-color: #007bff;
            }}
        """)

    def setup_shadow_effect(self):
        """Ajoute un effet d'ombre subtile à la carte"""
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 35))  # Noir à 35% opacité
        self.shadow.setOffset(0, 3)
        self.setGraphicsEffect(self.shadow)

    def enterEvent(self, event):
        """Affiche les actions au survol + augmente l'ombre"""
        self.actions_widget.show()
        # Augmente l'ombre au survol
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(0, 0, 0, 60))  # Plus foncé
        self.shadow.setOffset(0, 6)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Cache les actions quand la souris sort + restaure l'ombre"""
        self.actions_widget.hide()
        # Restaure l'ombre normale
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 35))
        self.shadow.setOffset(0, 3)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Gère le clic sur la carte"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Si on clique sur la carte (mais pas sur un bouton)
            if not self.actions_widget.underMouse():
                self.card_clicked.emit(self.yca_code)
        super().mousePressEvent(event)

    def set_status(self, new_status):
        """Change le statut de la carte"""
        self.status = new_status
        self.update_status_badge()
        self.update_card_style()

    def set_compact_mode(self, compact):
        """Bascule entre mode compact et large"""
        self.compact_mode = compact
        # Reconstruire l'UI avec les nouvelles dimensions
        # Pour simplifier, on peut juste recréer la carte
        self.setup_ui()
