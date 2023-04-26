import logging
import os
import traceback

import paramiko

from src.server.commands.install_client_files_and_dependencies import python_scripts, python_installation, \
    python_path, python_packages, wait_for_ssh_shutdown
from src.server.commands.path_functions import list_files_recursive, find_directory, change_directory_to_root_folder
from src.server.config import Infos
from src.server.ssh.ssh_commands import is_ssh_server_available, stdout_err_execute_ssh_command, manage_ssh_output, \
    wait_and_reconnect
from src.server.wake_on_lan.wake_on_lan_utils import send_wol


class Computer:
    """
    A class used to represent a computer in the local network.
    It contains : \n
    - hostname\n
    - ipv4\n
    - mac_address\n
    - username\n
    - password\n
    - logger (logging.Logger, used to log the computer's activity in a file)\n

    Methods
    -------
    setup_logger()
        Sets up the logger for the computer.
    log(level: str, message: str)
        Logs a message in the computer's log file.
    close_logger()
        Closes the logger for the computer.
    """
    _id_counter = 0

    def __init__(self, computer_info: dict, hostname: str) -> None:
        Computer._id_counter += 1
        self.id = Computer._id_counter

        self.hostname = hostname
        self.ipv4 = computer_info.get("ip")
        self.mac_address = computer_info.get("mac")
        self.username = computer_info.get("username")
        self.password = computer_info.get("password")

        self.check_informations_integrity()

        self.client_project_folder: str = os.path.join(self.get_project_directory_on_client(), self.username,
                                                       Infos.PROJECT_NAME)

        change_directory_to_root_folder()
        self.logs_filename = "logs"
        self.logs_filename = os.path.join(self.logs_filename,
                                          f"{self.hostname}-{Computer._id_counter}.log")

        self.computer_logger = ComputerLogger(self.logs_filename)

        self.ssh_session: paramiko.SSHClient | None = None
        self.current_log_message: str = ""

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
            if not self.install_update():
                return self.log_error("Could not install update on client.")

            self.log_add_vertical_space()
            if not self.shutdown():
                return self.log_error("Could not shutdown client.")

            return True
        except Exception:
            self.log_add_vertical_space(2)
            self.log_raw("\n" + ComputerLogger.get_header_style_string("ERROR"))
            self.log_error(f"Unhandled error. Could not update computer {self.hostname}: ")
            self.log_add_vertical_space(1)
            trace_back_str: str = traceback.format_exc()
            self.log_error(f"Here is the traceback:\n{trace_back_str}")
            # string: str = "Unhandled error. Could not update computer " + self.hostname
            # string += f"\nHere is the traceback:\n{e}"
            # send_mail("Unhandled error. Could not update computer " + self.hostname, string)

    def connect(self):
        self.log(message="Connecting to computer...")
        try:
            self.ssh_session = paramiko.SSHClient()
            self.ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_session.connect(self.ipv4, username=self.username, password=self.password)
            self.log(f"Connected to computer {self.hostname}.")
            return True
        except paramiko.AuthenticationException as e:
            self.log_error("Authentication failed: " + str(e))
            self.log_error(f"Please, check your username and password for the computer {self.hostname}.")
            return False
        except Exception as e:
            self.log_error(f"Unhandled error. Could not connect to {self.hostname}: " + str(e))
            return False

    def is_pc_awake(self) -> bool:
        if not is_ssh_server_available(computer=self, timeout=180):
            self.log("The pc is off.")
            return False
        self.log("The pc is on.")
        return True

    def awake_pc(self):
        """
        Turn on the pc to update windows.
        :return: True if the pc is on, False otherwise.
        """
        self.log("Waking up the pc...")

        send_wol(mac_address=self.mac_address, ip_address=self.ipv4)

        if not is_ssh_server_available(self, timeout=180):
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

    def install_update(self) -> bool:
        self.log("Installing update on the client...")
        result = self.__start_python_script()
        if result is None:
            return False

        if result.lower() == "reboot":
            self.log("The client needs to reboot, waiting for it to be back online...")
            return self.wait_for_pc_to_be_online_again()
        return True

    def __start_python_script(self):
        self.log("Starting the python script...")
        command: str = "cd " + Infos.PROJECT_NAME + " && python " + self.get_main_script_path()

        stdout, stderr = stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log("Python script started.")

        return manage_ssh_output(stderr, stdout)

    def shutdown(self):
        """
        Shutdown the pc after the update.
        :return: True if the pc is off, False otherwise.
        """
        self.log(level="info", message="Shutting down the pc...")
        command: str = "shutdown /s /t 0"

        stdout, stderr = stdout_err_execute_ssh_command(self.ssh_session, command)

        self.log(level="info", message="The pc should be off...")
        if manage_ssh_output(stdout, stderr) is None:
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
        remote_password: str = self.password

        if not wait_and_reconnect(ssh, ipaddress, remote_user, remote_password):
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
        return "C:\\Users\\" + self.username

    @staticmethod
    def get_list_client_files_to_send() -> list[str]:
        files: list[str] = list_files_recursive(find_directory("client"))
        files = [file for file in files if file.endswith(".py") or file.endswith(".txt")]
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
            'password': "The password of the computer is not set.",
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

    def __str__(self):
        str_repr = f"Computer {self.hostname}:\n"
        str_repr += "\tipv4: " + self.ipv4 + "\n"
        str_repr += "\tmac_address: " + self.mac_address + "\n"
        str_repr += "\tusername: " + self.username + "\n"
        str_repr += "\tpassword: " + self.password + "\n"
        return str_repr

    def log_add_vertical_space(self, new_lines: int = 1):
        self.computer_logger.log_add_vertical_space(new_lines=new_lines)

    def log_raw(self, param):
        self.computer_logger.log_raw(param=param)


