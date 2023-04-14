import os.path
import unittest

import paramiko

from src.server.commands.path_functions import go_back_one_dir
from src.server.ssh.ssh_commands import delete_folder_ssh, create_folder_ssh, does_path_exists_ssh, send_file_ssh, \
    delete_file_ssh


class TestSSHFunctions(unittest.TestCase):
    CAN_NOT_DELETE_FOLDER: str = "Can not delete folder"
    CAN_NOT_DELETE_FILE: str = "Can not delete file"
    CAN_NOT_CREATE_FOLDER: str = "Can not create folder"
    CAN_NOT_CREATE_FILE: str = "Can not create file"

    def setUp(self):
        self.host = "192.168.7.226"
        self.port = 22
        self.username = "Administrateur"
        self.password = ""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, self.port, self.username, self.password)

    def tearDown(self):
        self.ssh.close()

    def test_folders_exists(self):
        result = does_path_exists_ssh(self.ssh, "C:\\Users\\Administrateur\\Desktop")
        self.assertTrue(result)
        result = does_path_exists_ssh(self.ssh, "C:\\users\\")
        self.assertTrue(result)

        result = does_path_exists_ssh(self.ssh, "C:\\users\\k")
        self.assertFalse(result)
        result = does_path_exists_ssh(self.ssh, "C:\\users\\administrateur\\dk")
        self.assertFalse(result)
        result = does_path_exists_ssh(self.ssh, "C:::\\Users\\Administrateur\\Desktop")
        self.assertFalse(result)

    def test_create_delete_folder_ssh(self):
        folder_path = "C:\\Users\\Administrateur\\Desktop\\test"
        result = does_path_exists_ssh(self.ssh, folder_path)
        if result:
            result = delete_folder_ssh(self.ssh, folder_path)
            if not result:
                self.fail(self.CAN_NOT_DELETE_FOLDER)

        result = create_folder_ssh(self.ssh, folder_path)
        self.assertTrue(result)
        result = delete_folder_ssh(self.ssh, folder_path)
        self.assertTrue(result)

    def test_create_folder_ssh_failure(self):
        folder_path = "C:\\Users\\Administrateur\\Desktop\\test\\test"
        result = does_path_exists_ssh(self.ssh, folder_path)
        if result:
            result = delete_folder_ssh(self.ssh, folder_path)
            if not result:
                self.fail(self.CAN_NOT_DELETE_FOLDER)

        result = create_folder_ssh(self.ssh, folder_path)
        self.assertTrue(result)
        result = create_folder_ssh(self.ssh, folder_path)
        self.assertFalse(result)

        result = delete_folder_ssh(self.ssh, folder_path)
        if not result:
            self.fail(self.CAN_NOT_DELETE_FOLDER)

        folder_path = go_back_one_dir(folder_path)
        result = delete_folder_ssh(self.ssh, folder_path)
        if not result:
            self.fail(self.CAN_NOT_DELETE_FOLDER)

    def test_send_file_ssh(self):
        file_path = "new_file_test.py"
        with open(file_path, "w") as file:
            file.write("print('Hello world')")

        remote_path = "C:\\Users\\Administrateur\\Desktop\\test\\test"
        result = does_path_exists_ssh(self.ssh, remote_path)
        if not result:
            result = create_folder_ssh(self.ssh, remote_path)
            if not result:
                self.fail(self.CAN_NOT_CREATE_FOLDER)

        result = send_file_ssh(self.ssh, file_path, remote_path)

        self.assertTrue(result)

        result = delete_file_ssh(self.ssh, os.path.join(remote_path, file_path))
        if not result:
            self.fail(self.CAN_NOT_DELETE_FILE)

        result = delete_folder_ssh(self.ssh, remote_path)
        if not result:
            self.fail(self.CAN_NOT_DELETE_FOLDER)

        os.remove(file_path)
