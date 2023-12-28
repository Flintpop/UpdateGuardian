from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from newServer.core.remote_computer_manager import RemoteComputerManager
from newServer.core.remote_computers_database import RemoteComputerDatabase
from newServer.infrastructure.config import Infos
from newServer.logs_management.server_logger import log, log_new_lines, log_error
from newServer.report.mails import EmailResults
from newServer.update_management.computer_update_manager import ComputerUpdateManager


class UpdateManager:
    def __init__(self):
        self.lock = Lock()
        self.computer_database: RemoteComputerDatabase | None = None

    def execute_update(self):
        """
        Executes the automation update program
        :returns: None
        """
        with self.lock:
            log("Checking for updates...", print_formatted=False)
            # check_for_update_and_restart("--force")

            log("Executing scheduled task...", print_formatted=False)

            log_new_lines(2)

            self.computer_database: RemoteComputerDatabase = RemoteComputerDatabase.load_computer_data()
            self.computer_database.load_email_infos()

            self.update_all_computers()

    def force_execute_update(self):
        """
        Forces the execution of the automation update program
        :returns: None
        """
        with self.lock:
            log("Checking for updates...", print_formatted=False)
            # check_for_update_and_restart("--force")

            log("Force executing scheduled task...", print_formatted=False)
            log_new_lines(2)
            self.update_all_computers()

    def update_all_computers(self):
        max_workers = self.computer_database.get_max_number_of_simultaneous_updates()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Update all computers using threads
            computers: list[RemoteComputerManager] = self.computer_database.get_computers()
            executor.map(self.update_one_computer, computers)

        log("Update rollout over. Checks logs for more informations.")
        log("Sending result email...")
        if Infos.email_send:
            EmailResults(self.computer_database).send_email_results()

    @staticmethod
    def update_one_computer(remote_computer_manager: RemoteComputerManager):
        log(message="Updating computer " + remote_computer_manager.get_hostname() + "...")
        computer = ComputerUpdateManager(remote_computer_manager)

        if not computer.update():
            remote_computer_manager.download_log_file_ssh()
            computer.updated_successfully = False
            computer.no_updates = False

            log_error("Error while updating computer " + remote_computer_manager.get_hostname())
            log_error("Skipping this computer...")
            return

        if computer.no_updates:
            log("Computer " + remote_computer_manager.get_hostname() + " has no updates.")
            return

        log("Computer " + remote_computer_manager.get_hostname() + " updated successfully!")
