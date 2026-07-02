# core/data_collector.py
from typing import Dict, List, Any
from datetime import datetime

class ValidationDataCollector:
    """Collecte et organise toutes les données de validation pour l'export"""
    
    def __init__(self, session_manager, pdf_processor, excel_processor, validator):
        self.session_manager = session_manager
        self.pdf_processor = pdf_processor
        self.excel_processor = excel_processor
        self.validator = validator
    
    def collect_all_validation_data(self) -> Dict[str, Any]:
        """Collecte toutes les données de validation de la session"""
        
        # Informations de base
        session_info = self.session_manager.get_session_info()
        all_litho_codes = self.pdf_processor.get_all_litho_codes()
        
        # Collecte des résultats de validation
        validation_results = []
        litho_details = []
        
        for litho_code in all_litho_codes:
            # Récupérer les données Excel pour cette litho
            excel_data = self.excel_processor.get_data_for_litho(litho_code)
            
            if excel_data:
                # Récupérer le texte PDF
                pdf_text = self.pdf_processor.get_text_for_litho(litho_code)
                
                # Effectuer la validation
                validation_result = self.validator.validate(pdf_text, excel_data)
                
                # Statut de validation de la session
                session_status = self.session_manager.get_litho_status(litho_code)
                
                # Analyser les résultats
                litho_summary = self._analyze_litho_results(
                    litho_code, excel_data, validation_result, session_status
                )
                
                validation_results.append(litho_summary)
                
                # Détails ligne par ligne
                for i, (data_row, validation_row) in enumerate(zip(excel_data, validation_result)):
                    detail_row = self._create_detail_row(
                        litho_code, i, data_row, validation_row, session_status
                    )
                    litho_details.append(detail_row)
        
        # Statistiques globales
        global_stats = self._calculate_global_statistics(validation_results)
        
        return {
            'session_info': session_info,
            'global_statistics': global_stats,
            'litho_summaries': validation_results,
            'litho_details': litho_details,
            'generation_date': datetime.now().isoformat(),
            'validator_settings': {
                'check_digits': self.validator.check_digits
            }
        }
    
    def _analyze_litho_results(self, litho_code, excel_data, validation_result, session_status):
        """Analyse les résultats pour une litho spécifique"""
        
        # Détecter le type de litho
        is_cubby = validation_result and validation_result[0].get('is_cubby', False)
        is_mixed = validation_result and validation_result[0].get('is_mixed', False)
        has_space_savers = any(v.get('is_space_saver', False) for v in validation_result) if validation_result else False
        
        # Calculer les statistiques de validation
        if is_cubby:
            # Pour les CUBBY
            dimensions = validation_result[0].get('cubby_dimensions', (0, 0))
            faces, tiers = dimensions
            
            return {
                'litho_code': litho_code,
                'type': 'CUBBY',
                'description': validation_result[0].get('description', ''),
                'dimensions': f"{faces}F x {tiers}T",
                'total_positions': faces * tiers,
                'validation_status': 'N/A',
                'session_status': session_status['status'] if session_status else 'pending',
                'session_comment': session_status['comment'] if session_status else '',
                'session_date': session_status['date'] if session_status else '',
                'products_count': len(excel_data),
                'overall_success': True,  # CUBBY sont considérés comme valides
                'shade_number_success': 'N/A',
                'shade_name_success': 'N/A',
                'digits_success': 'N/A'
            }
        else:
            # Pour les lithos normales
            valid_products = [v for v in validation_result 
                            if not v.get('is_frame') and not v.get('is_space_saver')] if validation_result else []
            
            if valid_products:
                total_valid = len(valid_products)
                shade_number_ok = sum(1 for v in valid_products if v.get('shade_number', False))
                shade_name_ok = sum(1 for v in valid_products if v.get('shade_name', False))
                digits_ok = sum(1 for v in valid_products if v.get('digits', False))
                overall_ok = sum(1 for v in valid_products if v.get('overall', False))
                
                # Types de litho
                litho_types = []
                if is_mixed:
                    litho_types.append('MIXED')
                if has_space_savers:
                    litho_types.append('SPACE_SAVER')
                litho_type = ' + '.join(litho_types) if litho_types else 'Standard'
                
                return {
                    'litho_code': litho_code,
                    'type': litho_type,
                    'description': excel_data[0].get('DECRIPTION', '') if excel_data else '',
                    'products_count': len(excel_data),
                    'valid_products_count': total_valid,
                    'session_status': session_status['status'] if session_status else 'pending',
                    'session_comment': session_status['comment'] if session_status else '',
                    'session_date': session_status['date'] if session_status else '',
                    'overall_success': f"{overall_ok}/{total_valid}" if total_valid > 0 else "0/0",
                    'overall_percentage': round((overall_ok / total_valid) * 100, 1) if total_valid > 0 else 0,
                    'shade_number_success': f"{shade_number_ok}/{total_valid}",
                    'shade_number_percentage': round((shade_number_ok / total_valid) * 100, 1) if total_valid > 0 else 0,
                    'shade_name_success': f"{shade_name_ok}/{total_valid}",
                    'shade_name_percentage': round((shade_name_ok / total_valid) * 100, 1) if total_valid > 0 else 0,
                    'digits_success': f"{digits_ok}/{total_valid}" if self.validator.check_digits else 'N/A',
                    'digits_percentage': round((digits_ok / total_valid) * 100, 1) if self.validator.check_digits and total_valid > 0 else 'N/A'
                }
            else:
                return {
                    'litho_code': litho_code,
                    'type': 'Aucun produit',
                    'description': '',
                    'products_count': len(excel_data) if excel_data else 0,
                    'valid_products_count': 0,
                    'session_status': session_status['status'] if session_status else 'pending',
                    'session_comment': session_status['comment'] if session_status else '',
                    'session_date': session_status['date'] if session_status else '',
                    'overall_success': '0/0',
                    'overall_percentage': 0,
                    'shade_number_success': '0/0',
                    'shade_number_percentage': 0,
                    'shade_name_success': '0/0',
                    'shade_name_percentage': 0,
                    'digits_success': '0/0',
                    'digits_percentage': 0
                }
    
    def _create_detail_row(self, litho_code, row_index, data_row, validation_row, session_status):
        """Crée une ligne de détail pour l'export"""
        return {
            'litho_code': litho_code,
            'row_index': row_index + 1,
            'upc': data_row.get('UPC', ''),
            'product_description': data_row.get('PRODUCT DESCRIPTION', ''),
            'shade_name': data_row.get('SHADE NAME', ''),
            'shade_number': data_row.get('SHADE NUMBER', ''),
            'product_facing': data_row.get('PRODUCT FACING SL', ''),
            'digits_4': data_row.get('4 DIGITS', ''),
            'is_frame': validation_row.get('is_frame', False),
            'is_space_saver': validation_row.get('is_space_saver', False),
            'shade_number_valid': validation_row.get('shade_number', False) if not validation_row.get('is_frame') and not validation_row.get('is_space_saver') else 'N/A',
            'shade_name_valid': validation_row.get('shade_name', False) if not validation_row.get('is_frame') and not validation_row.get('is_space_saver') else 'N/A',
            'digits_valid': validation_row.get('digits', False) if not validation_row.get('is_frame') and not validation_row.get('is_space_saver') and self.validator.check_digits else 'N/A',
            'overall_valid': validation_row.get('overall', False) if not validation_row.get('is_frame') and not validation_row.get('is_space_saver') else 'N/A',
            'session_status': session_status['status'] if session_status else 'pending'
        }
    
    def _calculate_global_statistics(self, litho_summaries):
        """Calcule les statistiques globales"""
        total_lithos = len(litho_summaries)
        
        # Compter par statut de session
        approved_count = sum(1 for l in litho_summaries if l.get('session_status') == 'approved')
        rejected_count = sum(1 for l in litho_summaries if l.get('session_status') == 'rejected')
        pending_count = total_lithos - approved_count - rejected_count
        
        # Compter par type
        cubby_count = sum(1 for l in litho_summaries if l.get('type') == 'CUBBY')
        mixed_count = sum(1 for l in litho_summaries if 'MIXED' in l.get('type', ''))
        space_saver_count = sum(1 for l in litho_summaries if 'SPACE_SAVER' in l.get('type', ''))
        standard_count = sum(1 for l in litho_summaries if l.get('type') == 'Standard')
        
        # Statistiques de validation (pour les lithos non-CUBBY)
        non_cubby_lithos = [l for l in litho_summaries if l.get('type') != 'CUBBY']
        
        if non_cubby_lithos:
            avg_overall = sum(l.get('overall_percentage', 0) for l in non_cubby_lithos) / len(non_cubby_lithos)
            avg_shade_number = sum(l.get('shade_number_percentage', 0) for l in non_cubby_lithos) / len(non_cubby_lithos)
            avg_shade_name = sum(l.get('shade_name_percentage', 0) for l in non_cubby_lithos) / len(non_cubby_lithos)
            
            digits_lithos = [l for l in non_cubby_lithos if l.get('digits_percentage') != 'N/A']
            avg_digits = sum(l.get('digits_percentage', 0) for l in digits_lithos) / len(digits_lithos) if digits_lithos else 0
        else:
            avg_overall = avg_shade_number = avg_shade_name = avg_digits = 0
        
        return {
            'total_lithos': total_lithos,
            'approved_lithos': approved_count,
            'rejected_lithos': rejected_count,
            'pending_lithos': pending_count,
            'cubby_lithos': cubby_count,
            'mixed_lithos': mixed_count,
            'space_saver_lithos': space_saver_count,
            'standard_lithos': standard_count,
            'avg_overall_success': round(avg_overall, 1),
            'avg_shade_number_success': round(avg_shade_number, 1),
            'avg_shade_name_success': round(avg_shade_name, 1),
            'avg_digits_success': round(avg_digits, 1) if avg_digits > 0 else 'N/A',
            'digits_validation_enabled': self.validator.check_digits
        }