import git
import os
import sys

from src.server.environnement.server_logs import log


# TODO: Tester avec un nouveau repo git.
#  Tester avec d'autres, différentes branches.
#  Tester avec de nouveaux changements, et voir si le script se relance bien.
def check_for_update_and_restart():
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
        log('New commit detected. Pulling changes...', print_formatted=False)

        # Pull new changes
        repo.git.pull()

        # Restart the script
        log("Restarting script...", print_formatted=False)
        os.execl(sys.executable, sys.executable, *sys.argv)
        sys.exit(0)
    else:
        log('No new commits.', print_formatted=False)
