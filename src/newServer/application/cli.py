from newServer.application.cli_settings import modify_settings
from newServer.core.computer_update_manager import ComputerDatabaseManager
from newServer.infrastructure.setup_manager import load_launch_time
from newServer.logs_management.server_logger import log, log_new_lines
from newServer.update_management.network_update_manager import UpdateManager


class Cli:
    def __init__(self, update_manager: 'UpdateManager'):
        self.stopped = False
        self.update_manager = update_manager

    def start(self):
        """
        Thread used to change settings by the user.
        """
        log("Program started, settings loaded", print_formatted=False)
        log_new_lines()
        # force_start_execute_job()
        # return
        # noinspection PyUnboundLocalVariable
        while not self.stopped:
            scheduled_time = load_launch_time()

            day, hour = scheduled_time['day'], scheduled_time['hour']
            print(f"\nThe program is scheduled to start every {day} at {hour}:00.\n")
            print("Type 'settings' to modify settings.")
            print("Type 'force' to force start the scheduled task.")
            print("Type 'list' to list all the computers in the database.")
            print("Type 'shutdown' to shutdown all the computers in the database.")
            print("Type 'exit' to exit the program.\n")
            try:
                usr_input = input("> ")

                switcher = {
                    "settings": modify_settings,
                    "force": self.update_manager.force_execute_update,
                    "list": ComputerDatabaseManager.list_computers,
                    "shutdown": ComputerDatabaseManager.shutdown_all_computers,
                    "exit": self.stop_code
                }

                switcher.get(usr_input, lambda: print("Invalid input."))()
            except KeyboardInterrupt:
                log("Program stopped.", print_formatted=False)
                self.stop_code()
                break

    def stop_code(self):
        self.stopped = True
