import json
import os
import traceback

from src.server.core.remote_computer_manager import RemoteComputerManager
from src.server.exceptions.ConnectionSSHException import ConnectionSSHException
from src.server.infrastructure.config import Infos
from src.server.logs_management.computer_logger import ComputerLogger
from src.server.report.mails import send_error_email
from src.server.ssh.commands import SSHCommandResult
from src.server.update_management.computer_dependencies_manager import ComputerDependenciesManager


class ComputerUpdateManager:
    def __init__(self, computer: 'RemoteComputerManager'):
        self.computer: 'RemoteComputerManager' = computer
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

        self.updates_string = None

    def update(self):
        # noinspection PyBroadException
        try:
            self.log(f"Updating computer {self.hostname}... Checking if the PC is awake...")
            if not self.computer.is_pc_on():
                self.log("Waking up the pc...")
                if not self.computer.awake_pc():
                    self.log_error("Could not awake computer... Cannot Update.")
                    raise ConnectionSSHException()

            self.log_add_vertical_space()
            if not self.computer.connect():
                self.log_error("Could not connect to computer... Cannot Update.")
                raise ConnectionSSHException()

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
            self.computer.shutdown()

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

        if not computer_dependencies_manager.send_client_application():
            return False

        self.log_add_vertical_space()
        return True

    def install_update(self):
        self.log("Installing update on the client...")
        try:
            result: dict = self.__start_python_script()

            if not result:
                self.log_error("Could not start python script.")
                return False, None

            if result["ErrorMessage"]:
                self.log_error(f"An error occurred :\n{result['ErrorMessage']}.")
                return False, None

            self.updates_string = result["UpdateNames"]
            if result["RebootRequired"]:
                self.log("Pc is rebooting...")
                four_hours: int = 60 * 60 * 4
                if not self.wait_for_pc_to_be_online_again(timeout=four_hours):
                    self.log_error("Could not wait for pc to be online again.")
                    return False, None

                self.computer.set_ssh_session_to_commands()
                return True, None
            if result["UpdateCount"] == 0:
                self.log("No updates found.")
                return True, "no updates found"

        except Exception as e:
            self.log_error("Unhandled error while installing update on client:\n" + str(e) + "\nTraceback:\n" +
                           traceback.format_exc())
            return False, None

        return True, None

    def __start_python_script(self):
        self.log("Starting the python script...")
        command: str = "cd " + Infos.PROJECT_NAME + " && python " + self.computer.paths.get_main_script()

        res: 'SSHCommandResult' = self.computer.execute_command(command)
        stdout, stderr = res.stdout, res.stderr

        self.log("Python script started.")

        if stderr:
            self.log_error(f"Error while starting the python script:\n{stderr}")
            return None
        if stdout:
            if "traceback" in stdout.lower():
                self.log_error(f"Error while starting the python script:\n\n{stdout}")
                return None
            self.log(f"Stdout : \n{stdout}")

            json_filename: str = f"results-{self.hostname}.json"
            remote_file_path: str = self.computer.paths.join(self.computer.paths.get_project_directory(),
                                                             json_filename.replace(f"-{self.hostname}", ""))

            if not self.computer.download_file(json_filename, remote_file_path):
                self.log_error("Could not download the json file.")
                return None

            with open(json_filename, "r") as f:
                json_res: dict = json.load(f)
                self.log(f"Here is the json file content:\n{json.dumps(json_res, indent=4)}", new_lines=1)

            os.remove(json_filename)

            return json_res
        self.log_error("The python script returned nothing.")
        return None

    def wait_for_pc_to_be_online_again(self, timeout: int):
        """
        Wait for the pc to be online again, and reconnect to it.
        """
        self.computer.wait_for_ssh_shutdown()

        if not self.computer.wait_and_reconnect(timeout=timeout):
            self.log_error(f"Failed to reconnect to {self.hostname}, timeout likely reached.")
            return False
        return True

    def get_hostname(self):
        return self.hostname

    def __str__(self):
        return f"ComputerUpdateManager({self.hostname})"
