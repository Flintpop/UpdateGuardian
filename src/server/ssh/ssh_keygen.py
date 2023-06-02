# -----------------------------------------------------------
# ssh_keygen.py
# Author: darwh
# Date: 02/05/2023
# Description: Used to generate ssh keys for the server.
# -----------------------------------------------------------
import os
import stat
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, NoEncryption

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.environnement.server_logs import log, log_error


def gen_keys_and_save_them(computer: 'Computer') -> None:
    """
    Generate and saves a new ED25519 private key and its public key.
    :return:
    """
    # Generate an RSA private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    # private_key = rsa.generate_private_key(
    #     public_exponent=65537,
    #     key_size=4096,
    # )

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

    add_key = subprocess.run("ssh-add " + private_key_file, shell=True, check=True)

    if add_key.returncode != 0:
        log_error(f"An error occurred while adding the private key to the ssh agent. Error code: {add_key.returncode}.",
                  print_formatted=False)

    delete_key = subprocess.run("del" + private_key_file, shell=True, check=True)

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

    print()
    log(f"Private and public ed25519 keys have been generated and saved to files and ssh-agent "
        f"for computer {computer.hostname}.", print_formatted=False)


if __name__ == '__main__':
    dict_computer = {
        "username": "pc-pret-02\\administrateur",
        "mac_address": "C8-60-00-38-64-79",
        "hostname": "PC-PRET-02",
        "ipv4": "192.168.7.227"
    }
    gen_keys_and_save_them(Computer(dict_computer))
