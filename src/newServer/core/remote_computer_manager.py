import hashlib
import logging
import socket
import time

import paramiko

from newServer.core.remote_computer import RemoteComputer
from newServer.factory.ssh_commands_factory import SSHCommandsFactory
from newServer.security.encryption import Hasher
from src.newServer.ssh.commands import SSHCommands


class RemoteComputerManager:
    def __init__(self, computer: 'RemoteComputer') -> None:
        self.remote_computer: 'RemoteComputer' = computer
        self.ssh_commands: 'SSHCommands' = SSHCommandsFactory.create(computer.get_ssh_session())

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

    def get_sftp(self) -> paramiko.SFTPClient:
        return self.ssh_commands.get_sftp()
