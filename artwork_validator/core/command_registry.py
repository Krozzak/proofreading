# core/command_registry.py
from dataclasses import dataclass
from typing import Callable, List, Optional
import difflib


@dataclass
class Command:
    """Représente une commande exécutable dans l'application"""
    id: str
    name: str
    description: str
    callback: Callable
    category: str
    shortcut: str = ""
    icon: str = ""
    enabled: bool = True

    def execute(self):
        """Exécute la commande"""
        if self.enabled and self.callback:
            self.callback()

    def matches_query(self, query: str) -> tuple[bool, int]:
        """
        Vérifie si la commande correspond à la requête
        Returns: (matches, score) - score plus élevé = meilleure correspondance
        """
        if not query:
            return True, 0

        query = query.lower()
        name_lower = self.name.lower()
        desc_lower = self.description.lower()
        shortcut_lower = self.shortcut.lower()

        # Correspondance exacte dans le nom
        if query == name_lower:
            return True, 1000

        # Correspondance exacte dans le raccourci
        if query == shortcut_lower:
            return True, 900

        # Commence par la query
        if name_lower.startswith(query):
            return True, 800

        # Contient la query dans le nom
        if query in name_lower:
            return True, 700

        # Contient la query dans la description
        if query in desc_lower:
            return True, 600

        # Fuzzy matching avec difflib
        ratio = difflib.SequenceMatcher(None, query, name_lower).ratio()
        if ratio > 0.6:
            return True, int(ratio * 500)

        return False, 0


class CommandRegistry:
    """Registre central de toutes les commandes de l'application"""

    def __init__(self):
        self.commands: dict[str, Command] = {}
        self.categories: set[str] = set()

    def register(self, command: Command):
        """Enregistre une nouvelle commande"""
        self.commands[command.id] = command
        self.categories.add(command.category)

    def unregister(self, command_id: str):
        """Désenregistre une commande"""
        if command_id in self.commands:
            del self.commands[command_id]

    def get(self, command_id: str) -> Optional[Command]:
        """Récupère une commande par son ID"""
        return self.commands.get(command_id)

    def execute(self, command_id: str):
        """Exécute une commande par son ID"""
        command = self.get(command_id)
        if command:
            command.execute()

    def search(self, query: str) -> List[Command]:
        """
        Recherche des commandes correspondant à la requête
        Retourne une liste triée par pertinence
        """
        if not query:
            # Si pas de query, retourner toutes les commandes activées
            return [cmd for cmd in self.commands.values() if cmd.enabled]

        results = []
        for command in self.commands.values():
            if not command.enabled:
                continue

            matches, score = command.matches_query(query)
            if matches:
                results.append((command, score))

        # Trier par score décroissant
        results.sort(key=lambda x: x[1], reverse=True)

        return [cmd for cmd, score in results]

    def get_by_category(self, category: str) -> List[Command]:
        """Récupère toutes les commandes d'une catégorie"""
        return [cmd for cmd in self.commands.values()
                if cmd.category == category and cmd.enabled]

    def get_all_categories(self) -> List[str]:
        """Récupère toutes les catégories"""
        return sorted(list(self.categories))

    def get_all_commands(self) -> List[Command]:
        """Récupère toutes les commandes activées"""
        return [cmd for cmd in self.commands.values() if cmd.enabled]

    def register_batch(self, commands: List[Command]):
        """Enregistre plusieurs commandes à la fois"""
        for command in commands:
            self.register(command)

    def clear(self):
        """Vide le registre"""
        self.commands.clear()
        self.categories.clear()

    def enable_command(self, command_id: str):
        """Active une commande"""
        command = self.get(command_id)
        if command:
            command.enabled = True

    def disable_command(self, command_id: str):
        """Désactive une commande"""
        command = self.get(command_id)
        if command:
            command.enabled = False
