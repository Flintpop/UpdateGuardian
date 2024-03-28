# -----------------------------------------------------------
# http_server_setup.py
# Author: darwh
# Date: 02/05/2023
# Description: File that is used to set up the HTTP server.
# This server is used to receive the whoami command and send the SSH public keys to the clients.
# -----------------------------------------------------------
import ctypes
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from src.newServer.infrastructure.config import Infos
from src.newServer.infrastructure.paths import ServerPath
from typing import TYPE_CHECKING

from src.newServer.core.remote_computers_database import RemoteComputerDatabase
if TYPE_CHECKING:
    from src.newServer.core.remote_computer_manager import RemoteComputerManager
from src.newServer.logs_management.server_logger import log, log_error, log_new_lines

authorized_keys_directory = ServerPath.get_ssh_keys_folder()
if not ServerPath.exists(authorized_keys_directory):
    os.makedirs(authorized_keys_directory)
    if not ServerPath.exists(authorized_keys_directory):
        log_error("Could not create the SSH keys directory.")
        sys.exit(1)

authorized_keys_file = ServerPath.join(authorized_keys_directory, Infos.authorized_keys_filename)


# This is for Windows only
class PowerInformation(ctypes.Structure):
    """
    Class used to get the power information on Windows.
    """
    _fields_ = [('ACLineStatus', ctypes.c_byte),
                ('BatteryFlag', ctypes.c_byte),
                ('BatteryLifePercent', ctypes.c_byte),
                ('SystemStatusFlag', ctypes.c_byte),
                ('BatteryLifeTime', ctypes.c_ulong),
                ('BatteryFullLifeTime', ctypes.c_ulong)]


class LastInputInfo(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_ulong)]


def set_sleep_timeout(ac_dc, timeout):
    if os.name == 'nt':
        os.system(f'powercfg -change -standby-timeout-{ac_dc} {timeout}')
    else:
        log_error("Set sleep timeout function is only available on Windows.")


def prevent_sleep():
    # Disable sleep mode
    set_sleep_timeout('ac', 0)
    set_sleep_timeout('dc', 0)


def allow_sleep():
    # Restore the original sleep timeouts
    set_sleep_timeout('ac', "30")
    set_sleep_timeout('dc', "30")


class MyRequestHandler(BaseHTTPRequestHandler):
    """
    Class that handles the HTTP requests so that the server can receive the whoami command and send the SSH public
    keys to the clients.
    """
    # computer_database: ComputerDatabase = ComputerDatabase.load_computer_data_if_exists()
    computer_database: 'RemoteComputerDatabase' = RemoteComputerDatabase.load_computer_data_if_exists()

    # noinspection PyShadowingBuiltins
    def log_message(self, format, *args):
        return

    # noinspection PyPep8Naming
    def do_POST(self):
        """
        Handles the POST requests.

        The POST requests are used to receive the whoami command.
        """
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

        # The MAC address is received with dashes, but the database uses colons.
        received_data["mac_address"] = received_data["mac_address"].replace("-", ":")
        host_key = received_data["host_key"]

        # Tries to add the new computer to the database.
        if not self.computer_database.add_new_computer(received_data, host_key):
            log_error("Could not add the new computer to the database. It is probably already in the database.")
            log_error(f"Received data: {json.dumps(received_data, indent=4)}")
            log_error(f"Current database:\n {self.computer_database}")
            return

        log(f"Received data: {json.dumps(received_data, indent=4)}", print_formatted=False)
        log(f"Current database:\n {self.computer_database}", print_formatted=False)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Received data.")

        print("Write 'stop' to stop the server.")
        print("> ", end="")

    # noinspection PyPep8Naming
    def do_GET(self):
        """
        Handles the GET requests.

        The GET requests are used to send the SSH public keys to the clients.
        """
        log_new_lines()
        if "/get_public_key" not in self.path:
            self.send_response(404, "Page not found.")
            return

        hostname_index: int = 2
        hostname: str = self.path.split("/")[hostname_index]
        computer: 'RemoteComputerManager' = self.computer_database.find_computer(hostname)

        if not computer:
            self.send_error(404, f"Computer with hostname '{hostname}' not found.")
            return

        # Get and generate the public key
        public_key = computer.get_public_key()

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        # Sends the public key to the client.
        self.wfile.write(public_key.encode())


keep_running = True


def stop_server():
    global keep_running
    keep_running = False


def wait_for_stop(httpd):
    """
    Waits for the user to write 'stop' in the console to stop the server.
    """
    while True:
        log("Press 'stop' to stop the server", print_formatted=False)
        cmd = input('> ')
        if cmd.lower() == "stop":
            httpd.shutdown()
            break


def run_server(server_class=HTTPServer, handler_class=MyRequestHandler, port=8000) -> bool:
    """
    Runs the HTTP server used to receive the whoami command and send the SSH public keys to the clients.
    """
    # If on windows do prevent sleep
    if os.name == 'nt':
        prevent_sleep()
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    log(f"Starting server on port {port}", print_formatted=False)

    MyRequestHandler.computer_database = RemoteComputerDatabase.load_computer_data_if_exists()
    server_thread = threading.Thread(target=httpd.serve_forever)
    # Start a thread with the server -- that thread will then start one more thread for each request
    server_thread.start()

    wait_for_stop(httpd)

    server_thread.join()

    log(f"Stopping server on port {port}", print_formatted=False)
    httpd.server_close()

    if os.name == 'nt':
        allow_sleep()

    if len(MyRequestHandler.computer_database.computers_json) == 0:
        log_error("The database is empty, so it will not be saved.", print_formatted=False)
        log_error("The set up is not complete and has failed.", print_formatted=False)
        return False

    log("Saving database...", print_formatted=False)
    log(f"The database looks like this: \n{MyRequestHandler.computer_database}", print_formatted=False)
    MyRequestHandler.computer_database.save_computer_data(MyRequestHandler.computer_database.computers_json)
    return True
