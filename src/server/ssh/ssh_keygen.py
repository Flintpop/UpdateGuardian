# -----------------------------------------------------------
# ssh_keygen.py
# Author: darwh
# Date: 02/05/2023
# Description: Used to generate ssh keys for the server.
# -----------------------------------------------------------
import base64
import os
import stat
import subprocess

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, NoEncryption

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.environnement.server_logs import log, log_error


def create_known_hosts_file() -> None:
    user_path = os.environ["USERPROFILE"]
    known_hosts_file = open(os.path.join(user_path, ".ssh", "known_hosts"), "w")
    known_hosts_file.close()


def gen_keys_and_save_them(computer: 'Computer', host_key: str) -> None:
    """
    Generate and saves a new ED25519 private key and its public key.
    :param computer: The computer object to which the keys will be saved.
    :param host_key: The host key to save in the ssh client that will connect to many servers.
    :return:
    """
    # Generate an RSA private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    private_key_file: str = computer.private_key_filepath
    public_key_file: str = computer.public_key_filepath

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

    add_key = subprocess.run("ssh-add \"" + private_key_file + "\"", shell=True, check=True)

    if add_key.returncode != 0:
        log_error(f"An error occurred while adding the private key to the ssh agent. Error code: {add_key.returncode}.",
                  print_formatted=False)

    delete_key = subprocess.run(f"del \"{private_key_file}\"", shell=True, check=True)

    if delete_key.returncode != 0:
        log_error(f"An error occurred while deleting the private key from the server. Error code: "
                  f"{delete_key.returncode}.", print_formatted=False)

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

    print(host_key)
    host_key_data_decoded = base64.b64decode(host_key.split(' ')[1].encode('ascii'))
    host_key_raw = paramiko.Ed25519Key(data=host_key_data_decoded)
    print()

    user_directory: str = os.environ["USERPROFILE"]
    ssh_user_directory: str = os.path.join(user_directory, ".ssh")
    if not os.path.exists(ssh_user_directory):
        log("The .ssh folder does not exists, creating it...", "warning", print_formatted=False)
        os.mkdir(ssh_user_directory)
        create_known_hosts_file()

    if not os.path.exists(os.path.join(ssh_user_directory, "known_hosts")):
        log("The known_hosts file does not exists, creating it...", "warning", print_formatted=False)
        create_known_hosts_file()

    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys(os.path.join(ssh_user_directory, "known_hosts"))  # Load the existing known_hosts file
    ssh_client.get_host_keys().add(computer.hostname, 'ssh-ed25519', host_key_raw)

    ssh_client.save_host_keys(os.path.join(user_directory, ".ssh", "known_hosts"))  # Save the updated known_hosts file

    log(f"Private and public ed25519 keys have been generated and saved to files and ssh-agent "
        f"for computer {computer.hostname}.", print_formatted=False)
