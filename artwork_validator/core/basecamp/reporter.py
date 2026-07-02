"""
Module de reporting pour BaseCamp
Gère la génération de rapports détaillés et les statistiques
"""

import json
import logging
import os
from datetime import datetime
from difflib import SequenceMatcher


class BaseCampReporter:
    """Gestionnaire de rapports et statistiques pour BaseCamp"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.save_reports = True  # Configuration par défaut

    def create_detailed_report(self, results, detailed_log, session_start_time=None):
        """Crée un rapport détaillé avec traçabilité complète"""
        try:
            # Informations de session
            session_info = {
                'start_time': session_start_time or datetime.now(),
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
                'statistics': self.calculate_statistics(detailed_log),
                'recommendations': self.generate_recommendations(results, detailed_log),
                'report_version': '2.0'
            }

            # Sauvegarder le rapport si configuré
            if self.save_reports:
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

    def calculate_statistics(self, detailed_log):
        """Calcule des statistiques avancées sur le traitement"""
        try:
            if not detailed_log:
                return {}

            # Temps de traitement par fichier
            processing_times = []
            matching_strategies = {}
            error_types = {}
            file_found_count = 0
            comment_added_count = 0

            for entry in detailed_log:
                if 'processing_time' in entry:
                    processing_times.append(entry['processing_time'])

                if 'matching_strategy' in entry and entry['matching_strategy']:
                    strategy = entry['matching_strategy']
                    matching_strategies[strategy] = matching_strategies.get(strategy, 0) + 1

                if 'error_type' in entry and entry['error_type']:
                    error_type = entry['error_type']
                    error_types[error_type] = error_types.get(error_type, 0) + 1

                if entry.get('file_found', False):
                    file_found_count += 1

                if entry.get('comment_added', False):
                    comment_added_count += 1

            # Calculs statistiques
            total_files = len(detailed_log)
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

            stats = {
                'total_files_processed': total_files,
                'files_found_count': file_found_count,
                'files_found_ratio': file_found_count / total_files if total_files > 0 else 0,
                'comments_added_count': comment_added_count,
                'comments_success_ratio': comment_added_count / file_found_count if file_found_count > 0 else 0,
                'avg_processing_time': avg_time,
                'max_processing_time': max(processing_times) if processing_times else 0,
                'min_processing_time': min(processing_times) if processing_times else 0,
                'total_processing_time': sum(processing_times),
                'matching_strategies_used': matching_strategies,
                'error_breakdown': error_types,
                'performance_metrics': self._calculate_performance_metrics(processing_times)
            }

            return stats

        except Exception as e:
            self.logger.debug(f"Erreur calcul statistiques: {e}")
            return {}

    def _calculate_performance_metrics(self, processing_times):
        """Calcule des métriques de performance détaillées"""
        if not processing_times:
            return {}

        sorted_times = sorted(processing_times)
        n = len(sorted_times)

        return {
            'median_time': sorted_times[n // 2],
            'percentile_75': sorted_times[int(n * 0.75)] if n > 0 else 0,
            'percentile_90': sorted_times[int(n * 0.90)] if n > 0 else 0,
            'percentile_95': sorted_times[int(n * 0.95)] if n > 0 else 0,
            'slow_files_count': len([t for t in processing_times if t > 30]),  # Plus de 30 secondes
            'fast_files_count': len([t for t in processing_times if t < 5])    # Moins de 5 secondes
        }

    def generate_recommendations(self, results, detailed_log):
        """Génère des recommandations basées sur les résultats"""
        try:
            recommendations = []

            # Analyser le taux de succès global
            total = sum(results.values())
            if total > 0:
                success_rate = results['success'] / total

                if success_rate < 0.5:
                    recommendations.append({
                        'type': 'critical',
                        'message': f"Taux de succès très faible ({success_rate:.1%}). Vérifiez la connexion et les correspondances de fichiers.",
                        'action': 'review_file_matching'
                    })
                elif success_rate < 0.7:
                    recommendations.append({
                        'type': 'warning',
                        'message': f"Taux de succès modéré ({success_rate:.1%}). Considérez améliorer les stratégies de correspondance.",
                        'action': 'optimize_matching'
                    })

                # Analyser les fichiers non trouvés
                not_found_rate = results.get('not_found', 0) / total
                if not_found_rate > 0.3:
                    recommendations.append({
                        'type': 'warning',
                        'message': f"{not_found_rate:.1%} des fichiers non trouvés. Vérifiez les noms de fichiers et la navigation.",
                        'action': 'check_file_names'
                    })

                # Analyser les erreurs
                error_rate = results.get('errors', 0) / total
                if error_rate > 0.2:
                    recommendations.append({
                        'type': 'error',
                        'message': f"Taux d'erreur élevé ({error_rate:.1%}). Vérifiez la stabilité de la connexion réseau.",
                        'action': 'check_network'
                    })

            # Analyser les stratégies de correspondance
            matching_strategies = {}
            slow_files = []

            for entry in detailed_log:
                if 'matching_strategy' in entry and entry['matching_strategy']:
                    strategy = entry['matching_strategy']
                    matching_strategies[strategy] = matching_strategies.get(strategy, 0) + 1

                if entry.get('processing_time', 0) > 30:
                    slow_files.append(entry['litho_code'])

            # Recommandations basées sur les stratégies
            if 'similarity_matching' in matching_strategies:
                if matching_strategies['similarity_matching'] > len(detailed_log) * 0.5:
                    recommendations.append({
                        'type': 'optimization',
                        'message': "Usage élevé de correspondance par similarité. Considérez standardiser les noms de fichiers.",
                        'action': 'standardize_file_names'
                    })

            if 'exact_name' in matching_strategies:
                exact_rate = matching_strategies['exact_name'] / len(detailed_log)
                if exact_rate > 0.8:
                    recommendations.append({
                        'type': 'success',
                        'message': f"Excellent taux de correspondance exacte ({exact_rate:.1%}). Noms de fichiers bien standardisés.",
                        'action': 'maintain_standards'
                    })

            # Recommandations sur les performances
            if slow_files:
                recommendations.append({
                    'type': 'performance',
                    'message': f"{len(slow_files)} fichiers traités lentement (>30s): {', '.join(slow_files[:5])}{'...' if len(slow_files) > 5 else ''}",
                    'action': 'investigate_slow_files'
                })

            return recommendations

        except Exception as e:
            self.logger.debug(f"Erreur génération recommandations: {e}")
            return []

    def save_report_to_file(self, detailed_report):
        """Sauvegarde le rapport dans un fichier JSON"""
        try:
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

            # Créer aussi un rapport résumé en texte
            self.save_summary_report(detailed_report, reports_dir, timestamp)

        except Exception as e:
            self.logger.error(f"Erreur sauvegarde rapport: {e}")

    def save_summary_report(self, detailed_report, reports_dir, timestamp):
        """Sauvegarde un rapport résumé en format texte"""
        try:
            filename = f"basecamp_summary_{timestamp}.txt"
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RAPPORT DE TRAITEMENT BASECAMP\n")
                f.write("=" * 80 + "\n\n")

                # Résumé de session
                session_info = detailed_report.get('session_info', {})
                f.write(f"Début: {session_info.get('start_time', 'N/A')}\n")
                f.write(f"Fin: {session_info.get('end_time', 'N/A')}\n")
                f.write(f"Durée: {session_info.get('duration', 0):.1f} secondes\n\n")

                # Résultats
                summary = detailed_report.get('summary', {})
                f.write("RÉSULTATS:\n")
                f.write(f"  Succès: {summary.get('success', 0)}\n")
                f.write(f"  Erreurs: {summary.get('errors', 0)}\n")
                f.write(f"  Ignorés: {summary.get('skipped', 0)}\n")
                f.write(f"  Non trouvés: {summary.get('not_found', 0)}\n")
                f.write(f"  Taux de succès: {session_info.get('success_rate', 0):.1f}%\n\n")

                # Statistiques
                stats = detailed_report.get('statistics', {})
                if stats:
                    f.write("STATISTIQUES:\n")
                    f.write(f"  Temps moyen: {stats.get('avg_processing_time', 0):.1f}s\n")
                    f.write(f"  Fichiers trouvés: {stats.get('files_found_ratio', 0):.1%}\n")
                    f.write(f"  Commentaires ajoutés: {stats.get('comments_success_ratio', 0):.1%}\n\n")

                # Recommandations
                recommendations = detailed_report.get('recommendations', [])
                if recommendations:
                    f.write("RECOMMANDATIONS:\n")
                    for i, rec in enumerate(recommendations, 1):
                        f.write(f"  {i}. [{rec.get('type', 'info').upper()}] {rec.get('message', '')}\n")

            self.logger.info(f"📝 Rapport résumé sauvegardé: {filepath}")

        except Exception as e:
            self.logger.error(f"Erreur sauvegarde rapport résumé: {e}")

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

    def generate_html_report(self, detailed_report):
        """Génère un rapport HTML pour visualisation"""
        try:
            # Template HTML basique
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rapport BaseCamp</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
                    .summary { display: flex; gap: 20px; margin: 20px 0; }
                    .metric { background-color: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; }
                    .success { color: #4CAF50; }
                    .error { color: #f44336; }
                    .warning { color: #FF9800; }
                    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Rapport de Traitement BaseCamp</h1>
                    <p>Généré le: {timestamp}</p>
                </div>

                <div class="summary">
                    <div class="metric">
                        <h3>Succès</h3>
                        <p class="success">{success}</p>
                    </div>
                    <div class="metric">
                        <h3>Erreurs</h3>
                        <p class="error">{errors}</p>
                    </div>
                    <div class="metric">
                        <h3>Taux de Succès</h3>
                        <p>{success_rate:.1f}%</p>
                    </div>
                </div>

                <h2>Recommandations</h2>
                <ul>
                {recommendations_html}
                </ul>
            </body>
            </html>
            """

            # Préparer les données
            summary = detailed_report.get('summary', {})
            session_info = detailed_report.get('session_info', {})
            recommendations = detailed_report.get('recommendations', [])

            recommendations_html = ""
            for rec in recommendations:
                rec_type = rec.get('type', 'info')
                message = rec.get('message', '')
                recommendations_html += f'<li class="{rec_type}">{message}</li>\n'

            # Remplir le template
            html_content = html_template.format(
                timestamp=detailed_report.get('timestamp', ''),
                success=summary.get('success', 0),
                errors=summary.get('errors', 0),
                success_rate=session_info.get('success_rate', 0),
                recommendations_html=recommendations_html
            )

            return html_content

        except Exception as e:
            self.logger.error(f"Erreur génération rapport HTML: {e}")
            return None