import os.path
import re


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


def find_file(filename: str, root_folder='.') -> str:
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file == filename:
                return os.path.join(root, file)
    raise FileNotFoundError(f"File '{filename}' not found in the root folder '{root_folder}' and its subdirectories.")


def find_directory(directory_name: str, root_folder='.') -> str:
    for root, dirs, files in os.walk(root_folder):
        for directory in dirs:
            if directory == directory_name:
                return os.path.join(root, directory)
    raise FileNotFoundError(f"Directory '{directory_name}' not found in the root folder '{root_folder}'"
                            f" and its subdirectories.")


def list_files_recursive(directory: str) -> list[str]:
    if not is_path_valid(directory):
        raise ValueError(f"Path {directory} is not valid")

    all_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    return all_files
