from src.server.data.local_network_data import Data
from src.server.data.generate_json import generate_json
from src.server.commands.install_update import install_windows_update_all_pc


def launch_software(data: Data) -> None:
    print("Installing Windows Update on all computers...")

    install_windows_update_all_pc(data)


def main_loop() -> None:
    generate_json(13)
    data = Data()

    launch_software(data)


if __name__ == '__main__':
    main_loop()
