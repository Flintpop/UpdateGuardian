import concurrent
import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from src.server.core.remote_computers_database import RemoteComputerDatabase
from src.server.exceptions.ConnectionSSHException import ConnectionSSHException
from src.server.factory.computer_updater_manager_factory import ComputerUpdaterManagerFactory
from src.server.infrastructure.config import Infos
from src.server.infrastructure.paths import ServerPath
from src.server.logs_management.server_logger import log, log_new_lines, log_error
from src.server.report.mails import EmailResults
from src.server.update.auto_update_factory import AutoUpdateFactory
from src.server.update_management.computer_update_manager import ComputerUpdateManager


class UpdateManager(RemoteComputerDatabase):
    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.computers: list['ComputerUpdateManager'] = []

    def execute_update(self):
        """
        Executes the automation update program
        :returns: None
        """
        with self.lock:
            log("Executing scheduled task...", print_formatted=False)

            log("Checking for updates..., may be converted to forced task if there are updates",
                print_formatted=False)
            AutoUpdateFactory.create_auto_update(force_update=True).update()

            log_new_lines(2)

            self.load_computer_data()
            self.load_email_infos()

            self.update_all_computers()

    def force_execute_update(self, already_updated: bool = False):
        """
        Forces the execution of the automation update program
        :returns: None
        """
        with self.lock:
            if not already_updated:
                AutoUpdateFactory.create_auto_update(force_update=True).update()
            log("Checking for updates...", print_formatted=False)
            # check_for_update_and_restart("--force")

            self.load_computer_data()
            self.load_email_infos()
            log("Force executing scheduled task...", print_formatted=False)
            print()
            log_new_lines(2)
            self.update_all_computers()

    def update_all_computers(self):
        max_workers = self.get_max_number_of_simultaneous_updates()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            computers: list[ComputerUpdateManager] = self.get_computers()
            if not computers:
                log("No computers to update.")
                return

            # Lancer les tâches de mise à jour et récupérer les résultats
            future_to_computer = {
                executor.submit(self.update_one_computer, computer): computer for computer in computers
            }

            # Itérer sur les résultats pour détecter et traiter les exceptions
            for future in concurrent.futures.as_completed(future_to_computer):
                computer = future_to_computer[future]
                try:
                    future.result()  # Cela lèvera une exception si la tâche a échoué
                    # Traiter le résultat ici si nécessaire
                except Exception as exc:
                    # Récupérer le traceback complet
                    tb = traceback.format_exc()
                    log(f"Computer update failed for {computer} with exception: {exc}\nTraceback: {tb}",
                        print_formatted=False)

        log("Update rollout over. Checks logs for more informations.", print_formatted=False)
        if Infos.email_send:
            log("Sending result email...", print_formatted=False)
            EmailResults(self).send_email_results()

    @staticmethod
    def update_one_computer(computer: ComputerUpdateManager):
        log(message="Updating computer " + computer.get_hostname() + "...")

        try:
            if not computer.update():
                computer.updated_successfully = False
                computer.no_updates = False

                log_error("Error while updating computer " + computer.get_hostname())
                log_error("Skipping this computer...")
                return

            if computer.no_updates:
                log("Computer " + computer.get_hostname() + " has no updates.")
                return

            log("Computer " + computer.get_hostname() + " updated successfully!")
        except ConnectionSSHException:
            log_error("SSH connection error on :" + computer.get_hostname())
            log_error("Skipping this computer...")

    def get_successfully_number_of_updated_computers(self) -> int:
        res = 0
        for computer in self.computers:
            if computer.updated_successfully and not computer.no_updates:
                res += 1

        return res

    def get_not_updated_computers(self) -> list['ComputerUpdateManager']:
        res = []
        for computer in self.computers:
            if not computer.updated_successfully:
                res.append(computer)

        return res

    def get_computers_without_new_updates(self) -> list['ComputerUpdateManager']:
        res = []
        for computer in self.computers:
            if computer.no_updates and computer.updated_successfully:
                res.append(computer)

        return res

    def get_number_of_updatable_computers(self) -> int:
        res = []
        for computer in self.computers:
            if computer.no_updates is not None and not computer.no_updates:
                res.append(computer)
        return len(res)

    def get_updated_computers(self) -> list['ComputerUpdateManager']:
        computers: list[ComputerUpdateManager] = []
        for computer in self.computers:
            if computer.updated_successfully and not computer.no_updates:
                computers.append(computer)

        return computers

    def get_number_of_failed_computers(self) -> int:
        res = []
        for computer in self.computers:
            if not computer.updated_successfully:
                res.append(computer)
        return len(res)

    def add_computer(self, computer: 'ComputerUpdateManager') -> None:
        self.computers.append(computer)

    def load_computer_data(self) -> None:
        computers_data_json_file = ServerPath.get_database_path()

        if not ServerPath.exists(computers_data_json_file):
            raise FileNotFoundError(f"Cannot find the file '{os.path.abspath(computers_data_json_file)}'. "
                                    f"It should have been created at the" "setup phase. Please check the setup process,"
                                    " and restart the program.")

        UpdateManager.__load_computers_from_json(self, computers_data_json_file, init_logger=True)

        log(f"Loaded {len(self.computers)} computers from the database.")

    @classmethod
    def load_computer_data_if_exists(cls, init_logger=False) -> 'UpdateManager':
        computer_database = UpdateManager()
        computers_data_json_file = ServerPath.get_database_path()

        if not ServerPath.exists(computers_data_json_file):
            return computer_database

        cls.__load_computers_from_json(computer_database, computers_data_json_file, init_logger=init_logger)

        return computer_database

    @classmethod
    def __load_computers_from_json(cls, computer_database: 'UpdateManager', json_file_path: str,
                                   init_logger) -> None:
        with open(json_file_path, "r") as file:
            computer_database.computers_json = json.loads(file.read())

        computer_database.computers.clear()

        # Add all the computers to the database, using the Computer class.
        for computer_hostname in computer_database.computers_json:
            new_computer_dict = computer_database.computers_json[computer_hostname]
            new_computer = ComputerUpdaterManagerFactory.create_from_dictionary(
                new_computer_dict,
                init_logger=init_logger
            )
            computer_database.add_computer(new_computer)

    def find_computer(self, hostname: str) -> 'ComputerUpdateManager':
        for computer in self.computers:
            if computer.get_hostname() == hostname:
                return computer

    def get_computers(self) -> list[ComputerUpdateManager]:
        return self.computers

    def get_computer(self, index: int) -> ComputerUpdateManager:
        return self.computers[index]
