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
    if not is_path_valid(path):
        raise ValueError("Path is not valid")
    path = os.path.join(path, "..", "")
    return os.path.abspath(path)


def go_back_n_dir(path: str, n: int) -> str:
    for _ in range(n):
        path = go_back_one_dir(path)
    return path
