# utils/styles.py
class LorealStyles:
    # Couleurs L'Oréal Canada (inchangées)
    COLORS = {
        'primary': '#E53E3E',      # Rouge L'Oréal signature
        'primary_dark': '#C53030',  # Rouge foncé
        'secondary': '#2B2B2B',     # Gris anthracite
        'secondary_light': '#4A5568', # Gris moyen
        'background': '#F7FAFC',    # Gris très clair
        'surface': '#FFFFFF',       # Blanc
        'accent': '#3182CE',        # Bleu accent
        'success': '#38A169',       # Vert
        'warning': '#D69E2E',       # Orange
        'error': '#E53E3E',         # Rouge erreur
        'text_primary': '#1A202C',  # Texte principal
        'text_secondary': '#4A5568', # Texte secondaire
        'border': '#E2E8F0'         # Bordures
    }

    # 8px Grid Spacing System (Modern UI - Phase 1.3)
    # Use these values for consistent spacing throughout the app
    SPACING = {
        'micro': 4,      # 4px - Tight elements
        'small': 8,      # 8px - Related elements
        'medium': 12,    # 12px - Between cards in list
        'large': 16,     # 16px - Major sections
        'xlarge': 24,    # 24px - Page-level spacing
        'xxlarge': 32    # 32px - Very large gaps
    }

    # Shadow Effects (Modern UI - Phase 1.3)
    # Note: Use QGraphicsDropShadowEffect in PyQt6, not CSS box-shadow
    # Example:
    #   shadow = QGraphicsDropShadowEffect()
    #   shadow.setBlurRadius(SHADOWS['default']['blur'])
    #   shadow.setColor(QColor(0, 0, 0, SHADOWS['default']['opacity']))
    #   shadow.setOffset(0, SHADOWS['default']['offset'])
    SHADOWS = {
        'subtle': {'blur': 10, 'opacity': 25, 'offset': 2},   # Cards at rest
        'default': {'blur': 15, 'opacity': 35, 'offset': 3},  # Default elevation
        'elevated': {'blur': 20, 'opacity': 50, 'offset': 4}, # Hover state
        'floating': {'blur': 25, 'opacity': 60, 'offset': 6}  # Modal/dialog
    }
    
    @staticmethod
    def get_main_stylesheet():
        return f"""
        /* Style principal de l'application - TEXTE PLUS GRAND */
        QMainWindow {{
            background-color: {LorealStyles.COLORS['background']};
            color: {LorealStyles.COLORS['text_primary']};
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-size: 11px;  /* 🔧 Augmenté de 9px à 11px */
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {LorealStyles.COLORS['secondary']};
            color: white;
            border: none;
            padding: 4px;
            font-size: 11px;  /* 🔧 Augmenté */
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 1px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {LorealStyles.COLORS['primary']};
        }}
        
        QMenu {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 6px;
            padding: 4px;
            font-size: 11px;  /* 🔧 Augmenté */
        }}
        
        QMenu::item {{
            padding: 6px 12px;
            border-radius: 3px;
        }}
        
        QMenu::item:selected {{
            background-color: {LorealStyles.COLORS['primary']};
            color: white;
        }}
        
        /* Groupes et panneaux */
        QGroupBox {{
            font-weight: 600;
            font-size: 12px;  /* 🔧 Augmenté de 10px à 12px */
            color: {LorealStyles.COLORS['text_primary']};
            border: 2px solid {LorealStyles.COLORS['border']};
            border-radius: 6px;
            margin-top: 6px;
            padding-top: 6px;
            background-color: {LorealStyles.COLORS['surface']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 6px 0 6px;
            background-color: {LorealStyles.COLORS['surface']};
        }}
        
        /* Boutons - Modern UI (Phase 1.3) */
        QPushButton {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 2px solid {LorealStyles.COLORS['border']};
            border-radius: 6px;  /* 🔧 Augmenté de 4px à 6px (modern) */
            padding: 8px 16px;  /* 🔧 Augmenté le padding horizontal */
            font-weight: 500;
            font-size: 11px;
            color: {LorealStyles.COLORS['text_primary']};
            min-height: 32px;  /* 🔧 Augmenté de 24px à 32px (better touch target) */
        }}

        QPushButton:hover {{
            background-color: {LorealStyles.COLORS['primary']};
            border-color: {LorealStyles.COLORS['primary']};
            color: white;
            /* Note: Shadow effect added via QGraphicsDropShadowEffect in code */
        }}

        QPushButton:pressed {{
            background-color: {LorealStyles.COLORS['primary_dark']};
            transform: scale(0.98);  /* Subtle press feedback */
        }}

        QPushButton:disabled {{
            background-color: {LorealStyles.COLORS['border']};
            color: {LorealStyles.COLORS['text_secondary']};
            border-color: {LorealStyles.COLORS['border']};
            opacity: 0.6;
        }}
        
        /* Boutons spéciaux */
        QPushButton#primaryButton {{
            background-color: {LorealStyles.COLORS['primary']};
            color: white;
            border-color: {LorealStyles.COLORS['primary']};
        }}
        
        QPushButton#primaryButton:hover {{
            background-color: {LorealStyles.COLORS['primary_dark']};
        }}
        
        QPushButton#navigationButton {{
            min-width: 70px;  /* 🔧 Augmenté de 60px à 70px */
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
        }}
        
        QPushButton#approveButton {{
            background-color: {LorealStyles.COLORS['success']};
            color: white;
            border-color: {LorealStyles.COLORS['success']};
        }}
        
        QPushButton#rejectButton {{
            background-color: {LorealStyles.COLORS['error']};
            color: white;
            border-color: {LorealStyles.COLORS['error']};
        }}
        
        QPushButton[objectName="basecampButton"] {{
            background-color: #FF6B35;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 11px;
        }}

        QPushButton[objectName="basecampButton"]:hover {{
            background-color: #E55A2B;
        }}

        QPushButton[objectName="basecampButton"]:pressed {{
            background-color: #CC4A1F;
        }}
        
        /* CheckBox */
        QCheckBox {{
            font-size: 11px;  /* 🔧 Augmenté de 9px à 11px */
            color: {LorealStyles.COLORS['text_primary']};
            spacing: 6px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;  /* 🔧 Augmenté de 14px à 16px */
            height: 16px;  /* 🔧 Augmenté de 14px à 16px */
            border-radius: 2px;
            border: 2px solid {LorealStyles.COLORS['border']};
            background-color: {LorealStyles.COLORS['surface']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {LorealStyles.COLORS['primary']};
            border-color: {LorealStyles.COLORS['primary']};
        }}
        
        /* Progress Bar */
        QProgressBar {{
            border: 2px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            text-align: center;
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
            background-color: {LorealStyles.COLORS['surface']};
            height: 18px;  /* 🔧 Augmenté de 16px à 18px */
        }}
        
        QProgressBar::chunk {{
            background-color: {LorealStyles.COLORS['primary']};
            border-radius: 2px;
        }}
        
        /* Labels */
        QLabel {{
            color: {LorealStyles.COLORS['text_primary']};
            font-size: 11px;  /* 🔧 Augmenté de 9px à 11px */
        }}
        
        /* Liste et tableaux */
        QListWidget {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
            padding: 2px;
        }}
        
        QListWidget::item {{
            padding: 6px;  /* 🔧 Augmenté de 4px à 6px */
            border-radius: 3px;
            margin: 1px;
        }}
        
        QListWidget::item:selected {{
            background-color: {LorealStyles.COLORS['primary']};
            color: white;
        }}
        
        QTableWidget {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
            gridline-color: {LorealStyles.COLORS['border']};
        }}
        
        QHeaderView::section {{
            background-color: {LorealStyles.COLORS['secondary']};
            color: white;
            padding: 6px;  /* 🔧 Augmenté de 4px à 6px */
            border: none;
            font-weight: 600;
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
        }}
        
        /* TextEdit */
        QTextEdit {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 2px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            padding: 8px;  /* 🔧 Augmenté de 6px à 8px */
            font-size: 11px;  /* 🔧 Augmenté de 9px à 11px */
        }}
        
        QTextEdit:focus {{
            border-color: {LorealStyles.COLORS['primary']};
        }}
        
        /* Scroll Area */
        QScrollArea {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {LorealStyles.COLORS['border']};
            width: 2px;
            height: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {LorealStyles.COLORS['primary']};
        }}
        
        /* Onglets - styles améliorés */
        QTabWidget::pane {{
            border: 1px solid {LorealStyles.COLORS['border']};
            border-radius: 4px;
            margin-top: 2px;
        }}
        
        QTabBar::tab {{
            background-color: {LorealStyles.COLORS['surface']};
            border: 1px solid {LorealStyles.COLORS['border']};
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 6px 12px;  /* 🔧 Augmenté le padding */
            margin-right: 1px;
            font-size: 10px;  /* 🔧 Augmenté de 8px à 10px */
            font-weight: 500;
            min-width: 60px;  /* 🔧 Largeur minimale */
        }}
        
        QTabBar::tab:selected {{
            background-color: {LorealStyles.COLORS['primary']};
            color: white;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {LorealStyles.COLORS['background']};
        }}
        """