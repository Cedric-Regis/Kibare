"""Conteneur init de Kibaré : secrets et configurations.

1. Génère chaque secret UNE SEULE FOIS dans /secrets (dossier infra/.secrets/, ignoré par git).
   Les secrets viennent du module standard `secrets` (générateur aléatoire du système) :
   aucune cryptographie n'est écrite ici.
2. Rend les configurations de chaque service dans /run/kibare/<service>/, lisibles
   uniquement par l'utilisateur de ce service.

Relancer init ne change aucun secret existant : c'est idempotent.
"""

import os
import secrets
from pathlib import Path
from string import Template

SECRETS = Path("/secrets")
RUN = Path("/run/kibare")
TEMPLATES = Path("/init/templates")

DOMAINE = os.environ.get("KIBARE_DOMAINE", "kibare.internal")
PROFIL = os.environ.get("KIBARE_PROFIL", "production")

# Utilisateurs système des images (aucun conteneur applicatif ne tourne en root).
UID_POSTGRES = 70
UID_SYNAPSE = 991
UID_KEYCLOAK = 1000

NOMS_SECRETS = [
    "pg_superuser",
    "pg_synapse",
    "pg_keycloak",
    "pg_kibare",
    "keycloak_admin",
    "synapse_oidc",        # secret du client OIDC « synapse » dans Keycloak
    "console_kc",          # secret du client « kibare-console » dans Keycloak
    "synapse_macaroon",
    "synapse_form",
    "as_token",            # jeton du compte de service admin Synapse (API console)
    "hs_token",
]


def secret(nom: str) -> str:
    """Lit le secret s'il existe, sinon le crée (32 octets aléatoires, encodés URL)."""
    chemin = SECRETS / nom
    if not chemin.exists():
        chemin.write_text(secrets.token_urlsafe(32))
        chemin.chmod(0o600)
    return chemin.read_text().strip()


def ecrire(chemin: Path, contenu: str, uid: int) -> None:
    """Écrit un fichier lisible par un seul utilisateur (mode 0400)."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    os.chown(chemin.parent, uid, uid)
    chemin.parent.chmod(0o700)
    if chemin.exists():
        chemin.chmod(0o600)
    chemin.write_text(contenu)
    os.chown(chemin, uid, uid)
    chemin.chmod(0o400)


def rendre(nom_modele: str, valeurs: dict) -> str:
    # substitute (et non safe_substitute) : une variable oubliée fait échouer init.
    return Template((TEMPLATES / nom_modele).read_text()).substitute(valeurs)


def main() -> None:
    SECRETS.mkdir(exist_ok=True)
    s = {nom: secret(nom) for nom in NOMS_SECRETS}

    # PostgreSQL : un fichier par mot de passe, lus par 01-bases.sh au premier démarrage.
    for nom in ("superuser", "synapse", "keycloak", "kibare"):
        ecrire(RUN / "postgres" / nom, s[f"pg_{nom}"], UID_POSTGRES)

    # Synapse
    valeurs_synapse = {
        "domaine": DOMAINE,
        "pg_synapse": s["pg_synapse"],
        "synapse_oidc": s["synapse_oidc"],
        "synapse_macaroon": s["synapse_macaroon"],
        "synapse_form": s["synapse_form"],
        "as_token": s["as_token"],
        "hs_token": s["hs_token"],
    }
    ecrire(RUN / "synapse" / "homeserver.yaml", rendre("homeserver.yaml.tmpl", valeurs_synapse), UID_SYNAPSE)
    ecrire(RUN / "synapse" / "console-appservice.yaml", rendre("console-appservice.yaml.tmpl", valeurs_synapse), UID_SYNAPSE)
    os.chown("/vol/synapse", UID_SYNAPSE, UID_SYNAPSE)

    # Keycloak : variables lues par l'entrypoint ; les ${...} du royaume sont remplacés à l'import.
    ecrire(
        RUN / "keycloak" / "keycloak.env",
        "\n".join([
            f"KC_DB_PASSWORD={s['pg_keycloak']}",
            "KC_BOOTSTRAP_ADMIN_USERNAME=kibare-bootstrap",
            f"KC_BOOTSTRAP_ADMIN_PASSWORD={s['keycloak_admin']}",
            f"KIBARE_SYNAPSE_OIDC_SECRET={s['synapse_oidc']}",
            f"KIBARE_CONSOLE_KC_SECRET={s['console_kc']}",
            f"KIBARE_DOMAINE={DOMAINE}",
        ]) + "\n",
        UID_KEYCLOAK,
    )

    # Bootstrap (root dans son conteneur à usage unique).
    ecrire(RUN / "bootstrap" / "as_token", s["as_token"], 0)
    ecrire(RUN / "bootstrap" / "pg_superuser", s["pg_superuser"], 0)

    # API console (Prisca) : fichier d'environnement, cf. CONTRATS.md §4.
    console_env = SECRETS / "console.env"
    console_env.write_text("\n".join([
        f"KIBARE_DB_URL=postgresql://kibare:{s['pg_kibare']}@postgres:5432/kibare",
        "KEYCLOAK_URL=http://keycloak:8080",
        "KEYCLOAK_REALM=kibare",
        "KEYCLOAK_CONSOLE_CLIENT_ID=kibare-console",
        f"KEYCLOAK_CONSOLE_CLIENT_SECRET={s['console_kc']}",
        "SYNAPSE_URL=http://synapse:8008",
        f"SYNAPSE_ADMIN_TOKEN={s['as_token']}",
        f"KIBARE_DOMAINE={DOMAINE}",
        f"KIBARE_PROFIL={PROFIL}",
    ]) + "\n")
    console_env.chmod(0o600)

    print(f"init : secrets prêts, configurations rendues (profil {PROFIL}, domaine {DOMAINE}).")


if __name__ == "__main__":
    main()
