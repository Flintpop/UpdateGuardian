import os
import unittest
from unittest.mock import patch, MagicMock


from src.server.infrastructure.paths import ServerPath


class TestYourClass(unittest.TestCase):

    @patch('os.path.abspath')
    @patch('os.path.dirname')
    def test_get_project_root_path_success(self, mock_dirname, mock_abspath):
        # Mock the __file__ and directory structure
        mock_abspath.return_value = '/path/to/your/project/subdir/file.py'
        mock_dirname.side_effect = [
            '/path/to/your/project/subdir',
            '/path/to/your/project',
            '/path/to/your',
            '/path/to'
        ]

        expected_path = '/path/to/your/project'
        with patch('src.server.infrastructure.config.Infos.PROJECT_NAME', 'project'):
            result = ServerPath.get_project_root()
            self.assertEqual(result, expected_path)

    @patch('os.path.abspath')
    def test_get_project_root_path_failure(self, mock_abspath):
        # Mock the __file__ and directory structure
        mock_abspath.return_value = '/path/to/wrong/dir/file.py'

        with patch('src.server.infrastructure.config.Infos.PROJECT_NAME', 'project'), \
                self.assertRaises(EnvironmentError) as context:
            ServerPath.get_project_root()

        self.assertIn("The project root path is not correct", str(context.exception))

    def test_get_project_root_path_current_state(self):
        # Obtenez le chemin attendu en utilisant la logique de votre fonction
        path = os.path.abspath(__file__)
        for _ in range(3):  # Assurez-vous que ce nombre correspond à votre méthode
            path = os.path.dirname(path)

        # Exécutez la méthode et comparez le résultat avec le chemin attendu
        result = ServerPath.get_project_root()
        self.assertEqual(result, path)


if __name__ == '__main__':
    unittest.main()
