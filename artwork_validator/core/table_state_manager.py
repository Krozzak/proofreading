# core/table_state_manager.py
import json
import os
from pathlib import Path


class TableStateManager:
    """
    Gestionnaire de l'état des tables pour persistence
    Sauvegarde et restaure les configurations de tables
    """

    def __init__(self, state_file="table_states.json"):
        self.state_file = state_file
        self.states = {}
        self.load_states()

    def get_state_file_path(self):
        """Retourne le chemin complet du fichier d'état"""
        # Sauvegarder dans le dossier utilisateur
        home_dir = Path.home()
        app_dir = home_dir / ".litho_validator"
        app_dir.mkdir(exist_ok=True)

        return app_dir / self.state_file

    def load_states(self):
        """Charge les états depuis le fichier"""
        state_path = self.get_state_file_path()

        if not state_path.exists():
            self.states = {}
            return

        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                self.states = json.load(f)
        except Exception as e:
            print(f"Erreur chargement états tables: {e}")
            self.states = {}

    def save_states(self):
        """Sauvegarde les états dans le fichier"""
        state_path = self.get_state_file_path()

        try:
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde états tables: {e}")

    def save_table_state(self, table_id, state):
        """
        Sauvegarde l'état d'une table
        Args:
            table_id: Identifiant unique de la table
            state: Dict contenant l'état (column_order, widths, etc.)
        """
        self.states[table_id] = state
        self.save_states()

    def get_table_state(self, table_id):
        """
        Récupère l'état d'une table
        Args:
            table_id: Identifiant unique de la table
        Returns:
            Dict contenant l'état ou None
        """
        return self.states.get(table_id)

    def delete_table_state(self, table_id):
        """Supprime l'état d'une table"""
        if table_id in self.states:
            del self.states[table_id]
            self.save_states()

    def get_all_table_ids(self):
        """Retourne tous les IDs de tables sauvegardées"""
        return list(self.states.keys())

    def clear_all_states(self):
        """Supprime tous les états"""
        self.states = {}
        self.save_states()
