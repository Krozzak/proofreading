# core/enhanced_validator.py
import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher

class EnhancedValidator:
    """
    Validateur amélioré avec correspondance séquentielle et élimination progressive
    pour éviter les correspondances multiples et assurer une validation 1:1
    """

    def __init__(self):
        self.equivalences = {
            'WTP': 'WATERPROOF',
            'WATERPROOF': 'WTP'
        }
        self.check_digits = False
        self.logger = logging.getLogger(__name__)

        # Métriques de validation
        self.validation_stats = {
            'total_tokens': 0,
            'consumed_tokens': 0,
            'orphan_tokens': 0,
            'exact_matches': 0,
            'partial_matches': 0,
            'failed_matches': 0,
            'duplicate_allowances': 0
        }

    def _safe_str(self, value) -> str:
        """Convertit de manière sécurisée une valeur en string"""
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            if float(value).is_integer():
                return str(int(value))
            return str(value)
        return str(value).strip()

    def _tokenize_pdf_text(self, pdf_text: str) -> List[Dict]:
        """
        Tokenise le texte PDF en gardant la position et les métadonnées
        """
        # Normaliser le texte
        text = pdf_text.upper().strip()

        # Diviser en tokens (mots/nombres/symboles)
        # Pattern pour capturer mots, nombres, et symboles significatifs
        pattern = r'\b\w+\b|\d+|[A-Z]+'
        tokens = []

        for match in re.finditer(pattern, text):
            token = {
                'text': match.group(),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'consumed': False,
                'consumed_by': None,  # Quelle entrée Excel a consommé ce token
                'type': self._classify_token(match.group())
            }
            tokens.append(token)

        self.validation_stats['total_tokens'] = len(tokens)
        self.logger.info(f"📝 PDF tokenisé: {len(tokens)} tokens extraits")

        return tokens

    def _classify_token(self, token: str) -> str:
        """Classifie le type de token pour optimiser la recherche"""
        if token.isdigit():
            if len(token) == 4:
                return 'digits_4'
            elif len(token) in [2, 3]:
                return 'shade_number'
            else:
                return 'number'
        elif token.isalpha():
            if token in ['WATERPROOF', 'WTP']:
                return 'waterproof_tag'
            elif len(token) > 1:
                return 'shade_name'
            else:
                return 'letter'
        else:
            return 'mixed'

    def _normalize_excel_data(self, excel_data: List[Dict]) -> List[Dict]:
        """
        Normalise les données Excel pour la correspondance
        """
        normalized = []

        for row in excel_data:
            normalized_row = row.copy()

            # Identifier les types spéciaux
            facing_value = self._safe_str(row.get('PRODUCT FACING SL'))
            is_frame = facing_value == 'FRAME'
            is_space_saver = any(
                self._safe_str(row.get(field)) == 'SPACE_SAVER'
                for field in ['UPC', 'PRODUCT DESCRIPTION', 'SHADE NAME']
            )

            # Normaliser les noms de teintes WTP -> WATERPROOF
            shade_name = self._safe_str(row.get('SHADE NAME'))
            if shade_name and 'WTP' in shade_name:
                normalized_row['SHADE_NAME_NORMALIZED'] = shade_name.replace('WTP', 'WATERPROOF')
            else:
                normalized_row['SHADE_NAME_NORMALIZED'] = shade_name

            # Métadonnées pour le traitement
            normalized_row['_is_frame'] = is_frame
            normalized_row['_is_space_saver'] = is_space_saver
            normalized_row['_should_validate'] = not (is_frame or is_space_saver)

            normalized.append(normalized_row)

        return normalized

    def _find_token_match(self, tokens: List[Dict], search_text: str,
                         start_index: int = 0, token_types: List[str] = None) -> Optional[Tuple[int, Dict, int]]:
        """
        Trouve la première correspondance d'un texte dans les tokens à partir d'un index.
        Retourne: (index_début, premier_token, nombre_de_tokens_consommés)
        """
        if not search_text:
            return None

        search_text = search_text.upper().strip()
        search_words = search_text.split()  # Diviser en mots pour les noms composés

        # CAS 1: Recherche multi-tokens (pour les noms composés comme "FOREST BROWN")
        if len(search_words) > 1:
            for i in range(start_index, len(tokens) - len(search_words) + 1):
                # Vérifier si les tokens ne sont pas déjà consommés
                tokens_slice = tokens[i:i + len(search_words)]
                if any(t['consumed'] for t in tokens_slice):
                    continue

                # Vérifier si les tokens correspondent aux mots
                match = True
                for j, word in enumerate(search_words):
                    if tokens[i + j]['text'] != word:
                        match = False
                        break

                if match:
                    # Retourner l'index de début, le premier token, et le nombre de tokens
                    return i, tokens[i], len(search_words)

        # CAS 2: Recherche single-token (comportement original)
        for i in range(start_index, len(tokens)):
            token = tokens[i]

            # Ignorer les tokens déjà consommés
            if token['consumed']:
                continue

            # Filtrer par type si spécifié
            if token_types and token['type'] not in token_types:
                continue

            # Correspondance exacte
            if token['text'] == search_text:
                return i, token, 1

            # Correspondance partielle pour les noms longs
            if len(search_text) > 3 and search_text in token['text']:
                return i, token, 1

        return None

    def _consume_token(self, tokens: List[Dict], token_index: int, consumed_by: str, num_tokens: int = 1):
        """
        Marque un ou plusieurs tokens consécutifs comme consommés

        Args:
            tokens: Liste des tokens
            token_index: Index de départ
            consumed_by: Identifiant de l'entrée qui consomme
            num_tokens: Nombre de tokens à consommer (défaut: 1)
        """
        for i in range(token_index, min(token_index + num_tokens, len(tokens))):
            if 0 <= i < len(tokens):
                tokens[i]['consumed'] = True
                tokens[i]['consumed_by'] = consumed_by
                self.validation_stats['consumed_tokens'] += 1

    def _check_duplicate_allowance(self, excel_data: List[Dict], current_index: int) -> bool:
        """
        Vérifie si l'entrée courante est un doublon légitime
        """
        if current_index == 0:
            return False

        current_row = excel_data[current_index]

        # Comparer avec les entrées précédentes
        for i in range(current_index):
            prev_row = excel_data[i]

            # Même shade number et shade name = doublon légitime
            if (self._safe_str(current_row.get('SHADE NUMBER')) ==
                self._safe_str(prev_row.get('SHADE NUMBER')) and
                self._safe_str(current_row.get('SHADE NAME')) ==
                self._safe_str(prev_row.get('SHADE NAME'))):
                return True

        return False

    def validate_enhanced(self, pdf_text: str, excel_data: List[Dict]) -> Dict:
        """
        Validation améliorée avec correspondance séquentielle et élimination progressive
        """
        self.logger.info("🔍 Début de la validation améliorée")

        # Réinitialiser les statistiques
        self.validation_stats = {key: 0 for key in self.validation_stats}

        if not excel_data or not pdf_text:
            return {'results': [], 'stats': self.validation_stats, 'errors': ['Données manquantes']}

        # 1. Tokeniser le PDF
        tokens = self._tokenize_pdf_text(pdf_text)

        # 2. Normaliser les données Excel
        normalized_excel = self._normalize_excel_data(excel_data)

        # 3. Validation séquentielle
        results = []
        current_position = 0
        errors = []

        for idx, row in enumerate(normalized_excel):
            result = self._validate_single_entry(tokens, row, idx, current_position)
            results.append(result)

            # Mettre à jour la position pour la prochaine recherche
            if result.get('last_token_position') is not None:
                current_position = result['last_token_position'] + 1

        # 4. Analyser les tokens orphelins
        orphan_tokens = [t for t in tokens if not t['consumed']]
        self.validation_stats['orphan_tokens'] = len(orphan_tokens)

        if orphan_tokens:
            self.logger.warning(f"⚠️ {len(orphan_tokens)} tokens non consommés détectés")
            for token in orphan_tokens[:5]:  # Limiter le log
                self.logger.warning(f"   Token orphelin: '{token['text']}'")

        # 5. Vérification du décompte
        expected_validations = sum(1 for row in normalized_excel if row['_should_validate'])
        actual_validations = sum(1 for r in results if r.get('overall', False))

        if expected_validations != actual_validations:
            errors.append(f"Décompte incorrect: {actual_validations}/{expected_validations} validations")

        self.logger.info(f"✅ Validation améliorée terminée: {actual_validations}/{expected_validations} succès")

        return {
            'results': results,
            'stats': self.validation_stats,
            'errors': errors,
            'orphan_tokens': [t['text'] for t in orphan_tokens],
            'summary': {
                'expected_validations': expected_validations,
                'actual_validations': actual_validations,
                'success_rate': (actual_validations / expected_validations * 100) if expected_validations > 0 else 0
            }
        }

    def _validate_single_entry(self, tokens: List[Dict], row: Dict, row_index: int, start_position: int) -> Dict:
        """
        Valide une entrée Excel individuelle contre les tokens PDF
        """
        entry_id = f"Row_{row_index + 1}"

        result = {
            'shade_number': True,
            'shade_name': True,
            'digits': True,
            'facing': row.get('PRODUCT FACING SL', ''),
            'is_mixed': False,  # À déterminer par le processus principal
            'is_cubby': False,
            'is_frame': row['_is_frame'],
            'is_space_saver': row['_is_space_saver'],
            'overall': True,
            'validation_details': {
                'method': 'enhanced',
                'tokens_used': [],
                'start_position': start_position,
                'last_token_position': None
            }
        }

        # Ne pas valider les FRAME et SPACE_SAVER
        if not row['_should_validate']:
            return result

        # Vérifier si c'est un doublon légitime
        is_duplicate = self._check_duplicate_allowance([row] + [{}] * row_index, row_index)
        if is_duplicate:
            self.validation_stats['duplicate_allowances'] += 1

        current_pos = start_position
        validation_success = True

        # 1. Validation du shade number
        shade_number = self._safe_str(row.get('SHADE NUMBER'))
        if shade_number:
            match = self._find_token_match(tokens, shade_number, current_pos, ['shade_number', 'number'])
            if match:
                token_idx, token, num_tokens = match  # ⭐ Récupérer le nombre de tokens
                if not is_duplicate:  # Seulement consommer si pas un doublon
                    self._consume_token(tokens, token_idx, f"{entry_id}_SHADE_NUMBER", num_tokens)
                result['validation_details']['tokens_used'].append({
                    'field': 'SHADE_NUMBER',
                    'token': token['text'],
                    'position': token_idx,
                    'num_tokens': num_tokens
                })
                current_pos = token_idx + num_tokens  # ⭐ Avancer de num_tokens
                result['validation_details']['last_token_position'] = token_idx + num_tokens - 1
                self.validation_stats['exact_matches'] += 1
            else:
                result['shade_number'] = False
                validation_success = False
                self.validation_stats['failed_matches'] += 1

        # 2. Validation du shade name
        shade_name = row.get('SHADE_NAME_NORMALIZED', '')
        if shade_name:
            match = self._find_token_match(tokens, shade_name, current_pos, ['shade_name', 'mixed'])
            if match:
                token_idx, token, num_tokens = match  # ⭐ Récupérer le nombre de tokens
                if not is_duplicate:
                    self._consume_token(tokens, token_idx, f"{entry_id}_SHADE_NAME", num_tokens)
                result['validation_details']['tokens_used'].append({
                    'field': 'SHADE_NAME',
                    'token': token['text'],
                    'position': token_idx,
                    'num_tokens': num_tokens
                })
                current_pos = token_idx + num_tokens  # ⭐ Avancer de num_tokens
                result['validation_details']['last_token_position'] = token_idx + num_tokens - 1
                self.validation_stats['exact_matches'] += 1
            else:
                result['shade_name'] = False
                validation_success = False
                self.validation_stats['failed_matches'] += 1

        # 3. Validation des 4 digits (si activée)
        if self.check_digits:
            digits = self._safe_str(row.get('4 DIGITS'))
            if digits:
                match = self._find_token_match(tokens, digits, current_pos, ['digits_4', 'number'])
                if match:
                    token_idx, token, num_tokens = match  # ⭐ Récupérer le nombre de tokens
                    if not is_duplicate:
                        self._consume_token(tokens, token_idx, f"{entry_id}_4DIGITS", num_tokens)
                    result['validation_details']['tokens_used'].append({
                        'field': '4_DIGITS',
                        'token': token['text'],
                        'position': token_idx,
                        'num_tokens': num_tokens
                    })
                    current_pos = token_idx + num_tokens  # ⭐ Avancer de num_tokens
                    result['validation_details']['last_token_position'] = token_idx + num_tokens - 1
                    self.validation_stats['exact_matches'] += 1
                else:
                    result['digits'] = False
                    validation_success = False
                    self.validation_stats['failed_matches'] += 1

        # Validation globale
        validation_criteria = [result['shade_number'], result['shade_name']]
        if self.check_digits and self._safe_str(row.get('4 DIGITS')):
            validation_criteria.append(result['digits'])

        result['overall'] = all(validation_criteria)

        return result