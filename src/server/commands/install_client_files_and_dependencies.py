import os
import time

import paramiko

from src.server.commands.install_python_scripts import check_python_script_installed, install_python_script
from src.server.commands.path_functions import find_file
from src.server.config import Infos

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.ssh.ssh_commands import stdout_err_execute_ssh_command, send_file_ssh, does_path_exists_ssh, \
    reboot_remote_pc, wait_and_reconnect, is_pc_on, is_client_file_different, create_folder_ssh

STDOUT_MESSAGE = "STDOUT: \n"


def os_windows(computer: 'Computer'):
    # Try to get OS information using 'uname' command (usually works on Unix-like systems)
    ssh: paramiko.SSHClient = computer.ssh_session

    stdout, _ = stdout_err_execute_ssh_command(ssh, "uname -a")
    os_info = stdout

    if not os_info:
        # If 'uname' command doesn't work, try to get OS information using 'ver' command
        # (usually works on Windows systems)
        stdout, _ = stdout_err_execute_ssh_command(ssh, "ver")
        os_info = stdout

    if not os_info:
        computer.log("Failed to get OS information.", level="warning")
        return True
    if "windows" in os_info.lower():
        return True

    return False


def check_python_installed(computer: 'Computer') -> bool:
    if not os_windows(computer):
        raise NotImplementedError("Only Windows is supported.")
    python_executables = ("python.exe", "python3.exe", "python311.exe", "py.exe")

    folder_path = computer.get_home_directory_on_client()
    folder_path += "\\AppData\\Local\\Programs\\Python\\"
    programs_path: bool = does_path_exists_ssh(computer.ssh_session, folder_path)

    if not programs_path:
        computer.log("Programs folder does not exists", "warning")
        create_folder_ssh(computer, folder_path)

        programs_path: bool = does_path_exists_ssh(computer.ssh_session, folder_path)

        if not programs_path:
            computer.log_error("Programs folder does not exists even after creation")
            return False
        return False

    computer.log("Programs folder exists")
    folder_path += Infos.python_folder_name

    if not does_path_exists_ssh(computer.ssh_session, folder_path):
        computer.log(f"{folder_path} folder does not exists on remote computer.", "warning")
        return False

    computer.log("Python folder exists")
    for executable in python_executables:
        executable_path = computer.join_path(folder_path, executable)
        if does_path_exists_ssh(computer.ssh_session, executable_path):
            computer.log(f"Python executable {executable} exists")
            return True

    computer.log("Failed to find python executable.", level="warning")
    return False


def check_python_in_path(computer: 'Computer') -> bool:
    computer.log("Checking if python is path again...")

    # Check if 'python' command is available
    stdout, stderr = stdout_err_execute_ssh_command(computer.ssh_session, "where python")

    if not stderr and "python" in stdout:
        computer.log("Python is path.")
        return True
    else:
        computer.log_error("Python is not installed.")
        return False


def check_python_packages_installed(computer: 'Computer') -> bool:
    """
    Checks if all the packages in the requirements_client.txt file are installed for the client.
    :param computer: The remote computer to check if python packages are installed
    :return: True if packages are installed, False if at least one is lacking
    """
    ssh: paramiko.SSHClient = computer.ssh_session
    requirements_file_path: str = find_file(os.path.basename(computer.get_requirements_path()))
    computer.log("Checking if requirements_client.txt packages are installed...")

    with open(requirements_file_path, 'r') as file:
        requirements = file.readlines()

    # Remove newlines and spaces
    requirements = [req.strip() for req in requirements if req.strip()]

    all_installed = True

    for req in requirements:
        # Check if the package is installed using 'pip show'
        stdout, stderr = stdout_err_execute_ssh_command(ssh, f"pip show {req}")

        if not stderr and req in stdout:
            computer.log(f"{req} is installed")
        elif stderr or stdout and "package(s) not found" in stderr.lower():
            computer.log(f"{req} is not found. Make sure you have the correct name in requirements_client.txt",
                         level="warning")
            all_installed = False
        else:
            computer.log(f"{req} is not installed")
            all_installed = False

    return all_installed


def check_file_exists(installer_path: str) -> bool:
    res: bool = os.path.isfile(installer_path)
    return res


def send_python_installer(computer: 'Computer') -> bool:
    ssh: paramiko.SSHClient = computer.ssh_session
    computer.log("Sending python installer...")

    installer_path: str = Infos.get_server_python_installer_name()
    installer_path = find_file(installer_path)
    does_file_exists: bool = check_file_exists(installer_path)
    if not does_file_exists:
        computer.log_error("Error, the python installer does not exist on the server. Please check the path, "
                           "or if it exists.")
        return False

    send_file_ssh(ssh, installer_path, computer.get_project_directory_on_client())
    computer.log("Python installer sent.")
    return True


