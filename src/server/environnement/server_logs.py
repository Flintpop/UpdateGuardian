import logging
import os

from src.server.commands.path_functions import change_directory_to_root_folder


class ComputerLogger:
    """
    Class to log messages from a computer.
    It is used to log messages of a computer in a file, and to display them in the console.
    """

    def __init__(self, logs_filename: str, new_msg_header: str = "New computer session"):
        self.logs_filename = logs_filename
        self.logger = self.setup_logger(new_msg_header=new_msg_header)
        self.current_log_message: str = ""

    def setup_logger(self, new_msg_header: str) -> logging.Logger:
        logger = logging.getLogger(self.logs_filename)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            file_handler = logging.FileHandler(filename=self.logs_filename, encoding="utf-8")
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.setup_log_file(new_msg_header=new_msg_header)

        return logger

    def log(self, message: str, level: str = "info", new_lines: int = 0) -> None:
        message = "\n" * new_lines + message
        if level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.logger.error(message)
        elif level.lower() == "critical":
            self.logger.critical(message)
        else:
            self.logger.debug(message)

    def close_logger(self) -> None:
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def add_log_memory(self, message: str = "") -> None:
        self.current_log_message += message + "\n"

    def log_from_memory(self, level: str = "info") -> None:
        self.log(message=self.current_log_message, level=level)
        self.current_log_message = ""

    @staticmethod
    def get_header_style_string(header_txt: str) -> str:
        width = len(header_txt) * 4
        edge = "═" * width
        padding = " " * 3  # Add 3 spaces for padding

        header = f"╔{edge}╗\n║{padding}{header_txt.center(width - 6)}{padding}║\n╚{edge}╝"
        return header

    def setup_log_file(self, new_msg_header: str) -> None:
        write_lines: bool = False
        with open(self.logs_filename, "r", encoding="utf-8") as f:
            if len(f.read()) > 1:
                write_lines = True

        if write_lines:
            with open(self.logs_filename, "a", encoding="utf-8") as f:
                f.write("\n\n")

        # Write the header
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            f.write(self.get_header_style_string(header_txt=new_msg_header) + "\n")

    def log_add_vertical_space(self, new_lines: int = 1, print_in_console: bool = False) -> None:
        """
        To make the logs more readable, add a vertical space in the log file and in the console.
        :param new_lines: The number of new lines to add.
        :return: Nothing.
        """
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            new_lines: str = "\n" * new_lines
            f.write(new_lines)

        if print_in_console:
            print(new_lines.split("\n").pop(0))

    def log_raw(self, param):
        """
        Log a raw object, without the formatter.
        :param param: The object to log.
        :return: Nothing.
        """
        with open(self.logs_filename, "a", encoding="utf-8") as f:
            f.write(str(param) + "\n")


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
