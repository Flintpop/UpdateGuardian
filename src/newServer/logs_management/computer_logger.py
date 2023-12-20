import logging
import os

from newServer.infrastructure.paths import ServerPath


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
        if not os.path.isdir(ServerPath.get_log_folder_path()):
            os.mkdir("logs")

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

    def log_error(self, msg: str, new_lines=0) -> None:
        self.log(level="error", message=msg, new_lines=new_lines)

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
