import os.path
import re
import sys

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


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # noinspection PyProtectedMember
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def change_directory_to_root_folder() -> None:
    current_directory: str = os.getcwd()
    if current_directory.endswith(Infos.PROJECT_NAME):
        return

    if os.name == 'nt':
        cond = "\\" + Infos.PROJECT_NAME + "\\" not in os.getcwd()
    else:
        cond = "/" + Infos.PROJECT_NAME + "/" not in os.getcwd()

    if cond:
        print("Name of the project not found in the current nested directory. Please change directory to the "
              "root folder containing the name of the project.")
        raise EnvironmentError("Name of the project not found in the current nested directory.")

    root_folder = get_resource_path('')
    root_folder_str = root_folder.decode('utf-8') if isinstance(root_folder, bytes) else root_folder
    project_directory = os.path.join(root_folder_str.split(Infos.PROJECT_NAME)[0], Infos.PROJECT_NAME)

    # Change the working directory to the project_directory
    os.chdir(project_directory)


def find_file(filename: str, root_folder=None, already_called=False, show_print=True) -> str | None:
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
    if root_folder is None:
        root_folder = get_resource_path('')

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


def find_directory(directory_name: str, root_folder=None, already_called=False) -> str | None:
    change_directory_to_root_folder()
    if root_folder is None:
        root_folder = get_resource_path('')

    if os.getcwd().endswith(Infos.PROJECT_NAME) and directory_name == Infos.PROJECT_NAME:
        root_folder = os.getcwd()
        return root_folder

    excluded_dirs = ["__pycache__", ".git", ".idea", ".vscode", "venv", ".gitignore", "__init__.py", ".github",
                     "build", "dist"]

    skip = False
    for root, dirs, files in os.walk(root_folder):
        for directory in dirs:
            if directory in excluded_dirs:
                continue
            for excluded_dir in excluded_dirs:
                if os.path.sep + excluded_dir + os.path.sep in os.path.join(root, directory):
                    skip = True
                    break
            if skip:
                skip = False
                continue
            if directory == directory_name:
                return os.path.join(root, directory)

    if already_called:
        return None

    change_directory_to_root_folder()
    return find_directory(directory_name, root_folder, True)


def list_files_recursive(directory: str) -> list[str]:
    all_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            add_file(all_files, file, root)

    return all_files


def add_file(all_files: list[str], file: str, root: str) -> None:
    dir_exceptions = ["__pycache__", ".git", ".idea", ".vscode", "venv", ".gitignore", "__init__.py"]
    if file not in all_files:
        file_path = os.path.join(root, file)
        add_var = True

        for exception in dir_exceptions:
            if file_path.__contains__(exception):
                add_var = False
                break

        if add_var:
            all_files.append(file_path)


def get_root_project_dir():
    change_directory_to_root_folder()
    return os.getcwd()
