# -----------------------------------------------------------
# test_mails.py
# Author: darwh
# Date: 07/06/2023
# Description: Tests for the email system. Manual test but the formatting is done automatically, as well as the
#              sending of the email, and the content of it is simulated too.
# -----------------------------------------------------------
import json
import os.path
import unittest

from src.server.infrastructure.paths import ServerPath
from src.server.report.mails import EmailResults, setup_email_config, load_email_infos
from src.server.update_management.network_update_manager import UpdateManager


class TestMails(unittest.TestCase):
    def setUp(self) -> None:
        if not load_email_infos():
            print("No email config found, creating one to run this test")
            setup_email_config()

        ServerPath.json_computers_database_filename = "test_computers_database.json"
        with open(ServerPath.get_database_path(), "w") as file:
            json.dump({
                "test_computer": {
                    "username": "test_computer\\serveur",
                    "mac_address": "08:00:27:08:61:22",
                    "hostname": "test_computer",
                    "ipv4": "192.168.2.73",
                    "host_key": "ssh-rsa AAAAB3NzaC1yc2E"
                },
                "test_computer2": {
                    "username": "test_computer2\\serveur",
                    "mac_address": "08:00:27:07:61:22",
                    "hostname": "test_computer2",
                    "ipv4": "192.168.2.73",
                    "host_key": "ssh-rsa AAAAB3NzaC1yc2ssE"
                },
                "test_computer3": {
                    "username": "test_computer3\\serveur",
                    "mac_address": "08:00:27:08:61:22",
                    "hostname": "test_computer3",
                    "ipv4": "192.168.2.73",
                    "host_key": "ssh-rsa AAAAB3NzaC1yc2Ee"
                },
                "test_computer4": {
                    "username": "test_computer4\\serveur",
                    "mac_address": "08:00:27:08:61:22",
                    "hostname": "test_computer4",
                    "ipv4": "192.168.2.73",
                    "host_key": "ssh-rsa AAAAB3NzaC1yc2Ei"
                }
            }, file, indent=4)

        # BUG: Ça vient de la ligne suivante. Dans load_computer, il obtient le fichier json, mais le mauvais. Il prend
        # ServerPath et non pas UpdateManager. Voir conv chatGPT.
        self.database: UpdateManager = UpdateManager.load_computer_data_if_exists()
        # TODO: Bug ici, computer not found
        computer_mod = self.database.find_computer("test_computer")
        if computer_mod is None:
            raise ValueError("Computer not found")

        computer_mod.updates_string = [
            '2023-05 Aperçu de la mise à jour cumulative de .NET Framework 3.5',
            '4.8 et 4.8.1 Windows 10 Version 22H2 pour x64(KB5026958)',
            '2023-05 Mise à jour cumulative pour Windows 10 Version 22H2 de x64 avec systèmes basés dessus (KB5026361)'
        ]
        computer_mod.no_updates = False
        computer_mod.updated_successfully = True

        computer_mod = self.database.find_computer("test_computer2")
        computer_mod.updates_string = [
            '2022-05 Aperçu de la mise à jour cumulative de .NET Framework 3.5',
        ]
        computer_mod.no_updates = False
        computer_mod.updated_successfully = True

        computer_mod = self.database.find_computer("test_computer3")
        computer_mod.no_updates = True
        computer_mod.updated_successfully = True

        computer_mod = self.database.find_computer("test_computer4")
        computer_mod.error = "Je suis une erreur"
        computer_mod.no_updates = False
        computer_mod.updated_successfully = False

    def test_send_mail(self):
        EmailResults(self.database).send_email_results()
        database_path = ServerPath.get_database_path()
        if os.path.exists(ServerPath.get_database_path() and database_path == "test_computers_database.json"):
            os.remove(ServerPath.get_database_path())
