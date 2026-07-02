# core/basecamp_processor.py
import time
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

class BasecampProcessor:
    def __init__(self, session_manager=None, pdf_processor=None):
        self.driver = None
        self.wait = None
        self.session_manager = session_manager
        self.pdf_processor = pdf_processor
        self.current_user = None
        self.start_time = None

        # Configuration du logging
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self, headless=False):
        """Configure et initialise le driver Edge avec options avancées"""
        try:
            edge_options = Options()

            # Options pour une expérience plus naturelle et stable
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--disable-features=VizDisplayCompositor")

            if headless:
                edge_options.add_argument("--headless")

            self.driver = webdriver.Edge(options=edge_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, 20)

            self.logger.info("✅ Driver Edge initialisé avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation du driver: {e}")
            return False
    
    def get_current_user_name(self):
        """Récupère le nom de l'utilisateur connecté à Basecamp"""
        try:
            # Essayer de récupérer depuis les meta tags
            meta_user = self.driver.find_element(By.CSS_SELECTOR, "meta[name='current-person-name']")
            if meta_user:
                self.current_user = meta_user.get_attribute('content')
                self.logger.info(f"✅ Utilisateur connecté détecté: {self.current_user}")
                return self.current_user
        except:
            pass

        # Valeur par défaut
        self.current_user = "Thomas Silliard"
        self.logger.info(f"🔧 Utilisateur par défaut: {self.current_user}")
        return self.current_user

    def wait_for_user_ready(self, project_url=None):
        """Attend que l'utilisateur soit connecté et configure l'environnement"""
        try:
            # URLs de connexion Basecamp
            login_urls = [
                "https://launchpad.37signals.com/signin",
                "https://3.basecamp.com/signin",
                "https://basecamp.com/signin"
            ]

            # Essayer d'ouvrir Basecamp
            for url in login_urls:
                try:
                    self.logger.info(f"🌐 Tentative d'ouverture: {url}")
                    self.driver.get(url)
                    time.sleep(2)
                    break
                except Exception as e:
                    self.logger.warning(f"Impossible d'ouvrir {url}: {e}")
                    continue

            self.logger.info("⏸️ En attente de la connexion utilisateur...")

            # Détecter l'utilisateur connecté
            self.get_current_user_name()

            # Navigation vers le projet si fourni
            if project_url:
                self.logger.info(f"🌐 Navigation vers le projet: {project_url}")
                self.driver.get(project_url)
                self.wait_for_page_load()

            # Optimiser le chargement de la page
            self.optimized_scroll_to_load_more_files()

            # Initialiser le timer
            self.start_time = datetime.now()

            self.logger.info("✅ Configuration Basecamp terminée")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la configuration Basecamp: {e}")
            return False
    
    def wait_for_page_load(self, timeout=10):
        """Attend que la page soit complètement chargée"""
        try:
            # Attendre que jQuery soit prêt (si utilisé)
            self.wait.until(lambda driver: driver.execute_script("return jQuery.active == 0") if driver.execute_script("return typeof jQuery !== 'undefined'") else True)
        except:
            pass

        try:
            # Attendre que le document soit prêt
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except:
            pass

        time.sleep(0.5)

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
            initial_files = self.count_visible_files()
            self.logger.info(f"📁 Fichiers initialement visibles: {initial_files}")

            while scroll_count < max_scrolls and stable_count < max_stable:
                # Scroll progressif
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(0.4)  # Temps d'attente plus long

                # Vérifier les changements
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                current_files = self.count_visible_files()

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
            final_files = self.count_visible_files()
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

    def count_visible_files(self):
        """Compte le nombre de fichiers visibles sur la page"""
        try:
            # Chercher différents sélecteurs possibles pour les fichiers
            selectors = [
                "div[data-behavior='file_preview']",
                ".recording",
                ".attachment",
                "[class*='file']",
                "[data-file-id]"
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

    def process_approved_lithos(self):
        """Traite toutes les lithographies approuvées depuis le session_manager avec reporting détaillé"""
        if not self.session_manager:
            self.logger.error("❌ Session manager non disponible")
            return self.create_detailed_report({"success": 0, "errors": 0, "skipped": 0, "not_found": 0}, [])

        approved_lithos = self.session_manager.get_approved_lithos()

        if not approved_lithos:
            self.logger.warning("⚠️ Aucune lithographie approuvée à traiter")
            return self.create_detailed_report({"success": 0, "errors": 0, "skipped": 0, "not_found": 0}, [])

        self.logger.info(f"🚀 Début du traitement de {len(approved_lithos)} lithographies approuvées")

        # Initialiser le rapport détaillé
        results = {"success": 0, "errors": 0, "skipped": 0, "not_found": 0}
        detailed_log = []
        session_start = datetime.now()

        for i, litho_code in enumerate(approved_lithos, 1):
            self.logger.info(f"📁 [{i}/{len(approved_lithos)}] Traitement de {litho_code}")

            # Initialiser le log détaillé pour ce fichier
            file_start_time = datetime.now()
            file_log_entry = {
                'litho_code': litho_code,
                'index': i,
                'total': len(approved_lithos),
                'start_time': file_start_time,
                'file_found': False,
                'comment_added': False,
                'error_type': None,
                'matching_strategy': None,
                'user_comment': '',
                'basecamp_url': '',
                'processing_time': 0
            }

            try:
                # Récupérer les informations de la lithographie
                litho_status = self.session_manager.get_litho_status(litho_code)
                comment = litho_status.get('comment', '') if litho_status else ''
                file_log_entry['user_comment'] = comment

                # Convertir le code litho en nom de fichier
                file_name = f"{litho_code}.pdf"

                # Traiter le fichier avec logging détaillé
                result, processing_details = self.process_file_with_details(file_name, litho_code, comment)

                # Enrichir le log avec les détails de traitement
                file_log_entry.update(processing_details)

                # Comptabiliser les résultats
                if result in results:
                    results[result] += 1
                else:
                    results["errors"] += 1
                    file_log_entry['error_type'] = 'unknown_result'

            except Exception as e:
                self.logger.error(f"Erreur traitement {litho_code}: {e}")
                results["errors"] += 1
                file_log_entry['error_type'] = 'processing_exception'
                file_log_entry['error_message'] = str(e)

            finally:
                # Finaliser le temps de traitement
                file_end_time = datetime.now()
                file_log_entry['end_time'] = file_end_time
                file_log_entry['processing_time'] = (file_end_time - file_start_time).total_seconds()

                # Ajouter au log détaillé
                detailed_log.append(file_log_entry)

            # Retour à la liste pour le fichier suivant
            if i < len(approved_lithos):
                try:
                    self.navigate_back_to_files()
                except Exception as e:
                    self.logger.warning(f"Erreur retour à la liste: {e}")

        # Finaliser le rapport
        session_end = datetime.now()
        total_duration = (session_end - session_start).total_seconds()

        self.logger.info(f"🎉 Traitement terminé en {total_duration:.1f}s: {results}")
        return self.create_detailed_report(results, detailed_log)

    def process_file_with_details(self, file_name, litho_code, comment="", status="approved", force_comment=False):
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

            # Rechercher le fichier avec stratégies avancées
            element = self.find_file_by_advanced_matching(file_name, litho_code)
            details['navigation_attempts'] += 1

            if element:
                details['file_found'] = True
                details['matching_strategy'] = getattr(element, '_matching_strategy', 'unknown')

                # Compter les fichiers sur la page pour statistiques
                details['file_elements_count'] = self.count_visible_files()

                # Cliquer sur le fichier
                element.click()
                self.wait_for_page_load()

                # Vérifier les commentaires existants
                comment_check = self.check_existing_comments(force_comment)
                details['existing_comments'] = comment_check.get('existing_comments', [])

                if comment_check['skip_file']:
                    self.logger.info(f"⏭️ Fichier ignoré: {comment_check['reason']}")
                    return "skipped", details

                # Préparer et ajouter le commentaire
                comment_text = self.prepare_comment(status, comment)
                if self.add_intelligent_comment(comment_text, status):
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

    def process_file(self, file_name, litho_code, comment="", status="approved", force_comment=False):
        """Traite un fichier spécifique avec gestion intelligente des commentaires (version simple)"""
        result, _ = self.process_file_with_details(file_name, litho_code, comment, status, force_comment)
        return result

    def process_file_legacy(self, file_name, litho_code, comment="", status="approved", force_comment=False):
        """Version originale du traitement de fichier (conservée pour compatibilité)"""
        try:
            if not self.check_window_status():
                return "error"

            self.logger.info(f"🔍 Traitement de {file_name} (Code: {litho_code}, Statut: {status})")

            # Utiliser la recherche avancée avec multiples stratégies
            file_element = self.find_file_by_advanced_matching(file_name, litho_code)

            if not file_element:
                self.logger.warning(f"❌ Fichier {file_name} non trouvé dans Basecamp")
                return "not_found"

            # Ouvrir le fichier
            self.logger.info(f"🖱️ Ouverture du fichier {file_name}")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", file_element)
            time.sleep(0.8)

            if not self.check_window_status():
                return "error"

            self.driver.execute_script("arguments[0].click();", file_element)
            self.logger.info(f"✅ Fichier {file_name} ouvert avec succès")

            # Attendre le chargement complet
            self.wait_for_page_load()
            time.sleep(1)  # Attente supplémentaire pour le chargement des commentaires

            # Vérifier les commentaires existants avec logique intelligente
            comment_status = self.check_existing_comments_intelligent(force_comment)

            if comment_status['skip_file']:
                self.logger.info(f"⏭️ Fichier {file_name} ignoré: {comment_status['reason']}")
                return "skipped"

            # Préparer le commentaire selon le statut
            comment_text = self.prepare_comment(status, comment)

            # Ajouter le commentaire
            if self.add_intelligent_comment(comment_text, status):
                self.logger.info(f"✅ Commentaire {status} ajouté avec succès pour {file_name}")
                return "success"
            else:
                self.logger.error(f"❌ Erreur lors de l'ajout du commentaire pour {file_name}")
                return "error"

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement de {file_name}: {e}")
            return "error"

    def check_existing_comments_intelligent(self, force_comment=False):
        """Vérification intelligente des commentaires existants"""
        try:
            self.logger.info("🔍 Vérification intelligente des commentaires...")
            self.wait_for_page_load()

            # Patterns d'approbation et de rejet étendus
            approval_patterns = [
                r"✅\s*APPROVED", r"APPROVED", r"approuvé", r"approved",
                r"✓\s*APPROVED", r"👍\s*APPROVED", r"✅\s*approuvé",
                r"OK", r"Validé", r"Validated", r"Accepté", r"Accepted"
            ]

            rejection_patterns = [
                r"❌\s*REJECTED", r"REJECTED", r"rejeté", r"rejected",
                r"NOT\s+APPROVED", r"REFUSED", r"refusé", r"DENIED",
                r"TO\s+MODIFY", r"à\s+modifier", r"CHANGES\s+NEEDED"
            ]

            comment_articles = self.driver.find_elements(By.CSS_SELECTOR, "article.thread-entry.recording[data-type='comment']")

            results = {
                'skip_file': False,
                'reason': '',
                'approval_found': False,
                'rejection_found': False,
                'user_already_commented': False,
                'other_users_approved': [],
                'other_users_rejected': []
            }

            for article in comment_articles:
                try:
                    if not article.is_displayed():
                        continue

                    # Extraire l'auteur
                    author_element = article.find_element(By.CSS_SELECTOR, ".thread-entry__author strong")
                    comment_author = author_element.text.strip() if author_element else ""

                    # Extraire le contenu
                    content_element = article.find_element(By.CSS_SELECTOR, ".thread-entry__content.formatted_content")
                    comment_text = content_element.text.strip() if content_element else ""

                    if not comment_text:
                        continue

                    # Vérifier les approbations
                    for pattern in approval_patterns:
                        if re.search(pattern, comment_text, re.IGNORECASE):
                            results['approval_found'] = True

                            # Vérifier si c'est l'utilisateur actuel
                            if (self.current_user and comment_author and
                                (self.current_user.lower() in comment_author.lower() or
                                 comment_author.lower() in self.current_user.lower())):
                                results['user_already_commented'] = True
                                if not force_comment:
                                    results['skip_file'] = True
                                    results['reason'] = "Déjà approuvé par vous"
                            else:
                                results['other_users_approved'].append(comment_author)
                            break

                    # Vérifier les rejets
                    for pattern in rejection_patterns:
                        if re.search(pattern, comment_text, re.IGNORECASE):
                            results['rejection_found'] = True

                            if (self.current_user and comment_author and
                                (self.current_user.lower() in comment_author.lower() or
                                 comment_author.lower() in self.current_user.lower())):
                                results['user_already_commented'] = True
                                if not force_comment:
                                    results['skip_file'] = True
                                    results['reason'] = "Déjà rejeté par vous"
                            else:
                                results['other_users_rejected'].append(comment_author)
                            break

                except Exception as e:
                    self.logger.debug(f"Erreur analyse commentaire: {e}")
                    continue

            # Logique de décision
            if not force_comment:
                if results['approval_found'] and len(results['other_users_approved']) > 0:
                    # Fichier déjà approuvé par d'autres
                    self.logger.info(f"Fichier déjà approuvé par: {', '.join(results['other_users_approved'])}")
                    # On peut choisir de l'ignorer ou de continuer selon la configuration

                if results['rejection_found'] and len(results['other_users_rejected']) > 0:
                    self.logger.info(f"Fichier déjà rejeté par: {', '.join(results['other_users_rejected'])}")

            return results

        except Exception as e:
            self.logger.error(f"Erreur vérification commentaires: {e}")
            return {'skip_file': False, 'reason': 'Erreur vérification', 'approval_found': False, 'rejection_found': False, 'user_already_commented': False}

    def prepare_comment(self, status, user_comment=""):
        """Prépare le texte du commentaire selon le statut et la configuration"""
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        if status == "approved":
            base_text = "APPROVED"
            if user_comment.strip():
                comment_text = f"{base_text}\n\n{user_comment.strip()}"
            else:
                comment_text = base_text

        elif status == "rejected":
            base_text = "REJECTED"
            if user_comment.strip():
                comment_text = f"{base_text}: {user_comment.strip()}"
            else:
                comment_text = f"{base_text}: Nécessite des modifications"

        else:
            # Statut personnalisé
            comment_text = user_comment.strip() if user_comment.strip() else "Commentaire ajouté"

        # Ajouter signature automatique si configuré
        comment_text += f"\n\n--- Ajouté automatiquement via Litho Validator le {timestamp} ---"

        return comment_text

    def add_intelligent_comment(self, comment_text, status="approved"):
        """Ajoute un commentaire avec gestion intelligente"""
        try:
            self.logger.info(f"📝 Ajout commentaire {status}: '{comment_text[:50]}...'")

            # Scroll vers la zone de commentaires
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Activer l'éditeur avec retry
            trix_editor = None
            max_retries = 3

            for attempt in range(max_retries):
                trix_editor = self.activate_trix_editor()
                if trix_editor:
                    break

                self.logger.warning(f"Tentative {attempt + 1}/{max_retries} d'activation de l'éditeur")
                time.sleep(1)

            if not trix_editor:
                self.logger.error("❌ Impossible d'activer l'éditeur après plusieurs tentatives")
                return False

            # Écrire le commentaire avec retry
            for attempt in range(max_retries):
                if self.write_to_trix_editor(trix_editor, comment_text):
                    break

                self.logger.warning(f"Tentative {attempt + 1}/{max_retries} d'écriture")
                time.sleep(0.5)
            else:
                self.logger.error("❌ Échec de l'écriture après plusieurs tentatives")
                return False

            # Soumettre avec retry
            for attempt in range(max_retries):
                if self.find_and_click_submit_button():
                    self.logger.info("✅ Commentaire soumis avec succès")
                    return True

                self.logger.warning(f"Tentative {attempt + 1}/{max_retries} de soumission")
                time.sleep(1)

            self.logger.error("❌ Échec de la soumission après plusieurs tentatives")
            return False

        except Exception as e:
            self.logger.error(f"Erreur ajout commentaire intelligent: {e}")
            return False
    
    def find_file_by_advanced_matching(self, file_name, litho_code, pdf_description=""):
        """Recherche avancée avec multiples stratégies de correspondance"""
        try:
            self.logger.info(f"🎯 Recherche avancée pour: {file_name} (Code: {litho_code})")

            # Récupérer tous les fichiers PDF de la page
            pdf_files = self.get_all_pdf_files()

            if not pdf_files:
                self.logger.warning("❌ Aucun fichier PDF trouvé sur la page")
                return None

            self.logger.info(f"📊 {len(pdf_files)} fichiers PDF détectés sur la page")

            # Stratégie 1: Correspondance exacte par nom
            match = self.exact_name_matching(pdf_files, file_name, litho_code)
            if match:
                self.logger.info(f"✅ Correspondance exacte trouvée: {match['text']}")
                return match['element']

            # Stratégie 2: Correspondance par code YCA
            match = self.yca_code_matching(pdf_files, litho_code)
            if match:
                self.logger.info(f"✅ Correspondance YCA trouvée: {match['text']}")
                return match['element']

            # Stratégie 3: Correspondance par 8 premiers caractères
            match = self.partial_matching(pdf_files, litho_code)
            if match:
                self.logger.info(f"✅ Correspondance partielle trouvée: {match['text']}")
                return match['element']

            # Stratégie 4: Correspondance flexible par numéros
            match = self.flexible_number_matching(pdf_files, litho_code)
            if match:
                self.logger.info(f"✅ Correspondance numérique trouvée: {match['text']}")
                return match['element']

            # Stratégie 5: Correspondance par similarité (fuzzy matching)
            match = self.similarity_matching(pdf_files, litho_code, file_name)
            if match:
                self.logger.info(f"✅ Correspondance par similarité trouvée: {match['text']} (score: {match.get('score', 'N/A')})")
                return match['element']

            # Aucune correspondance automatique trouvée
            self.logger.warning(f"❌ Aucune correspondance automatique pour {file_name}")

            # Proposer une correspondance manuelle
            manual_match = self.propose_manual_matching(pdf_files, litho_code, file_name)
            if manual_match:
                return manual_match['element']

            return None

        except Exception as e:
            self.logger.error(f"Erreur recherche avancée: {e}")
            return None

    def get_all_pdf_files(self):
        """Récupère tous les fichiers PDF de la page avec leurs métadonnées"""
        try:
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            pdf_files = []

            for link in all_links:
                if not link.is_displayed():
                    continue

                link_text = link.text.strip()
                link_href = link.get_attribute('href') or ""
                link_title = link.get_attribute('title') or ""

                # Filtrer les liens PDF
                if ('.pdf' in link_text.lower() or
                    '.pdf' in link_href.lower() or
                    '.pdf' in link_title.lower()):

                    pdf_files.append({
                        'element': link,
                        'text': link_text,
                        'href': link_href,
                        'title': link_title,
                        'combined': f"{link_text} {link_href} {link_title}".upper()
                    })

            return pdf_files

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des fichiers PDF: {e}")
            return []

    def exact_name_matching(self, pdf_files, file_name, litho_code):
        """Stratégie 1: Correspondance exacte par nom de fichier"""
        self.logger.debug(f"🎯 Stratégie 1: Correspondance exacte pour {file_name}")

        search_terms = [
            file_name,  # YCA12345.pdf
            file_name.replace('.pdf', ''),  # YCA12345
            litho_code  # YCA12345
        ]

        for pdf_file in pdf_files:
            for term in search_terms:
                if term.lower() in pdf_file['text'].lower():
                    return pdf_file
                if term.lower() in pdf_file['href'].lower():
                    return pdf_file

        return None

    def yca_code_matching(self, pdf_files, litho_code):
        """Stratégie 2: Correspondance par code YCA"""
        self.logger.debug(f"🎯 Stratégie 2: Correspondance YCA pour {litho_code}")

        # Extraire le code YCA si possible
        yca_match = re.search(r'(YCA\d{5})', litho_code.upper())
        if not yca_match:
            return None

        yca_code = yca_match.group(1)

        for pdf_file in pdf_files:
            if yca_code in pdf_file['combined']:
                return pdf_file

        return None

    def partial_matching(self, pdf_files, litho_code):
        """Stratégie 3: Correspondance par 8 premiers caractères"""
        self.logger.debug(f"🎯 Stratégie 3: Correspondance partielle pour {litho_code}")

        if len(litho_code) < 8:
            return None

        partial_code = litho_code[:8].upper()

        for pdf_file in pdf_files:
            if partial_code in pdf_file['combined']:
                return pdf_file

        return None

    def flexible_number_matching(self, pdf_files, litho_code):
        """Stratégie 4: Correspondance flexible par numéros"""
        self.logger.debug(f"🎯 Stratégie 4: Correspondance numérique pour {litho_code}")

        # Extraire tous les numéros du code litho
        numbers = re.findall(r'\d+', litho_code)

        for number in numbers:
            if len(number) >= 4:  # Seulement les numéros significatifs
                for pdf_file in pdf_files:
                    if number in pdf_file['combined'] and 'PDF' in pdf_file['combined']:
                        return pdf_file

        return None

    def similarity_matching(self, pdf_files, litho_code, file_name):
        """Stratégie 5: Correspondance par similarité (fuzzy matching)"""
        self.logger.debug(f"🎯 Stratégie 5: Correspondance par similarité pour {litho_code}")

        best_match = None
        best_score = 0
        min_similarity = 0.7  # Seuil de similarité minimum

        search_terms = [litho_code.upper(), file_name.upper().replace('.PDF', '')]

        for pdf_file in pdf_files:
            file_text = pdf_file['text'].upper()

            for term in search_terms:
                # Calcul de similarité simple (ratio de caractères communs)
                similarity = self.calculate_similarity(term, file_text)

                if similarity > best_score and similarity >= min_similarity:
                    best_score = similarity
                    best_match = pdf_file
                    best_match['score'] = similarity

        return best_match

    def calculate_similarity(self, str1, str2):
        """Calcule un score de similarité simple entre deux chaînes"""
        if not str1 or not str2:
            return 0

        # Recherche de sous-chaînes communes
        common_chars = 0
        str1_chars = set(str1)
        str2_chars = set(str2)

        common_chars = len(str1_chars.intersection(str2_chars))
        total_chars = len(str1_chars.union(str2_chars))

        if total_chars == 0:
            return 0

        return common_chars / total_chars

    def propose_manual_matching(self, pdf_files, litho_code, file_name):
        """Propose une correspondance manuelle à l'utilisateur"""
        self.logger.info(f"👤 Recherche manuelle nécessaire pour {file_name}")

        # Pour l'instant, on peut implanter une logique simple
        # Dans une version plus avancée, on pourrait ouvrir un dialogue
        # ou demander à l'utilisateur via l'interface

        # Proposer les 3 fichiers les plus probables
        candidates = []

        for pdf_file in pdf_files[:10]:  # Limiter aux 10 premiers
            # Calculer un score basé sur la présence de numéros ou caractères similaires
            score = 0
            file_text = pdf_file['text'].upper()
            litho_upper = litho_code.upper()

            # Recherche de numéros communs
            litho_numbers = set(re.findall(r'\d+', litho_upper))
            file_numbers = set(re.findall(r'\d+', file_text))

            if litho_numbers.intersection(file_numbers):
                score += 0.5

            # Recherche de lettres communes
            if any(char in file_text for char in ['YCA', 'LITHO']):
                score += 0.3

            if score > 0:
                candidates.append((pdf_file, score))

        # Trier par score et retourner le meilleur candidat s'il existe
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_candidate = candidates[0][0]

            self.logger.info(f"🤔 Meilleur candidat proposé: {best_candidate['text']} (score: {candidates[0][1]})")

            # Pour l'instant, on accepte automatiquement si le score est raisonnable
            if candidates[0][1] >= 0.5:
                return best_candidate

        return None

    def find_file_by_yca_code(self, file_name, litho_code):
        """Méthode de compatibilité - utilise la nouvelle recherche avancée"""
        return self.find_file_by_advanced_matching(file_name, litho_code)

    def check_window_status(self):
        """Vérifie que la fenêtre du navigateur est toujours active"""
        try:
            self.driver.current_url
            return True
        except WebDriverException as e:
            if "no such window" in str(e).lower():
                self.logger.error("❌ La fenêtre du navigateur a été fermée")
                return False
            return True
    
    def check_existing_comments_precise(self):
        """Vérification précise des commentaires existants"""
        try:
            self.logger.info("🔍 Vérification des commentaires existants...")
            self.wait_for_page_load()

            # Patterns d'approbation
            approval_patterns = [
                r"✅\s*APPROVED", r"APPROVED", r"approuvé", r"approved",
                r"✓\s*APPROVED", r"👍\s*APPROVED", r"✅\s*approuvé", r"OK", r"Validé"
            ]

            # Sélecteurs pour les commentaires Basecamp
            comment_articles = self.driver.find_elements(By.CSS_SELECTOR, "article.thread-entry.recording[data-type='comment']")

            approval_found = False
            user_already_approved = False

            for article in comment_articles:
                try:
                    if not article.is_displayed():
                        continue

                    # Extraire l'auteur du commentaire
                    author_element = article.find_element(By.CSS_SELECTOR, ".thread-entry__author strong")
                    comment_author = author_element.text.strip() if author_element else ""

                    # Extraire le contenu du commentaire
                    content_element = article.find_element(By.CSS_SELECTOR, ".thread-entry__content.formatted_content")
                    comment_text = content_element.text.strip() if content_element else ""

                    if not comment_text:
                        continue

                    # Vérifier si le commentaire contient une approbation
                    for pattern in approval_patterns:
                        if re.search(pattern, comment_text, re.IGNORECASE):
                            approval_found = True
                            self.logger.info(f"📝 Approbation trouvée par {comment_author}")

                            # Vérifier si c'est l'utilisateur actuel qui a déjà approuvé
                            if (self.current_user and comment_author and
                                (self.current_user.lower() in comment_author.lower() or
                                 comment_author.lower() in self.current_user.lower())):
                                user_already_approved = True
                                self.logger.warning(f"⚠️ Vous avez déjà approuvé ce fichier !")
                            break

                except Exception as e:
                    self.logger.debug(f"Erreur lors de l'analyse d'un commentaire: {e}")
                    continue

            return {
                'approval_found': approval_found,
                'user_already_approved': user_already_approved
            }

        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des commentaires: {e}")
            return {'approval_found': False, 'user_already_approved': False}
    
    def add_approval_comment(self, comment=""):
        """Méthode de compatibilité - utilise la nouvelle logique intelligente"""
        comment_text = self.prepare_comment("approved", comment)
        return self.add_intelligent_comment(comment_text, "approved")

    def activate_trix_editor(self):
        """Active l'éditeur Trix de Basecamp"""
        try:
            self.logger.info("🎯 Activation de l'éditeur de commentaires...")

            # Boutons d'activation possibles
            expand_selectors = [
                "button[data-behavior='expand_on_click']",
                "button.prompt",
                "//button[contains(text(), 'Add a comment here')]",
                ".collapsed_content button"
            ]

            expand_button = None
            for i, selector in enumerate(expand_selectors, 1):
                try:
                    if selector.startswith("//"):
                        expand_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        expand_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if expand_button.is_displayed():
                        self.logger.info(f"✅ Bouton d'activation trouvé (méthode {i})")
                        break
                except:
                    continue

            if expand_button:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", expand_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", expand_button)
                self.logger.info("✅ Formulaire de commentaire activé")
                time.sleep(1.5)

            # Trouver l'éditeur Trix
            trix_selectors = [
                "trix-editor#comment_content",
                "trix-editor[placeholder*='Type your comment here']",
                "trix-editor",
                "#comment_content"
            ]

            trix_editor = None
            for i, selector in enumerate(trix_selectors, 1):
                try:
                    trix_editor = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if trix_editor.is_displayed():
                        self.logger.info(f"✅ Éditeur Trix trouvé (méthode {i})")
                        break
                except:
                    continue

            if not trix_editor:
                self.logger.error("❌ Éditeur Trix non trouvé")
                return None

            # Activer l'éditeur
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", trix_editor)
            time.sleep(0.3)
            trix_editor.click()
            time.sleep(0.3)

            self.logger.info("✅ Éditeur Trix activé et prêt")
            return trix_editor

        except Exception as e:
            self.logger.error(f"Erreur lors de l'activation de l'éditeur: {e}")
            return None

    def write_to_trix_editor(self, trix_editor, text):
        """Écrit du texte dans l'éditeur Trix avec méthodes multiples"""
        try:
            self.logger.info(f"✏️ Écriture du commentaire: '{text}'")

            # Méthode 1: Clear + Send keys
            try:
                trix_editor.clear()
                trix_editor.click()
                time.sleep(0.2)
                trix_editor.send_keys(text)
                time.sleep(0.3)

                content = trix_editor.get_attribute('textContent') or ""
                if "APPROVED" in content:
                    self.logger.info("✅ Commentaire écrit avec succès (Clear + Send keys)")
                    return True
            except Exception as e:
                self.logger.debug(f"Méthode 1 échouée: {e}")

            # Méthode 2: API Trix directe
            try:
                escaped_text = text.replace("'", "\\'")
                script = f"""
                var editor = arguments[0].editor;
                if (editor) {{
                    editor.setSelectedRange([0, 0]);
                    editor.deleteInDirection('backward');
                    editor.insertString('{escaped_text}');
                }}
                """
                self.driver.execute_script(script, trix_editor)
                time.sleep(0.5)

                content = trix_editor.get_attribute('textContent') or ""
                if "APPROVED" in content:
                    self.logger.info("✅ Commentaire écrit avec succès (API Trix)")
                    return True
            except Exception as e:
                self.logger.debug(f"Méthode 2 échouée: {e}")

            self.logger.error("❌ Toutes les méthodes d'écriture ont échoué")
            return False

        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture: {e}")
            return False

    def find_and_click_submit_button(self):
        """Trouve et clique sur le bouton de soumission"""
        try:
            self.logger.info("🎯 Recherche du bouton de soumission...")

            submit_selectors = [
                "input[value='Add this comment']",
                "input[type='submit'][value*='Add this comment']",
                ".btn--primary[value*='Add this comment']",
                "input.btn--primary[type='submit']",
                "//input[@value='Add this comment']"
            ]

            submit_button = None
            for i, selector in enumerate(submit_selectors, 1):
                try:
                    if selector.startswith("//"):
                        submit_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if submit_button.is_displayed():
                        self.logger.info(f"✅ Bouton trouvé (méthode {i})")
                        break
                except:
                    continue

            if not submit_button:
                self.logger.error("❌ Bouton de soumission non trouvé")
                return False

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
            time.sleep(0.3)

            try:
                submit_button.click()
                self.logger.info("✅ Commentaire soumis avec succès")
            except:
                self.driver.execute_script("arguments[0].click();", submit_button)
                self.logger.info("✅ Commentaire soumis avec JavaScript")

            time.sleep(1.5)
            self.logger.info("✅ Commentaire publié")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la soumission: {e}")
            return False
    
    def navigate_back_to_files(self):
        """Retourne à la liste des fichiers avec méthodes multiples"""
        try:
            if not self.check_window_status():
                return False

            self.logger.info("🔙 Retour à la liste des fichiers...")

            # Méthodes de retour
            back_methods = [
                ("Bouton retour", lambda: self.driver.back()),
                ("Lien breadcrumb", lambda: self.driver.find_element(By.XPATH, "//a[contains(text(), 'Lithos')]").click()),
                ("Navigation breadcrumb", lambda: self.driver.find_element(By.CSS_SELECTOR, ".breadcrumb a, nav a").click())
            ]

            for method_name, method in back_methods:
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
    
    def create_detailed_report(self, results, detailed_log):
        """Crée un rapport détaillé avec traçabilité complète"""
        try:
            # Informations de session
            session_info = {
                'start_time': getattr(self, 'start_time', datetime.now()),
                'end_time': datetime.now(),
                'total_processed': sum(results.values()),
                'success_rate': (results['success'] / sum(results.values()) * 100) if sum(results.values()) > 0 else 0
            }

            session_info['duration'] = (session_info['end_time'] - session_info['start_time']).total_seconds()

            # Rapport enrichi
            detailed_report = {
                'summary': results,
                'session_info': session_info,
                'detailed_log': detailed_log,
                'timestamp': datetime.now().isoformat(),
                'browser_info': self.get_browser_info(),
                'statistics': self.calculate_statistics(detailed_log),
                'recommendations': self.generate_recommendations(results, detailed_log)
            }

            # Sauvegarder le rapport si configuré
            if hasattr(self, 'save_reports') and self.save_reports:
                self.save_report_to_file(detailed_report)

            self.logger.info(f"📊 Rapport détaillé généré - Succès: {results['success']}, Erreurs: {results['errors']}")
            return detailed_report

        except Exception as e:
            self.logger.error(f"Erreur création rapport détaillé: {e}")
            return {
                'summary': results,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_browser_info(self):
        """Récupère les informations du navigateur pour traçabilité"""
        try:
            if self.driver:
                return {
                    'browser': 'Microsoft Edge',
                    'version': self.driver.capabilities.get('browserVersion', 'Unknown'),
                    'platform': self.driver.capabilities.get('platformName', 'Unknown'),
                    'current_url': self.driver.current_url if hasattr(self.driver, 'current_url') else 'Unknown'
                }
        except:
            pass
        return {'browser': 'Unknown', 'version': 'Unknown', 'platform': 'Unknown'}

    def calculate_statistics(self, detailed_log):
        """Calcule des statistiques avancées sur le traitement"""
        try:
            if not detailed_log:
                return {}

            # Temps de traitement par fichier
            processing_times = []
            matching_strategies = {}
            error_types = {}

            for entry in detailed_log:
                if 'processing_time' in entry:
                    processing_times.append(entry['processing_time'])

                if 'matching_strategy' in entry:
                    strategy = entry['matching_strategy']
                    matching_strategies[strategy] = matching_strategies.get(strategy, 0) + 1

                if 'error_type' in entry:
                    error_type = entry['error_type']
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            stats = {
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'max_processing_time': max(processing_times) if processing_times else 0,
                'min_processing_time': min(processing_times) if processing_times else 0,
                'matching_strategies_used': matching_strategies,
                'error_breakdown': error_types,
                'files_found_ratio': len([e for e in detailed_log if e.get('file_found', False)]) / len(detailed_log) if detailed_log else 0
            }

            return stats

        except Exception as e:
            self.logger.debug(f"Erreur calcul statistiques: {e}")
            return {}

    def generate_recommendations(self, results, detailed_log):
        """Génère des recommandations basées sur les résultats"""
        try:
            recommendations = []

            # Analyser le taux de succès
            total = sum(results.values())
            if total > 0:
                success_rate = results['success'] / total

                if success_rate < 0.7:
                    recommendations.append("Taux de succès faible (<70%). Vérifiez la correspondance des noms de fichiers.")

                if results['not_found'] > total * 0.3:
                    recommendations.append("Beaucoup de fichiers non trouvés. Considérez améliorer les stratégies de correspondance.")

                if results['errors'] > total * 0.2:
                    recommendations.append("Taux d'erreur élevé. Vérifiez la stabilité de la connexion réseau.")

            # Analyser les stratégies de correspondance
            matching_strategies = {}
            for entry in detailed_log:
                if 'matching_strategy' in entry:
                    strategy = entry['matching_strategy']
                    matching_strategies[strategy] = matching_strategies.get(strategy, 0) + 1

            if 'similarity_matching' in matching_strategies:
                if matching_strategies['similarity_matching'] > len(detailed_log) * 0.5:
                    recommendations.append("Usage élevé de correspondance par similarité. Considérez standardiser les noms de fichiers.")

            return recommendations

        except Exception as e:
            self.logger.debug(f"Erreur génération recommandations: {e}")
            return []

    def save_report_to_file(self, detailed_report):
        """Sauvegarde le rapport dans un fichier JSON"""
        try:
            import json
            import os

            # Créer le dossier de rapports s'il n'existe pas
            reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            # Nom de fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"basecamp_report_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)

            # Convertir les objets datetime en string pour JSON
            json_report = self.make_json_serializable(detailed_report)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"📁 Rapport sauvegardé: {filepath}")

        except Exception as e:
            self.logger.error(f"Erreur sauvegarde rapport: {e}")

    def make_json_serializable(self, obj):
        """Convertit les objets non sérialisables en JSON"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self.make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.make_json_serializable(item) for item in obj]
        else:
            return obj

    def cleanup(self):
        """Nettoie les ressources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass