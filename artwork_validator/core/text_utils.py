# core/text_utils.py
import re
from typing import Optional

class TextNormalizer:
    """Utilitaires pour normaliser et comparer du texte extrait de PDFs"""
    
    @staticmethod
    def normalize_text(text: str, preserve_newlines: bool = False) -> str:
        """
        Normalise un texte en :
        - Supprimant les espaces multiples
        - Optionnellement en supprimant les retours à la ligne
        - Normalisant les espaces autour de la ponctuation
        
        Args:
            text: Texte à normaliser
            preserve_newlines: Si True, garde les retours à la ligne
            
        Returns:
            Texte normalisé
        """
        if not text:
            return ""
        
        # Convertir en string et nettoyer
        text = str(text).strip()
        
        if not preserve_newlines:
            # Remplacer tous les types de retours à la ligne par des espaces
            text = re.sub(r'[\n\r\t]+', ' ', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Nettoyer les espaces autour de certains caractères spéciaux
        # Exemple: "2-IN-1 BASE & TOP COAT" au lieu de "2-IN-1 BASE  &  TOP COAT"
        text = re.sub(r'\s*&\s*', ' & ', text)
        text = re.sub(r'\s*-\s*', '-', text)
        text = re.sub(r'\s*/\s*', '/', text)
        
        return text.strip()
    
    @staticmethod
    def normalize_for_comparison(text: str) -> str:
        """
        Normalise un texte pour comparaison stricte en :
        - Supprimant tous les espaces et retours à la ligne
        - Convertissant en majuscules
        - Supprimant la ponctuation non significative
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé pour comparaison
        """
        if not text:
            return ""
        
        # Convertir en string
        text = str(text)
        
        # Supprimer tous les espaces et retours à la ligne
        text = re.sub(r'\s+', '', text)
        
        # Convertir en majuscules
        text = text.upper()
        
        return text
    
    @staticmethod
    def flexible_match(text1: str, text2: str, strict: bool = False) -> bool:
        """
        Compare deux textes de manière flexible
        
        Args:
            text1: Premier texte
            text2: Deuxième texte
            strict: Si True, comparaison stricte, sinon flexible
            
        Returns:
            True si les textes correspondent
        """
        if not text1 and not text2:
            return True
        
        if not text1 or not text2:
            return False
        
        if strict:
            # Comparaison stricte après normalisation simple
            return TextNormalizer.normalize_text(text1) == TextNormalizer.normalize_text(text2)
        else:
            # Comparaison flexible (ignore espaces, casse, ponctuation)
            return (TextNormalizer.normalize_for_comparison(text1) == 
                    TextNormalizer.normalize_for_comparison(text2))
    
    @staticmethod
    def find_text_in_pdf(search_text: str, pdf_text: str, context_chars: int = 50) -> Optional[str]:
        """
        Recherche un texte dans un PDF et retourne le contexte
        
        Args:
            search_text: Texte à rechercher
            pdf_text: Texte complet du PDF
            context_chars: Nombre de caractères de contexte à retourner
            
        Returns:
            Contexte du texte trouvé ou None
        """
        # Normaliser pour la recherche
        normalized_search = TextNormalizer.normalize_for_comparison(search_text)
        normalized_pdf = TextNormalizer.normalize_for_comparison(pdf_text)
        
        # Chercher
        index = normalized_pdf.find(normalized_search)
        
        if index >= 0:
            # Trouver la position correspondante dans le texte original
            # (approximatif car on a supprimé des caractères)
            start = max(0, index - context_chars)
            end = min(len(pdf_text), index + len(search_text) + context_chars)
            return pdf_text[start:end]
        
        return None
    
    @staticmethod
    def extract_multiline_text(pdf_text: str, start_marker: str, max_lines: int = 3) -> Optional[str]:
        """
        Extrait un texte qui peut être sur plusieurs lignes dans le PDF
        
        Args:
            pdf_text: Texte complet du PDF
            start_marker: Marqueur de début
            max_lines: Nombre maximum de lignes à extraire
            
        Returns:
            Texte extrait sur plusieurs lignes
        """
        lines = pdf_text.split('\n')
        
        for i, line in enumerate(lines):
            if start_marker in line:
                # Extraire cette ligne et les suivantes
                extracted_lines = lines[i:min(i + max_lines, len(lines))]
                return ' '.join(extracted_lines).strip()
        
        return None