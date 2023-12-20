from newServer.core.remote_computers_database import RemoteComputerDatabase
from newServer.infrastructure.config import Infos
from newServer.infrastructure.http_server_setup import run_server
from newServer.infrastructure.setup_manager import load_launch_time, ask_and_save_launch_time
from newServer.logs_management.server_logger import log_error, log_new_lines, log
from newServer.report.mails import setup_email_config

done = False


def modify_launch_time():
    """
    Modify the launch time of the program.

    The user will be asked to enter the day and the hour of the new launch time.
    """
    print("Modify launch time")
    print("Here is the current launch time configuration:")
    launch_time = load_launch_time()
    print(f"Day: {launch_time['day']}")
    print(f"Hour: {launch_time['hour']}")

    ask_and_save_launch_time()
    modify_settings()


def add_host():
    """
    Add a host to the database.

    It just restarts the http server.
    """
    print("By using this option, will start a http server to add new hosts.\n"
          f"Please, go to the computer you want to add and execute the powershell installer "
          f"{Infos.powershell_client_script_installer_name} :\n")
    if not run_server():
        log_error("Error with the http server. The database may be empty, or something else went wrong.",
                  print_formatted=False)
        return
    modify_settings()


def remove_host():
    """
    Remove a host from the database.

    The user will be asked to enter the name of the host to remove.
    """
    current_database = RemoteComputerDatabase.load_computer_data()
    if current_database.get_number_of_computers() <= 0:
        print("There are no hosts to remove.")
        return

    print("Here is the list of hosts:")
    print(current_database)
    print("")
    print("Type the name of the host you want to remove. Enter nothing if you no longer want to delete a computer.\n"
          " A backup will be created just in case after deletion.\n")
    hostname_to_remove: str = input("> ")

    if hostname_to_remove == "":
        return
    while not current_database.remove_computer(hostname_to_remove):
        print("Host not found. Please try again.")
        print("Type the name of the host you want to remove. Enter nothing if you no longer want to delete a computer."
              "\nA backup will be created just in case after deletion.\n")
        hostname_to_remove: str = input("> ")
        if hostname_to_remove == "":
            return

    current_database.save_computer_data()
    print("Host removed successfully.")


def exit_settings():
    """
    Exit the settings menu.
    """
    global done
    print("Exit settings called")
    done = True


def print_infos():
    """
    Print the settings menu.
    """
    log_new_lines()
    log("Modifying settings...", print_formatted=False)
    log("Type 'launch time' to modify the launch time of the program.", print_formatted=False)
    log("Type 'add' to add a new host.", print_formatted=False)
    log("Type 'remove' to remove a host.", print_formatted=False)
    log("Type 'exit' to exit the settings menu.\n", print_formatted=False)


def mails():
    """
    Modify the mail configuration.
    """
    setup_email_config()


def modify_settings():
    """
    Modify the settings of the server.

    The settings are:
    - The launch time of the program.
    - The mail configuration.
    - The hosts (read, delete, create).
    """
    global done
    print_infos()
    inputs = {
        "launch time": lambda: modify_launch_time(),
        "mails": lambda: mails(),
        "add": lambda: add_host(),
        "remove": lambda: remove_host(),
        "exit": lambda: exit_settings()
    }
    while not done:
        usr_input: str = input("> ")
        if usr_input not in inputs:
            log_error("Invalid input. Please enter a valid input.\n", print_formatted=False)
        else:
            inputs.get(usr_input, lambda: print("Invalid input."))()
        print_infos()
