# ui/litho_row_card.py
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QWidget, QProgressBar, QApplication,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QCursor, QColor
from ..utils.styles import LorealStyles


class LithoRowCard(QFrame):
    """
    Card compacte pour une litho dans la overview list
    Click → ouvre validation détaillée
    """

    clicked = pyqtSignal(str)  # litho_code

    def __init__(self, litho_data, parent=None):
        super().__init__(parent)
        self.litho_code = litho_data['code']
        self.data = litho_data
        self.setup_ui(litho_data)
        self.setup_styles()
        self.setup_shadow_effect()

    def setup_ui(self, data):
        """
        Layout horizontal:
        [Icon Status] [Thumbnail] [Info Block] [Metrics] [Actions]
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)  # Augmenté pour plus d'espace
        layout.setSpacing(20)  # Augmenté de 12 à 20 pour meilleure répartition

        # 1. Status Icon (40px)
        self.status_icon = self.create_status_badge(data.get('status', 'pending'))
        layout.addWidget(self.status_icon)

        # 2. Thumbnail (60x80px)
        self.thumbnail = self.create_thumbnail(data.get('thumbnail'))
        layout.addWidget(self.thumbnail)

        # 3. Info Block (expand)
        info_block = self.create_info_block(data)
        layout.addWidget(info_block, stretch=1)

        # 4. Metrics (150px)
        metrics = self.create_metrics(data)
        layout.addWidget(metrics)

        # 5. Quick Actions (80px)
        actions = self.create_actions()
        layout.addWidget(actions)

        # Hover effect
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def create_status_badge(self, status):
        """Badge circulaire moderne avec icône et ombre"""
        badge = QLabel()
        badge.setFixedSize(48, 48)  # Augmenté de 40 à 48px

        icons = {
            'approved': '✅',
            'rejected': '❌',
            'pending': '⏳'
        }
        colors = {
            'approved': LorealStyles.COLORS['success'],
            'rejected': LorealStyles.COLORS['error'],
            'pending': LorealStyles.COLORS['warning']
        }

        badge.setText(icons.get(status, '⏳'))
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {colors.get(status, '#999')};
                border-radius: 24px;
                font-size: 22px;
                qproperty-alignment: AlignCenter;
            }}
        """)

        # Ajoute une ombre subtile au badge
        badge_shadow = QGraphicsDropShadowEffect()
        badge_shadow.setBlurRadius(8)
        badge_shadow.setColor(QColor(0, 0, 0, 40))
        badge_shadow.setOffset(0, 2)
        badge.setGraphicsEffect(badge_shadow)

        return badge

    def create_thumbnail(self, pixmap):
        """Thumbnail du PDF"""
        thumb = QLabel()
        thumb.setFixedSize(80, 120)  # Augmenté pour meilleure lisibilité
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 4px; background: white;")

        if pixmap:
            # Conserver le ratio d'aspect
            scaled_pixmap = pixmap.scaled(
                80, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            thumb.setPixmap(scaled_pixmap)
        else:
            # Skeleton placeholder
            thumb.setStyleSheet("""
                background: qlineargradient(
                    x1:0, x2:1,
                    stop:0 #e0e0e0,
                    stop:0.5 #f0f0f0,
                    stop:1 #e0e0e0
                );
                border-radius: 4px;
            """)
        return thumb

    def create_info_block(self, data):
        """Bloc principal avec code, description, commentaire"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Ligne 1: Code + Type badge
        header_layout = QHBoxLayout()

        code_label = QLabel(f"<b>{data['code']}</b>")
        code_label.setStyleSheet("font-size: 16px; color: #1a1a1a; font-weight: 700;")  # Augmenté 14→16px
        header_layout.addWidget(code_label)

        if data.get('type'):
            type_badge = QLabel(data['type'])
            type_badge.setStyleSheet(f"""
                background: {LorealStyles.COLORS['accent']};
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 9px;
                font-weight: bold;
            """)
            header_layout.addWidget(type_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Ligne 2: Description (si CUBBY ou info importante)
        if data.get('description'):
            desc_label = QLabel(data['description'])
            desc_label.setStyleSheet("font-size: 12px; color: #666;")  # Augmenté 11→12px
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Ligne 3: Commentaire
        comment_text = data.get('comment', '(Aucun commentaire)')
        comment_label = QLabel(f"💬 {comment_text}")
        comment_label.setStyleSheet("""
            font-size: 12px;
            color: #888;
            font-style: italic;
        """)  # Augmenté 11→12px
        comment_label.setWordWrap(True)
        layout.addWidget(comment_label)

        # Ligne 4: Metadata (user, date)
        meta_text = ""
        if data.get('status') != 'pending':
            action = "Validé" if data.get('status') == 'approved' else "Rejeté"
            meta_text = f"👤 {action} le {data.get('timestamp', 'N/A')}"
        else:
            meta_text = "🕐 En attente de validation"

        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("font-size: 11px; color: #999;")  # Augmenté 10→11px
        layout.addWidget(meta_label)

        layout.addStretch()
        return container

    def create_metrics(self, data):
        """Métriques de validation compactes"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Items count
        items_label = QLabel(f"📦 {data.get('items_count', 0)} items")
        items_label.setStyleSheet("font-size: 11px; font-weight: 600;")
        layout.addWidget(items_label)

        # Validation percentage
        validation_pct = data.get('validation_percentage', 0)
        pct_label = QLabel(f"✓ {validation_pct}%")

        color = LorealStyles.COLORS['success'] if validation_pct >= 95 else \
                LorealStyles.COLORS['warning'] if validation_pct >= 80 else \
                LorealStyles.COLORS['error']

        pct_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(pct_label)

        # Progress bar mini
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setValue(int(validation_pct))
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background: #e0e0e0;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress)

        layout.addStretch()
        return container

    def create_actions(self):
        """Boutons d'action rapide"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Bouton principal: Valider/Voir
        main_btn = QPushButton("🔍 Valider")
        main_btn.setObjectName("primaryButton")
        main_btn.setFixedHeight(32)
        main_btn.clicked.connect(lambda: self.clicked.emit(self.litho_code))
        layout.addWidget(main_btn)

        # Bouton secondaire: Copier code
        copy_btn = QPushButton("📋")
        copy_btn.setToolTip("📋 Copier le code litho dans le presse-papier")
        copy_btn.setFixedSize(36, 28)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f5f5f5;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #e8e8e8;
                border-color: {LorealStyles.COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: #d8d8d8;
            }}
        """)
        copy_btn.clicked.connect(self.copy_code)
        layout.addWidget(copy_btn)

        layout.addStretch()
        return container

    def copy_code(self):
        """Copie le code litho dans le presse-papier"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.litho_code)

    def mousePressEvent(self, event):
        """Click sur la card entière → ouvre validation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.litho_code)
        super().mousePressEvent(event)

    def setup_styles(self):
        """Styles de base de la card"""
        self.setStyleSheet(f"""
            LithoRowCard {{
                background: white;
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 8px;
            }}
        """)

    def setup_shadow_effect(self):
        """Ajoute un effet d'ombre subtile à la carte"""
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(12)
        self.shadow.setColor(QColor(0, 0, 0, 30))  # Noir à 30% opacité
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)

    def enterEvent(self, event):
        """Hover effect - augmente l'ombre et change la bordure"""
        self.setStyleSheet(f"""
            LithoRowCard {{
                background: {LorealStyles.COLORS['background']};
                border: 2px solid {LorealStyles.COLORS['primary']};
                border-radius: 8px;
            }}
        """)
        # Augmente l'ombre au survol
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 50))  # Plus foncé
        self.shadow.setOffset(0, 4)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset hover - ombre subtile"""
        self.setup_styles()
        # Restaure l'ombre normale
        self.shadow.setBlurRadius(12)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 2)
        super().leaveEvent(event)
