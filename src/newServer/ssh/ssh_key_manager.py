import os

import paramiko

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.newServer.core.computer import Computer


class SSHKeyManager:
    def __init__(self, computer: 'Computer', log_error: callable, log: callable):
        self.__private_key: paramiko.PKey | None = None
        self.__public_key: str | None = None
        self.private_key_filepath: str = os.path.join("keys", f"private_key_{computer.hostname}")
        self.public_key_filepath: str = os.path.join("keys", f"public_key_{computer.hostname}.pub")
        self.log_error = log_error
        self.log = log

    def get_private_key(self) -> paramiko.PKey | None:
        """
        Get the private key of the computer.
        :return: The private key of the computer.
        """
        if self.private_key_filepath is None:
            self.log_error("Error, the private key filepath is not defined.")
            return None

        if self.__private_key is None:
            self.__private_key = paramiko.Ed25519Key.from_private_key_file(self.private_key_filepath)
        return self.__private_key

    def get_public_key(self):
        """
        Get the public key of the computer.
        :return: The public key of the computer.
        """
        if self.public_key_filepath is None:
            # self.log_error("Error, the public key filepath is not defined.")
            return None

        if self.__public_key is None:
            try:
                with open(self.public_key_filepath, "r") as file:
                    self.__public_key = file.read()
            except FileNotFoundError:
                self.log_error("Error, the public key file does not exist.\nIt should have been generated at the setup "
                               "phase.")
                return None
        return self.__public_key

    def remove_keys(self):
        """
        Remove the private and public keys of the computer.
        """
        try:
            os.remove(self.private_key_filepath)
            os.remove(self.public_key_filepath)
        except FileNotFoundError:
            self.log("Could not remove keys, they do not exist.")
