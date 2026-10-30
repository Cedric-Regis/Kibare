#!/bin/sh
# Épreuve « Le serveur ne lit rien », étape 2 : capture du trafic entre Caddy et Synapse
# (HTTP en clair sur le réseau interne : on y voit exactement ce que reçoit le serveur).
# Puis vérification qu'aucun conteneur interne ne peut sortir.
set -eu
MARQUEUR=${MARQUEUR:-KIBARE-MARQUEUR}
DUREE=${DUREE:-20}
cd "$(dirname "$0")/.."
echo "== Capture ${DUREE}s sur synapse:8008 : envoyez maintenant un message contenant « $MARQUEUR »"
docker run --rm --net container:kibare-synapse-1 nicolaka/netshoot:v0.13 \
  timeout "$DUREE" tcpdump -l -A -s0 -i any tcp port 8008 2>/dev/null > /tmp/kibare-capture.txt || true
echo "-- extrait (texte chiffré Megolm) :"
grep -o '"ciphertext":"[A-Za-z0-9+/=]\{0,60\}' /tmp/kibare-capture.txt | head -3 || true
if grep -q "$MARQUEUR" /tmp/kibare-capture.txt; then echo "RÉSULTAT : ÉCHEC, marqueur vu en clair"; exit 1; fi
echo "RÉSULTAT : OK, marqueur absent du trafic."

echo "== Aucune requête sortante (attendu : échec de connexion)"
if docker compose exec -T synapse python -c "import socket; socket.create_connection(('1.1.1.1', 443), timeout=3)" 2>/dev/null; then
  echo "RÉSULTAT : ÉCHEC, Synapse peut joindre Internet"; exit 1
fi
echo "RÉSULTAT : OK, Synapse n'a aucune route sortante."
