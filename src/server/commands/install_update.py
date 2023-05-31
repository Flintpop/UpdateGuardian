from concurrent.futures import ThreadPoolExecutor

from src.server.config import Infos
from src.server.data.computer import Computer
from src.server.data.computer_database import ComputerDatabase

from src.server.environnement.server_logs import log, log_error
from src.server.warn_admin.mails import send_result_email


def update_all_computer(database: ComputerDatabase) -> None:
    """
    Install Windows Update on all pc in the local network.
    :param database: The database contains all the computers and the data object.
    """

    max_workers = database.data.get_max_number_of_simultaneous_updates()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Update all computers using threads
        computers: list[Computer] = database.get_computers()
        executor.map(update_computer, computers)

    log("Update rollout over. Checks logs for more informations.")
    log("Sending result email...")
    if Infos.email_send:
        send_result_email(database)


def update_computer(computer: Computer):
    log(message="Updating computer " + computer.hostname + "...")
    if not computer.update():
        computer.download_log_file_ssh()
        computer.updated_successfully = False
        computer.no_updates = False

        log_error("Error while updating computer " + computer.hostname)
        log_error("Skipping this computer...")
        return

    if computer.no_updates:
        log("Computer " + computer.hostname + " has no updates.")
        return
    log("Computer " + computer.hostname + " updated successfully!")
