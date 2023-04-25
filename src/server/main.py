import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler

from src.server.commands.install_update import update_all_computer
from src.server.data.computer_database import ComputerDatabase
from src.server.data.local_network_data import Data
from src.server.data.logs import add_spaces_logging_file, print_and_log
from src.server.data.setup import server_setup, get_launch_time

function_executed: bool = False


def execute_job():
    print("Executing scheduled task...")

    add_spaces_logging_file(server_setup=False)
    computer_database = ComputerDatabase()
    update_all_computer(computer_database)


def launch_software(data: Data) -> None:
    add_spaces_logging_file(server_setup=True)
    server_setup(data)

    data.load_computer_data()

    scheduled_time = get_launch_time()

    day, hour = scheduled_time['day'], scheduled_time['hour']

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        execute_job, "cron", day_of_week=day[:3].lower(), hour=hour, minute=00, args=(data,)
    )

    scheduler.start()

    print_and_log(f"The program is scheduled to launch on {day} at {hour} o'clock.")

    try:
        while True:
            time.sleep(20)  # Sleep for 20 seconds, then check again if the scheduled time has been reached.
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        sys.exit(0)


def main_loop() -> None:
    data = Data()

    launch_software(data)


if __name__ == '__main__':
    main_loop()
