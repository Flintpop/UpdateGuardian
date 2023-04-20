import os
import threading

import paramiko

from src.server.commands.find_all_pc import generate_ip_range, scan_network
from src.server.commands.install_client_files_and_dependencies import check_and_install_client_setup, \
    wait_for_ssh_shutdown
from src.server.commands.path_functions import find_file
from src.server.config import Infos
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import stdout_err_execute_ssh_command, wait_and_reconnect, is_ssh_server_available
from src.server.ssh.ssh_connect import ssh_connect
from src.server.wake_on_lan.wake_on_lan_utils import send_wol


def generate_port_list(max_computers_per_iteration: int) -> list[int]:
    port_list: list[int] = []
    start_port: int = 12346
    for i in range(0, max_computers_per_iteration):
        port_list.append(start_port + i)
    return port_list


def refresh_ip_addresses_database(data: Data):
    ip_range_test = generate_ip_range("192.168.7.220", "192.168.7.253")

    hosts_refreshed = scan_network(ip_range_test)
    old_hosts = data.computers_data
    for host in hosts_refreshed.keys():
        if host in old_hosts:
            old_hosts[host]["ip"] = hosts_refreshed[host]["ip"]

    data.save_computer_data()


def install_windows_update_all_pc(data: Data) -> None:
    print("Updating ip addresses database...")
    refresh_ip_addresses_database(data)
    print("Checking for updates on all pc...")

    max_computers_per_iteration = data.get_max_computers_per_iteration()
    threads: list[threading.Thread] = []
    port_list: list[int] = generate_port_list(max_computers_per_iteration)

    for i in range(0, max_computers_per_iteration):
        print("Starting thread " + str(i + 1) + "...")
        threads.append(
            threading.Thread(target=install_windows_update, args=(data, i, port_list[i])))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def ssh_connexion_via_index(data: Data, i: int) -> paramiko.SSHClient | None:
    try:
        computer_connexion_data = data.get_computer_info(i)
        remote_user = computer_connexion_data.get("username")
        remote_passwords = computer_connexion_data.get("password")
        remote_host = computer_connexion_data.get("ip")
        return ssh_connect(remote_user=remote_user, remote_passwords=remote_passwords, remote_host=remote_host)
    except TimeoutError:
        print("Timeout error, the pc is probably off")
        return None
        # try:
        #     wake_up_pc(data.get_data_json().get("remote_host")[i])
        # except TimeoutError:
        #     print("Error, IP address or password are probably not valid.")
        #     return None


def wake_up_pc(computer_info: dict[str, str, str, str]) -> bool:
    """
    Turn on the pc to update windows.
    :return: True if the pc is on, False otherwise.
    """
    print("Waking up the pc...")

    mac_address: str = computer_info.get("mac_address")
    send_wol(mac_address)

    print("The pc should be awake...")

    # TODO: Not tested timeout
    if not is_ssh_server_available(computer_info.get("ip"), timeout=60):
        print("Error, the pc is still off.")
        return False
    return True


def start_python_scripts(ssh: paramiko.SSHClient, python_main_script_path: str,
                         server_ip_address: str, port: int) -> None | str:
    print("Starting the python script...")
    command: str = "cd " + Infos.project_name + " && python " + python_main_script_path + " " + \
                   server_ip_address + " " + str(port)

    stdout, stderr = stdout_err_execute_ssh_command(ssh, command)

    print("Python script started.")

    if stderr:
        print("Stderr:")
        print(stderr)
        return None
    if stdout:
        print("Stdout:")
        print(stdout)
    return stdout


def check_pc_is_on(computer_info: dict[str, str, str]):
    return is_ssh_server_available(computer_info.get("ip"))


def install_windows_update(data: Data, i: int, port: int):
    n_computers = data.get_number_of_computers()
    max_computers_per_iteration = data.get_max_computers_per_iteration()

    for j in range(i, n_computers, max_computers_per_iteration):
        current_computer_info: dict = data.get_computer_info(j)
        
        if current_computer_info is None:
            print("Error, could not find computer info for pc " + str(j) + ".")
            continue
            
        client_number = j + 1
        print("Installing Windows Update on pc " + str(j) + "...")

        if not check_pc_is_on(current_computer_info):
            print(f"Client {client_number} is off, trying to wake it up...")
            wake_up_pc(current_computer_info.get("mac"))

        print("Connecting to pc '" + str(client_number) + "' of ip address '" + data.get_ip_address(i) + "'")
        ssh = ssh_connexion_via_index(data, j)

        if ssh is None:
            print(f"Connection failed on pc {client_number} of ip address {data.get_ip_address(i)}")
            continue

        print("Connected to pc '" + str(client_number) + "' of ip address '" + data.get_ip_address(i) + "'")

        client_is_setup: bool = check_and_install_client_setup(ssh, data, j)
        if not client_is_setup:
            print(f"Client setup {client_number} failed")
            continue

        main_path: str = os.path.join(data.get_python_script_path(), "main_client.py")

        stdout = start_python_scripts(ssh, main_path, Data.server_ip_address, port)

        if stdout is not None and "reboot" in stdout:
            ssh.close()
            ipaddress, remote_user, remote_password = data.get_client_info(i)
            wait_for_ssh_shutdown(ipaddress)
            reconnected: bool = wait_and_reconnect(ssh, ipaddress, remote_user, remote_password)
            if reconnected:
                print("Windows Update installed successfully on pc " + str(client_number))
            else:
                print("Error while trying to reconnect to the pc " + str(client_number))
                print("Updates may or may not have been installed.")


if __name__ == '__main__':
    data_test: Data = Data(find_file("computers_informations.json"))
    install_windows_update(data_test, 0, 12345)
