# -----------------------------------------------------------
# test_http_server_setup.py
# Author: darwh
# Date: 02/05/2023
# Description: Tests for the HTTP server.
# -----------------------------------------------------------
import unittest
import os
import json
import tempfile
import shutil
from http.server import HTTPServer
from threading import Thread

import requests

from src.server.environnement.http_server_setup import MyRequestHandler


class TestHTTPServerSetup(unittest.TestCase):
    def setUp(self):
        self.port = 8000
        self.server = HTTPServer(("", self.port), MyRequestHandler)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.temp_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.temp_dir)
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def test_do_POST(self):
        url = f"http://localhost:{self.port}"
        data = {
            "username": "TEST-PC\\darwh",
            "hostname": "DESKTOP90UERF",
            "mac_address": "00:00:00:00:00:00"
        }

        headers = {'Content-type': 'application/json'}

        response = requests.post(url, data=json.dumps(data), headers=headers)

        self.assertEqual(response.status_code, 200)

    def test_do_GET_public_key(self):
        with open("public_key_TEST-PC.pub", "w") as f:
            f.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHxP6oVQerX9Tb7V1UsTcJmIv2QrraNf6Eyyh6GAXx6C")

        response = requests.get(f"http://localhost:{self.port}/get_public_key/TEST-PC")

        self.assertEqual(response.status_code, 200)
        public_key = response.text
        self.assertEqual(public_key, "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHxP6oVQerX9Tb7V1UsTcJmIv2QrraNf6Eyyh6GAXx6C")

    def test_do_GET_not_found(self):
        response = requests.get(f"http://localhost:{self.port}/nonexistent")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
