import json
import socket

from src.server.commands.path_functions import find_file, change_directory_to_root_folder
from src.server.config import Infos
from src.server.data.computer import Computer
from src.server.data.local_network_data import Data
from threading import Lock

from src.server.environnement.server_logs import log_error
from src.server.ssh.ssh_keygen import gen_keys_and_save_them
from src.server.warn_admin.mails import load_email_infos


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
        Infos.email_send = load_email_infos()

    def add_computer(self, computer: Computer) -> None:
        self.__computers.append(computer)

    def add_new_computer(self, dict_computer: dict) -> bool:
        """
        Add a new computer to the database and the self.computers_json property.
        :param dict_computer: The computer to add in dictionary form.
        :return: None
        """
        if dict_computer["hostname"] in self.computers_json:
            return False
        self.computers_json[dict_computer["hostname"]] = dict_computer
        new_computer: Computer = Computer(dict_computer)
        gen_keys_and_save_them(new_computer)
        self.add_computer(new_computer)
        return True

    def remove_computer(self, hostname: str) -> bool:
        for computer in self.__computers:
            if computer.hostname == hostname:
                computer.remove_keys()
                self.__computers.remove(computer)
                self.computers_json.pop(hostname)
                return True
        return False

    def find_computer(self, hostname: str) -> Computer:
        for computer in self.__computers:
            if computer.hostname == hostname:
                return computer

    def get_computers(self) -> list[Computer]:
        return self.__computers

    def get_computer(self, index: int) -> Computer:
        return self.__computers[index]

    def refresh_ip_addresses(self) -> None:
        """
        Refresh the local ip adresses of all the computers in the database.
        :return: None
        """
        at_least_one_online: bool = False
        for computer in self.__computers:
            try:
                computer.ipv4 = socket.gethostbyname(computer.hostname)
                at_least_one_online = True
            except socket.gaierror:
                log_error(f"Cannot find the ip address of the computer {computer.hostname}. It might be offline.")
                continue

        if at_least_one_online:
            self.save_computer_data()
        else:
            raise ConnectionError("Cannot find any computer on the local network. Please check your connection.")

    def refresh_ip_address(self, host: str, new_host: dict) -> None:
        if host in self.computers_json:
            self.computers_json[host]["ip"] = new_host[host]["ip"]

    def save_computer_data(self, hosts=None) -> None:
        """
        Save the computers data in the computers_database.json file.
        Creates a backup of the file before saving, just in case.
        :return: Nothing.
        """

        # Read the current data from the file
        if hosts is not None:
            # Save the new data to the file
            change_directory_to_root_folder()
            with open(self.json_computers_database_filename, "w") as f:
                json.dump(hosts, f, indent=4)
                return

        with ComputerDatabase.computer_database_lock:
            try:
                with open(find_file(self.json_computers_database_filename), 'r') as file:
                    current_data = json.load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find the file {self.json_computers_database_filename}. "
                                        f"It should have been created " "at the setup phase. Please check the setup "
                                        "process, and restart the program.You can try deleting the file "
                                        f"'{self.json_computers_database_filename}' (make a backup first). "
                                        f"The program will create a " "new one.You can try copy paste the old "
                                        "information into the new file.")

            # Save the current data as a backup
            with open("computers_database_backup.json", 'w') as backup_file:
                json.dump(current_data, backup_file, indent=4)

            # Save the new data to the file
            with open(find_file(self.json_computers_database_filename), "w") as f:
                json.dump(self.computers_json, f, indent=4)

    @classmethod
    def load_computer_data(cls) -> "ComputerDatabase":
        computer_database = ComputerDatabase()
        computers_data_json_file = find_file(cls.json_computers_database_filename)
        if computers_data_json_file is None:
            raise FileNotFoundError(f"Cannot find the file '{cls.json_computers_database_filename}'. "
                                    f"It should have been created at the" "setup phase. Please check the setup process,"
                                    " and restart the program.")

        cls.__load_computers_from_json(computer_database, computers_data_json_file)

        return computer_database

    @classmethod
    def load_computer_data_if_exists(cls):
        computer_database = ComputerDatabase()
        computers_data_json_file = find_file(cls.json_computers_database_filename)
        if computers_data_json_file is None:
            return computer_database

        cls.__load_computers_from_json(computer_database, computers_data_json_file)

        return computer_database

    @classmethod
    def __load_computers_from_json(cls, computer_database: "ComputerDatabase", json_file_path: str) -> None:
        with open(json_file_path, "r") as file:
            computer_database.computers_json = json.loads(file.read())

        # Add all the computers to the database, using the Computer class.
        for computer_hostname in computer_database.computers_json:
            new_computer_dict = computer_database.computers_json[computer_hostname]
            new_computer = Computer(new_computer_dict)
            computer_database.add_computer(new_computer)

    def get_number_of_computers(self) -> int:
        return len(self.__computers)

    def get_successfully_number_of_updated_computers(self) -> int:
        res = 0
        for computer in self.__computers:
            if computer.updated_successfully:
                res += 1

        return res


    def get_not_updated_computers(self):
        res = []
        for computer in self.__computers:
            if not computer.updated_successfully:
                res.append(computer)

        return res

    def __str__(self) -> str:
        string_representation = "########## Computer Database ##########\n\n"
        for computer in self.__computers:
            string_representation += f"{computer.hostname}\n"
            string_representation += f"\tMAC  : \t{computer.mac_address}\n"
            string_representation += f"\tLOGS : \t{computer.logs_filename}\n"
            string_representation += f"\tIPv4 : \t{computer.ipv4}\n"
            string_representation += f"\tUSER : \t{computer.username}\n"
        return string_representation


if __name__ == '__main__':
    computers_test = ComputerDatabase()
    print()
    print(computers_test)
