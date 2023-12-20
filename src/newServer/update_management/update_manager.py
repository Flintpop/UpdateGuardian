from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from newServer.core.remote_computers_database import RemoteComputerDatabase
from newServer.logs_management.server_logger import log, log_new_lines


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

    def update_all_computers(self):
        max_workers = self.computer_database.get_max_number_of_simultaneous_updates()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pass
