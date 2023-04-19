import os

import paramiko

from src.server.commands.install_python_scripts import check_python_script_installed, install_python_script
from src.server.commands.path_functions import find_file, list_files_recursive, find_directory
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import stdout_err_execute_ssh_command, send_file_ssh, does_path_exists_ssh, \
    reboot_remote_pc, wait_and_reconnect, is_ssh_server_available, is_client_file_different

STDOUT_MESSAGE = "STDOUT: \n"


def check_python_installed(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    python_executables = ("python.exe", "python3.exe", "python311.exe")

    folder_path = "C:\\Users\\" + data.get_data_json().get("remote_user")[i]
    folder_path += "\\AppData\\Local\\Programs\\"
    programs_path: bool = does_path_exists_ssh(ssh, folder_path)

    if not programs_path:
        print("Programs folder does not exists")
        return False

    print("Programs folder exists")
    folder_path += Data.python_folder_name

    if not does_path_exists_ssh(ssh, folder_path):
        print("Python folder does not exists")
        return False

    print("Python folder exists")
    for executable in python_executables:
        executable_path = os.path.join(folder_path, executable)
        if does_path_exists_ssh(ssh, executable_path):
            print(f"Python executable {executable} exists")
            return True

    print("Failed to find python executable.")
    return False


def check_python_in_path(ssh) -> bool:
    print("Checking if python is path again...")

    # Check if 'python' command is available
    stdout, stderr = stdout_err_execute_ssh_command(ssh, "where python")

    if not stderr and "python" in stdout:
        print("Python is path.")
        return True
    else:
        print("Python is not installed.")
        return False


def check_python_packages_installed(ssh: paramiko.SSHClient, requirements_file_path: str) -> bool:
    """
    Checks if all the packages in the requirements_client.txt file are installed for the client.
    :param ssh: SSH client session
    :param requirements_file_path: Path to the requirements_client.txt file but in the server computer.
    :return:
    """
    print("Checking if requirements_client.txt packages are installed...")

    with open(requirements_file_path, 'r') as file:
        requirements = file.readlines()

    # Remove newlines and spaces
    requirements = [req.strip() for req in requirements if req.strip()]

    all_installed = True

    for req in requirements:
        # Check if the package is installed using 'pip show'
        stdout, stderr = stdout_err_execute_ssh_command(ssh, f"pip show {req}")

        if not stderr and req in stdout:
            print(f"{req} is installed")
        else:
            print(f"{req} is not installed")
            all_installed = False

    return all_installed


def check_file_exists(installer_path: str) -> bool:
    res: bool = os.path.isfile(installer_path)
    return res


def send_python_installer(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    print("Sending python installer...")

    installer_path: str = Data.get_server_python_installer_path()
    does_file_exists: bool = check_file_exists(installer_path)
    if not does_file_exists:
        print("Error, the python installer does not exist on the server. Please check the path, or if it exists.")
        return False
    send_file_ssh(ssh, installer_path, data.get_python_script_path(i))
    print("Python installer sent.")
    return True


def add_python_to_path(ssh: paramiko.SSHClient) -> bool:
    print("Adding python to path...")

    # Get the current PATH from the registry
    get_path_command = 'reg query "HKCU\\Environment" /v Path'
    stdout, stderr = stdout_err_execute_ssh_command(ssh, get_path_command)

    if "REG_SZ" in stdout:
        current_path = stdout.split("REG_SZ")[-1].strip()
    else:
        current_path = ""

    # Get the current USERPROFILE
    stdout, stderr = stdout_err_execute_ssh_command(ssh, 'echo %USERPROFILE%')
    user_profile = stdout.strip()

    # Construct the new PATH
    python_path_var = f'{user_profile}\\AppData\\Local\\Programs\\{Data.python_folder_name}'
    scripts_path = f'{python_path_var}\\Scripts'
    if current_path:
        if current_path[-1] == ';':
            current_path = current_path[:-1]
        new_path = f'{current_path};{python_path_var};{scripts_path}'
    else:
        new_path = f'{python_path_var};{scripts_path}'

    # Set the new PATH using reg command
    path_add_command = f'reg add "HKCU\\Environment" /v Path /t REG_SZ /d "{new_path}" /f'
    stdout, stderr = stdout_err_execute_ssh_command(ssh, path_add_command)

    if stderr is not None and (stderr and not stdout or "error" in stderr.lower()):
        print("Error, could not add python to path : " + stderr)
        return False
    if stdout:
        print(STDOUT_MESSAGE + stdout)
    return True


def check_python_path_set(ssh) -> bool:
    print("Checking if python is in path...")

    path_check_command: str = r'echo %PATH%'

    stdout, stderr = stdout_err_execute_ssh_command(ssh, path_check_command)

    if stderr:
        print("Error, path command failed : " + stderr)
        return False

    if "python" not in stdout.lower():
        print("Python is not in path")
        return False

    print("Python seems to be in path. Checking if python executable is launchable...")

    # Check if 'python' command is available
    stdout2, stderr2 = stdout_err_execute_ssh_command(ssh, "where python")

    if not stderr2 and "python" in stdout2.lower():
        print("Python is installed and in path")
        print("Checking pip...")
        stdout3, stderr3 = stdout_err_execute_ssh_command(ssh, "pip --version")
        if stdout3:
            print("Pip is installed")
            return True
        print("Error, pip is not installed : " + stderr3)
        return False
    else:
        print("Python is not set correctly in path, because it may be there despite the fact that it is installed.")
        return False


def python_installer_exists(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    return does_path_exists_ssh(ssh, os.path.join(data.get_python_script_path(i), Data.get_installer_name()))


def install_python_installer(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    print("\nChecking if python installer exists on client computer...")
    does_python_installer_exists: bool = python_installer_exists(ssh, data, i)
    if does_python_installer_exists:
        print("Python installer exists, not sending it.")
    if not does_python_installer_exists:
        print("Python installer does not exist, sending it to client computer...")
        python_installer_sent = send_python_installer(ssh, data, i)
        if not python_installer_sent:
            print("Error, could not send python installer.")
            return False
    return True


def install_python(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    python_installer_installed: bool = install_python_installer(ssh, data, i)
    if not python_installer_installed:
        return False

    print("\nInstalling Python...")

    # Get the path to the python script that will install python
    path_update_guardian: str = data.get_python_script_path(i)
    python_installer_filename: str = os.path.basename(Data.get_server_python_installer_path())
    parameters: str = "/quiet InstallAllUsers=0 TargetDir=%USERPROFILE%\\AppData\\Local\\Programs\\" + \
                      Data.python_folder_name + " " r"Include_launcher=0 Include_test=0 Include_dev=0 Include_doc=0 " \
                                                r"Include_pip=1"
    command: str = os.path.join(path_update_guardian, python_installer_filename) + " " + parameters

    stdout, stderr = stdout_err_execute_ssh_command(ssh, command)

    if stderr:
        print("Error, could not install python : " + stderr)
        print("command : " + command)
        print("Python update guardian variable : " + path_update_guardian)
        return False

    if stdout:
        print(STDOUT_MESSAGE + stdout)

    print("Python installed.")

    return True


def install_python_packages(ssh: paramiko.SSHClient, requirements_file_path: str) -> bool:
    command: str = "pip install -r " + requirements_file_path
    stdout, stderr = stdout_err_execute_ssh_command(ssh, command)

    if stderr and "error" in stderr.lower() or "erreur" in stderr.lower():
        print("Error, could not install python packages : " + stderr)
        return False
    if stderr and "warning" in stderr.lower():
        print("Warning, but python packages installed")
        if "pip" in stderr.lower():
            print("Pip should be updated.")
        else:
            print("Stderr : " + stderr)
    if stdout:
        print(STDOUT_MESSAGE + stdout)
    return True


def wait_for_ssh_shutdown(ipaddress: str) -> None:
    ssh_server_shutdown = False
    print("Waiting for SSH server to be down...")
    while not ssh_server_shutdown:
        ssh_server_shutdown = not is_ssh_server_available(ipaddress)
    print("SSH server is down, waiting for it to be up again...")


def refresh_env_variables(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    print("Rebooting remote computer...")
    reboot_remote_pc(ssh)
    ipaddress, remote_user, remote_password = data.get_client_info(i)
    wait_for_ssh_shutdown(ipaddress)

    if not wait_and_reconnect(ssh, ipaddress, remote_user, remote_password):
        print("Failed to reconnect to remote computer.")
        return False

    if not check_python_in_path(ssh):
        print("Failed to add python to path.")
        return False

    return True


def check_python_script_up_to_date(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    files: list[str] = list_files_recursive(find_directory("client"))
    remote_root_path: str = data.get_python_script_path(i)

    files_to_update: list[str] = []
    for file in files:
        remote_file: str = os.path.join(remote_root_path, os.path.basename(file))
        if not is_client_file_different(ssh, remote_file, file):
            print(f"File {file} is not up to date.")
            files_to_update.append(file)

    if len(files_to_update) > 0:
        return False
    return True


def python_scripts(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    installed: bool = check_python_script_installed(data.get_python_script_path(i), ssh)

    if installed:
        print("Scripts are installed.")
    else:
        print("Scripts are not installed or not up to date, installing / updating them...")
        installed_python_scripts_success: bool = install_python_script(data, ssh, i)
        if not installed_python_scripts_success:
            print("Error, could not install scripts.")
            return False

    print("Checking if scripts are up to date...")
    up_to_date: bool = check_python_script_up_to_date(ssh, data, i)
    if up_to_date:
        print("Scripts are up to date.")
    else:
        print("Scripts are not up to date, updating them...")
        updated_python_scripts_success: bool = install_python_script(data, ssh, i)
        if not updated_python_scripts_success:
            print("Error, could not update scripts.")
            return False

    return True


def python_installation(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    python_installed: bool = check_python_installed(ssh, data, i)

    if python_installed:
        print("Python is installed.")
    else:
        installed_success: bool = install_python(ssh, data, i)
        if not installed_success:
            print("Error, could not install python.")
            return False
    return True


def python_path(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    python_path_set: bool = check_python_path_set(ssh)

    if python_path_set:
        print("Python is in path.")
    else:
        added_to_path: bool = add_python_to_path(ssh)
        if not added_to_path:
            print("Error, could not add python to path.")
            return False
        refresh_env: bool = refresh_env_variables(ssh, data, i)
        if not refresh_env:
            print("Error, could not refresh environment variables. Failed to reboot the pc.")
            return False
    return True


def python_packages(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    # Get the path to the requirements_client.txt file in the server computer
    local_requirements_path = find_file("requirements_client.txt")
    python_packages_installed: bool = check_python_packages_installed(ssh, local_requirements_path)

    if not python_packages_installed:
        installed_packages_success: bool = install_python_packages(ssh, data.get_python_requirements_path(i))
        if not installed_packages_success:
            print("Error, could not install python packages.")
            return False
    return True


def check_and_install_client_setup(ssh: paramiko.SSHClient, data: Data, i: int) -> bool:
    print()

    if not python_scripts(ssh, data, i):
        return False

    print()
    if not python_installation(ssh, data, i):
        return False

    print()
    if not python_path(ssh, data, i):
        return False

    print()
    if not python_packages(ssh, data, i):
        return False

    return True
