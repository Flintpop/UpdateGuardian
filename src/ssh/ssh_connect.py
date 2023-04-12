import paramiko


def ssh_connect(cur_remote_host: str, cur_remote_user: str, cur_remote_password: str) -> paramiko.SSHClient:
    """
    Connect to a remote computer using SSH.
    :param cur_remote_host: The remote computer's IP address or hostname.
    :param cur_remote_user: The remote computer's username.
    :param cur_remote_password: The remote computer's password.
    :return: The SSH session.
    """
    ssh: paramiko.SSHClient = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Se connecter à la machine distante
    ssh.connect(cur_remote_host, username=cur_remote_user, password=cur_remote_password)
    return ssh


def get_number_of_computers(data_json: dict) -> int:
    try:
        return len(data_json.get("remote_user"))
    except TypeError:
        raise TypeError("The JSON file is empty.")
    except AttributeError:
        raise AttributeError("The JSON file wrongly formatted.")
