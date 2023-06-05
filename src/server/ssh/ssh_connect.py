import paramiko
import chardet

from src.server.Exceptions.DecodingExceptions import DecodingError


def execute_and_get_all_decoded_streams_ssh(ssh: paramiko.SSHClient, command: str) -> tuple[str, str, str]:
    stdin, stdout, stderr = ssh.exec_command(command)
    return decode_all_ssh_streams(stdin, stdout, stderr)


def decode_stream(stream) -> str | None:
    if stream is None or stream == b'':
        return None

    encodings = ['cp850', chardet.detect(stream)['encoding'], 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16', 'utf-32']

    for encoding in encodings:
        try:
            return stream.decode(encoding, errors="replace").strip().replace("\r\n", "\n").replace("\r", "")
        except UnicodeDecodeError:
            pass

    raise DecodingError("None of the tested encodings were able to decode the stream")


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
    _, stdout, _ = ssh.exec_command(command)
    return decode_stream(stdout.read())
