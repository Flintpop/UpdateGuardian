import ctypes
import datetime
import json
import subprocess
import os
import sys
import logging
import time
import traceback

import psutil
import requests

path_output_file: str = os.path.abspath("output.txt")
if " " in path_output_file:
    path_output_file = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop", "output.txt"))
    if " " in path_output_file:
        raise ValueError(f"Path to output file still contains spaces: {path_output_file}.")


def get_cmd(ps_script: str) -> list[str]:
    global path_output_file

    command: str = ps_script + " | Out-File -FilePath " + path_output_file + " -Encoding UTF8"
    command += "; $Error | Out-File -FilePath " + path_output_file.replace("output", "error") + " -Encoding UTF8"
    cmd = [
        "powershell.exe", "-Command", "Start-Process", "powershell", "-Verb", "runAs", "-Wait", "-ArgumentList",
        "'-executionpolicy', 'bypass', '-Command', '" + command + "'"
    ]
    return cmd


def execute_command(command: list[str]) -> tuple[str, str | None]:
    global path_output_file

    subprocess.run(command, shell=True)

    try:
        with open(path_output_file, "r") as file:
            output = file.read()
        with open(path_output_file.replace("output", "error"), "r") as file:
            error = file.read()
    except FileNotFoundError:
        print_and_log_client("File not found", "error")

    return output, error


def execute_file() -> tuple[str, str | None]:
    import subprocess
    import time

    # Define the paths for your batch file and output file
    batch_file_path = os.path.abspath("yes.bat")
    output_file_path = os.path.abspath('output.txt')

    start_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%H:%M")

    # Define the command to create the scheduled task
    create_task_command = f'schtasks /create /tn "WindowsUpdate" /tr "{batch_file_path}" /sc once /st ' \
                          f'{start_time} /rl highest'

    # Run the command to create the task
    subprocess.run(create_task_command, shell=True, check=True)

    # Define the command to run the scheduled task
    run_task_command = 'schtasks /run /tn "WindowsUpdate"'

    # Run the command to start the task
    subprocess.run(run_task_command, shell=True, check=True)

    # Wait for the task to complete. This is a simple way to wait,
    # but in a real-world situation, you'd want to check the task's
    # actual status or implement a timeout.
    time.sleep(60)

    # Read the output file
    with open(output_file_path, 'r') as file:
        output = file.read()

    print_and_log_client(output)
    # return output.replace(b"\r\n", b"\n").decode('cp1252'), error.replace(b"\r\n", b"\n").decode('cp1252')

    return output, None


def update_windows():
    # TODO:
    #  - Corriger le bug qui fait que le programme ne s'arrête pas
    #  - Corriger le bug qui fait que le module PSWindowsUpdate n'est pas trouvé par
    #   le script en ssh ✔️
    #  - Corriger le bug qui fait que quand ça crash il me dit "bool" n'a pas d'attribut "lower"
    #  - Corriger le bug qui fait que le script s'arrête alors que le truc qui fait les maj ne s'est pas terminé ✔️
    print_and_log_client("Starting Windows Update and launching the scheduled task...")

    task_name = "TestTask"
    file_path = os.path.abspath("Update.ps1")

    # Check and create folder in C:\Temp
    temp_folder = "C:\\Temp"
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    temp_folder = os.path.join(temp_folder, 'UpdateGuardian')
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    # Create a symbolic link to script
    link_path = os.path.join(temp_folder, 'Update.ps1')
    if not os.path.exists(link_path):
        os.symlink(file_path, link_path)

    # Create batch file to run PowerShell script and log output
    batch_file_path = os.path.join(temp_folder, 'RunUpdateScript.bat')
    with open(batch_file_path, 'w') as batch_file:
        batch_file.write('@echo off\n')
        batch_file.write('powershell -ExecutionPolicy Bypass -File ' + link_path + ' > ' + os.path.join(temp_folder, 'UpdateLog.txt') + ' 2>&1\n')

    find_task_command = ['schtasks', '/query', '/TN', task_name]
    task_found = subprocess.run(find_task_command, capture_output=True, text=True)

    if task_name in task_found.stdout:
        delete_task_command = ['schtasks', '/delete', '/TN', task_name, '/F']
        delete_task = subprocess.run(delete_task_command, capture_output=True, text=True)
        if delete_task.returncode != 0:
            raise OSError(f'Failed to delete task: {delete_task.stderr}')

    create_task_command = ['schtasks', '/create', '/tn', task_name, '/tr',
                           f'cmd.exe /C "{batch_file_path}"', '/sc', 'once', '/st', '00:00',
                           '/RL', 'HIGHEST', '/ru', 'SYSTEM', '/F']
    create_task = subprocess.run(create_task_command, capture_output=True, text=True)
    if create_task.returncode != 0:
        raise OSError(f'Failed to create task: {create_task.stderr}')

    run_task_command = ['schtasks', '/run', '/tn', task_name]
    run_task = subprocess.run(run_task_command, capture_output=True, text=True)
    if run_task.returncode != 0:
        raise OSError(f'Failed to run task: {run_task.stderr}')

    delete_task_command = ['schtasks', '/delete', '/TN', task_name, '/F']
    delete_task = subprocess.run(delete_task_command, capture_output=True, text=True)
    if delete_task.returncode != 0:
        raise OSError(f'Failed to delete task: {delete_task.stderr}')

    json_infos = get_updates_infos()
    with open("results.json", "w") as json_file:
        json.dump(json_infos, json_file)

    print_and_log_client("Windows Update finished, json file dumped.")

    # if not list_updates():
    #     return
    #
    # print_and_log_client("Downloading updates...")
    # if not download_updates():
    #     return
    #
    # print_and_log_client("Installing updates...")
    # if not install_updates():
    #     return


