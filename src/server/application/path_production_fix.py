import sys
import os

def add_project_to_path():
    # Obtenez le chemin absolu vers le script en cours d'exécution
    chemin_script = os.path.abspath(__file__)

    # Pour reculer de 3 répertoires
    chemin_projet_3 = os.path.dirname(os.path.dirname(os.path.dirname(chemin_script)))
    chemin_projet_4 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(chemin_script))))

    if chemin_projet_4 not in sys.path:
        sys.path.append(chemin_projet_4)

    if chemin_projet_3 not in sys.path:
        sys.path.append(chemin_projet_3)

