import os
import time

import asyncio

import paramiko


def test_with_paramiko(hostname: str, username: str, password: str, command: str, responses: list[str]) -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    command_full_response: str = ""
    response_index: int = 0
    channel = None

    if len(responses) != 0 and [x for x in responses if x == "" or not x.endswith("\n")] != []:
        raise ValueError("Empty response not allowed, or response must end with a newline character.")

    try:
        client.connect(hostname, username=username, password=password)
        channel = client.get_transport().open_session()
        channel.exec_command(command)

        # Utiliser un buffer pour recevoir toutes les données
        while True:
            # Attendre que les données soient disponibles
            while not channel.recv_ready() and not channel.exit_status_ready():
                time.sleep(0.1)

            # Lire les données disponibles
            if channel.recv_ready():
                output = channel.recv(4096).decode('utf-8')
                command_full_response += output
                print(output)
                if not channel.exit_status_ready():
                    if response_index >= len(responses):
                        raise ValueError("Not enough responses provided, at least one response is missing.\n\n"
                                         + command_full_response)
                    channel.send(responses[response_index].encode())
                    print("> " + responses[response_index])
                    response_index += 1

            # Vérifier si la commande a terminé son exécution
            if channel.exit_status_ready():
                # S'assurer de lire toutes les données restantes
                if channel.recv_ready():
                    output = channel.recv(4096).decode('utf-8')
                    command_full_response += output
                    print(output)
                break

    finally:
        if channel:
            channel.close()
        client.close()

    # print(command_full_response)


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
    start_update_guardian_command: str = "updateguardian"

    # await connect_and_run("192.168.1.49", "linuxserver", "changeme",
    #                       install_update_guardian_command, [])
    test_with_paramiko("192.168.1.49", "linuxserver", "changeme",
                       start_update_guardian_command, ["Monday\n"])


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
