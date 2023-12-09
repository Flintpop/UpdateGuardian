import ipaddress
import os
import re
import json
import socket

from src.server.commands.path_functions import find_file
from src.server.config import Infos


def get_local_ipv4() -> str:
    """
    Get the IP address of the running computer.
    :return: The IP address of the running computer.
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
    server_ip_address: str = get_local_ipv4()
    data_json: dict = {}
    computers_data: dict = {}
    ipaddresses: dict = {}

    def __init__(self, filename: str = find_file(Infos.config_json_file), json_data: dict = None):
        if json_data is None:
            self.__load_data(filename)
        else:
            self.data_json = json_data

    def __load_data(self, filename: str = find_file(Infos.config_json_file)):
        # Ouvrir le fichier JSON en mode lecture
        with open(filename, 'r', encoding='utf-8') as fichier:
            # Charger le contenu du fichier JSON dans une variable
            self.data_json: dict = json.load(fichier)

    def get_data_json(self) -> dict:
        return self.data_json

    def get_max_number_of_simultaneous_updates(self) -> int:
        return self.data_json.get("max_computers_per_iteration")

    def get_number_of_computers(self) -> int:
        return len(self.data_json.get("remote_user"))

    def get_python_script_path(self, user_index: int = 0) -> str:
        """
        Return the path to the python scripts folder **on the client computer** via it's username index listed in the
        json file.
        :param user_index: Index of the username in the json file
        :return: The string path of the python scripts folder on the client computer
        """
        path_chose_by_user: str = self.data_json.get("python_client_script_path")
        from server.data.computer import Computer
        if path_chose_by_user == "":
            return Computer.join_path(r'C:\Users', self.data_json.get("remote_user")[user_index], Infos.PROJECT_NAME)

        return Computer.join_path(self.data_json.get("python_client_script_path"),
                                  self.data_json.get("remote_user")[user_index], Infos.PROJECT_NAME)

    @staticmethod
    def is_path_valid(path: str) -> bool:
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
            return bool(windows_regex.match(path))
        elif current_os == 'posix':  # Linux
            return bool(linux_regex.match(path))
        else:
            return False

    def does_file_exists(self, path="") -> bool:
        evaluate_path: str = self.get_python_script_path() if path == "" else path
        return os.path.isfile(evaluate_path) and path.endswith('.py')

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

    def get_passwords_with_ip(self, ip_address: str) -> str | None:
        for i in range(len(self.get_data_json()["remote_host"])):
            if self.get_data_json()["remote_host"][i] == ip_address:
                return self.get_data_json()["remote_passwords"][i]
        return None

    def get_username_per_ip(self, ip_address: str):
        for ip in self.data_json["remote_host"]:
            if ip == ip_address:
                return self.data_json["remote_user"][self.data_json["remote_host"].index(ip)]
