import requests


# TODO: Does not work for now
def get_latest_github_release(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching release info: {response.status_code}")
        return None


def check_for_updates(current_version):
    user = "flintpop"
    repo = "UpdateGuardian"

    latest_release_info = get_latest_github_release(user, repo)

    if latest_release_info:
        latest_version = latest_release_info["tag_name"]

        if current_version != latest_version:
            print(f"Update available: {current_version} -> {latest_version}")
            print(f"Download the latest release here: {latest_release_info['html_url']}")
        else:
            print("You are using the latest version")


# Your project's current installed version
if __name__ == '__main__':
    current_project_version = "v0.5.0"

    check_for_updates(current_project_version)
