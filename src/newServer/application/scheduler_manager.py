from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time


class SchedulerManager:
    def __init__(self, update_manager, setup_manager):
        self.scheduler = BackgroundScheduler()
        self.update_manager = update_manager
        self.setup_manager = setup_manager
        self.launch_thread = None
        self.stopped = False

    def launch_software(self):
        # Configure l'heure de lancement à partir du fichier de configuration
        launch_time = self.setup_manager.get_launch_time()

        # Ajoute la tâche de mise à jour au planificateur
        self.scheduler.add_job(
            self.update_manager.execute_update,
            'cron',
            day_of_week=launch_time['day'][:3].lower(),
            hour=launch_time['hour'],
            minute=0
        )

        self.scheduler.start()
        try:
            while not self.stopped:
                time.sleep(2)  # Pause de 2 secondes
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            print("Scheduler stopped.")
            raise

    def start(self):
        self.launch_thread = threading.Thread(target=self.launch_software)
        self.launch_thread.start()

    def stop(self):
        self.stopped = True
        self.scheduler.shutdown(wait=False)
        if self.launch_thread is not None:
            self.launch_thread.join()

    def join(self):
        if self.launch_thread is not None:
            self.launch_thread.join()
