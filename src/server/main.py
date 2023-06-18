import sys
import time
import threading
import warnings
import os

from src.server.commands.path_functions import change_directory_to_root_folder
from src.server.update.update_project import check_for_update_and_restart
from src.server.warn_admin.mails import setup_email_config

# If running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Add the directory containing your modules to sys.path
    # noinspection PyUnresolvedReferences, PyProtectedMember
    sys.path.append(os.path.join(sys._MEIPASS, 'src/server'))
else:
    # Add the directory containing your modules to sys.path
    sys.path.append(os.path.abspath('src/server'))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change to the script's directory

# noinspection PyUnresolvedReferences
import add_paths  # Import and execute add_paths.py to update sys.path

from pytz_deprecation_shim import PytzUsageWarning
from apscheduler.schedulers.background import BackgroundScheduler

from commands.install_update import update_all_computer
from data.computer_database import ComputerDatabase
from environnement.modify_settings import modify_settings
from environnement.setup import server_setup, get_launch_time, setup_email_config_done
from environnement.server_logs import log, log_new_lines

function_executed: bool = False

warnings.filterwarnings("ignore", category=PytzUsageWarning)

stopped: bool = False


def execute_job_force():
    log("Force executing scheduled task...")
    log_new_lines(2)
    start_program()


def execute_job() -> None:
    log("Executing scheduled task...")

    log_new_lines(2)

    start_program()


def start_program():
    computer_database: ComputerDatabase = ComputerDatabase.load_computer_data()
    computer_database.load_email_infos()

    change_directory_to_root_folder()
    update_all_computer(computer_database)


def launch_software() -> None:
    scheduled_time = get_launch_time()

    day, hour = scheduled_time['day'], scheduled_time['hour']

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        execute_job, "cron", day_of_week=day[:3].lower(), hour=hour, minute=00
    )

    scheduler.start()

    try:
        while not stopped:
            time.sleep(2)  # Sleep for 2 seconds, then check again if the scheduled time has been reached.
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log("Program stopped.")


def force_start_execute_job():
    execute_job_force()


def stop_code():
    global stopped
    stopped = True


def list_computers():
    computer_database: ComputerDatabase = ComputerDatabase.load_computer_data()
    print(computer_database)


def shutdown_all_computers():
    log("Shutting down all computers...")
    computer_database: ComputerDatabase = ComputerDatabase.load_computer_data()
    computer_database.shutdown_all_computers()
    log("All computers have been shut down.")


def settings_thread() -> None:
    log("Program started, settings loaded", print_formatted=False)
    log_new_lines()
    global stopped
    # force_start_execute_job()
    # return
    # noinspection PyUnboundLocalVariable
    while not stopped:
        scheduled_time = get_launch_time()

        day, hour = scheduled_time['day'], scheduled_time['hour']
        print(f"\nThe program is scheduled to start every {day} at {hour}:00.\n")
        print("Type 'settings' to modify settings.")
        print("Type 'force' to force start the scheduled task.")
        print("Type 'list' to list all the computers in the database.")
        print("Type 'shutdown' to shutdown all the computers in the database.")
        print("Type 'exit' to exit the program.\n")
        try:
            usr_input = input("> ")
            switcher = {
                "settings": modify_settings,
                "force": force_start_execute_job,
                "list": list_computers,
                "shutdown": shutdown_all_computers,
                "exit": stop_code
            }
            switcher.get(usr_input, lambda: print("Invalid input."))()
        except KeyboardInterrupt:
            log("Program stopped.", print_formatted=False)
            stop_code()
            break


def main_loop() -> None:
    if not server_setup():
        exit(1)

    get_launch_time()

    if not setup_email_config_done():
        setup_email_config()

    launch_thread = threading.Thread(target=launch_software)
    launch_thread.start()

    settings_thread()

    launch_thread.join()
    exit(0)


if __name__ == '__main__':
    check_for_update_and_restart()
    main_loop()
