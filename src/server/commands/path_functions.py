import os.path
import re

from src.server.config import Infos


# from src.server.data.local_network_data import Data


def is_path_valid(path: str) -> bool:
    # Détecte l'OS actuel
    current_os = os.name
    # current_os = os.name

    # Expression régulière pour les chemins de fichiers et dossiers Windows
    windows_regex = re.compile(
        r'^\w:[\\/](?:[\w\-._]+\\)*[\w\-._]*$'
    )

    # Expression régulière pour les chemins de fichiers et dossiers Linux
    linux_regex = re.compile(
        r'^/(?:[\w\-._]+/)*[\w\-._]*$'
    )

    # Vérifie si le chemin est valide pour l'OS actuel
    if current_os == 'nt':  # Windows
        return bool(windows_regex.match(path))
    elif current_os == 'posix':  # Linux
        return bool(linux_regex.match(path))
    else:
        return False


def go_back_one_dir(path: str) -> str:
    # if not is_path_valid(path):
    #     raise ValueError(f"Path {path} is not valid")
    path = os.path.join(path, "..", "")
    return os.path.abspath(path)


def go_back_n_dir(path: str, n: int) -> str:
    for _ in range(n):
        path = go_back_one_dir(path)
    return path


def change_directory_to_root_folder() -> None:
    current_directory: str = os.getcwd()
    if current_directory.endswith(Infos.project_name):
        return
    if os.name == 'nt':
        cond = "\\" + Infos.project_name + "\\" not in os.getcwd()
    else:
        cond = "/" + Infos.project_name + "/" not in os.getcwd()
    if cond:
        print("Name of the project not found in the current nested directory. Please change directory to the "
              "root folder containing the name of the project.")
        raise EnvironmentError("Name of the project not found in the current nested directory.")

    print("Changing directory to the root folder...")
    project_directory = os.path.join(current_directory.split(Infos.project_name)[0], Infos.project_name)

    # Change the working directory to the project_directory
    os.chdir(project_directory)


def find_file(filename: str, root_folder='.', already_called=False, show_print=True) -> str | None:
    """
    Find a file in the project root folder and its subdirectories.\n
    **Note**: If the file is not found in the root folder, the function will change the working directory to the root
    folder and search again. The change to the root folder is permanent.\n
    :param filename: The name of the file to be found
    :param root_folder: The root folder to start the search from (default: current directory, but searches the root
    folder if not found)
    :param already_called: Internal use only
    :param show_print: To print if file not found
    :return: The relative path to the file if found, None otherwise
    """
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file == filename:
                return os.path.join(root, file)

    if already_called:
        if show_print:
            print(f"File '{filename}' not found in the root folder '{root_folder}' and its subdirectories.")
        return None

    change_directory_to_root_folder()
    return find_file(filename, root_folder, True, show_print=show_print)


def find_directory(directory_name: str, root_folder='.') -> str:
    for root, dirs, files in os.walk(root_folder):
        for directory in dirs:
            if directory == directory_name:
                return os.path.join(root, directory)
    raise FileNotFoundError(f"Directory '{directory_name}' not found in the root folder '{root_folder}'"
                            f" and its subdirectories.")


def list_files_recursive(directory: str) -> list[str]:
    # if not is_path_valid(directory):
    #     raise ValueError(f"Path {directory} is not valid")

    all_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    return all_files


def get_root_project_dir():
    change_directory_to_root_folder()
    return os.getcwd()
