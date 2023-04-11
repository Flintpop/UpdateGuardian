from ssh.ssh_connect import ssh_connect, find_and_connect_all_remote_computers
from config import remote_command


def main_loop() -> None:
    find_and_connect_all_remote_computers()


if __name__ == '__main__':
    main_loop()
