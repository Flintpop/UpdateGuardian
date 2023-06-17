import git
import os
import sys

from src.server.environnement.server_logs import log


def check_for_update_and_restart():
    # Path to your repository
    repo_path = 'path_to_your_repository'
    repo = git.Repo(repo_path)

    # Fetch the remote repository
    repo.remotes.origin.fetch()

    # Check if the local commit is the latest
    local_commit = repo.head.commit
    remote_commit = repo.remotes.origin.refs.main.commit

    if local_commit != remote_commit:
        log('New commit detected. Pulling changes...', print_formatted=False)

        # Pull new changes
        repo.git.pull()

        # Restart the script
        log("Restarting script...", print_formatted=False)
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        log('No new commits.', print_formatted=False)
