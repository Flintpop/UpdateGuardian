import paramiko

from src.server.Exceptions.FilesExceptionsSSH import FileCreationError
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import does_path_exists_ssh, create_folder_ssh


def check_python_script_installed(folder_path: str, ssh: paramiko.SSHClient) -> bool:
    """
    Checks if the python script is installed on the remote computer.
    Being implemented
    :return: True if the script is installed, False otherwise.
    """
    software_name: str = "UpdateGuardian"
    software_path = os.path.join(folder_path, software_name)

    install_exists: bool = does_path_exists_ssh(ssh, software_path)

    if not install_exists:
        print(f"Error, the {software_path} is not a valid path or does not lead to the correct directory")
        return install_exists

    main_script_path = os.path.join(software_path, "main.py")
    requirements_path = os.path.join(software_path, "requirements.txt")
    install_exists = install_exists and does_path_exists_ssh(ssh, main_script_path)
    if not install_exists:
        print(f"Error, the {main_script_path} does not exits.")
    install_exists = install_exists and does_path_exists_ssh(ssh, requirements_path)
    if not install_exists:
        print(f"Error, the {requirements_path} does not exits.")

    return install_exists


def install_python_script(data: Data, ssh: paramiko.SSHClient) -> None:
    """
    Installs the update_windows python script on the remote computer if not already installed.
    This will be used by ssh, and then python to update Windows computers.
    :param data: The data object containing the data of the local network. This is used to get the path of the python
    script.
    :param ssh: The ssh session to the remote computer to install the python script.
    """
    # TODO: Check if all python files exists in the folder client in the project, to prevent a waste of time of the
    #  user.
    python_script_path: str = data.get_python_script_path()
    fail = create_folder_ssh(ssh, python_script_path)

    if fail:
        FileCreationError(f"Error while creating the folder {python_script_path}")

    sftp = ssh.open_sftp()
    print("Opened sftp communication to install the scripts and requirements")

    current_script_path = os.path.abspath(__file__)
    current_folder_script_path = os.path.dirname(current_script_path)

    files_to_upload: list[str] = ["main.py", "requirements.txt", "update_windows.py"]
    client_folder_path = os.path.join(current_folder_script_path, '..', '..', 'client')

    for file in files_to_upload:
        file_path = os.path.join(client_folder_path, file)
        file_path = os.path.abspath(file_path)
        sftp.put(file_path, os.path.join(python_script_path, file))

    sftp.close()


if __name__ == '__main__':
    import os
