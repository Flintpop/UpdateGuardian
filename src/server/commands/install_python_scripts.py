import paramiko

from src.server.Exceptions.FilesExceptionsSSH import FileCreationError
from src.server.commands.path_functions import find_file, list_files_recursive, find_directory
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import does_path_exists_ssh, create_folder_ssh


def check_file_exists(ssh: paramiko.SSHClient, file_path: str) -> bool:
    """
    Checks if the file exists on the remote computer.
    :param ssh: The ssh session to the remote computer.
    :param file_path: The path of the file to check.
    :return: True if the file exists, False otherwise.
    """
    file_exists: bool = does_path_exists_ssh(ssh, file_path)

    if not file_exists:
        print(f"The file path : '{file_path}' is not a valid path or does not exists.")

    return file_exists


def check_all_files_exists(ssh: paramiko.SSHClient):
    files: list[str] = [file for file in list_files_recursive(find_directory("client")) if file.endswith(".py")
                        or file.endswith(".txt")]

    for file in files:
        if not check_file_exists(ssh, file):
            return False
    return True


def check_python_script_installed(client_folder_path: str, ssh: paramiko.SSHClient) -> bool:
    """
    Checks if the python script is installed on the remote computer.
    :return: True if the script is installed, False otherwise.
    """
    install_exists: bool = does_path_exists_ssh(ssh, client_folder_path)

    if not install_exists:
        print(f"The client folder path : '{client_folder_path}' is not a valid path or does not exists.")
        return install_exists

    return check_all_files_exists(ssh)


def install_python_script(data: Data, ssh: paramiko.SSHClient, i: int) -> bool:
    """
    Installs the update_windows python script on the remote computer if not already installed.
    This will be used by ssh, and then python to update Windows computers.
    :param data: The data object containing the data of the local network. This is used to get the path of the python
    script.
    :param ssh: The ssh session to the remote computer to install the python script.
    :param i: The index of the computer in the local network data in the json.
    """
    import os

    python_script_path: str = data.get_python_script_path(i)

    created = create_folder_ssh(ssh, python_script_path)

    if not created:
        FileCreationError(f"Error while creating the folder {python_script_path}")

    sftp = ssh.open_sftp()
    print("Opened sftp communication to install the scripts and requirements")

    try:
        files_to_upload: list[str] = [os.path.basename(file) for file in list_files_recursive(find_directory("client"))]

        for file in files_to_upload:
            file_path = find_file(file)
            sftp.put(file_path, os.path.join(python_script_path, file))
    except (FileNotFoundError, FileExistsError, IOError):
        print("Error while uploading the files to the remote computer.")
        return False

    sftp.close()
    return True


if __name__ == '__main__':
    import os
