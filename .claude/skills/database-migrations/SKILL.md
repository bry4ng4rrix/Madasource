---
name: database-migrations
description: "Prépare, relit et applique en local une migration Alembic pour le backend MadaSource à partir des modèles SQLAlchemy, en contrôlant cohérence, réversibilité et risque de perte de données. À utiliser après toute modification de models.py, ou en cas de problème d'historique Alembic (plusieurs têtes, écart modèles/migrations). Ne réinitialise jamais une base."
argument-hint: "<message de migration>"
---

# Skill database-migrations

Migration demandée : $ARGUMENTS

Les commandes s'exécutent depuis `backend/`, avec le préfixe défini dans `backend/README.md` (proposé : `uv run alembic …`, à confirmer au Jour 4).

## Quand l'utiliser

- Un modèle SQLAlchemy a été ajouté ou modifié.
- `alembic check` signale un écart, ou `alembic heads` montre plusieurs têtes.

## Procédure

1. **État** : `alembic current`, `alembic heads` (une seule tête attendue), `alembic history --verbose`. S'il y a plusieurs têtes, s'arrêter, expliquer et proposer `alembic merge`. Ne rien supprimer.
2. **Lire** les modèles modifiés et la dernière migration.
3. **Générer** : `alembic revision --autogenerate -m "<message court en anglais>"`.
4. **Relire le fichier généré, ligne à ligne** :
   - Seules les opérations attendues sont présentes.
   - Corriger à la main ce qu'autogenerate rate ou interprète mal : renommage vu comme drop + add, enums PostgreSQL (création et suppression explicites du type), contraintes CHECK, `server_default`.
   - Un `NOT NULL` ajouté sur une table existante a un `server_default` ou suit un backfill en trois étapes (ajout nullable, remplissage, contrainte).
   - Les noms de contraintes suivent la naming convention du projet.
   - Le `downgrade` est cohérent. Une migration irréversible le déclare explicitement (exception levée) et le rapport le signale.
5. **SQL hors ligne** pour les migrations sensibles : `alembic upgrade <rev_precedente>:<rev> --sql` pour relire le SQL sans l'appliquer.
6. **Appliquer**, uniquement sur la base locale de développement ou de test : `alembic upgrade head`, puis `alembic current`.
7. **Réversibilité**, uniquement sur une base de test jetable sans données à conserver : `alembic downgrade -1` puis `alembic upgrade head`.
8. **Contrôle** : `alembic check` ne doit plus signaler d'écart.
9. **Relecture** par l'agent `database-reviewer` si la migration touche des données existantes, des contraintes d'unicité, des montants ou des tables d'historique (négociations, TradeEvent, audit, paiements).

## Classification des risques

| Opération | Risque | Exigence |
|---|---|---|
| `create_table`, `add_column` nullable, `create_index` | faible | relecture |
| `add_column` NOT NULL, ajout de contrainte UNIQUE/CHECK sur données existantes | moyen | default ou backfill, vérification des données |
| changement de type, renommage | élevé | migration manuelle, plan écrit |
| `drop_column`, `drop_table`, suppression de contrainte | destructif | accord explicite de l'utilisateur et sauvegarde préalable |

## Interdits

- Supprimer ou réinitialiser une base, lancer `alembic downgrade base`, supprimer un volume Docker pour « réparer ».
- Supprimer ou éditer une migration déjà appliquée ou partagée : créer une nouvelle révision.
- Utiliser `alembic stamp` pour masquer un écart sans l'expliquer.
- Exécuter une migration sur une base de production.
- Insérer des données métier réelles dans une migration. Seules les données de référence validées sont admises (catégories Vanilla, Cloves, Cocoa par exemple).

## Résultat attendu

- Révision créée (identifiant, fichier) et opérations qu'elle contient.
- Classification du risque.
- Résultats réels de `upgrade`, `check` et du test de réversibilité.
- Points `À VALIDER`.
