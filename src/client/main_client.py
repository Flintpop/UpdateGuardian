import logging

from update_windows import start_client_update

LOGS_FILENAME: str = "update_windows.log"
logging.basicConfig(level=logging.INFO, filename=LOGS_FILENAME, filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")


def add_spaces_logging_file() -> None:
    write_spaces: bool = False
    with open(LOGS_FILENAME, "r") as f:
        if len(f.readline()) > 1:
            write_spaces = True

    if write_spaces:
        with open(LOGS_FILENAME, "a") as f:
            f.write("\n\n")


def main_loop() -> None:
    # Lancer les mises à jour avec la fonction update_windows() définie précédemment
    add_spaces_logging_file()

    logging.info("Starting client update script...")

    start_client_update()


if __name__ == '__main__':
    main_loop()
