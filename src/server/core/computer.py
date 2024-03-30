from dataclasses import dataclass


@dataclass
class Computer:
    ipv4: str
    hostname: str
    mac_address: str
    username: str
