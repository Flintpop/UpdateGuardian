import json
import re
import socket

import keyring

from src.newServer.infrastructure.config import Infos
from src.newServer.infrastructure.http_server_setup import run_server
from src.newServer.infrastructure.paths import ServerPath
from src.newServer.logs_management.server_logger import log_error, log, log_new_lines
from src.newServer.report.mails import setup_email_config


def load_launch_time() -> dict:
    with open(ServerPath.get_launch_time_filename(), "r") as file:
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

    with open(ServerPath.get_launch_time_filename(), "w") as file:
        json.dump(launch_time, file, indent=4)

    return launch_time


def check_if_setup_needed() -> bool:
    """
    Checks if the setup is needed. True if the setup of the application regarding
     computers registration. False if the setup is already done, i.e. : already at least one computer registered.
    """
    if ServerPath.exists(ServerPath.get_database_path()) is False:
        return True
    return False


def setup_config():
    """
    Sets up the configuration file for the server.
    """
    log("Setting up the configuration file...", print_formatted=False)
    print("How many computers do you want to update at the same time ?")
    max_computers = input("> ")
    if not max_computers.isdigit():
        log_error("Error: Invalid input. Please enter a number.")
        return setup_config()

    max_computers = int(max_computers)

    if max_computers < 1:
        log_error("Error: The number of computers must be at least 1.")
        return setup_config()

    # Dump the config file as json

    config = {
        "max_computers_per_iteration": max_computers
    }

    with open(ServerPath.get_config_json_file(), "w") as file:
        json.dump(config, file, indent=4)


class SetupManager:
    def __init__(self):
        pass

    # Initialisation des attributs nécessaires

    def server_setup(self) -> bool:
        if not self.is_launch_time_setup() and not ask_and_save_launch_time():
            return False

        if not self.setup_email_config_done():
            setup_email_config()

        if not self.is_settings_configured():
            setup_config()

        if check_if_setup_needed() and not self.register_computers_first_time():
            return False

        return True

    def register_computers_first_time(self):
        log("Setting up server...", print_formatted=False)

        current_ip = self.get_local_ipv4_address()
        self.update_powershell_client_script_ip(current_ip)

        self.print_log_setup()

        usr_input: str = input("> ")

        while usr_input != "y":
            usr_input: str = input("> ")
            if usr_input == "exit":
                log("Setup cancelled. Exiting...")
                exit(0)
            if usr_input != "y":
                log_error("Error: Invalid input. Please enter 'y' to continue, or 'exit' to cancel.",
                          print_formatted=False)

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

    @staticmethod
    def get_launch_time():
        if ServerPath.exists(ServerPath.get_launch_time_filename()):
            return load_launch_time()

        return ask_and_save_launch_time()

    @staticmethod
    def is_launch_time_setup():
        return ServerPath.exists(ServerPath.get_launch_time_filename())

    @staticmethod
    def setup_email_config_done() -> bool:
        service_id = "UpdateGuardian"
        email_infos_file: str | None = ServerPath.get_email_infos_json_file()
        email_infos_file_exists: bool = ServerPath.exists(email_infos_file)

        if email_infos_file_exists is None or not email_infos_file_exists:
            # Setup not done
            return False

        with open(email_infos_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            email = data.get("email", None)
            email_send = data.get("send_mail", None)

            if email_send is None:
                log_error("Error: The send_mail key is missing in the email_infos.json file.", print_formatted=False)
                return False

            Infos.email_send = email_send

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
                          "environnement, nor in the keyring.",
                          print_formatted=False)
                return False

        Infos.email = email_send
        return True

    @staticmethod
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

    @staticmethod
    def update_powershell_client_script_ip(ip: str):
        """
        Updates the ip variable in the powershell script.
        :param ip: The ip to update
        :return: Nothing.
        """

        try:
            powershell_client_path = ServerPath.get_powershell_client_script_installer_path()

            if not ServerPath.exists(powershell_client_path):
                raise FileNotFoundError(f"The client \n"
                                        f"'{powershell_client_path}'\n"
                                        f" powershell script does not exist.")

            # Read the existing PowerShell script
            with open(powershell_client_path, 'r') as f:
                powershell_script = f.read()

            # Replace the existing IP address or set a new one
            powershell_script = re.sub(r'\$server_ip\s*=\s*".*"', f'$server_ip = "{ip}"', powershell_script)

            # Write the updated script to the file
            with open(powershell_client_path, 'w') as f:
                f.write(powershell_script)

            log(f"Powershell script updated successfully with the {ip} IP address as server.", print_formatted=False)
        except FileNotFoundError:
            log_error("Failed to update the powershell script. Make sure you run this script with administrative "
                      "privileges.\nFurthermore, make sure that the powershell script name "
                      f"{Infos.powershell_client_script_installer_name} exists in the {Infos.PROJECT_NAME} root folder.")
            raise FileNotFoundError

    @staticmethod
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

    @staticmethod
    def is_settings_configured():
        return ServerPath.exists(ServerPath.get_config_json_file())
