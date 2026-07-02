# core/excel_processor.py
import pandas as pd
import logging
import os
from typing import List, Dict, Any, Optional
from .brand_configs.base_config import BaseBrandConfig
from .brand_configs.brand_registry import BrandRegistry

class ExcelProcessor:
    def __init__(self, brand_config: Optional[BaseBrandConfig] = None):
        """
        Initialise le processeur Excel avec une configuration de marque.

        Args:
            brand_config (Optional[BaseBrandConfig]): Configuration de la marque.
                                                      Si None, utilise MNY par défaut.
        """
        self.data: Optional[pd.DataFrame] = None
        self.logger = logging.getLogger(__name__)
        self._current_file_path: Optional[str] = None  # 🆕 Pour reload automatique

        # Configuration du logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.required_columns = brand_config.get_required_columns()
        self.optional_columns = brand_config.get_optional_columns()
        self.column_types = brand_config.get_column_types()

        self.logger.info(f"📊 ExcelProcessor initialized for: {self.brand_config.get_brand_display_name()}")

    def set_brand_config(self, brand_config: BaseBrandConfig):
        """
        Change la configuration de marque et recharge les données si un fichier était chargé.

        Args:
            brand_config (BaseBrandConfig): Nouvelle configuration de marque

        Note:
            Si un fichier Excel est actuellement chargé, il sera automatiquement
            rechargé avec les nouvelles règles de validation de la marque.
        """
        old_brand = self.brand_config.get_brand_display_name() if self.brand_config else "None"

        # Sauvegarder le chemin du fichier actuel si un fichier est chargé
        current_file = self._current_file_path

        # Changer la configuration
        self.brand_config = brand_config
        self.required_columns = brand_config.get_required_columns()
        self.optional_columns = brand_config.get_optional_columns()
        self.column_types = brand_config.get_column_types()

        new_brand = brand_config.get_brand_display_name()
        self.logger.info(f"🔄 Configuration changed from {old_brand} to {new_brand}")

        # 🆕 Recharger le fichier Excel avec la nouvelle configuration si un fichier était chargé
        if current_file and os.path.exists(current_file):
            self.logger.info(f"🔄 Reloading Excel file with {new_brand} configuration...")
            success = self.load_file(current_file)
            if success:
                self.logger.info(f"✅ File reloaded successfully for {new_brand}")
            else:
                self.logger.error(f"❌ Error reloading file for {new_brand}")
        elif self.data is not None:
            self.logger.warning(
                "⚠️  Excel data was loaded with a different brand configuration. "
                f"Please reload the Excel file to apply {new_brand} rules."
            )

    def validate_excel_format(self, file_path: str) -> Dict[str, Any]:
        """
        Valide le format du fichier Excel et retourne un rapport.
        - 'is_valid' dépend UNIQUEMENT des colonnes obligatoires.
        - Les colonnes optionnelles manquantes ne bloquent pas.
        """
        try:
            self.logger.info(f"Validation du fichier Excel: {file_path}")
            df = pd.read_excel(file_path)

            found_columns = list(df.columns)
            missing_required = [c for c in self.required_columns if c not in found_columns]
            missing_optional = [c for c in self.optional_columns if c not in found_columns]

            # Colonnes supplémentaires (tolérées)
            all_known = set(self.required_columns + self.optional_columns)
            extra_columns = [c for c in found_columns if c not in all_known]

            is_valid = len(missing_required) == 0

            if is_valid:
                self.logger.info(f"✅ Fichier Excel valide - {len(df)} lignes, {len(found_columns)} colonnes")
            else:
                self.logger.error(f"❌ Fichier Excel invalide - Colonnes obligatoires manquantes: {missing_required}")

            if extra_columns:
                self.logger.info(f"ℹ️  Colonnes supplémentaires détectées (acceptées): {extra_columns}")

            if missing_optional:
                self.logger.info(f"ℹ️  Colonnes optionnelles manquantes (non bloquant): {missing_optional}")

            return {
                'is_valid': is_valid,
                'found_columns': found_columns,
                'missing_columns': missing_required,          # pour compatibilité UI (→ obligatoires)
                'missing_optional_columns': missing_optional, # nouveau champ d'info
                'extra_columns': extra_columns,
                'total_rows': len(df),
                'error_message': None
            }

        except FileNotFoundError:
            error_msg = "Fichier Excel non trouvé"
            self.logger.error(f"❌ {error_msg}: {file_path}")
            return {
                'is_valid': False,
                'found_columns': [],
                'missing_columns': self.required_columns,
                'missing_optional_columns': self.optional_columns,
                'extra_columns': [],
                'total_rows': 0,
                'error_message': error_msg
            }
        except Exception as e:
            error_msg = f"Erreur de lecture du fichier Excel: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {
                'is_valid': False,
                'found_columns': [],
                'missing_columns': self.required_columns,
                'missing_optional_columns': self.optional_columns,
                'extra_columns': [],
                'total_rows': 0,
                'error_message': error_msg
            }

    def load_file(self, file_path: str) -> bool:
        """
        Charge le fichier Excel et effectue les validations nécessaires.
        Échoue uniquement si une colonne OBLIGATOIRE est manquante.
        """
        try:
            self.logger.info(f"🔄 Chargement du fichier Excel: {file_path}")

            # 🆕 Sauvegarder le chemin du fichier
            self._current_file_path = file_path

            self.data = pd.read_excel(file_path)

            missing_required = [c for c in self.required_columns if c not in self.data.columns]
            if missing_required:
                self.logger.error(f"❌ Colonnes obligatoires manquantes: {missing_required}")
                self.data = None
                return False

            conversion_success = self._convert_data_types()
            if not conversion_success:
                self.logger.warning("⚠️  Certaines conversions de types ont échoué, mais le fichier reste utilisable")

            self._validate_data_quality()

            self.logger.info(f"✅ Fichier Excel chargé avec succès: {len(self.data)} lignes, {len(self.data.columns)} colonnes")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erreur lors du chargement du fichier Excel: {str(e)}")
            self.data = None
            return False

    def _convert_data_types(self) -> bool:
        """Convertit les types pour les colonnes PRÉSENTES uniquement."""
        if self.data is None:
            return False

        conversion_errors = []
        self.logger.info("🔄 Conversion des types de données...")

        for column in self.data.columns:
            try:
                expected_type = self.column_types.get(column, str)
                if expected_type == 'numeric':
                    original_values = self.data[column].copy()
                    self.data[column] = pd.to_numeric(self.data[column], errors='coerce')
                    na_count = self.data[column].isna().sum() - original_values.isna().sum()
                    if na_count > 0:
                        self.logger.warning(f"⚠️  {na_count} valeurs non numériques dans '{column}' (converties en NaN)")
                elif expected_type == str:
                    self.data[column] = self.data[column].fillna('').astype(str).str.strip()

            except Exception as e:
                msg = f"Erreur lors de la conversion de '{column}': {str(e)}"
                conversion_errors.append(msg)
                self.logger.error(f"❌ {msg}")
                try:
                    self.data[column] = self.data[column].fillna('').astype(str)
                    self.logger.info(f"🔧 Colonne '{column}' convertie en string par sécurité")
                except:
                    self.logger.error(f"❌ Impossible de convertir '{column}' même en string")

        if conversion_errors:
            self.logger.warning(f"⚠️  {len(conversion_errors)} erreurs de conversion détectées")
            return False
        self.logger.info("✅ Conversions de types terminées")
        return True

    def _validate_data_quality(self):
        """Contrôles légers (protégés si colonnes absentes)."""
        if self.data is None:
            return

        self.logger.info("🔍 Validation de la qualité des données...")

        # 🆕 LITHO (obligatoire) - Validation selon la marque
        litho_issues = []
        for idx, litho in enumerate(self.data['LITHO']):
            litho_str = str(litho).strip()
            # Utiliser la validation de la brand config
            if not self.brand_config.is_valid_litho_code(litho_str):
                litho_issues.append(f"Ligne {idx + 2}: '{litho_str}'")
        if litho_issues:
            self.logger.warning(
                f"⚠️  {len(litho_issues)} codes LITHO avec format incorrect "
                f"(marque: {self.brand_config.get_brand_code()})"
            )
            for issue in litho_issues[:5]:
                self.logger.warning(f"  - {issue}")
            if len(litho_issues) > 5:
                self.logger.warning(f"  ... et {len(litho_issues) - 5} autres")

        # UPC (obligatoire)
        upc_issues = 0
        for upc in self.data['UPC']:
            upc_str = str(upc).strip()
            if len(upc_str) != 11 or not upc_str.isdigit():
                upc_issues += 1
        if upc_issues > 0:
            self.logger.warning(f"⚠️  {upc_issues} codes UPC au mauvais format")

        # Statistiques (toutes protégées)
        unique_lithos = self.data['LITHO'].nunique()
        unique_products = self.data['PRODUCT'].nunique() if 'PRODUCT' in self.data.columns else 0
        unique_tiers = self.data['TIER'].nunique() if 'TIER' in self.data.columns else 0

        self.logger.info("📊 Statistiques des données:")
        self.logger.info(f"  - Codes LITHO uniques: {unique_lithos}")
        if 'PRODUCT' in self.data.columns:
            self.logger.info(f"  - Produits uniques: {unique_products}")
        if 'TIER' in self.data.columns:
            self.logger.info(f"  - Tiers uniques: {unique_tiers}")

    def get_data_for_litho(self, litho_code: str) -> List[Dict[str, Any]]:
        """Récupère les lignes pour un code LITHO donné."""
        if self.data is None:
            self.logger.warning("⚠️  Aucune donnée Excel n'a été chargée")
            return []

        try:
            litho_code_str = str(litho_code).strip()
            self.data['LITHO'] = self.data['LITHO'].astype(str)
            filtered = self.data[self.data['LITHO'].str.strip() == litho_code_str]
            if filtered.empty:
                self.logger.warning(f"⚠️  Aucune donnée pour la litho: {litho_code_str}")
                return []

            self.logger.info(f"✅ {len(filtered)} enregistrements pour la litho: {litho_code_str}")
            records = []
            for idx, row in filtered.iterrows():
                record = {}
                for column in filtered.columns:
                    try:
                        value = row[column]
                        if pd.isna(value):
                            record[column] = ""
                        elif isinstance(value, (int, float)):
                            record[column] = int(value) if float(value).is_integer() else value
                        else:
                            record[column] = str(value).strip()
                    except Exception as e:
                        self.logger.warning(f"⚠️  Erreur col '{column}' ligne {idx}: {str(e)}")
                        record[column] = ""
                records.append(record)
            return records
        except Exception as e:
            self.logger.error(f"❌ Erreur get_data_for_litho({litho_code}): {str(e)}")
            return []

    def get_unique_values(self, column_name: str) -> List[str]:
        """Valeurs uniques d'une colonne si présente."""
        if self.data is None:
            self.logger.warning("⚠️  Aucune donnée Excel n'a été chargée")
            return []
        if column_name not in self.data.columns:
            self.logger.error(f"❌ Colonne '{column_name}' non trouvée")
            return []
        try:
            values = self.data[column_name].dropna().unique().tolist()
            self.logger.info(f"✅ {len(values)} valeurs uniques pour '{column_name}'")
            return [str(v) for v in values]
        except Exception as e:
            self.logger.error(f"❌ Erreur uniques '{column_name}': {str(e)}")
            return []

    def get_data_summary(self) -> Dict[str, Any]:
        """Résumé des données (robuste aux colonnes optionnelles manquantes)."""
        if self.data is None:
            return {'loaded': False, 'error': 'Aucune donnée chargée'}

        try:
            summary: Dict[str, Any] = {
                'loaded': True,
                'brand': self.brand_config.get_brand_display_name(),  # 🆕 Ajout marque
                'brand_code': self.brand_config.get_brand_code(),     # 🆕 Ajout code marque
                'total_rows': len(self.data),
                'total_columns': len(self.data.columns),
                'columns': list(self.data.columns),
                'unique_lithos': self.data['LITHO'].nunique(),
            }

            if 'PRODUCT' in self.data.columns:
                summary['unique_products'] = self.data['PRODUCT'].nunique()
            if 'TIER' in self.data.columns:
                summary['unique_tiers'] = self.data['TIER'].nunique()
            if 'STATUS' in self.data.columns:
                summary['status_distribution'] = self.data['STATUS'].value_counts().to_dict()
            if 'TIER' in self.data.columns:
                summary['tier_distribution'] = self.data['TIER'].value_counts().to_dict()
            if 'STRIP TYPE' in self.data.columns:
                summary['strip_type_distribution'] = self.data['STRIP TYPE'].value_counts().to_dict()

            self.logger.info("✅ Résumé des données généré")
            return summary

        except Exception as e:
            self.logger.error(f"❌ Erreur résumé: {str(e)}")
            return {'loaded': True, 'error': f'Erreur résumé: {str(e)}'}
