#!/bin/sh
# Test d'intégration du module zéro clair sur la pile démarrée (make up).
# Utilise le compte de service @kibare-console : aucun compte humain nécessaire.
set -u
cd "$(dirname "$0")/../.."
DOMAINE=${KIBARE_DOMAINE:-kibare.internal}
TOKEN=$(cat infra/.secrets/as_token)
URL="https://$DOMAINE/_matrix/client/v3"
MARQUEUR="KIBARE-MARQUEUR-$(date +%s)"
echec=0

# requete METHODE CHEMIN [JSON] [CONTENT-TYPE] → affiche le code HTTP, corps dans /tmp/kibare-rep.json
requete() {
  curl -sk --resolve "$DOMAINE:443:127.0.0.1" -o /tmp/kibare-rep.json -w '%{http_code}' \
    -X "$1" -H "Authorization: Bearer $TOKEN" -H "Content-Type: ${4:-application/json}" \
    --data-binary "${3:-}" "$2"
}
attendu() { if [ "$2" = "$3" ]; then echo "OK    $1 (HTTP $2)"; else echo "ÉCHEC $1 (HTTP $2, attendu $3) $(cat /tmp/kibare-rep.json)"; echec=1; fi; }
classe() { printf '{"preset":"private_chat","initial_state":[{"type":"bf.gov.classification","state_key":"","content":{"niveau":"%s"}}]}' "$1"; }

attendu "Création d'un salon Non classifié" "$(requete POST "$URL/createRoom" "$(classe nc)")" 200
SALON=$(sed -n 's/.*"room_id":"\([^"]*\)".*/\1/p' /tmp/kibare-rep.json)
S=$(printf '%s' "$SALON" | sed 's/!/%21/; s/:/%3A/')

CLAIR=$(printf '{"msgtype":"m.text","body":"%s"}' "$MARQUEUR")
CHIFFRE_PLUS_BODY=$(printf '{"algorithm":"m.megolm.v1.aes-sha2","ciphertext":"QUJD","session_id":"s","body":"%s"}' "$MARQUEUR")
attendu "R1 message en clair refusé" "$(requete PUT "$URL/rooms/$S/send/m.room.message/t1" "$CLAIR")" 403
attendu "R3 champ body glissé dans un message chiffré refusé" \
  "$(requete PUT "$URL/rooms/$S/send/m.room.encrypted/t2" "$CHIFFRE_PLUS_BODY")" 403
attendu "R3 message chiffré bien formé accepté" \
  "$(requete PUT "$URL/rooms/$S/send/m.room.encrypted/t3" '{"algorithm":"m.megolm.v1.aes-sha2","ciphertext":"QUJDREVGRw","session_id":"s"}')" 200
attendu "R2 retrait du chiffrement refusé" \
  "$(requete PUT "$URL/rooms/$S/state/m.room.encryption/" '{"algorithm":"aucun"}')" 403
attendu "R6 reposer le même niveau accepté" \
  "$(requete PUT "$URL/rooms/$S/state/bf.gov.classification/" '{"niveau":"nc"}')" 200
attendu "R6 relèvement par un non-superviseur refusé" \
  "$(requete PUT "$URL/rooms/$S/state/bf.gov.classification/" '{"niveau":"dr"}')" 403
attendu "R6 salon Confidentiel par un non-superviseur refusé" "$(requete POST "$URL/createRoom" "$(classe confidentiel)")" 403
attendu "R5 salon public refusé" "$(requete POST "$URL/createRoom" '{"preset":"public_chat"}')" 403
attendu "R1 widget (intégration externe) refusé" \
  "$(requete PUT "$URL/rooms/$S/state/im.vector.modular.widgets/w" '{"url":"https://exemple.org"}')" 403

MEDIA="https://$DOMAINE/_matrix/media/v3/upload"
attendu "R4 fichier en clair refusé" "$(requete POST "$MEDIA" "$MARQUEUR" text/plain)" 415
attendu "R4 fichier opaque accepté" "$(requete POST "$MEDIA" "octets-chiffres" application/octet-stream)" 200
attendu "Fédération fermée" "$(requete GET "https://$DOMAINE/_matrix/federation/v1/version")" 404

n=$(cd infra && docker compose exec -T -e PGPASSWORD="$(cat .secrets/pg_superuser)" postgres \
  psql -h localhost -U postgres -d synapse -At -c "SELECT count(*) FROM event_json WHERE json LIKE '%$MARQUEUR%';")
attendu "Marqueur absent de la base (occurrences)" "$n" 0

exit $echec
