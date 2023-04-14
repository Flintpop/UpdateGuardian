import os

import paramiko

from src.server.ssh.ssh_connect import decode_stream


def stdout_err_execute_ssh_command(ssh: paramiko.SSHClient, command: str) -> tuple[str, str] | tuple[None, None] | \
                                                                             tuple[str, None] | tuple[None, str]:
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout = decode_stream(stdout.read())
    stderr = decode_stream(stderr.read())
    return stdout, stderr


def does_path_exists_ssh(ssh: paramiko.SSHClient, file_path: str) -> bool:
    stdin, stdout, stderr = ssh.exec_command(f"if exist {file_path} (echo True) else (echo False)")
    result = decode_stream(stdout.read())
    return True if result == 'True' else False


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
    sftp.put(local_path, os.path.join(remote_path, local_path))
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
