import os
import socket
import time

import paramiko

from src.server.ssh.ssh_connect import decode_stream


def stdout_err_execute_ssh_command(ssh: paramiko.SSHClient, command: str) -> tuple[str, str] | tuple[None, None] | \
                                                                             tuple[str, None] | tuple[None, str]:
    """
    Executes a command on the remote computer and returns the stdout and stderr outputs decoded in the correct format.
    :param ssh: SSH Session.
    :param command: The command to execute
    :return: First stdout, then stderr. If there is no output, None is returned.
    """
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout = decode_stream(stdout.read())
    stderr = decode_stream(stderr.read())
    return stdout, stderr


def does_path_exists_ssh(ssh: paramiko.SSHClient, file_path: str) -> bool:
    stdin, stdout, stderr = ssh.exec_command(f"if exist {file_path} (echo True) else (echo False)")
    result = decode_stream(stdout.read())
    return True if result == 'True' else False


def reboot_remote_pc(ssh: paramiko.SSHClient) -> None:
    reboot_command = 'shutdown /r /t 0'
    ssh.exec_command(reboot_command)


def is_ssh_server_available(ip: str, port: int = 22, timeout: float = 5.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
            return True
        except (socket.timeout, OSError):
            return False


def wait_and_reconnect(ssh: paramiko.SSHClient, ip: str, username: str, password: str, timeout: int = 600,
                       retry_interval: int = 10) -> bool:
    ssh.close()
    start_time = time.time()
    connected = False

    while not connected and time.time() - start_time < timeout:
        try:
            ssh.connect(ip, username=username, password=password, timeout=timeout)
            connected = True
        except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout):
            time.sleep(retry_interval)

    return connected


def create_folder_ssh(ssh: paramiko.SSHClient, folder_path: str) -> bool:
    stdout, stderr = stdout_err_execute_ssh_command(ssh, f"mkdir {folder_path}")

    if stderr:
        if "exist" in stderr:
            print(f"Folder {folder_path} already exists")
            return False
        print(f"Error while creating the folder {folder_path}: {stderr}")
        return False

    if stdout:
        print(f"Stdout : {stdout}")

    return True


def delete_folder_ssh(ssh: paramiko.SSHClient, folder_path: str) -> bool:
    stdout, stderr = stdout_err_execute_ssh_command(ssh, f"rmdir {folder_path}")

    if stderr:
        print(f"Error while deleting the folder {folder_path}: {stderr}")
        return False

    if stdout:
        print(f"Stdout : {stdout}")

    return True


def delete_file_ssh(ssh: paramiko.SSHClient, file_path: str) -> bool:
    stdout, stderr = stdout_err_execute_ssh_command(ssh, f"del {file_path}")

    if stderr:
        print(f"Error while deleting the file {file_path}: {stderr}")
        return False

    if stdout:
        print(f"Stdout : {stdout}")

    return True


def send_file_ssh(ssh: paramiko.SSHClient, local_path: str, remote_path: str) -> bool:
    sftp = ssh.open_sftp()
    sftp.put(local_path, os.path.join(remote_path, os.path.basename(local_path)))
    sftp.close()
    return True


def send_files_ssh(ssh: paramiko.SSHClient, local_paths: list[str], remote_path: str) -> bool:
    """
    Sends multiple files to the remote computer. The files will be sent to the remote_path folder, and will keep their
    original name.
    :param ssh: SSH session to the remote computer.
    :param local_paths: List of the local paths of the files to send.
    :param remote_path: The remote path of the folder where the files will be sent.
    :return: True if the files were sent successfully, False otherwise.
    """
    sftp = ssh.open_sftp()
    for local_path in local_paths:
        sftp.put(local_path, os.path.join(remote_path, os.path.basename(local_path)))
    sftp.close()
    return True


def manage_stdout_stderr_output(stdout: str, stderr: str) -> bool:
    if stderr:
        print(f"Error : {stderr}")
        return False

    if stdout:
        print(f"Stdout : {stdout}")

    return True