def get_updates_infos() -> dict:
    json_file_path = "C:/Temp/UpdateGuardian/update_status.json"

    while True:
        try:
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
                print_and_log_client(data)  # or do something else with the data

                if data["UpdateFinished"]:
                    print_and_log_client("Update process is finished.")
                    if data["ErrorMessage"]:
                        print_and_log_client("Error occurred:", data["ErrorMessage"])
                    break
        except json.JSONDecodeError:
            # This error occurs when the JSON file is being written to while we're trying to read it
            print_and_log_client("Waiting for file to be available...")
        except FileNotFoundError:
            # This error occurs if the file does not exist
            print_and_log_client("File not found. Waiting for file to be created...")

        # Wait for a bit before checking the file again to not overwhelm the system
        time.sleep(1)

    return data


def list_updates() -> bool:
    ps_script = 'Get-WindowsUpdate'

    cmd = get_cmd(ps_script)

    output, error = execute_command(cmd)

    if error:
        print_and_log_client(f"Error: {error}", "error")
        return False

    if not output or output == "":
        print_and_log_client("No updates available.")
        return False

    print_and_log_client(f"Updates available.\n{output}")
    return True


def download_updates() -> bool:
    ps_script = 'Download-WindowsUpdate -AcceptAll'
    cmd = get_cmd(ps_script)

    output, error = execute_command(cmd)

    if error:
        print_and_log_client(f"Error: {error}", "error")
        return False

    if not output:
        print_and_log_client("Error: No updates downloadable.", "error")
        return False

    print_and_log_client(f"Updates downloaded.\n{output}")
    return True


def install_updates() -> bool:
    ps_script = 'Install-WindowsUpdate -AcceptAll -AutoReboot'
    cmd = get_cmd(ps_script)

    output, error = execute_command(cmd)

    if error:
        print_and_log_client(f"Error: {error}", "error")
        return False

    if not output:
        print_and_log_client("Updates could not be installed.", "error")
        return False

    print_and_log_client(f"Updates installed.\n{output}")
    return True


def reset_windows_update_components():
    commands = [
        "net stop wuauserv",
        "net stop cryptSvc",
        "net stop bits",
        "net stop msiserver",
        "ren C:\\Windows\\SoftwareDistribution SoftwareDistribution.old",
        "ren C:\\Windows\\System32\\catroot2 catroot2.old",
        "net start wuauserv",
        "net start cryptSvc",
        "net start bits",
        "net start msiserver"
    ]

    for command in commands:
        try:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print_and_log_client(f"Successfully executed command: {command}")
        except subprocess.CalledProcessError as e:
            print_and_log_client(f"Error occurred while executing command '{command}': {e.stderr.decode('cp850')}",
                                 "error")


def check_internet_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code != 200:
            raise EnvironmentError("No internet connection")
    except Exception as e:
        print_and_log_client(f"Error occurred while checking internet connection: {e}", "error")
        print_and_log_client(f"The traceback : \n{traceback.format_exc()}", "error")
        raise EnvironmentError("No internet connection")


def check_disk_space(disk_space_required: int = 5):
    # Check for available disk space
    hdd = psutil.disk_usage('/')
    free_space_gb = hdd.free / (1024 ** 3)
    if free_space_gb < disk_space_required:  # Adjust the value as needed
        print_and_log_client(f"Not enough disk space available for the update, there is only {free_space_gb:.2f} GB."
                             f"The program aimed at {disk_space_required} GB.", "error")
        raise EnvironmentError("Not enough disk space available for the update.")


def start_client_update():
    if is_admin():
        try:
            check_disk_space(3)
            check_internet_connection()
            update_windows()
        except Exception as e:
            traceback_str: str = traceback.format_exc()
            print_and_log_client(f"Error occurred during Python update process:\n {e}\nTraceback:\n {traceback_str}",
                                 "error")
            check_disk_space(20)
            check_internet_connection()
            update_windows()
    else:
        print_and_log_client("Please, execute this script in administrator to update the windows pc.", "error")
        sys.exit(1)


def run_windows_update_troubleshooter():
    process = subprocess.Popen(["msdt.exe", "/id", "WindowsUpdateDiagnostic", "/quiet"], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return_code = process.returncode
    if return_code != 0:
        print_and_log_client(f"Error running Windows Update Troubleshooter. Return code: {return_code}", "error")
        if stderr:
            print_and_log_client(f"Error details: {stderr.decode('cp850')}", "error")
    else:
        print_and_log_client("Windows Update Troubleshooter ran successfully.")


def troubleshoot():
    reset_windows_update_components()
    run_windows_update_troubleshooter()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        logging.error(e)
        return False


def reboot(reboot_msg: str = "reboot"):
    print_and_log_client("A system reboot is required to complete the update installation.", "warning")
    print_and_log_client("Rebooting...")
    print_and_log_client(reboot_msg)  # This lines allows the server to know that the client needs to reboot
    os.system("shutdown /g /t 1")


def print_and_log_client(message: str, level: str = "info") -> None:
    message = message + "\n"
    print(message, end="")
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)
