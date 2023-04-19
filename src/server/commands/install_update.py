import os
import threading
import socket

import paramiko

from src.server.commands.install_client_files_and_dependencies import check_and_install_client_setup, \
    wait_for_ssh_shutdown
from src.server.commands.path_functions import find_file
from src.server.config import Infos
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_commands import stdout_err_execute_ssh_command, wait_and_reconnect
from src.server.ssh.ssh_connect import ssh_connect
from src.server.wake_on_lan.wake_on_lan_utils import send_wol


def generate_port_list(max_computers_per_iteration: int) -> list[int]:
    port_list: list[int] = []
    start_port: int = 12346
    for i in range(0, max_computers_per_iteration):
        port_list.append(start_port + i)
    return port_list


def install_windows_update_all_pc(data: Data) -> None:
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
        remote_user = data.get_data_json().get("remote_user")[i]
        remote_passwords = data.get_data_json().get("remote_passwords")[i]
        remote_host = data.get_data_json().get("remote_host")[i]
        return ssh_connect(remote_user=remote_user, remote_passwords=remote_passwords, remote_host=remote_host)
    except TimeoutError:
        pass
        # print("Timeout error, the pc is probably off, trying to wake it up...")
        # try:
        #     wake_up_pc(data.get_data_json().get("remote_host")[i])
        # except TimeoutError:
        #     print("Error, IP address or password are probably not valid.")
        #     return None


def wake_up_pc(ip_address: str) -> None:
    """
    Turn on the pc to update windows.
    :return: Void
    """
    print("Waking up the pc...")
    send_wol(ip_address)
    print("The pc is now awake.")


def connect_to_remote_computer() -> socket.socket:
    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 12345))
    server.listen(5)

    print("Serveur en écoute sur le port 12345")
    return server


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


def create_socket_server(server_ip_address: str, port: int) -> socket.socket:
    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip_address, port))
    server.listen(1)

    print("Server listening on port " + str(port))
    return server


def install_windows_update(data: Data, i: int, port: int):
    n_computers = data.get_number_of_computers()
    max_computers_per_iteration = data.get_max_computers_per_iteration()

    for j in range(i, n_computers, max_computers_per_iteration):
        client_number = j + 1
        print("Installing Windows Update on pc " + str(j) + "...")
        # TODO: Building so remove mac address later
        # wake_up_pc("c8-60-00-38-64-79")

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

    # send_wol("c8-60-00-38-64-79")
