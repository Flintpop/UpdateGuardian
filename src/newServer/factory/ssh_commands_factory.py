import paramiko

from src.newServer.ssh.commands import SSHCommands, SSHCommandExecutor


class SSHCommandsFactory:
    """
    This class is a factory for creating SSHCommands objects.
    """

    @staticmethod
    def create(ssh: paramiko.SSHClient) -> SSHCommands:
        """
        Creates an SSHCommands object.
        :param ssh: The ssh session.
        :return: The SSHCommands object.
        """
        ssh_command_executor: SSHCommandExecutor = SSHCommandExecutor(ssh)
        return SSHCommands(ssh_command_executor)
