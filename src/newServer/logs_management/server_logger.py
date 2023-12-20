import logging

from newServer.infrastructure.paths import ServerPath
from newServer.logs_management.computer_logger import ComputerLogger


class ServerLogs(ComputerLogger):
    """
    Class to log messages from the server.
    """
    def __init__(self, logs_filename: str = "server_logs.log"):
        logs_folder_path: str = ServerPath.get_log_folder_path()
        logs_filename = ServerPath.join(logs_folder_path, logs_filename)
        super().__init__(logs_filename, "New server session")
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    def emit(self, record, print_formatted: bool = True):
        formatted_record = self.formatter.format(record)
        if print_formatted:
            print(formatted_record)
        else:
            print(record.message)
        try:
            with open(self.logs_filename, 'a') as log_file:  # Write the message to the log file
                log_file.write(formatted_record + '\n')
        except FileNotFoundError:
            pass

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
