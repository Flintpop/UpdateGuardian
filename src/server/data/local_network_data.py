import ipaddress
import os
import re
import json

from src.server.commands.path_functions import find_file


class Data:
    """
    Class that loads the data from the JSON file.
    Getters are used to access the data.
    Checks are made to ensure the integrity of the JSON file.
    """
    project_name = "UpdateGuardian"
    python_version = "3.11"
    python_folder_name = f"Python{python_version.replace('.', '')}"
    python_precise_version = "3.11.3"
    data_json: dict = {}

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

    def __check_json_integrity(self) -> bool:
        # Vérifier la présence des champs requis
        required_fields = ["remote_user", "remote_host", "remote_passwords", "max_computers_per_iteration",
                           "subnet_mask", "taken_ips", "python_client_script_path"]

        for field in required_fields:
            if field not in self.data_json:
                print(f"Champ manquant : {field}")
                return False

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

        return True

    def get_max_computers_per_iteration(self) -> int:
        return self.data_json.get("max_computers_per_iteration")

    def get_number_of_computers(self) -> int:
        try:
            return len(self.data_json.get("remote_user"))
        except TypeError:
            raise TypeError("The JSON file is empty.")
        except AttributeError:
            raise AttributeError("The JSON file wrongly formatted.")

    def get_python_script_path(self, user_index: int = 0) -> str:
        """
        Return the path to the python scripts folder **on the client computer** via it's username index listed in the
        json file.
        :param user_index: Index of the username in the json file
        :return: The string of the path of the
        """
        path_chose_by_user: str = self.data_json.get("python_client_script_path")
        if path_chose_by_user == "":
            return os.path.join(r'C:\Users', self.data_json.get("remote_user")[user_index], Data.project_name)

        return os.path.join(self.data_json.get("python_client_script_path"),
                            self.data_json.get("remote_user")[user_index], Data.project_name)

    def is_path_valid(self, path="") -> bool:
        # TODO: A tester
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
