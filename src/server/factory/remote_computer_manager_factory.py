import paramiko

from src.server.core.computer import Computer
from src.server.core.remote_computer import RemoteComputer
from src.server.core.remote_computer_manager import RemoteComputerManager


class RemoteComputerManagerFactory:
    """
    This class is responsible for creating a RemoteComputerManager object.
    The object can be created with two possible contexts:
    - The context of a remote computer that is already registered in the database.
    - The context of a remote computer that is not registered in the database.

    The way to create the object in the first context requires the following parameters:
    - The hostname
    """

    @staticmethod
    def create(hostname: str, ip: str, mac_address: str, username: str, init_logger: bool = True) \
            -> RemoteComputerManager:
        """
        Creates a RemoteComputerManager object, with the context of a remote computer that is not registered
        in the database.
        """
        computer = Computer(ip, hostname, mac_address, username)
        remote_computer = RemoteComputer(computer, init_logger)
        return RemoteComputerManager(remote_computer)

    @staticmethod
    def create_from_computer(computer: 'Computer', init_logger: bool = True) -> RemoteComputerManager:
        """
        Creates a RemoteComputerManager object from a Computer object.
        :param computer: The Computer object.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        remote_computer = RemoteComputer(computer, init_logger)
        return RemoteComputerManager(remote_computer)

    @staticmethod
    def create_from_dictionary(dict_computer: dict, init_logger: bool = True) -> RemoteComputerManager:
        """
        Creates a RemoteComputerManager object from a dictionary.
        :param dict_computer: The dictionary.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        ipv4: str | None = dict_computer.get("ipv4", None)
        hostname: str | None = dict_computer.get("hostname", None)
        mac_address: str | None = dict_computer.get("mac_address", None)
        username: str | None = dict_computer.get("username", None)

        cond = ipv4 and hostname and mac_address and username
        if not cond:
            raise ValueError("The dictionary must contain the following keys: ipv4, hostname, mac_address, username."
                             "Here is the dictionary: \n" + str(dict_computer))

        computer = Computer(ipv4, hostname, mac_address, username)
        remote_computer = RemoteComputer(computer, init_logger)
        return RemoteComputerManager(remote_computer)

    @staticmethod
    def create_from_dictionary_and_ssh(dict_computer: dict, ssh: paramiko.SSHClient,
                                       init_logger: bool = True) -> RemoteComputerManager:
        """
        Creates a RemoteComputerManager object from a dictionary, AND ssh. The ssh client must be setup and
        connected to the remote computer, since the RemoteComputerManager object will use it and be linked to it.
        :param dict_computer: The dictionary.
        :param ssh: The ssh client.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        ipv4: str | None = dict_computer.get("ipv4", None)
        hostname: str | None = dict_computer.get("hostname", None)
        mac_address: str | None = dict_computer.get("mac_address", None)
        username: str | None = dict_computer.get("username", None)

        cond = ipv4 and hostname and mac_address and username
        if not cond:
            raise ValueError("The dictionary must contain the following keys: ipv4, hostname, mac_address, username."
                             "Here is the dictionary: \n" + str(dict_computer))

        computer = Computer(ipv4, hostname, mac_address, username)
        remote_computer = RemoteComputer(computer, init_logger)
        remote_computer.ssh_session = ssh
        return RemoteComputerManager(remote_computer)
