import paramiko

from src.server.Exceptions.FilesExceptionsSSH import FileCreationError
from src.server.commands.path_functions import find_file
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import does_path_exists_ssh, create_folder_ssh


def check_python_script_installed(folder_path: str, ssh: paramiko.SSHClient) -> bool:
    """
    Checks if the python script is installed on the remote computer.
    Being implemented
    :return: True if the script is installed, False otherwise.
    """
    import os
    software_path = folder_path

    install_exists: bool = does_path_exists_ssh(ssh, software_path)

    if not install_exists:
        print(f"The {software_path} is not a valid path or does not exists.")
        return install_exists

    main_script_path = os.path.join(software_path, "main.py")
    requirements_path = os.path.join(software_path, "requirements_client.txt")
    install_exists = install_exists and does_path_exists_ssh(ssh, main_script_path)
    if not install_exists:
        print(f"Error, the {main_script_path} does not exits.")
    install_exists = install_exists and does_path_exists_ssh(ssh, requirements_path)
    if not install_exists:
        print(f"Error, the {requirements_path} does not exits.")

    return install_exists


def install_python_script(data: Data, ssh: paramiko.SSHClient, i: int) -> bool:
    """
    Installs the update_windows python script on the remote computer if not already installed.
    This will be used by ssh, and then python to update Windows computers.
    :param data: The data object containing the data of the local network. This is used to get the path of the python
    script.
    :param ssh: The ssh session to the remote computer to install the python script.
    :param i: The index of the computer in the local network data in the json.
    """
    # TODO: Check if all python files exists in the folder client in the project, to prevent a waste of time of the
    #  user.
    import os
    python_script_path: str = data.get_python_script_path(i)
    # TODO: Check if folder exists, if not create it and then check if folder creation was successful. If not, raise
    #  exception.
    created = create_folder_ssh(ssh, python_script_path)

    if not created:
        FileCreationError(f"Error while creating the folder {python_script_path}")

    sftp = ssh.open_sftp()
    print("Opened sftp communication to install the scripts and requirements")

    try:
        files_to_upload: list[str] = ["main.py", "requirements_client.txt", "update_windows.py"]

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
