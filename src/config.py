import json

global remote_user
global remote_host
global remote_password
global remote_command


def load_data() -> dict:
    # Ouvrir le fichier JSON en mode lecture
    with open('../computers_informations.json', 'r', encoding='utf-8') as fichier:
        # Charger le contenu du fichier JSON dans une variable
        data = json.load(fichier)
    global remote_user
    global remote_host
    global remote_password
    global remote_command

    # Afficher le contenu de la variable data (qui contient les données JSON)
    remote_user = data_dict_json['remote_user']
    remote_host = data_dict_json['remote_host']
    remote_password = data_dict_json['remote_password']
    remote_command = "powershell.exe Get-Process"
    return data


if __name__ == '__main__':
    data_dict_json = load_data()
    # remote_user = data_dict_json['remote_user']
    # remote_host = data_dict_json['remote_host']
    # remote_password = data_dict_json['remote_password']
    # remote_command = "powershell.exe Get-Process"
