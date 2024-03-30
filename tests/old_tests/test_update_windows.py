import os
import tempfile
import unittest
from src.client.update_windows import file_exists


class TestJsonFileExists(unittest.TestCase):
    def test_file_exists(self):
        file_path = os.path.abspath(__file__)
        self.assertTrue(file_exists(file_path, False))

    def test_file_does_not_exist(self):
        file_path = "/path/to/nonexistent/file.json"
        self.assertFalse(file_exists(file_path, False))

    def test_file_path_is_directory(self):
        file_path = "/path/to/directory"
        self.assertFalse(file_exists(file_path, False))

    def test_file_path_is_empty(self):
        file_path = ""
        self.assertFalse(file_exists(file_path, False))

    def test_file_path_is_none(self):
        file_path = None
        self.assertFalse(file_exists(file_path, False))

    def test_file_path_is_temporary_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_file_path = temp.name
            self.assertTrue(file_exists(temp_file_path, False))
        os.remove(temp_file_path)


if __name__ == '__main__':
    unittest.main()
