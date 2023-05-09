import os
import time
import traceback

import paramiko
from cryptography.hazmat.backends.openssl import ed25519

from src.server.commands.install_client_files_and_dependencies import python_scripts, python_installation, \
    python_path, python_packages, wait_for_ssh_shutdown
from src.server.commands.path_functions import list_files_recursive, find_directory, change_directory_to_root_folder
from src.server.config import Infos
from src.server.environnement.server_logs import ComputerLogger
from src.server.ssh.ssh_commands import is_ssh_server_available, stdout_err_execute_ssh_command, wait_and_reconnect
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

    def __init__(self, computer_info: dict) -> None:

        self.no_updates = None
        self.hostname = computer_info.get("hostname")
        self.ipv4 = computer_info.get("ipv4")
        self.mac_address = computer_info.get("mac_address")
        self.username = computer_info.get("username")

        self.__private_key: ed25519.Ed25519PrivateKey | None = None
        self.__public_key: ed25519.Ed25519PublicKey | None = None

        self.private_key_filepath: str = os.path.join(find_directory("ssh_keys"), f"private_key_{self.hostname}")
        self.public_key_filepath: str = os.path.join(find_directory("ssh_keys"), f"public_key_{self.hostname}.pub")

        self.check_informations_integrity()

        self.client_project_folder: str = os.path.join(self.get_project_directory_on_client(), self.username,
                                                       Infos.PROJECT_NAME)

        change_directory_to_root_folder()
        self.logs_filename = "logs"
        self.logs_filename = os.path.join(self.logs_filename,
                                          f"{self.hostname}.log")

        self.computer_logger = ComputerLogger(self.logs_filename)

        self.ssh_session: paramiko.SSHClient | None = None
        self.current_log_message: str = ""

        self.updated_successfully: bool = False

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

            if up is not None:
                self.log("No updates found.")
                self.updated_successfully = True
                self.no_updates = True

            self.no_updates = False
            self.log_add_vertical_space()
            if not self.shutdown():
                return self.log_error("Could not shutdown client.")

            self.updated_successfully = True
            return True
        except Exception as e:
            self.log_add_vertical_space(2)
            self.log_raw("\n" + ComputerLogger.get_header_style_string("ERROR"))
            self.log_error(f"Unhandled error. Could not update computer {self.hostname}: ")
            self.log_add_vertical_space(1)
            trace_back_str: str = traceback.format_exc()
            self.log_error(f"Here is the traceback:\n{trace_back_str}")
            if Infos.email_send:
                send_error_email(computer=self, error=str(e), traceback=trace_back_str)

    def connect(self):
        self.log(message="Connecting to computer...")
        try:
            self.__private_key = self.get_private_key()
            if not self.__private_key:
                self.log_error("Could not get private key... Cannot connect.")
                return False

            self.ssh_session = paramiko.SSHClient()
            self.ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_session.connect(self.hostname, username=self.username, pkey=self.__private_key)
            self.log(f"Connected to computer {self.hostname}.")
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

    def is_pc_awake(self) -> bool:
        if not is_ssh_server_available(computer=self, timeout=5):
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
            if not is_ssh_server_available(computer=self, timeout=3, print_log_connected=False):
                self.log("The pc is off.")
                return True
        return False

    def awake_pc(self):
        """
        Turn on the pc to update windows.
        :return: True if the pc is on, False otherwise.
        """
        send_wol(mac_address=self.mac_address, ip_address=self.ipv4)

        if not is_ssh_server_available(self, timeout=20):
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
        result = self.__start_python_script()
        if result is None or result is False:
            return False, None

        if result.lower() == "reboot":
            self.log("The client needs to reboot, waiting for it to be back online...")
            return self.wait_for_pc_to_be_online_again(), None

        if "no updates found" in result.lower():
            return self.shutdown(), "no up"
        return True, None

    def __start_python_script(self) -> str | bool:
        self.log("Starting the python script...")
        command: str = "cd " + Infos.PROJECT_NAME + " && python " + self.get_main_script_path()

        stdout, stderr = stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log("Python script started.")

        if stderr:
            self.log_error("Error while starting the python script:")
            return False
        if "Traceback" in stdout:
            self.log_error(f"Error while starting the python script:\n\n{stdout}")
            return False
        if stdout:
            self.log(f"Stdout : \n{stdout}")
            return stdout
        self.log_error("Error, the python script returned nothing.")
        return False

    def shutdown(self):
        """
        Shutdown the pc after the update.
        :return: True if the pc is off, False otherwise.
        """
        self.log(level="info", message="Shutting down the pc...")
        command: str = "shutdown /s /t 0"

        stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log(level="info", message="The pc should be off...")
        if not self.waiting_pc_off(timeout=60):
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

    def wait_for_pc_to_be_online_again(self) -> bool:
        wait_for_ssh_shutdown(self.ipv4)

        ssh: paramiko.SSHClient = self.ssh_session
        ipaddress: str = self.ipv4
        remote_user: str = self.username
        remote_private_key: paramiko.pkey = self.__private_key

        if not wait_and_reconnect(ssh, ipaddress, remote_user, remote_private_key):
            self.log_error("Failed to reconnect to remote computer.")
            return False
        return True

    def get_project_directory_on_client(self) -> str:
        """
        Get the project directory on the client. It supposes that the project is in the home directory of the client,
        and that the home directory is in "C:\\Users\\" on Windows.
        :return: The string of the project directory on the client.
        """
        return os.path.join(self.get_home_directory_on_client(), Infos.PROJECT_NAME)

    def get_home_directory_on_client(self) -> str:
        """
        Get the home directory on the client. It supposes that the home directory is in "C:\\Users\\" on Windows.
        :return: The string of the home directory on the client.
        """
        return "C:\\Users\\" + self.username.split("\\")[1]

    @staticmethod
    def get_list_client_files_to_send() -> list[str]:
        files: list[str] = list_files_recursive(find_directory("client"))
        files = [file for file in files if file.endswith(".py") or file.endswith(".txt") or file.endswith(".ps1")]
        return files

    def get_installer_path(self) -> str:
        installer_path: str = os.path.join(self.get_project_directory_on_client(), Infos.get_installer_name())
        return installer_path

    def get_requirements_path(self) -> str:
        """
        Get the path of the requirements file on the client.
        :return:
        """
        requirements_path: str = os.path.join(self.get_project_directory_on_client(), "requirements_client.txt")
        return requirements_path

    def get_main_script_path(self) -> str:
        """
        Get the path of the main script on the client.
        :return: The path of the "main_client.py" script on the client.
        """
        return os.path.join(self.get_project_directory_on_client(), "main_client.py")

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
        self.computer_logger.log_raw(param=param)

    def close_logger(self):
        self.computer_logger.close_logger()

    def remove_keys(self):
        os.remove(self.private_key_filepath)
        os.remove(self.public_key_filepath)

    def __str__(self):
        str_repr = f"Computer {self.hostname}:\n"
        str_repr += "\tipv4: " + self.ipv4 + "\n"
        str_repr += "\tmac_address: " + self.mac_address + "\n"
        str_repr += "\tusername: " + self.username + "\n"
        return str_repr
