from wakeonlan import send_magic_packet
import platform
import re
import subprocess


def is_secureon_password_valid(secureon_password: str) -> bool:
    # Vérifier que le mot de passe SecureOn a 12 caractères hexadécimaux et les sépare par des deux-points
    length_secureon_password = 17
    if len(secureon_password) != length_secureon_password:
        return False

    # Utiliser une expression régulière pour vérifier le format
    regex_pattern = r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$"
    match = re.match(regex_pattern, secureon_password)

    return match is not None


def send_wol_with_secureon(mac_address: str, secureon_password: str) -> None:
    # Vérifier l'intégrité du mot de passe SecureOn
    if not is_secureon_password_valid(secureon_password):
        raise ValueError("Le mot de passe SecureOn est invalide.")

    # Envoyer le paquet magique avec le mot de passe SecureOn
    send_magic_packet(f"{mac_address}/{secureon_password}")


def send_wol(ip_address: str) -> None:
    # TODO: Change that because test
    mac_address: str = get_mac_address(ip_address)
    send_magic_packet(mac_address)


def ping_ip(ip_address: str) -> bool:
    if platform.system() == 'Windows':
        ping_command = ['ping', '-n', '1', '-w', '1000', ip_address]
    else:
        ping_command = ['ping', '-c', '1', '-W', '1', ip_address]

    try:
        _ = subprocess.check_output(ping_command, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError:
        print(f"Erreur lors du ping de {ip_address}")
        return False

    return True


def get_mac_address(ip_address: str) -> str | None:
    if not ping_ip(ip_address):
        print("Impossible de récupérer l'adresse MAC car l'ordinateur est éteint.")
        return None

    try:
        if platform.system() == 'Windows':
            arp_output = subprocess.check_output(['arp', '-a', ip_address], text=True)
            mac_address = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", arp_output, re.IGNORECASE).group()
        else:
            arp_output = subprocess.check_output(['arp', '-n', ip_address], text=True)
            mac_address = re.search(r"(([a-f\d]{1,2}:){5}[a-f\d]{1,2})", arp_output, re.IGNORECASE).group()
    except subprocess.CalledProcessError:
        print(f"Erreur lors de la récupération de l'adresse MAC pour {ip_address}")
        mac_address = None
    except AttributeError:
        print(f"Impossible de trouver l'adresse MAC pour {ip_address}")
        mac_address = None

    return mac_address


def get_mac_addresses(ip_addresses: list[str]) -> dict:
    mac_addresses = {}
    for current_ip in ip_addresses:
        current_mac = get_mac_address(current_ip)
        if current_mac:
            mac_addresses[current_ip] = current_mac

    return mac_addresses


def get_router_ip():
    router_ip = None

    try:
        if platform.system() == 'Windows':
            output = subprocess.check_output(['ipconfig'], text=True)
            regex_pattern = r"Default Gateway[^\n]*\n[^\d]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            try:
                router_ip = re.search(regex_pattern, output, re.IGNORECASE).group(1)
            except AttributeError:
                # Check if the ipconfig returned french text
                regex_pattern = r"Passerelle par défaut[^\n]*\n[^\d]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                router_ip = re.search(regex_pattern, output, re.IGNORECASE).group(1)
        else:
            output = subprocess.check_output(['route', '-n'], text=True)
            regex_pattern = r"^0\.0\.0\.0\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            router_ip = re.search(regex_pattern, output, re.IGNORECASE).group(1)
    except subprocess.CalledProcessError:
        print("Erreur lors de la récupération de l'adresse IP du routeur.")
    except AttributeError:
        print("Impossible de trouver l'adresse IP du routeur.")

    return router_ip


# Exemple d'utilisation
if __name__ == "__main__":
    print()
    print("Adresse du routeur : ", get_router_ip())
    print()
    ip_list = ["192.168.7.227"]
    mac_list = get_mac_addresses(ip_list)

    for ip, mac in mac_list.items():
        print(f"{ip} -> {mac}")
