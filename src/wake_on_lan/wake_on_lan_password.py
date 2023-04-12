import random


def generate_secureon_password() -> str:
    secureon_password = ""

    for _ in range(6):
        secureon_password += f"{random.randint(0, 255):02X}:"

    # Supprimer le dernier deux-points
    secureon_password = secureon_password[:-1]

    return secureon_password


# Exemple d'utilisation
if __name__ == "__main__":
    print("Mot de passe SecureOn généré : ", generate_secureon_password())
