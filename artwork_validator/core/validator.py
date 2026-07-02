# core/validator.py
import pandas as pd
import logging
from typing import Optional
from .enhanced_validator import EnhancedValidator
from .brand_configs.base_config import BaseBrandConfig
from .brand_configs.brand_registry import BrandRegistry

class LithoValidator:
    def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
        """
        Initialise le validateur avec une configuration de marque.

        Args:
            brand_config (Optional[BaseBrandConfig]): Configuration de la marque.
                                                      Si None, utilise MNY par défaut.
        """
        # Dictionnaire des équivalences
        self.equivalences = {
            'WTP': 'WATERPROOF',
            'WATERPROOF': 'WTP'
        }
        self.check_digits = False  # Par défaut, ne pas vérifier les 4 DIGITS
        self.use_enhanced_validation = False  # Par défaut, utiliser l'ancienne méthode

        # 🆕 Configuration de la marque
        if brand_config is None:
            # Par défaut, utiliser MNY
            brand_config = BrandRegistry.get_brand('MNY')
            if brand_config is None:
                # Fallback si registry pas initialisé
                from .brand_configs.mny_config import MNYBrandConfig
                brand_config = MNYBrandConfig()

        self.brand_config = brand_config

        # Instance du validateur amélioré
        self.enhanced_validator = EnhancedValidator()

        # Logger pour la comparaison
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔍 LithoValidator initialized for: {self.brand_config.get_brand_display_name()}")
        
    def _safe_str(self, value) -> str:
        """Convertit de manière sécurisée une valeur en string"""
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            if float(value).is_integer():
                return str(int(value))
            return str(value)
        return str(value).strip()
    
    def _extract_cubby_dimensions(self, description):
        """Extrait les dimensions du CUBBY depuis la description"""
        import re

        # Pattern pour capturer XFY format (ex: 10F2T, 10F3T, 10F4T)
        pattern = r'(\d+)F(\d+)T'

        # Chercher le pattern dans la description
        match = re.search(pattern, description.upper())
        if match:
            try:
                faces = int(match.group(1))
                tiers = int(match.group(2))
                return (faces, tiers)
            except (ValueError, AttributeError):
                pass

        # Fallback: chercher "CUBBY" explicite avec dimensions séparées
        if 'CUBBY' in description.upper():
            parts = description.split()
            for part in parts:
                if 'F' in part and 'T' in part:
                    try:
                        faces = int(part.split('F')[0])
                        tiers = int(part.split('F')[1].split('T')[0])
                        return (faces, tiers)
                    except:
                        pass

            # Dimensions par défaut pour CUBBY si pas spécifiées
            return (10, 2)

        return None

    def _sort_by_upc_sequence(self, excel_data):
        """Trie les données Excel selon la colonne UPC SEQUENCE pour les CUBBY"""
        if not excel_data or 'UPC SEQUENCE' not in excel_data[0]:
            print("⚠️ Colonne UPC SEQUENCE manquante - utilisation ordre Excel original")
            return excel_data

        # Récupérer la séquence UPC de la première ligne
        upc_sequence_str = str(excel_data[0].get('UPC SEQUENCE', '')).strip()
        if not upc_sequence_str:
            print("⚠️ UPC SEQUENCE vide - utilisation ordre Excel original")
            return excel_data

        # Parser la séquence (séparée par virgules)
        target_sequence = [upc.strip() for upc in upc_sequence_str.split(',') if upc.strip()]
        print(f"🔄 SEQUENCE CIBLE: {target_sequence}")

        # Créer un mapping UPC → ordre dans la séquence cible
        upc_order_map = {}
        for i, target_upc in enumerate(target_sequence):
            upc_order_map[target_upc] = i

        # Trier les données selon l'ordre de la séquence
        def get_sort_key(row):
            row_upc = str(row.get('UPC', '')).strip()
            # Si UPC trouvé dans séquence, utiliser son ordre, sinon mettre à la fin
            return upc_order_map.get(row_upc, len(target_sequence))

        sorted_data = sorted(excel_data, key=get_sort_key)

        # Logs de validation
        sorted_upcs = [str(row.get('UPC', '')).strip() for row in sorted_data]
        print(f"📝 UPC TRIÉS: {sorted_upcs}")

        return sorted_data

    def _validate_upc_sequence_order(self, excel_data, target_sequence):
        """Valide que les UPC Excel correspondent à la séquence cible"""
        excel_upcs = [str(row.get('UPC', '')).strip() for row in excel_data]

        print(f"🔍 VALIDATION SEQUENCE:")
        print(f"   Cible: {target_sequence}")
        print(f"   Excel: {excel_upcs}")

        matches = 0
        mismatches = []

        min_length = min(len(target_sequence), len(excel_upcs))
        for i in range(min_length):
            if target_sequence[i] == excel_upcs[i]:
                matches += 1
                print(f"   ✅ Position {i+1}: {target_sequence[i]} = {excel_upcs[i]}")
            else:
                mismatches.append(f"Position {i+1}: attendu '{target_sequence[i]}', trouvé '{excel_upcs[i]}'")
                print(f"   ❌ Position {i+1}: attendu '{target_sequence[i]}', trouvé '{excel_upcs[i]}'")

        # Vérifier les longueurs
        if len(target_sequence) != len(excel_upcs):
            mismatches.append(f"Longueurs différentes: séquence={len(target_sequence)}, excel={len(excel_upcs)}")

        coherence_percentage = (matches / min_length * 100) if min_length > 0 else 0
        print(f"📊 COHÉRENCE: {matches}/{min_length} ({coherence_percentage:.1f}%)")

        if mismatches:
            print(f"⚠️ INCOHÉRENCES DÉTECTÉES:")
            for mismatch in mismatches:
                print(f"   - {mismatch}")

        return len(mismatches) == 0

    def validate(self, pdf_text, excel_data, comparison_mode=False):
        """
        Méthode principale de validation

        Args:
            pdf_text: Texte extrait du PDF
            excel_data: Données Excel à valider
            comparison_mode: Si True, exécute les deux validations pour comparaison

        Returns:
            dict ou list: Résultats selon la méthode utilisée
        """
        # Synchroniser les options avec le validateur amélioré
        self.enhanced_validator.check_digits = self.check_digits

        if comparison_mode:
            return self._validate_comparison_mode(pdf_text, excel_data)
        elif self.use_enhanced_validation:
            return self._validate_enhanced(pdf_text, excel_data)
        else:
            return self._validate_legacy(pdf_text, excel_data)

    def _validate_comparison_mode(self, pdf_text, excel_data):
        """Exécute les deux validations et compare les résultats"""
        self.logger.info("🔄 Mode comparaison: exécution des deux validations")

        # Validation legacy
        legacy_results = self._validate_legacy(pdf_text, excel_data)

        # Validation enhanced
        enhanced_results = self._validate_enhanced(pdf_text, excel_data)

        # Calculer les métriques de comparaison
        comparison_stats = self._compare_validation_results(legacy_results, enhanced_results)

        return {
            'legacy_results': legacy_results,
            'enhanced_results': enhanced_results,
            'comparison_stats': comparison_stats,
            'mode': 'comparison'
        }

    def _validate_enhanced(self, pdf_text, excel_data):
        """Utilise la nouvelle méthode de validation améliorée"""
        enhanced_result = self.enhanced_validator.validate_enhanced(pdf_text, excel_data)

        # Adapter le format pour compatibilité avec l'interface existante
        if enhanced_result.get('results'):
            return enhanced_result['results']
        else:
            return []

    def _validate_legacy(self, pdf_text, excel_data):
        """Ancienne méthode de validation (conservée intacte)"""
        results = []
        if not excel_data:
            return results
            
        pdf_text = pdf_text.upper()  # Convertir en majuscules pour la comparaison
        
        # Vérifier si c'est une litho CUBBY
        # Chercher dans différentes colonnes possibles pour la description
        description = ''
        for col_name in ['DECRIPTION', 'DESCRIPTION', 'PRODUCT DESCRIPTION', 'DESC']:
            if col_name in excel_data[0]:
                description = str(excel_data[0].get(col_name, ''))
                break

        # Détecter CUBBY par pattern ou mot-clé
        cubby_dimensions = self._extract_cubby_dimensions(description)
        is_cubby = cubby_dimensions is not None

        # Pour les CUBBY, organiser les données en matrice
        if is_cubby and cubby_dimensions:
            faces, tiers = cubby_dimensions

            # Trier les données selon UPC SEQUENCE si disponible
            sorted_excel_data = self._sort_by_upc_sequence(excel_data)

            # Valider la cohérence si UPC SEQUENCE était disponible
            if 'UPC SEQUENCE' in excel_data[0]:
                upc_sequence_str = str(excel_data[0].get('UPC SEQUENCE', '')).strip()
                if upc_sequence_str:
                    target_sequence = [upc.strip() for upc in upc_sequence_str.split(',') if upc.strip()]
                    self._validate_upc_sequence_order(sorted_excel_data, target_sequence)

            matrix_data = self._organize_cubby_matrix(sorted_excel_data, faces, tiers)
            
            # Créer un résultat spécial pour les CUBBY
            return [{
                'is_cubby': True,
                'cubby_dimensions': cubby_dimensions,
                'matrix_data': matrix_data,
                'description': description
            }]
            
        # Vérification des facings (seulement pour les produits réels)
        facings = set()
        for row in excel_data:
            facing = self._safe_str(row.get('PRODUCT FACING SL'))
            if facing and facing not in ['FRAME', 'SPACE_SAVER', 'CUBBY']:
                try:
                    facing_int = int(facing)
                    facings.add(facing_int)
                except (ValueError, TypeError):
                    continue
                    
        is_mixed = len(facings) > 1

        for row in excel_data:
            # Déterminer si c'est un FRAME ou SPACE_SAVER
            facing_value = self._safe_str(row.get('PRODUCT FACING SL'))
            is_frame = facing_value == 'FRAME'
            
            is_space_saver = any(
                self._safe_str(row.get(field)) == 'SPACE_SAVER' 
                for field in ['UPC', 'PRODUCT DESCRIPTION', 'SHADE NAME']
            )

            validation_details = {
                'shade_number': True,
                'shade_name': True,
                'digits': True,
                'facing': row.get('PRODUCT FACING SL', ''),  # Garder la valeur originale
                'is_mixed': is_mixed,
                'is_cubby': is_cubby,
                'is_frame': is_frame,
                'is_space_saver': is_space_saver,
                'overall': True  # Par défaut True pour FRAME et SPACE_SAVER
            }

            # Ne pas valider si c'est un FRAME ou SPACE_SAVER
            if not (is_frame or is_space_saver):
                # Vérification du numéro de teinte
                shade_number = self._safe_str(row.get('SHADE NUMBER'))
                if shade_number:
                    validation_details['shade_number'] = shade_number in pdf_text
                    
                # Vérification du nom de teinte
                shade_name = self._safe_str(row.get('SHADE NAME'))
                if shade_name:
                    validation_details['shade_name'] = self._validate_shade_name(shade_name, pdf_text)

                # 🆕 Vérification des 4 DIGITS (conditionnelle selon marque)
                digits = self._safe_str(row.get('4 DIGITS'))

                # Vérifier si la marque supporte la validation des 4 DIGITS
                should_validate_digits = self.brand_config.requires_digits_validation()

                if digits and self.check_digits and should_validate_digits:
                    validation_details['digits'] = digits in pdf_text
                else:
                    # Si marque ne supporte pas ou option désactivée, toujours True
                    validation_details['digits'] = True

                # 🆕 Validation globale conditionnelle (selon marque)
                validation_criteria = [
                    validation_details['shade_number'],
                    validation_details['shade_name']
                ]

                # N'ajouter les 4 DIGITS que si marque le supporte ET option activée
                if self.check_digits and should_validate_digits and digits:
                    validation_criteria.append(validation_details['digits'])

                validation_details['overall'] = all(validation_criteria)
            
            results.append(validation_details)
            
        return results

    def _validate_shade_name(self, shade_name: str, pdf_text: str) -> bool:
        """Valide le nom de teinte en tenant compte des équivalences"""
        shade_name = shade_name.upper()
        
        # Si le nom exact est trouvé
        if shade_name in pdf_text:
            return True
            
        # Gestion du cas WTP/WATERPROOF
        if 'WTP' in shade_name:
            alternate_name = shade_name.replace('WTP', 'WATERPROOF')
            return alternate_name in pdf_text
        elif 'WATERPROOF' in shade_name:
            alternate_name = shade_name.replace('WATERPROOF', 'WTP')
            return alternate_name in pdf_text
            
        return False
    
    def _organize_cubby_matrix(self, excel_data, faces, tiers):
        """Organise les données du CUBBY en matrice avec détection automatique des TIER"""
        import re

        # Initialiser la matrice vide
        matrix = [[None for _ in range(faces)] for _ in range(tiers)]

        current_tier = 0
        current_position = 0
        upc_position_pattern = re.compile(r'UPC\.(\d+)', re.IGNORECASE)

        print(f"Organisation CUBBY: {faces} faces × {tiers} tiers")
        print(f"📊 LECTURE EXCEL - {len(excel_data)} lignes détectées")

        for i, row in enumerate(excel_data):
            upc = str(row.get('UPC', '')).strip()
            # Log de debug pour voir l'ordre de lecture
            print(f"📝 Ligne {i+1}: UPC='{upc}', SHADE_NAME='{row.get('SHADE NAME', '')}'")

            # Créer l'élément
            item = {
                'upc': upc,
                'shade_name': str(row.get('SHADE NAME', '')).strip(),
                'shade_number': str(row.get('SHADE NUMBER', '')).strip(),
                'is_frame': upc.upper() == 'FRAME'
            }

            # Détecter les patterns UPC.X pour automatiser le placement
            upc_match = upc_position_pattern.search(upc)
            if upc_match:
                detected_position = int(upc_match.group(1))

                # Détecter changement de TIER : si on passe de UPC.10 à UPC.1
                if detected_position == 1 and current_position > 1:
                    current_tier += 1
                    current_position = 0
                    # Afficher le TIER physique correct (inversé pour empilement)
                    physical_tier = tiers - current_tier
                    print(f"Changement de TIER détecté: TIER {physical_tier} (ligne {current_tier})")

                # Utiliser la position détectée (ajustée à base 0)
                target_position = detected_position - 1
            else:
                # Pas de pattern UPC.X détecté, utiliser position séquentielle
                target_position = current_position

            # Vérifier les limites et placer l'élément
            if current_tier < tiers and target_position < faces:
                matrix[current_tier][target_position] = item
                # Afficher le TIER physique correct (inversé pour empilement)
                physical_tier = tiers - current_tier
                print(f"Placé {upc} en TIER {physical_tier} (ligne {current_tier}), Position {target_position + 1}")

                # Incrémenter la position pour le prochain élément
                current_position = target_position + 1

                # Si on dépasse le nombre de faces, passer au tier suivant
                if current_position >= faces:
                    current_tier += 1
                    current_position = 0
            else:
                physical_tier = tiers - current_tier if current_tier < tiers else "?"
                print(f"Hors limites: {upc} - TIER {physical_tier} (ligne {current_tier}), Position {target_position}")

        # Remplir les cases vides
        for tier in range(tiers):
            for pos in range(faces):
                if matrix[tier][pos] is None:
                    matrix[tier][pos] = {
                        'upc': 'EMPTY',
                        'shade_name': '',
                        'shade_number': '',
                        'is_frame': False
                    }

        return matrix

    def _compare_validation_results(self, legacy_results, enhanced_results):
        """Compare les résultats des deux méthodes de validation"""
        if not legacy_results or not enhanced_results:
            return {
                'comparison_possible': False,
                'reason': 'Résultats manquants'
            }

        stats = {
            'total_entries': len(legacy_results),
            'legacy_success': sum(1 for r in legacy_results if r.get('overall', False)),
            'enhanced_success': sum(1 for r in enhanced_results if r.get('overall', False)),
            'agreements': 0,
            'disagreements': 0,
            'detailed_differences': []
        }

        # Comparer entrée par entrée
        min_length = min(len(legacy_results), len(enhanced_results))
        for i in range(min_length):
            legacy = legacy_results[i]
            enhanced = enhanced_results[i]

            legacy_overall = legacy.get('overall', False)
            enhanced_overall = enhanced.get('overall', False)

            if legacy_overall == enhanced_overall:
                stats['agreements'] += 1
            else:
                stats['disagreements'] += 1
                stats['detailed_differences'].append({
                    'entry_index': i,
                    'legacy_result': legacy_overall,
                    'enhanced_result': enhanced_overall,
                    'legacy_details': {
                        'shade_number': legacy.get('shade_number', False),
                        'shade_name': legacy.get('shade_name', False),
                        'digits': legacy.get('digits', False)
                    },
                    'enhanced_details': {
                        'shade_number': enhanced.get('shade_number', False),
                        'shade_name': enhanced.get('shade_name', False),
                        'digits': enhanced.get('digits', False)
                    }
                })

        # Calculer les métriques de performance
        stats['agreement_rate'] = (stats['agreements'] / min_length * 100) if min_length > 0 else 0
        stats['legacy_success_rate'] = (stats['legacy_success'] / len(legacy_results) * 100) if legacy_results else 0
        stats['enhanced_success_rate'] = (stats['enhanced_success'] / len(enhanced_results) * 100) if enhanced_results else 0

        return stats

    def set_enhanced_validation(self, enabled: bool):
        """Active ou désactive la validation améliorée"""
        self.use_enhanced_validation = enabled
        self.logger.info(f"Validation améliorée: {'activée' if enabled else 'désactivée'}")

    def get_validation_method(self) -> str:
        """Retourne la méthode de validation courante"""
        return "enhanced" if self.use_enhanced_validation else "legacy"