import getpass
import os
import shutil
import unittest
import uuid

from src.server.commands.install_client_files_and_dependencies import check_python_script_up_to_date
from src.server.commands.install_python_scripts import check_python_script_installed, install_python_script
from src.server.commands.path_functions import find_file
from src.server.config import Infos
from src.server.data.computer import Computer


def load_password_test():
    try:
        path = find_file("password_test.txt")
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print("Error, could not find the password_test.txt file in the tests_data folder.")
        print("Please, create a file called password_test.txt in the tests/tests_data folder.")
        raise FileNotFoundError


def get_mac_address():
    mac_address = uuid.UUID(int=uuid.getnode()).hex[-12:]
    formatted_mac_address = ":".join([mac_address[i:i + 2] for i in range(0, 12, 2)])
    return formatted_mac_address


class LoadLocalEnvironment:
    def __init__(self):
        # For this test to work, please create a file called password_test.txt in the tests/tests_data folder.
        # This file should contain the password of your computer.
        # Make sure you have openssh server installed.
        computer_info: dict = {
            "ip": "localhost",
            "mac": get_mac_address(),
            "username": getpass.getuser(),
            "password": load_password_test()
        }
        self.computer = Computer(computer_info, "test")
        self.project_path = self.computer.get_project_directory_on_client()


class TestClientEnvInstall(unittest.TestCase, LoadLocalEnvironment):
    def __init__(self):
        super().__init__()
        LoadLocalEnvironment.__init__(self)

    def setUp(self) -> None:
        # For this test to work, please create a file called password_test.txt in the tests/tests_data folder.
        # This file should contain the password of your computer. Make sure you have openssh server installed.
        self.computer.connect()
        self.computer.log_add_vertical_space()
        self.delete_test_folder()

    def delete_test_folder(self):
        folder_path = f"C:\\Users\\{self.computer.username}\\{Infos.PROJECT_NAME}"
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    def test_scripts_not_installed(self):
        self.assertFalse(check_python_script_installed(self.computer))

    def test_scripts_uploaded(self):
        installed: bool = check_python_script_installed(self.computer)
        self.assertFalse(installed)

        installed_python_scripts_success: bool = install_python_script(self.computer)
        self.assertTrue(installed_python_scripts_success)
        self.assertTrue(check_python_script_installed(self.computer))

        self.assertTrue(os.path.exists(self.project_path))

        files: list[str] = self.computer.get_list_client_files_to_send()

        for file in files:
            path_to_check: str = os.path.join(self.project_path, file)
            self.assertTrue(path_to_check)

    def test_scripts_up_to_date(self):
        # Upload scripts
        installed_python_scripts_success: bool = install_python_script(self.computer)
        self.assertTrue(installed_python_scripts_success)
        # Should be OK
        self.assertTrue(check_python_script_up_to_date(self.computer))

        # Get a list of files to send to a client, and change them so that they are not up-to-date
        files: list[str] = self.computer.get_list_client_files_to_send()
        files = list(map(lambda x: os.path.basename(x), files))

        # Upload scripts, but change them
        for file in files:
            with open(os.path.join(self.project_path, file), "w") as f:
                f.write("test")

        # Should not be OK, files not like the files in the server
        self.assertFalse(check_python_script_up_to_date(self.computer))

        # Upload scripts again
        install_python_script(self.computer)

        # Should be OK
        self.assertTrue(check_python_script_up_to_date(self.computer))

    def test_scripts_installed_overall(self):
        self.assertTrue(self.computer.install_prerequisites_client())
