#!/bin/sh
# Premier démarrage de PostgreSQL : 3 bases, 3 utilisateurs aux droits minimaux.
# Chaque utilisateur possède sa base et ne peut se connecter à aucune autre.
set -eu

for nom in synapse keycloak kibare; do
  mdp=$(cat "/run/kibare/postgres/$nom")
  psql -v ON_ERROR_STOP=1 -U postgres -v nom="$nom" -v mdp="$mdp" <<'SQL'
CREATE ROLE :"nom" LOGIN PASSWORD :'mdp' NOSUPERUSER NOCREATEDB NOCREATEROLE;
SQL
done

psql -v ON_ERROR_STOP=1 -U postgres <<'SQL'
-- Synapse exige une collation C.
CREATE DATABASE synapse OWNER synapse ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;
CREATE DATABASE keycloak OWNER keycloak ENCODING 'UTF8';
CREATE DATABASE kibare OWNER kibare ENCODING 'UTF8';
REVOKE ALL ON DATABASE synapse, keycloak, kibare, postgres FROM PUBLIC;
SQL
