"""
Module de gestion des commentaires pour BaseCamp
Gère la vérification, préparation et ajout de commentaires intelligents
"""

import logging
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseCampCommentManager:
    """Gestionnaire des commentaires BaseCamp avec logique intelligente"""

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)

    def check_existing_comments(self, force_comment=False):
        """
        Vérifie les commentaires existants et détermine s'il faut ajouter un nouveau commentaire

        Args:
            force_comment (bool): Force l'ajout même si déjà commenté

        Returns:
            dict: Informations sur les commentaires existants et décision
        """
        try:
            results = {
                'skip_file': False,
                'reason': '',
                'approval_found': False,
                'rejection_found': False,
                'user_already_commented': False,
                'other_users_approved': [],
                'other_users_rejected': [],
                'existing_comments': []
            }

            # Chercher la section des commentaires
            comment_selectors = [
                ".comments",
                "[data-behavior='comments']",
                ".comment-list",
                ".comment",
                "[class*='comment']"
            ]

            comments_section = None
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        comments_section = elements[0]
                        break
                except:
                    continue

            if not comments_section:
                self.logger.debug("Aucune section de commentaires trouvée")
                return results

            # Analyser les commentaires existants
            try:
                # Chercher tous les commentaires
                comment_elements = comments_section.find_elements(By.XPATH, ".//*[contains(@class, 'comment') or contains(@class, 'message')]")

                for comment in comment_elements:
                    try:
                        comment_text = comment.text.strip().upper()

                        # Extraire l'auteur si possible
                        author = "Utilisateur inconnu"
                        author_elements = comment.find_elements(By.XPATH, ".//*[contains(@class, 'author') or contains(@class, 'name')]")
                        if author_elements:
                            author = author_elements[0].text.strip()

                        # Enregistrer le commentaire
                        results['existing_comments'].append({
                            'author': author,
                            'text': comment_text,
                            'timestamp': datetime.now().isoformat()
                        })

                        # Analyser le contenu
                        if 'APPROVED' in comment_text:
                            results['approval_found'] = True
                            if author not in results['other_users_approved']:
                                results['other_users_approved'].append(author)

                        if 'REJECTED' in comment_text:
                            results['rejection_found'] = True
                            if author not in results['other_users_rejected']:
                                results['other_users_rejected'].append(author)

                        # Vérifier si l'utilisateur actuel a déjà commenté
                        if 'Litho Validator' in comment_text or 'Ajouté automatiquement' in comment_text:
                            results['user_already_commented'] = True

                    except Exception as e:
                        self.logger.debug(f"Erreur analyse commentaire: {e}")
                        continue

            except Exception as e:
                self.logger.debug(f"Erreur analyse commentaires: {e}")

            # Logique de décision
            if not force_comment:
                if results['user_already_commented']:
                    results['skip_file'] = True
                    results['reason'] = "Utilisateur a déjà commenté ce fichier"

                elif results['approval_found'] and len(results['other_users_approved']) > 0:
                    # Fichier déjà approuvé par d'autres
                    self.logger.info(f"Fichier déjà approuvé par: {', '.join(results['other_users_approved'])}")

                elif results['rejection_found'] and len(results['other_users_rejected']) > 0:
                    self.logger.info(f"Fichier déjà rejeté par: {', '.join(results['other_users_rejected'])}")

            return results

        except Exception as e:
            self.logger.error(f"Erreur vérification commentaires: {e}")
            return {
                'skip_file': False,
                'reason': 'Erreur vérification',
                'approval_found': False,
                'rejection_found': False,
                'user_already_commented': False,
                'existing_comments': []
            }

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

        # Ajouter signature automatique
        comment_text += f"\n\n--- Ajouté automatiquement via Litho Validator le {timestamp} ---"

        return comment_text

    def add_intelligent_comment(self, comment_text, status="approved"):
        """Ajoute un commentaire avec gestion intelligente des erreurs"""
        try:
            self.logger.info(f"💬 Ajout commentaire: {status}")

            # Stratégies multiples pour trouver la zone de commentaire
            strategies = [
                self._add_comment_textarea,
                self._add_comment_input,
                self._add_comment_contenteditable,
                self._add_comment_fallback
            ]

            for strategy in strategies:
                try:
                    if strategy(comment_text):
                        self.logger.info("✅ Commentaire ajouté avec succès")
                        return True
                except Exception as e:
                    self.logger.debug(f"Échec stratégie commentaire: {e}")
                    continue

            self.logger.error("❌ Impossible d'ajouter le commentaire")
            return False

        except Exception as e:
            self.logger.error(f"Erreur ajout commentaire: {e}")
            return False

    def _add_comment_textarea(self, comment_text):
        """Stratégie 1: Textarea classique"""
        textarea = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
        textarea.clear()
        textarea.send_keys(comment_text)

        # Chercher le bouton de soumission
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add') or contains(text(), 'Post') or contains(text(), 'Submit')]")
        submit_button.click()
        time.sleep(2)
        return True

    def _add_comment_input(self, comment_text):
        """Stratégie 2: Input text"""
        input_field = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text' and (contains(@placeholder, 'comment') or contains(@class, 'comment'))]"))
        )
        input_field.clear()
        input_field.send_keys(comment_text)

        # Envoyer ou cliquer submit
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'submit') or contains(text(), 'Add')]")
        submit_button.click()
        time.sleep(2)
        return True

    def _add_comment_contenteditable(self, comment_text):
        """Stratégie 3: Div contenteditable"""
        editable_div = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )

        # Cliquer pour focus et entrer le texte
        editable_div.click()
        time.sleep(0.5)
        editable_div.clear()
        editable_div.send_keys(comment_text)

        # Chercher submit
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add') or contains(text(), 'Post')]")
        submit_button.click()
        time.sleep(2)
        return True

    def _add_comment_fallback(self, comment_text):
        """Stratégie 4: Fallback générique"""
        # Chercher n'importe quel champ de saisie
        possible_inputs = self.driver.find_elements(By.XPATH, "//textarea | //input[@type='text'] | //div[@contenteditable='true']")

        for input_elem in possible_inputs:
            try:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_elem.click()
                    time.sleep(0.5)
                    input_elem.clear()
                    input_elem.send_keys(comment_text)

                    # Chercher bouton proche
                    parent = input_elem.find_element(By.XPATH, "./..")
                    buttons = parent.find_elements(By.TAG_NAME, "button")

                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            time.sleep(2)
                            return True

            except Exception:
                continue

        return False

    def scroll_to_comments_section(self):
        """Scroll vers la section commentaires si nécessaire"""
        try:
            # Chercher la section commentaires
            comment_selectors = [
                ".comments",
                "[data-behavior='comments']",
                ".comment-form",
                "textarea",
                "#comment"
            ]

            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", elements[0])
                        time.sleep(0.5)
                        return True
                except:
                    continue

            return False
        except Exception as e:
            self.logger.debug(f"Erreur scroll vers commentaires: {e}")
            return False