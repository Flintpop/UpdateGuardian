# -----------------------------------------------------------
# ssh_keygen.py
# Author: darwh
# Date: 02/05/2023
# Description: Used to generate ssh keys for the server.
# -----------------------------------------------------------
import os

import paramiko
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import PrivateFormat
from cryptography.hazmat.primitives.serialization import NoEncryption
from cryptography.hazmat.primitives.serialization import PublicFormat

from typing import TYPE_CHECKING

from src.server.commands.path_functions import find_directory

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.environnement.server_logs import log


def gen_keys_and_save_them(computer: 'Computer') -> None:
    """
    Generate and saves a new ED25519 private key and its public key.
    :return:
    """

    # Generate a new ED25519 private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_key_file: str = computer.private_key_filepath
    public_key_file: str = computer.public_key_filepath

    # Serialize the private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )

    # Save the private key to a file
    with open(private_key_file, "wb") as f:
        f.write(private_pem)

    # Get the public key from the private key
    public_key: ed25519.Ed25519PublicKey = private_key.public_key()

    # Serialize the public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=Encoding.OpenSSH,
        format=PublicFormat.OpenSSH
    )

    # Save the public key to a file
    with open(public_key_file, "wb") as f:
        f.write(public_pem)

    log(f"Private and public keys have been generated and saved to files for computer {computer.hostname}.",
        print_formatted=False)
