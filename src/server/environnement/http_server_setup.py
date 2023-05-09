# -----------------------------------------------------------
# http_server_setup.py
# Author: darwh
# Date: 02/05/2023
# Description: File that is used to set up the HTTP server.
# This server is used to receive the whoami command and send the SSH public keys to the clients.
# -----------------------------------------------------------
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from src.server.commands.path_functions import find_directory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer

from src.server.data.computer_database import ComputerDatabase
from src.server.environnement.server_logs import log, log_error, log_new_lines

authorized_keys_filename = "authorized_keys.json"
authorized_keys_directory = find_directory("ssh_keys")
if authorized_keys_directory is None:
    os.mkdir(os.path.join("src", "server", "data", "ssh_keys"))
authorized_keys_directory = find_directory("ssh_keys")
if authorized_keys_directory is None:
    log_error("Could not create the 'ssh_keys' directory.")
    exit(1)
authorized_keys_file = os.path.join(authorized_keys_directory, authorized_keys_filename)


class MyRequestHandler(BaseHTTPRequestHandler):
    """
    Class that handles the HTTP requests so that the server can receive the whoami command and send the SSH public
    keys to the clients.
    """
    computer_database: ComputerDatabase = ComputerDatabase.load_computer_data_if_exists()

    # noinspection PyPep8Naming
    def do_POST(self):
        log_new_lines()
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            log_error("Received an empty request, or without 'Content-Length' parameter.")
            log_error(f"Request: {self} (maybe wrong request object?)")
            return

        body = self.rfile.read(content_length)

        try:
            received_data = json.loads(body.decode())
        except json.decoder.JSONDecodeError:
            log_error("Received data is not a valid JSON.")
            self.send_error(400, "Received data is not a valid JSON.")
            return

        received_data["mac_address"] = received_data["mac_address"].replace("-", ":")

        if not self.computer_database.add_new_computer(received_data):
            log_error("Could not add the new computer to the database. It is probably already in the database.")
            log_error(f"Received data: {received_data}")
            log_error(f"Current database:\n {self.computer_database}")
            return

        log(f"Received data: {received_data}", print_formatted=False)
        log(f"Current database:\n {self.computer_database}", print_formatted=False)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Received data.")

    # noinspection PyPep8Naming
    def do_GET(self):
        log_new_lines()
        if "/get_public_key" not in self.path:
            self.send_response(404, "Page not found.")
            return

        hostname_index: int = 2
        hostname: str = self.path.split("/")[hostname_index]
        computer: 'Computer' = self.computer_database.find_computer(hostname)

        if not computer:
            self.send_error(404, f"Computer with hostname '{hostname}' not found.")
            return

        public_key = computer.get_public_key()

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(public_key.encode())


keep_running = True


def stop_server():
    global keep_running
    keep_running = False


def wait_for_stop(httpd):
    while True:
        log("Press 'stop' to stop the server", print_formatted=False)
        cmd = input('> ')
        if cmd.lower() == "stop":
            httpd.shutdown()
            break


def run_server(server_class=HTTPServer, handler_class=MyRequestHandler, port=8000) -> bool:
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    log(f"Starting server on port {port}", print_formatted=False)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()

    wait_for_stop(httpd)

    server_thread.join()

    log(f"Stopping server on port {port}", print_formatted=False)
    httpd.server_close()

    if len(MyRequestHandler.computer_database.computers_json) == 0:
        log_error("The database is empty, so it will not be saved.", print_formatted=False)
        log_error("The set up is not complete and has failed.", print_formatted=False)
        return False

    log("Saving database...", print_formatted=False)
    log(f"The database looks like this: \n{MyRequestHandler.computer_database}", print_formatted=False)
    MyRequestHandler.computer_database.save_computer_data(MyRequestHandler.computer_database.computers_json)
    return True
