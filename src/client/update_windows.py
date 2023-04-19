import ctypes
import os
import sys
import logging

import win32com.client


def print_and_log(message: str, level: str = "info") -> None:
    print(message)
    if level == "info":
        logging.info(message)
    elif level == "error":
        logging.error(message)
    elif level == "warning":
        logging.warning(message)
    else:
        logging.info(message)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        logging.error(e)
        return False


def update_windows():
    wua = win32com.client.Dispatch("Microsoft.Update.Session")
    searcher = wua.CreateUpdateSearcher()
    print_and_log("Searching for new updates...")
    search_result = searcher.Search("IsInstalled=0 and Type='Software'")
    updates_to_install = win32com.client.Dispatch("Microsoft.Update.UpdateColl")

    if search_result.Updates.Count == 0:
        print_and_log("No updates found.")
        return
    else:
        print_and_log(f"{search_result.Updates.Count} update(s) found.")

    for update in search_result.Updates:
        print_and_log(f"Update {update.Title} is available.")
        updates_to_install.Add(update)

    if updates_to_install.Count == 0:
        print_and_log("No updates found.")
        return

    # Download updates
    downloader = wua.CreateUpdateDownloader()
    downloader.Updates = updates_to_install
    download_result = downloader.Download()

    if download_result.ResultCode != 2:
        logging.error("Error downloading updates.")
        return

    installer = wua.CreateUpdateInstaller()
    installer.Updates = updates_to_install
    installation_result = installer.Install()

    if installation_result.ResultCode == 2:
        print_and_log("Updates installed successfully.")
        if installation_result.RebootRequired:
            print_and_log("A system reboot is required to complete the update installation.", "warning")
            print_and_log("Rebooting...")
            print("reboot")  # This lines allows the server to know that the client needs to reboot
            os.system("shutdown /r /g /t 1")
    else:
        hresult = installation_result.HResult
        for i in range(updates_to_install.Count):
            update_result = installation_result.GetUpdateResult(i)
            update = updates_to_install.Item(i)
            print_and_log(f"Error installing update {update.Title}. Error code: {update_result.ResultCode}, HRESULT: "
                          f"{hresult}", "error")


def start_client_update():
    if is_admin():
        update_windows()
    else:
        logging.error("Please, execute this script in administrator to update the windows pc.")
        sys.exit(1)
