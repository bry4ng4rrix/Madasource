---
paths:
  - "backend/alembic/**"
  - "backend/alembic.ini"
---

# Règles pour les migrations Alembic

- Suivre le skill `database-migrations`.
- Ne jamais éditer une révision déjà appliquée ou partagée : créer une nouvelle révision.
- Relire chaque fichier autogenerate ligne à ligne. Gérer explicitement les enums PostgreSQL, les CHECK, les `server_default`, et les renommages (qu'autogenerate interprète comme drop + add).
- Toute opération destructrice (`drop_table`, `drop_column`, changement de type avec perte, suppression de contrainte) exige l'accord explicite de l'utilisateur et une sauvegarde préalable.
- Le `downgrade` est implémenté, ou bien la révision lève explicitement une exception pour signaler qu'elle est irréversible.
- Pas de données métier réelles. Seules les données de référence validées sont admises.
- Ne jamais lancer `downgrade base`, réinitialiser une base ou supprimer un volume pour résoudre un problème de migration.
