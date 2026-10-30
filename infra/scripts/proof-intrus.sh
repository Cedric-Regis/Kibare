#!/bin/sh
# Épreuve « Intrus » : toutes les portes d'entrée hors SSO enrôlé sont fermées.
set -u
DOMAINE=${KIBARE_DOMAINE:-kibare.internal}
URL="https://$DOMAINE"
c() { curl -sk --resolve "$DOMAINE:443:127.0.0.1" "$@"; }
echec=0
attendu() { if [ "$2" = "$3" ]; then echo "OK    $1 (HTTP $2)"; else echo "ÉCHEC $1 (HTTP $2, attendu $3)"; echec=1; fi; }

attendu "Création de compte par l'API" \
  "$(c -o /dev/null -w '%{http_code}' -X POST -d '{"username":"intrus","password":"x","auth":{"type":"m.login.dummy"}}' "$URL/_matrix/client/v3/register")" 403

flux=$(c "$URL/_matrix/client/v3/login")
echo "      méthodes de connexion proposées : $flux"
echo "$flux" | grep -q 'm.login.password' && { echo "ÉCHEC mot de passe proposé"; echec=1; }
attendu "Connexion par mot de passe Matrix" \
  "$(c -o /dev/null -w '%{http_code}' -X POST -d '{"type":"m.login.password","identifier":{"type":"m.id.user","user":"agent"},"password":"x"}' "$URL/_matrix/client/v3/login")" 400

attendu "API admin Synapse depuis l'extérieur" "$(c -o /dev/null -w '%{http_code}' "$URL/_synapse/admin/v1/server_version")" 404
attendu "Console Keycloak depuis l'extérieur" "$(c -o /dev/null -w '%{http_code}' --resolve "auth.$DOMAINE:443:127.0.0.1" "https://auth.$DOMAINE/admin/")" 404

if [ -n "${TOKEN:-}" ] && [ -n "${SALON:-}" ]; then
  attendu "Agent enrôlé rejoignant un salon sans invitation" \
    "$(c -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer $TOKEN" -d '{}' "$URL/_matrix/client/v3/join/$SALON")" 403
else
  echo "(passer TOKEN et SALON pour tester l'entrée sans invitation)"
fi
echo "Compte Keycloak non enrôlé : se connecter dans le navigateur avec « intrus.demo » → Synapse refuse."
exit $echec
