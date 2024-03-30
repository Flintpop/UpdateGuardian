import sys

import apscheduler.schedulers

from path_production_fix import add_project_to_path

add_project_to_path()

from src.server.application.cli import Cli
from src.server.application.scheduler_manager import SchedulerManager
from src.server.infrastructure.setup_manager import SetupManager
from src.server.logs_management.server_logger import log_error
from src.server.update_management.network_update_manager import UpdateManager


class Program:
    """
    Main class of the program. It is used to start the program and to stop it.
    Initializes the different managers, and starts the CLI and the scheduler.
    """
    def __init__(self):
        self.setup_manager = SetupManager()
        self.update_manager = UpdateManager()
        self.cli: Cli = Cli(update_manager=self.update_manager)
        self.scheduler_manager = SchedulerManager(self.update_manager, self.setup_manager)

    def start(self):
        try:
            if self.setup_manager.server_setup():
                self.scheduler_manager.start()
            else:
                log_error("Failed to set up the server. Exiting...")
                sys.exit(1)

            self.cli.start()

            self.scheduler_manager.stop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        try:
            self.scheduler_manager.stop()
        except apscheduler.schedulers.SchedulerNotRunningError:
            pass


if __name__ == '__main__':
    # TODO: Logique de maj automatique
    Program().start()
