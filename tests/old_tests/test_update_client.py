import unittest
from unittest.mock import patch, MagicMock
from src.client.update_windows import get_updates_info


class TestGetUpdatesInfo(unittest.TestCase):
    def setUp(self):
        self.json_file_path = "C:\\Temp\\updateguardian\\update_status.json"
        self.file_exists_mock = MagicMock()
        self.check_file_empty_mock = MagicMock()
        self.process_json_file_mock = MagicMock()
        self.handle_json_decode_error_mock = MagicMock()
        self.handle_file_not_found_error_mock = MagicMock()
        self.handle_general_error_mock = MagicMock()

@patch('src.client.update_windows.file_exists', new_callable=MagicMock)
@patch('src.client.update_windows.check_file_empty', new_callable=MagicMock)
@patch('src.client.update_windows.process_json_file', new_callable=MagicMock)
@patch('src.client.update_windows.handle_json_decode_error', new_callable=MagicMock)
@patch('src.client.update_windows.handle_file_not_found_error', new_callable=MagicMock)
@patch('src.client.update_windows.handle_general_error', new_callable=MagicMock)
def test_get_updates_info(self, mock_general_error, mock_file_not_found_error, mock_json_decode_error, mock_process_json_file, mock_check_file_empty, mock_file_exists):
    # Ici, vous devez utiliser les mocks passés en argument (par exemple, mock_file_exists) au lieu des mocks définis dans setUp
    mock_file_exists.return_value = True
    mock_check_file_empty.return_value = False
    mock_process_json_file.return_value = (True, {"status": "OK"})

    result = get_updates_info()

    mock_file_exists.assert_called_once_with(self.json_file_path, False)
    mock_check_file_empty.assert_called_once_with(self.json_file_path)
    mock_process_json_file.assert_called_once_with(self.json_file_path)
    self.assertEqual(result, {"status": "OK"})


if __name__ == '__main__':
    unittest.main()
