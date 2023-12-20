import paramiko

from newServer.infrastructure.paths import ServerPath
from newServer.core.computer import Computer


class SSHConnect:
    @staticmethod
    def private_key_connexion(computer: 'Computer', private_key) -> paramiko.SSHClient or False:
        """
        Connect to a computer via SSH.
        Nothing is checked here, the connection is made with the given parameters.
        Make sure to check the parameters before calling this method.
        """
        hostname, username = computer.hostname, computer.username

        ssh_session = paramiko.SSHClient()
        ssh_session.set_missing_host_key_policy(paramiko.RejectPolicy())
        ssh_session.load_host_keys(ServerPath.join(ServerPath.get_home_path(), ".ssh", "known_hosts"))
        ssh_session.connect(hostname=hostname, username=username, pkey=private_key)
        return ssh_session
