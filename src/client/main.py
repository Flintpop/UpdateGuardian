import socket

from update_windows import start_client_update


def main_loop() -> None:
    # Lancer les mises à jour avec la fonction update_windows() définie précédemment

    # Se connecter au serveur
    server_ip = "192.168.7.225"
    server_port = 12345
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    print("Connected to server.")

    start_client_update()

    # client.close()


if __name__ == '__main__':
    main_loop()
