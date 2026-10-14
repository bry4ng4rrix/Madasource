#!/bin/sh
# Crée ou met à jour le rôle applicatif madasource_app (backend/app/db/roles.py).
#
# - Exécuté automatiquement par l'image PostgreSQL à la création d'une base vide
#   (/docker-entrypoint-initdb.d), donc pour db-test à chaque démarrage.
# - Idempotent : pour une base déjà initialisée (volume existant), le relancer à la main :
#   docker compose exec db sh /docker-entrypoint-initdb.d/10-create-app-role.sh
# - Ne supprime rien, ne modifie aucune donnée.
#
# Le rôle peut se connecter ; il n'a aucun attribut d'administration. Son usage du schéma
# public et ses droits sur chaque table sont accordés par les migrations.
#
# Le mot de passe est lu dans l'environnement par psql (\getenv) : il n'apparaît ni dans
# les arguments du processus, ni dans les journaux du serveur en cas d'échec.
set -eu

: "${POSTGRES_USER:?}"
: "${POSTGRES_DB:?}"
: "${MADASOURCE_APP_PASSWORD:?MADASOURCE_APP_PASSWORD manquant}"

psql -v ON_ERROR_STOP=1 --no-psqlrc --quiet \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_role=madasource_app <<'SQL'
\getenv app_password MADASOURCE_APP_PASSWORD

-- Les instructions de cette session ne sont pas journalisées par le serveur, ni en cas
-- d'échec, ni avec log_statement actif (le mot de passe y figurerait en clair).
SET log_min_error_statement = panic;
SET log_statement = 'none';

SELECT format('CREATE ROLE %I', :'app_role')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_role') \gexec

-- Attributs réappliqués à chaque exécution, y compris sur un rôle déjà existant.
SELECT format(
  'ALTER ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS '
  'NOINHERIT PASSWORD %L',
  :'app_role', :'app_password'
) \gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'app_role') \gexec

-- Aucun rôle ne crée d'objet dans public, sauf le propriétaire (déjà le défaut en PG 15+).
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
