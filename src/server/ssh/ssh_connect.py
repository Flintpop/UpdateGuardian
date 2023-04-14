import paramiko
import chardet


def ssh_connect(remote_host: str, remote_user: str, remote_password: str) -> paramiko.SSHClient:
    """
    Connect to a remote computer using SSH.
    :param remote_host: The remote computer's IP address or hostname.
    :param remote_user: The remote computer's username.
    :param remote_password: The remote computer's password.
    :return: The SSH session.
    """
    ssh: paramiko.SSHClient = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Se connecter à la machine distante
    ssh.connect(remote_host, username=remote_user, password=remote_password)
    return ssh


def execute_and_get_all_decoded_streams_ssh(ssh: paramiko.SSHClient, command: str) -> tuple[str, str, str]:
    stdin, stdout, stderr = ssh.exec_command(command)
    return decode_all_ssh_streams(stdin, stdout, stderr)


def decode_stream(stream) -> str | None:
    if stream is None or stream == b'':
        return None
    detected_encoding = chardet.detect(stream)['encoding']
    return stream.decode(detected_encoding).strip().replace("\n", "").replace("\r", "")


def decode_all_ssh_streams(stdin, stdout, stderr) -> tuple[str, str, str]:
    """
    Get the output of a command.
    :param stdin: The input stream.
    :param stdout: The output stream.
    :param stderr: The error stream.
    :return: The output of the command.
    """
    ssh_output = stdout.read()
    ssh_input = stdin.read()
    ssh_errors = stderr.read()
    detected_encoding = chardet.detect(ssh_output)['encoding']
    return ssh_input.decode(detected_encoding), ssh_output.decode(detected_encoding), ssh_errors.decode(
        detected_encoding)


def get_stdout_decoded_str(ssh: paramiko.SSHClient, command: str) -> str:
    """
    Get the output of a command.
    :param ssh: The SSH session.
    :param command: The command to execute.
    :return: The output of the command.
    """
    stdin, stdout, stderr = ssh.exec_command(command)
    return decode_stream(stdout.read())
