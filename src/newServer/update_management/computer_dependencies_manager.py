import os

from newServer.core.remote_computer_manager import RemoteComputerManager
from newServer.exceptions.FilesExceptionsSSH import FileCreationError
from newServer.infrastructure.paths import ServerPath


class ComputerDependenciesManager:
    def __init__(self, remote_computer_manager: 'RemoteComputerManager'):
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
        client_folder_path: str = self.computer.paths.get_project_directory_on_client()
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
        python_script_path: str = self.computer.paths.get_project_directory_on_client()

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
