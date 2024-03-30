import unittest

import paramiko


class TestSSHFunctions(unittest.TestCase):
    CAN_NOT_DELETE_FOLDER: str = "Can not delete folder"
    CAN_NOT_DELETE_FILE: str = "Can not delete file"
    CAN_NOT_CREATE_FOLDER: str = "Can not create folder"
    CAN_NOT_CREATE_FILE: str = "Can not create file"

    def setUp(self):
        self.host = "192.168.7.229"
        self.port = 22
        self.username = "admin"
        self.password = ""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, self.port, self.username, self.password)

    def tearDown(self):
        self.ssh.close()

    def test_path_updated(self):
        pass
