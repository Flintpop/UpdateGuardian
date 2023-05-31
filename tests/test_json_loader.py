import json
import os
import unittest

from src.server.data.generate_json import generate_dict
from src.server.data.local_network_data import Data
from src.server.commands.path_functions import find_file

JSON_TEST_FILENAME = 'test.json'
with open(JSON_TEST_FILENAME, 'w') as file_created:
    file_created.write("{}")
JSON_FILE_PATH = find_file(JSON_TEST_FILENAME)


class TestLoadJson(unittest.TestCase):
    json_test_dict: dict = generate_dict(13)

    def test_load_json(self):
        json_test_dict: dict = {
            "remote_user": ["user1", "user2"],
            "remote_host": ["192.168.1.14", "192.168.1.3"],
            "remote_passwords": ["password154554", "password2"],
            "max_computers_per_iteration": 2,
            "subnet_mask": "1",
            "taken_ips": ["192.168.1.1"],
            "python_client_script_path": "C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python39\\python.exe"
        }

        with open(JSON_TEST_FILENAME, 'w') as file:
            json.dump(json_test_dict, file)

        data = Data(JSON_FILE_PATH)

        self.assertDictEqual(json_test_dict, data.get_data_json())

    def test_load_json_empty(self):
        json_test_dict: dict = {
            "remote_user": [],
            "remote_host": [],
            "remote_passwords": [],
            "max_computers_per_iteration": 0,
            "subnet_mask": "0",
            "taken_ips": []
        }

        with open(JSON_TEST_FILENAME, 'w') as file:
            json.dump(json_test_dict, file)

        with self.assertRaises(ValueError):
            Data(JSON_FILE_PATH)

    def test_json_ip_address_already_taken(self):
        self.json_test_dict.get('taken_ips').append(self.json_test_dict.get('remote_host')[0])

        with self.assertRaises(ValueError):
            Data(JSON_FILE_PATH, self.json_test_dict)

    def test_json_ip_address_not_in_subnet(self):
        current_subnet: str = self.json_test_dict.get('subnet_mask')
        self.json_test_dict.get('remote_host')[0] = f"192.168.{int(current_subnet) + 1}.49"

        with self.assertRaises(ValueError):
            Data(JSON_FILE_PATH, self.json_test_dict)

    def test_json_wrong_ip_address(self):
        self.json_test_dict.get('remote_host')[0] = "192.168.1.256"

        with self.assertRaises(ValueError):
            Data(JSON_FILE_PATH, self.json_test_dict)

    def test_load_json_error(self):
        with open(JSON_TEST_FILENAME, 'w') as file:
            file.write("This is not a json file")

        with self.assertRaises(json.JSONDecodeError):
            Data(JSON_FILE_PATH)


class TestCheminFichier(unittest.TestCase):
    json_test_dict: dict = generate_dict(13)
    data: Data = Data(JSON_FILE_PATH, json_test_dict)

    def setUp(self) -> None:
        if os.name == "nt":
            self.valid_path = "C:\\Users\\utilisateur\\Documents\\mon_fichier.py"
            self.invalid_path = "C:\\Users\\utilisateur\\Documents\\mon_fichier.txt"
            self.invalid_path2 = "C:Users/utilisateur/Documents/mon_fichier.py"
        else:
            self.valid_path = "/home/utilisateur/Documents/mon_fichier.py"
            self.invalid_path = "/home/utilisateur/Documents/mon_fichier.txt"
            self.invalid_path2 = "/home/utilisateur/Documents\\mon_fichier.py"

    def test_valid_path(self):
        is_path_valid = Data.is_path_valid

        self.assertTrue(is_path_valid(self.valid_path), "Path should be valid.")
        self.assertFalse(is_path_valid(self.invalid_path), "Path should not be valid.")
        self.assertFalse(is_path_valid(self.invalid_path2), "Path should not be valid.")

    def test_fichier_existe(self):
        does_file_exists = self.data.does_file_exists
        file_exists_name: str = "test_fichier_existant.py"
        file_not_exists_path: str = "tests/test_fichier_non_existant.py"

        with open(file_exists_name, 'w') as file:
            file.write("print('Hello World!')")

        file_exists_path = os.path.abspath(file_exists_name)

        self.assertTrue(does_file_exists(file_exists_path), "Le fichier devrait exister.")
        self.assertFalse(does_file_exists(file_not_exists_path), "Le fichier ne devrait pas exister.")

        os.remove(file_exists_name)
        
        
class TestIPMacAddress(unittest.TestCase):
    def test_is_valid_mac_address(self):
        self.assertTrue(Data.is_valid_mac_address("00:11:22:33:44:55"))
        self.assertTrue(Data.is_valid_mac_address("00-11-22-33-44-55"))
        self.assertFalse(Data.is_valid_mac_address("00:11:22:33:44:GG"))
        self.assertFalse(Data.is_valid_mac_address("00:11:22:33:44"))
        self.assertFalse(Data.is_valid_mac_address("00:11:22:33:44:55:66"))
        self.assertFalse(Data.is_valid_mac_address("0011.2233.4455"))
        self.assertFalse(Data.is_valid_mac_address("00:11:22-33:44:55"))
