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


def send_wol(mac_address: str, ip_address: str, port: int = 9) -> bool:
    send_magic_packet(mac_address, ip_address=ip_address, port=port)
    return True


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


def get_gateway_ip():
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
