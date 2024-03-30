import json
import os.path
import unittest

from src.server.commands.path_functions import find_file
from src.server.data.computer import Computer


class ComputerTest(unittest.TestCase):
    def setUp(self):
        self.logs_filename = "test.log"
        self.logs_filename2 = "test2.log"
        with open(find_file("computers_database.json"), "r") as f:
            data = json.load(f)

        self.computer = Computer(data["PC-PRET-02"], self.logs_filename)
        self.computer2 = Computer(data["PC-PRET-02"], self.logs_filename2)

    def tearDown(self):
        self.computer.close_logger()
        self.computer2.close_logger()
        os.remove(find_file(self.logs_filename))
        os.remove(find_file(self.logs_filename2))

    def test_does_file_exist(self):
        self.assertTrue(os.path.exists(find_file(self.logs_filename)))
        self.assertTrue(os.path.exists(find_file(self.logs_filename2)))

    def test_does_loggers_work(self):
        self.computer.log("info", "test")
        self.computer2.log("info", "test2")
        self.computer.log("warning", "test")
        self.computer2.log("warning", "test2")
        self.computer.log("error", "test")
        self.computer2.log("error", "test2")

        # Read log file content
        with open(find_file(self.logs_filename), "r") as f:
            log_content = f.read()

        # Check the number of lines and content of each line
        log_lines = log_content.splitlines()
        self.assertEqual(len(log_lines), 3)
        self.assertIn("test", log_lines[0])
        self.assertIn("INFO", log_lines[0])
        self.assertIn("test", log_lines[1])
        self.assertIn("WARNING", log_lines[1])
        self.assertIn("test", log_lines[2])
        self.assertIn("ERROR", log_lines[2])

        # Read log file content for computer2
        with open(find_file(self.logs_filename2), "r") as f:
            log_content2 = f.read()

        # Check the number of lines and content of each line for computer2
        log_lines2 = log_content2.splitlines()
        self.assertEqual(len(log_lines2), 3)
        self.assertIn("test2", log_lines2[0])
        self.assertIn("INFO", log_lines2[0])
        self.assertIn("test2", log_lines2[1])
        self.assertIn("WARNING", log_lines2[1])
        self.assertIn("test2", log_lines2[2])
        self.assertIn("ERROR", log_lines2[2])
