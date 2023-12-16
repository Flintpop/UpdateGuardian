import hashlib
import logging
import socket
import time

import paramiko

from src.newServer.core.computer import Computer
from src.newServer.ssh.commands import SSHCommands


class RemoteComputerManager:
    def __init__(self, computer: 'Computer', ssh_commands: 'SSHCommands') -> None:
        self.computer = computer
        self.ssh_commands = ssh_commands

    def is_pc_on(self, port: int = 22, timeout: float = 5.0, print_log_connected: bool = True) -> bool:
        """
        Give true if the pc is on
        :param computer: The computer to test
        :param port: The port to test
        :param timeout: The timeout to test
        :param print_log_connected: If True, the computer will log when it is connected to the socket
        :return: True if the pc can connect to the socket on the computer parameter, False otherwise.
        """
        ip: str = self.computer.ipv4
        start = time.time()
        last_os_error_msg = ""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            while time.time() - start < timeout:
                try:
                    sock.connect((ip, port))
                    if print_log_connected:
                        self.computer.log(f"Connected to {ip} of {self.computer.hostname} via sockets")
                    return True
                except socket.timeout:
                    time.sleep(0.1)
                    time_left = timeout - (time.time() - start).__round__(2)

                    if time_left <= 0:
                        self.computer.log("Timeout")
                        break

                    self.computer.log(f"Trying again, timeout left is {(timeout - (time.time() - start)).__round__(2)}")
                except OSError as e:
                    if last_os_error_msg == e:
                        continue
                    self.computer.log(f"OSError occurred: {e}")
                    last_os_error_msg = e
                except Exception as e:
                    self.computer.log_error(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}")
                    return False

    def wait_and_reconnect(self, timeout: int = 300, retry_interval: int = 10) -> bool:
        """
        Waits for the ssh server to be available and reconnects to it.
        :param timeout: How long to wait for the ssh server to be available.
        :param retry_interval: How long to wait between each attempt to connect to the ssh server.
        :return: A boolean, True if the ssh server is available and the computer is reconnected to it, False otherwise.
        """
        ssh: paramiko.SSHClient = self.computer.ssh_session
        # Close the ssh session to avoid an error
        ssh.close()

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
                    self.computer.connect_ssh_procedures()
                    success_count += 1
                    time.sleep(0.2)

                if success_count >= attempts:  # if all n connection attempts succeeded
                    connected = True
                    self.computer.log("Connected to remote computer via SSH.")

                    break
            except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, paramiko.ssh_exception.SSHException,
                    OSError) as e:
                self.computer.log(f"SSH server is not available yet, trying again in 10 seconds.\nHere is the exception:\n{e}",
                             "warning")
                time.sleep(retry_interval)
            except Exception as e:
                self.computer.log(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}", "warning")
                time.sleep(retry_interval)

        logging.getLogger("paramiko").setLevel(original_logging_level)
        return connected


    def sha256(file: str) -> str:
        """
        Calculates the sha256 hash of a file.
        :param file: The path of the file to hash.
        :return: The sha256 hash of the file.
        """
        hasher = hashlib.sha256()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()


    def is_client_file_different(self, remote_file_path: str, local_file_path: str) -> bool:
        """
        Checks if a file on the remote computer is different from a local file.
        :param computer: The computer on which to check the file.
        :param remote_file_path: The path of the file on the remote computer.
        :param local_file_path: The path of the file on the local computer.
        :return: True if the files are different, False otherwise.
        """
        # Create the sftp session
        ssh: paramiko.SSHClient = self.computer.ssh_session
        sftp = ssh.open_sftp()

        try:
            # Get the remote file content
            with sftp.open(remote_file_path, 'rb') as remote_file:
                contenu_distant = remote_file.read()

            # Calculate the cryptographic summary of the remote file
            hachage_distant = hashlib.sha256(contenu_distant).hexdigest()

            # Calculate the cryptographic summary of the local file
            hachage_local = self.sha256(local_file_path)

            # Compare the two summaries
            return hachage_distant == hachage_local

        except FileNotFoundError:
            self.computer.log(f"File not found : {remote_file_path} or {local_file_path}", level="warning")
            # False because the file is not on the remote computer, so it will be sent
            return False
        finally:
            sftp.close()
