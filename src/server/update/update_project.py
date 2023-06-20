import subprocess

import git
import os
import sys

from src.server.environnement.server_logs import log


def check_for_update_and_restart(args=""):
    # Path to your repository
    repo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
    repo_path = os.path.abspath(repo_path)
    repo = git.Repo(repo_path)

    # Fetch the remote repository
    repo.remotes.origin.fetch()

    # Reset the local repository's main branch to match the remote repository stable branch
    repo.git.checkout('main')

    # Check if the local commit is the latest
    local_commit = repo.head.commit
    remote_commit = repo.remotes.origin.refs.main.commit

    if local_commit != remote_commit:
        log('New updates detected. Applying changes...', print_formatted=False)

        # Pull new changes
        repo.git.pull()

        # Restart the script
        log("Restarting software...", print_formatted=False)
        main_file: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'main.py')
        main_file = os.path.abspath(main_file)
        if args == "--force":
            subprocess.call([sys.executable, main_file, args])
            sys.exit(0)
        else:
            subprocess.call([sys.executable, main_file])
            sys.exit(0)
    else:
        log('No new updates.', print_formatted=False)
