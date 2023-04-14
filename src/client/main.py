import socket


def main_loop() -> None:
    # Lancer les mises à jour avec la fonction update_windows() définie précédemment

    # Se connecter au serveur
    server_ip = "192.168.7.225"
    server_port = 12345
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    print("Connected to server.")
    # Votre logique de communication avec le serveur
    # Par exemple, envoyer des résultats de mise à jour, etc.

    # Fermer la connexion une fois terminé
    client.close()


if __name__ == '__main__':
    main_loop()
