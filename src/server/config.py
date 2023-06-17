class Infos:
    config_json_file = "config.json"
    email_infos_json = "email_infos.json"
    PROJECT_NAME: str = "UpdateGuardian"
    python_version = "3.11"
    python_folder_name = f"Python{python_version.replace('.', '')}"
    python_precise_version = "3.11.3"
    powershell_client_script_installer_name = "Setup_Client.ps1"
    email_send: bool

    @staticmethod
    def get_installer_name() -> str:
        return "python_" + Infos.python_precise_version + ".exe"

    @staticmethod
    def get_server_python_installer_name():
        path: str = "python_" + Infos.python_precise_version + ".exe"
        return path
