import paramiko

from newServer.ssh.ssh_key_manager import SSHKeyManager


class SSHConnect:
    def __init__(self, ssh_key_manager: 'SSHKeyManager'):
        self.ssh_key_manager = ssh_key_manager

    def connect(self, computer):
        self.log(message=f"Connecting to {self.hostname} computer via SSH...")
        try:
            self.connect_ssh_procedures()

            self.log(f"Connected via SSH to computer {self.hostname}.")
            return True
        except paramiko.AuthenticationException as e:
            self.log_add_vertical_space()
            self.log_error("Authentication failed: " + str(e))
            self.log_error(f"Please, check your username and password for the computer {self.hostname}.")
            self.log_error("The connection password may be the os connection password if there are no "
                           "microsoft accounts linked.\nOtherwise, it is the account password.")
            self.log_error("Furthermore, if there are several accounts to the computer that a user can connect to,"
                           f"make sure the username {self.username} is something as follows: \n'pc-name\\username@ip' "
                           "(or 'pc-name\\username@hostname').")
            self.log_add_vertical_space()
            self.log_error(f"Here are some informations about the connection settings:"
                           f"\n\tip: {self.ipv4}"
                           f"\n\tmac: {self.mac_address}"
                           f"\n\tusername: {self.username}")
            return False
        except Exception as e:
            self.log_error(f"Unhandled error. Could not connect to {self.hostname}:\n " + str(e))
            self.log_error(f"Here is the traceback: \n{traceback.format_exc()}\n")
            return False
