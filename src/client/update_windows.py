import ctypes
import subprocess
import os
import sys
import logging
import time
import traceback

import psutil
import requests
import win32com.client
from win32com.universal import com_error


def update_windows():
    wua = win32com.client.Dispatch("Microsoft.Update.Session")
    searcher = wua.CreateUpdateSearcher()
    print_and_log_client("Searching for new updates...")

    # Search for updates
    updates_to_install = search_for_updates(searcher)

    # Download updates
    download_updates(wua, updates_to_install)

    # Install updates
    installer, installation_result = install_updates(wua, updates_to_install)

    process_updates(installation_result, updates_to_install)


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
            print_and_log_client(f"Error occurred while executing command '{command}': {e.stderr.decode('utf-8')}",
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
            print_and_log_client(f"Error occurred during Python update process:\n {e}\nTraceback:\n {traceback_str}", "error")
            print_and_log_client("Attempting to update using PowerShell script...", "warning")
            check_disk_space(20)
            run_powershell_script()
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
            # TODO: Bug here with the stderr decoding
            print_and_log_client(f"Error details: {stderr.decode()}", "error")
    else:
        print_and_log_client("Windows Update Troubleshooter ran successfully.")


def troubleshoot():
    reset_windows_update_components()
    run_windows_update_troubleshooter()


def run_powershell_script(troubleshooted=False):
    try:
        process = subprocess.Popen(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "install_updates.ps1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output, error = process.communicate()
        exit_code: int = process.returncode

        if exit_code == 2:
            print_and_log_client("PowerShell script indicates a reboot is required.", "warning")
            reboot()
        elif exit_code == 3:
            print_and_log_client("Powershell script indicates that no updates were found.")
        elif exit_code != 0:
            print_and_log_client(f"Error occurred while running the PowerShell script: {error.decode()}",
                                 "error")
        else:
            print_and_log_client(f"PowerShell script output: {output.decode('utf-8')}")

    except Exception as e:
        print_and_log_client(f"Error occurred while executing the PowerShell script: \n{e}", "error")
        print_and_log_client(f"The traceback : \n{traceback.format_exc()}", "error")
        sys.exit(-1)
        # TODO: Test this new troubleshooting method below
        # print_and_log_client("Attempting to troubleshoot the problem...", "warning")
        # if not troubleshooted:
        #     troubleshoot()
        #     run_powershell_script(troubleshooted=True)


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
    print(reboot_msg)  # This lines allows the server to know that the client needs to reboot
    os.system("shutdown /g /t 1")


def install_updates(wua, updates_to_install) -> tuple:
    print_and_log_client("Installing updates...")
    try:
        installer = wua.CreateUpdateInstaller()
        installer.Updates = updates_to_install
        installation_result = installer.Install()
    except com_error as e:
        print_and_log_client(f"COM Error: \n{e}")
        print_and_log_client(f"Exception info: \n{e.excepinfo}")
        return None, None
    return installer, installation_result


def download_updates(wua, updates_to_install) -> None:
    print_and_log_client("Downloading updates...")

    updates_to_install = [update for update in updates_to_install if not update.IsDownloaded and update.DownloadPriority == 1]

    # If there are no updates to download, return
    if not updates_to_install:
        print_and_log_client("No updates to download.")
        return

    attempts = 0
    while attempts < 5:  # Retry up to 5 times
        try:
            downloader = wua.CreateUpdateDownloader()
            downloader.Updates = updates_to_install
            download_result = downloader.Download()
            break
        except com_error as e:
            if e.hresult == -2147024891:  # Access denied
                attempts += 1
                print_and_log_client(f"Access denied, retrying after 10 seconds... ({attempts})")
                time.sleep(10)  # Wait for 10 seconds before retrying
            else:
                raise  # Re-raise the exception if it's not "access denied"
    else:  # No break, all attempts exhausted
        print_and_log_client("Error: Access denied 5 times, aborting.", "error")
        sys.exit(1)

    if download_result.ResultCode != 2:
        print_and_log_client("Error downloading updates.", "error")
        sys.exit(1)
    print_and_log_client("Updates downloaded successfully.")


def search_for_updates(searcher):
    search_result = searcher.Search("IsInstalled=0 and Type='Software'")
    updates_to_install = win32com.client.Dispatch("Microsoft.Update.UpdateColl")

    if search_result.Updates.Count == 0:
        print_and_log_client("No updates found.")
        sys.exit(0)
    else:
        print_and_log_client(f"{search_result.Updates.Count} update(s) found.")

    for update in search_result.Updates:
        print_and_log_client(f"Update {update.Title} is available.")
        updates_to_install.Add(update)

    if updates_to_install.Count == 0:
        print_and_log_client("No updates found.")
        sys.exit(0)
    return updates_to_install


def process_updates(installation_result, updates_to_install) -> None:
    if installation_result.ResultCode == 2:
        print_and_log_client("Updates installed successfully.")
        if installation_result.RebootRequired:
            reboot()
    else:
        process_update_error(installation_result, updates_to_install)


def process_update_error(installation_result, updates_to_install) -> None:
    hresult = installation_result.HResult
    for i in range(updates_to_install.Count):
        update_result = installation_result.GetUpdateResult(i)
        update = updates_to_install.Item(i)
        print_and_log_client(f"Error installing update {update.Title}. Error code: {update_result.ResultCode},"
                             f" HRESULT: {hresult}", "error")


def print_and_log_client(message: str, level: str = "info") -> None:
    print(message)
    message = message + "\n"
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)
