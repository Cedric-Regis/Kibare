# PATCHES.md — modifications apportées au cœur d'Element Web

Ce fichier liste **toutes** les modifications que nous avons apportées au code amont.
Le jury peut le lire en deux minutes et vérifier chaque ligne avec `git show <commit>`.

**Principe directeur : le module d'abord, le patch en dernier recours.**

Element Web expose une API d'extension officielle (`client/packages/module-api`) qui charge, au
runtime, un fichier JavaScript déclaré dans `config.json` :

```json
{ "modules": ["/modules/kibare.js"] }
```

Tout ce qui peut passer par cette API passe par cette API. Un patch du cœur n'est accepté que si
l'API ne fournit **aucun** point d'extension — et il est alors documenté ci-dessous.

---

## État au 30 octobre 2026, 13 h 00

**Aucun patch du cœur pour l'instant.**

| Fonctionnalité | Mécanisme | Patch du cœur ? |
|---|---|---|
| Bandeau de classification | module : `api.rootNode` | non |
| Filigrane nom + matricule | module : overlay `pointer-events: none` | non |
| Annuaire des agents | module : panneau rendu par le module | non |
| Mooré (`mos`) | `i18n/languages.json` + `i18n/mos.json` (runtime) | non |
| Repli français | `i18n/mos.json` généré depuis `fr.json` | non |
| Langue par défaut `fr` | `config.json` | non |
| Aperçus de liens coupés | `api.urlPreviews` | non |
| Téléchargement bloqué | `api.customComponents` | non |
| Boutons d'en-tête de salon | `api.extras` | non |

Deux points restent **candidats** à un patch, et ne seront faits que si le temps le permet,
séparément, et expliqués ici :

1. **Masquer « Transférer »** — l'énumération `UIComponent` n'expose pas de slot pour les actions de
   message. Contournement actuel, sans patch : le module masque le bouton par CSS et neutralise
   l'action. Limite assumée, écrite dans le dossier.
2. **Choisir le niveau à la création d'un salon** — `UIComponent.CreateRooms` permet de *bloquer*
   la création, pas de la *remplacer*. Contournement actuel, sans patch : le module ouvre son propre
   panneau de création et appelle `POST /salons`.

---

## Format d'une entrée

Quand un patch sera ajouté, il figurera ici sous cette forme :

```
### <titre court>
- **Fichier** : `chemin/exact/du/fichier`
- **Commit** : `<sha>`
- **Pourquoi** : ce que l'API de modules ne permet pas.
- **Différence** : N lignes ajoutées, M lignes retirées.
- **Vérification** : commande ou test qui prouve que le comportement voulu est obtenu.
```

Rien d'autre ne sera modifié dans le cœur : ni le chiffrement, ni l'authentification, ni le réseau.
