# -----------------------------------------------------------
# HostFactory.py
# Author: darwh
# Date: 15/01/2024
# Description: 
# -----------------------------------------------------------

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.newServer.core.computer import Computer


class HostFactory(ABC):
    """
    This is an interface for creating RemoteComputerManager objects.
    """

    @abstractmethod
    def create(self, hostname: str, ip: str, mac_address: str, username: str, init_logger: bool = True):
        """
        Creates a RemoteComputerManager object, with the context of a remote computer that is not registered
        in the database.
        """
        pass

    @abstractmethod
    def create_from_computer(self, computer: 'Computer', init_logger: bool = True):
        """
        Creates a RemoteComputerManager object from a Computer object.
        :param computer: The Computer object.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        pass

    @abstractmethod
    def create_from_dictionary(self, dict_computer: dict, init_logger: bool = True):
        """
        Creates a RemoteComputerManager object from a dictionary.
        :param dict_computer: The dictionary.
        :param init_logger: True if the logger should be initialized, False otherwise.
        :return: The RemoteComputerManager object.
        """
        pass
