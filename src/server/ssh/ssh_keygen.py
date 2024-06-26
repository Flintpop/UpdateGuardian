# -----------------------------------------------------------
# ssh_keygen.py
# Author: darwh
# Date: 02/05/2023
# Description: Used to generate ssh keys for the server.
# -----------------------------------------------------------
import base64
import os
import stat

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, NoEncryption

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.core.remote_computer_manager import RemoteComputerManager
from src.server.infrastructure.paths import ServerPath

from src.server.logs_management.server_logger import log


def create_known_hosts_file() -> None:
    """
    Creates the known_hosts file in the .ssh folder.
    """
    user_path = ServerPath.get_home_path()
    known_hosts_file = open(ServerPath.join(user_path, ".ssh", "known_hosts"), "w")
    known_hosts_file.close()


def gen_keys_and_save_them(computer: 'RemoteComputerManager', host_key: str) -> None:
    """
    Generate and saves a new ED25519 private key and its public key.
    :param computer: The computer object to which the keys will be saved.
    :param host_key: The host key to save in the ssh client that will connect to many servers.
    :return: None
    """
    # Generate an RSA private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    private_key_file: str = computer.get_private_key_filepath()
    public_key_file: str = computer.get_public_key_filepath()

    # Serialize the private key to OpenSSH format
    private_openssh = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=NoEncryption(),
    )

    # Save the private key to a file in OpenSSH format
    with open(private_key_file, "wb") as f:
        f.write(private_openssh)

    os.chmod(private_key_file, stat.S_IRUSR | stat.S_IWUSR)

    # Get the public key from the private key
    public_key = private_key.public_key()

    # Serialize the public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=Encoding.OpenSSH,
        format=PublicFormat.OpenSSH,
    )

    # Save the public key to a file
    with open(public_key_file, "wb") as f:
        f.write(public_pem)

    host_key_data_decoded = base64.b64decode(host_key.split(' ')[1].encode('ascii'))
    host_key_raw = paramiko.Ed25519Key(data=host_key_data_decoded)
    print()

    # Add the host key to the ssh client
    user_directory: str = ServerPath.get_home_path()
    ssh_user_directory: str = ServerPath.join(user_directory, ".ssh")
    if not os.path.exists(ssh_user_directory):
        log("The .ssh folder does not exists, creating it...", "warning", print_formatted=False)
        os.mkdir(ssh_user_directory)
        create_known_hosts_file()

    if not os.path.exists(ServerPath.join(ssh_user_directory, "known_hosts")):
        log("The known_hosts file does not exists, creating it...", "warning", print_formatted=False)
        create_known_hosts_file()

    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys(ServerPath.join(ssh_user_directory, "known_hosts"))  # Load the existing known_hosts file
    ssh_client.get_host_keys().add(computer.get_hostname(), 'ssh-ed25519', host_key_raw)

    # Save the updated known_hosts file
    ssh_client.save_host_keys(ServerPath.join(user_directory, ".ssh", "known_hosts"))

    log(f"Private and public ed25519 keys have been generated and saved to files and ssh-agent "
        f"for computer {computer.get_hostname()}.", print_formatted=False)
