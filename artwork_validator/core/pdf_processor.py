# core/pdf_processor.py
import os
import re
import fitz  # PyMuPDF
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import numpy as np
import logging
from typing import Optional
from .brand_configs.base_config import BaseBrandConfig
from .brand_configs.brand_registry import BrandRegistry

class PDFProcessor:
    def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
        """
        Initialise le processeur PDF avec une configuration de marque.

        Args:
            brand_config (Optional[BaseBrandConfig]): Configuration de la marque.
                                                      Si None, utilise MNY par défaut.
        """
        self.current_pdf = None
        self.pdf_files = []
        self.current_index = 0
        self.folder_path = ""
        self.invalid_files = []  # Pour stocker les fichiers avec format incorrect
        self.current_page_index = 0  # Page courante (0 = première page)
        self._thumbnail_cache = {}  # Cache pour les thumbnails: {pdf_file: QPixmap}

        # Configuration du logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # 🆕 Configuration de la marque
        if brand_config is None:
            # Par défaut, utiliser MNY
            brand_config = BrandRegistry.get_brand('MNY')
            if brand_config is None:
                # Fallback si registry pas initialisé
                self.logger.warning("⚠️  BrandRegistry not initialized, using hardcoded MNY config")
                from .brand_configs.mny_config import MNYBrandConfig
                brand_config = MNYBrandConfig()

        self.brand_config = brand_config
        self.logger.info(f"📄 PDFProcessor initialized for: {self.brand_config.get_brand_display_name()}")

        # OCR Processor (lazy loading)
        self._ocr_processor = None
        self.use_ocr_fallback = True  # Activer fallback OCR par défaut

    def set_brand_config(self, brand_config: BaseBrandConfig):
        """
        Change la configuration de marque et recharge les PDFs si un dossier était chargé.

        Args:
            brand_config (BaseBrandConfig): Nouvelle configuration de marque

        Note:
            Si un dossier PDF est actuellement chargé, il sera automatiquement
            rechargé avec les nouvelles règles de validation de la marque.
        """
        old_brand = self.brand_config.get_brand_display_name() if self.brand_config else "None"

        # Sauvegarder le chemin du dossier actuel
        current_folder = self.folder_path

        # Changer la configuration
        self.brand_config = brand_config

        new_brand = brand_config.get_brand_display_name()
        self.logger.info(f"🔄 Configuration changed from {old_brand} to {new_brand}")

        # Recharger le dossier avec la nouvelle configuration
        if current_folder and os.path.exists(current_folder):
            self.logger.info(f"🔄 Reloading PDF folder with {new_brand} configuration...")
            self.load_folder(current_folder)
            self.logger.info(f"✅ PDF folder reloaded for {new_brand}")

    def load_folder(self, folder_path):
        self.folder_path = folder_path
        all_pdf_files = [f for f in os.listdir(folder_path) 
                        if f.endswith('.pdf')]
        
        # Séparer les fichiers valides et invalides
        self.pdf_files = []
        self.invalid_files = []
        
        for pdf_file in all_pdf_files:
            if self._is_valid_filename(pdf_file):
                self.pdf_files.append(pdf_file)
            else:
                self.invalid_files.append(pdf_file)
                self.logger.warning(f"Fichier avec format incorrect détecté: {pdf_file}")
        
        # Log du résumé avec nom de marque
        brand_name = self.brand_config.get_brand_display_name()
        self.logger.info(f"Fichiers PDF trouvés: {len(all_pdf_files)}")
        self.logger.info(f"Fichiers valides ({brand_name}): {len(self.pdf_files)}")
        self.logger.info(f"Fichiers invalides: {len(self.invalid_files)}")
        
        if self.invalid_files:
            self.logger.warning("Fichiers invalides détectés:")
            for invalid_file in self.invalid_files:
                self.logger.warning(f"  - {invalid_file}")
        
        if self.pdf_files:
            self.load_pdf(os.path.join(folder_path, self.pdf_files[0]))
    
    def _is_valid_filename(self, filename):
        """
        🆕 Vérifie si le nom de fichier respecte le format de la marque.

        Utilise la configuration de marque pour valider le format.
        """
        return self.brand_config.is_valid_filename(filename)

    def _extract_litho_code(self, filename):
        """
        🆕 Extrait le code litho du nom de fichier selon la marque.

        Utilise la configuration de marque pour extraire le code.
        """
        return self.brand_config.extract_litho_code(filename)
            
    def load_pdf(self, pdf_path):
        self.current_pdf = fitz.open(pdf_path)
        self.current_page_index = 0  # Réinitialiser à la première page
        
    def get_current_pdf_image(self, page_index=None):
        if not self.current_pdf:
            return None

        # Utiliser la page spécifiée ou la page courante
        if page_index is None:
            page_index = self.current_page_index

        # Vérifier que l'index est valide
        if page_index < 0 or page_index >= len(self.current_pdf):
            return None

        page = self.current_pdf[page_index]
        pix = page.get_pixmap()

        # Conversion en QImage
        img_data = pix.samples
        qim = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qim)
        
    def get_current_text(self):
        if not self.current_pdf:
            return ""
            
        text = ""
        for page in self.current_pdf:
            text += page.get_text()
        return text

    def get_page_count(self):
        """Retourne le nombre total de pages du PDF courant"""
        if not self.current_pdf:
            return 0
        return len(self.current_pdf)

    def get_current_page_index(self):
        """Retourne l'index de la page courante (0-based)"""
        return self.current_page_index

    def next_page(self):
        """Passe à la page suivante. Retourne True si succès, False si déjà à la dernière page"""
        if not self.current_pdf or self.current_page_index >= len(self.current_pdf) - 1:
            return False
        self.current_page_index += 1
        return True

    def previous_page(self):
        """Passe à la page précédente. Retourne True si succès, False si déjà à la première page"""
        if not self.current_pdf or self.current_page_index <= 0:
            return False
        self.current_page_index -= 1
        return True

    def set_page(self, page_index):
        """Définit la page courante. Retourne True si succès, False si index invalide"""
        if not self.current_pdf or page_index < 0 or page_index >= len(self.current_pdf):
            return False
        self.current_page_index = page_index
        return True

    def get_current_litho_code(self):
        if not self.pdf_files:
            return None
        
        filename = self.pdf_files[self.current_index]
        return self._extract_litho_code(filename)
    
    def get_all_litho_codes(self):
        """Retourne tous les codes litho disponibles"""
        litho_codes = []
        for pdf_file in self.pdf_files:
            litho_code = self._extract_litho_code(pdf_file)
            if litho_code and litho_code not in litho_codes:
                litho_codes.append(litho_code)
        return litho_codes
    
    def _get_ocr_processor(self):
        """Lazy loading de l'OCR processor"""
        if self._ocr_processor is None:
            try:
                from .ocr_processor import OCRProcessor
                self._ocr_processor = OCRProcessor(use_gpu=False)
                self.logger.info("OCR Processor initialisé")
            except ImportError:
                self.logger.warning("PaddleOCR non disponible - OCR désactivé")
                self.use_ocr_fallback = False
            except Exception as e:
                self.logger.error(f"Erreur initialisation OCR: {e}")
                self.use_ocr_fallback = False
        return self._ocr_processor

    def get_text_for_litho(self, litho_code, return_method=False):
        """
        Récupère le texte du PDF pour un code litho spécifique.
        Utilise PyMuPDF en priorité, puis OCR si nécessaire (PDFs scannés).

        Args:
            litho_code: Code litho à rechercher
            return_method: Si True, retourne (texte, méthode) au lieu de juste le texte

        Returns:
            str si return_method=False, tuple (str, str) si return_method=True
            méthode peut être: 'pymupdf', 'ocr', 'error', 'none'
        """
        for pdf_file in self.pdf_files:
            file_litho_code = self._extract_litho_code(pdf_file)
            if file_litho_code == litho_code:
                pdf_path = os.path.join(self.folder_path, pdf_file)
                try:
                    pdf_doc = fitz.open(pdf_path)
                    text = ""

                    # Extraire le texte de toutes les pages
                    for page in pdf_doc:
                        text += page.get_text()

                    pdf_doc.close()

                    # Vérifier si le texte extrait est suffisant
                    if len(text.strip()) < 50 and self.use_ocr_fallback:
                        self.logger.info(
                            f"Texte insuffisant extrait ({len(text.strip())} chars) - "
                            f"Basculement vers OCR pour {pdf_file}"
                        )

                        # Utiliser OCR
                        ocr_processor = self._get_ocr_processor()
                        if ocr_processor:
                            ocr_text, method = ocr_processor.extract_text_auto(pdf_path, 0)
                            if method == "ocr" and ocr_text:
                                self.logger.info(f"OCR réussi: {len(ocr_text)} caractères extraits")
                                if return_method:
                                    return ocr_text, "ocr"
                                return ocr_text

                    # Retourner le texte PyMuPDF
                    if return_method:
                        return text, "pymupdf"
                    return text

                except Exception as e:
                    self.logger.error(f"Erreur lors de la lecture du PDF {pdf_file}: {e}")
                    if return_method:
                        return "", "error"
                    return ""

        if return_method:
            return "", "none"
        return ""
    
    def get_invalid_files(self):
        """Retourne la liste des fichiers avec un format incorrect"""
        return self.invalid_files.copy()
    
    def get_validation_report(self):
        """Retourne un rapport détaillé sur la validation des fichiers"""
        report = {
            'total_files': len(self.pdf_files) + len(self.invalid_files),
            'valid_files': len(self.pdf_files),
            'invalid_files': len(self.invalid_files),
            'invalid_file_list': self.invalid_files.copy(),
            'valid_litho_codes': self.get_all_litho_codes()
        }
        return report
    
    def debug_filename_analysis(self, filename):
        """Méthode de debug pour analyser un nom de fichier"""
        print(f"Analyse du fichier: {filename}")
        print(f"Longueur: {len(filename)}")
        
        if len(filename) >= 8:
            first_8 = filename[:8]
            print(f"8 premiers caractères: '{first_8}'")
            print(f"Commence par 'YCA': {first_8.startswith('YCA')}")
            if len(first_8) >= 3:
                print(f"5 derniers caractères: '{first_8[3:]}'")
                print(f"Sont des chiffres: {first_8[3:].isdigit()}")
            print(f"Format valide: {self._is_valid_code_format(first_8)}")
        else:
            print("Fichier trop court (moins de 8 caractères)")
    
    # navigation
    def previous_pdf(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_pdf(os.path.join(self.folder_path, self.pdf_files[self.current_index]))
            return True
        return False
        
    def next_pdf(self):
        if self.current_index < len(self.pdf_files) - 1:
            self.current_index += 1
            self.load_pdf(os.path.join(self.folder_path, self.pdf_files[self.current_index]))
            return True
        return False
        
    def get_all_results(self):
        """Retourne un dictionnaire avec les informations de base"""
        results = {
            'total_pdfs': len(self.pdf_files),
            'pdf_files': self.pdf_files,
            'litho_codes': self.get_all_litho_codes(),
            'folder_path': self.folder_path,
            'invalid_files': self.invalid_files,
            'validation_report': self.get_validation_report()
        }
        return results

    def get_thumbnail(self, pdf_file, size=(180, 240)):
        """
        Génère un thumbnail haute résolution pour un fichier PDF
        Args:
            pdf_file: Nom du fichier PDF (ou chemin complet)
            size: Tuple (width, height) pour la taille du thumbnail (par défaut 180x240 pour qualité 3x)
        Returns:
            QPixmap du thumbnail ou None si échec

        Note:
            Taille par défaut augmentée de 60x80 à 180x240 pour améliorer la qualité (facteur 3x)
            Résolution doublée via matrix zoom pour éviter le flou
        """
        # Extraire juste le nom du fichier si c'est un chemin complet
        if os.path.sep in pdf_file:
            pdf_file = os.path.basename(pdf_file)

        # Vérifier le cache
        if pdf_file in self._thumbnail_cache:
            return self._thumbnail_cache[pdf_file]

        # Générer le thumbnail
        try:
            pdf_path = os.path.join(self.folder_path, pdf_file)

            # Vérifier que le fichier existe
            if not os.path.exists(pdf_path):
                self.logger.warning(f"Fichier PDF introuvable pour thumbnail: {pdf_path}")
                return self._get_placeholder_thumbnail(size)

            # Ouvrir le PDF temporairement
            pdf_doc = fitz.open(pdf_path)

            # Utiliser la première page
            if len(pdf_doc) == 0:
                pdf_doc.close()
                return self._get_placeholder_thumbnail(size)

            page = pdf_doc[0]

            # Calculer le facteur de zoom pour atteindre la taille souhaitée
            # On utilise la largeur comme référence
            rect = page.rect
            zoom_x = size[0] / rect.width
            zoom_y = size[1] / rect.height
            zoom = min(zoom_x, zoom_y)  # Garder l'aspect ratio

            # 🆕 Doubler la résolution pour qualité supérieure (anti-aliasing)
            zoom *= 2.0

            # Générer le pixmap avec le zoom haute résolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Conversion en QPixmap
            img_data = pix.samples
            qim = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qim)

            # 🆕 Redimensionner à la taille cible avec smooth scaling pour qualité optimale
            pixmap = pixmap.scaled(size[0], size[1], Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

            # Fermer le document
            pdf_doc.close()

            # Mettre en cache
            self._thumbnail_cache[pdf_file] = pixmap

            return pixmap

        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du thumbnail pour {pdf_file}: {e}")
            return self._get_placeholder_thumbnail(size)

    def _get_placeholder_thumbnail(self, size=(180, 240)):
        """Crée un placeholder QPixmap quand le thumbnail ne peut être généré"""
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.GlobalColor.lightGray)
        return pixmap

    def clear_thumbnail_cache(self):
        """Vide le cache des thumbnails"""
        self._thumbnail_cache.clear()