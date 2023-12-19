import os

from newServer.infrastructure.config import Infos


class ServerPath:
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
        path: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if not path.endswith(Infos.PROJECT_NAME):
            raise EnvironmentError(f"The project root path is not correct : {path}"
                                   f"It does not end with {Infos.PROJECT_NAME}")

        return path

    @staticmethod
    def get_log_path():
        return ServerPath.join(ServerPath.get_project_root_path(), "logs")
