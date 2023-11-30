
class Computer:
    def __init__(self, ipv4: str, hostname: str, mac_address: str, username: str) -> None:
        self.ipv4: str = ipv4
        self.hostname = hostname
        self.mac_address = mac_address
        self.username = username
