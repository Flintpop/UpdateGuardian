import ctypes
import sys
import logging

import win32com.client


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(e)
        return False


def update_windows():
    wua = win32com.client.Dispatch("Microsoft.Update.Session")
    searcher = wua.CreateUpdateSearcher()
    logging.info("Searching for new updates...")
    search_result = searcher.Search("IsInstalled=0 and Type='Software'")
    updates_to_install = win32com.client.Dispatch("Microsoft.Update.UpdateColl")

    if search_result.Updates.Count == 0:
        logging.info("No updates found.")
        return
    else:
        logging.info(f"{search_result.Updates.Count} update(s) found.")

    for update in search_result.Updates:
        logging.info(f"Update {update.Title} is available.")

    if updates_to_install.Count == 0:
        logging.info("No automatic updates found.")
        return

    installer = wua.CreateUpdateInstaller()
    installer.Updates = updates_to_install
    installation_result = installer.Install()

    if installation_result.ResultCode == 2:
        logging.info("Updates installed successfully.")
    else:
        logging.error(f"Error, could not install updates. Error code: {installation_result.ResultCode}")


def start_client_update():
    if is_admin():
        update_windows()
    else:
        logging.error("Please, execute this script in administrator to update the windows pc.")
        sys.exit(1)
