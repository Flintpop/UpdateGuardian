import os.path
import platform
import unittest

from src.server.core.remote_computer_manager import RemoteComputerManager

from src.server.factory.remote_computer_manager_factory import RemoteComputerManagerFactory
from tests.new_tests.ssh.environment_setup import SSHConnexion


class TestCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.ssh_connexion = SSHConnexion()
        self.ssh_session = self.ssh_connexion.ssh_session
        self.remote_computer_manager: 'RemoteComputerManager' = \
            RemoteComputerManagerFactory.create_from_dictionary_and_ssh(
                self.ssh_connexion.get_computer_dict(), self.ssh_session
            )

    def test_create_folder(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test_folder"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test_folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test_folder"))

    def test_create_folder_already_exists(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test_folder"))
        self.assertTrue(self.remote_computer_manager.create_folder("test_folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test_folder"))

    def test_create_folder_whitespace(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test folder"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test folder"))

    def test_create_folder_wrong_name(self):
        self.assertFalse(self.remote_computer_manager.create_folder("test_folder/"))
        self.assertFalse(self.remote_computer_manager.create_folder("test_folder\0"))
        self.assertTrue(self.remote_computer_manager.create_folder(".test_folder."))
        self.assertTrue(self.remote_computer_manager.delete_folder(".test_folder."))

    def test_delete_folder(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test_folder"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test_folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test_folder"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test_folder"))

    def test_delete_folder_not_exists(self):
        self.assertFalse(self.remote_computer_manager.does_path_exists("test_folder"))
        self.assertFalse(self.remote_computer_manager.delete_folder("test_folder"))

    def test_delete_folder_whitespace(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test folder"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test folder"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test folder"))

    def test_delete_file(self):
        self.assertTrue(self.remote_computer_manager.create_file("test_file"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test_file"))
        self.assertTrue(self.remote_computer_manager.delete_file("test_file"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test_file"))

    def test_delete_file_not_exist(self):
        self.assertFalse(self.remote_computer_manager.does_path_exists("test_file"))
        self.assertFalse(self.remote_computer_manager.delete_file("test_file"))

    def test_delete_file_whitespace(self):
        self.assertTrue(self.remote_computer_manager.create_file("test file"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test file"))
        self.assertTrue(self.remote_computer_manager.delete_file("test file"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test file"))

    def test_upload_file(self):
        if platform.system() != "Windows":
            raise unittest.SkipTest("Test only available on Windows")

        file = "test_file.txt"
        home_path = os.environ.get('USERPROFILE')

        self.assertTrue(self.remote_computer_manager.create_file(file))
        file_path = os.path.join(home_path, 'test_file.txt')
        self.assertTrue(self.remote_computer_manager.upload_file(file_path, os.path.join(home_path, "Desktop")))
        file_path = os.path.join(home_path, 'Desktop', 'test_file.txt')
        self.assertTrue(self.remote_computer_manager.does_path_exists(file_path))
        self.assertTrue(self.remote_computer_manager.delete_file(file_path))
        self.assertFalse(self.remote_computer_manager.does_path_exists(file_path))
