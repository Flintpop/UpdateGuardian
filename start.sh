#!/bin/bash

LOCKFILE=/tmp/updateguardian.lock

(
    flock -n 9 || exit 1
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PYTHON_SCRIPT="$DIR/src/server/application/program.py"

    if [ -f "$PYTHON_SCRIPT" ]; then
        python3.11 "$PYTHON_SCRIPT"
    else
        echo "Erreur : le chemin ou le fichier '$PYTHON_SCRIPT' est introuvable. Veuillez vérifier que le script
        est bien présent dans le répertoire du projet, sinon faîtes git pull pour le récupérer."
        exit 1
    fi
) 9>$LOCKFILE
