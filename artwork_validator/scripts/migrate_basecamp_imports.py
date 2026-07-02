#!/usr/bin/env python3
"""
Script de migration pour mettre à jour les imports BaseCamp
Migre automatiquement du monolithe vers l'architecture modulaire

Usage:
    python scripts/migrate_basecamp_imports.py [--dry-run] [--path PATH]
"""

import os
import re
import argparse
import logging
from pathlib import Path


class BaseCampImportMigrator:
    """Outil de migration automatique des imports BaseCamp"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.changes_made = []
        self.setup_logging()

    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def find_python_files(self, root_path):
        """Trouve tous les fichiers Python dans le répertoire"""
        python_files = []
        for root, dirs, files in os.walk(root_path):
            # Ignorer certains dossiers
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules']]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        return python_files

    def migrate_file(self, file_path):
        """Migre les imports dans un fichier spécifique"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_in_file = []

            # Patterns de migration
            migrations = [
                # Import direct de l'ancien module
                (
                    r'from\s+core\.basecamp_processor\s+import\s+BaseCampProcessor',
                    'from core.basecamp import BaseCampProcessor',
                    'Import direct BaseCampProcessor'
                ),
                (
                    r'from\s+core\.basecamp_processor\s+import\s+BasecampProcessor',
                    'from core.basecamp import BaseCampProcessor',
                    'Import direct BasecampProcessor (variante)'
                ),
                # Import avec alias
                (
                    r'from\s+core\.basecamp_processor\s+import\s+BaseCampProcessor\s+as\s+(\w+)',
                    r'from core.basecamp import BaseCampProcessor as \1',
                    'Import avec alias'
                ),
                # Import module complet
                (
                    r'import\s+core\.basecamp_processor',
                    'from core import basecamp',
                    'Import module complet'
                ),
                # Usage dans le code
                (
                    r'core\.basecamp_processor\.BaseCampProcessor',
                    'basecamp.BaseCampProcessor',
                    'Usage dans le code'
                ),
            ]

            # Appliquer les migrations
            for pattern, replacement, description in migrations:
                matches = list(re.finditer(pattern, content))
                if matches:
                    content = re.sub(pattern, replacement, content)
                    changes_in_file.append({
                        'description': description,
                        'pattern': pattern,
                        'replacement': replacement,
                        'count': len(matches)
                    })

            # Sauvegarder si des changements ont été faits
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                self.changes_made.append({
                    'file': file_path,
                    'changes': changes_in_file
                })

                self.logger.info(f"✅ Migré: {file_path}")
                for change in changes_in_file:
                    self.logger.info(f"   - {change['description']}: {change['count']} occurrences")

            return len(changes_in_file) > 0

        except Exception as e:
            self.logger.error(f"❌ Erreur migration {file_path}: {e}")
            return False

    def migrate_directory(self, root_path):
        """Migre tous les fichiers Python d'un répertoire"""
        self.logger.info(f"🚀 Début migration dans: {root_path}")

        if self.dry_run:
            self.logger.info("⚠️ Mode DRY-RUN activé - aucun fichier ne sera modifié")

        python_files = self.find_python_files(root_path)
        self.logger.info(f"📁 {len(python_files)} fichiers Python trouvés")

        migrated_count = 0
        for file_path in python_files:
            if self.migrate_file(file_path):
                migrated_count += 1

        self.logger.info(f"🎉 Migration terminée: {migrated_count} fichiers modifiés")
        return migrated_count

    def generate_report(self):
        """Génère un rapport des changements"""
        if not self.changes_made:
            return "Aucun changement nécessaire."

        report = []
        report.append("RAPPORT DE MIGRATION BASECAMP")
        report.append("=" * 50)
        report.append(f"Fichiers modifiés: {len(self.changes_made)}")
        report.append("")

        for file_change in self.changes_made:
            report.append(f"📁 {file_change['file']}")
            for change in file_change['changes']:
                report.append(f"   ✓ {change['description']}: {change['count']} occurrence(s)")
            report.append("")

        return "\n".join(report)

    def create_backup(self, root_path):
        """Crée une sauvegarde avant migration"""
        if self.dry_run:
            return

        backup_dir = os.path.join(root_path, '.migration_backup')
        os.makedirs(backup_dir, exist_ok=True)

        python_files = self.find_python_files(root_path)
        for file_path in python_files:
            # Créer le chemin de sauvegarde
            rel_path = os.path.relpath(file_path, root_path)
            backup_path = os.path.join(backup_dir, rel_path)

            # Créer les dossiers nécessaires
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Copier le fichier
            import shutil
            shutil.copy2(file_path, backup_path)

        self.logger.info(f"💾 Sauvegarde créée dans: {backup_dir}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Migre les imports BaseCamp vers l'architecture modulaire")
    parser.add_argument('--dry-run', action='store_true', help="Mode test - ne modifie aucun fichier")
    parser.add_argument('--path', default='.', help="Chemin racine pour la migration")
    parser.add_argument('--backup', action='store_true', help="Créer une sauvegarde avant migration")
    parser.add_argument('--report', help="Fichier pour sauvegarder le rapport")

    args = parser.parse_args()

    # Initialiser le migrateur
    migrator = BaseCampImportMigrator(dry_run=args.dry_run)

    # Créer une sauvegarde si demandé
    if args.backup:
        migrator.create_backup(args.path)

    # Exécuter la migration
    migrator.migrate_directory(args.path)

    # Générer le rapport
    report = migrator.generate_report()
    print("\n" + report)

    # Sauvegarder le rapport si demandé
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Rapport sauvegardé: {args.report}")


if __name__ == '__main__':
    main()