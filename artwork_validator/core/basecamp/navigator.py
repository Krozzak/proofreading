"""
Module de navigation pour BaseCamp
Gère la navigation, le scroll et les retours vers les listes de fichiers
"""

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseCampNavigator:
    """Gestionnaire de navigation pour BaseCamp"""

    def __init__(self, driver, file_matcher, logger=None):
        self.driver = driver
        self.file_matcher = file_matcher
        self.logger = logger or logging.getLogger(__name__)

    def setup_basecamp_page(self):
        """Configuration initiale de la page BaseCamp"""
        try:
            self.logger.info("🔧 Configuration de la page BaseCamp...")

            # Attendre que la page soit stable
            self.wait_for_page_load()

            # Optimiser le chargement de la page
            self.optimized_scroll_to_load_more_files()

            self.logger.info("✅ Configuration BaseCamp terminée")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration BaseCamp: {e}")
            return False

    def optimized_scroll_to_load_more_files(self):
        """Scroll optimisé pour charger tous les fichiers de la page avec détection intelligente"""
        try:
            self.logger.info("🔄 Chargement de tous les fichiers de la page...")

            # Configuration adaptative
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_step = 300  # Scroll plus petit pour meilleure détection
            max_scrolls = 15   # Plus de tentatives
            scroll_count = 0
            stable_count = 0   # Compteur de stabilité
            max_stable = 3     # Nombre de scrolls sans changement avant arrêt

            # Compter les fichiers initiaux
            initial_files = self.file_matcher.count_visible_files()
            self.logger.info(f"📁 Fichiers initialement visibles: {initial_files}")

            while scroll_count < max_scrolls and stable_count < max_stable:
                # Scroll progressif
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.4)  # Temps d'attente plus long

                # Vérifier les changements
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                current_files = self.file_matcher.count_visible_files()

                if new_height > initial_height or current_files > initial_files:
                    self.logger.info(f"✅ Nouveaux éléments détectés - Fichiers: {current_files}")
                    initial_height = new_height
                    initial_files = current_files
                    stable_count = 0  # Reset compteur stabilité
                    time.sleep(0.6)   # Pause pour chargement complet
                else:
                    stable_count += 1

                # Vérifier si on a atteint le bas
                if current_position >= new_height:
                    self.logger.info("📍 Bas de page atteint")
                    break

                scroll_count += 1

            # Scroll final au bas pour être sûr
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)

            # Vérification finale du nombre de fichiers
            final_files = self.file_matcher.count_visible_files()
            self.logger.info(f"📊 Fichiers finalement chargés: {final_files}")

            # Remonter vers le haut pour navigation
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.4)
            self.logger.info("✅ Chargement et retour en haut terminés")

        except Exception as e:
            self.logger.error(f"Erreur lors du scroll optimisé: {e}")
            # En cas d'erreur, essayer un scroll simple
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
            except:
                pass

    def navigate_back_to_files(self):
        """
        Retourne intelligemment à la liste des fichiers
        Utilise plusieurs stratégies de retour avec fallbacks
        """
        try:
            self.logger.info("🔙 Retour à la liste des fichiers...")

            # Stratégies de retour ordonnées par fiabilité
            navigation_methods = [
                ("browser_back", self._navigate_back_browser),
                ("breadcrumb", self._navigate_back_breadcrumb),
                ("url_based", self._navigate_back_url),
                ("smart_links", self._navigate_back_smart_links),
                ("force_refresh", self._navigate_back_force_refresh)
            ]

            for method_name, method in navigation_methods:
                try:
                    self.logger.info(f"🔄 Tentative: {method_name}")
                    method()
                    self.wait_for_page_load()
                    self.logger.info(f"✅ Retour réussi avec: {method_name}")
                    return True
                except Exception as e:
                    self.logger.debug(f"⚠️ {method_name} échoué: {e}")
                    continue

            self.logger.warning("❌ Retour automatique impossible")
            return False

        except Exception as e:
            self.logger.error(f"Erreur lors du retour: {e}")
            return False

    def _navigate_back_browser(self):
        """Stratégie 1: Utiliser le bouton back du navigateur"""
        self.driver.back()
        time.sleep(1)

    def _navigate_back_breadcrumb(self):
        """Stratégie 2: Utiliser les breadcrumbs"""
        # Chercher différents types de breadcrumbs
        breadcrumb_selectors = [
            ".breadcrumbs a",
            ".breadcrumb a",
            "[data-behavior='breadcrumb'] a",
            ".navigation a",
            ".path a"
        ]

        for selector in breadcrumb_selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) >= 2:  # Prendre l'avant-dernier élément
                elements[-2].click()
                return

        raise Exception("Pas de breadcrumb trouvé")

    def _navigate_back_url(self):
        """Stratégie 3: Navigation basée sur l'URL"""
        current_url = self.driver.current_url

        # Essayer de remonter dans l'URL
        if '/files/' in current_url:
            # Extraire la partie avant le fichier spécifique
            base_url = current_url.split('/files/')[0] + '/files'
            self.driver.get(base_url)
        elif current_url.count('/') > 3:
            # Remonter d'un niveau dans l'URL
            parent_url = '/'.join(current_url.rstrip('/').split('/')[:-1])
            self.driver.get(parent_url)
        else:
            raise Exception("URL navigation impossible")

    def _navigate_back_smart_links(self):
        """Stratégie 4: Détection intelligente de liens de retour"""
        # Chercher des liens avec des mots-clés de retour
        back_keywords = ['back', 'return', 'files', 'list', 'folder', 'directory']

        for keyword in back_keywords:
            # Chercher dans le texte des liens
            links = self.driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")

            if links:
                links[0].click()
                return

        # Chercher dans les attributs title et aria-label
        for keyword in back_keywords:
            links = self.driver.find_elements(By.XPATH, f"//a[contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}') or contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")

            if links:
                links[0].click()
                return

        raise Exception("Pas de lien de retour intelligent trouvé")

    def _navigate_back_force_refresh(self):
        """Stratégie 5: Forcer le rafraîchissement vers une URL connue"""
        current_url = self.driver.current_url

        # Essayer de construire une URL de liste de fichiers
        if 'basecamp.com' in current_url:
            # Extraire l'ID du projet si possible
            import re
            project_match = re.search(r'/(\d+)/', current_url)

            if project_match:
                project_id = project_match.group(1)
                files_url = f"https://3.basecamp.com/{project_id}/files"
                self.driver.get(files_url)
                return

        # Fallback: actualiser la page actuelle
        self.driver.refresh()

    def wait_for_page_load(self, timeout=10):
        """Attend que la page soit complètement chargée"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(0.5)  # Petit délai supplémentaire pour la stabilité
        except Exception as e:
            self.logger.debug(f"Timeout attente chargement page: {e}")

    def check_window_status(self):
        """Vérifie si la fenêtre du navigateur est encore active"""
        try:
            # Vérifier que le driver est toujours actif
            if not self.driver:
                return False

            # Test simple pour vérifier la connexion
            self.driver.current_url
            return True

        except Exception as e:
            self.logger.error(f"Fenêtre navigateur fermée ou erreur: {e}")
            return False

    def scroll_to_element(self, element):
        """Scroll vers un élément spécifique"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
        except Exception as e:
            self.logger.debug(f"Erreur scroll vers élément: {e}")

    def get_current_page_info(self):
        """Récupère les informations de la page actuelle pour debugging"""
        try:
            return {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'files_count': self.file_matcher.count_visible_files()
            }
        except Exception:
            return {'url': 'Unknown', 'title': 'Unknown', 'files_count': 0}