from src.server.data.local_network_data import Data


def find_password(data: Data, ip_address: str) -> str:
    if ip_address in data.get_data_json()["remote_host"]:
        return data.get_passwords_with_ip(ip_address)
    else:
        return ""
