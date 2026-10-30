# CONTRATS.md — interfaces entre les blocs

> Toute modification de ce fichier se décide à trois (Cédric, Aman, Prisca).
> Les points marqués **[à valider]** sont des propositions de Cédric pour le point de 8 h.

## 1. Noms d'hôtes (tous servis par Caddy sur le port 443, TLS par autorité interne)

| Hôte | Service | Notes |
|---|---|---|
| `kibare.internal` | Element Web (client) + API Matrix (`/_matrix`, `/_synapse/client`) | `/_synapse/admin`, `/_matrix/federation`, `/_matrix/key` bloqués |
| `auth.kibare.internal` | Keycloak (connexion, TOTP) | `/admin` bloqué : la console Keycloak n'est pas exposée |
| `console.kibare.internal` | API FastAPI + pages de la console | `/interne` bloqué de l'extérieur |

Sur chaque poste de démo, `/etc/hosts` contient :
`127.0.0.1 kibare.internal auth.kibare.internal console.kibare.internal`

## 2. Adresses internes (réseau Docker `interne`, sans route sortante)

| Service | URL interne |
|---|---|
| Synapse | `http://synapse:8008` |
| Keycloak | `http://keycloak:8080` |
| API console | `http://console:8000` |
| PostgreSQL | `postgres:5432` |

## 3. PostgreSQL : 3 bases, 3 utilisateurs (chacun ne se connecte qu'à sa base)

| Base | Utilisateur | Utilisée par |
|---|---|---|
| `synapse` | `synapse` | Synapse uniquement |
| `keycloak` | `keycloak` | Keycloak uniquement |
| `kibare` | `kibare` | API console uniquement (via `KIBARE_DB_URL`) |

Le schéma de la base `kibare` est dans `console/db/schema.sql` (Prisca). L'API applique elle-même
le retrait des droits UPDATE et DELETE sur le journal.

## 4. Secrets

Générés au premier lancement par le conteneur `init`, jamais dans le dépôt. L'API console reçoit
un fichier d'environnement `/run/kibare/console/console.env` :

| Variable | Contenu |
|---|---|
| `KIBARE_DB_URL` | `postgresql://kibare:<mdp>@postgres:5432/kibare` |
| `KEYCLOAK_URL` | `http://keycloak:8080` |
| `KEYCLOAK_REALM` | `kibare` |
| `KEYCLOAK_CONSOLE_CLIENT_ID` | `kibare-console` |
| `KEYCLOAK_CONSOLE_CLIENT_SECRET` | secret aléatoire |
| `SYNAPSE_URL` | `http://synapse:8008` |
| `SYNAPSE_ADMIN_TOKEN` | jeton du compte de service `@kibare-console:kibare.internal` (admin Synapse) |
| `KIBARE_PROFIL` | `production` ou `demo` |

## 5. Royaume Keycloak (contenu : Prisca ; intégration : Cédric)

Fichier livré par Prisca : `console/keycloak/kibare-realm.json`, importé au démarrage
(`--import-realm`). **Sans aucun secret en clair** : utiliser les variables ci-dessous,
remplacées par Keycloak à l'import.

- Royaume : `kibare`. Rôles de royaume : `agent`, `superviseur`, `admin`.
- Attributs utilisateur : `ministere`, `fonction`, `matricule`.
- TOTP obligatoire (action requise `CONFIGURE_TOTP` à la création).
- Client `synapse` (confidentiel, OIDC) :
  - `secret` : `"${KIBARE_SYNAPSE_OIDC_SECRET}"`
  - URI de redirection : `https://kibare.internal/_synapse/client/oidc/callback`
  - URL de déconnexion back-channel : `http://synapse:8008/_synapse/client/oidc/backchannel_logout`
    (« Backchannel logout session required » : activé)
  - Mappers (dans l'ID token **et** userinfo) : `kibare_enrolled` = `"true"` (chaîne) pour un agent
    enrôlé, `preferred_username`, `name`, `ministere`, `fonction`, `matricule`.
- Client `kibare-console` (confidentiel, compte de service, rôles `realm-management` :
  `manage-users`, `view-users`) : `secret` : `"${KIBARE_CONSOLE_KC_SECRET}"`.
- Utilisateurs : **aucun** dans le royaume de production. Les comptes de démo sont dans
  `console/keycloak/demo-users.json` **[à valider]**, importés uniquement avec le profil démo.

Synapse n'accepte la connexion que si la revendication `kibare_enrolled` vaut `"true"`.
Le nom d'affichage Matrix est `{{ name }} · {{ fonction }} · {{ ministere }}`, remis à jour
à chaque connexion.

## 6. Identifiants Matrix

`@<preferred_username>:kibare.internal` ; `preferred_username` = matricule en minuscules
**[à valider]**.

## 7. Classification des salons

Événement d'état `bf.gov.classification`, `state_key` vide, contenu `{"niveau": "nc" | "dr" | "confidentiel"}`.
Posé par le client dans `initial_state` à la création du salon.

Règles appliquées **par le serveur** (module zéro clair, R6) :
- le niveau ne peut jamais être abaissé (`nc` < `dr` < `confidentiel`) ;
- poser ou modifier `confidentiel`, ou modifier un niveau existant : superviseur seulement.

Pour savoir si un expéditeur est superviseur, le module appelle l'API console **[à valider]** :

```
GET http://console:8000/interne/role?mxid=@x:kibare.internal
200 {"role": "agent" | "superviseur" | "admin", "statut": "actif" | "revocation_en_cours" | "revoque"}
404 si inconnu
```

Sans réponse de l'API, le module refuse (fermé par défaut).

## 8. Contrat d'API console (Prisca) — résumé

`GET /health`, `GET /me`, `GET /agents`, `GET /classifications`, `GET /salons/{room_id}`,
`POST /agents`, `POST /agents/{id}/revocation`, `GET /journal/verification`.
Authentification : jeton Matrix (`Authorization: Bearer`) vérifié auprès de Synapse sans cache.
Détail des schémas JSON : `console/CONTRAT_API.md` (source de vérité, Prisca).

## 9. Médias

Seuls les envois `Content-Type: application/octet-stream` sont acceptés (Caddy, règle R4) :
Element chiffre les fichiers dans le navigateur avant l'envoi. Pas d'avatar image.

## 10. Client

Caddy sert le build d'Element depuis `client/webapp/` (sortie de `yarn build`, Aman).
`config.json` : `default_server_config.m.homeserver.base_url = https://kibare.internal`.
