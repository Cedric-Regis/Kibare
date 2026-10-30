# Kibaré

Messagerie chiffrée de bout en bout pour les agents de l'État, auto-hébergée, sans aucune
dépendance externe. Le serveur ne lit rien : il ne stocke que des messages chiffrés.

> Brouillon : README final (2 pages) pour le tag v1.0.

## Installation (une commande)

Prérequis : Docker et Docker Compose, `make`.

```sh
make hosts   # une seule fois : ajoute kibare.internal dans /etc/hosts
make up      # génère les secrets, puis démarre toute la pile
```

Puis ouvrir https://kibare.internal (certificat de l'autorité interne de Caddy).

## Vérifier la sécurité

```sh
make test-securite   # tests unitaires du module zéro clair
make test-pile       # module zéro clair et Caddy sur la pile démarrée
make proof-db        # la base ne contient aucun clair
make proof-intrus    # inscription, mot de passe, API admin : refusés
```

## Architecture

| Service | Rôle |
|---|---|
| Caddy | Seul point d'entrée (port 443), TLS interne, routes sensibles bloquées |
| Synapse | Serveur Matrix, fédération fermée, module « zéro clair » |
| Keycloak | Connexion unique (SSO) avec TOTP obligatoire |
| PostgreSQL | 3 bases, 3 utilisateurs aux droits minimaux, réseau sans route sortante |
| Element Web | Client adapté (`client/`) |
| API console | Enrôlement, révocation, annuaire (`console/`) |

Le chiffrement (Olm/Megolm) est celui d'Element (vodozemac). L'équipe n'a écrit aucune
cryptographie.

## Licence

AGPL-3.0 (voir `LICENSE`).
