import logging
from dataclasses import dataclass


@dataclass
class Computer:
    ipv4: str
    hostname: str
    mac_address: str
    username: str

    def log(self, message, level=logging.INFO):
        pass

    def log_error(self, message):
        self.log(message, logging.ERROR)

    def get_ipv4(self):
        return self.ipv4
