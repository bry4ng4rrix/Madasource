"""Rôles PostgreSQL (security-design.md §19 ; indexes-and-constraints.md §6.1).

Deux rôles, retenus le 2026-10-14 :
- le **propriétaire du schéma**, utilisé seulement par Alembic (`MIGRATION_DATABASE_URL`) :
  il crée et modifie les tables. En local, c'est l'utilisateur créé par l'image PostgreSQL
  (`POSTGRES_USER`) ; en production, un rôle propriétaire non superutilisateur (Audit D) ;
- le **rôle applicatif** `madasource_app`, utilisé par l'API (`DATABASE_URL`) : aucun droit
  de modifier le schéma ; chaque migration qui crée une table lui accorde explicitement
  ses droits (`GRANT`), table par table et colonne par colonne (§6.2).

Le rôle applicatif est créé hors des migrations, car il porte un mot de passe :
`infrastructure/postgres/10-create-app-role.sh` en local, l'exploitation en production.
"""

APP_ROLE = "madasource_app"