class ComputerLogger:
    def __init__(self, logs_filename: str, new_msg_header: str = "New computer session"):
        self.logs_filename = logs_filename
        self.logger = self.setup_logger(new_msg_header=new_msg_header)
        self.current_log_message: str = ""

    def setup_logger(self, new_msg_header: str) -> logging.Logger:
        logger = logging.getLogger(self.logs_filename)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            file_handler = logging.FileHandler(filename=self.logs_filename, encoding="utf-8")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.setup_log_file(new_msg_header=new_msg_header)

        return logger

    def log(self, message: str, level: str = "info", new_lines: int = 0) -> None:
        message = "\n" * new_lines + message
        if level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.logger.error(message)
        elif level.lower() == "critical":
            self.logger.critical(message)
        else:
            self.logger.debug(message)

    def close_logger(self) -> None:
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def add_log_memory(self, message: str = "") -> None:
        self.current_log_message += message + "\n"

    def log_from_memory(self, level: str = "info") -> None:
        self.log(message=self.current_log_message, level=level)
        self.current_log_message = ""

    @staticmethod
    def get_header_style_string(header_txt: str) -> str:
        width = len(header_txt) * 4
        edge = "═" * width
        padding = " " * 3  # Add 3 spaces for padding

        header = f"╔{edge}╗\n║{padding}{header_txt.center(width - 6)}{padding}║\n╚{edge}╝"
        return header

    def setup_log_file(self, new_msg_header: str) -> None:
        write_lines: bool = False
        with open(self.logs_filename, "r", encoding="utf-8") as f:
            if len(f.read()) > 1:
                write_lines = True

        if write_lines:
            with open(self.logs_filename, "a", encoding="utf-8") as f:
                f.write("\n\n")

        # Write the header
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            f.write(self.get_header_style_string(header_txt=new_msg_header) + "\n")

    def log_add_vertical_space(self, new_lines: int = 1):
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            new_lines: str = "\n" * new_lines
            f.write(new_lines)

        print(new_lines.split("\n").pop(0))

    def log_raw(self, param):
        """
        Log a raw object, without the formatter.
        :param param: The object to log.
        :return: Nothing.
        """
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            f.write(str(param) + "\n")
