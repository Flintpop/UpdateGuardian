import logging
import os

from src.server.commands.path_functions import change_directory_to_root_folder
from src.server.data.computer import ComputerLogger


# Create a custom logging handler that writes messages to a log file and the console
class PrintAndLogHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)  # Write the message to the console
        with open(os.path.join('logs', 'log_file.log'), 'a') as log_file:  # Write the message to the log file
            log_file.write(self.format(record) + '\n')


class ServerLogs(ComputerLogger):
    def __init__(self, logs_filename: str = "server_logs.log"):
        change_directory_to_root_folder()
        logs_filename = os.path.join("logs", logs_filename)
        super().__init__(logs_filename, "New server session")
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    def emit(self, record, print_formatted: bool = True):
        formatted_record = self.formatter.format(record)
        if print_formatted:
            print(formatted_record)  # Print the message to the console
        else:
            print(record.message)
        with open(self.logs_filename, 'a') as log_file:  # Write the message to the log file
            log_file.write(formatted_record + '\n')

    def log_error(self, message: str, print_formatted: bool = True) -> None:
        self.log(level="error", message=message, print_formatted=print_formatted)

    def log(self, message: str, level: str = "info", new_lines: int = 0, print_formatted: bool = True) -> None:
        """
        Prints to the console, and log to the logfile of the server, the message.
        :param message: The message to print
        :param level: The level of the message, e.g. "info", or "error"
        :param new_lines: The number of new lines to print before the message
        :param print_formatted: If True, the message will be printed with the date and the level, else it will be
        printed like a normal print
        :return: None
        """
        message = "\n" * new_lines + message
        record = self.logger.makeRecord(
            self.logger.name,
            logging.getLevelName(level.upper()),
            None,
            0,
            message,
            None,
            None
        )
        self.emit(record, print_formatted=print_formatted)  # Call emit method for ServerLogs only


server_logs: ServerLogs = ServerLogs()
log = server_logs.log
log_error = server_logs.log_error
log_new_lines = server_logs.log_add_vertical_space
add_log_memory = server_logs.add_log_memory

if __name__ == '__main__':
    lo = ServerLogs()
    lo.log("test")
    lo.log_error("test")
