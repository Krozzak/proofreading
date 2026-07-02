"""
Tests unitaires pour BaseCampFileMatcher
Exemple de tests pour le nouveau package modulaire
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from selenium.webdriver.common.by import By

# Import du module à tester
from litho_validator.core.basecamp import BaseCampFileMatcher


class TestBaseCampFileMatcher(unittest.TestCase):
    """Tests pour la classe BaseCampFileMatcher"""

    def setUp(self):
        """Configuration pour chaque test"""
        self.mock_driver = Mock()
        self.mock_logger = Mock()
        self.file_matcher = BaseCampFileMatcher(self.mock_driver, self.mock_logger)

    def test_init(self):
        """Test de l'initialisation"""
        self.assertEqual(self.file_matcher.driver, self.mock_driver)
        self.assertEqual(self.file_matcher.logger, self.mock_logger)

    def test_find_by_exact_name_success(self):
        """Test de recherche par nom exact - succès"""
        # Arrange
        mock_element = Mock()
        self.mock_driver.find_elements.return_value = [mock_element]

        # Act
        result = self.file_matcher._find_by_exact_name("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertEqual(result, mock_element)
        self.mock_driver.find_elements.assert_called_once()

    def test_find_by_exact_name_not_found(self):
        """Test de recherche par nom exact - non trouvé"""
        # Arrange
        self.mock_driver.find_elements.return_value = []

        # Act
        result = self.file_matcher._find_by_exact_name("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertIsNone(result)

    def test_find_by_yca_code_success(self):
        """Test de recherche par code YCA - succès"""
        # Arrange
        mock_element = Mock()
        self.mock_driver.find_elements.return_value = [mock_element]

        # Act
        result = self.file_matcher._find_by_yca_code("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertEqual(result, mock_element)

    def test_find_by_yca_code_invalid_format(self):
        """Test de recherche par code YCA - format invalide"""
        # Arrange
        self.mock_driver.find_elements.return_value = []

        # Act
        result = self.file_matcher._find_by_yca_code("test.pdf", "INVALID", "")

        # Assert
        self.assertIsNone(result)

    def test_count_visible_files(self):
        """Test du comptage des fichiers visibles"""
        # Arrange
        mock_elements = [Mock(), Mock(), Mock()]
        self.mock_driver.find_elements.return_value = mock_elements

        # Act
        result = self.file_matcher.count_visible_files()

        # Assert
        self.assertEqual(result, 3)

    def test_find_file_by_advanced_matching_exact_success(self):
        """Test de recherche avancée - succès avec stratégie exacte"""
        # Arrange
        mock_element = Mock()
        self.mock_driver.find_elements.return_value = [mock_element]

        # Act
        result = self.file_matcher.find_file_by_advanced_matching("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertEqual(result, mock_element)
        self.assertTrue(hasattr(result, '_matching_strategy'))
        self.assertEqual(result._matching_strategy, 'exact_name')

    @patch('difflib.SequenceMatcher')
    def test_find_by_similarity_success(self, mock_sequence_matcher):
        """Test de recherche par similarité - succès"""
        # Arrange
        mock_element = Mock()
        mock_element.get_attribute.return_value = "YCA12345.pdf"
        mock_element.text = "YCA12345.pdf"
        self.mock_driver.find_elements.return_value = [mock_element]

        # Mock SequenceMatcher pour retourner une similarité élevée
        mock_matcher_instance = Mock()
        mock_matcher_instance.ratio.return_value = 0.8
        mock_sequence_matcher.return_value = mock_matcher_instance

        # Act
        result = self.file_matcher._find_by_similarity("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertEqual(result, mock_element)

    def test_wait_for_page_load(self):
        """Test de l'attente de chargement de page"""
        # Arrange
        mock_wait = Mock()

        with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
            # Act
            self.file_matcher.wait_for_page_load(5)

            # Assert
            mock_wait.until.assert_called_once()


class TestBaseCampFileMatcherIntegration(unittest.TestCase):
    """Tests d'intégration pour BaseCampFileMatcher"""

    def setUp(self):
        """Configuration pour les tests d'intégration"""
        self.mock_driver = Mock()
        self.mock_logger = Mock()
        self.file_matcher = BaseCampFileMatcher(self.mock_driver, self.mock_logger)

    def test_full_matching_workflow(self):
        """Test du workflow complet de correspondance"""
        # Arrange
        mock_element = Mock()
        self.mock_driver.find_elements.side_effect = [
            [],  # Première stratégie échoue
            [mock_element],  # Deuxième stratégie réussit
        ]

        # Act
        result = self.file_matcher.find_file_by_advanced_matching("YCA12345.pdf", "YCA12345", "")

        # Assert
        self.assertEqual(result, mock_element)
        self.assertEqual(result._matching_strategy, 'yca_code')

    def test_no_match_found(self):
        """Test quand aucune stratégie ne trouve le fichier"""
        # Arrange
        self.mock_driver.find_elements.return_value = []

        # Act
        result = self.file_matcher.find_file_by_advanced_matching("NOTFOUND.pdf", "NOTFOUND", "")

        # Assert
        self.assertIsNone(result)


if __name__ == '__main__':
    # Configuration du logger pour les tests
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Exécution des tests
    unittest.main(verbosity=2)