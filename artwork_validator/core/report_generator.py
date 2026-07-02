# core/report_generator.py
import pandas as pd
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self, pdf_processor=None):
        """Initialise le générateur de rapport avec le processeur PDF"""
        self.pdf_processor = pdf_processor
    
    def generate_report(self, file_path, collected_data):
        """Génère un rapport à partir des données collectées"""
        if file_path.endswith('.xlsx'):
            self.generate_excel_report(file_path, collected_data)
        elif file_path.endswith('.pdf'):
            self.generate_pdf_report(file_path, collected_data)
            
    def generate_excel_report(self, file_path, collected_data):
        """Génère un rapport Excel détaillé"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                
                # Feuille 1: Résumé de session
                session_summary = self._create_session_summary(collected_data)
                session_summary.to_excel(writer, sheet_name='Résumé Session', index=False)
                
                # Feuille 2: Statistiques globales
                global_stats = self._create_global_stats_df(collected_data)
                global_stats.to_excel(writer, sheet_name='Statistiques Globales', index=False)
                
                # Feuille 3: Résumé par litho avec descriptions PDF et statut
                litho_summaries = self._create_enhanced_litho_summaries(collected_data)
                if not litho_summaries.empty:
                    # Réorganiser les colonnes pour plus de clarté (avec les nouvelles colonnes)
                    column_order = [
                        'litho_code', 'type', 'session_status', 'validation_status', 
                        'pdf_description', 'pdf_validation_status', 'products_count', 
                        'valid_products_count', 'overall_success', 'overall_percentage',
                        'shade_number_success', 'shade_number_percentage',
                        'shade_name_success', 'shade_name_percentage',
                        'digits_success', 'digits_percentage',
                        'description', 'session_comment', 'session_date'
                    ]
                    litho_summaries = litho_summaries.reindex(columns=[col for col in column_order if col in litho_summaries.columns])
                    
                litho_summaries.to_excel(writer, sheet_name='Résumé par Litho', index=False)
                
                # Feuille 4: Détails complets
                litho_details = pd.DataFrame(collected_data['litho_details'])
                if not litho_details.empty:
                    litho_details.to_excel(writer, sheet_name='Détails Complets', index=False)
                
                # Feuille 5: Lithos en attente
                pending_lithos = [l for l in collected_data['litho_summaries'] if l.get('session_status') == 'pending']
                if pending_lithos:
                    pending_df = self._enhance_pending_lithos_data(pending_lithos)
                    pending_df.to_excel(writer, sheet_name='Lithos en Attente', index=False)
                
                # Feuille 6: Lithos rejetées
                rejected_lithos = [l for l in collected_data['litho_summaries'] if l.get('session_status') == 'rejected']
                if rejected_lithos:
                    rejected_df = self._enhance_rejected_lithos_data(rejected_lithos)
                    rejected_df.to_excel(writer, sheet_name='Lithos Rejetées', index=False)
                
                # NOUVELLE FEUILLE 7: Analyse des PDFs
                pdf_analysis = self._create_pdf_analysis(collected_data)
                if not pdf_analysis.empty:
                    pdf_analysis.to_excel(writer, sheet_name='Analyse PDFs', index=False)
                
                # NOUVELLE FEUILLE 8: Statuts de Validation
                validation_summary = self._create_validation_summary(collected_data)
                if not validation_summary.empty:
                    validation_summary.to_excel(writer, sheet_name='Statuts Validation', index=False)
                
                print(f"Rapport Excel généré avec succès: {file_path}")
                
        except Exception as e:
            print(f"Erreur lors de la génération du rapport Excel: {e}")
            raise
    
    def _create_enhanced_litho_summaries(self, collected_data):
        """Crée un DataFrame amélioré avec les descriptions PDF et statuts de validation"""
        litho_summaries = pd.DataFrame(collected_data['litho_summaries'])
        
        if litho_summaries.empty:
            return litho_summaries
        
        # Ajouter les informations PDF pour chaque litho
        pdf_descriptions = []
        pdf_validation_statuses = []
        validation_statuses = []
        
        for _, row in litho_summaries.iterrows():
            litho_code = row.get('litho_code', '')
            
            # Extraire la description du PDF
            pdf_description = self._extract_pdf_description(litho_code)
            pdf_descriptions.append(pdf_description)
            
            # Déterminer le statut de validation du PDF
            pdf_validation_status = self._get_pdf_validation_status(litho_code, pdf_description)
            pdf_validation_statuses.append(pdf_validation_status)
            
            # Statut de validation général
            session_status = row.get('session_status', 'pending')
            validation_status = self._map_session_to_validation_status(session_status)
            validation_statuses.append(validation_status)
        
        # Ajouter les nouvelles colonnes
        litho_summaries['validation_status'] = validation_statuses
        litho_summaries['pdf_description'] = pdf_descriptions
        litho_summaries['pdf_validation_status'] = pdf_validation_statuses
        
        return litho_summaries
    
    def _extract_pdf_description(self, litho_code):
        """Extrait la description du fichier PDF pour un code litho donné"""
        if not self.pdf_processor or not litho_code:
            return "PDF non disponible"
        
        try:
            # Récupérer le texte du PDF
            pdf_text = self.pdf_processor.get_text_for_litho(litho_code)
            
            if not pdf_text:
                return "PDF vide ou illisible"
            
            # Extraire une description significative (premier paragraphe ou section titre)
            lines = pdf_text.split('\n')
            description_lines = []
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Ignorer les lignes trop courtes
                    description_lines.append(line)
                    if len(description_lines) >= 3:  # Prendre les 3 premières lignes significatives
                        break
            
            if description_lines:
                description = ' | '.join(description_lines)
                # Tronquer si trop long
                if len(description) > 200:
                    description = description[:197] + "..."
                return description
            else:
                return "Description non identifiable"
                
        except Exception as e:
            return f"Erreur extraction: {str(e)[:50]}"
    
    def _get_pdf_validation_status(self, litho_code, pdf_description):
        """Détermine le statut de validation du PDF basé sur son contenu"""
        if not pdf_description or pdf_description in ["PDF non disponible", "PDF vide ou illisible"]:
            return "❌ PDF Invalide"
        
        if "Erreur extraction" in pdf_description:
            return "⚠️ Erreur Lecture"
        
        if "Description non identifiable" in pdf_description:
            return "⚠️ Contenu Unclear"
        
        # Vérifications de base du contenu
        pdf_description_lower = pdf_description.lower()
        
        # Mots-clés positifs pour L'Oréal
        positive_keywords = ['loreal', 'l\'oreal', 'cosmetic', 'beauty', 'shade', 'color', 'teinte', 'produit']
        negative_keywords = ['error', 'erreur', 'invalid', 'corrupt']
        
        has_positive = any(keyword in pdf_description_lower for keyword in positive_keywords)
        has_negative = any(keyword in pdf_description_lower for keyword in negative_keywords)
        
        if has_negative:
            return "❌ Contenu Problématique"
        elif has_positive:
            return "✅ PDF Valide"
        else:
            return "⚠️ À Vérifier"
    
    def _map_session_to_validation_status(self, session_status):
        """Mappe le statut de session vers un statut de validation plus explicite"""
        status_mapping = {
            'approved': '✅ Approuvé',
            'rejected': '❌ Rejeté', 
            'pending': '⏳ En Attente',
            None: '❓ Indéterminé'
        }
        return status_mapping.get(session_status, '❓ Indéterminé')
    
    def _enhance_pending_lithos_data(self, pending_lithos):
        """Améliore les données des lithos en attente avec les infos PDF"""
        df = pd.DataFrame(pending_lithos)
        
        if not df.empty and 'litho_code' in df.columns:
            df['pdf_description'] = df['litho_code'].apply(self._extract_pdf_description)
            df['pdf_validation_status'] = df.apply(
                lambda row: self._get_pdf_validation_status(row['litho_code'], row['pdf_description']), 
                axis=1
            )
        
        return df
    
    def _enhance_rejected_lithos_data(self, rejected_lithos):
        """Améliore les données des lithos rejetées avec les infos PDF"""
        df = pd.DataFrame(rejected_lithos)
        
        if not df.empty and 'litho_code' in df.columns:
            df['pdf_description'] = df['litho_code'].apply(self._extract_pdf_description)
            df['pdf_validation_status'] = df.apply(
                lambda row: self._get_pdf_validation_status(row['litho_code'], row['pdf_description']), 
                axis=1
            )
        
        return df
    
    def _create_pdf_analysis(self, collected_data):
        """Crée une analyse détaillée des PDFs"""
        if not self.pdf_processor:
            return pd.DataFrame()
        
        pdf_analysis_data = []
        litho_summaries = collected_data.get('litho_summaries', [])
        
        for litho_data in litho_summaries:
            litho_code = litho_data.get('litho_code', '')
            if not litho_code:
                continue
            
            # Informations PDF détaillées
            pdf_text = self.pdf_processor.get_text_for_litho(litho_code) if self.pdf_processor else ""
            pdf_description = self._extract_pdf_description(litho_code)
            pdf_validation_status = self._get_pdf_validation_status(litho_code, pdf_description)
            
            # Statistiques du texte PDF
            word_count = len(pdf_text.split()) if pdf_text else 0
            char_count = len(pdf_text) if pdf_text else 0
            line_count = len(pdf_text.split('\n')) if pdf_text else 0
            
            # Analyse du contenu
            contains_product_info = any(keyword in pdf_text.lower() for keyword in ['shade', 'teinte', 'color', 'couleur']) if pdf_text else False
            contains_codes = any(keyword in pdf_text for keyword in ['YCA', 'CUBBY', 'MIXED']) if pdf_text else False
            
            pdf_analysis_data.append({
                'litho_code': litho_code,
                'pdf_description': pdf_description,
                'pdf_validation_status': pdf_validation_status,
                'word_count': word_count,
                'character_count': char_count,
                'line_count': line_count,
                'contains_product_info': '✅ Oui' if contains_product_info else '❌ Non',
                'contains_codes': '✅ Oui' if contains_codes else '❌ Non',
                'pdf_size_category': self._categorize_pdf_size(word_count),
                'session_status': litho_data.get('session_status', 'pending')
            })
        
        return pd.DataFrame(pdf_analysis_data)
    
    def _categorize_pdf_size(self, word_count):
        """Catégorise la taille du PDF basée sur le nombre de mots"""
        if word_count == 0:
            return "Vide"
        elif word_count < 50:
            return "Très petit"
        elif word_count < 200:
            return "Petit"
        elif word_count < 500:
            return "Moyen"
        elif word_count < 1000:
            return "Grand"
        else:
            return "Très grand"
    
    def _create_validation_summary(self, collected_data):
        """Crée un résumé des statuts de validation"""
        validation_data = []
        litho_summaries = collected_data.get('litho_summaries', [])
        
        # Compteurs par statut
        status_counts = {'approved': 0, 'rejected': 0, 'pending': 0}
        pdf_status_counts = {'✅ PDF Valide': 0, '❌ PDF Invalide': 0, '⚠️ À Vérifier': 0, '⚠️ Erreur Lecture': 0, '⚠️ Contenu Unclear': 0, '❌ Contenu Problématique': 0}
        
        for litho_data in litho_summaries:
            session_status = litho_data.get('session_status', 'pending')
            if session_status in status_counts:
                status_counts[session_status] += 1
            
            litho_code = litho_data.get('litho_code', '')
            pdf_description = self._extract_pdf_description(litho_code)
            pdf_validation_status = self._get_pdf_validation_status(litho_code, pdf_description)
            
            if pdf_validation_status in pdf_status_counts:
                pdf_status_counts[pdf_validation_status] += 1
        
        # Résumé des statuts de session
        for status, count in status_counts.items():
            validation_data.append({
                'Catégorie': 'Statut Session',
                'Type': self._map_session_to_validation_status(status),
                'Nombre': count,
                'Pourcentage': f"{(count / len(litho_summaries) * 100):.1f}%" if litho_summaries else "0%",
                'Description': f"Lithos avec statut de session: {status}"
            })
        
        # Résumé des statuts PDF
        for pdf_status, count in pdf_status_counts.items():
            if count > 0:  # Inclure seulement les statuts avec au moins 1 occurrence
                validation_data.append({
                    'Catégorie': 'Statut PDF',
                    'Type': pdf_status,
                    'Nombre': count,
                    'Pourcentage': f"{(count / len(litho_summaries) * 100):.1f}%" if litho_summaries else "0%",
                    'Description': f"PDFs avec statut: {pdf_status}"
                })
        
        return pd.DataFrame(validation_data)
    
    def _create_session_summary(self, collected_data):
        """Crée un DataFrame avec le résumé de session (version améliorée)"""
        session_info = collected_data['session_info']
        global_stats = collected_data['global_statistics']
        
        # Statistiques PDF si disponibles
        pdf_stats = self._get_pdf_statistics(collected_data)
        
        summary_data = [
            ['Nom de la Session', session_info.get('name', 'Non défini')],
            ['Date de Création', session_info.get('created', '')[:19] if session_info.get('created') else 'Non définie'],
            ['Dernière Modification', session_info.get('updated', '')[:19] if session_info.get('updated') else 'Non définie'],
            ['Date de Génération du Rapport', collected_data['generation_date'][:19]],
            ['', ''],
            ['Dossier PDFs', session_info.get('pdf_folder', 'Non défini')],
            ['Fichier Excel', os.path.basename(session_info.get('excel_file', 'Non défini'))],
            ['Fichier Session', session_info.get('file_path', 'Non sauvegardé')],
            ['', ''],
            ['Total Lithos', global_stats.get('total_lithos', 0)],
            ['Lithos Approuvées', global_stats.get('approved_lithos', 0)],
            ['Lithos Rejetées', global_stats.get('rejected_lithos', 0)],
            ['Lithos en Attente', global_stats.get('pending_lithos', 0)],
            ['', ''],
            # Nouvelles statistiques PDF
            ['📄 STATISTIQUES PDF', ''],
            ['PDFs Valides', pdf_stats.get('valid_pdfs', 0)],
            ['PDFs Invalides', pdf_stats.get('invalid_pdfs', 0)],
            ['PDFs à Vérifier', pdf_stats.get('to_verify_pdfs', 0)],
            ['PDFs avec Erreurs', pdf_stats.get('error_pdfs', 0)],
            ['', ''],
            ['Vérification 4 DIGITS', 'Activée' if collected_data['validator_settings']['check_digits'] else 'Désactivée'],
            ['Lithos CUBBY', global_stats.get('cubby_lithos', 0)],
            ['Lithos MIXED', global_stats.get('mixed_lithos', 0)],
            ['Lithos SPACE SAVER', global_stats.get('space_saver_lithos', 0)],
            ['Lithos Standard', global_stats.get('standard_lithos', 0)]
        ]
        
        return pd.DataFrame(summary_data, columns=['Paramètre', 'Valeur'])
    
    def _get_pdf_statistics(self, collected_data):
        """Calcule des statistiques sur les PDFs"""
        if not self.pdf_processor:
            return {'valid_pdfs': 0, 'invalid_pdfs': 0, 'to_verify_pdfs': 0, 'error_pdfs': 0}
        
        stats = {'valid_pdfs': 0, 'invalid_pdfs': 0, 'to_verify_pdfs': 0, 'error_pdfs': 0}
        litho_summaries = collected_data.get('litho_summaries', [])
        
        for litho_data in litho_summaries:
            litho_code = litho_data.get('litho_code', '')
            if litho_code:
                pdf_description = self._extract_pdf_description(litho_code)
                pdf_validation_status = self._get_pdf_validation_status(litho_code, pdf_description)
                
                if '✅' in pdf_validation_status:
                    stats['valid_pdfs'] += 1
                elif '❌' in pdf_validation_status:
                    stats['invalid_pdfs'] += 1
                elif '⚠️' in pdf_validation_status:
                    if 'Erreur' in pdf_validation_status:
                        stats['error_pdfs'] += 1
                    else:
                        stats['to_verify_pdfs'] += 1
        
        return stats
    
    def _create_global_stats_df(self, collected_data):
        """Crée un DataFrame avec les statistiques globales détaillées (version améliorée)"""
        global_stats = collected_data['global_statistics']
        pdf_stats = self._get_pdf_statistics(collected_data)
        
        stats_data = [
            ['Métrique', 'Valeur', 'Description'],
            ['Total Lithos', global_stats.get('total_lithos', 0), 'Nombre total de lithos dans la session'],
            ['', '', ''],
            ['STATUTS DE SESSION', '', ''],
            ['Approuvées', global_stats.get('approved_lithos', 0), 'Lithos validées et approuvées'],
            ['Rejetées', global_stats.get('rejected_lithos', 0), 'Lithos rejetées nécessitant une révision'],
            ['En Attente', global_stats.get('pending_lithos', 0), 'Lithos non encore validées'],
            ['', '', ''],
            ['STATUTS PDF', '', ''],
            ['PDFs Valides', pdf_stats.get('valid_pdfs', 0), 'PDFs avec contenu valide et lisible'],
            ['PDFs Invalides', pdf_stats.get('invalid_pdfs', 0), 'PDFs non disponibles ou illisibles'],
            ['PDFs à Vérifier', pdf_stats.get('to_verify_pdfs', 0), 'PDFs nécessitant une vérification manuelle'],
            ['PDFs avec Erreurs', pdf_stats.get('error_pdfs', 0), 'PDFs avec erreurs de lecture'],
            ['', '', ''],
            ['TYPES DE LITHOS', '', ''],
            ['CUBBY', global_stats.get('cubby_lithos', 0), 'Lithos de type CUBBY (pas de validation de produits)'],
            ['MIXED Facings', global_stats.get('mixed_lithos', 0), 'Lithos avec facings mélangés'],
            ['SPACE SAVER', global_stats.get('space_saver_lithos', 0), 'Lithos contenant des space savers'],
            ['Standard', global_stats.get('standard_lithos', 0), 'Lithos de type standard'],
            ['', '', ''],
            ['MOYENNES DE VALIDATION', '', ''],
            ['Succès Global Moyen', f"{global_stats.get('avg_overall_success', 0)}%", 'Pourcentage moyen de réussite globale'],
            ['Succès Teintes Moyen', f"{global_stats.get('avg_shade_number_success', 0)}%", 'Pourcentage moyen de réussite des numéros de teinte'],
            ['Succès Noms Moyen', f"{global_stats.get('avg_shade_name_success', 0)}%", 'Pourcentage moyen de réussite des noms de teinte'],
            ['Succès 4 DIGITS Moyen', f"{global_stats.get('avg_digits_success', 'N/A')}", 'Pourcentage moyen de réussite des 4 DIGITS (si activé)']
        ]
        
        return pd.DataFrame(stats_data[1:], columns=stats_data[0])  # Exclure la ligne d'en-tête
            
    def generate_pdf_report(self, file_path, collected_data):
        """Génère un rapport PDF (à implémenter si nécessaire)"""
        # TODO: Implémenter la génération PDF avec ReportLab
        print(f"Génération PDF non encore implémentée pour: {file_path}")
        pass