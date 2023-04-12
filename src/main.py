from src.data.generate_json import generate_json
from src.powershell.install_update import install_windows_update_all_pc
from src.ssh.ssh_connect import get_number_of_computers
from src.data.local_network_data import Data


def launch_software(data: Data) -> None:
    data_json = data.get_data_json()
    n_computers = get_number_of_computers(data_json)
    print("Number of computers: " + str(n_computers))

    print("Installing Windows Update on all computers...")

    install_windows_update_all_pc(data.get_max_computers_per_iteration(), n_computers)


def main_loop() -> None:
    generate_json(13)
    data = Data('test.json')

    launch_software(data)


if __name__ == '__main__':
    main_loop()
