import sys

from newServer.application.cli import Cli
from newServer.application.scheduler_manager import SchedulerManager
from newServer.infrastructure.setup_manager import SetupManager
from newServer.logs_management.server_logger import log_error
from newServer.update_management.network_update_manager import UpdateManager


class Program:
    def __init__(self):
        self.setup_manager = SetupManager()
        self.update_manager = UpdateManager()
        self.cli: Cli = Cli()
        self.scheduler_manager = SchedulerManager(self.update_manager, self.setup_manager)

    def start(self):
        if self.setup_manager.server_setup():
            self.scheduler_manager.start()
        else:
            log_error("Failed to set up the server. Exiting...")
            sys.exit(1)

        self.cli.start()

    def stop(self):
        self.scheduler_manager.stop()


if __name__ == '__main__':
    # TODO: Logique de maj automatique
    Program().start()
