#!/bin/sh
# Épreuve « Le serveur ne lit rien », étape 3 : un envoi en clair par l'API est refusé.
# Usage : TOKEN=<jeton d'un agent> SALON='!abc:kibare.internal' make proof-clear
set -eu
: "${TOKEN:?jeton d'accès d'un agent (Element : Paramètres > Aide > Avancé)}"
: "${SALON:?identifiant du salon}"
DOMAINE=${KIBARE_DOMAINE:-kibare.internal}
code=$(curl -sk -o /tmp/kibare-clear.json -w '%{http_code}' --resolve "$DOMAINE:443:127.0.0.1" \
  -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"msgtype":"m.text","body":"KIBARE-MARQUEUR en clair"}' \
  "https://$DOMAINE/_matrix/client/v3/rooms/$SALON/send/m.room.message/preuve-$(date +%s)")
echo "HTTP $code : $(cat /tmp/kibare-clear.json)"
[ "$code" = "403" ] && echo "RÉSULTAT : OK, message en clair refusé." || { echo "RÉSULTAT : ÉCHEC"; exit 1; }
