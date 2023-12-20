import os

from newServer.infrastructure.config import Infos


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
    def get_project_root_path():
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
        return ServerPath.join(ServerPath.get_project_root_path(), "logs")

    @staticmethod
    def get_database_path():
        return ServerPath.join(ServerPath.get_project_root_path(), ServerPath.json_computers_database_filename)

    @staticmethod
    def exists(computers_data_json_file):
        return os.path.exists(computers_data_json_file)

    @staticmethod
    def get_config_json_file():
        return ServerPath.join(ServerPath.get_project_root_path(), Infos.config_json_file)

    @staticmethod
    def get_email_infos_json_file():
        return ServerPath.join(ServerPath.get_project_root_path(), Infos.email_infos_json)
