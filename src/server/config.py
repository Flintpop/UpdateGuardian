class Infos:
    python_main_script_path = None
    PROJECT_NAME: str = "UpdateGuardian"
    python_version = "3.11"
    python_folder_name = f"Python{python_version.replace('.', '')}"
    python_precise_version = "3.11.3"

    @staticmethod
    def get_installer_name() -> str:
        return "python_" + Infos.python_precise_version + ".exe"

    @staticmethod
    def get_server_python_installer_name():
        path: str = "python_" + Infos.python_precise_version + ".exe"
        return path
