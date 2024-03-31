from src.server.infrastructure.paths import ServerPath
from src.server.logs_management.server_logger import log, log_error
from src.server.update.auto_update import AutoUpdate


class AutoUpdateFactory:
    @staticmethod
    def create_auto_update(force_update: bool) -> AutoUpdate:
        """
        Creates an AutoUpdate object. The object is used to update the server,
        and then restart the app (server side).
        """
        return AutoUpdate(
            ps1_file_path=ServerPath.get_powershell_client_script_installer(),
            repo_path=ServerPath.get_project_root(),
            main_file=ServerPath.get_main_file(),
            force_update=force_update,
            log=log,
            log_error=log_error
        )
