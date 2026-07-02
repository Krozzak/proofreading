# core/error_templates.py
"""
Base de données des erreurs courantes et messages préremplis
pour assister les validateurs dans leur travail
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = "low"          # Erreurs mineures, validation possible
    MEDIUM = "medium"    # Erreurs modérées, attention requise
    HIGH = "high"        # Erreurs importantes, rejet recommandé
    CRITICAL = "critical"  # Erreurs critiques, rejet obligatoire


class ErrorCategory(Enum):
    """Catégories d'erreurs"""
    SHADE_VALIDATION = "shade_validation"    # Erreurs de teinte/numéro
    LAYOUT = "layout"                        # Erreurs de mise en page
    WALMART_SPECIFIC = "walmart_specific"    # Erreurs spécifiques Walmart
    CONTENT = "content"                      # Erreurs de contenu


@dataclass
class ErrorTemplate:
    """Template d'une erreur avec informations d'assistance"""
    code: str                      # Code unique de l'erreur
    title: str                     # Titre court de l'erreur
    template: str                  # Message template avec placeholders
    suggestions: List[str]         # Suggestions d'action
    quick_responses: List[str]     # Réponses rapides préremplies
    severity: ErrorSeverity        # Niveau de sévérité
    category: ErrorCategory        # Catégorie d'erreur
    auto_reject: bool = False      # Si True, recommande le rejet automatique
    requires_comment: bool = True  # Si True, force l'ajout d'un commentaire


# ========================================
# BASE DE DONNÉES DES ERREURS COURANTES
# ========================================

