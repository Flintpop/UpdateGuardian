import unittest
import random
import json

from src.server.data.generate_json import generate_json, generate_flawed_json
from src.server.data.local_network_data import Data
from src.server.main import launch_software


class TestThreading(unittest.TestCase):
    def test_threading(self):
        generate_flawed_json(13)
        Data('test.json')
        # launch_software(data)
