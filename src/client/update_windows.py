import ctypes
import json
import subprocess
import os
import sys
import logging
import time
import traceback

import psutil
import requests


def update_windows():
    # TODO:
    #  - Corriger le bug qui fait que le programme ne s'arrête pas
    #  - Corriger le bug qui fait que le module PSWindowsUpdate n'est pas trouvé par
    #   le script en ssh ✔️
    #  - Corriger le bug qui fait que quand ça crash il me dit "bool" n'a pas d'attribut "lower" ~✔️
    #  - Corriger le bug qui fait que le script s'arrête alors que le truc qui fait les maj ne s'est pas terminé ✔️
    print_and_log_client("Starting Windows Update and launching the scheduled task...")
    update_status_json_filename: str = "C:\\Temp\\UpdateGuardian\\update_status.json"
    if os.path.exists(update_status_json_filename):
        os.remove(update_status_json_filename)

    task_name = "TestTask"
    file_path = os.path.abspath("Update.ps1")

    # Check and create folder in C:\Temp
    temp_folder = "C:\\Temp"
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    temp_folder = os.path.join(temp_folder, 'UpdateGuardian')
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    # Create a symbolic link to powershell script
    link_path = os.path.join(temp_folder, 'Update.ps1')
    # If the link already exists, remove it
    if os.path.exists(link_path):
        os.remove(link_path)

    # Create a new symbolic link
    os.symlink(file_path, link_path)

    # Create batch file to run PowerShell script and log output
    batch_file_path = os.path.join(temp_folder, 'RunUpdateScript.bat')
    with open(batch_file_path, 'w') as batch_file:
        batch_file.write('@echo off\n')
        batch_file.write('powershell -ExecutionPolicy Bypass -File ' + link_path + ' > '
                         + os.path.join(temp_folder, 'UpdateLog.txt') + ' 2>&1\n')

    find_task_command = ['schtasks', '/query', '/TN', task_name]
    task_found = subprocess.run(find_task_command, capture_output=True, text=True)

    if task_name in task_found.stdout:
        delete_task_command = ['schtasks', '/delete', '/TN', task_name, '/F']
        delete_task = subprocess.run(delete_task_command, capture_output=True, text=True)
        if delete_task.returncode != 0:
            raise OSError(f'Failed to delete task: {delete_task.stderr}')

    create_task_command = ['schtasks', '/create', '/tn', task_name, '/tr',
                           f'cmd.exe cmd /C {batch_file_path}', '/sc', 'once', '/st', '00:00',
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
    if json_infos is None:
        print_and_log_client("Error occurred while getting updates infos.", "error")
        with open("results.json", "w") as file:
            with open("C:/Temp/UpdateGuardian/update_status.json", "r") as file_read:
                file.write(file_read.read())
                os.remove("C:/Temp/UpdateGuardian/update_status.json")
                return
    with open("results.json", "w") as json_file:
        json.dump(json_infos, json_file)

    os.remove("C:/Temp/UpdateGuardian/update_status.json")
    print_and_log_client("Windows Update finished, json file dumped.")


def handle_json_decode_error(e, json_file_path):
    with open(json_file_path, 'r') as faulty_json_file:
        content = faulty_json_file.read()
        print_and_log_client(f"JSONDecodeError occurred. Error details: \n{e}. Content of the file: \n{content}",
                             "error")


def handle_file_not_found_error(e, already_printed: bool):
    if not already_printed:
        print_and_log_client(f"File not found: {e}. Waiting for file to be created...", "warning")


def handle_general_error(e):
    logging.error(f"An unexpected error occurred. Error details: {e}")
    print_and_log_client(f"An unexpected error occurred. Error details: \n{e}\n\nTraceback: \n{traceback.format_exc()}",
                         "error")


def process_data_json_updates_results(data: dict):
    update_finished: bool = data.get("UpdateFinished", None)
    error_message = data.get("ErrorMessage", None)

    if error_message is not None and error_message is not False:
        print_and_log_client(f"Error occurred: {data['ErrorMessage']}", "error")
        return True, None
    if update_finished is None:
        print_and_log_client("Error, update_finished is None", "error")
        return True, None

    if update_finished:
        print_and_log_client("Update process is finished.")
        print_and_log_client(data.__str__())
        return True, data

    return False, None


def get_updates_infos() -> dict | None:
    already_printed: bool = False
    json_file_path: str = "C:/Temp/UpdateGuardian/update_status.json"
    while True:
        if not os.path.isfile(json_file_path):
            if not already_printed:
                print_and_log_client("File does not exist. Waiting for file to be created...")
                already_printed = True
            time.sleep(1)
            continue

        try:
            with open(json_file_path, 'r', encoding="utf-8") as json_file:
                if os.stat(json_file_path).st_size <= 0:
                    print_and_log_client("File is empty. Waiting for data to be written...")
                    time.sleep(1)
                    continue

                data = json.load(json_file)

                will_return, res = process_data_json_updates_results(data)
                if will_return:
                    return res

        except json.JSONDecodeError as e:
            handle_json_decode_error(e, json_file_path)

        except FileNotFoundError as e:
            handle_file_not_found_error(e, already_printed=already_printed)
            already_printed = True

        except Exception as e:
            handle_general_error(e)
            return None

        finally:
            time.sleep(1)


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
        print_and_log_client("Error occurred while checking if the user is admin.", "error")
        return False


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
