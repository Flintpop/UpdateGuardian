import logging
import socket
import sys

from update_windows import start_client_update

logging.basicConfig(level=logging.INFO, filename="update_windows.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")


def add_spaces_logging_file() -> None:
    write_spaces: bool = False
    with open("update_windows.log", "r") as f:
        if len(f.readline()) > 1:
            write_spaces = True

    if write_spaces:
        with open("update_windows.log", "a") as f:
            f.write("\n\n")


def print_and_log(message: str, level: str = "info") -> None:
    print(message)
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)


def main_loop() -> None:
    # Lancer les mises à jour avec la fonction update_windows() définie précédemment
    add_spaces_logging_file()

    logging.info("Starting client update script...")
    if len(sys.argv) != 3:
        print_and_log("Please, enter the server ip and the server port.", "error")
        print_and_log("Example: python main_client.py", "error")
        sys.exit(1)

    # Se connecter au serveur
    server_ip: str = sys.argv[1]
    server_port: int = int(sys.argv[2])
    print_and_log(f"Connecting to server {server_ip}:{server_port}...")
    # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client.connect((server_ip, server_port))

    print_and_log("Connected to server.")

    start_client_update()

    # client.close()


if __name__ == '__main__':
    main_loop()
