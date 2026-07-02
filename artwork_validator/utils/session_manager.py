# utils/session_manager.py
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

class SessionManager(QObject):
    # Signal émis quand la session est mise à jour
    session_updated = pyqtSignal()
    def __init__(self):
        super().__init__()  # Appeler le constructeur QObject
        self.current_session_file = None
        self.settings_file = "app_settings.json"  # Fichier pour les paramètres globaux
        self.current_sessions_folder = None  # Dossier actuel des sessions
        self.reset_session()
        self.load_app_settings()

    def reset_session(self):
        """Réinitialise la session avec des valeurs par défaut"""
        self.current_session = {
            'session_name': '',
            'pdf_folder': '',
            'excel_file': '',
            'last_litho_index': 0,
            'validations': {},
            'created_date': '',
            'last_updated': '',
            'session_type': '',  # WM, GEN, CUBBY, etc.
            'check_digits': False,
            'brand_code': 'MNY',  # 🆕 Code de marque par défaut
            'session_version': '1.0'
        }

    def load_app_settings(self):
        """Charge les paramètres de l'application"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.current_sessions_folder = settings.get('sessions_folder', os.getcwd())
                    return True
        except Exception as e:
            print(f"Erreur lors du chargement des paramètres: {e}")
        
        # Par défaut, utiliser le répertoire courant
        self.current_sessions_folder = os.getcwd()
        return False

    def save_app_settings(self):
        """Sauvegarde les paramètres de l'application"""
        try:
            settings = {
                'sessions_folder': self.current_sessions_folder,
                'last_session_file': self.current_session_file,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")
            return False

    def get_last_session_path(self) -> Optional[str]:
        """Récupère le chemin de la dernière session utilisée"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    last_session = settings.get('last_session_file')
                    if last_session and os.path.exists(last_session):
                        return last_session
        except Exception as e:
            print(f"Erreur lors de la lecture de la dernière session: {e}")
        return None

    def set_sessions_folder(self, folder_path: str) -> bool:
        """Définit le dossier de sessions"""
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            self.current_sessions_folder = folder_path
            self.save_app_settings()
            return True
        return False

    def load_last_session(self) -> bool:
        """Charge automatiquement la dernière session utilisée"""
        last_session_path = self.get_last_session_path()
        if last_session_path:
            return self.load_session_from_file(last_session_path)
        return False

    def get_available_sessions(self, folder_path: str = None) -> List[Dict[str, str]]:
        """Retourne la liste des sessions disponibles dans un dossier spécifique"""
        search_folder = folder_path or self.current_sessions_folder
        sessions = []
        
        try:
            if not os.path.exists(search_folder):
                return sessions
                
            for file in os.listdir(search_folder):
                if file.endswith('.json') and file != 'app_settings.json':
                    file_path = os.path.join(search_folder, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Vérifier si c'est bien un fichier de session
                            if 'session_name' in data and 'created_date' in data:
                                sessions.append({
                                    'file_path': os.path.abspath(file_path),
                                    'name': data.get('session_name', 'Sans nom'),
                                    'created': data.get('created_date', ''),
                                    'updated': data.get('last_updated', ''),
                                    'file_name': file,
                                    'validations_count': len(data.get('validations', {}))
                                })
                    except (json.JSONDecodeError, KeyError):
                        # Ignorer les fichiers JSON qui ne sont pas des sessions
                        continue
        except Exception as e:
            print(f"Erreur lors de la recherche des sessions dans {search_folder}: {e}")
        
        # Trier par date de modification (plus récent en premier)
        sessions.sort(key=lambda x: x['updated'], reverse=True)
        return sessions

    def save_session_as(self, folder_path: str, session_name: str) -> bool:
        """Sauvegarde la session dans un dossier spécifique avec un nom"""
        try:
            # Nettoyer le nom de session pour éviter les caractères invalides
            clean_name = "".join(c for c in session_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not clean_name:
                clean_name = "session_sans_nom"
            
            # Créer le nom de fichier
            filename = f"{clean_name}.json"
            full_path = os.path.join(folder_path, filename)
            
            # Mettre à jour les métadonnées
            self.current_session['session_name'] = session_name
            self.current_session['last_updated'] = datetime.now().isoformat()
            
            # Si c'est une nouvelle session, définir la date de création
            if not self.current_session.get('created_date'):
                self.current_session['created_date'] = datetime.now().isoformat()
            
            # Sauvegarder le fichier
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=4, ensure_ascii=False)
            
            self.current_session_file = full_path
            
            # Mettre à jour le dossier de sessions et sauvegarder les paramètres
            self.current_sessions_folder = folder_path
            self.save_app_settings()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la session: {e}")
            return False

    def save_session(self) -> bool:
        """Sauvegarde la session courante (si un fichier est déjà défini)"""
        if self.current_session_file:
            try:
                self.current_session['last_updated'] = datetime.now().isoformat()
                with open(self.current_session_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_session, f, indent=4, ensure_ascii=False)
                # Sauvegarder les paramètres pour mémoriser cette session
                self.save_app_settings()
                return True
            except Exception as e:
                print(f"Erreur lors de la sauvegarde automatique: {e}")
                return False
        return False

    def load_session_from_file(self, file_path: str) -> bool:
        """Charge une session depuis un fichier spécifique"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_session = json.load(f)
                
                # Validation et migration si nécessaire
                self.current_session = self._validate_and_migrate_session(loaded_session)
                self.current_session_file = file_path
                
                # Mettre à jour le dossier de sessions
                self.current_sessions_folder = os.path.dirname(file_path)
                self.save_app_settings()
                
                return True
        except Exception as e:
            print(f"Erreur lors du chargement de la session: {e}")
        return False

    def _validate_and_migrate_session(self, session_data: dict) -> dict:
        """Valide et migre les données de session si nécessaire"""
        # Créer une session par défaut
        validated_session = {
            'session_name': session_data.get('session_name', 'Session sans nom'),
            'pdf_folder': session_data.get('pdf_folder', ''),
            'excel_file': session_data.get('excel_file', ''),
            'last_litho_index': session_data.get('last_litho_index', 0),
            'validations': session_data.get('validations', {}),
            'created_date': session_data.get('created_date', datetime.now().isoformat()),
            'last_updated': session_data.get('last_updated', datetime.now().isoformat()),
            'session_type': session_data.get('session_type', ''),
            'check_digits': session_data.get('check_digits', False),
            'session_version': session_data.get('session_version', '1.0')
        }
        
        return validated_session

    def start_new_session(self, session_name: str = "Nouvelle Session"):
        """Démarre une nouvelle session"""
        self.reset_session()
        self.current_session['session_name'] = session_name
        self.current_session['created_date'] = datetime.now().isoformat()
        self.current_session['last_updated'] = datetime.now().isoformat()
        self.current_session_file = None

    def update_paths(self, pdf_folder: str = None, excel_file: str = None):
        """Met à jour les chemins des fichiers"""
        if pdf_folder:
            self.current_session['pdf_folder'] = pdf_folder
        if excel_file:
            self.current_session['excel_file'] = excel_file
        self.save_session()

    def update_litho_status(self, litho_code: str, status: str, comment: str = ""):
        """Met à jour le statut d'une litho"""
        self.current_session['validations'][litho_code] = {
            'status': status,
            'date': datetime.now().isoformat(),
            'comment': comment
        }
        self.save_session()
        # Émettre le signal de mise à jour
        self.session_updated.emit()

    def get_litho_status(self, litho_code: str) -> Optional[Dict]:
        """Récupère le statut d'une litho"""
        return self.current_session['validations'].get(litho_code)

    def get_rejected_lithos(self) -> List[str]:
        """Retourne la liste des lithos rejetées"""
        return [code for code, data in self.current_session['validations'].items() 
                if data['status'] == 'rejected']

    def get_approved_lithos(self) -> List[str]:
        """Retourne la liste des lithos approuvées"""
        return [code for code, data in self.current_session['validations'].items() 
                if data['status'] == 'approved']
    
    def get_all_lithos(self) -> List[str]:
        """Retourne la liste de toutes les lithos connues"""
        pdf_folder = self.current_session['pdf_folder']
        if pdf_folder and os.path.exists(pdf_folder):
            pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
            return [f.split('_')[0] for f in pdf_files]
        return []

    def get_session_info(self) -> Dict:
        """Retourne les informations de la session courante"""
        return {
            'name': self.current_session.get('session_name', 'Sans nom'),
            'created': self.current_session.get('created_date', ''),
            'updated': self.current_session.get('last_updated', ''),
            'pdf_folder': self.current_session.get('pdf_folder', ''),
            'excel_file': self.current_session.get('excel_file', ''),
            'validations_count': len(self.current_session.get('validations', {})),
            'file_path': self.current_session_file,
            'sessions_folder': self.current_sessions_folder
        }

    def get_sessions_folder(self) -> str:
        """Retourne le dossier actuel des sessions"""
        return self.current_sessions_folder or os.getcwd()

    def get_session_name(self) -> str:
        """Retourne le nom de la session actuelle"""
        return self.current_session.get('session_name', 'Session sans nom')