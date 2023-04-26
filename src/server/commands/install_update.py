from concurrent.futures import ThreadPoolExecutor

from src.server.data.computer import Computer
from src.server.data.computer_database import ComputerDatabase

from src.server.data.server_logs import log


def update_all_computer(database: ComputerDatabase) -> None:
    """
    Install Windows Update on all pc in the local network.
    :param database: The database containing all the computers, and the data object.
    """

    log("Updating ip addresses database...")
    database.refresh_ip_addresses()
    log("Checking for updates on all pc...")

    max_workers = database.data.get_max_number_of_simultaneous_updates()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Update all computers using threads
        computers: list[Computer] = database.get_computers()
        executor.map(update_computer, computers)


def update_computer(computer: Computer):
    log(message="Updating computer " + computer.hostname + "...")
    computer.update()
