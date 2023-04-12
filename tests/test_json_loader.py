import json
import unittest

from src.data.generate_json import generate_dict
from src.data.local_network_data import Data

JSON_TEST_FILENAME = 'test.json'
JSON_FILE_PATH = '../tests/' + JSON_TEST_FILENAME


class TestLoadJson(unittest.TestCase):
    json_test_dict: dict = generate_dict(13)

    def test_load_json(self):
        json_test_dict: dict = {
            "remote_user": ["user1", "user2"],
            "remote_host": ["192.168.1.14", "192.168.1.3"],
            "remote_password": ["password154554", "password2"],
            "max_computers_per_iteration": 2,
            "subnet_mask": "1",
            "taken_ips": ["192.168.1.1"]
        }

        with open(JSON_TEST_FILENAME, 'w') as file:
            json.dump(json_test_dict, file)

        data = Data(JSON_FILE_PATH)

        self.assertDictEqual(json_test_dict, data.get_data_json())

    def test_load_json_empty(self):
        json_test_dict: dict = {
            "remote_user": [],
            "remote_host": [],
            "remote_password": [],
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
