import traceback

import paramiko

from newServer.core.computer import Computer
from newServer.logs_management.computer_logger import ComputerLogger
from newServer.ssh.connect import SSHConnect
from newServer.ssh.ssh_key_manager import SSHKeyManager


class RemoteComputer:
    def __init__(self, computer: 'Computer', init_logger: bool = True):
        self.__computer = computer
        self.logs_filename = f"{computer.hostname}.log"
        self.computer_logger = None
        self.ssh_key_manager = SSHKeyManager(computer, self.log_error)
        self.ssh_session: paramiko.SSHClient | None = None

        if init_logger:
            self.computer_logger = ComputerLogger(self.logs_filename)

    def log(self, message: str, level: str = "info", new_lines: int = 0) -> None:
        self.computer_logger.log(message=message, level=level, new_lines=new_lines)

    def log_error(self, msg: str, new_lines=0) -> False:
        self.log(level="error", message=msg, new_lines=new_lines)
        return False

    def get_ipv4(self):
        return self.__computer.ipv4

    def get_hostname(self):
        return self.__computer.hostname

    def connect(self):
        self.log(message=f"Connecting to {self.get_hostname()} computer via SSH...")
        try:
            if not self.connect_ssh_procedures():
                return False

            self.log(f"Connected via SSH to computer {self.get_hostname()}.")
            return True
        except paramiko.AuthenticationException as e:
            self.log_add_vertical_space()
            self.log_error("Authentication failed: " + str(e))
            self.log_error(f"Please, check your username and password for the computer {self.get_hostname()}.")
            self.log_error("The connection password may be the os connection password if there are no "
                           "microsoft accounts linked.\nOtherwise, it is the account password.")
            self.log_error("Furthermore, if there are several accounts to the computer that a user can connect to,"
                           f"make sure the username {self.get_username()} is something as follows: "
                           f"\n'pc-name\\username@ip' " "(or 'pc-name\\username@hostname').")
            self.log_add_vertical_space()
            self.log_error(f"Here are some informations about the connection settings:"
                           f"\n\tip: {self.get_ipv4()}"
                           f"\n\tmac: {self.get_mac_address()}"
                           f"\n\tusername: {self.get_username()}")
            return False
        except Exception as e:
            self.log_error(f"Unhandled error. Could not connect to {self.get_hostname()}:\n " + str(e))
            self.log_error(f"Here is the traceback: \n{traceback.format_exc()}\n")
            return False

    def connect_ssh_procedures(self) -> bool:
        private_key = self.ssh_key_manager.get_private_key()
        if not private_key:
            self.log_error("Could not get the private key.")
            return False
        self.ssh_session: paramiko.SSHClient = SSHConnect.private_key_connexion(self.__computer, private_key)
        return True

    def get_ssh_session(self) -> paramiko.SSHClient:
        return self.ssh_session

    def log_add_vertical_space(self, new_lines: int = 1, print_in_console: bool = False):
        self.computer_logger.log_add_vertical_space(new_lines=new_lines, print_in_console=print_in_console)

    def get_username(self):
        return self.__computer.username

    def get_mac_address(self):
        return self.__computer.mac_address
