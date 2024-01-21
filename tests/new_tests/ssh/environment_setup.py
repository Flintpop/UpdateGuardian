import json
import os
import unittest

import paramiko

from src.newServer.infrastructure.paths import ServerPath
from src.newServer.infrastructure.setup_manager import SetupManager


class SSHConnexion:
    def __init__(self) -> None:
        super().__init__()
        file_path = __file__
        file_path = os.path.abspath(os.path.join(file_path, "..", "credentials.json"))

        print(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError("credentials.json not found for path : " + file_path)
        with open(file_path, "r", encoding="utf-8") as file:
            credentials = json.load(file)
            if not credentials:
                raise ValueError("No credentials found in credentials.json")
            if not credentials["port"]:
                raise ValueError("No port found in credentials.json")
            if not credentials["hostname"]:
                raise ValueError("No hostname found in credentials.json")
            if not credentials["username"]:
                raise ValueError("No username found in credentials.json")
            if not credentials["password"]:
                raise ValueError("No password found in credentials.json")
            if not credentials["mac_address"]:
                raise ValueError("No mac_address found in credentials.json")

            self.mac_address = credentials["mac_address"]
            self.port = credentials["port"]
            self.hostname = credentials["hostname"]
            self.username = credentials["username"]
            self.password = credentials["password"]

            self.ssh_session = paramiko.SSHClient()
            self.ssh_session.set_missing_host_key_policy(paramiko.RejectPolicy())
            self.ssh_session.load_host_keys(ServerPath.join(ServerPath.get_home_path(), ".ssh", "known_hosts"))
            self.ssh_session.connect(hostname=self.hostname, username=self.username, password=self.password)

    def get_computer_dict(self):
        return {
            "hostname": self.hostname,
            "ipv4": SetupManager.get_local_ipv4_address(),
            "username": self.username,
            "password": self.password,
            "port": self.port,
            "mac_address": self.mac_address
        }


if __name__ == '__main__':
    SSHConnexion()
