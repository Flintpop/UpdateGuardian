import ipaddress
import json


class Data:
    """
    Class that loads the data from the JSON file.
    Getters are used to access the data.
    Checks are made to ensure the integrity of the JSON file.
    """
    data_json: dict = {}

    def __init__(self, filename: str = '../computers_informations.json', json_data: dict = None):
        if json_data is None:
            self.__load_data(filename)
        else:
            self.data_json = json_data

        data_check: bool = self.__check_json_integrity()
        if not data_check:
            raise ValueError("Le fichier JSON est invalide.")

    def __load_data(self, filename: str = '../computers_informations.json'):
        # Ouvrir le fichier JSON en mode lecture
        with open(filename, 'r', encoding='utf-8') as fichier:
            # Charger le contenu du fichier JSON dans une variable
            self.data_json: dict = json.load(fichier)

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
        required_fields = ["remote_user", "remote_host", "remote_password", "max_computers_per_iteration",
                           "subnet_mask", "taken_ips"]
        for field in required_fields:
            if field not in self.data_json:
                print(f"Champ manquant : {field}")
                return False

        # Vérifier l'intégrité des longueurs des listes
        if not (len(self.data_json["remote_user"]) == len(self.data_json["remote_host"]) == len(
                self.data_json["remote_password"])):
            print("Les longueurs des listes 'remote_user', 'remote_host' et 'remote_password' ne correspondent pas.")
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
