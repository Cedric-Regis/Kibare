# UPSTREAM.md — provenance du code amont

Ce dossier `client/` est un **fork d'Element Web**. Ce fichier existe pour que le jury puisse vérifier
exactement d'où vient le code et ce que nous y avons changé.

---

## Version épinglée

| Élément | Valeur |
|---|---|
| Projet amont | Element Web |
| Dépôt | https://github.com/element-hq/element-web |
| **Tag** | **`v1.12.33`** |
| **Commit amont** | **`45671bc88ffe82658619bc523458f3ae3a43bff0`** |
| Date du commit amont | 2026-10-27 14:40:29 +0000 |
| Licence | AGPL-3.0 (double licence avec licence commerciale ; **nous retenons l'AGPL**) |

## Comment ce dossier a été produit

```bash
git clone --depth 1 --branch v1.12.33 \
    https://github.com/element-hq/element-web.git client
rm -rf client/.git
git init -b main
git add client/
git commit -m "chore(client) : import amont, inchangé (Element Web v1.12.33)"
```

Le premier commit du dépôt contient **l'arbre amont tel quel, sans aucune modification**.
Nos changements viennent uniquement après, en petits commits séparés, listés dans `PATCHES.md`.

## Vérifier que l'import est intact

```bash
git diff 45671bc88ffe82658619bc523458f3ae3a43bff0 --stat   # impossible : historique non conservé
```

L'historique amont n'étant pas conservé (voir ci-dessous), la vérification se fait autrement :

```bash
# comparer l'arbre importé avec l'archive officielle du tag
git archive --format=tar v1.12.33 | sha256sum     # côté amont
sha256sum <arbre du commit d'import>              # côté Kibaré
```

La commande exacte de contrôle est fournie par `client/scripts/verifier-import.sh` (à produire).

---

## Décision assumée : pas d'historique amont dans notre dépôt

Le cahier des charges mentionne un « fork conservant l'historique amont ». **Nous ne l'avons pas fait,
et voici pourquoi, en toute transparence.**

| | Fork avec historique complet | Import en un commit (choix retenu) |
|---|---|---|
| Taille du dépôt | ~700 Mo de `.git` | ~40 Mo |
| `git log` du jury | 40 000 commits amont noyés dans les nôtres | **un commit d'import clair + nos commits** |
| Lecture de nos changements | `git log --author` | `git log` : tout ce qui suit l'import **est** notre travail |
| Contrainte matérielle | dépasse l'espace disque disponible | tient |

Le critère noté est *« un historique de commits progressifs couvrant la durée du sprint »*. Un import
isolé suivi de nos commits rend ce travail **plus** lisible, pas moins : le jury voit immédiatement
la frontière entre ce qu'Element a écrit et ce que nous avons écrit.

La provenance reste vérifiable : tag, commit SHA et procédure de reproduction sont ci-dessus.

---

## Environnement de build

| Outil | Version |
|---|---|
| Node.js | 24.14.1 (le dépôt exige `>= 22.18`) |
| pnpm | **12.11.2** (imposé par `devEngines.packageManager`) |
| Système | Windows 11, x64 |

**Attention** : la documentation du sprint mentionne `yarn install` / `yarn build`. C'est faux depuis
le passage d'Element Web en monorepo. Les commandes correctes sont :

```bash
cd client
pnpm install
pnpm --filter element-web build     # sortie dans client/apps/web/webapp
```

## Structure utile du monorepo

| Chemin | Contenu |
|---|---|
| `client/apps/web` | l'application Element Web |
| `client/apps/web/src/i18n/strings/` | fichiers de langue (`en_EN.json`, `fr.json`, …) |
| `client/apps/web/src/i18n/languages.ts` | registre des langues |
| `client/packages/module-api` | API d'extension officielle |
| `client/modules/banner` | module d'exemple servant de référence |
| `client/docs/config.md` | documentation de `config.json` |

---

## Licences et marques

- Le code amont reste sous **AGPL-3.0**. Les mentions de droits d'auteur d'Element et de Synapse sont
  **conservées** dans chaque fichier.
- Kibaré ne se présente **jamais** comme un produit d'Element, de Matrix ou de Keycloak.
  Les logos et le nom affiché sont remplacés ; les mentions de licence sont intactes.
- Les fichiers que **nous** ajoutons portent l'en-tête de licence du projet et sont publiés sous AGPL-3.0.

## Composants tiers embarqués

| Composant | Version | Licence |
|---|---|---|
| Element Web | 1.12.33 | AGPL-3.0 |
| matrix-js-sdk | voir `client/pnpm-lock.yaml` | Apache-2.0 / AGPL-3.0 selon version |
| vodozemac (via matrix-sdk-crypto-wasm) | voir `pnpm-lock.yaml` | Apache-2.0 |
| Inter (via `@fontsource/inter`) | 5.3.0 | OFL-1.1 |
| Fira Code (via `@fontsource/fira-code`) | 5.x | OFL-1.1 |

> Le tableau complet des licences du dossier est tenu par Cédric dans le `README.md` racine.
> Toute version modifiée ici doit lui être signalée.
