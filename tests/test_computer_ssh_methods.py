import unittest

from src.server.data.computer_database import ComputerDatabase


class TestComputerSSHMethods(unittest.TestCase):
    def setUp(self) -> None:
        # For this test to work, please create a file called password_test.txt in the tests/tests_data folder.
        # This file should contain the password of your computer. Make sure you have openssh server installed.
        computer_database = ComputerDatabase.load_computer_data()
        self.computer = computer_database.get_computer(1)
        self.project_path = self.computer.get_project_directory_on_client()

        self.computer.connect()
        self.computer.log_add_vertical_space()

    def test_shutdown(self):
        self.computer.shutdown()
