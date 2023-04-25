import json

from src.server.commands.find_all_pc import generate_ip_range, scan_network
from src.server.commands.path_functions import find_file
from src.server.data.computer import Computer
from src.server.data.local_network_data import Data


class ComputerDatabase:
    """
    This class is used to store all the computers in the database.
    It loads the computers from the computers_database.json file.
    It contains a list of Computer objects, and methods to add, remove and find computers.
    """
    def __init__(self) -> None:
        """
        Creates a new ComputerDatabase object. This object is used to store all the computers in the database.
        It loads the computers from the computers_database.json file.
        """
        self.data = Data()
        self.__computers: list[Computer] = []

        with open(find_file("computers_database.json"), "r") as file:
            self.computers_json: dict = json.loads(file.read())

        # Add all the computers to the database, using the Computer class.
        for computer_hostname in self.computers_json:
            new_computer_dict = self.computers_json[computer_hostname]
            new_computer = Computer(new_computer_dict, computer_hostname)
            self.add_computer(new_computer)

    def add_computer(self, computer: Computer) -> None:
        self.__computers.append(computer)

    def remove_computer(self, hostname: str) -> bool:
        for computer in self.__computers:
            if computer.hostname == hostname:
                self.__computers.remove(computer)
                return True
        return False

    def find_computer(self, hostname: str) -> Computer:
        for computer in self.__computers:
            if computer.hostname == hostname:
                return computer

    def get_computers(self) -> list[Computer]:
        return self.__computers

    def get_computer(self, index: int) -> Computer:
        for computer in self.__computers:
            if computer.id == index:
                return computer

    def refresh_ip_addresses(self) -> None:
        """
        Refresh the local ip adresses of all the computers in the database.
        :return: None
        """
        ip_range: list[str, str] = self.data.get_ip_range()
        ip_range_test = generate_ip_range(ip_range[0], ip_range[1])

        hosts_refreshed = scan_network(ip_range_test)

        for host in hosts_refreshed.keys():
            self.refresh_ip_address(host, hosts_refreshed)

        self.data.save_computer_data()

    def refresh_ip_address(self, host: str, new_host: dict) -> None:
        if host in self.computers_json:
            self.computers_json[host]["ip"] = new_host[host]["ip"]

    def __str__(self) -> str:
        string_representation = "########## Computer Database ##########\n\n"
        for computer in self.__computers:
            string_representation += f"{computer.hostname}\n"
            string_representation += f"\tMAC  : \t{computer.mac_address}\n"
            string_representation += f"\tLOGS : \t{computer.logs_filename}\n"
            string_representation += f"\tIPv4 : \t{computer.ipv4}\n"
        return string_representation


if __name__ == '__main__':
    computers_test = ComputerDatabase()
    print()
    print(computers_test)
