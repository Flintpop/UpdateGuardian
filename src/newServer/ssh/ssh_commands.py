import logging
import os
import hashlib
import socket
import time
from dataclasses import dataclass

import chardet
import paramiko

from typing import TYPE_CHECKING

from src.newServer.Exceptions.DecodingExceptions import DecodingError

if TYPE_CHECKING:
    from src.server.data.computer import Computer


from abc import ABC, abstractmethod


class ISSHCommand(ABC):
    @abstractmethod
    def execute(self, command: str):
        pass


@dataclass
class SSHCommandResult:
    """
    A dataclass containing the stdout and stderr outputs of a command executed on a remote computer.
    """

    def __init__(self, stdout: str, stderr: str):
        self.stdout = ""
        self.stderr = ""


class SSHCommandExecutor(ISSHCommand):
    def __init__(self, ssh: paramiko.SSHClient):
        self.ssh = ssh

    def execute(self, command: str) -> SSHCommandResult:
        """
        Executes a command on the remote computer and returns the stdout and stderr outputs decoded in the correct format.
        :param command: The command to execute
        :return: An object SSHCommandResult containing the stdout and stderr outputs decoded in the correct format.
        """
        _, stdout, stderr = self.ssh.exec_command("cmd /C \"" + command + "\"")
        stdout = SSHCommandExecutor.__decode_stream(stdout.read())
        stderr = SSHCommandExecutor.__decode_stream(stderr.read())
        return SSHCommandResult(stdout, stderr)

    @staticmethod
    def __decode_stream(stream) -> str | None:
        """
        Decode a stream.
        :param stream: The stream used to decode.
        :return: The decoded stream.
        """
        if stream is None or stream == b'':
            return None

        encodings = ['cp850', chardet.detect(stream)['encoding'], 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16', 'utf-32']

        for encoding in encodings:
            try:
                return stream.decode(encoding, errors="replace").strip().replace("\r\n", "\n").replace("\r", "")
            except UnicodeDecodeError:
                pass

        raise DecodingError("None of the tested encodings were able to decode the stream")


class SSHCommands:
    """
    This class contains all the methods that can be used to execute commands on a remote computer.
    """

    def __init__(self, ssh_command_executor: SSHCommandExecutor):
        self.__ssh = ssh_command_executor.ssh
        self.__execute_command: SSHCommandExecutor.execute = SSHCommandExecutor.execute

    def does_path_exists(self, file_path: str) -> bool:
        result = self.__execute_command(f"if exist {file_path} (echo True) else (echo False)")
        return True if result == 'True' else False

    def reboot_remote_pc(self) -> None:
        """
        Reboots the remote computer by executing 'shutdown /r /t 2' on it.
        """
        self.__execute_command("shutdown /r /t 2")

    def shutdown_remote_pc(self) -> None:
        """
        Shuts down the remote computer by executing 'shutdown /s /t 2' on it.
        """
        self.__execute_command("shutdown /s /t 2")

    def create_folder(self, computer: 'Computer', folder_path: str) -> bool:
        """
        Creates a folder on the remote computer.
        :param computer: The computer on which to create the folder.
        :param folder_path: The path of the folder to create ON the remote computer.
        :return: True if the folder was created, False otherwise.
        """
        result: SSHCommandResult = self.__execute_command(f"mkdir {folder_path}")

        if result.stderr and "exist" in result.stderr:
            computer.log(f"Folder {folder_path} already exists")
            return True

        if result.stderr:
            computer.log_error(f"Error while creating the folder {folder_path}: {result.stderr}")
            return False

        if result.stdout:
            computer.log(f"Stdout : {result.stdout}")

        return True

    def delete_folder(self, folder_path: str) -> bool:
        """
        Deletes a folder on the remote computer.
        :param folder_path: The path of the folder to delete ON the remote computer.
        :return: True if the folder was deleted, False otherwise.
        """
        stdout, stderr = self.__execute_command(f"rmdir {folder_path}")

        if stderr:
            print(f"Error while deleting the folder {folder_path}: {stderr}")
            return False

        if stdout:
            print(f"Stdout : {stdout}")

        return True

    def delete_file(self, file_path: str) -> bool:
        stdout, stderr = self.__execute_command(f"del {file_path}")

        if stderr:
            print(f"Error while deleting the file {file_path}: {stderr}")
            return False

        if stdout:
            print(f"Stdout : {stdout}")

        return True

    def download_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        Downloads a file from the remote computer.
        :param local_file_path: The path of the downloaded file ON the local computer.
        :param remote_file_path: The path of the file to download ON the remote computer.
        """
        original_logging_level = logging.getLogger("paramiko").level
        logging.getLogger("paramiko").setLevel(logging.CRITICAL)
        # noinspection PyBroadException
        try:
            sftp = self.__ssh.open_sftp()
            sftp.get(remote_file_path, local_file_path)
            sftp.close()
        except Exception:
            logging.getLogger("paramiko").setLevel(original_logging_level)
            return False
        return True

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Sends a file to the remote computer.
        The file will be sent to the remote_path folder, and will keep its original name.

        :param local_path: The local path of the file to send.
        :param remote_path: The remote path of the folder where the file will be sent.
        :return: True if the file was sent successfully, False otherwise.
        """

        # noinspection PyBroadException
        try:
            sftp = self.__ssh.open_sftp()
            sftp.put(local_path, os.path.join(remote_path, os.path.basename(local_path)))
            sftp.close()
        except Exception:
            return False
        return True

    def upload_files(self, local_paths: list[str], remote_path: str) -> bool:
        """
        Sends multiple files to the remote computer. The files will be sent to the remote_path folder,
         and will keep their original name.
        :param local_paths: List of the files local paths to send.
        :param remote_path: The remote path of the folder where the files will be sent.
        :return: True if the files were sent successfully, False otherwise.
        """
        sftp = self.__ssh.open_sftp()
        for local_path in local_paths:
            sftp.put(local_path, os.path.join(remote_path, os.path.basename(local_path)))
        sftp.close()
        return True


def is_pc_on(computer: 'Computer', port: int = 22, timeout: float = 5.0,
             print_log_connected: bool = True) -> bool:
    """
    Give true if the pc is on
    :param computer: The computer to test
    :param port: The port to test
    :param timeout: The timeout to test
    :param print_log_connected: If True, the computer will log when it is connected to the socket
    :return: True if the pc can connect to the socket on the computer parameter, False otherwise.
    """
    ip: str = computer.ipv4
    start = time.time()
    last_os_error_msg = ""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        while time.time() - start < timeout:
            try:
                sock.connect((ip, port))
                if print_log_connected:
                    computer.log(f"Connected to {ip} of {computer.hostname} via sockets")
                return True
            except socket.timeout:
                time.sleep(0.1)
                time_left = timeout - (time.time() - start).__round__(2)

                if time_left <= 0:
                    computer.log("Timeout")
                    break

                computer.log(f"Trying again, timeout left is {(timeout - (time.time() - start)).__round__(2)}")
            except OSError as e:
                if last_os_error_msg == e:
                    continue
                computer.log(f"OSError occurred: {e}")
                last_os_error_msg = e
            except Exception as e:
                computer.log_error(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}")
                return False


def wait_and_reconnect(computer: 'Computer', timeout: int = 300, retry_interval: int = 10) -> bool:
    """
    Waits for the ssh server to be available and reconnects to it.
    :param computer: The computer to wait and reconnect to.
    :param timeout: How long to wait for the ssh server to be available.
    :param retry_interval: How long to wait between each attempt to connect to the ssh server.
    :return: A boolean, True if the ssh server is available and the computer is reconnected to it, False otherwise.
    """
    ssh: paramiko.SSHClient = computer.ssh_session
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
            if not is_pc_on(computer=computer, timeout=retry_interval):
                continue
            success_count = 0
            for _ in range(attempts):  # check connection stability n times
                computer.connect_ssh_procedures()
                success_count += 1
                time.sleep(0.2)

            if success_count >= attempts:  # if all n connection attempts succeeded
                connected = True
                computer.log("Connected to remote computer via SSH.")

                break
        except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, paramiko.ssh_exception.SSHException,
                OSError) as e:
            computer.log(f"SSH server is not available yet, trying again in 10 seconds.\nHere is the exception:\n{e}",
                         "warning")
            time.sleep(retry_interval)
        except Exception as e:
            computer.log(f"Unknown error occurred: {e}\nTraceback: \n{e.__traceback__}", "warning")
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


def is_client_file_different(computer: 'Computer', remote_file_path: str, local_file_path: str) -> bool:
    """
    Checks if a file on the remote computer is different from a local file.
    :param computer: The computer on which to check the file.
    :param remote_file_path: The path of the file on the remote computer.
    :param local_file_path: The path of the file on the local computer.
    :return: True if the files are different, False otherwise.
    """
    # Create the sftp session
    ssh: paramiko.SSHClient = computer.ssh_session
    sftp = ssh.open_sftp()

    try:
        # Get the remote file content
        with sftp.open(remote_file_path, 'rb') as remote_file:
            contenu_distant = remote_file.read()

        # Calculate the cryptographic summary of the remote file
        hachage_distant = hashlib.sha256(contenu_distant).hexdigest()

        # Calculate the cryptographic summary of the local file
        hachage_local = sha256(local_file_path)

        # Compare the two summaries
        return hachage_distant == hachage_local

    except FileNotFoundError:
        computer.log(f"File not found : {remote_file_path} or {local_file_path}", level="warning")
        # False because the file is not on the remote computer, so it will be sent
        return False
    finally:
        sftp.close()