def add_python_to_path(computer: 'Computer') -> bool:
    ssh: paramiko.SSHClient = computer.ssh_session
    computer.log("Adding python to path...")

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
    python_path_var = f'{user_profile}\\AppData\\Local\\Programs\\Python\\{Infos.python_folder_name}'
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
        computer.log_error("Error, could not add python to path : " + stderr)
        return False
    if stdout:
        computer.log(STDOUT_MESSAGE + stdout)
    return True


def check_python_path_set(computer: 'Computer') -> bool:
    ssh: paramiko.SSHClient = computer.ssh_session
    computer.log("Checking if python is in path...")

    path_check_command: str = r'echo %PATH%'

    stdout, stderr = stdout_err_execute_ssh_command(ssh, path_check_command)

    if stderr:
        computer.log_error("Error, path command failed : " + stderr)
        return False

    if "python" not in stdout.lower():
        computer.log("Python is not in path", "warning")
        return False

    computer.log("Python seems to be in path. Checking if python executable is launchable...")

    # Check if 'python' command is available
    stdout2, stderr2 = stdout_err_execute_ssh_command(ssh, "where python")

    if not stderr2 and "python" in stdout2.lower():
        computer.log("Python is installed and in path")
        computer.log("Checking pip...")
        stdout3, stderr3 = stdout_err_execute_ssh_command(ssh, "pip --version")
        if stdout3:
            computer.log("Pip is installed")
            return True
        if stderr3:
            computer.log_error("Error, pip is not installed : " + stderr3)
        else:
            computer.log_error("Error, pip is not installed and there is no error message."
                               "Make sure that python is installed correctly. You may have to reinstall it "
                               "manually. Also, please check the path.")
        return False
    else:
        computer.log_error("Python is not set correctly in path, because it may be there despite the fact that it is"
                           " installed.")
        computer.log_error(f"Here is the path variable: \n{stdout}")
        computer.log_error("Please check the path manually, and if it is correct, please reinstall python manually.")
        return False


def python_installer_exists(computer: 'Computer') -> bool:
    ssh: paramiko.SSHClient = computer.ssh_session
    installer_path = computer.get_installer_path()
    return does_path_exists_ssh(ssh, installer_path)


def install_python_installer(computer: 'Computer') -> bool:
    computer.log("Checking if python installer exists on client computer...")
    does_python_installer_exists: bool = python_installer_exists(computer)

    if does_python_installer_exists:
        computer.log("Python installer exists, not sending it.")
    if not does_python_installer_exists:
        computer.log("Python installer does not exist, sending it to client computer...")
        python_installer_sent = send_python_installer(computer)
        if not python_installer_sent:
            computer.log_error("Error, could not send python installer.")
            return False
    return True


def install_python(computer: 'Computer', second_attempt=False) -> bool:
    python_installer_installed: bool = install_python_installer(computer)
    if not python_installer_installed:
        return False

    computer.log("Installing Python...")

    target_dir: str = r"%USERPROFILE%\AppData\Local\Programs\Python"
    if not does_path_exists_ssh(computer.ssh_session, target_dir):
        create_folder_ssh(computer, target_dir)

    target_dir = target_dir + "\\" + Infos.python_folder_name
    # Get the path to the python script that will install python
    path_update_guardian: str = computer.get_project_directory_on_client()
    python_installer_filename: str = Infos.get_server_python_installer_name()

    parameters: str = f"/quiet InstallAllUsers=0 TargetDir={target_dir}" \
                      f" Include_launcher=0 Include_test=0 Include_dev=0 Include_doc=0 Include_pip=1 PrependPath=1"

    command: str = os.path.join(path_update_guardian, python_installer_filename) + " " + parameters

    stdout, stderr = stdout_err_execute_ssh_command(computer.ssh_session, command)

    if stderr:
        computer.add_log_memory("Error, could not install python : " + stderr)
        computer.log_error("command : " + command)
        computer.log_error("Python update guardian variable : " + path_update_guardian)
        if not second_attempt:
            computer.log("The installer may be corrupted. Trying to install python again...")
            send_python_installer(computer)
            time.sleep(0.1)  # To make sure that the installer is sent before trying to install it
            return install_python(computer, second_attempt=True)
        return False

    if stdout:
        computer.log(STDOUT_MESSAGE + stdout)

    computer.log("Python installed.")

    return True


