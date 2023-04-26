import json

from src.server.commands.find_all_pc import generate_ip_range, scan_network
from src.server.commands.path_functions import find_file, change_directory_to_root_folder
from src.server.data.computer import Computer
from src.server.data.local_network_data import Data
from threading import Lock


class ComputerDatabase:
    """
    This class is used to store all the computers in the database.
    It loads the computers from the computers_database.json file.
    It contains a list of Computer objects, and methods to add, remove and find computers.
    """
    json_computers_database_filename: str = "computers_database.json"

    computer_database_lock = Lock()

    def __init__(self) -> None:
        """
        Creates a new ComputerDatabase object. This object is used to store all the computers in the database.
        It loads the computers from the computers_database.json file.
        """
        self.data = Data()
        self.__computers: list[Computer] = []
        self.computers_json: dict = {}

        # TODO: Do thread lock here to maybe fix bug that erases all computers in database
        #  ChatGPT has the explanation, look for it

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

        self.save_computer_data()

    def refresh_ip_address(self, host: str, new_host: dict) -> None:
        if host in self.computers_json:
            self.computers_json[host]["ip"] = new_host[host]["ip"]

    @classmethod
    def save_computer_data(cls, hosts=None) -> None:
        """
        Save the computers data in the computers_database.json file.
        Creates a backup of the file before saving, just in case.
        :return: Nothing.
        """
        # Read the current data from the file
        if hosts is not None:
            # Save the new data to the file
            change_directory_to_root_folder()
            with open(cls.json_computers_database_filename, "w") as f:
                json.dump(hosts, f, indent=4)
                return

        with ComputerDatabase.computer_database_lock:
            try:
                with open(find_file(cls.json_computers_database_filename), 'r') as file:
                    current_data = json.load(file)
            except FileNotFoundError:
                raise FileNotFoundError("Cannot find the file 'computers_database.json'. It should have been created "
                                        "at the setup phase. Please check the setup process, and restart the program."
                                        "You can try deleting the file 'computers_database.json' (make a backup first)"
                                        ". The program will create a new one."
                                        "You can try copy paste the old information into the new file.")

            # Save the current data as a backup
            with open("computers_database_backup.json", 'w') as backup_file:
                json.dump(current_data, backup_file, indent=4)

            # Save the new data to the file
            with open(find_file(cls.json_computers_database_filename), "w") as f:
                json.dump(current_data, f, indent=4)

    @classmethod
    def load_computer_data(cls) -> "ComputerDatabase":
        computer_database = ComputerDatabase()
        computers_data_json_file = find_file(cls.json_computers_database_filename)
        if computers_data_json_file is None:
            raise FileNotFoundError("Cannot find the file 'computers_database.json'. It should have been created at the"
                                    "setup phase. Please check the setup process, and restart the program.")

        with open(find_file("computers_database.json"), "r") as file:
            computer_database.computers_json = json.loads(file.read())

        # Add all the computers to the database, using the Computer class.
        for computer_hostname in computer_database.computers_json:
            new_computer_dict = computer_database.computers_json[computer_hostname]
            new_computer = Computer(new_computer_dict, computer_hostname)
            computer_database.add_computer(new_computer)

        return computer_database

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
