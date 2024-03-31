import os
import subprocess
import sys

import git
from git.exc import GitCommandError


# noinspection PyShadowingNames
class AutoUpdate:
    """
    Class used to manage automatic update of the server.
    It uses GitHub and gitpython to update the server.
    Only the main branch is used.
    Before updating, the server_ip variable in the .ps1 file is preserved,
    and files that are ignored or not tracked by Git are also preserved.
    """

    def __init__(self, main_file: str, repo_path: str, log, log_error, ps1_file_path: str, force_update=False):
        self.main_file = main_file
        self.repo_path = repo_path
        self.ps1_file_path = ps1_file_path
        self.force_update = force_update
        self.server_ip = None
        self.log = log
        self.log_error = log_error

    def save_server_ip(self):
        """
        Saves the server_ip variable from the .ps1 file.
        """
        with open(self.ps1_file_path, 'r') as file:
            for line in file:
                if line.strip().startswith('$server_ip'):
                    self.server_ip = line.strip().split('=')[1].strip()
                    self.log(f"Saved server_ip: {self.server_ip}", print_formatted=False)
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
        self.log("Restored server_ip in the .ps1 file.", print_formatted=False)

    def preserve_untracked_files(self):
        """
        Preserves untracked or ignored files by stashing them before update.
        """
        repo = git.Repo(self.repo_path)
        untracked_files = repo.untracked_files
        if untracked_files:
            repo.git.stash('save', '--keep-index', '--include-untracked')
            self.log("Untracked files have been stashed.", print_formatted=False)
        return untracked_files

    def restore_untracked_files(self, untracked_files):
        """
        Restores untracked files from stash after update.
        """
        if untracked_files:
            repo = git.Repo(self.repo_path)
            repo.git.stash('pop')
            self.log("Untracked files have been restored from stash.", print_formatted=False)

    def update(self):
        """
        Checks for updates and applies them if available.
        """
        try:
            repo = git.Repo(self.repo_path)

            if repo.active_branch.name != 'main':
                self.log("The active branch is not 'main'. Cancelling update..."
                         "Please switch to the 'main' (stable) branch of the software before updating "
                         "and running the app. \nRun the command : 'git checkout main' to update the software.")
                return

            repo.remotes.origin.fetch()

            local_commit = repo.head.commit
            remote_commit = repo.remotes.origin.refs.main.commit

            if local_commit != remote_commit:
                self.log('New updates detected. Applying changes...', print_formatted=False)
                self.save_server_ip()
                untracked_files = self.preserve_untracked_files()
                repo.git.reset('--hard', 'origin/main')
                self.restore_untracked_files(untracked_files)
                self.restore_server_ip()
                self.log("Restarting the application to apply updates...", print_formatted=False)
                self.restart_application()
            else:
                self.log('No new updates.', print_formatted=False)
        except GitCommandError as e:
            self.log_error(f"Error updating the repository: {e}", print_formatted=False)

    def restart_application(self):
        """
        Restarts the application to apply updates.
        """
        self.log("Restarting software...", print_formatted=False)
        main_file = self.main_file
        if not os.path.exists(main_file):
            self.log_error(f"Main file not found: {main_file}. Could not restart the application. Exiting...",
                           print_formatted=False)
            sys.exit(1)

        if self.force_update:
            subprocess.call([sys.executable, main_file, "--force"])
        else:
            subprocess.call([sys.executable, main_file])
        sys.exit(0)
