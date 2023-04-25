import paramiko

from src.server.Exceptions.FilesExceptionsSSH import FileCreationError
from src.server.commands.path_functions import find_file, list_files_recursive, find_directory

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.ssh.ssh_commands import does_path_exists_ssh, create_folder_ssh


def check_file_exists(computer: 'Computer', file_path: str) -> bool:
    """
    Checks if the file exists on the remote computer.
    :param computer: The computer to check on if the file exists.
    :param file_path: The path of the file to check.
    :return: True if the file exists, False otherwise.
    """
    ssh: paramiko.SSHClient = computer.ssh_session
    file_exists: bool = does_path_exists_ssh(ssh, file_path)

    if not file_exists:
        computer.log_error(f"The file path : '{file_path}' is not a valid path or does not exists.")

    return file_exists


def check_all_files_exists(computer: 'Computer') -> bool:
    """
    Checks if all the installation files exists on the remote computer.
    It compares all .py and .txt files in the client folder, with the files on the remote computer
    in the %USERPROFILE%/Infos.project_name folder
    :param computer: The computer to check on if the files exists.
    :return: True if all the files exists, False otherwise.
    """
    import os
    files: list[str] = [file for file in list_files_recursive(find_directory("client")) if file.endswith(".py")
                        or file.endswith(".txt")]
    files = [os.path.basename(file) for file in files]
    files = [os.path.join(computer.get_project_directory_on_client(), file) for file in files]

    for file in files:
        if not check_file_exists(computer, file):
            return False
    return True


def check_python_script_installed(computer: 'Computer') -> bool:
    """
    Checks if the python script is installed on the remote computer.
    :return: True if the script is installed, False otherwise.
    """
    ssh: paramiko.SSHClient = computer.ssh_session
    client_folder_path: str = computer.get_project_directory_on_client()
    install_exists: bool = does_path_exists_ssh(ssh, client_folder_path)

    if not install_exists:
        computer.log("There is not installation of the python script on the remote computer, because the folder is "
                     "not here.")
        return install_exists

    return check_all_files_exists(computer=computer)


def install_python_script(computer: 'Computer') -> bool:
    """
    Installs the update_windows python script on the remote computer. Overwrites the files if they already exist.
    :param computer: The computer to install the script on\n
    :return True if the upload was successful, False otherwise
    """
    import os

    ssh: paramiko.SSHClient = computer.ssh_session
    python_script_path: str = computer.get_project_directory_on_client()

    created = create_folder_ssh(ssh, python_script_path)

    if not created:
        computer.log_error(f"Error while creating the folder {python_script_path}")
        FileCreationError(f"Error while creating the folder {python_script_path}")

    sftp = ssh.open_sftp()
    computer.log("Opened sftp communication to install the scripts and requirements")

    # TODO : Simplifier le code pour avoir les fichiers à upload
    files_to_upload: list[str] = [os.path.basename(file) for file in list_files_recursive(find_directory("client"))
                                  if not file.endswith(".log")]
    try:

        for file in files_to_upload:
            file_path = find_file(file)
            sftp.put(file_path, os.path.join(python_script_path, file))
            computer.log(f"File {file} uploaded to {python_script_path}")
    except (FileNotFoundError, FileExistsError, IOError):
        computer.log_error(f"Error while uploading the files {files_to_upload} to the remote computer.")
        return False

    sftp.close()
    return True


if __name__ == '__main__':
    import os
