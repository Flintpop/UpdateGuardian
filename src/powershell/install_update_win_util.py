import paramiko


def install_update_manager(ssh: paramiko.SSHClient) -> None:
    """
    Installs the update manager on the remote computer if not already installed.
    This will be used by ssh, and then powershell to update Windows computers.
    """
    pass
