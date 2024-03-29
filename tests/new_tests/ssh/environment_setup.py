import json
import os

import paramiko

from src.newServer.infrastructure.paths import ServerPath
from src.newServer.infrastructure.setup_manager import SetupManager
from src.newServer.ssh.connect import SSHConnect


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

            self.port = credentials.get("port")
            if not self.port:
                raise ValueError("No port found in credentials.json")

            self.hostname = credentials.get("hostname")
            if not self.hostname:
                raise ValueError("No hostname found in credentials.json")

            self.username = credentials.get("username")
            if not self.username:
                raise ValueError("No username found in credentials.json")

            self.password = credentials.get("password")
            host_key = credentials.get("host_key")
            if not self.password and not host_key:
                raise ValueError("No password found, and no host key too in credentials.json")

            self.mac_address = credentials.get("mac_address")
            if not self.mac_address:
                raise ValueError("No mac_address found in credentials.json")

            if credentials["host_key"] and credentials["ipv4"]:
                print("Connecting with host key, to a remote computer")
                private_key = paramiko.Ed25519Key.from_private_key_file(
                    ServerPath.join(ServerPath.get_ssh_keys_folder(), f"private_key_{self.hostname}"))
                self.ssh_session = SSHConnect.private_key_connexion_no_computer(self.hostname, self.username,
                                                                                private_key)
                return

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
