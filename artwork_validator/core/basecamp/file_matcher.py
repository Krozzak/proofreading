"""
Module de correspondance de fichiers pour BaseCamp
Gère les différentes stratégies de recherche et correspondance de fichiers
"""

import re
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from difflib import SequenceMatcher


class BaseCampFileMatcher:
    """Gestionnaire des stratégies de correspondance de fichiers BaseCamp"""

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)

    def find_file_by_advanced_matching(self, file_name, litho_code, pdf_description=""):
        """Recherche avancée avec multiples stratégies de correspondance"""
        strategies = [
            ("exact_name", self._find_by_exact_name),
            ("yca_code", self._find_by_yca_code),
            ("partial_8chars", self._find_by_partial_match),
            ("flexible_number", self._find_by_flexible_number),
            ("similarity_matching", self._find_by_similarity)
        ]

        self.logger.info(f"🔍 Recherche de {file_name} avec code {litho_code}")

        for strategy_name, strategy_func in strategies:
            try:
                self.logger.debug(f"Tentative stratégie: {strategy_name}")
                element = strategy_func(file_name, litho_code, pdf_description)

                if element:
                    # Marquer l'élément avec la stratégie utilisée
                    element._matching_strategy = strategy_name
                    self.logger.info(f"✅ Fichier trouvé avec stratégie: {strategy_name}")
                    return element

            except Exception as e:
                self.logger.debug(f"Erreur stratégie {strategy_name}: {e}")
                continue

        self.logger.warning(f"❌ Aucune stratégie n'a trouvé le fichier {file_name}")
        return None

    def _find_by_exact_name(self, file_name, litho_code, pdf_description=""):
        """Recherche par nom exact"""
        try:
            xpath = f"//a[contains(@href, '{file_name}') or contains(text(), '{file_name}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            return elements[0] if elements else None
        except Exception:
            return None

    def _find_by_yca_code(self, file_name, litho_code, pdf_description=""):
        """Recherche par code YCA avec support de toutes les variations BaseCamp"""
        try:
            # Le file_name est maintenant le code YCA direct (ex: YCA28654)
            # litho_code contient aussi le même code
            yca_code = file_name if file_name.startswith('YCA') else litho_code

            self.logger.debug(f"Recherche YCA avec code: {yca_code}")

            # Patterns optimisés pour BaseCamp (ordre de priorité)
            patterns = [
                yca_code,                    # YCA28654 (exact)
                f"{yca_code}_",             # YCA28654_ (underscore)
                f"{yca_code}-",             # YCA28654- (tiret)
                f"{yca_code}.pdf",          # YCA28654.pdf (extension simple)
                f"{yca_code} ",             # YCA28654 (avec espace)
            ]

            for i, pattern in enumerate(patterns, 1):
                try:
                    # XPath optimisé pour recherche par début de nom
                    xpath = f"//a[starts-with(@href, '{pattern}') or starts-with(text(), '{pattern}') or contains(@href, '{pattern}') or contains(text(), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)

                    if elements:
                        self.logger.info(f"✅ Correspondance trouvée avec pattern {i}: '{pattern}'")
                        self.logger.debug(f"Élément trouvé: {elements[0].text[:50]}...")
                        return elements[0]
                    else:
                        self.logger.debug(f"Pattern {i} '{pattern}': aucune correspondance")

                except Exception as e:
                    self.logger.debug(f"Erreur pattern '{pattern}': {e}")
                    continue

            # Fallback: extraction YCA classique pour compatibilité
            yca_match = re.search(r'YCA(\d{5})', yca_code.upper())
            if yca_match:
                yca_number = yca_match.group(1)
                fallback_patterns = [f"YCA{yca_number}", yca_number]

                for pattern in fallback_patterns:
                    try:
                        xpath = f"//a[contains(@href, '{pattern}') or contains(text(), '{pattern}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            self.logger.info(f"✅ Correspondance trouvée avec fallback: '{pattern}'")
                            return elements[0]
                    except:
                        continue

            self.logger.warning(f"❌ Aucune correspondance YCA trouvée pour: {yca_code}")
            return None

        except Exception as e:
            self.logger.error(f"Erreur dans _find_by_yca_code: {e}")
            return None

    def _find_by_partial_match(self, file_name, litho_code, pdf_description=""):
        """Recherche par correspondance partielle (8 premiers caractères)"""
        try:
            if len(file_name) >= 8:
                partial_name = file_name[:8]
                xpath = f"//a[starts-with(@href, '{partial_name}') or starts-with(text(), '{partial_name}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)
                return elements[0] if elements else None
            return None
        except Exception:
            return None

    def _find_by_flexible_number(self, file_name, litho_code, pdf_description=""):
        """Recherche flexible par numéros dans le nom"""
        try:
            # Extraire tous les numéros du nom de fichier
            numbers = re.findall(r'\d+', file_name)

            for number in numbers:
                if len(number) >= 4:  # Chercher des numéros significatifs
                    xpath = f"//a[contains(@href, '{number}') or contains(text(), '{number}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)

                    # Vérifier que c'est bien le bon fichier
                    for element in elements:
                        try:
                            href = element.get_attribute('href') or ''
                            text = element.text or ''

                            if (number in href or number in text) and (
                                'pdf' in href.lower() or 'pdf' in text.lower() or
                                element.get_attribute('class') and 'file' in element.get_attribute('class')
                            ):
                                return element
                        except:
                            continue

            return None
        except Exception:
            return None

    def _find_by_similarity(self, file_name, litho_code, pdf_description=""):
        """Recherche par similarité de texte"""
        try:
            # Récupérer tous les liens/fichiers potentiels
            potential_files = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(text(), '.pdf')]")

            if not potential_files:
                # Chercher d'autres éléments de fichier
                potential_files = self.driver.find_elements(By.XPATH, "//a[@href]")

            best_match = None
            best_ratio = 0.6  # Seuil minimum de similarité

            for element in potential_files:
                try:
                    href = element.get_attribute('href') or ''
                    text = element.text or ''

                    # Calculer similarité avec href et text
                    href_ratio = SequenceMatcher(None, file_name.lower(), href.lower()).ratio()
                    text_ratio = SequenceMatcher(None, file_name.lower(), text.lower()).ratio()

                    max_ratio = max(href_ratio, text_ratio)

                    if max_ratio > best_ratio:
                        best_ratio = max_ratio
                        best_match = element

                except:
                    continue

            if best_match:
                self.logger.info(f"Correspondance par similarité: {best_ratio:.2f}")
                return best_match

            return None
        except Exception:
            return None

    def count_visible_files(self):
        """Compte le nombre de fichiers visibles sur la page"""
        try:
            # Chercher différents sélecteurs possibles pour les fichiers
            selectors = [
                "div[data-behavior='file_preview']",
                ".recording",
                ".attachment",
                "[class*='file']",
                "[data-file-id]",
                "a[href*='.pdf']"
            ]

            max_count = 0
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    count = len(elements)
                    if count > max_count:
                        max_count = count
                except:
                    continue

            return max_count
        except Exception as e:
            self.logger.debug(f"Erreur comptage fichiers: {e}")
            return 0

    def wait_for_page_load(self, timeout=10):
        """Attend que la page soit complètement chargée"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(0.5)  # Petit délai supplémentaire pour la stabilité
        except Exception as e:
            self.logger.debug(f"Timeout attente chargement page: {e}")