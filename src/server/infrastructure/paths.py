import os

from src.server.infrastructure.config import Infos


class ServerPath:
    json_computers_database_filename: str = "computers_database.json"
    """
    Class that joins paths for the server.
    A simple wrapper for os.path.join, along with some utility methods.
    """

    @staticmethod
    def join(*args):
        return os.path.join(*args)

    @staticmethod
    def get_home_path():
        return os.path.expanduser("~")

    @staticmethod
    def get_project_root():
        # Get the path of the project root folder, in absolute.
        # To be tested
        number_of_goback: int = 4
        path = os.path.abspath(__file__)
        for _ in range(number_of_goback):
            path = os.path.dirname(path)
        if not path.endswith(Infos.PROJECT_NAME):
            raise EnvironmentError(f"The project root path is not correct : {path}"
                                   f"It does not end with {Infos.PROJECT_NAME}")

        return path

    @staticmethod
    def get_log_folder_path():
        return ServerPath.join(ServerPath.get_project_root(), "logs")

    @staticmethod
    def get_database_path():
        return ServerPath.join(ServerPath.get_project_root(), ServerPath.json_computers_database_filename)

    @staticmethod
    def exists(computers_data_json_file):
        return os.path.exists(computers_data_json_file)

    @staticmethod
    def get_config_json_file():
        return ServerPath.join(ServerPath.get_project_root(), Infos.config_json_file)

    @staticmethod
    def get_email_infos_json_file():
        return ServerPath.join(ServerPath.get_project_root(), Infos.email_infos_json)

    @staticmethod
    def get_launch_time_filename():
        return ServerPath.join(ServerPath.get_project_root(), Infos.launch_time_filename)

    @staticmethod
    def get_powershell_client_script_installer():
        return ServerPath.join(ServerPath.get_project_root(), "scripts_powershell",
                               Infos.powershell_client_script_installer_name)

    @staticmethod
    def get_error_logs_path(hostname: str, logs_filename: str):
        return ServerPath.join(ServerPath.get_log_folder_path(), logs_filename, f"update_windows-{hostname}"
                                                                                f"-ERROR-LOGS.log")

    @staticmethod
    def get_client_folder():
        return ServerPath.join(ServerPath.get_project_root(), "src", "client")

    @staticmethod
    def get_client_files() -> list[str]:
        """
        Gets all the useful files that can be uploaded to the client.
        This includes the .exe file, and the .ps1 file only.
        :return: A list of all the files that can be uploaded to the client.
        """
        client_folder: str = ServerPath.get_client_folder()
        exe_file: str = ServerPath.join(client_folder, "dist", Infos.client_exe_filename)
        ps1_file: str = ServerPath.join(client_folder, Infos.client_powershell_program_name)

        if not os.path.exists(exe_file):
            raise FileNotFoundError(f"The client exe file was not found at {exe_file}")

        if not os.path.exists(ps1_file):
            raise FileNotFoundError(f"The client ps1 file was not found at {ps1_file}")

        return [exe_file, ps1_file]

    @staticmethod
    def get_python_installer():
        """
        :returns: The name of the server python installer
        """
        path: str = "python_" + Infos.python_precise_version + ".exe"
        return ServerPath.join(ServerPath.get_project_root(), path)

    @staticmethod
    def get_requirement_file():
        return ServerPath.join(ServerPath.get_project_root(), "src", "client", Infos.requirements_client_filename)

    @staticmethod
    def get_ssh_keys_folder():
        return ServerPath.join(ServerPath.get_project_root(), "src", "server", "ssh", "keys")

    @staticmethod
    def get_main_file():
        return ServerPath.join(ServerPath.get_project_root(), "src", "server", "application", "program.py")


class ClientPath:
    def __init__(self, hostname: str, username: str):
        self.hostname: str = hostname
        self.username: str = username

    @staticmethod
    def join(*args) -> str:
        """
        Join the paths using Windows-style path separator.

        Computer class should represent a Windows computer, so we need to replace Linux-style path separators with
        Windows-style path separators, and then join the paths using Windows-style path separator.
        """
        # Replace empty components with a backslash
        args = ['\\' if arg == '' else arg for arg in args]
        # Join the paths
        joined_path = os.path.join(*args)
        # Replace Linux-style path separators with Windows-style path separators
        windows_path = joined_path.replace('/', '\\')

        replaced_all_duplicated_backslashes = False
        while not replaced_all_duplicated_backslashes:
            if '\\\\' in windows_path:
                windows_path = windows_path.replace('\\\\', '\\')
            else:
                replaced_all_duplicated_backslashes = True
        return windows_path

    def get_project_directory(self):
        return ClientPath.join(self.get_home_directory(), Infos.PROJECT_NAME)

    def get_home_directory(self):
        return "C:\\Users\\" + self.username.split("\\")[1]  # Get the username without the domain

    def get_installer_path(self):
        return ClientPath.join(self.get_project_directory(), ServerPath.get_python_installer())

    def get_requirements_file(self):
        return ClientPath.join(self.get_project_directory(), Infos.requirements_client_filename)

    def get_program_path(self):
        return ClientPath.join(self.get_project_directory(), Infos.client_program_name)


def list_files_recursive(directory: str) -> list[str]:
    all_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            add_file(all_files, file, root)

    return all_files


def add_file(all_files: list[str], file: str, root: str) -> None:
    dir_exceptions = ["__pycache__", ".git", ".idea", ".vscode", "venv", ".gitignore", "__init__.py"]
    if file not in all_files:
        file_path = os.path.join(root, file)
        add_var = True

        for exception in dir_exceptions:
            if file_path.__contains__(exception):
                add_var = False
                break

        if add_var:
            all_files.append(file_path)
