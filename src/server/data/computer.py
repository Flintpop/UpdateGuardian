import json
import os
import time
import traceback

import paramiko
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from server.data.server_join_path import ServerPath
from src.server.commands.install_client_files_and_dependencies import python_scripts, python_installation, \
    python_path, python_packages, wait_for_ssh_shutdown
from src.server.commands.path_functions import list_files_recursive, find_directory, change_directory_to_root_folder
from src.server.config import Infos
from src.server.environnement.server_logs import ComputerLogger
from src.server.ssh.ssh_commands import is_pc_on, stdout_err_execute_ssh_command, wait_and_reconnect, \
    download_file_ssh
from src.server.wake_on_lan.wake_on_lan_utils import send_wol
from src.server.warn_admin.mails import send_error_email


class Computer:
    """
    A class used to represent a computer in the local network.
    It contains : \n
    - hostname\n
    - ipv4\n
    - mac_address\n
    - username\n
    - logger (logging.Logger, used to log the computer's activity in a file)\n
    """

    def __init__(self, computer_info: dict, init_logger=False) -> None:

        self.no_updates = None
        self.hostname = computer_info.get("hostname")
        self.ipv4 = computer_info.get("ipv4")
        self.mac_address = computer_info.get("mac_address")
        self.username = computer_info.get("username")

        self.__private_key: Ed25519PrivateKey | None = None
        self.__public_key: Ed25519PublicKey | None = None

        self.private_key_filepath: str = Computer.join_path(find_directory("ssh_keys"), f"private_key_{self.hostname}")
        self.public_key_filepath: str = ServerPath.join(find_directory("ssh_keys"), f"public_key_{self.hostname}.pub")

        self.check_informations_integrity()

        self.client_project_folder: str = Computer.join_path(self.get_project_directory_on_client(), self.username,
                                                             Infos.PROJECT_NAME)

        change_directory_to_root_folder()
        self.logs_filename = "logs"
        self.logs_filename = ServerPath.join(self.logs_filename, f"{self.hostname}.log")

        if init_logger:
            self.computer_logger = ComputerLogger(self.logs_filename)

        self.ssh_session: paramiko.SSHClient | None = None
        self.current_log_message: str = ""

        self.updated_successfully: bool = False

        self.updates_string: list[str] = []
        self.error: str | None = None
        self.traceback: str | None = None

    def update(self) -> bool:
        # noinspection PyBroadException
        try:
            self.log(f"Updating computer {self.hostname}... Checking if the PC is awake...")
            if not self.is_pc_awake():
                self.log("Waking up the pc...")
                if not self.awake_pc():
                    return self.log_error("Could not awake computer... Cannot Update.")

            self.log_add_vertical_space()
            if not self.connect():
                return self.log_error("Could not connect to computer... Cannot Update.")

            self.log_add_vertical_space()
            if not self.install_prerequisites_client():
                return self.log_error("Could not install prerequisites on the client... Cannot Update.")

            self.log_add_vertical_space()
            res, up = self.install_update()
            if not res:
                return self.log_error("Could not install update on client.")

            self.no_updates = False

            if up is not None:
                self.no_updates = True

            self.log_add_vertical_space()
            if not self.shutdown():
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
                send_error_email(computer=self, error=str(self.error), traceback=self.traceback)

            return False

    def connect(self):
        self.log(message=f"Connecting to {self.hostname} computer via SSH...")
        try:
            self.connect_ssh_procedures()

            self.log(f"Connected via SSH to computer {self.hostname}.")
            return True
        except paramiko.AuthenticationException as e:
            self.log_add_vertical_space()
            self.log_error("Authentication failed: " + str(e))
            self.log_error(f"Please, check your username and password for the computer {self.hostname}.")
            self.log_error("The connection password may be the os connection password if there are no "
                           "microsoft accounts linked.\nOtherwise, it is the account password.")
            self.log_error("Furthermore, if there are several accounts to the computer that a user can connect to,"
                           f"make sure the username {self.username} is something as follows: \n'pc-name\\username@ip' "
                           "(or 'pc-name\\username@hostname').")
            self.log_add_vertical_space()
            self.log_error(f"Here are some informations about the connection settings:"
                           f"\n\tip: {self.ipv4}"
                           f"\n\tmac: {self.mac_address}"
                           f"\n\tusername: {self.username}")
            return False
        except Exception as e:
            self.log_error(f"Unhandled error. Could not connect to {self.hostname}:\n " + str(e))
            self.log_error(f"Here is the traceback: \n{traceback.format_exc()}\n")
            return False

    def connect_ssh_procedures(self):
        self.__private_key = self.get_private_key()
        if not self.__private_key:
            self.log_error("Could not get private key... Cannot connect.")
            return False

        self.ssh_session = paramiko.SSHClient()
        self.ssh_session.set_missing_host_key_policy(paramiko.RejectPolicy())
        self.ssh_session.load_host_keys(ServerPath.join(ServerPath.get_home_path(), ".ssh", "known_hosts"))
        self.ssh_session.connect(self.hostname, username=self.username, pkey=self.__private_key)

    def connect_if_awake(self) -> bool:
        if not self.is_pc_awake():
            self.log("Waking up the pc...")
            if not self.awake_pc():
                self.log("Could not awake computer...", "warning")
                return False

        self.log_add_vertical_space()
        if not self.connect():
            self.log("Could not connect to computer...", "warning")
            return False
        return True

    def is_pc_awake(self) -> bool:
        if not is_pc_on(computer=self, timeout=5):
            self.log("The pc is off.")
            return False
        self.log("The pc is on.")
        return True

    def waiting_pc_off(self, timeout=40) -> bool:
        """
        Wait for the pc to be off.
        :param timeout: The number of seconds to wait that the pc is off.
        :return: True if the pc is off, False otherwise.
        """
        start_time: float = time.time()
        while start_time + timeout > time.time():
            if not is_pc_on(computer=self, timeout=3, print_log_connected=False):
                self.log("The pc is off.")
                return True
        return False

    def awake_pc(self):
        """
        Turn on the pc to update windows.
        :return: True if the pc is on, False otherwise.
        """
        send_wol(mac_address=self.mac_address, ip_address=self.ipv4)

        if not is_pc_on(self, timeout=20):
            self.log_error("Error, the pc is still off.")
            return False

        self.log("The pc is awake...")
        return True

    def install_prerequisites_client(self):
        self.log("Checking if pre-requisites are installed on the client...")
        if not self.prerequisites_installed():
            self.log_error("Pre-requisites not installed on the client, and could not be installed.")
            return False

        self.log("Pre-requisites installed on the client.")
        return True

    def install_update(self) -> tuple[bool, str | None]:
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

                return True, None
            if result["UpdateCount"] == 0:
                self.log("No updates found.")
                return True, "no updates found"

        except Exception as e:
            self.log_error("Unhandled error while installing update on client:\n" + str(e) + "\nTraceback:\n" +
                           traceback.format_exc())
            return False, None

        return True, None

    def __start_python_script(self) -> dict | None:
        self.log("Starting the python script...")
        command: str = "cd " + Infos.PROJECT_NAME + " && python " + self.get_main_script_path()

        stdout, stderr = stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log("Python script started.")

        if stderr:
            self.log_error(f"Error while starting the python script:\n\n{stderr}")
            return None
        if stdout:
            if "Traceback" in stdout:
                self.log_error(f"Error while starting the python script:\n\n{stdout}")
                return None
            self.log(f"Stdout : \n{stdout}")

            json_filename: str = f"results-{self.hostname}.json"
            remote_file_path: str = Computer.join_path(self.get_project_directory_on_client(),
                                                       json_filename.replace(f"-{self.hostname}", ""))

            if not download_file_ssh(self.ssh_session, json_filename, remote_file_path):
                self.log_error("Could not download the json file.")
                return None

            with open(json_filename, "r") as f:
                json_res: dict = json.load(f)
                self.log(f"Here is the json file content:\n{json.dumps(json_res, indent=4)}", new_lines=1)

            os.remove(json_filename)

            return json_res
        self.log_error("The python script returned nothing.")
        return None

    def shutdown(self):
        """
        Shutdown the pc after the update.
        :return: True if the pc is off, False otherwise.
        """
        self.log(level="info", message="Shutting down the pc...")
        command: str = "shutdown /s /t 0"

        stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log(level="info", message="The pc should be off...")
        if not self.waiting_pc_off(timeout=600):
            return False
        return True

    def prerequisites_installed(self):
        if not python_scripts(computer=self):
            return False

        self.log_add_vertical_space()
        if not python_installation(computer=self):
            return False

        self.log_add_vertical_space()
        if not python_path(computer=self):
            return False

        self.log_add_vertical_space()
        if not python_packages(computer=self):
            return False

        self.log_add_vertical_space()
        return True

    def download_log_file_ssh(self) -> bool:
        """
        Download the log file from the client.
        :return: True if the log file has been downloaded, False otherwise.
        """
        if not is_pc_on(self, timeout=20):
            self.log_error("Error, the pc is not connectable, could not download log file.")
            return False

        if not self.connect():
            self.log_error("Could not connect via SSH to the client.")
            return False

        self.log("Downloading log file from the client...")
        local_path: str = ServerPath.join(self.logs_filename, "..", f"update_windows-{self.hostname}-ERROR-LOGS.log")
        remote_file_path: str = Computer.join_path(self.get_project_directory_on_client(), "update_windows.log")
        if not download_file_ssh(self.ssh_session, local_path, remote_file_path):
            self.log_error("Error while downloading the log file from the client.")
            return False
        self.log("Log file downloaded from the client.")
        return True

    def wait_for_pc_to_be_online_again(self, timeout=300) -> bool:
        """
        Wait for the pc to be online again, and reconnect to it.
        """
        wait_for_ssh_shutdown(self)

        if not wait_and_reconnect(self, timeout=timeout):
            self.log_error(f"Failed to reconnect to {self.hostname}, timeout likely reached.")
            return False
        return True

    def force_close_ssh_session(self) -> bool:
        """
        Stops the sshd service on the remote computer.
        :return: True if the service was stopped, False otherwise.
        """
        self.log("Stopping sshd service...")
        ssh: paramiko.SSHClient = self.ssh_session

        _, stderr = stdout_err_execute_ssh_command(ssh, "powershell -Command \"Stop-Service sshd\"")
        if stderr:
            self.log_error("Failed to stop sshd service. \nStderr: \n" + stderr)
            return False

        self.log("Sshd service stopped.")
        return True

    def get_project_directory_on_client(self) -> str:
        """
        Get the project directory on the client. It supposes that the project is in the home directory of the client,
        and that the home directory is in "C:\\Users\\" on Windows.
        :return: The string of the project directory on the client.
        """
        return Computer.join_path(self.get_home_directory_on_client(), Infos.PROJECT_NAME)

    def get_home_directory_on_client(self) -> str:
        """
        Get the home directory on the client. It supposes that the home directory is in "C:\\Users\\" on Windows.
        :return: The string of the home directory on the client.
        """
        return "C:\\Users\\" + self.username.split("\\")[1]

    @staticmethod
    def get_list_client_files_to_send() -> list[str]:
        """
        Get the list of the files to send to the client.

        They are all the files in the client folder except some files that are not needed.
        """
        files: list[str] = list_files_recursive(find_directory("client"))
        files = [file for file in files if file.endswith(".py") or file.endswith(".txt") or file.endswith(".ps1")]
        return files

    def get_installer_path(self) -> str:
        """
        Get the path of the python .exe installer on the client.
        """
        installer_path: str = Computer.join_path(self.get_project_directory_on_client(),
                                                 Infos.get_server_python_installer_name())
        return installer_path

    def get_requirements_path(self) -> str:
        """
        Get the path of the requirements file on the client.
        :return:
        """
        requirements_path: str = Computer.join_path(self.get_project_directory_on_client(), "requirements_client.txt")
        return requirements_path

    def get_main_script_path(self) -> str:
        """
        Get the path of the main script on the client.
        :return: The path of the "main_client.py" script on the client.
        """
        return Computer.join_path(self.get_project_directory_on_client(), "main_client.py")

    def get_private_key(self) -> paramiko.PKey | None:
        """
        Get the private key of the computer.
        :return: The private key of the computer.
        """
        if self.private_key_filepath is None:
            self.log_error("Error, the private key filepath is not defined.")
            return None

        if self.__private_key is None:
            self.__private_key = paramiko.Ed25519Key.from_private_key_file(self.private_key_filepath)
        return self.__private_key

    def get_public_key(self):
        """
        Get the public key of the computer.
        :return: The public key of the computer.
        """
        if self.public_key_filepath is None:
            self.log_error("Error, the public key filepath is not defined.")
            return None

        if self.__public_key is None:
            try:
                with open(self.public_key_filepath, "r") as file:
                    self.__public_key = file.read()
            except FileNotFoundError:
                self.log_error("Error, the public key file does not exist.\nIt should have been generated at the setup "
                               "phase.")
        return self.__public_key

    def log_error(self, msg: str, new_lines=0) -> False:
        self.log(level="error", message=msg, new_lines=new_lines)
        return False

    def add_log_memory(self, message: str = "") -> None:
        self.computer_logger.add_log_memory(message=message)

    def log_from_memory(self, level: str = "info") -> None:
        self.computer_logger.log_from_memory(level=level)

    def log(self, message: str, level: str = "info", new_lines: int = 0) -> None:
        self.computer_logger.log(message=message, level=level, new_lines=new_lines)

    def check_informations_integrity(self):
        attributes = {
            'ipv4': "The ipv4 of the computer is not set.",
            'mac_address': "The mac address of the computer is not set.",
            'username': "The username of the computer is not set.",
            'hostname': "The hostname of the computer is not set.",
        }

        error: bool = False
        error_message_list: str = ""
        for attr, error_message in attributes.items():
            if not getattr(self, attr):
                error_message_list += error_message + "\n"
                error = True

        if error:
            raise ValueError(error_message_list)

    def log_add_vertical_space(self, new_lines: int = 1, print_in_console: bool = False):
        self.computer_logger.log_add_vertical_space(new_lines=new_lines, print_in_console=print_in_console)

    def log_raw(self, param):
        """
        Log a raw message.
        """
        self.computer_logger.log_raw(param=param)

    def close_logger(self):
        self.computer_logger.close_logger()

    def remove_keys(self):
        """
        Remove the private and public keys of the computer.
        """
        try:
            os.remove(self.private_key_filepath)
            os.remove(self.public_key_filepath)
        except FileNotFoundError:
            self.log("Could not remove keys, they do not exist.")

    def __str__(self):
        str_repr = f"Computer {self.hostname}:\n"
        str_repr += "\tipv4: " + self.ipv4 + "\n"
        str_repr += "\tmac_address: " + self.mac_address + "\n"
        str_repr += "\tusername: " + self.username + "\n"
        return str_repr

    @staticmethod
    def join_path(*args) -> str:
        """
        Join the paths using Windows-style path separator.

        Computer class should represent a Windows computer, so we need to replace Linux-style path separators with
        Windows-style path separators, and then join the paths using Windows-style path separator.
        """
        # Replace empty components with a backslash
        args = ['\\' if arg == '' else arg for arg in args]
        # Join the paths
        joined_path = os.path.join(*args)
        # Replace Linux-style path separators with Windows-style path separators
        windows_path = joined_path.replace('/', '\\')

        replaced_all_duplicated_backslashes = False
        while not replaced_all_duplicated_backslashes:
            if '\\\\' in windows_path:
                windows_path = windows_path.replace('\\\\', '\\')
            else:
                replaced_all_duplicated_backslashes = True
        return windows_path
