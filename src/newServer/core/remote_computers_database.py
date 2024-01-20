import json
import os.path

from threading import Lock

from src.newServer.core.remote_computer_manager import RemoteComputerManager
from src.newServer.factory.remote_computer_manager_factory import RemoteComputerManagerFactory
from src.newServer.infrastructure.paths import ServerPath
from src.newServer.report.mails import load_email_infos
from src.newServer.ssh.ssh_keygen import gen_keys_and_save_them
from src.newServer.infrastructure.config import Infos


class RemoteComputerDatabase:
    """
    This class is used to store all the computers in the database.
    It loads the computers from the computers_database.json file.
    It contains a list of Computer objects and methods to add, remove, and find computers.
    """
    computer_database_lock = Lock()

    def __init__(self) -> None:
        """
        Creates a new ComputerDatabase object. This object is used to store all the computers in the database.
        It loads the computers from the computers_database.json file.
        """
        self.max_number_of_simultaneous_updates = 0
        self.computers: list[RemoteComputerManager] = []
        self.computers_json: dict = {}

    def add_computer(self, computer: RemoteComputerManager) -> None:
        self.computers.append(computer)

    def add_new_computer(self, dict_computer: dict, host_key) -> bool:
        """
        Add a new computer to the database and the self.computers_json property.
        :param dict_computer: The computer to add in dictionary form.
        :param host_key: The host key of the computer.
        :return: None
        """
        if dict_computer["hostname"] in self.computers_json:
            return False
        self.computers_json[dict_computer["hostname"]] = dict_computer
        new_computer: RemoteComputerManager = RemoteComputerManagerFactory.create_from_dictionary(dict_computer)
        gen_keys_and_save_them(new_computer, host_key)
        self.add_computer(new_computer)
        return True

    def remove_computer(self, hostname: str) -> bool:
        for computer in self.computers:
            if computer.get_hostname() == hostname:
                computer.remove_keys()
                self.computers.remove(computer)
                self.computers_json.pop(hostname)
                return True
        return False

    def find_computer(self, hostname: str) -> RemoteComputerManager:
        for computer in self.computers:
            if computer.get_hostname() == hostname:
                return computer

    def get_computers(self) -> list[RemoteComputerManager]:
        return self.computers

    def get_computer(self, index: int) -> RemoteComputerManager:
        return self.computers[index]

    def save_computer_data(self, hosts=None) -> None:
        """
        Save the computers data in the computers_database.json file.
        Creates a backup of the file before saving, just in case.
        :return: Nothing.
        """

        # Read the current data from the file
        json_database_path: str = ServerPath.get_database_path()

        if hosts is not None:
            # Save the new data to the file
            with open(json_database_path, "w") as f:
                json.dump(hosts, f, indent=4)
                return

        with RemoteComputerDatabase.computer_database_lock:
            try:
                with open(json_database_path, 'r') as file:
                    current_data = json.load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Cannot find the file {ServerPath.json_computers_database_filename}. "
                                        f"It should have been created " "at the setup phase. Please check the setup "
                                        "process, and restart the program.You can try deleting the file "
                                        f"'{ServerPath.json_computers_database_filename}' (make a backup first). "
                                        f"The program will create a " "new one.You can try copy paste the old "
                                        "information into the new file.")

            # Save the current data as a backup
            with open("computers_database_backup.json", 'w') as backup_file:
                json.dump(current_data, backup_file, indent=4)

            # Save the new data to the file
            with open(json_database_path, "w") as f:
                json.dump(self.computers_json, f, indent=4)

    @classmethod
    def load_computer_data(cls) -> "RemoteComputerDatabase":
        computer_database = RemoteComputerDatabase()
        computers_data_json_file = ServerPath.get_database_path()

        if not ServerPath.exists(computers_data_json_file):
            raise FileNotFoundError(f"Cannot find the file '{os.path.abspath(computers_data_json_file)}'. "
                                    f"It should have been created at the" "setup phase. Please check the setup process,"
                                    " and restart the program.")

        cls.__load_computers_from_json(computer_database, computers_data_json_file, init_logger=True)

        return computer_database

    @classmethod
    def load_computer_data_if_exists(cls, init_logger=False) -> "RemoteComputerDatabase":
        computer_database = RemoteComputerDatabase()
        computers_data_json_file = ServerPath.get_database_path()

        if not ServerPath.exists(computers_data_json_file):
            return computer_database

        cls.__load_computers_from_json(computer_database, computers_data_json_file, init_logger=init_logger)

        return computer_database

    @classmethod
    def __load_computers_from_json(cls, computer_database: "RemoteComputerDatabase", json_file_path: str,
                                   init_logger) -> None:
        with open(json_file_path, "r") as file:
            computer_database.computers_json = json.loads(file.read())

        # Add all the computers to the database, using the Computer class.
        for computer_hostname in computer_database.computers_json:
            new_computer_dict = computer_database.computers_json[computer_hostname]
            new_computer = RemoteComputerManagerFactory.create_from_dictionary(
                new_computer_dict,
                init_logger=init_logger
            )
            computer_database.add_computer(new_computer)

    def get_number_of_computers(self) -> int:
        return len(self.computers)


    def shutdown_all_computers(self):
        for computer in self.computers:
            if not computer.connect_if_awake():
                continue
            computer.shutdown()

    @staticmethod
    def load_email_infos():
        Infos.email_send = load_email_infos()

    def __str__(self) -> str:
        string_representation = "########## Computer Database ##########\n\n"
        for computer in self.computers:
            string_representation += f"{computer.get_hostname()}\n"
            string_representation += f"\tMAC  : \t{computer.get_mac_address()}\n"
            string_representation += f"\tLOGS : \t{computer.get_logs_filename()}\n"
            string_representation += f"\tIPv4 : \t{computer.get_ipv4()}\n"
            string_representation += f"\tUSER : \t{computer.get_username()}\n"
        return string_representation

    def get_max_number_of_simultaneous_updates(self):
        if self.max_number_of_simultaneous_updates == 0:
            config_filename: str = ServerPath.get_config_json_file()
            if config_filename is None:
                json.dump({"max_computers_per_iteration": 2}, open("config.json", "w"), indent=4)
                self.max_number_of_simultaneous_updates = 2

                return self.max_number_of_simultaneous_updates

            with open(config_filename, "r") as f:
                config_file = json.load(f)
                if "max_computers_per_iteration" not in config_file:
                    config_file["max_computers_per_iteration"] = 2
                    json.dump(config_file, open(config_filename, "w"), indent=4)
                    self.max_number_of_simultaneous_updates = 2

                    return self.max_number_of_simultaneous_updates

                self.max_number_of_simultaneous_updates = int(config_file["max_computers_per_iteration"])

        return self.max_number_of_simultaneous_updates


if __name__ == '__main__':
    computers_test = RemoteComputerDatabase()
    print()
    print(computers_test)
