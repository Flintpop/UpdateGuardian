import os


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
