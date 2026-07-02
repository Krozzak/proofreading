# ui/smart_table.py
from PyQt6.QtWidgets import (QTableWidget, QMenu, QApplication, QHeaderView,
                             QStyledItemDelegate, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QBrush, QAction
from ..utils.styles import LorealStyles
import json


class SmartTable(QTableWidget):
    """
    Table widget avancée avec fonctionnalités modernes:
    - Export sélection
    - Column reordering
    - Context menu enrichi
    - Cell comments
    - État persistant
    """

    # Signaux
    cell_comment_changed = pyqtSignal(int, int, str)  # row, col, comment
    column_order_changed = pyqtSignal(list)  # new order

    def __init__(self, parent=None):
        super().__init__(parent)

        # Stockage des métadonnées
        self.cell_comments = {}  # {(row, col): comment}
        self.frozen_columns = []
        self.column_presets = {}

        # Configuration de base
        self.setup_features()
        self.setup_context_menu()

    def setup_features(self):
        """Configure les fonctionnalités de base"""
        # Activer le tri
        self.setSortingEnabled(True)

        # Sélection par cellule
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)

        # Column reordering
        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.sectionMoved.connect(self.on_column_moved)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Style
        self.apply_smart_table_styles()

    def setup_context_menu(self):
        """Prépare le menu contextuel"""
        # Le menu sera créé dynamiquement dans show_context_menu
        pass

    def apply_smart_table_styles(self):
        """Applique les styles modernes"""
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {LorealStyles.COLORS['surface']};
                border: 1px solid {LorealStyles.COLORS['border']};
                border-radius: 4px;
                gridline-color: {LorealStyles.COLORS['border']};
                font-size: 10px;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {LorealStyles.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {LorealStyles.COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 10px;
            }}
            QHeaderView::section:hover {{
                background-color: {LorealStyles.COLORS['primary']};
            }}
        """)

    def show_context_menu(self, position: QPoint):
        """Affiche le menu contextuel"""
        menu = QMenu(self)

        # Vérifier s'il y a une sélection
        selected_ranges = self.selectedRanges()
        has_selection = len(selected_ranges) > 0

        # Actions de copie
        copy_cell_action = QAction("📋 Copier cellule", self)
        copy_cell_action.setShortcut("Ctrl+C")
        copy_cell_action.triggered.connect(self.copy_selection)
        copy_cell_action.setEnabled(has_selection)
        menu.addAction(copy_cell_action)

        copy_row_action = QAction("📋 Copier ligne complète", self)
        copy_row_action.triggered.connect(self.copy_full_row)
        copy_row_action.setEnabled(has_selection)
        menu.addAction(copy_row_action)

        copy_column_action = QAction("📋 Copier colonne", self)
        copy_column_action.triggered.connect(self.copy_column)
        copy_column_action.setEnabled(has_selection)
        menu.addAction(copy_column_action)

        copy_with_headers_action = QAction("📋 Copier avec en-têtes", self)
        copy_with_headers_action.setShortcut("Ctrl+Shift+C")
        copy_with_headers_action.triggered.connect(self.copy_with_headers)
        copy_with_headers_action.setEnabled(has_selection)
        menu.addAction(copy_with_headers_action)

        menu.addSeparator()

        # Export
        export_excel_action = QAction("📊 Exporter sélection → Excel", self)
        export_excel_action.triggered.connect(self.export_selection_to_excel)
        export_excel_action.setEnabled(has_selection)
        menu.addAction(export_excel_action)

        menu.addSeparator()

        # Commentaires
        current_item = self.itemAt(position)
        if current_item:
            row, col = current_item.row(), current_item.column()
            has_comment = (row, col) in self.cell_comments

            if has_comment:
                view_comment_action = QAction("💬 Voir commentaire", self)
                view_comment_action.triggered.connect(lambda: self.view_comment(row, col))
                menu.addAction(view_comment_action)

                edit_comment_action = QAction("✏️ Modifier commentaire", self)
                edit_comment_action.triggered.connect(lambda: self.edit_comment(row, col))
                menu.addAction(edit_comment_action)

                delete_comment_action = QAction("🗑️ Supprimer commentaire", self)
                delete_comment_action.triggered.connect(lambda: self.delete_comment(row, col))
                menu.addAction(delete_comment_action)
            else:
                add_comment_action = QAction("💬 Ajouter commentaire", self)
                add_comment_action.setShortcut("Shift+F2")
                add_comment_action.triggered.connect(lambda: self.add_comment(row, col))
                menu.addAction(add_comment_action)

        # Afficher le menu
        menu.exec(self.viewport().mapToGlobal(position))

    def copy_selection(self):
        """Copie la sélection courante"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        # Construire le texte à copier
        text_data = []
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.item(row, col)
                    row_data.append(item.text() if item else "")
                text_data.append("\t".join(row_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(text_data))

    def copy_full_row(self):
        """Copie la ligne entière"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        text_data = []
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    row_data.append(item.text() if item else "")
                text_data.append("\t".join(row_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(text_data))

    def copy_column(self):
        """Copie la colonne entière"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        text_data = []
        for selected_range in selected_ranges:
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                col_data = []
                for row in range(self.rowCount()):
                    item = self.item(row, col)
                    col_data.append(item.text() if item else "")
                text_data.append("\n".join(col_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\t".join(text_data))

    def copy_with_headers(self):
        """Copie la sélection avec les en-têtes"""
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        text_data = []

        for selected_range in selected_ranges:
            # Headers
            headers = []
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                header_item = self.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Col{col}")
            text_data.append("\t".join(headers))

            # Data
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                row_data = []
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.item(row, col)
                    row_data.append(item.text() if item else "")
                text_data.append("\t".join(row_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(text_data))

    def export_selection_to_excel(self):
        """Exporte la sélection vers Excel"""
        # TODO: Implémenter export Excel avec pandas
        QMessageBox.information(self, "Export Excel", "Fonctionnalité à venir dans la prochaine version!")

    def add_comment(self, row, col):
        """Ajoute un commentaire à une cellule"""
        from PyQt6.QtWidgets import QInputDialog

        comment, ok = QInputDialog.getMultiLineText(
            self,
            "Ajouter un commentaire",
            f"Commentaire pour la cellule ({row}, {col}):",
            ""
        )

        if ok and comment:
            self.cell_comments[(row, col)] = comment
            self.mark_cell_with_comment(row, col)
            self.cell_comment_changed.emit(row, col, comment)

    def edit_comment(self, row, col):
        """Modifie un commentaire existant"""
        from PyQt6.QtWidgets import QInputDialog

        current_comment = self.cell_comments.get((row, col), "")

        comment, ok = QInputDialog.getMultiLineText(
            self,
            "Modifier le commentaire",
            f"Commentaire pour la cellule ({row}, {col}):",
            current_comment
        )

        if ok:
            if comment:
                self.cell_comments[(row, col)] = comment
                self.cell_comment_changed.emit(row, col, comment)
            else:
                self.delete_comment(row, col)

    def view_comment(self, row, col):
        """Affiche un commentaire"""
        comment = self.cell_comments.get((row, col), "")
        QMessageBox.information(
            self,
            f"Commentaire ({row}, {col})",
            comment
        )

    def delete_comment(self, row, col):
        """Supprime un commentaire"""
        if (row, col) in self.cell_comments:
            del self.cell_comments[(row, col)]
            self.unmark_cell_with_comment(row, col)
            self.cell_comment_changed.emit(row, col, "")

    def mark_cell_with_comment(self, row, col):
        """Marque visuellement une cellule avec commentaire"""
        item = self.item(row, col)
        if item:
            # Ajouter un indicateur visuel (triangle dans le coin)
            comment = self.cell_comments.get((row, col), "")
            item.setToolTip(f"💬 {comment}")

            # Changer la couleur de fond
            current_bg = item.background()
            if current_bg.color() == QColor("white"):
                item.setBackground(QBrush(QColor("#fff9c4")))  # Jaune clair

    def unmark_cell_with_comment(self, row, col):
        """Retire la marque visuelle du commentaire"""
        item = self.item(row, col)
        if item:
            item.setToolTip("")
            item.setBackground(QBrush(QColor("white")))

    def on_column_moved(self, logical_index, old_visual_index, new_visual_index):
        """Callback quand une colonne est déplacée"""
        # Émettre le signal avec le nouvel ordre
        new_order = []
        for i in range(self.columnCount()):
            new_order.append(self.horizontalHeader().logicalIndex(i))

        self.column_order_changed.emit(new_order)

    def get_column_order(self):
        """Retourne l'ordre actuel des colonnes"""
        order = []
        header = self.horizontalHeader()
        for i in range(self.columnCount()):
            order.append(header.logicalIndex(i))
        return order

    def set_column_order(self, order):
        """Définit l'ordre des colonnes"""
        header = self.horizontalHeader()
        for visual_index, logical_index in enumerate(order):
            header.moveSection(header.visualIndex(logical_index), visual_index)

    def keyPressEvent(self, event):
        """Gère les raccourcis clavier"""
        # Ctrl+C → Copier
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selection()
            return

        # Ctrl+Shift+C → Copier avec headers
        if (event.key() == Qt.Key.Key_C and
            event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
            self.copy_with_headers()
            return

        # Shift+F2 → Ajouter commentaire
        if event.key() == Qt.Key.Key_F2 and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            current_item = self.currentItem()
            if current_item:
                self.add_comment(current_item.row(), current_item.column())
            return

        super().keyPressEvent(event)

    def get_state(self):
        """Retourne l'état actuel de la table pour persistence"""
        state = {
            'column_order': self.get_column_order(),
            'column_widths': {},
            'comments': {f"{k[0]},{k[1]}": v for k, v in self.cell_comments.items()},
        }

        # Largeurs des colonnes
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                state['column_widths'][header_item.text()] = self.columnWidth(col)

        return state

    def restore_state(self, state):
        """Restaure l'état de la table"""
        if not state:
            return

        # Ordre des colonnes
        if 'column_order' in state:
            try:
                self.set_column_order(state['column_order'])
            except Exception as e:
                print(f"Erreur restauration ordre colonnes: {e}")

        # Largeurs
        if 'column_widths' in state:
            for col in range(self.columnCount()):
                header_item = self.horizontalHeaderItem(col)
                if header_item and header_item.text() in state['column_widths']:
                    self.setColumnWidth(col, state['column_widths'][header_item.text()])

        # Commentaires
        if 'comments' in state:
            for key, comment in state['comments'].items():
                row, col = map(int, key.split(','))
                if row < self.rowCount() and col < self.columnCount():
                    self.cell_comments[(row, col)] = comment
                    self.mark_cell_with_comment(row, col)