ERROR_TEMPLATES: Dict[str, ErrorTemplate] = {

    # ===== ERREURS DE VALIDATION DE TEINTE =====

    'shade_name_mismatch': ErrorTemplate(
        code='shade_name_mismatch',
        title='Nom de teinte incorrect',
        template='Nom attendu: "{expected}", Trouvé: "{found}"',
        suggestions=[
            'Vérifier l\'orthographe exacte du nom',
            'Vérifier les espaces et la casse',
            'Vérifier les équivalences WTP/WATERPROOF',
            'Comparer avec le PDF original'
        ],
        quick_responses=[
            '❌ Nom de teinte incorrect - Refaire le PDF',
            '❌ Erreur typographique dans nom de teinte',
            '⚠️ Nom de teinte absent du PDF',
            '✏️ Erreur mineure d\'orthographe - À corriger'
        ],
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SHADE_VALIDATION,
        auto_reject=False
    ),

    'shade_name_missing': ErrorTemplate(
        code='shade_name_missing',
        title='Nom de teinte manquant',
        template='Nom de teinte "{expected}" non trouvé dans le PDF',
        suggestions=[
            'Vérifier que le nom est présent dans le PDF',
            'Vérifier l\'extraction du texte PDF',
            'Si c\'est un PDF scanné, vérifier la qualité OCR',
            'Contacter le fournisseur si le nom est réellement absent'
        ],
        quick_responses=[
            '❌ Nom de teinte manquant dans le PDF',
            '❌ Texte non extrait - PDF scanné de mauvaise qualité',
            '📞 Contacter fournisseur - Information manquante'
        ],
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SHADE_VALIDATION,
        auto_reject=True
    ),

    'shade_number_mismatch': ErrorTemplate(
        code='shade_number_mismatch',
        title='Numéro de teinte incorrect',
        template='Numéro attendu: "{expected}", Trouvé: "{found}" ou absent',
        suggestions=[
            'Vérifier le numéro dans le PDF',
            'Vérifier la concordance avec l\'Excel',
            'Vérifier s\'il n\'y a pas de confusion avec un autre code',
            'Contacter le fournisseur si incohérence persistante'
        ],
        quick_responses=[
            '❌ Numéro de teinte incorrect',
            '❌ Numéro de teinte manquant',
            '⚠️ Incohérence Excel/PDF - Vérifier la source',
            '📞 Contacter fournisseur pour clarification'
        ],
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.SHADE_VALIDATION,
        auto_reject=False
    ),

    'shade_number_missing': ErrorTemplate(
        code='shade_number_missing',
        title='Numéro de teinte manquant',
        template='Numéro de teinte "{expected}" non trouvé dans le PDF',
        suggestions=[
            'Vérifier que le numéro est présent dans le PDF',
            'Vérifier s\'il n\'est pas dans un format différent',
            'Vérifier l\'extraction du texte',
            'Rejeter si le numéro est obligatoire'
        ],
        quick_responses=[
            '❌ Numéro de teinte manquant - Refaire',
            '⚠️ Numéro présent mais format différent',
            '📞 Contacter fournisseur'
        ],
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.SHADE_VALIDATION,
        auto_reject=True
    ),

    # ===== ERREURS WALMART SPÉCIFIQUES =====

    'missing_4digits': ErrorTemplate(
        code='missing_4digits',
        title='4 DIGITS manquant (Walmart)',
        template='Code 4 DIGITS "{expected}" non trouvé dans le PDF',
        suggestions=[
            '⚠️ Requis pour toutes les lithos Walmart',
            'Vérifier que le code est présent dans le PDF',
            'Le code doit être exactement 4 chiffres',
            'REJET OBLIGATOIRE si Walmart et code manquant'
        ],
        quick_responses=[
            '❌ 4 DIGITS manquant - REJET WALMART',
            '❌ Code Walmart absent - Non conforme',
            '📞 Urgence: Contacter fournisseur - Walmart requis'
        ],
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.WALMART_SPECIFIC,
        auto_reject=True
    ),

    'invalid_4digits': ErrorTemplate(
        code='invalid_4digits',
        title='4 DIGITS incorrect',
        template='Code attendu: "{expected}", Trouvé: "{found}"',
        suggestions=[
            'Vérifier que le code correspond exactement',
            'Le format doit être exactement 4 chiffres',
            'Pas d\'espaces ou caractères spéciaux',
            'Rejeter si le code ne correspond pas'
        ],
        quick_responses=[
            '❌ Code 4 DIGITS incorrect - REJET',
            '⚠️ Format 4 DIGITS invalide',
            '📞 Contacter fournisseur - Code erroné'
        ],
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.WALMART_SPECIFIC,
        auto_reject=True
    ),

    # ===== ERREURS DE MISE EN PAGE =====

    'facing_mismatch': ErrorTemplate(
        code='facing_mismatch',
        title='Facing incorrect',
        template='Facing attendu: {expected}, Trouvé: {found}',
        suggestions=[
            'Vérifier le planogramme',
            'Confirmer avec le retail',
            'Vérifier si c\'est intentionnel',
            'Documenter la raison si approuvé'
        ],
        quick_responses=[
            '⚠️ Facing incorrect - Vérifier planogramme',
            '✅ Facing différent mais validé par retail',
            '❌ Facing incorrect - Refaire layout',
            '📞 Contacter planogramme pour confirmation'
        ],
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.LAYOUT,
        auto_reject=False
    ),

    'mixed_facings': ErrorTemplate(
        code='mixed_facings',
        title='Mixed Facings détecté',
        template='Mixed facings détecté: {facings}',
        suggestions=[
            'Vérifier si c\'est intentionnel selon le planogramme',
            'Confirmer avec le département retail',
            'Documenter la raison si approuvé',
            'Rejeter si non conforme au plan'
        ],
        quick_responses=[
            '⚠️ Mixed facings - Validé par retail',
            '⚠️ Mixed facings - Conforme au planogramme',
            '❌ Mixed facings non autorisé - Refaire',
            '📞 Contacter retail pour validation'
        ],
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.LAYOUT,
        auto_reject=False
    ),

    'space_saver_issue': ErrorTemplate(
        code='space_saver_issue',
        title='Problème Space Saver',
        template='Space Saver: {issue}',
        suggestions=[
            'Vérifier l\'emplacement du Space Saver',
            'Confirmer avec le planogramme',
            'Vérifier les dimensions',
            'S\'assurer que c\'est conforme'
        ],
        quick_responses=[
            '⚠️ Space Saver mal positionné',
            '✅ Space Saver conforme',
            '❌ Space Saver incorrect - Refaire',
            '📞 Contacter planogramme'
        ],
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.LAYOUT,
        auto_reject=False
    ),

    # ===== ERREURS DE CONTENU =====

    'wrong_product': ErrorTemplate(
        code='wrong_product',
        title='Mauvais produit',
        template='Produit incorrect: attendu "{expected}", trouvé "{found}"',
        suggestions=[
            'Vérifier que le PDF correspond au bon produit',
            'Vérifier le code produit',
            'REJET IMMÉDIAT si mauvais produit',
            'Contacter le fournisseur'
        ],
        quick_responses=[
            '❌ MAUVAIS PRODUIT - REJET IMMÉDIAT',
            '❌ PDF ne correspond pas à la commande',
            '📞 URGENCE: Mauvais fichier reçu'
        ],
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.CONTENT,
        auto_reject=True
    ),

    'missing_mandatory_info': ErrorTemplate(
        code='missing_mandatory_info',
        title='Information obligatoire manquante',
        template='Information manquante: {info}',
        suggestions=[
            'Vérifier les exigences du projet',
            'Rejeter si information obligatoire',
            'Documenter l\'information manquante',
            'Contacter le fournisseur'
        ],
        quick_responses=[
            '❌ Information obligatoire manquante - REJET',
            '⚠️ Information recommandée manquante',
            '📞 Demander complément d\'information'
        ],
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.CONTENT,
        auto_reject=True
    ),
}


