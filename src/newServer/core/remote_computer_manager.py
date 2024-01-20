import hashlib
import logging
import socket
import time

import paramiko

from src.newServer.core.remote_computer import RemoteComputer
from src.newServer.factory.ssh_commands_factory import SSHCommandsFactory
from src.newServer.infrastructure.paths import ServerPath, ClientPath
from src.newServer.security.encryption import Hasher
from src.newServer.wake_on_lan.wake_on_lan_utils import send_wol
from src.newServer.ssh.commands import SSHCommands, SSHCommandResult


class RemoteComputerManager:
    def __init__(self, computer: 'RemoteComputer') -> None:
        self.remote_computer: 'RemoteComputer' = computer
        self.ssh_commands: 'SSHCommands' = SSHCommandsFactory.create(computer.get_ssh_session())
        self.paths: 'ClientPath' = ClientPath(self.get_hostname(), self.get_username())

    def execute_command(self, command: str) -> SSHCommandResult:
        """
        Executes a command on the remote computer.
        :param command: The command to execute.
        :return: True if the command was executed successfully, False otherwise.
        """
        return self.ssh_commands.execute_command(command)

    def is_pc_on(self, port: int = 22, timeout: float = 5.0, print_log_connected: bool = True) -> bool:
        """
        Give true if the pc is on
        :param port: The port to test
        :param timeout: The timeout to test
        :param print_log_connected: If True, the computer will log when it is connected to the socket
        :return: True if the pc can connect to the socket on the computer parameter, False otherwise.
        """
        ip: str = self.remote_computer.get_ipv4()
        start = time.time()
        last_os_error_msg = ""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            while time.time() - start < timeout:
                try:
                    sock.connect((ip, port))
                    if print_log_connected:
                        self.remote_computer.log(f"Connected to {ip} of {self.remote_computer.get_hostname()}"
                                                 f" via sockets")
                    return True
                except socket.timeout:
                    time.sleep(0.1)
                    time_left = timeout - (time.time() - start).__round__(2)

                    if time_left <= 0:
                        self.remote_computer.log("Timeout")
                        break

                    timeout_calc = (timeout - (time.time() - start)).__round__(2)
                    self.remote_computer.log(f"Trying again, timeout left is {timeout_calc}")
                except OSError as e:
                    if last_os_error_msg == e:
                        continue
                    self.remote_computer.log(f"OSError occurred: {e}")
                    last_os_error_msg = e
                except Exception as e:
                    self.remote_computer.log_error(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}")
                    return False

    def wait_for_ssh_shutdown(self) -> None:
        """
        Wait for the SSH server to be down.
        :return: Nothing
        """
        ssh_server_shutdown = False
        self.log("Waiting for SSH server to be down...")
        self.force_close_ssh_session()
        self.close_ssh_session()
        while not ssh_server_shutdown:
            ssh_server_shutdown = not self.is_pc_on(print_log_connected=False)
        self.log("SSH server is down, waiting for it to be up again...")

    def force_close_ssh_session(self):
        """
        Stops the sshd service on the remote computer.
        :return: True if the service was stopped, False otherwise.
        """
        self.log("Stopping sshd service...")

        _, stderr = self.execute_command("powershell -Command \"Stop-Service sshd\"")
        if stderr:
            self.log_error("Failed to stop sshd service. \nStderr: \n" + stderr)
            return False

        self.log("Sshd service stopped.")
        return True

    def wait_and_reconnect(self, timeout: int = 300, retry_interval: int = 10) -> bool:
        """
        Waits for the ssh server to be available and reconnects to it.
        :param timeout: How long to wait for the ssh server to be available.
        :param retry_interval: How long to wait between each attempt to connect to the ssh server.
        :return: A boolean, True if the ssh server is available and the computer is reconnected to it, False otherwise.
        """
        self.ssh_commands.close_ssh_session()

        start_time = time.time()
        connected = False

        original_logging_level = logging.getLogger("paramiko").level
        logging.getLogger("paramiko").setLevel(logging.NOTSET)
        attempts: int = 5

        # Try to connect to the ssh server every retry_interval seconds until timeout is reached
        while time.time() - start_time < timeout and not connected:
            try:
                if not self.is_pc_on(timeout=retry_interval):
                    continue
                success_count = 0
                for _ in range(attempts):  # check connection stability n times
                    self.remote_computer.connect_ssh_procedures()
                    success_count += 1
                    time.sleep(0.2)

                if success_count >= attempts:  # if all n connection attempts succeeded
                    connected = True
                    self.remote_computer.log("Connected to remote computer via SSH.")

                    break
            except (paramiko.ssh_exception.NoValidConnectionsError, paramiko.ssh_exception.SSHException, OSError) as e:
                self.remote_computer.log(f"SSH server is not available yet, trying again in 10 seconds.\nHere is the "
                                         f"exception:\n{e}", "warning")
                time.sleep(retry_interval)
            except Exception as e:
                self.remote_computer.log(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}", "warning")
                time.sleep(retry_interval)

        logging.getLogger("paramiko").setLevel(original_logging_level)
        return connected

    def is_client_file_different(self, remote_file_path: str, local_file_path: str) -> bool:
        """
        Checks if a file on the remote computer is different from a local file.
        :param remote_file_path: The path of the file on the remote computer.
        :param local_file_path: The path of the file on the local computer.
        :return: True if the files are different, False otherwise.
        """
        # Create the sftp session
        sftp = self.ssh_commands.get_sftp()

        try:
            # Get the remote file content
            with sftp.open(remote_file_path, 'rb') as remote_file:
                contenu_distant = remote_file.read()

            # Calculate the cryptographic summary of the remote file
            hachage_distant = hashlib.sha256(contenu_distant).hexdigest()

            # Calculate the cryptographic summary of the local file
            hachage_local = Hasher.sha256(local_file_path)

            # Compare the two summaries
            return hachage_distant == hachage_local

        except FileNotFoundError:
            self.remote_computer.log(f"File not found for this path : {remote_file_path} "
                                     f"The local path that is not checked : {local_file_path}", level="warning")
            # False because the file is not on the remote computer, so it will be sent
            return False
        finally:
            sftp.close()

    def does_path_exists(self, file_path: str) -> bool:
        return self.ssh_commands.does_path_exists(file_path)

    def reboot(self):
        """
        Reboots the remote computer.
        :return: True if the reboot command was sent successfully, False otherwise.
        """
        self.ssh_commands.reboot()

    def shutdown(self) -> None:
        """
        Shuts down the remote computer.
        :return: True if the shutdown command was sent successfully, False otherwise.
        """
        self.ssh_commands.shutdown()

    def create_folder(self, folder_path: str) -> bool:
        """
        Creates a folder on the remote computer.
        :param folder_path: The path of the folder to create.
        :return: True if the folder was created successfully, False otherwise.
        """
        return self.ssh_commands.create_folder(self.remote_computer, folder_path)

    def delete_folder(self, folder_path: str) -> bool:
        """
        Deletes a folder on the remote computer.
        :param folder_path: The path of the folder to delete.
        :return: True if the folder was deleted successfully, False otherwise.
        """
        return self.ssh_commands.delete_folder(self.remote_computer, folder_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes a file on the remote computer.
        :param file_path: The path of the file to delete.
        :return: True if the file was deleted successfully, False otherwise.
        """
        return self.ssh_commands.delete_file(self.remote_computer, file_path)

    def download_file(self, remote_file_path: str, local_file_path: str) -> bool:
        """
        Downloads a file from the remote computer.
        :param remote_file_path: The path of the file to download.
        :param local_file_path: The path where to save the file.
        :return: True if the file was downloaded successfully, False otherwise.
        """
        return self.ssh_commands.download_file(remote_file_path, local_file_path)

    def upload_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        Uploads a file to the remote computer.
        :param local_file_path: The path of the file to upload.
        :param remote_file_path: The path where to save the file.
        :return: True if the file was uploaded successfully, False otherwise.
        """
        return self.ssh_commands.upload_file(local_file_path, remote_file_path)

    def upload_files(self, files: list[str], remote_path: str) -> bool:
        """
        Uploads multiple files to the remote computer.
        :param files: The list of files to upload.
        :param remote_path: The path where to save the files.
        :return: True if the files were uploaded successfully, False otherwise.
        """
        return self.ssh_commands.upload_files(files, remote_path)

    def close_ssh_session(self) -> None:
        """
        Closes the ssh session.
        """
        self.ssh_commands.close_ssh_session()

    def connect_if_awake(self) -> bool:
        if not self.is_pc_on(timeout=20):
            self.log("Waking up the pc...")
            if not self.awake_pc():
                self.log("Could not awake computer...", "warning")
                return False

        self.log_add_vertical_space()
        if not self.remote_computer.connect():
            self.log("Could not connect to computer...", "warning")
            return False
        return True

    def is_os_windows(self, computer: 'RemoteComputer') -> bool:
        return self.ssh_commands.is_os_windows(computer)

    def awake_pc(self):
        """
        Turn on the pc to update windows.
        :return: True if the pc is on, False otherwise.
        """
        send_wol(mac_address=self.get_mac_address(), ip_address=self.get_ipv4())

        if not self.is_pc_on(timeout=20):
            self.log_error("Error, the pc is still off.")
            return False

        self.log("The pc is awake...")
        return True

    def download_log_file_ssh(self) -> bool:
        """
        Download the log file from the client.
        :return: True if the log file has been downloaded, False otherwise.
        """
        if not self.is_pc_on(timeout=20):
            self.log_error("Error, the pc is not connectable, could not download log file.")
            return False

        if not self.connect():
            self.log_error("Could not connect via SSH to the client.")
            return False

        self.log("Downloading log file from the client...")
        local_path: str = ServerPath.get_error_logs_path(self.get_hostname(), self.get_logs_filename())
        remote_file_path: str = ClientPath.join(self.paths.get_project_directory(), "update_windows.log")
        if not self.ssh_commands.download_file(local_path, remote_file_path):
            self.log_error("Error while downloading the log file from the client.")
            return False
        self.log("Log file downloaded from the client.")
        return True

    def get_sftp(self) -> paramiko.SFTPClient:
        return self.ssh_commands.get_sftp()

    def get_private_key_filepath(self):
        return self.remote_computer.get_private_key_filepath()

    def get_public_key_filepath(self):
        return self.remote_computer.get_public_key_filepath()

    def get_hostname(self):
        return self.remote_computer.get_hostname()

    def get_mac_address(self):
        return self.remote_computer.get_mac_address()

    def get_logs_filename(self):
        return self.remote_computer.get_logs_filename()

    def get_ipv4(self):
        return self.remote_computer.get_ipv4()

    def get_username(self):
        return self.remote_computer.get_username()

    def remove_keys(self):
        self.remote_computer.get_ssh_key_manager().remove_keys()

    def log(self, message: str, level: str = "info", new_lines: int = 0):
        self.remote_computer.log(message=message, level=level, new_lines=new_lines)

    def log_error(self, message: str, new_lines: int = 0):
        self.remote_computer.log_error(msg=message, new_lines=new_lines)

    def log_add_vertical_space(self, new_lines: int = 1, print_in_console: bool = False):
        self.remote_computer.log_add_vertical_space(new_lines=new_lines, print_in_console=print_in_console)

    def log_raw(self, message):
        self.remote_computer.get_logger().log_raw(message=message)

    def connect(self):
        return self.remote_computer.connect()

    def get_ssh_session(self):
        return self.remote_computer.get_ssh_session()

    def get_remote_computer(self):
        return self.remote_computer
