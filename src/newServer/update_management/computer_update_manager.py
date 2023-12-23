import traceback

from newServer.core.remote_computer_manager import RemoteComputerManager
from newServer.infrastructure.config import Infos
from newServer.logs_management.computer_logger import ComputerLogger
from newServer.report.mails import send_error_email
from newServer.update_management.computer_dependencies_manager import ComputerDependenciesManager


class ComputerUpdateManager:
    def __init__(self, computer: 'RemoteComputerManager'):
        self.computer = computer
        self.log = computer.log
        self.log_raw = computer.log_raw
        self.log_add_vertical_space = computer.log_add_vertical_space
        self.log_error = computer.log_error

        self.hostname = computer.get_hostname()
        self.ipv4 = computer.get_ipv4()
        self.mac_address = computer.get_mac_address()

        self.updated_successfully = False
        self.no_updates = False
        self.traceback = None
        self.error = None

    def update(self):
        # noinspection PyBroadException
        try:
            self.log(f"Updating computer {self.hostname}... Checking if the PC is awake...")
            if not self.computer.is_pc_on():
                self.log("Waking up the pc...")
                if not self.computer.awake_pc():
                    return self.log_error("Could not awake computer... Cannot Update.")

            self.log_add_vertical_space()
            if not self.computer.connect():
                return self.log_error("Could not connect to computer... Cannot Update.")

            self.log_add_vertical_space()
            if not self.install_prerequisites_client():
                return self.log_error("Could not install prerequisites on the client... Cannot Update.")

            self.log_add_vertical_space()
            update_successful, up = self.install_update()
            if not update_successful:
                return self.log_error("Could not install update on client.")

            self.no_updates = False

            if up is not None:
                self.no_updates = True

            self.log_add_vertical_space()
            if not self.computer.shutdown():
                return self.log_error("Could not shut down client.")

            self.updated_successfully = True
            return True
        except Exception as e:
            self.log_add_vertical_space(2)
            self.log_raw("\n" + ComputerLogger.get_header_style_string("ERROR"))
            self.log_error(f"Unhandled error. Could not update computer {self.hostname}: ")
            self.log_add_vertical_space(1)

            self.traceback: str = traceback.format_exc()
            self.error = e

            self.log_error(f"Here is the traceback:\n{self.traceback}")
            if Infos.email_send:
                send_error_email(computer=self.computer, error=str(self.error), traceback=self.traceback)

            return False

    def install_prerequisites_client(self):
        self.log("Checking if pre-requisites are installed on the client...")
        if not self.prerequisites_installed():
            self.log_error("Pre-requisites not installed on the client, and could not be installed.")
            return False

        self.log("Pre-requisites installed on the client.")
        return True

    def prerequisites_installed(self):
        computer_dependencies_manager = ComputerDependenciesManager(self.computer)
        if not computer_dependencies_manager.python_scripts(computer=self):
            return False

        self.log_add_vertical_space()
        if not computer_dependencies_manager.python_installation(computer=self):
            return False

        self.log_add_vertical_space()
        if not computer_dependencies_manager.python_path(computer=self):
            return False

        self.log_add_vertical_space()
        if not computer_dependencies_manager.python_packages(computer=self):
            return False

        self.log_add_vertical_space()
        return True
