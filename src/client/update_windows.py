import ctypes
import json
import subprocess
import os
import sys
import logging
import time
import traceback
from ctypes import wintypes

import psutil
import requests

counter: int = 0

lock_file_path = "C:\\Temp\\UpdateGuardian\\update_status.lock"


class SystemPowerStatus(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', wintypes.BYTE),
        ('BatteryFlag', wintypes.BYTE),
        ('BatteryLifePercent', wintypes.BYTE),
        ('Reserved1', wintypes.BYTE),
        ('BatteryLifeTime', wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD),
    ]


SYSTEM_POWER_STATUS_P = ctypes.POINTER(SystemPowerStatus)

GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
GetSystemPowerStatus.restype = wintypes.BOOL

TEMP_FOLDER = "C:\\Temp"
UPDATE_FOLDER = os.path.join(TEMP_FOLDER, 'UpdateGuardian')
STATUS_FILENAME = os.path.join(UPDATE_FOLDER, "update_status.json")
SCRIPT_PATH = os.path.abspath("Update.ps1")
TASK_NAME = "TestTask"


def is_on_ac_power():
    status = SystemPowerStatus()
    if not GetSystemPowerStatus(ctypes.pointer(status)):
        raise ctypes.WinError()
    return status.ACLineStatus == 1  # 1 means AC power


def remove_existing_update_status_file():
    if os.path.exists(STATUS_FILENAME):
        os.remove(STATUS_FILENAME)


def create_update_folder():
    if not os.path.exists(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)
        os.mkdir(UPDATE_FOLDER)
    if not os.path.exists(UPDATE_FOLDER):
        os.mkdir(UPDATE_FOLDER)


def create_symbolic_link():
    link_path = os.path.join(UPDATE_FOLDER, 'Update.ps1')
    # If the link already exists, remove it
    if os.path.exists(link_path):
        os.remove(link_path)
    # Create a new symbolic link
    os.symlink(SCRIPT_PATH, link_path)
    return link_path


def create_batch_file(link_path):
    # Create batch file to run PowerShell script and log output
    batch_file_path = os.path.join(UPDATE_FOLDER, 'RunUpdateScript.bat')
    with open(batch_file_path, 'w') as batch_file:
        batch_file.write('@echo off\n')
        batch_file.write('powershell -ExecutionPolicy Bypass -File ' + link_path + ' > '
                         + os.path.join(UPDATE_FOLDER, 'UpdateLog.txt') + ' 2>&1\n')
    return batch_file_path


def update_windows_task(batch_file_path):
    delete_existing_task()
    create_new_task(batch_file_path)
    run_task()
    delete_existing_task()


def delete_existing_task():
    find_task_command = ['schtasks', '/query', '/TN', TASK_NAME]
    task_found = subprocess.run(find_task_command, capture_output=True, text=True)
    if TASK_NAME in task_found.stdout:
        delete_task_command = ['schtasks', '/delete', '/TN', TASK_NAME, '/F']
        delete_task = subprocess.run(delete_task_command, capture_output=True, text=True)
        if delete_task.returncode != 0:
            raise OSError(f'Failed to delete task: {delete_task.stderr}')


def create_new_task(batch_file_path):
    create_task_command = ['schtasks', '/create', '/tn', TASK_NAME, '/tr',
                           f'cmd.exe cmd /C {batch_file_path}', '/sc', 'once', '/st', '00:00',
                           '/RL', 'HIGHEST', '/ru', 'SYSTEM', '/F']
    create_task = subprocess.run(create_task_command, capture_output=True, text=True)
    if create_task.returncode != 0:
        raise OSError(f'Failed to create task: {create_task.stderr}')


def run_task():
    run_task_command = ['schtasks', '/run', '/tn', TASK_NAME]
    run_task = subprocess.run(run_task_command, capture_output=True, text=True)
    if run_task.returncode != 0:
        raise OSError(f'Failed to run task: {run_task.stderr}')


def update_windows():
    print_and_log_client("Starting Windows Update and launching the scheduled task...")
    remove_existing_update_status_file()
    create_update_folder()
    link_path = create_symbolic_link()
    batch_file_path = create_batch_file(link_path)
    update_windows_task(batch_file_path)
    save_updates_info()


def save_updates_info():
    json_infos = get_updates_info()
    if json_infos is None:
        print_and_log_client("Error occurred while getting updates infos.", "error")
        with open("results.json", "w") as file:
            with open(STATUS_FILENAME, "r") as file_read:
                file.write(file_read.read())
                os.remove(STATUS_FILENAME)
                return
    with open("results.json", "w") as json_file:
        json.dump(json_infos, json_file)
    os.remove(STATUS_FILENAME)
    print_and_log_client("Windows Update finished, json file dumped.")


