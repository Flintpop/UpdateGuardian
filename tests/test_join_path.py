import unittest
from src.server.data.computer import Computer


class TestComputer(unittest.TestCase):
    """
    Check that the Computer can join a Windows path but in a linux environment.
    """
    def test_join_path(self):
        result = Computer.join_path('C:', 'Users', 'test_user', 'Desktop')
        self.assertEqual(result, 'C:\\Users\\test_user\\Desktop')

    def test_join_path_with_mixed_separators(self):
        result = Computer.join_path('C:/', 'Users', 'test_user', 'Desktop')
        self.assertEqual(result, 'C:\\Users\\test_user\\Desktop')

    def test_join_path_with_special_characters(self):
        result = Computer.join_path('C:', 'Users', 'test_user', 'Desk\\top')
        self.assertEqual(result, 'C:\\Users\\test_user\\Desk\\top')

    def test_join_path_with_spaces(self):
        result = Computer.join_path('C:', 'Users', 'test user', 'Desktop')
        self.assertEqual(result, 'C:\\Users\\test user\\Desktop')

    def test_join_path_with_empty_components(self):
        result = Computer.join_path('C:', '', 'Users', 'test_user', '', 'Desktop')
        self.assertEqual(result, 'C:\\Users\\test_user\\Desktop')


if __name__ == '__main__':
    unittest.main()
