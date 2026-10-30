# CLAUDE.md — Kibaré

À donner à l'IA au début de chaque session, avec CONTRATS.md.

## Le projet

Kibaré est une messagerie chiffrée de bout en bout pour les agents de l'État
(hackathon). Pile : Caddy, PostgreSQL, Synapse (Matrix), Keycloak (SSO + TOTP),
Element Web adapté (client), API FastAPI (console d'administration).
Domaine figé : `kibare.internal`. Données fictives uniquement.

## Qui possède quoi (ne jamais modifier le dossier d'un autre sans accord)

| Dossier | Propriétaire | Relecteur |
|---|---|---|
| `infra/`, `tests/securite/`, `docs/` (note de sécurité, README, licences) | Cédric | Prisca |
| `client/`, `tests/e2e/` | Aman | Cédric (sécurité du client) |
| `console/`, `tests/api/`, `docs/` (pré-projet, fiche équipe) | Prisca | Cédric (révocation, authentification) |

`CONTRATS.md` et le contrat d'API ne changent que par décision à trois.

## Règles éliminatoires — l'IA ne doit JAMAIS

- écrire de la cryptographie (le chiffrement est celui d'Element / vodozemac) ;
- désactiver ou contourner le chiffrement, même « juste pour tester » ;
- laisser passer un seul message en clair côté serveur ;
- utiliser des données, comptes ou systèmes réels ; tester autre chose que notre pile locale ;
- écrire du code que le membre qui le fusionne ne sait pas expliquer.

Seul usage autorisé de `hashlib` : le chaînage du journal (intégrité, pas cryptographie).

## Conventions

- Commits en français : `type(portée) : message` (ex. `feat(infra) : module zéro clair R1-R3`).
  Types : feat, fix, test, docs, chore, refactor. Au moins un commit toutes les 2 h.
- Branches courtes `infra`, `client`, `console`, fusion dans `main` toutes les 2 h.
- Jamais d'historique réécrit, jamais de secret dans le dépôt (`.env`, `infra/.secrets/` ignorés ; gitleaks en pre-commit).
- Avant chaque fusion : faire expliquer le code en 5 lignes, puis le relire.
- Toute fusion touchant au chiffrement, à l'authentification ou au module zéro clair : veto de Cédric.

## Commandes

- `make up` / `make down` / `make logs` — pile locale
- `make test` — tous les tests (sécurité, API, e2e)
- `make proof-db`, `make proof-net`, `make proof-clear`, `make proof-intrus`, `make demo-reset`
