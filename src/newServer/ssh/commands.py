import logging
import os
from dataclasses import dataclass

import chardet
import paramiko

from paramiko.sftp_client import SFTPClient

from newServer.core.remote_computer import RemoteComputer
from src.newServer.exceptions.DecodingExceptions import DecodingError

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
    stdout: str
    stderr: str


class SSHCommandExecutor(ISSHCommand):
    def __init__(self, ssh: paramiko.SSHClient):
        self.ssh = ssh

    def execute(self, command: str) -> SSHCommandResult:
        """
        Executes a command on the remote computer and returns the stdout and stderr outputs decoded in the correct
        format.
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
        :param stream: Stream used to decode.
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
        self.__execute_command: SSHCommandExecutor.execute = ssh_command_executor.execute
        self.__ssh: paramiko.SSHClient = ssh_command_executor.ssh

    def execute_command(self, command: str) -> SSHCommandResult:
        """
        Executes a command on the remote computer and returns the stdout and stderr outputs decoded in the correct
        format.
        :param command: The command to execute
        :return: An object SSHCommandResult containing the stdout and stderr outputs
        decoded in the correct format.
        """
        return self.__execute_command(command)


    def does_path_exists(self, file_path: str) -> bool:
        result = self.__execute_command(f"if exist {file_path} (echo True) else (echo False)")
        return True if result == 'True' else False

    def reboot(self) -> None:
        """
        Reboots the remote computer by executing 'shutdown /r /t 2' on it.
        """
        self.__execute_command("shutdown /r /t 2")

    def shutdown(self) -> None:
        """
        Shuts down the remote computer by executing 'shutdown /s /t 2' on it.
        """
        self.__execute_command("shutdown /s /t 2")

    def create_folder(self, computer: 'RemoteComputer', folder_path: str) -> bool:
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

    def delete_folder(self, computer: 'RemoteComputer', folder_path: str) -> bool:
        """
        Deletes a folder on the remote computer.
        :param computer: The computer on which to delete the folder.
        :param folder_path: The path of the folder to delete ON the remote computer.
        :return: True if the folder was deleted, False otherwise.
        """
        stdout, stderr = self.__execute_command(f"rmdir {folder_path}")

        if stderr:
            computer.log_error(f"Error while deleting the folder {folder_path}: {stderr}")
            return False

        if stdout:
            computer.log(f"Stdout : {stdout}")

        return True

    def delete_file(self, computer: 'RemoteComputer', file_path: str) -> bool:
        stdout, stderr = self.__execute_command(f"del {file_path}")

        if stderr:
            computer.log_error(f"Error while deleting the file {file_path}: {stderr}")
            return False

        if stdout:
            computer.log(f"Stdout : {stdout}")

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
            sftp: SFTPClient = self.__ssh.open_sftp()
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

    def close_ssh_session(self):
        self.__ssh.close()

    def get_sftp(self) -> paramiko.SFTPClient:
        return self.__ssh.open_sftp()

    def is_os_windows(self, computer: 'RemoteComputer') -> bool:
        # Try to get OS information using 'uname' command (usually works on Unix-like systems)
        res: SSHCommandResult = self.__execute_command("uname -a")
        os_info = res.stdout

        if not os_info:
            # If 'uname' command doesn't work, try to get OS information using 'ver' command
            # (usually works on Windows systems)
            res = self.__execute_command("ver")
            os_info = res.stdout

        if not os_info:
            computer.log("Failed to get OS information.", level="warning")
            return True
        if "windows" in os_info.lower():
            return True

        return False
