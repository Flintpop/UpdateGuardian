import ipaddress
import os
import re
import json
import socket

from src.server.commands.find_all_pc import generate_ip_range
from src.server.commands.path_functions import find_file
from src.server.config import Infos


def get_local_ipv4() -> str:
    """
    Get the IP address of the server computer.
    :return: The IP address of the server computer.
    """
    hostname = socket.gethostname()
    local_ipv4 = socket.gethostbyname(hostname)
    return local_ipv4


class Data:
    """
    Class that loads the data from the JSON file.
    Getters are used to access the data.
    Checks are made to ensure the integrity of the JSON file.
    """
    python_version = "3.11"
    python_folder_name = f"Python{python_version.replace('.', '')}"
    python_precise_version = "3.11.3"
    server_ip_address: str = get_local_ipv4()
    data_json: dict = {}
    computers_data: dict = {}
    ipaddresses: dict = {}
    json_computers_database_filename: str = "computers_database.json"

    def __init__(self, filename: str = find_file("computers_informations.json"), json_data: dict = None):
        if json_data is None:
            self.__load_data(filename)
        else:
            self.data_json = json_data

        data_check: bool = self.__check_json_integrity()
        if not data_check:
            raise ValueError("Le fichier JSON est invalide.")

    def __load_data(self, filename: str = find_file("computers_informations.json")):
        # Ouvrir le fichier JSON en mode lecture
        with open(filename, 'r', encoding='utf-8') as fichier:
            # Charger le contenu du fichier JSON dans une variable
            self.data_json: dict = json.load(fichier)

        if not self.data_json.get("remote_passwords"):
            self.__load_passwords()

    def __load_passwords(self):
        with open(find_file("passwords.txt"), 'r', encoding='utf-8') as fichier:
            passwords = fichier.readlines()

            # Enlever les sauts de ligne et ignorer les lignes vides
        cleaned_passwords = [pwd.strip() for pwd in passwords if pwd.strip()]

        self.data_json['remote_passwords'] = cleaned_passwords

    def get_data_json(self) -> dict:
        return self.data_json

    @staticmethod
    def __is_valid_ipv4_address(address):
        try:
            ipaddress.IPv4Address(address)
            return True
        except ipaddress.AddressValueError:
            return False

    def load_computer_data(self):
        computers_data_json_file = find_file(self.json_computers_database_filename)
        if computers_data_json_file is None:
            raise FileNotFoundError("Cannot find the file 'computers_database.json'. It should have been created at the"
                                    "setup phase. Please check the setup process, and restart the program.")

        with open(computers_data_json_file, 'r', encoding='utf-8') as fichier:
            self.computers_data: dict = json.load(fichier)

    def __check_json_integrity(self) -> bool:
        if not self.check_fields_required():
            return False

        if not self.check_fields_length():
            return False

        # Vérifier l'intégrité des adresses IP
        subnet_mask = self.data_json["subnet_mask"]
        taken_ips = self.data_json["taken_ips"]

        for host in self.data_json["remote_host"]:
            if not self.__is_valid_ipv4_address(host):
                print(f"L'adresse IP {host} n'est pas valide.")
                return False

            # Vérifier si l'adresse IP est dans la plage autorisée
            ip_parts = host.split(".")
            if not (ip_parts[0] == "192" and ip_parts[1] == "168" and ip_parts[2] == subnet_mask and 1 <= int(
                    ip_parts[3]) <= 255):
                print(f"L'adresse IP {host} n'est pas dans la plage autorisée.")
                return False

            # Vérifier si l'adresse IP n'est pas déjà prise
            if host in taken_ips:
                print(f"L'adresse IP {host} est déjà prise.")
                return False

        ip_pool: list[str] = self.data_json["ip_pool_range"]
        cond: bool = len(ip_pool) == 2
        cond = cond and self.__is_valid_ipv4_address(ip_pool[0])
        cond = cond and self.__is_valid_ipv4_address(ip_pool[1])
        cond = cond and int(ip_pool[0].split(".")[3]) < int(ip_pool[1].split(".")[3])

        if not cond:
            print("Please, enter a valid IP range. 2 IPv4 values are required in the 192.168 format.")
            print("The first ip must be lower than the third.")
            return False
        return True

    def check_fields_required(self):
        # Vérifier la présence des champs requis
        required_fields = ["remote_user", "remote_host", "remote_passwords", "max_computers_per_iteration",
                           "subnet_mask", "taken_ips", "python_client_script_path", "ip_pool_range"]

        for field in required_fields:
            if field not in self.data_json:
                print(f"Lacking field in the json file : {field}")
                return False
        return True

    def check_fields_length(self) -> bool:
        # Vérifier l'intégrité des longueurs des listes
        if not (len(self.data_json["remote_user"]) == len(self.data_json["remote_host"]) == len(
                self.data_json["remote_passwords"])):
            print("Les longueurs des listes 'remote_user', 'remote_host' et 'remote_passwords' ne correspondent pas.")
            print("Vous avez probablement oublié de mettre à jour l'un des trois champs. Il doit manquer un mot "
                  "de passe, un nom d'utilisateur ou une adresse IP.")
            return False

        if len(self.data_json["remote_user"]) == 0:
            print("Aucun ordinateur n'a été ajouté.")
            return False
        return True

    def get_max_computers_per_iteration(self) -> int:
        return self.data_json.get("max_computers_per_iteration")

    def get_number_of_computers(self) -> int:
        return len(self.data_json.get("remote_user"))

    def get_python_script_path(self, user_index: int = 0) -> str:
        """
        Return the path to the python scripts folder **on the client computer** via it's username index listed in the
        json file.
        :param user_index: Index of the username in the json file
        :return: The string of the path of the
        """
        path_chose_by_user: str = self.data_json.get("python_client_script_path")
        if path_chose_by_user == "":
            return os.path.join(r'C:\Users', self.data_json.get("remote_user")[user_index], Infos.project_name)

        return os.path.join(self.data_json.get("python_client_script_path"),
                            self.data_json.get("remote_user")[user_index], Infos.project_name)

    def is_path_valid(self, path="") -> bool:
        evaluate_path = self.get_python_script_path() if path == "" else path

        # Détecte l'OS actuel
        current_os = os.name

        # Expression régulière pour les chemins de fichiers Windows
        windows_regex = re.compile(
            r'^\w:[\\/](?:[\w\-._]+\\)*\w[\w\-._]*\.py$'
        )

        # Expression régulière pour les chemins de fichiers Linux
        linux_regex = re.compile(
            r'^/(?:[\w\-._]+/)*\w[\w\-._]*\.py$'
        )

        # Vérifie si le chemin est valide pour l'OS actuel
        if current_os == 'nt':  # Windows
            return bool(windows_regex.match(evaluate_path))
        elif current_os == 'posix':  # Linux
            return bool(linux_regex.match(evaluate_path))
        else:
            return False

    def does_file_exists(self, path="") -> bool:
        evaluate_path: str = self.get_python_script_path() if path == "" else path
        return os.path.isfile(evaluate_path) and path.endswith('.py')

    def get_ip_address(self, i: int):
        return self.data_json.get("remote_host")[i]

    def get_python_requirements_path(self, i: int):
        return os.path.join(self.get_python_script_path(i), "requirements_client.txt")

    @staticmethod
    def get_server_python_installer_path() -> str:
        current_file_path: str = os.path.dirname(os.path.abspath(__file__))
        installer_path = os.path.join(current_file_path, "..", "..", "..", "python_3.11.3.exe")
        return os.path.abspath(installer_path)

    @staticmethod
    def get_installer_name() -> str:
        return "python_" + Data.python_precise_version + ".exe"

    def get_client_info(self, i: int) -> tuple[str, str, str]:
        """
        Return the tuple (ip_address, username, password) of the client computer at index i.
        :param i: Client index.
        :return: Tuple (ip_address, username, password)
        """
        return self.data_json.get("remote_host")[i], self.data_json.get("remote_user")[i], \
            self.data_json.get("remote_passwords")[i]

    def get_mac_address(self, ip_address) -> str | None:
        """
        Return the MAC address of the computer with the given IP address.
        :param ip_address: IP address of the computer.
        :return: MAC address of the computer.
        """

        if not self.__is_valid_ipv4_address(ip_address):
            raise ValueError("L'adresse IP n'est pas valide.")

        if ip_address not in self.ipaddresses:
            return None

        if self.ipaddresses[ip_address] == "" or self.ipaddresses[ip_address] == "00:00:00:00:00:00":
            return None

        return self.ipaddresses[ip_address]

    def add_mac_address(self, mac_address: str, ip_address: str) -> None:
        if not self.__is_valid_ipv4_address(ip_address):
            raise ValueError("L'adresse IP n'est pas valide.")

        if not self.is_valid_mac_address(mac_address):
            raise ValueError("L'adresse MAC n'est pas valide.")

        if ip_address in self.ipaddresses:
            print("IP address already in dictionary, overwriting it.")
        self.ipaddresses[ip_address] = mac_address

    @staticmethod
    def is_valid_mac_address(mac_address):
        """
        Return True if the given MAC address is valid, False otherwise.
        :param mac_address: MAC address to validate.
        :return: True if the given MAC address is valid, False otherwise.
        """
        # noinspection RegExpSuspiciousBackref
        mac_regex = re.compile(
            r'^([0-9A-Fa-f]{2}([:-]))(?:[0-9A-Fa-f]{2}\2){4}[0-9A-Fa-f]{2}$'
        )
        return bool(mac_regex.match(mac_address))

    def get_ip_range(self):
        raw_ip_range: str = self.data_json.get("ip_pool_range")
        return generate_ip_range(raw_ip_range[0], raw_ip_range[1])

    def get_passwords_with_ip(self, ip_address: str) -> str | None:
        for i in range(len(self.get_data_json()["remote_host"])):
            if self.get_data_json()["remote_host"][i] == ip_address:
                return self.get_data_json()["remote_passwords"][i]
        return None

    def get_computer_info(self, j) -> dict[str, str, str] | None:
        i = 0
        for computer in self.computers_data.values():
            if i == j:
                return computer
            i += 1
        return None

    def save_computer_data(self) -> None:
        """
        Save the computers data in the computers_database.json file.
        Creates a backup of the file before saving, just in case.
        :return: Nothing.
        """
        with open(find_file(self.json_computers_database_filename), 'w') as file:
            json.dump("computers_database_backup.json", file, indent=4)
        with open(find_file(self.json_computers_database_filename), "w") as f:
            json.dump(self.computers_data, f, indent=4)

    def get_username_per_ip(self, ip_address: str):
        for ip in self.data_json["remote_host"]:
            if ip == ip_address:
                return self.data_json["remote_user"][self.data_json["remote_host"].index(ip)]
