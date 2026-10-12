---
name: pytest-workflow
description: "Lance les contrôles qualité du backend MadaSource (Ruff lint et format, vérification de types, Pytest unitaire/intégration/API, cohérence des migrations), en mode rapide pendant le développement ou complet aux points de validation. Ajoute les tests manquants et analyse les échecs sans les masquer. À utiliser après une modification de code, avant de clore un jour, ou quand un test échoue."
argument-hint: "[rapide | complet | <chemin de test>]"
allowed-tools:
  - Bash(uv run pytest *)
  - Bash(uv run ruff check *)
  - Bash(uv run ruff format *)
---

# Skill pytest-workflow

Mode demandé : $ARGUMENTS (par défaut : rapide)

## Commandes

Provisoires jusqu'aux Jours 4 à 7. Ensuite, la source de vérité est `backend/README.md`, qui prime sur cette liste.
Depuis `backend/` :

| Contrôle | Commande proposée |
|---|---|
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format --check .` |
| Types | outil choisi au Jour 4/7 (mypy ou pyright), par exemple `uv run mypy app` |
| Tests unitaires | `uv run pytest tests/unit -q` |
| Suite complète | `uv run pytest -q` |
| Migrations | `uv run alembic check`, puis `uv run alembic upgrade head` sur la base de test |

Si `backend/` n'existe pas encore, le dire et ne rien exécuter d'inventé.

## Mode rapide (pendant le développement)

1. `ruff check` et `ruff format --check` sur les fichiers modifiés.
2. `pytest -x -q` sur les tests du module modifié.

## Mode complet (fin de lot, fin de jour)

1. `ruff check .` et `ruff format --check .`.
2. Vérification de types.
3. Pytest complet (unit, integration, api), avec la base de test isolée démarrée.
4. `alembic check`, puis `upgrade head` sur la base de test.
5. Si Docker est concerné : skill `docker-ci`.

## Analyse d'un échec

1. Lire le message complet et relancer le test seul : `pytest <chemin>::<test> -x -vv`.
2. Classer la cause : bug applicatif, test erroné ou environnement (base non démarrée, variable manquante).
3. Corriger la cause. Un test n'est modifié que si son attente est fausse, avec une justification écrite dans le rapport.
4. Relancer et rapporter le nouveau résultat.

## Tests manquants

Pour chaque fonctionnalité du lot, vérifier la présence des cas suivants :
- succès ;
- validation (422) ;
- 401 et 403 ;
- accès inter-organisation ;
- transitions interdites ;
- non-exposition des champs privés ;
- idempotence pour les actions critiques.

En cas de volume important, déléguer à l'agent `test-engineer`.

## Interdits

- `skip`, `xfail`, suppression de test ou assertion affaiblie pour obtenir un passage.
- `# noqa` ou `# type: ignore` sans justification en commentaire.
- Présenter une exécution partielle (`--lf`, `-k`) comme la suite complète.
- Exécuter les tests contre une base de développement partagée ou de production.
- Annoncer un résultat qui n'a pas été obtenu.

## Résultat attendu

| Contrôle | Commande exacte | Résultat réel | Durée |
|---|---|---|---|

Puis : échecs analysés, tests ajoutés, limites (ce qui n'a pas pu être exécuté, et pourquoi).
