import ctypes
import os
import sys
import logging

import win32com.client


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


def start_client_update():
    if is_admin():
        update_windows()
    else:
        logging.error("Please, execute this script in administrator to update the windows pc.")
        sys.exit(1)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        logging.error(e)
        return False


def reboot():
    print_and_log_client("A system reboot is required to complete the update installation.", "warning")
    print_and_log_client("Rebooting...")
    print("reboot")  # This lines allows the server to know that the client needs to reboot
    os.system("shutdown /g /t 1")


def install_updates(wua, updates_to_install) -> tuple:
    print_and_log_client("Installing updates...")
    installer = wua.CreateUpdateInstaller()
    installer.Updates = updates_to_install
    installation_result = installer.Install()
    return installer, installation_result


def download_updates(wua, updates_to_install) -> None:
    print_and_log_client("Downloading updates...")
    downloader = wua.CreateUpdateDownloader()
    downloader.Updates = updates_to_install
    download_result = downloader.Download()

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
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)
