# -----------------------------------------------------------
# computer_updater_manager_factory.py
# Author: darwh
# Date: 15/01/2024
# Description: 
# -----------------------------------------------------------
# Type checking to avoid circular imports on Computer :

from src.server.core.remote_computer import RemoteComputer
from src.server.core.remote_computer_manager import RemoteComputerManager
from src.server.update_management.computer_update_manager import ComputerUpdateManager

from src.server.core.computer import Computer

from src.server.factory.HostFactory import HostFactory


class ComputerUpdaterManagerFactory(HostFactory):
    @staticmethod
    def create(hostname: str, ip: str, mac_address: str, username: str, init_logger: bool = True, **kwargs) \
            -> ComputerUpdateManager:
        """
        Creates a RemoteComputerManager object, with the context of a remote computer that is not registered
        in the database.
        """
        computer = Computer(ip, hostname, mac_address, username)
        remote_computer = RemoteComputer(computer, init_logger)
        remote_computer_manager = RemoteComputerManager(remote_computer)
        return ComputerUpdateManager(remote_computer_manager)

    @staticmethod
    def create_from_computer(computer: 'Computer', init_logger: bool = True) -> ComputerUpdateManager:
        """
        Creates a RemoteComputerManager object from a Computer object.
        :param computer: The Computer object.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        remote_computer = RemoteComputer(computer, init_logger)
        remote_computer_manager = RemoteComputerManager(remote_computer)
        return ComputerUpdateManager(remote_computer_manager)

    @staticmethod
    def create_from_dictionary(dict_computer: dict, init_logger: bool = True) -> ComputerUpdateManager:
        """
        Creates a RemoteComputerManager object from a dictionary.
        :param dict_computer: The dictionary.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        ipv4: str = dict_computer.get("ipv4", None)
        hostname: str = dict_computer.get("hostname", None)
        mac_address: str = dict_computer.get("mac_address", None)
        username: str = dict_computer.get("username", None)

        cond = ipv4 and hostname and mac_address and username
        if not cond:
            raise ValueError("The dictionary must contain the following keys: ipv4, hostname, mac_address, username."
                             "Here is the dictionary: \n" + str(dict_computer))

        computer = Computer(ipv4, hostname, mac_address, username)
        remote_computer = RemoteComputer(computer, init_logger)
        remote_computer_manager = RemoteComputerManager(remote_computer)
        return ComputerUpdateManager(remote_computer_manager)
