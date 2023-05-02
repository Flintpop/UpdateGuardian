import sys
import time
import threading
import warnings

from pytz_deprecation_shim import PytzUsageWarning
from apscheduler.schedulers.background import BackgroundScheduler

from src.server.commands.install_update import update_all_computer
from src.server.data.computer_database import ComputerDatabase
from src.server.data.local_network_data import Data
from src.server.environnement.modify_settings import modify_settings
from src.server.environnement.setup import server_setup, get_launch_time
from src.server.environnement.server_logs import log, log_new_lines

function_executed: bool = False

warnings.filterwarnings("ignore", category=PytzUsageWarning)

stopped: bool = False


def execute_job() -> None:
    log("Executing scheduled task...")

    log_new_lines(2)

    computer_database: ComputerDatabase = ComputerDatabase.load_computer_data()

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
        while True:
            time.sleep(20)  # Sleep for 20 seconds, then check again if the scheduled time has been reached.
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log("Program stopped.")
        sys.exit(0)


def force_start_execute_job():
    execute_job()


def stop_code():
    global stopped
    log("Program stopped.")
    stopped = True


def settings_thread() -> None:
    log("Program started, settings loaded", print_formatted=False)
    log_new_lines()
    global stopped
    while not stopped:
        scheduled_time = get_launch_time()

        day, hour = scheduled_time['day'], scheduled_time['hour']
        print(f"The program is scheduled to start every {day} at {hour}:00.\n")
        print("Type 'modify' to modify settings.")
        print("Type 'force' to force start the scheduled task.")
        print("Type 'exit' to exit the program.\n")
        try:
            usr_input = input("> ")
            switcher = {
                "modify": modify_settings,
                "force": force_start_execute_job,
                "exit": stop_code
            }
            switcher.get(usr_input, lambda: print("Invalid input."))()
        except KeyboardInterrupt:
            log("Program stopped.", print_formatted=False)
            stop_code()
            break


def main_loop() -> None:
    setup_data = Data()

    if not server_setup():
        exit(1)

    get_launch_time()

    launch_thread = threading.Thread(target=launch_software)
    launch_thread.start()

    settings_thread()

    launch_thread.join()
    exit(0)


if __name__ == '__main__':
    main_loop()
