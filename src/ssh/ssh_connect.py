import paramiko
from src.config import data_dict_json

from src.config import remote_host, remote_user, remote_password


def ssh_connect(cur_remote_host, cur_remote_user, cur_remote_password) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Se connecter à la machine distante
    ssh.connect(cur_remote_host, username=cur_remote_user, password=cur_remote_password)
    return ssh


def find_and_connect_all_remote_computers() -> list:
    ssh_sessions = []
    for i in range(len(data_dict_json.get("remote_user"))):
        ssh_sessions.append(ssh_connect(remote_host[i], remote_user[i], remote_password[i]))

    return ssh_sessions
