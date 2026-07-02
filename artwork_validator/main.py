# main.py
import sys
import traceback
import logging
import os
from PyQt6.QtWidgets import QApplication
try:
    # Importation package (pour exécution avec -m)
    from litho_validator.ui.main_window import MainWindow
except ModuleNotFoundError:
    # Importation relative (pour exécution directe)
    from pathlib import Path

    # Ajouter le dossier parent au path pour que Python trouve le package
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from litho_validator.ui.main_window import MainWindow

def initialize_brand_registry():
    """Initialise le registry des marques avec les configurations disponibles"""
    from litho_validator.core.brand_configs import BrandRegistry, MNYBrandConfig, ESSIEBrandConfig

    logger = logging.getLogger(__name__)

    try:
        # Enregistrer toutes les marques supportées
        BrandRegistry.register(MNYBrandConfig())
        BrandRegistry.register(ESSIEBrandConfig())

        logger.info("✅ Brand registry initialized with 2 brands: MNY, ESSIE")

    except Exception as e:
        logger.error(f"❌ Error initializing brand registry: {str(e)}")
        raise

def setup_logging():
    """Configure le système de logging avec gestion sécurisée des emojis"""

    # Configuration de l'encodage UTF-8 pour Windows
    try:
        if sys.platform == "win32":
            # Essayer de configurer la console pour UTF-8
            os.system("chcp 65001 > nul 2>&1")  # Change code page to UTF-8
            
            # Reconfigure stdout et stderr si possible (Python 3.7+)
            try:
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
            except Exception:
                pass
    except Exception:
        # Si ça échoue, on continue sans UTF-8
        pass
    
    # Handler sécurisé pour la console qui gère les emojis
    class SafeStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                super().emit(record)
            except UnicodeEncodeError:
                # Remplacer les caractères problématiques par des alternatives
                try:
                    msg = self.format(record)
                    # Remplacer les emojis par du texte simple pour les logs console
                    emoji_replacements = {
                        '🔄': '[LOADING]',
                        '✅': '[OK]',
                        '❌': '[ERROR]', 
                        '⚠️': '[WARNING]',
                        '🔍': '[SEARCH]',
                        '📊': '[STATS]',
                        '📝': '[INFO]',
                        '🔧': '[CONFIG]',
                        '🚀': '[START]',
                        '📁': '[FILE]',
                        '💬': '[COMMENT]',
                        '🎯': '[TARGET]',
                        '🏁': '[FINISH]',
                        '⏸️': '[PAUSE]',
                        '🔙': '[BACK]',
                        '📋': '[LIST]',
                        '🎉': '[SUCCESS]',
                        '⏭️': '[SKIP]',
                        '❓': '[QUESTION]'
                    }
                    for emoji, replacement in emoji_replacements.items():
                        msg = msg.replace(emoji, replacement)
                    
                    # Encoder en ASCII avec remplacement
                    safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
                    print(safe_msg)
                except Exception:
                    print(f"[LOG ERROR] - {record.levelname}: Message encoding failed")
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('litho_validator.log', encoding='utf-8'),  # Fichier avec UTF-8
            SafeStreamHandler(sys.stdout)  # Console avec gestion sécurisée
        ]
    )

def setup_application():
    """Configure l'application Qt avec optimisations"""

    # Note: PyQt6 gère automatiquement le High DPI, pas besoin de configuration manuelle
    # Les attributs AA_EnableHighDpiScaling et AA_UseHighDpiPixmaps ont été supprimés
    
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("L'Oréal Litho Validator")
    app.setApplicationVersion("1.0")
    app.setApplicationDisplayName("L'Oréal Litho Validator")
    
    # Configuration du style de l'application
    app.setStyle('Fusion')  # Style moderne et compatible
    
    return app

def exception_hook(exctype, value, tb):
    """Gestionnaire d'exceptions global amélioré"""
    if issubclass(exctype, KeyboardInterrupt):
        # Permettre l'interruption par Ctrl+C
        sys.__excepthook__(exctype, value, tb)
        return
    
    # Log de l'exception
    logger = logging.getLogger("root")
    logger.error("Exception non gérée:", exc_info=(exctype, value, tb))
    
    # Affichage dans la console également
    traceback.print_exception(exctype, value, tb)

def main():
    """Fonction principale avec gestion d'erreurs robuste"""
    
    # Configuration du logging en premier
    setup_logging()
    
    # Installation du gestionnaire d'exceptions
    sys.excepthook = exception_hook
    
    # Logger pour la fonction main
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Démarrage de L'Oréal Litho Validator")

        # 🆕 Initialiser le registry des marques AVANT l'application
        initialize_brand_registry()

        # Configuration et création de l'application
        app = setup_application()
        
        # Importation et création de la fenêtre principale
        logger.info("Initialisation de l'interface principale")
        window = MainWindow()
        window.show()
        
        logger.info("Application prête - Interface affichée")
        
        # Démarrage de la boucle principale
        return app.exec()
        
    except ImportError as e:
        error_msg = f"Erreur d'importation - Dépendance manquante: {str(e)}"
        logger.error(error_msg)
        print(f"ERREUR CRITIQUE: {error_msg}")
        return 1
        
    except Exception as e:
        error_msg = f"Erreur fatale lors du démarrage: {str(e)}"
        logger.error(error_msg)
        print(f"ERREUR CRITIQUE: {error_msg}")
        return 1
        
    finally:
        logger.info("Fermeture de l'application")

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur fatale non gérée: {str(e)}")
        traceback.print_exc()
        sys.exit(1)