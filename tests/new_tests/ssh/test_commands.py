import unittest

from src.newServer.core.remote_computer_manager import RemoteComputerManager

from src.newServer.factory.remote_computer_manager_factory import RemoteComputerManagerFactory
from src.newServer.infrastructure.paths import ServerPath
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

    def test_delete_folder(self):
        self.assertTrue(self.remote_computer_manager.create_folder("test_folder"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test_folder"))
        self.assertTrue(self.remote_computer_manager.delete_folder("test_folder"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test_folder"))

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

    def test_delete_file_whitespace(self):
        self.assertTrue(self.remote_computer_manager.create_file("test file"))
        self.assertTrue(self.remote_computer_manager.does_path_exists("test file"))
        self.assertTrue(self.remote_computer_manager.delete_file("test file"))
        self.assertFalse(self.remote_computer_manager.does_path_exists("test file"))

    def test_upload_file(self):
        file = "test.txt"
        home_path = ServerPath.get_home_path()
        self.assertTrue(self.remote_computer_manager.create_file(file))
        self.assertTrue(self.remote_computer_manager.upload_file(ServerPath.join(home_path, file)
                                                                 , ServerPath.join(home_path, "Desktop")))
        file = "Desktop\\" + file
        self.assertTrue(self.remote_computer_manager.does_path_exists(file))
        self.assertTrue(self.remote_computer_manager.delete_file(file))
        self.assertFalse(self.remote_computer_manager.does_path_exists(file))

    def test_download_file(self):
        file = "test.txt"
        home_path = ServerPath.get_home_path()
        self.assertTrue(self.remote_computer_manager.create_file(file))
        self.assertTrue(self.remote_computer_manager.download_file(ServerPath.join(home_path, "Desktop", file),
                                                                   ServerPath.join(home_path, file)))
        file = "Desktop\\" + file
        self.assertTrue(self.remote_computer_manager.does_path_exists(file))
        self.assertTrue(self.remote_computer_manager.delete_file(file))
        self.assertFalse(self.remote_computer_manager.does_path_exists(file))
