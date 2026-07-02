"""
Module principal de traitement BaseCamp - Version refactorisée
Orchestrateur principal utilisant les modules spécialisés pour une meilleure maintenabilité
"""

import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Import des modules spécialisés
from .file_matcher import BaseCampFileMatcher
from .comment_manager import BaseCampCommentManager
from .navigator import BaseCampNavigator
from .reporter import BaseCampReporter


class BaseCampProcessor:
    """
    Processeur principal BaseCamp refactorisé
    Utilise une architecture modulaire pour une meilleure maintenabilité
    """

    def __init__(self, session_manager=None, logger=None):
        self.session_manager = session_manager
        self.logger = logger or self._setup_logger()

        # Composants spécialisés
        self.driver = None
        self.file_matcher = None
        self.comment_manager = None
        self.navigator = None
        self.reporter = BaseCampReporter(self.logger)

        # Configuration
        self.start_time = None
        self.edge_driver_path = None

    def _setup_logger(self):
        """Configuration du logger par défaut"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def setup_browser(self, edge_driver_path=None, headless=False):
        """Configuration et initialisation du navigateur Edge"""
        try:
            self.logger.info("🌐 Configuration du navigateur Edge...")
            self.edge_driver_path = edge_driver_path

            # Configuration Edge avec options complètes du script original
            edge_options = Options()

            # Options pour une expérience plus naturelle (issues du script original)
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--disable-features=VizDisplayCompositor")

            # Support du mode headless
            if headless:
                edge_options.add_argument("--headless")
            else:
                edge_options.add_argument("--start-maximized")

            # Initialiser le driver
            if edge_driver_path:
                service = Service(edge_driver_path)
                self.driver = webdriver.Edge(service=service, options=edge_options)
            else:
                self.driver = webdriver.Edge(options=edge_options)

            # Masquer les indicateurs d'automation et configurer la fenêtre
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            if not headless:
                self.driver.set_window_size(1920, 1080)

            # Initialiser les composants spécialisés
            self.file_matcher = BaseCampFileMatcher(self.driver, self.logger)
            self.comment_manager = BaseCampCommentManager(self.driver, self.logger)
            self.navigator = BaseCampNavigator(self.driver, self.file_matcher, self.logger)

            self.logger.info("✅ Navigateur Edge configuré avec succès")
            return True

        except Exception as e:
            self.logger.error(f"Erreur configuration navigateur: {e}")
            return False

    def setup_driver(self, headless=False):
        """Méthode alias pour compatibilité avec l'interface existante"""
        return self.setup_browser(headless=headless)

    def open_basecamp(self, url=None):
        """Ouvre BaseCamp et attend la navigation utilisateur"""
        try:
            if not self.driver:
                self.logger.error("❌ Navigateur non initialisé")
                return False

            # URL par défaut ou fournie
            target_url = url or "https://3.basecamp.com"

            self.logger.info(f"🌐 Ouverture de BaseCamp: {target_url}")
            self.driver.get(target_url)

            self.logger.info("⏳ Veuillez vous connecter et naviguer vers le dossier de fichiers...")
            self.logger.info("📁 Une fois dans le dossier, l'application détectera automatiquement votre présence")

            return True

        except Exception as e:
            self.logger.error(f"Erreur ouverture BaseCamp: {e}")
            return False

    def setup_basecamp_page(self):
        """Configuration de la page BaseCamp après navigation utilisateur"""
        try:
            return self.navigator.setup_basecamp_page()
        except Exception as e:
            self.logger.error(f"Erreur configuration page BaseCamp: {e}")
            return False

    def process_approved_lithos(self):
        """Traite toutes les lithographies approuvées avec reporting détaillé"""
        if not self.session_manager:
            self.logger.error("❌ Session manager non disponible")
            return self.reporter.create_detailed_report(
                {"success": 0, "errors": 0, "skipped": 0, "not_found": 0},
                []
            )

        approved_lithos = self.session_manager.get_approved_lithos()

        if not approved_lithos:
            self.logger.warning("⚠️ Aucune lithographie approuvée à traiter")
            return self.reporter.create_detailed_report(
                {"success": 0, "errors": 0, "skipped": 0, "not_found": 0},
                []
            )

        self.logger.info(f"🚀 Début du traitement de {len(approved_lithos)} lithographies approuvées")

        # Initialiser le rapport détaillé
        results = {"success": 0, "errors": 0, "skipped": 0, "not_found": 0}
        detailed_log = []
        session_start = datetime.now()
        self.start_time = session_start

        # Traiter chaque lithographie
        for i, litho_code in enumerate(approved_lithos, 1):
            file_log_entry = self._process_single_litho(litho_code, i, len(approved_lithos))
            detailed_log.append(file_log_entry)

            # Comptabiliser les résultats
            result = file_log_entry.get('result', 'error')
            if result in results:
                results[result] += 1
            else:
                results["errors"] += 1

            # Navigation vers le fichier suivant
            if i < len(approved_lithos):
                self._navigate_to_next_file()

        # Finaliser le rapport
        session_end = datetime.now()
        total_duration = (session_end - session_start).total_seconds()

        self.logger.info(f"🎉 Traitement terminé en {total_duration:.1f}s: {results}")
        return self.reporter.create_detailed_report(results, detailed_log, session_start)

    def _process_single_litho(self, litho_code, index, total):
        """Traite une lithographie individuelle avec logging détaillé"""
        self.logger.info(f"📁 [{index}/{total}] Traitement de {litho_code}")

        # Initialiser le log pour ce fichier
        file_start_time = datetime.now()
        file_log_entry = {
            'litho_code': litho_code,
            'index': index,
            'total': total,
            'start_time': file_start_time,
            'file_found': False,
            'comment_added': False,
            'error_type': None,
            'matching_strategy': None,
            'user_comment': '',
            'basecamp_url': '',
            'processing_time': 0,
            'result': 'error'
        }

        try:
            # Récupérer les informations de la lithographie
            litho_status = self.session_manager.get_litho_status(litho_code)
            comment = litho_status.get('comment', '') if litho_status else ''
            file_log_entry['user_comment'] = comment

            # Traiter le fichier (passer le code YCA sans extension pour correspondance BaseCamp)
            file_name = litho_code  # Au lieu de f"{litho_code}.pdf"
            result, processing_details = self._process_file_with_details(file_name, litho_code, comment)

            # Enrichir le log
            file_log_entry.update(processing_details)
            file_log_entry['result'] = result

        except Exception as e:
            self.logger.error(f"Erreur traitement {litho_code}: {e}")
            file_log_entry['error_type'] = 'processing_exception'
            file_log_entry['error_message'] = str(e)
            file_log_entry['result'] = 'error'

        finally:
            # Finaliser le temps de traitement
            file_end_time = datetime.now()
            file_log_entry['end_time'] = file_end_time
            file_log_entry['processing_time'] = (file_end_time - file_start_time).total_seconds()

        return file_log_entry

    def _process_file_with_details(self, file_name, litho_code, comment="", status="approved", force_comment=False):
        """Traite un fichier avec reporting détaillé des étapes"""
        details = {
            'file_found': False,
            'comment_added': False,
            'matching_strategy': None,
            'basecamp_url': '',
            'file_elements_count': 0,
            'existing_comments': [],
            'navigation_attempts': 0,
            'error_type': None,
            'error_message': ''
        }

        try:
            # Enregistrer l'URL actuelle
            if self.driver:
                details['basecamp_url'] = self.driver.current_url

            # Rechercher le fichier
            element = self.file_matcher.find_file_by_advanced_matching(file_name, litho_code)
            details['navigation_attempts'] += 1

            if element:
                details['file_found'] = True
                details['matching_strategy'] = getattr(element, '_matching_strategy', 'unknown')
                details['file_elements_count'] = self.file_matcher.count_visible_files()

                # Cliquer sur le fichier
                element.click()
                self.navigator.wait_for_page_load()

                # Vérifier et ajouter le commentaire
                comment_check = self.comment_manager.check_existing_comments(force_comment)
                details['existing_comments'] = comment_check.get('existing_comments', [])

                if comment_check['skip_file']:
                    self.logger.info(f"⏭️ Fichier ignoré: {comment_check['reason']}")
                    return "skipped", details

                # Ajouter le commentaire
                comment_text = self.comment_manager.prepare_comment(status, comment)
                if self.comment_manager.add_intelligent_comment(comment_text, status):
                    details['comment_added'] = True
                    self.logger.info(f"✅ Commentaire ajouté pour {file_name}")
                    return "success", details
                else:
                    details['error_type'] = 'comment_failed'
                    self.logger.error(f"❌ Échec ajout commentaire pour {file_name}")
                    return "error", details

            else:
                details['error_type'] = 'file_not_found'
                self.logger.warning(f"❌ Fichier non trouvé: {file_name}")
                return "not_found", details

        except Exception as e:
            details['error_type'] = 'processing_exception'
            details['error_message'] = str(e)
            self.logger.error(f"Erreur traitement fichier {file_name}: {e}")
            return "error", details

    def _navigate_to_next_file(self):
        """Navigation vers le fichier suivant"""
        try:
            self.navigator.navigate_back_to_files()
        except Exception as e:
            self.logger.warning(f"Erreur retour à la liste: {e}")

    def process_file(self, file_name, litho_code, comment="", status="approved", force_comment=False):
        """Interface de compatibilité pour l'ancien code"""
        result, _ = self._process_file_with_details(file_name, litho_code, comment, status, force_comment)
        return result

    def check_window_status(self):
        """Vérifie si la fenêtre du navigateur est encore active"""
        return self.navigator.check_window_status() if self.navigator else False

    def get_current_page_info(self):
        """Récupère les informations de la page actuelle"""
        if self.navigator:
            return self.navigator.get_current_page_info()
        return {'url': 'Unknown', 'title': 'Unknown', 'files_count': 0}

    def cleanup(self):
        """Nettoie les ressources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🧹 Navigateur fermé")
            except Exception as e:
                self.logger.debug(f"Erreur fermeture navigateur: {e}")

    # Méthodes de délégation pour compatibilité avec l'interface UI
    def optimized_scroll_to_load_more_files(self):
        """Délégation vers navigator pour scroll optimisé"""
        if self.navigator:
            return self.navigator.optimized_scroll_to_load_more_files()
        else:
            self.logger.warning("⚠️ Navigator non initialisé pour scroll optimisé")
            return False

    def wait_for_page_load(self, timeout=10):
        """Délégation vers navigator pour attente de chargement"""
        if self.navigator:
            return self.navigator.wait_for_page_load(timeout)
        else:
            self.logger.warning("⚠️ Navigator non initialisé pour wait_for_page_load")
            return False

    def navigate_back_to_files(self):
        """Délégation vers navigator pour retour aux fichiers"""
        if self.navigator:
            return self.navigator.navigate_back_to_files()
        else:
            self.logger.warning("⚠️ Navigator non initialisé pour navigate_back_to_files")
            return False


class BaseCampProcessorLegacy:
    """
    Version legacy maintenue pour compatibilité
    À utiliser uniquement si la version refactorisée pose problème
    """

    def __init__(self, session_manager=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.warning("⚠️ Utilisation de la version legacy de BaseCampProcessor")
        self.logger.warning("⚠️ Considérez migrer vers la version refactorisée")

        # Importer l'ancienne implémentation si nécessaire
        # from .basecamp_processor_old import BaseCampProcessorOld
        # self.processor = BaseCampProcessorOld(session_manager, logger)

    def __getattr__(self, name):
        """Déléguer vers l'ancienne implémentation"""
        # return getattr(self.processor, name)
        raise NotImplementedError("Version legacy non disponible")


# Alias pour la compatibilité
BaseCampProcessorRefactored = BaseCampProcessor