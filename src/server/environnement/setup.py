import json
import os
import socket
import sys

from src.server.commands.find_all_pc import scan_network
from src.server.commands.path_functions import find_file, list_files_recursive, find_directory
from src.server.config import Infos
from src.server.data.computer_database import ComputerDatabase
from src.server.data.load_pc_passwords import find_password
from src.server.data.local_network_data import Data
from src.server.wake_on_lan.wake_on_lan_utils import ping_ip
from src.server.environnement.server_logs import log, log_error, log_new_lines

launch_infos_filename: str = "launch_infos.json"


def add_encrypted_passwords(data: Data, hosts: dict):
    # TODO: Encrypt passwords
    for computer in hosts.values():
        computer['password'] = find_password(data, computer["ip"])


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


def delete_unwanted_hosts(data: Data, hosts: dict):
    items_to_delete: list = []
    current_ip = get_local_ipv4_address()

    if current_ip is None:
        log_error("Error, could not get the local ip address.")

    taken_ips = data.get_data_json().get("taken_ips")
    if current_ip not in taken_ips:
        taken_ips.append(current_ip)

    for taken_ip in taken_ips:
        for hostname in hosts.keys():
            host = hosts[hostname]
            if host["ip"] == taken_ip:
                items_to_delete.append(hostname)

    for item in items_to_delete:
        hosts.pop(item)


def check_all_hosts_are_valid(ips: list[str], return_invalid_hosts: list[str]):
    for ip in ips:
        if not ping_ip(ip):
            log_error(f"Error: {ip} is not reachable.")
            return_invalid_hosts.append(ip)

    if len(return_invalid_hosts) > 0:
        return False
    return True


def add_usernames_hosts(data: Data, hosts: dict) -> bool:
    for hostname in hosts.keys():
        host = hosts[hostname]
        username = data.get_username_per_ip(host["ip"])
        if username is None:
            log_error(f"Error: could not find a username for {host['ip']}.")
            return False
        host["username"] = username
    return True


def get_all_files_from_server() -> list[str]:
    directory = find_directory("UpdateGuardian")
    files = list_files_recursive(directory)
    cur_sep = os.path.sep
    exceptions = ["HEAD", ".gitignore", ".git"]
    files_to_remove: list[str] = []
    for file in files:
        directories_and_files_of_file: list[str] = file.split(cur_sep)
        for exception in exceptions:
            if exception in directories_and_files_of_file and file in files:
                files_to_remove.append(file)

    # for file in files_to_remove:
    #     files.remove(file)

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
    log_new_lines()
    log(
        "Welcome to the Windows Update Server Setup. This software will help you to install Windows Update on "
        "all computers of your network.", print_formatted=False)

    log_new_lines()

    log("Please, make sure that all computers are connected to the same network.", print_formatted=False)
    log("Also, make sure you installed the Powershell script on all computers, and that Wake-on-lan is activated "
        "on each of them.", print_formatted=False)

    log_new_lines()

    log(
        "To scan the network and register mac addresses and hostnames, please turn on all computers that you "
        "wish to manage from this software. Be sure that all ipv4 addresses has been registered in "
        "'computer_informations.json' folder.", print_formatted=False
    )

    log_new_lines()

    log("Please, enter (y) when you are ready to start the setup, 'exit' to cancel.", print_formatted=False)
    print()


def server_setup(setup_data: Data):
    check_all_files_integrity()
    if not check_if_setup_needed():
        return

    log("Setting up server...")

    print_log_setup()

    usr_input: str = input("> ")

    while usr_input != "y":
        usr_input: str = input("> ")
        if usr_input == "exit":
            log("Setup cancelled. Exiting...")
            sys.exit(0)
        if usr_input != "y":
            log_error("Error: Invalid input. Please enter 'y' to continue, or 'exit' to cancel.", print_formatted=False)

    log_new_lines()
    log("Starting setup...", print_formatted=False)
    log("Scanning network...", print_formatted=False)
    ip_pool_range = setup_data.get_ip_range()

    hosts: dict = scan_network(ip_pool_range)

    list_invalid_hosts: list = []
    if not check_all_hosts_are_valid(setup_data.get_data_json().get("remote_host"), list_invalid_hosts):
        log_error("Error: Some hosts are not reachable. Please check your network and try again.")
        log_error("The following hosts are not reachable:")
        for host in list_invalid_hosts:
            log_error(host)
        log_error("Please modify the list of hosts in the file 'computers_informations.json' and try again.")
        sys.exit(1)

    log("Deleting unwanted hosts...", print_formatted=False)
    delete_unwanted_hosts(setup_data, hosts)

    log("Adding usernames...", print_formatted=False)
    if not add_usernames_hosts(setup_data, hosts):
        sys.exit(1)

    log("Adding passwords...", print_formatted=False)
    add_encrypted_passwords(setup_data, hosts)

    log("Creating database...", print_formatted=False)
    ComputerDatabase.save_computer_data(hosts)
    log_new_lines()


def load_launch_time() -> dict:
    with open(launch_infos_filename, "r") as file:
        return json.load(file)


def get_launch_time() -> dict[str, str]:
    if find_file(launch_infos_filename):
        return load_launch_time()

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


def check_if_setup_needed() -> bool:
    if find_file("computers_database.json", show_print=False) is None:
        return True
    return False
