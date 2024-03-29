import json
import os
import re
import socket
import sys

if sys.platform == "win32":
    import keyring

from src.server.commands.path_functions import find_file, list_files_recursive, find_directory
from src.server.config import Infos
from src.server.environnement.http_server_setup import run_server
from src.server.environnement.server_logs import log, log_error, log_new_lines

launch_infos_filename: str = "launch_infos.json"


def get_local_ipv4_address():
    try:
        # Create a temporary socket to establish a connection with a known server
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))  # Google's public DNS server

        # Obtain the local IPv4 address associated with the connection
        local_ipv4_address = temp_socket.getsockname()[0]

        # Close the temporary socket
        temp_socket.close()

        return local_ipv4_address
    except OSError:
        return None


def get_all_files_from_server() -> list[str]:
    directory = find_directory(Infos.PROJECT_NAME)
    files = list_files_recursive(directory)
    cur_sep = os.path.sep
    exceptions = ["HEAD", ".gitignore", ".git"]
    files_to_remove: list[str] = []
    for file in files:
        directories_and_files_of_file: list[str] = file.split(cur_sep)
        for exception in exceptions:
            if exception in directories_and_files_of_file and file in files:
                files_to_remove.append(file)

    return files


def check_all_files_integrity():
    files: list[str] = get_all_files_from_server()
    exceptions: list[str] = ["HEAD", ".gitignore", ".git"]
    for i, file1 in enumerate(files):
        for j in range(i + 1, len(files)):
            file1 = os.path.basename(file1)
            file2 = os.path.basename(files[j])
            if file1 == file2 and file1 not in exceptions:
                log_error(f"Error: The file {file1} is duplicated in the server with file {file2}.")
                log_error("Here is their path : ")
                log_error("File 1  : " + files[i])
                log_error("File 2  : " + files[j])
                log_new_lines()
                log_error(
                    f"The software, due to how it works, cannot have duplicated files in {Infos.PROJECT_NAME} "
                    f"directory, and subdirectories.")
                sys.exit(1)


def print_log_setup():
    log_new_lines(print_in_console=True)
    log(
        "Welcome to the Windows Update Server Setup. This software will help you to install Windows Update on "
        "all computers of your network.", print_formatted=False)

    log_new_lines(print_in_console=True)

    log("Please, make sure that all computers are connected to the same network, and all pc that interact with the "
        "software have a static local ip address.", print_formatted=False)
    log("The software will await you to install the client setup (powershell script) on each pc "
        "you desire to automate the update on.", print_formatted=False)

    log_new_lines(print_in_console=True)
    log("A http server will be created temporarily to allow the client to send connexion data to the server.",
        print_formatted=False)

    log_new_lines(print_in_console=True)

    log("Please, enter (y) when you are ready to start the setup, 'exit' to cancel.", print_formatted=False)
    print()


def setup_email_config_done() -> bool:
    service_id = "UpdateGuardian"
    email_infos_file: str | None = find_file("email_infos.json")
    if email_infos_file is None:
        log_error("Error: The file email_infos.json is missing.", print_formatted=False)
        return False

    with open(email_infos_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        email = data.get("email", None)
        email_send = data.get("send_mail", None)

        if email_send is None:
            log_error("Error: The send_mail key is missing in the email_infos.json file.", print_formatted=False)
            return False
        if email_send is True and email is None:
            log_error("Error: The email key is missing in the email_infos.json file.", print_formatted=False)
            return False
        if email_send is False:
            # Setup done but no email registered
            return True
        if email is None:
            log_error("Error: The email is not saved in the email_infos.json file.", print_formatted=False)
            return False
        if "@" not in email or "." not in email:
            log_error("Error: The email is not valid.", print_formatted=False)
            return False
        if keyring.get_password(service_id, email) is None:
            log_error("Error: The password for the email is not saved in the keyring.", print_formatted=False)
            return False
        elif data.get("password", None) is None:
            log_error("Error: The password for the email is not saved in the email_infos.json file in a linux "
                      "environnement.",
                      print_formatted=False)
            return False

    return True


def server_setup() -> bool:
    check_all_files_integrity()
    if not check_if_setup_needed():
        return True

    log("Setting up server...", print_formatted=False)

    current_ip = get_local_ipv4_address()
    update_powershell_client_script_ip(current_ip)

    print_log_setup()

    usr_input: str = input("> ")

    while usr_input != "y":
        usr_input: str = input("> ")
        if usr_input == "exit":
            log("Setup cancelled. Exiting...")
            exit(0)
        if usr_input != "y":
            log_error("Error: Invalid input. Please enter 'y' to continue, or 'exit' to cancel.", print_formatted=False)

    log_new_lines(print_in_console=True)
    log("Starting setup...", print_formatted=False)
    log("Scanning network... and setting up http server...", print_formatted=False)

    log_new_lines(print_in_console=True)
    log("Please press ctrl+c to stop the http server and continue the setup process once all desired computers has "
        "been registered...", print_formatted=False)

    if not run_server():
        log_error("Error with the http server. The database may be empty, or something else went wrong.",
                  print_formatted=False)
        return False

    return True


def load_launch_time() -> dict:
    with open(launch_infos_filename, "r") as file:
        return json.load(file)


def ask_and_save_launch_time():
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    while True:
        try:
            day = input("Please enter the day of the week to launch the program (e.g., Monday): ")
            day = day.capitalize()
            if day not in days_of_week:
                raise ValueError
        except ValueError:
            log_error("Invalid day input. Please enter a valid day of the week.")
        else:
            break

    while True:
        try:
            hour = int(input("Please enter the hour (0-23) to launch the program: "))
            if hour < 0 or hour > 23:
                raise ValueError
        except ValueError:
            log_error("Invalid hour input. Please enter a valid hour between 0 and 23.")
        else:
            break

    launch_time = {
        'day': day,
        'hour': hour
    }

    with open(launch_infos_filename, "w") as file:
        json.dump(launch_time, file, indent=4)

    return launch_time


def get_launch_time() -> dict[str, str]:
    if find_file(launch_infos_filename):
        return load_launch_time()

    return ask_and_save_launch_time()


def check_if_setup_needed() -> bool:
    if find_file("computers_database.json", show_print=False) is None:
        return True
    return False


def update_powershell_client_script_ip(ip: str):
    """
    Updates the ip variable in the powershell script.
    :param ip: The ip to update
    :return: Nothing.
    """

    try:
        powershell_file = find_file(Infos.powershell_client_script_installer_name)

        # Read the existing PowerShell script
        with open(powershell_file, 'r') as f:
            powershell_script = f.read()

        # Replace the existing IP address or set a new one
        powershell_script = re.sub(r'\$server_ip\s*=\s*".*"', f'$server_ip = "{ip}"', powershell_script)

        # Write the updated script to the file
        with open(powershell_file, 'w') as f:
            f.write(powershell_script)

        log(f"Powershell script updated successfully with the {ip} IP address as server.", print_formatted=False)
    except FileNotFoundError:
        log_error("Failed to update the powershell script. Make sure you run this script with administrative "
                  "privileges.\nFurthermore, make sure that the powershell script name "
                  f"{Infos.powershell_client_script_installer_name} exists in the {Infos.PROJECT_NAME} root folder.")
        raise FileNotFoundError