def install_python_packages(computer: 'Computer', requirements_file_path: str) -> bool:
    ssh: paramiko.SSHClient = computer.ssh_session
    command: str = "pip install -r " + requirements_file_path
    stdout, stderr = stdout_err_execute_ssh_command(ssh, command)

    if stderr and "error" in stderr.lower() or stderr and "erreur" in stderr.lower():
        computer.log_error("Error, could not install python packages : " + stderr)
        return False
    if stderr and "warning" in stderr.lower():
        computer.log("Warning, but python packages installed", level="warning")
        if "pip" in stderr.lower():
            computer.log("Pip should be updated.")
        else:
            computer.log_error("Stderr : " + stderr)
            return False
    if stdout:
        computer.log(STDOUT_MESSAGE + stdout)
    return True


def wait_for_ssh_shutdown(computer: 'Computer') -> None:
    """
    Wait for the SSH server to be down.
    :param computer: The computer to wait for.
    :return: Nothing
    """
    ssh_server_shutdown = False
    computer.log("Waiting for SSH server to be down...")
    computer.force_close_ssh_session()
    computer.ssh_session.close()
    while not ssh_server_shutdown:
        ssh_server_shutdown = not is_pc_on(computer=computer, print_log_connected=False)
    computer.log("SSH server is down, waiting for it to be up again...")


def refresh_env_variables(computer: 'Computer') -> bool:
    computer.log("Rebooting remote computer...")
    ssh: paramiko.SSHClient = computer.ssh_session
    reboot_remote_pc(ssh)
    ipaddress, remote_user, remote_computer_private_key = computer.ipv4, computer.username, computer.get_private_key()
    wait_for_ssh_shutdown(computer)

    if not wait_and_reconnect(computer, ipaddress, remote_user, remote_computer_private_key):
        computer.log_error("Failed to reconnect to remote computer.")
        return False

    if not check_python_in_path(computer):
        computer.log_error("Failed to add python to path.")
        return False

    return True


def check_python_script_up_to_date(computer: 'Computer') -> bool:
    files: list[str] = computer.get_list_client_files_to_send()
    remote_root_path: str = computer.get_project_directory_on_client()

    files_to_update: list[str] = []
    for file in files:
        remote_file: str = os.path.join(remote_root_path, os.path.basename(file))
        if not is_client_file_different(computer, remote_file, file):
            computer.log(f"File {file} is not up to date.")
            files_to_update.append(file)

    if len(files_to_update) > 0:
        return False
    return True


def python_scripts(computer: 'Computer') -> bool:
    installed: bool = check_python_script_installed(computer)

    if installed:
        computer.log("Scripts are installed.")
    else:
        computer.log("Scripts are not installed or not up to date, installing / updating them...")
        installed_python_scripts_success: bool = install_python_script(computer)
        if not installed_python_scripts_success:
            computer.log_error("Error, could not install scripts.")
            return False

    computer.log("Checking if scripts are up to date...")
    up_to_date: bool = check_python_script_up_to_date(computer)
    if up_to_date:
        computer.log("Scripts are up to date.")
    else:
        computer.log("Scripts are not up to date, updating them...")
        updated_python_scripts_success: bool = install_python_script(computer)
        if not updated_python_scripts_success:
            computer.log_error("Error, could not update scripts.")
            return False

    return True


def python_installation(computer: 'Computer') -> bool:
    python_installed: bool = check_python_installed(computer)

    if python_installed:
        computer.log("Python is installed.")
    else:
        installed_success: bool = install_python(computer)
        if not installed_success:
            computer.log_error("Error, could not install python.")
            return False
        computer.log("Rebooting after python has been installed and should be in path...")
        refresh_env: bool = refresh_env_variables(computer)
        if not refresh_env:
            computer.log_error("Error, could not refresh environment variables. Failed to reboot the pc.")
            return False

    return True


def python_path(computer: 'Computer') -> bool:
    python_path_set: bool = check_python_path_set(computer)

    if python_path_set:
        computer.log("Python is in path.")
    else:
        added_to_path: bool = add_python_to_path(computer=computer)
        if not added_to_path:
            computer.log_error("Error, could not add python to path.")
            return False
        refresh_env: bool = refresh_env_variables(computer)
        if not refresh_env:
            computer.log_error("Error, could not refresh environment variables. Failed to reboot the pc.")
            return False
    return True


def python_packages(computer: 'Computer') -> bool:
    python_packages_installed: bool = check_python_packages_installed(computer=computer)

    if not python_packages_installed:
        installed_packages_success: bool = install_python_packages(computer, computer.get_requirements_path())
        if not installed_packages_success:
            computer.log_error("Error, could not install python packages.")
            return False
    return True