class ErrorAnalyzer:
    """Analyse les résultats de validation et génère des erreurs appropriées"""

    def __init__(self):
        self.templates = ERROR_TEMPLATES

    def analyze_validation_results(self, validation_results: List[Dict],
                                   excel_data: List[Dict],
                                   check_digits: bool = False) -> List[Dict]:
        """
        Analyse les résultats de validation et génère une liste d'erreurs détaillées

        Returns:
            Liste de dicts avec: {
                'error_code': str,
                'template': ErrorTemplate,
                'context': dict,  # Variables pour le template
                'row_index': int
            }
        """
        errors = []

        for idx, (validation, data) in enumerate(zip(validation_results, excel_data)):
            # Ignorer les FRAME et SPACE_SAVER
            if validation.get('is_frame') or validation.get('is_space_saver'):
                continue

            # Analyser chaque type d'erreur

            # 1. Erreurs de nom de teinte
            if not validation.get('shade_name', True):
                shade_name = data.get('SHADE NAME', '')
                if shade_name:
                    errors.append({
                        'error_code': 'shade_name_mismatch',
                        'template': self.templates['shade_name_mismatch'],
                        'context': {
                            'expected': shade_name,
                            'found': 'Non trouvé ou différent'
                        },
                        'row_index': idx
                    })
                else:
                    errors.append({
                        'error_code': 'shade_name_missing',
                        'template': self.templates['shade_name_missing'],
                        'context': {
                            'expected': shade_name or 'Nom attendu'
                        },
                        'row_index': idx
                    })

            # 2. Erreurs de numéro de teinte
            if not validation.get('shade_number', True):
                shade_number = data.get('SHADE NUMBER', '')
                if shade_number:
                    errors.append({
                        'error_code': 'shade_number_mismatch',
                        'template': self.templates['shade_number_mismatch'],
                        'context': {
                            'expected': shade_number,
                            'found': 'Non trouvé ou différent'
                        },
                        'row_index': idx
                    })

            # 3. Erreurs 4 DIGITS (si check_digits activé)
            if check_digits and not validation.get('digits', True):
                digits = data.get('4 DIGITS', '')
                if digits:
                    errors.append({
                        'error_code': 'missing_4digits',
                        'template': self.templates['missing_4digits'],
                        'context': {
                            'expected': digits
                        },
                        'row_index': idx
                    })

            # 4. Mixed facings
            if validation.get('is_mixed'):
                errors.append({
                    'error_code': 'mixed_facings',
                    'template': self.templates['mixed_facings'],
                    'context': {
                        'facings': validation.get('facing', 'Multiple')
                    },
                    'row_index': idx
                })

        return errors

    def get_error_summary(self, errors: List[Dict]) -> Dict:
        """Génère un résumé des erreurs détectées"""
        summary = {
            'total_errors': len(errors),
            'critical_errors': 0,
            'high_errors': 0,
            'medium_errors': 0,
            'low_errors': 0,
            'auto_reject_recommended': False,
            'categories': {}
        }

        for error in errors:
            template = error['template']

            # Compter par sévérité
            if template.severity == ErrorSeverity.CRITICAL:
                summary['critical_errors'] += 1
                if template.auto_reject:
                    summary['auto_reject_recommended'] = True
            elif template.severity == ErrorSeverity.HIGH:
                summary['high_errors'] += 1
            elif template.severity == ErrorSeverity.MEDIUM:
                summary['medium_errors'] += 1
            else:
                summary['low_errors'] += 1

            # Compter par catégorie
            category = template.category.value
            summary['categories'][category] = summary['categories'].get(category, 0) + 1

        return summary

    def format_error_message(self, error: Dict) -> str:
        """Formate un message d'erreur complet à partir du template"""
        template = error['template']
        context = error.get('context', {})

        # Remplir le template
        message = template.template.format(**context)

        # Ajouter le titre
        full_message = f"{template.title}: {message}"

        return full_message

    def get_quick_response_suggestions(self, errors: List[Dict]) -> List[str]:
        """
        Retourne une liste de réponses rapides suggérées basées sur les erreurs
        Priorise les erreurs les plus critiques
        """
        if not errors:
            return ["✅ Validation réussie - Aucune erreur détectée"]

        suggestions = set()

        # Grouper les erreurs par template
        error_counts = {}
        for error in errors:
            code = error['error_code']
            error_counts[code] = error_counts.get(code, 0) + 1

        # Sélectionner les quick responses des erreurs les plus fréquentes
        for code, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            template = self.templates.get(code)
            if template and template.quick_responses:
                suggestions.add(template.quick_responses[0])  # Prendre la première suggestion

        return list(suggestions)
