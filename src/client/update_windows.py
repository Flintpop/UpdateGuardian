import ctypes
import sys

import win32com.client


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        return False


def update_windows():
    wua = win32com.client.Dispatch("Microsoft.Update.Session")
    searcher = wua.CreateUpdateSearcher()
    print("Recherche de mises à jour...")
    search_result = searcher.Search("IsInstalled=0 and Type='Software'")
    updates_to_install = win32com.client.Dispatch("Microsoft.Update.UpdateColl")

    if search_result.Updates.Count == 0:
        print("Aucune mise à jour à installer.")
        return
    else:
        print(f"{search_result.Updates.Count} mise(s) à jour trouvée(s).")

    for update in search_result.Updates:
        print(f"La mise à jour {update.Title} est disponible.")

    for unitary_windows_update in search_result.Updates:
        if unitary_windows_update.InstallationBehavior.CanRequestUserInput:
            print(f"La mise à jour {unitary_windows_update.Title} requiert une interaction utilisateur. Ignorée.")
        else:
            print(f"Installation de la mise à jour {unitary_windows_update.Title}...")
            updates_to_install.Add(unitary_windows_update)

    if updates_to_install.Count == 0:
        print("Aucune mise à jour automatique à installer.")
        return

    installer = wua.CreateUpdateInstaller()
    installer.Updates = updates_to_install
    installation_result = installer.Install()

    if installation_result.ResultCode == 2:
        print("Mises à jour installées avec succès.")
    else:
        print(f"Échec de l'installation des mises à jour. Code d'erreur: {installation_result.ResultCode}")


def start_client_update():
    if is_admin():
        update_windows()
    else:
        print("Exécutez ce script en tant qu'administrateur pour mettre à jour Windows.")
        sys.exit(1)
