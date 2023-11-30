from src.newServer.core.computer import Computer
from src.newServer.ssh.commands import SSHCommands


class RemoteComputerManager:
    def __init__(self, computer: 'Computer', ssh_commands: 'SSHCommands') -> None:
        self.computer = computer
        self.ssh_commands = ssh_commands
        