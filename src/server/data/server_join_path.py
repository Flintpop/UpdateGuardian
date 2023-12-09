import os


class ServerPath:
    """
    Class that joins paths for the server.
    A simple wrapper for os.path.join.
    """
    @staticmethod
    def join(*args):
        return os.path.join(*args)
