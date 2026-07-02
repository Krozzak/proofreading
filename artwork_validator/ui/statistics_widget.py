# ui/statistics_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from datetime import datetime
from ..utils.styles import LorealStyles

class StatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.reset_statistics()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # En-tête moderne
        header = QFrame()
        header.setFixedHeight(30)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['secondary']};
                border-radius: 4px;
            }}
        """)
        
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        title = QLabel("📊 Statistiques")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        layout.addWidget(header)

        # Container principal avec fond
        stats_container = QFrame()
        stats_container.setStyleSheet(f"""
            QFrame {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        container_layout = QVBoxLayout()
        stats_container.setLayout(container_layout)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(3)

        # Statistiques globales en grille compacte
        global_grid = QGridLayout()
        global_grid.setSpacing(2)
        
        # Labels des statistiques globales
        self.total_pdfs_label = self.create_stat_label("PDFs totaux: 0", "📄")
        self.current_pdf_label = self.create_stat_label("PDF actuel: 0", "👁️")
        self.pdfs_validated_label = self.create_stat_label("Validés: 0", "✅", LorealStyles.COLORS['success'])
        self.pdfs_rejected_label = self.create_stat_label("Rejetés: 0", "❌", LorealStyles.COLORS['error'])
        self.pdfs_pending_label = self.create_stat_label("En attente: 0", "⏳", LorealStyles.COLORS['warning'])
        
        # Disposition en grille 2x3
        global_grid.addWidget(self.total_pdfs_label, 0, 0)
        global_grid.addWidget(self.current_pdf_label, 0, 1)
        global_grid.addWidget(self.pdfs_validated_label, 1, 0)
        global_grid.addWidget(self.pdfs_rejected_label, 1, 1)
        global_grid.addWidget(self.pdfs_pending_label, 2, 0, 1, 2)  # Span 2 colonnes
        
        container_layout.addLayout(global_grid)

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"QFrame {{ background-color: {LorealStyles.COLORS['border']}; }}")
        container_layout.addWidget(separator)

        # Informations litho courante
        current_title = QLabel("🎯 Litho courante")
        current_title.setStyleSheet("font-weight: bold; font-size: 9px;")
        container_layout.addWidget(current_title)
        
        self.litho_type_label = self.create_info_label("Type: Standard")
        self.validation_details = QLabel()
        self.validation_details.setWordWrap(True)
        self.validation_details.setStyleSheet("font-size: 7px; color: #666;")
        
        container_layout.addWidget(self.litho_type_label)
        container_layout.addWidget(self.validation_details)
        
        layout.addWidget(stats_container)
        layout.addStretch()

    def create_stat_label(self, text, icon="", color=None):
        """Crée un label de statistique avec icône"""
        label = QLabel(f"{icon} {text}")
        style = "font-size: 8px; padding: 2px;"
        if color:
            style += f" color: {color}; font-weight: 600;"
        label.setStyleSheet(style)
        return label
        
    def create_info_label(self, text):
        """Crée un label d'information"""
        label = QLabel(text)
        label.setStyleSheet("font-size: 8px; font-weight: 500;")
        return label

    def reset_statistics(self):
        """Réinitialise toutes les statistiques"""
        self.total_pdfs_label.setText("📄 PDFs totaux: 0")
        self.current_pdf_label.setText("👁️ PDF actuel: 0")
        self.pdfs_validated_label.setText("✅ Validés: 0")
        self.pdfs_rejected_label.setText("❌ Rejetés: 0")
        self.pdfs_pending_label.setText("⏳ En attente: 0")
        self.litho_type_label.setText("Type: Standard")
        self.validation_details.setText("")

    def update_statistics(self, validation_results, session_data=None, current_pdf_info=None):
        """Met à jour les statistiques avec les nouvelles données"""
        if not validation_results:
            self.reset_statistics()
            return

        # Mise à jour des statistiques globales
        if current_pdf_info:
            total_pdfs = current_pdf_info.get('total', 0)
            current_index = current_pdf_info.get('current', 0)
            self.total_pdfs_label.setText(f"📄 PDFs totaux: {total_pdfs}")
            self.current_pdf_label.setText(f"👁️ PDF actuel: {current_index + 1}")

        if session_data:
            validated = len(session_data.get('approved', []))
            rejected = len(session_data.get('rejected', []))
            pending = current_pdf_info.get('total', 0) - (validated + rejected)
            
            self.pdfs_validated_label.setText(f"✅ Validés: {validated}")
            self.pdfs_rejected_label.setText(f"❌ Rejetés: {rejected}")
            self.pdfs_pending_label.setText(f"⏳ En attente: {pending}")

        # Analyse de la litho courante
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
        self.litho_type_label.setText(f"Type: {litho_type}")

        # Détails de validation compacts
        if not is_cubby:
            valid_items = len([v for v in validation_results 
                             if not v.get('is_frame') and not v.get('is_space_saver')])
            passed_items = sum(1 for v in validation_results if v.get('overall', False))
            
            if valid_items > 0:
                success_rate = (passed_items / valid_items) * 100
                details_text = f"Validation: {passed_items}/{valid_items} ({success_rate:.0f}%)"
                
                # Ajout de détails par type de validation
                shade_numbers = sum(1 for v in validation_results if v.get('shade_number', False))
                shade_names = sum(1 for v in validation_results if v.get('shade_name', False))
                digits = sum(1 for v in validation_results if v.get('digits', False))
                
                details_text += f"\nTeintes: {shade_numbers}/{valid_items}"
                details_text += f" | Noms: {shade_names}/{valid_items}"
                details_text += f" | Digits: {digits}/{valid_items}"
            else:
                details_text = "Aucun produit à valider"
        else:
            # Pour les CUBBY
            dimensions = validation_results[0].get('cubby_dimensions', (0, 0))
            faces, tiers = dimensions
            details_text = f"Dimensions: {faces}F × {tiers}T\nProduits: {faces * tiers}"

        self.validation_details.setText(details_text)
            
    def reset(self):
        """Réinitialise les statistiques (alias pour compatibilité)"""
        self.reset_statistics()