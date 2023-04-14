import threading
import socket


import paramiko

from src.server.commands.install_update_win_util import check_python_script_installed, install_python_script
from src.server.data.local_network_data import Data
from src.server.ssh.ssh_connect import ssh_connect


def install_windows_update_all_pc(data: Data):
    max_computers_per_iteration = data.get_max_computers_per_iteration()
    threads: list[threading.Thread] = []

    for i in range(0, max_computers_per_iteration):
        threads.append(
            threading.Thread(target=install_windows_update, args=(data, i)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def ssh_connexion_via_index(data: Data, i: int) -> paramiko.SSHClient:
    remote_user = data.get_data_json().get("remote_user")[i]
    remote_password = data.get_data_json().get("remote_password")[i]
    remote_host = data.get_data_json().get("remote_host")[i]
    return ssh_connect(remote_user=remote_user, remote_password=remote_password, remote_host=remote_host)


def wake_up_pc(ip_address: str):
    """
    Turn on the pc to update windows.
    # TODO:
    :return: ?
    """
    pass


def connect_to_remote_computer(ssh: paramiko.SSHClient) -> socket.socket:
    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 12345))
    server.listen(5)

    print("Serveur en écoute sur le port 12345")
    return server


def install_windows_update(data: Data, i: int):
    n_computers = data.get_number_of_computers()
    max_computers_per_iteration = data.get_max_computers_per_iteration()
    for j in range(i, n_computers, max_computers_per_iteration):
        print("Installing Windows Update on pc " + str(j) + "...")
        wake_up_pc("")

        print("Connecting to pc '" + str(i) + "' of ip address '" + data.get_ip_address(i) + "'")
        ssh = ssh_connexion_via_index(data, j)

        print("Connected to pc '" + str(i) + "' of ip address '" + data.get_ip_address(i) + "'")
        installed: bool = check_python_script_installed(data.get_python_script_path(), ssh)

        if not installed:
            install_python_script(data, ssh)

        # socket = connect_to_remote_computer(ssh)
        #
        # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.bind(('0.0.0.0', 12345))
        # server.listen(5)
        #
        # print("Serveur en écoute sur le port 12345")
        #
        # client_socket, client_address = server.accept()
        # print(f"Connexion établie avec {client_address}")

        # send_installation_flag(socket)

        print("Windows Update installed successfully")


if __name__ == '__main__':
    data_test: Data = Data("computers_informations.json")
    install_windows_update(data_test, 0)
