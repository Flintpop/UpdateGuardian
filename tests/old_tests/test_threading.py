import unittest

from src.server.data.generate_json import generate_flawed_json
from src.server.data.local_network_data import Data


class TestThreading(unittest.TestCase):
    def test_threading(self):
        generate_flawed_json(13)
        Data('test.json')
        # launch_software(data)
