import os
import unittest

from src.server.commands.path_functions import go_back_one_dir, go_back_n_dir, is_path_valid


class TestPathsUtils(unittest.TestCase):

    def setUp(self):
        if os.name == 'nt':
            self.path_correct = "C:\\Users\\Administrateur\\Desktop"
            self.path_correct_one_dir_back = "C:\\Users\\Administrateur"
            self.path_correct_two_dir_back = "C:\\Users"
            self.path_incorrect = "C:\\Users\\Administrateur/s\\"
        else:
            self.path_correct = "/home/administrateur/Desktop"
            self.path_correct_one_dir_back = "/home/administrateur"
            self.path_correct_two_dir_back = "/home"
            self.path_incorrect = "/home/administrateur/Desktop\\"

    def test_is_path_valid(self):
        self.assertTrue(is_path_valid(self.path_correct))
        self.assertFalse(is_path_valid(self.path_incorrect))

    def test_go_back_one_dir(self):
        self.assertEqual(go_back_one_dir(self.path_correct), self.path_correct_one_dir_back)
        self.assertNotEqual(go_back_one_dir(self.path_correct), self.path_correct)
        self.assertEqual(go_back_one_dir(go_back_one_dir(self.path_correct)), self.path_correct_two_dir_back)

    def test_go_n_dir_back(self):
        self.assertEqual(go_back_n_dir(self.path_correct, 2), self.path_correct_two_dir_back)
        self.assertEqual(go_back_n_dir(self.path_correct, 0), self.path_correct)
        self.assertEqual(go_back_n_dir(self.path_correct, 1), self.path_correct_one_dir_back)

        self.assertNotEqual(go_back_n_dir(self.path_correct, 2), self.path_correct)
