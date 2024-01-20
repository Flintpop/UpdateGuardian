from src.newServer.core.remote_computers_database import RemoteComputerDatabase
from src.newServer.logs_management.server_logger import log


class ComputerDatabaseManager:
    @staticmethod
    def list_computers():
        computer_database = RemoteComputerDatabase.load_computer_data()
        print(computer_database)

    @staticmethod
    def shutdown_all_computers() -> None:
        """Calls shutdown_all_computers() method after having loaded the data from scratch"""
        log("Shutting down all computers...")
        computer_database: RemoteComputerDatabase = RemoteComputerDatabase.load_computer_data()
        computer_database.shutdown_all_computers()
        log("All computers have been shut down.")
