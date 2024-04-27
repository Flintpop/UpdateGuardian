import os
import time

import asyncssh
import asyncio

import paramiko


def test_with_paramiko(hostname: str, username: str, password: str, command: str) -> None:
    # Configuration des informations de connexion

    # Créer une instance client SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    channel = None
    command_full_response: str = ""

    try:
        client.connect(hostname, username=username, password=password)
        # Ouvrir un canal SSH
        channel = client.get_transport().open_session()
        # Le programme à exécuter
        channel.exec_command(command)

        # Attente que le serveur soit prêt
        while not channel.recv_ready():
            time.sleep(1)

        if channel.recv_ready():
            output = channel.recv(1024).decode('utf-8')
            command_full_response += output

        # Gestion des inputs étape par étape
        while not channel.exit_status_ready():
            # Lire la sortie du serveur
            if channel.recv_ready():
                output = channel.recv(1024).decode('utf-8')
                command_full_response += output
                # Répondre basé sur le prompt
                if "password" in output:
                    channel.send('changeme\n')
                time.sleep(1)
    finally:
        if channel:
            channel.close()
        client.close()
        print(command_full_response)


async def read_with_timeout(process: asyncssh.connect, timeout: int = 0.5) -> str | None:
    """
    Read from process stdout with a timeout to avoid blocking indefinitely.

    :param process: The process from which to read.
    :param timeout: Timeout in seconds after which the read will return None if no data is received.
    :return: The received data or None if timed out.
    """
    try:
        return await asyncio.wait_for(process.stdout.read(512), timeout)
    except asyncio.TimeoutError:
        return None


async def interactive_command_execution(conn: asyncssh.connect, command: str, prompts_responses: list[str]) -> None:
    """
    Execute a command interactively, responding to multiple expected prompts.

    :param conn: Active SSH connection.
    :param command: Command to be executed on the SSH server.
    :param prompts_responses: Dictionary where keys are prompts to detect and values are the responses to send.
    """
    async with conn.create_process(command, stderr=asyncssh.STDOUT) as process:
        index: int = 0
        result_concatenated: str = ""
        while True:
            recv = await read_with_timeout(process)
            if not recv:
                print(result_concatenated)
                return
            else:
                result_concatenated += recv

            if index < len(prompts_responses):
                # Send the response to the prompt
                process.stdin.write(prompts_responses[index] + '\n')
                index += 1

            # No more data received, process likely completed
            if process.exit_status is not None:
                print(recv)
                break
            await asyncio.sleep(0.1)


async def connect_and_run(address: str, username: str, password: str, command: str,
                          prompts_responses: list[str]) -> None:
    """
    Connect to SSH and run a command interactively with multiple prompt handling.

    :param address: SSH server address.
    :param username: Username for SSH login.
    :param password: Password for SSH login.
    :param command: Command to execute.
    :param prompts_responses: Dictionary of prompts and their respective responses.
    """
    try:
        conn = await asyncssh.connect(address, username=username, password=password)
        print(f"Connected to {address}")
        await interactive_command_execution(conn, command, prompts_responses)
        print("\nCommand execution completed.")
    except Exception as e:
        print(f"\nConnection or command failed: {e}")


async def launch_vms() -> None:
    # Définissez le chemin vers votre script PowerShell
    ps_script_path = os.path.join(os.path.dirname(__file__), "startup_and_restore_snapshot.ps1")

    if not os.path.exists(ps_script_path):
        raise FileNotFoundError(f"PowerShell script not found at path: {ps_script_path}")

    # Exécutez le script PowerShell et attendez la fin de son exécution
    proc = await asyncio.create_subprocess_exec(
        'powershell.exe', ps_script_path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    # Vérifiez si le script PowerShell a été exécuté avec succès
    if proc.returncode != 0:
        print(f"Error executing PowerShell script: \n{stderr.decode()}")
        exit(1)
    else:
        print(f"PowerShell script executed successfully: {stdout.decode()}")


async def main() -> None:
    # Attendez que la coroutine launch_vms soit terminée avant de continuer
    os.chdir(os.path.dirname(__file__))
    await launch_vms()

    install_update_guardian_command: str = """echo 'changeme' | sudo -S bash -c "$(curl -sSl https://raw.githubusercontent.com/Flintpop/UpdateGuardian/main/install.sh)\""""

    # await connect_and_run("192.168.1.49", "linuxserver", "changeme",
    #                       install_update_guardian_command, [])
    test_with_paramiko("192.168.1.49", "linuxserver", "changeme", install_update_guardian_command)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
