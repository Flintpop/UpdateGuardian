class Infos:
    """
    Class containing information for the whole program.
    """
    REQUIREMENTS_CLIENT_FILENAME = "requirements_client.txt"
    config_json_file = "config.json"
    email_infos_json = "email_infos.json"
    PROJECT_NAME: str = "updateguardian"
    python_version = "3.11"
    python_folder_name = f"Python{python_version.replace('.', '')}"
    python_precise_version = "3.11.3"
    powershell_client_script_installer_name = "Setup_Client.ps1"
    email_send: bool

    @staticmethod
    def get_server_python_installer_name():
        """
        :returns: The name of the server python installer
        """
        path: str = "python_" + Infos.python_precise_version + ".exe"
        return path
