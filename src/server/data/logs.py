import logging
import os


# Create a custom logging handler that writes messages to a log file and the console
class PrintAndLogHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)  # Write the message to the console
        with open(os.path.join('logs', 'log_file.log'), 'a') as log_file:  # Write the message to the log file
            log_file.write(self.format(record) + '\n')


# Configure the logger and set the logging level to INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove any default handlers from the logger
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add the custom logging handler to the logger
handler = PrintAndLogHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
logger.addHandler(handler)


def add_spaces_logging_file(server_setup: bool = False) -> None:
    write_spaces: bool = False
    logs_path: str = os.path.join("logs", "log_file.log")
    if not os.path.exists(logs_path):
        write_spaces = True
        with open(logs_path, "w") as f:
            f.write("")

    if not write_spaces:
        with open(logs_path, "r") as f:
            if len(f.readline()) > 1:
                write_spaces = True

    with open(logs_path, "a") as f:
        if write_spaces:
            f.write("\n\n\n")
        if server_setup:
            f.write("Setup server\n\n")
        else:
            f.write("New session\n\n")


# Define a custom print function that logs messages using the logger
def print_and_log(message="", level=logging.INFO):
    if "error" in message:
        level = logging.ERROR
    logger.log(level, message)

# Example usage
# print_and_log("This message will be printed to the console and written to the log file without duplication.")
