import os
import subprocess
import sys

import git
from git.exc import GitCommandError

from src.server.infrastructure.paths import ServerPath
from src.server.logs_management.server_logger import log, log_error


class AutoUpdateProgram:
    """
    Class used to manage the automatic update of the server.
    It uses GitHub and gitpython to update the server.
    Only the main branch is used.
    Before updating, the server_ip variable in the .ps1 file is preserved,
    and files that are ignored or not tracked by Git are also preserved.
    """
    def __init__(self, repo_path, force_update=False):
        self.repo_path = repo_path
        self.ps1_file_path = ServerPath.get_powershell_client_script_installer_path()
        self.force_update = force_update
        self.server_ip = None

    def save_server_ip(self):
        """
        Saves the server_ip variable from the .ps1 file.
        """
        with open(self.ps1_file_path, 'r') as file:
            for line in file:
                if line.strip().startswith('$server_ip'):
                    self.server_ip = line.strip().split('=')[1].strip()
                    log(f"Saved server_ip: {self.server_ip}")
                    break

    def restore_server_ip(self):
        """
        Restores the server_ip variable to the .ps1 file.
        """
        with open(self.ps1_file_path, 'r') as file:
            lines = file.readlines()
        with open(self.ps1_file_path, 'w') as file:
            for line in lines:
                if line.strip().startswith('$server_ip'):
                    file.write(f'$server_ip = {self.server_ip}\n')
                else:
                    file.write(line)
        log("Restored server_ip in the .ps1 file.")

    def preserve_untracked_files(self):
        """
        Preserves untracked or ignored files by stashing them before update.
        """
        repo = git.Repo(self.repo_path)
        untracked_files = repo.untracked_files
        if untracked_files:
            repo.git.stash('save', '--keep-index', '--include-untracked')
            log("Untracked files have been stashed.")
        return untracked_files

    def restore_untracked_files(self, untracked_files):
        """
        Restores untracked files from stash after update.
        """
        if untracked_files:
            repo = git.Repo(self.repo_path)
            repo.git.stash('pop')
            log("Untracked files have been restored from stash.")

    def update(self):
        """
        Checks for updates and applies them if available.
        """
        try:
            repo = git.Repo(self.repo_path)
            current_branch = repo.active_branch
            repo.remotes.origin.fetch()

            local_commit = repo.head.commit
            remote_commit = repo.remotes.origin.refs.main.commit

            if local_commit != remote_commit:
                log('New updates detected. Applying changes...')
                self.save_server_ip()
                untracked_files = self.preserve_untracked_files()
                repo.git.reset('--hard', 'origin/main')
                self.restore_untracked_files(untracked_files)
                self.restore_server_ip()
                log("Restarting the application to apply updates...")
                self.restart_application()
            else:
                log('No new updates.')
        except GitCommandError as e:
            log_error(f"Error updating the repository: {e}")

    def restart_application(self):
        """
        Restarts the application to apply updates.
        """
        log("Restarting software...", print_formatted=False)
        main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_client.py')
        main_file = os.path.abspath(main_file)
        if self.force_update:
            subprocess.call([sys.executable, main_file, "--force"])
        else:
            subprocess.call([sys.executable, main_file])
        sys.exit(0)