def process_data_json_updates_results(data: dict):
    update_finished: bool | None = data.get("UpdateFinished", None)
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


def file_exists(file_path: str, already_printed: bool) -> bool:
    if file_path is None or file_path == "":
        return False
    if not os.path.isfile(file_path):
        if not already_printed:
            print_and_log_client(f"File {file_path} does not exist. Waiting for file to be created...")
        return False
    return True


def check_file_empty(file_path):
    if os.stat(file_path).st_size <= 0:
        print_and_log_client("File is empty. Waiting for data to be written...")
        return True
    return False


def process_json_file(file_path):
    with open(file_path, 'r', encoding="utf-8-sig") as json_file:
        data = json.load(json_file)
        will_return, res = process_data_json_updates_results(data)
        return will_return, res


def handle_json_decode_error(e, json_file_path):
    global counter
    with open(json_file_path, 'r', encoding="utf-8-sig") as faulty_json_file:
        content = faulty_json_file.read()
        print_and_log_client(f"JSONDecodeError occurred. Error details: \n{e}. Content of the file: \n{content}",
                             "error")
    counter = counter + 1


def handle_file_not_found_error(e, already_printed: bool):
    if not already_printed:
        print_and_log_client(f"File not found: {e}. Waiting for file to be created...", "warning")


def handle_general_error(e):
    logging.error(f"An unexpected error occurred. Error details: {e}")
    print_and_log_client(f"An unexpected error occurred. Error details: \n{e}\n\nTraceback: \n{traceback.format_exc()}",
                         "error")
    sys.exit(0)


def wait_for_lock_to_release(max_wait_time=20):
    wait_time = 0
    while os.path.exists(lock_file_path) and wait_time < max_wait_time:
        if wait_time == 0:  # Log only at the beginning
            print_and_log_client("Lock file exists. Waiting for it to be released...", "info")
        time.sleep(1)
        wait_time += 1
    if os.path.exists(lock_file_path):
        print_and_log_client(f"Lock file still exists after waiting {max_wait_time} seconds."
                             "There is likely a deadlock. Exiting program", "error")
        sys.exit(1)
    else:
        if wait_time > 0:  # If we waited, log that the lock was released
            print_and_log_client(f"Lock file released after {max_wait_time} seconds. "
                                 "Reading the file...", "info")


def get_updates_info() -> dict | None:
    global counter
    already_printed: bool = False
    json_file_path: str = "C:\\Temp\\updateguardian\\update_status.json"
    lock_file = None
    while True:
        if not file_exists(json_file_path, already_printed):
            already_printed = True
            time.sleep(1)
            continue

        if already_printed:
            print_and_log_client("File exists, processing...")
            already_printed = False

        try:
            wait_for_lock_to_release()  # Attente pour la libération du fichier de verrouillage
            lock_file = open(lock_file_path, "w")
            if check_file_empty(json_file_path):
                time.sleep(1)
                continue
            will_return, res = process_json_file(json_file_path)
            if will_return:
                return res
            counter = 0
            lock_file.close()
            os.remove(lock_file_path)
            lock_file = None
        except json.JSONDecodeError as e:
            handle_json_decode_error(e, json_file_path)
            if counter >= 20:
                print_and_log_client("JSONDecodeError occurred 20 times. Exiting...")
                return None
        except FileNotFoundError as e:
            handle_file_not_found_error(e, already_printed=already_printed)
            already_printed = True
        except Exception as e:
            handle_general_error(e)
            return None
        finally:
            if os.path.exists(lock_file_path) and lock_file is not None:
                lock_file.close()
                os.remove(lock_file_path)
                lock_file = None

            # If the file is there, but not handled by the program, it will be checked again
            # and if it is a mistake, it will be signaled in wait_for_lock_to_release
            time.sleep(1)


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
        error_string: str = f"Not enough disk space available for the update, there is only {free_space_gb:.2f} GB." \
                            f"The program aimed at {disk_space_required} GB."
        print_and_log_client(error_string, "error")
        raise EnvironmentError(error_string)


def start_client_update():
    if not is_admin():
        print_and_log_client("Please, execute this script in administrator to update the windows pc.", "error")
        sys.exit(1)
    if not is_on_ac_power():
        print_and_log_client("Please, connect the device to a power source instead of battery to update the pc.",
                             "error")
        sys.exit(1)

    try:
        check_disk_space(3)
        check_internet_connection()
        update_windows()
    except Exception as e:
        print_and_log_client(f"Error occurred during Python update process:\n {e}", "error")


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
        if stdout:
            print_and_log_client(f"Troubleshooter output: {stdout.decode('cp850')}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        print_and_log_client("Error occurred while checking if the user is admin.", "error")
        return False


def print_and_log_client(message: str, level: str = "info", print_mess=True) -> None:
    message = message + "\n"
    if print_mess:
        print(message, end="")
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)
