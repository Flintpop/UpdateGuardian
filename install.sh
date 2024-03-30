#!/bin/bash

# S'assurer que le script est exécuté avec des privilèges root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté avec des privilèges d'administrateur."
    exit 1
fi

# Mise à jour des paquets et installation de Python 3.12 et Git
echo "Mise à jour des paquets et installation de Python 3.12 et Git..."
apt update && apt install -y python3.12 git

# Vérifier si Python 3.12 est correctement installé
if ! command -v python3.12 &> /dev/null; then
    echo "L'installation de Python 3.12 a échoué."
    exit 1
fi

# Vérifier si Git est correctement installé
if ! command -v git &> /dev/null; then
    echo "L'installation de Git a échoué."
    exit 1
fi

# Cloner le repository GitHub
echo "Clonage du repository GitHub..."
git clone https://github.com/flintpop/updateguardian.git /opt/updateguardian

# Vérifier si le clonage a réussi
if [ ! -d "/opt/updateguardian" ]; then
    echo "Le clonage du repository a échoué."
    exit 1
fi

# Installer pip pour Python 3.12
echo "Installation de pip pour Python 3.12..."
apt install -y python3-pip

# Installer les dépendances Python spécifiées dans requirements.txt
echo "Installation des dépendances Python..."
python3.12 -m pip install -r /opt/updateguardian/requirements.txt

# Démarrer le logiciel (à ajuster selon la manière dont le logiciel est démarré)
echo "Démarrage d'UpdateGuardian..."
chmod +x /opt/updateguardian/start.sh
python3.12 /opt/updateguardian/start.sh

echo "Installation terminée."