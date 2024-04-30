import os
import time

import asyncio

import paramiko


def _create_ssh_client(hostname: str, username: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)
    return client


def _verify_responses(responses: list[str]) -> None:
    """
    Throws an exception if the responses list is empty or if any response is empty or does not end with a newline
    """
    if len(responses) != 0 and [x for x in responses if x == "" or not x.endswith("\n")] != []:
        raise ValueError("Empty response not allowed, or response must end with a newline character.")


def _exec_command(client: paramiko.SSHClient, command: str) -> paramiko.Channel:
    channel = client.get_transport().open_session()
    channel.exec_command(command)
    return channel


def _read_and_respond(channel: paramiko.Channel, responses: list[str]) -> str:
    command_full_response = ""
    response_index = 0

    while not channel.exit_status_ready():
        while not channel.recv_ready() and not channel.exit_status_ready():
            time.sleep(0.1)

        if channel.recv_ready():
            output = channel.recv(4096).decode('utf-8')
            command_full_response += output
            print(output)

            if not channel.exit_status_ready() and response_index < len(responses):
                channel.send(responses[response_index].encode())
                print("> " + responses[response_index])
                response_index += 1
            elif response_index >= len(responses):
                raise ValueError(
                    "Not enough responses provided, at least one response is missing.\n\n" + command_full_response)

    # Read any remaining output after the command execution completes
    while channel.recv_ready():
        output = channel.recv(4096).decode('utf-8')
        command_full_response += output
        print(output)

    return command_full_response


def execute_interactive_command(hostname: str, username: str, password: str, command: str,
                                responses: list[str]) -> None:
    _verify_responses(responses)
    client = None

    try:
        client = _create_ssh_client(hostname, username, password)
        channel = _exec_command(client, command)
        output = _read_and_respond(channel, responses)
        print(output)
    finally:
        if channel:
            channel.close()
        if client:
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
    execute_interactive_command("192.168.1.49", "linuxserver", "changeme",
                                start_update_guardian_command, ["Monday\n"])


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
