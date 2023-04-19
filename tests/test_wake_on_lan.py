import unittest

from src.server.wake_on_lan.wake_on_lan_password import generate_secureon_password
from src.server.wake_on_lan.wake_on_lan_utils import is_secureon_password_valid, send_wol_with_secureon


class TestWakeOnLan(unittest.TestCase):
    def test_is_secureon_password_valid(self):
        self.assertTrue(is_secureon_password_valid("AB:CD:EF:12:34:56"))
        self.assertTrue(is_secureon_password_valid("ab:cd:ef:12:34:56"))

        self.assertFalse(is_secureon_password_valid("AB:CD:EF:12:34:5Z"))
        self.assertFalse(is_secureon_password_valid("AB:CD:EF:12:34"))
        self.assertFalse(is_secureon_password_valid("AB:CD:EF:12:34:56:78"))

        print("Tous les tests de is_secureon_password_valid ont réussi.")

    def test_send_wol_with_secureon(self):
        mac_address = "00:11:22:33:44:55"
        secureon_password = "AB:CD:EF:12:34:56"

        try:
            send_wol_with_secureon(mac_address, secureon_password)
        except Exception as e:
            print(f"Le test de send_wol_with_secureon a échoué : {e}")
            raise e
        else:
            print("Le test de send_wol_with_secureon a réussi.")

    def test_wake_on_lan_password_generation(self):
        for _ in range(1000):
            self.assertTrue(is_secureon_password_valid(generate_secureon_password()))
            self.assertTrue(is_secureon_password_valid(generate_secureon_password()))
            self.assertTrue(is_secureon_password_valid(generate_secureon_password()))
            self.assertTrue(is_secureon_password_valid(generate_secureon_password()))
