#!/bin/sh
# Crée le compte de service @kibare-console (admin Synapse) utilisé par l'API console.
# Idempotent : peut être relancé à chaque démarrage.
set -eu

AS_TOKEN=$(cat /run/kibare/bootstrap/as_token)
export PGPASSWORD=$(cat /run/kibare/bootstrap/pg_superuser)

# 1) Enregistrement par le jeton d'appservice (fonctionne même inscription fermée).
#    M_USER_IN_USE au second passage : normal.
wget -q -O - \
  --header "Authorization: Bearer $AS_TOKEN" \
  --header "Content-Type: application/json" \
  --post-data '{"type":"m.login.application_service","username":"kibare-console"}' \
  http://synapse:8008/_matrix/client/v3/register >/dev/null 2>&1 || true

# 2) Droits d'administration Synapse pour ce seul compte.
psql -h postgres -U postgres -d synapse -v ON_ERROR_STOP=1 -c \
  "UPDATE users SET admin = 1 WHERE name LIKE '@kibare-console:%';" | grep -q "UPDATE 1"

echo "bootstrap : compte de service @kibare-console prêt."
