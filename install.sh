#!/bin/bash

# S'assurer que le script est exécuté avec des privilèges root
if [ "$(id -u)" -ne 0 ]; then
    echo "Ce script doit être exécuté avec des privilèges d'administrateur."
    exit 1
fi

# Vérifie que updateguardian n'est pas déjà installé
if [ -d "/opt/updateguardian" ]; then
    echo "UpdateGuardian est déjà installé."
    exit 1
fi

# Mise à jour des paquets et installation de Python 3.11 et Git
echo "Mise à jour des paquets et installation de Python 3.11 et Git..."
apt update && apt install -y python3.11 git

# Vérifier si Python 3.11 est correctement installé en utilisant une commande Python pour obtenir sa version
if ! python3.11 -c 'import sys; assert "3.11" in sys.version, "Version de Python incorrecte"' &> /dev/null; then
    echo "L'installation de Python 3.11 a échoué."
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
sudo_caller=${SUDO_USER:-$USER}
# Changer le propriétaire de /opt/updateguardian à l'utilisateur non-root
chown -R $sudo_caller:$sudo_caller /opt/updateguardian

old_pwd=$(pwd)
cd /opt/updateguardian
git config --global --add safe.directory /opt/updateguardian
git checkout main
git pull

cd $old_pwd

# Installer pip pour Python 3.11
echo "Installation de pip pour Python 3.11..."
apt install -y python3-pip &> /dev/null

# Installer les dépendances Python spécifiées dans requirements.txt
echo "Installation des dépendances Python..."
python3.11 -m pip install -r /opt/updateguardian/requirements.txt

chmod +x /opt/updateguardian/start.sh

# Ajouter un lien symbolique dans /usr/local/bin pour exécuter UpdateGuardian
echo "Configuration de la commande updateguardian..."
ln -s /opt/updateguardian/start.sh /usr/local/bin/updateguardian

echo "Installation terminée."
echo "Démarrer le logiciel avec la commande 'updateguardian'"
