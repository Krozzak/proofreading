# core/ocr_processor.py
"""
Processeur OCR basé sur PaddleOCR pour l'extraction de texte des PDFs scannés.
Utilisé comme fallback quand PyMuPDF ne peut pas extraire le texte (PDFs image).
"""

import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    Processeur OCR utilisant PaddleOCR pour extraire le texte des images et PDFs scannés.
    PaddleOCR offre de meilleures performances que Tesseract (2025 research).
    """

    def __init__(self, use_gpu: bool = False):
        """
        Initialise le processeur OCR avec PaddleOCR.

        Args:
            use_gpu: Utiliser le GPU pour l'accélération (nécessite CUDA)
        """
        self.ocr_engine = None
        self.use_gpu = use_gpu
        self._initialized = False

    def _initialize_ocr(self):
        """Initialisation lazy de PaddleOCR"""
        if self._initialized:
            return

        try:
            from paddleocr import PaddleOCR

            logger.info(f"Initialisation de PaddleOCR (GPU: {self.use_gpu})...")

            # Initialiser PaddleOCR avec configuration optimale
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True,  # Détection de l'orientation du texte
                lang='en',           # Langue anglaise (meilleure pour nos besoins)
                use_gpu=self.use_gpu,
                show_log=False       # Réduire la verbosité
            )

            self._initialized = True
            logger.info("PaddleOCR initialisé avec succès")

        except ImportError:
            logger.error("PaddleOCR n'est pas installé. Installez-le avec: pip install paddleocr")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de PaddleOCR: {e}")
            raise

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extrait le texte d'une image avec PaddleOCR.

        Args:
            image_path: Chemin vers l'image

        Returns:
            Texte extrait de l'image
        """
        self._initialize_ocr()

        try:
            logger.info(f"Extraction OCR depuis image: {image_path}")

            # Exécuter l'OCR
            result = self.ocr_engine.ocr(image_path, cls=True)

            # Extraire le texte des résultats
            text_lines = []

            if result and result[0]:
                for line in result[0]:
                    # Format PaddleOCR: [bbox, (text, confidence)]
                    if len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], tuple) else line[1]
                        text_lines.append(text)

            extracted_text = '\n'.join(text_lines)
            logger.info(f"OCR terminé: {len(text_lines)} lignes extraites, {len(extracted_text)} caractères")

            return extracted_text

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction OCR: {e}")
            return ""

    def extract_text_from_pdf_page(self, pdf_path: str, page_number: int = 0) -> str:
        """
        Extrait le texte d'une page PDF via OCR (pour les PDFs scannés).

        Args:
            pdf_path: Chemin vers le PDF
            page_number: Numéro de page (0-indexé)

        Returns:
            Texte extrait de la page
        """
        self._initialize_ocr()

        try:
            import fitz  # PyMuPDF

            logger.info(f"Extraction OCR depuis PDF: {pdf_path}, page {page_number}")

            # Ouvrir le PDF
            doc = fitz.open(pdf_path)

            if page_number >= len(doc):
                logger.warning(f"Page {page_number} n'existe pas dans {pdf_path}")
                return ""

            # Convertir la page en image haute résolution pour meilleure OCR
            page = doc[page_number]

            # Matrice de transformation pour haute résolution (300 DPI)
            zoom = 300 / 72  # 72 DPI par défaut -> 300 DPI
            mat = fitz.Matrix(zoom, zoom)

            # Rendre la page en image
            pix = page.get_pixmap(matrix=mat)

            # Convertir en format PIL Image
            img_data = pix.tobytes("png")
            from io import BytesIO
            img = Image.open(BytesIO(img_data))

            # Sauvegarder temporairement pour PaddleOCR
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                temp_path = tmp.name

            # Exécuter l'OCR sur l'image temporaire
            extracted_text = self.extract_text_from_image(temp_path)

            # Nettoyer le fichier temporaire
            Path(temp_path).unlink(missing_ok=True)

            doc.close()

            return extracted_text

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction OCR du PDF: {e}")
            return ""

    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """
        Extrait le texte avec positions et bounding boxes (pour future Phase 3).

        Args:
            image_path: Chemin vers l'image

        Returns:
            Liste de dictionnaires avec texte, bbox, et confiance
        """
        self._initialize_ocr()

        try:
            logger.info(f"Extraction OCR détaillée depuis: {image_path}")

            result = self.ocr_engine.ocr(image_path, cls=True)

            text_elements = []

            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        text_info = line[1]  # (text, confidence)

                        text = text_info[0] if isinstance(text_info, tuple) else text_info
                        confidence = text_info[1] if isinstance(text_info, tuple) else 1.0

                        text_elements.append({
                            'text': text,
                            'bbox': bbox,
                            'confidence': confidence
                        })

            logger.info(f"Extraction détaillée: {len(text_elements)} éléments extraits")
            return text_elements

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction détaillée: {e}")
            return []

    def is_pdf_scanned(self, pdf_path: str, threshold: int = 50) -> bool:
        """
        Détermine si un PDF est scanné (image) en vérifiant la quantité de texte extractible.

        Args:
            pdf_path: Chemin vers le PDF
            threshold: Nombre minimum de caractères pour considérer comme PDF texte

        Returns:
            True si le PDF est probablement scanné (OCR nécessaire)
        """
        try:
            import fitz

            doc = fitz.open(pdf_path)

            # Vérifier la première page
            if len(doc) > 0:
                page = doc[0]
                text = page.get_text()

                # Si moins de threshold caractères, c'est probablement un scan
                is_scanned = len(text.strip()) < threshold

                doc.close()

                logger.info(
                    f"PDF {'scanné' if is_scanned else 'texte'} détecté: "
                    f"{len(text.strip())} caractères extraits"
                )

                return is_scanned

            doc.close()
            return False

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du type de PDF: {e}")
            return False

    def extract_text_auto(self, pdf_path: str, page_number: int = 0) -> Tuple[str, str]:
        """
        Extraction automatique: tente PyMuPDF d'abord, puis OCR si nécessaire.

        Args:
            pdf_path: Chemin vers le PDF
            page_number: Numéro de page

        Returns:
            Tuple (texte_extrait, méthode_utilisée)
        """
        try:
            import fitz

            # Essayer extraction texte standard d'abord
            doc = fitz.open(pdf_path)

            if page_number >= len(doc):
                doc.close()
                return "", "none"

            page = doc[page_number]
            text = page.get_text()
            doc.close()

            # Si suffisamment de texte, retourner
            if len(text.strip()) >= 50:
                logger.info(f"Extraction standard réussie: {len(text)} caractères")
                return text, "pymupdf"

            # Sinon, utiliser OCR
            logger.info("Texte insuffisant, basculement vers OCR...")
            ocr_text = self.extract_text_from_pdf_page(pdf_path, page_number)

            return ocr_text, "ocr"

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction automatique: {e}")
            return "", "error"


# Fonction utilitaire pour usage simple
def extract_text_from_pdf(pdf_path: str, page_number: int = 0, use_ocr: bool = False) -> str:
    """
    Fonction helper pour extraire le texte d'un PDF.

    Args:
        pdf_path: Chemin vers le PDF
        page_number: Numéro de page (0-indexé)
        use_ocr: Forcer l'utilisation d'OCR même si texte disponible

    Returns:
        Texte extrait
    """
    processor = OCRProcessor()

    if use_ocr:
        return processor.extract_text_from_pdf_page(pdf_path, page_number)
    else:
        text, method = processor.extract_text_auto(pdf_path, page_number)
        return text
