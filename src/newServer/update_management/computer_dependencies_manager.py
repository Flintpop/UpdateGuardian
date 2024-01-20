import os
import time

from src.newServer.core.remote_computer_manager import RemoteComputerManager
from src.newServer.exceptions.FilesExceptionsSSH import FileCreationError
from src.newServer.infrastructure.config import Infos
from src.newServer.infrastructure.paths import ServerPath
from src.newServer.ssh.commands import SSHCommandResult


class ComputerDependenciesManager:
    def __init__(self, remote_computer_manager: 'RemoteComputerManager'):
        self.STDOUT_MESSAGE = "STDOUT :"
        self.computer: 'RemoteComputerManager' = remote_computer_manager

    def python_scripts(self):
        installed: bool = self.check_python_script_installed()

        if installed:
            self.computer.log("Scripts are installed.")
        else:
            self.computer.log("Scripts are not installed or not up to date, installing / updating them...")

            if not self.upload_python_scripts():
                self.computer.log_error("Error, could not install scripts.")
                return False

        self.computer.log("Checking if scripts are up to date...")
        up_to_date: bool = self.check_python_script_up_to_date()
        if up_to_date:
            self.computer.log("Scripts are up to date.")
        else:
            self.computer.log("Scripts are not up to date, updating them...")
            updated_python_scripts_success: bool = self.upload_python_scripts()
            if not updated_python_scripts_success:
                self.computer.log_error("Error, could not update scripts.")
                return False

        return True

    def check_python_script_installed(self) -> bool:
        """
        Checks if the python script is installed on the remote computer.
        :return: True if the script is installed, False otherwise.
        """
        client_folder_path: str = self.computer.paths.get_project_directory()
        install_exists: bool = self.computer.does_path_exists(client_folder_path)

        if not install_exists:
            self.computer.log(
                "There is not installation of the python script on the remote computer,"
                " because the folder is not here."
            )
            return install_exists

        return self.check_all_files_exists()

    def check_all_files_exists(self) -> bool:
        """
        Checks if all the installation files exist on the remote computer.
        It compares all .py and .txt files in the client folder, with the files on the remote computer
        in the %USERPROFILE%/Infos.project_name folder.
        :return: True if all the files exist, False otherwise.
        """
        files: list[str] = ServerPath.get_client_files()

        for file in files:
            if not self.computer.does_path_exists(file):
                self.computer.log_error(f"The file path : '{file}' is not a valid path or does not exists.")
                return False
        return True

    def upload_python_scripts(self) -> bool:
        """
        Installs the update_windows python script on the remote computer. Overwrites the files if they already exist.

        :return: True if the upload was successful, False otherwise.
        """
        python_script_path: str = self.computer.paths.get_project_directory()

        created = self.computer.create_folder(python_script_path)

        if not created:
            self.computer.log_error(f"Error while creating the folder {python_script_path}")
            raise FileCreationError(f"Error while creating the folder {python_script_path}")

        files_to_upload: list[str] = ServerPath.get_client_files()
        try:
            self.computer.upload_files(files_to_upload, python_script_path)
            self.computer.log(f"Uploaded all the files : {files_to_upload}\n to the remote computer.")
        except (FileNotFoundError, FileExistsError, IOError):
            self.computer.log_error(f"Error while uploading the files {files_to_upload} to the remote computer.")
            return False

        return True

    def check_python_script_up_to_date(self):
        files: list[str] = ServerPath.get_client_files()
        remote_root_path: str = self.computer.paths.get_project_directory()

        files_to_update: list[str] = []
        for file in files:
            remote_file: str = ServerPath.join(remote_root_path, os.path.basename(file))
            if not self.computer.is_client_file_different(remote_file, file):
                self.computer.log(f"File {file} is not up to date.")
                files_to_update.append(file)

        if len(files_to_update) > 0:
            return False
        return True

    def python_installation(self):
        computer: 'RemoteComputerManager' = self.computer
        python_installed: bool = self.check_python_installed()

        if python_installed:
            computer.log("Python is installed.")
        else:
            installed_success: bool = self.install_python()
            if not installed_success:
                computer.log_error("Error, could not install python.")
                return False
            self.computer.log_error("Python path check..")
            if not self.check_python_in_path():
                computer.log("Rebooting because python path is not actualized...")
                refresh_env: bool = self.refresh_env_variables()
                if not refresh_env:
                    computer.log_error("Error, could not refresh environment variables. Failed to reboot the pc.")
                    return False
            else:
                computer.log("Python path is actualized, no need for reboot.")

        return True

    def check_python_installed(self):
        computer = self.computer
        if not self.computer.is_os_windows(computer.get_remote_computer()):
            raise NotImplementedError("Only Windows is supported.")
        python_executables = ("python.exe", "python3.exe", "python311.exe", "py.exe")

        folder_path = computer.paths.get_home_directory()
        folder_path += "\\AppData\\Local\\Programs\\Python\\"
        programs_path: bool = computer.does_path_exists(folder_path)

        if not programs_path:
            computer.log("Programs folder does not exists", "warning")
            computer.create_folder(folder_path)

            programs_path: bool = computer.does_path_exists(folder_path)

            if not programs_path:
                computer.log_error("Programs folder does not exists even after creation")
                return False
            return False

        computer.log("Programs folder exists")
        folder_path += Infos.python_folder_name

        if not computer.does_path_exists(folder_path):
            computer.log(f"{folder_path} folder does not exists on remote computer.", "warning")
            return False

        computer.log("Python folder exists")
        for executable in python_executables:
            executable_path = computer.paths.join(folder_path, executable)
            if computer.does_path_exists(executable_path):
                computer.log(f"Python executable {executable} exists")
                return True

        computer.log("Failed to find python executable.", level="warning")
        return False

    def upload_python_installer(self) -> bool:
        computer = self.computer
        computer.log("Checking if python installer exists on client computer...")
        does_python_installer_exists: bool = self.python_installer_exists()

        if does_python_installer_exists:
            computer.log("Python installer exists, not sending it.")
        if not does_python_installer_exists:
            computer.log("Python installer does not exist, sending it to client computer...")
            python_installer_sent = self.send_python_installer()
            if not python_installer_sent:
                computer.log_error("Error, could not send python installer.")
                return False
        return True

    def install_python(self, second_attempt=False) -> bool:
        computer = self.computer
        python_installer_uploaded: bool = self.upload_python_installer()
        if not python_installer_uploaded:
            return False

        computer.log("Installing Python...")

        target_dir: str = r"%USERPROFILE%\AppData\Local\Programs\Python"
        if not computer.does_path_exists(target_dir):
            computer.log(f"Python folder does not exists, creating it at {target_dir}...")

            if not computer.create_folder(target_dir):
                computer.log_error(f"Error, could not create python folder at {target_dir}.")
                return False

        target_dir = target_dir + "\\" + Infos.python_folder_name
        # Get the path to the python script that will install python
        path_update_guardian: str = computer.paths.get_project_directory()
        python_installer_filename: str = Infos.get_server_python_installer_name()

        parameters: str = f"/quiet InstallAllUsers=0 TargetDir={target_dir}" \
                          f" Include_launcher=0 Include_test=0 Include_dev=0 Include_doc=0 Include_pip=1 PrependPath=1"

        command: str = os.path.join(path_update_guardian, python_installer_filename) + " " + parameters

        res: SSHCommandResult = computer.execute_command(command)
        stdout, stderr = res.stdout, res.stderr

        if stderr:
            computer.log_error("Error, could not install python : " + stderr)
            computer.log_error("command : " + command)
            computer.log_error("Python update guardian variable : " + path_update_guardian)
            if not second_attempt:
                computer.log("The installer may be corrupted. Trying to install python again...")
                self.send_python_installer()
                time.sleep(0.5)  # To make sure that the installer is sent before trying to install it
                return self.install_python(second_attempt=True)
            return False

        if stdout:
            computer.log(self.STDOUT_MESSAGE + stdout)

        computer.log("Python installed.")

        return True

    def send_python_installer(self) -> bool:
        self.computer.log("Sending python installer...")

        installer_path: str = ServerPath.get_python_installer()
        if not ServerPath.exists(installer_path):
            self.computer.log_error(f"Error, the python installer '{installer_path}' "
                                    f"does not exist on the server. Please check the path, or if it exists.")
            return False

        if not self.computer.upload_file(installer_path, self.computer.paths.get_project_directory()):
            self.computer.log_error("Error, could not send python installer.")
            return False
        self.computer.log("Python installer sent.")
        return True

    def python_installer_exists(self) -> bool:
        installer_path = self.computer.paths.get_installer_path()
        return self.computer.does_path_exists(installer_path)

    def refresh_env_variables(self) -> bool:
        self.computer.log("Rebooting remote computer...")
        self.computer.reboot()
        self.computer.wait_for_ssh_shutdown()

        if not self.computer.wait_and_reconnect(timeout=600):
            self.computer.log_error("Failed to reconnect to remote computer.")
            return False

        if not self.check_python_in_path():
            self.computer.log_error("Failed to add python to path.")
            return False

        return True

    def check_python_in_path(self) -> bool:
        self.computer.log("Checking if python is path again...")

        # Check if 'python' command is available
        res: SSHCommandResult = self.computer.execute_command("where python")
        stdout, stderr = res.stdout, res.stderr

        if not stderr and "python" in stdout.lower():
            self.computer.log("Python is path.")
            return True
        else:
            self.computer.log_error("Python is not installed.")
            return False

    def python_packages(self) -> bool:
        python_packages_installed: bool = self.check_python_packages_installed()

        if not python_packages_installed:
            installed_packages_success: bool = self.install_python_packages()
            if not installed_packages_success:
                self.computer.log_error("Error, could not install python packages.")
                return False
        return True

    def check_python_packages_installed(self) -> bool:
        """
        Checks if all the packages in the requirements_client.txt file are installed for the client.
        :return: True if packages are installed, False if at least one is lacking
        """
        requirements_file_path: str = ServerPath.get_requirement_file()
        self.computer.log("Checking if requirements_client.txt packages are installed...")

        with open(requirements_file_path, 'r') as file:
            requirements = file.readlines()

        # Remove newlines and spaces
        requirements = [req.strip() for req in requirements if req.strip()]

        all_installed = True

        for req in requirements:
            # Check if the package is installed using 'pip show'
            res: SSHCommandResult = self.computer.execute_command(f"pip show {req}")
            stdout, stderr = res.stdout, res.stderr

            if not stderr and req in stdout:
                self.computer.log(f"{req} is installed")
            elif stderr or stdout and "package(s) not found" in stderr.lower():
                self.computer.log(f"{req} is not found. Make sure you have the correct name in requirements_client.txt",
                                  level="warning")
                all_installed = False
            else:
                self.computer.log(f"{req} is not installed")
                all_installed = False

        return all_installed

    def install_python_packages(self):
        command: str = "pip install -r " + self.computer.paths.get_requirements_file()
        res: SSHCommandResult = self.computer.execute_command(command)
        stdout, stderr = res.stdout, res.stderr

        if stderr and "error" in stderr.lower() or stderr and "erreur" in stderr.lower():
            self.computer.log_error("Error, could not install python packages : " + stderr)
            return False
        if stderr and "warning" in stderr.lower():
            self.computer.log("Warning, but python packages installed", level="warning")
            if "pip" in stderr.lower():
                self.computer.log("Pip should be updated.")
            else:
                self.computer.log_error("Stderr : " + stderr)
                return False
        if stdout:
            self.computer.log(self.STDOUT_MESSAGE + stdout)
        return True
