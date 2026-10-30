#!/bin/sh
# Épreuve « Le serveur ne lit rien », étape 1 : ce que contient la base de Synapse.
# Attendu : uniquement des événements chiffrés et d'état ; marqueur introuvable.
set -eu
MARQUEUR=${MARQUEUR:-KIBARE-MARQUEUR}
cd "$(dirname "$0")/.."
psql() { docker compose exec -T -e PGPASSWORD="$(cat .secrets/pg_superuser)" postgres psql -h localhost -U postgres -d synapse -At "$@"; }

echo "== Types d'événements non-état stockés (attendu : m.room.encrypted, m.room.redaction)"
psql -c "SELECT type, count(*) FROM events WHERE state_key IS NULL GROUP BY type ORDER BY 2 DESC;"

echo "== Recherche du marqueur « $MARQUEUR » dans tous les événements"
# Requête par l'entrée standard : psql ne remplace :'m' (valeur échappée) que dans ce mode.
n=$(echo "SELECT count(*) FROM event_json WHERE json LIKE '%' || :'m' || '%';" | psql -v m="$MARQUEUR")
echo "occurrences : $n"

echo "== Recherche du marqueur dans les fichiers reçus (média)"
if docker compose exec -T synapse grep -rqa "$MARQUEUR" /data/media_store 2>/dev/null; then f=1; else f=0; fi
echo "fichiers contenant le marqueur : $f"

autres=$(psql -c "SELECT count(*) FROM events WHERE state_key IS NULL AND type NOT IN ('m.room.encrypted','m.room.redaction');")
if [ "$n" = "0" ] && [ "$f" = "0" ] && [ "$autres" = "0" ]; then echo "RÉSULTAT : OK, le serveur ne stocke aucun clair."; else echo "RÉSULTAT : ÉCHEC"; exit 1; fi
