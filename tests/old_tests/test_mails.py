# -----------------------------------------------------------
# test_mails.py
# Author: darwh
# Date: 07/06/2023
# Description: 
# -----------------------------------------------------------
import json
import unittest

from src.server.data.computer_database import ComputerDatabase
from src.server.warn_admin.mails import EmailResults


class TestMails(unittest.TestCase):
    def setUp(self) -> None:
        ComputerDatabase.json_computers_database_filename = "test_computers_database.json"
        with open(ComputerDatabase.json_computers_database_filename, "w") as file:
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

        self.database: ComputerDatabase = ComputerDatabase.load_computer_data_if_exists()
        computer_mod = self.database.find_computer("test_computer")
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
