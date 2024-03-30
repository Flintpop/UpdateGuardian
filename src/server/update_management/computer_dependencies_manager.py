import os

from src.server.core.remote_computer_manager import RemoteComputerManager
from src.server.exceptions.FilesExceptionsSSH import FileCreationError
from src.server.infrastructure.paths import ServerPath


class ComputerDependenciesManager:
    def __init__(self, remote_computer_manager: 'RemoteComputerManager'):
        self.STDOUT_MESSAGE = "STDOUT :"
        self.computer: 'RemoteComputerManager' = remote_computer_manager

    def send_client_application(self):
        self.computer.log(f"Checking if the executable and other files are uploaded on the path : "
                          f"{self.computer.paths.get_project_directory()}...")
        installed: bool = self.check_client_files_uploaded()

        if installed:
            self.computer.log("Files are uploaded.")
        else:
            self.computer.log("Files are not uploaded, uploading them...")

            if not self.upload_client_files():
                self.computer.log_error("Error, could not install scripts.")
                return False

        self.computer.log("Checking if files are up to date...")
        up_to_date: bool = self.are_client_files_up_to_date()
        if up_to_date:
            self.computer.log("Files are up to date.")
        else:
            self.computer.log("Files are not up to date, updating them...")
            updated_python_scripts_success: bool = self.upload_client_files()
            if not updated_python_scripts_success:
                self.computer.log_error("Error, could not update scripts.")
                return False

        return True

    def check_client_files_uploaded(self) -> bool:
        """
        Checks if the client application files are installed on the remote computer
        :return True if the files are sent, False otherwise.
        """
        client_folder_path: str = self.computer.paths.get_project_directory()
        install_exists: bool = self.computer.does_path_exists(client_folder_path)

        if not install_exists:
            self.computer.log(
                "There is no installation of the python script on the remote computer,"
                " because the folder is not here."
            )
            return install_exists

        self.computer.log("Folder exists, checking if all the files are here...")

        return self.check_all_files_exists()

    def check_all_files_exists(self) -> bool:
        """
        Checks if all the installation files exist on the remote computer.
        It compares the two .ps1 and .exe files in the client folder, with the files on the remote computer
        in the %USERPROFILE%/Infos.project_name folder.
        :return: True if all the files exist, False otherwise.
        """
        files: list[str] = ServerPath.get_client_files()
        files = [os.path.basename(file) for file in files]
        files = [self.computer.paths.join(self.computer.paths.get_project_directory(), file) for file in files]

        if len(files) == 0:
            self.computer.log_error("Error, no files to check.")
            return False

        for file in files:
            if not self.computer.does_path_exists(file):
                self.computer.log_error(f"The file path : '{file}' is not a valid path or does not exists.")
                return False
        return True

    def upload_client_files(self) -> bool:
        """
        Installs the client files on the computer. Overwrites the files if they already exist.

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

    def are_client_files_up_to_date(self):
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

    def reboot_and_reconnect(self) -> bool:
        self.computer.log("Rebooting remote computer...")
        self.computer.reboot()
        self.computer.wait_for_ssh_shutdown()

        if not self.computer.wait_and_reconnect(timeout=600):
            self.computer.log_error("Failed to reconnect to remote computer.")
            return False

        return True
