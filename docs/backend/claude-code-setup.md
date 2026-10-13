# Configuration Claude Code du projet MadaSource

Version de Claude Code au moment de la préparation : **2.1.220** (2026-10-12).
Résultats de l'audit d'environnement : [claude-code-audit.md](claude-code-audit.md).

## 1. Vue d'ensemble

```text
CLAUDE.md                      règles permanentes, chargées à chaque session
.claude/
├── settings.json              permissions (deny/ask) et hooks, partagés via Git
├── agents/                    6 agents spécialisés (sous-agents)
├── skills/                    8 procédures réutilisables (/nom-du-skill)
├── rules/                     règles ciblées, chargées seulement pour les fichiers concernés
├── hooks/                     scripts des hooks (Python, bibliothèque standard)
└── tests/test_hooks.py        auto-test des hooks
```

> **Versionnement (constaté le 2026-10-12)** : le `.gitignore` de l'utilisateur exclut `CLAUDE.md` et les deux roadmaps. Ils ont été retirés de l'index (commit f598049), mais restent présents dans l'historique poussé (commit c6e27d8). Le dossier `.claude/` (agents, skills, règles, hooks, settings) reste versionné. Une copie fraîche du dépôt n'aura donc pas `CLAUDE.md` : ses règles permanentes doivent être transmises autrement si d'autres personnes travaillent sur le projet.

Principe de répartition :
- `CLAUDE.md` : ce qui s'applique toujours, en quelques lignes.
- `rules/` : conventions d'un type de fichier.
- `skills/` : procédures longues et séquencées.
- `agents/` : expertises de revue ou de production, avec des outils limités.

## 2. Agents

| Agent | Rôle | Outils | Écrit des fichiers ? | Quand l'utiliser |
|---|---|---|---|---|
| `backend-architect` | Structure des modules, frontières, couches, dépendances | Read, Grep, Glob, Bash, WebFetch | Non | Avant un nouveau module ou une restructuration |
| `security-auditor` | Auth, permissions, IDOR/BOLA, fuites, secrets, documents, admin | Read, Grep, Glob, Bash | Non | Après des endpoints, de l'auth, des documents ou des paiements |
| `database-reviewer` | Schéma, contraintes, index, Decimal/UTC, transactions, migrations | Read, Grep, Glob, Bash | Non | Modèle de données, `models.py`, avant d'appliquer une migration |
| `test-engineer` | Écriture et analyse des tests Pytest | Read, Grep, Glob, Bash, Edit, Write | Oui, `backend/tests/` | Couvrir une fonctionnalité, analyser un échec |
| `code-reviewer` | Revue généraliste d'un lot (bugs, régressions, conventions) | Read, Grep, Glob, Bash | Non | Après chaque lot, avant de clore un jour |
| `devops-engineer` | Docker, Compose, `.env.example`, CI, documentation d'exploitation | Read, Grep, Glob, Bash, Edit, Write | Oui, infrastructure | Jours 4 et 7, et tout changement Docker ou CI |

**Limite connue** : les agents « lecture seule » disposent de Bash pour `git diff`, `ruff check` ou `pytest`. Bash peut techniquement modifier des fichiers. Ce risque est encadré par leurs instructions et par les hooks de garde, qui s'appliquent aussi aux sous-agents, mais il n'est pas supprimé. Pour un agent strictement en lecture seule, retirer `Bash` de sa ligne `tools`.

### Invoquer un agent

Le nommer dans la demande, par exemple : « Utilise l'agent security-auditor pour auditer le module rfqs. » Claude délègue aussi de lui-même quand la description de l'agent correspond à la tâche.

### Vérifier que les agents sont chargés

- Un agent créé ou modifié peut n'être pris en compte qu'avec un délai. Constaté le 2026-10-12 : les agents créés en cours de session ont d'abord été introuvables, puis sont devenus disponibles plus tard dans la même session, sans redémarrage. Les skills ont été détectés à chaud. Si un agent n'apparaît pas, **redémarrer Claude Code**.
- `/agents` : sur cette version, la commande rappelle d'éditer `.claude/agents/` directement.
- `/doctor` : signale les collisions de noms.
- `claude --debug` : indique pourquoi un fichier serait ignoré (frontmatter invalide, par exemple).

## 3. Skills

| Skill | Invocation | Rôle |
|---|---|---|
| `daily-delivery` | `/daily-delivery 1` | Exécuter un jour de la roadmap, critères de sortie, rapport. Ne passe jamais au jour suivant. |
| `fastapi-module` | `/fastapi-module rfqs` | Créer ou compléter un module conforme à l'architecture |
| `database-migrations` | `/database-migrations "add rfq table"` | Générer, relire et appliquer localement une migration Alembic |
| `secure-api` | `/secure-api rfqs` | Checklist de sécurité par endpoint et tests d'accès refusé |
| `pytest-workflow` | `/pytest-workflow complet` | Contrôles rapides ou complets, analyse des échecs |
| `code-review-madasource` | `/code-review-madasource backend/app/modules/rfqs` | Revue en lecture seule, exécutée par l'agent `code-reviewer` dans un contexte séparé |
| `api-documentation` | `/api-documentation rfqs` | Cohérence entre documentation, code et OpenAPI |
| `docker-ci` | `/docker-ci` | Vérifications Docker, CI, versions, secrets |

Claude peut aussi activer un skill de lui-même quand sa description correspond à la demande.

**Collision évitée** : un skill de projet nommé `code-review` remplacerait la commande intégrée `/code-review`, y compris `/code-review ultra`. Le skill du projet s'appelle donc `code-review-madasource`, et les deux restent utilisables. La commande intégrée `/security-review` reste également disponible, en complément de l'agent `security-auditor`.

**Format** : les descriptions du frontmatter sont entre guillemets doubles. La typographie française (« mot : suite ») produit sinon un YAML invalide, et le fichier serait ignoré.

## 4. Règles ciblées (`.claude/rules/`)

| Fichier | Chargé quand Claude lit ou modifie | Contenu |
|---|---|---|
| `backend-python.md` | `backend/app/**/*.py` | Couches, dépendances inter-modules par niveau et ports, DTO entre modules, transactions (commit par le cas d'usage), verrous (`FOR NO KEY UPDATE`), schéma par audience, erreurs, SQLAlchemy async, Pydantic v2, Decimal, UTC, statuts, logs |
| `alembic-migrations.md` | `backend/alembic/**`, `backend/alembic.ini` | Migrations immuables, opérations destructrices, downgrade |
| `tests.md` | `backend/tests/**` | Structure (dont `e2e/`), base éphémère, machines d'état testées exhaustivement, cas obligatoires, interdits |
| `documentation.md` | `docs/**` | Traçabilité CdC, `À VALIDER`, séparation V1/futur |

Les skills `fastapi-module` et `secure-api` ont été alignés au Jour 2 sur les conventions d'architecture et de sécurité : audiences, permissions `<ressource>:<action>`, DTO, projections, verrous, routers des modules de niveau 1 à 3 dans `api/v1/endpoints/`.

## 5. Hooks

Tous les hooks sont des scripts Python 3 (bibliothèque standard) appelés par `python3`. Ils ne lancent aucune suppression, migration, déploiement ou commande utilisant des secrets.

| Hook | Déclencheur | Commande | Conséquence |
|---|---|---|---|
| Garde Bash | `PreToolUse`, outil `Bash` | `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_bash.py"` | **Refuse** : `sudo`, prune Docker, `rm -r` sur `/`, `~`, `.` ou `*`, lecture ou copie d'un vrai `.env`, `alembic downgrade base`, `DROP DATABASE/SCHEMA` via psql, `chmod 777`, écriture disque brute. **Demande confirmation** : `rm -r`/`rm -f`, `docker compose down -v`, `docker volume rm`, `git reset --hard`, `git clean -f`, push forcé, `git checkout -- .`, `alembic downgrade`, SQL destructif via psql, `dropdb`, `ssh`/`scp`, déploiement, publication, `curl … \| sh`. |
| Garde fichiers | `PreToolUse`, outils `Edit`, `Write`, `NotebookEdit` | `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guard_files.py"` | **Refuse** l'écriture de vrais `.env`, clés et certificats, `secrets/`. **Demande confirmation** pour `.claude/settings*.json`, `.claude/hooks/`, `.github/workflows/`, `roadmap*.md`, `planning.md` et toute révision Alembic déjà existante. |
| Post-édition | `PostToolUse`, outils `Edit`, `Write` | `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/post_edit.py"` | Fichier `.py` : `ruff format` puis `ruff check` (sans `--fix`) sur ce fichier seul, si Ruff est installé. Les erreurs de lint sont renvoyées à Claude. Fichier critique (Docker, CI, dépendances, modèles, migrations, sécurité, configuration Claude) : rappel de relecture par l'agent adapté. Aucun test n'est lancé. |

Remarques :
- Tant que `backend/.venv` n'existe pas (avant le Jour 4), le hook post-édition ne fait que les rappels : Ruff n'est pas installé.
- `ruff format` réécrit le fichier juste après l'édition : Claude doit le relire avant de l'éditer à nouveau. C'est le comportement attendu.
- En cas d'erreur interne, un hook échoue « ouvert » (code 1, non bloquant). Les règles `permissions` de `settings.json` restent actives.
- Aucun hook `Stop` ou `SessionStart` : lancer la suite de tests à chaque fin de réponse ralentirait le travail sans bénéfice. La suite complète passe par `/pytest-workflow complet` aux points de validation.

### Voir, tester, désactiver

- Voir les hooks actifs et leur source : `/hooks`.
- Tester les hooks sans rien exécuter : `python3 .claude/tests/test_hooks.py` (doit afficher `0 échec(s)`).
- Désactiver tous les hooks pour soi seul : créer `.claude/settings.local.json` avec `{"disableAllHooks": true}`. Ce fichier est personnel et ignoré par Git (`.gitignore` du dépôt, depuis le Jour 4).
- Désactiver un seul hook : supprimer son entrée dans `.claude/settings.json`. Cette modification passe elle-même par une confirmation.

## 6. Permissions (`.claude/settings.json`)

- **deny** : lecture et écriture des vrais `.env` (`.env`, `.env.local`, `.env.*.local`, `.env.production`, `.env.prod`), `*.pem`, `*.key`, `secrets/` ; `sudo` ; prune Docker.
- **ask** : `rm -r`/`rm -rf`, `git reset --hard`, `git clean`, push forcé, `docker compose down -v`/`--volumes`, `docker volume rm`, `alembic downgrade`, `dropdb`.

Les règles `permissions` reposent sur des préfixes de commande et peuvent être contournées par une autre écriture de la commande. Le hook `guard_bash.py`, basé sur des expressions régulières, constitue la seconde ligne de défense. Les règles personnelles (« ne plus demander ») vont dans `.claude/settings.local.json`, jamais dans le fichier partagé.

## 7. Commandes de contrôle

| Contrôle | Commande | Disponible |
|---|---|---|
| Auto-test des hooks | `python3 .claude/tests/test_hooks.py` | Oui |
| Validité de `settings.json` | `jq -e . .claude/settings.json` | Oui |
| Lint, format, types, tests, migrations | voir le skill `pytest-workflow` ; commandes définitives fixées aux Jours 4 à 7 dans `backend/README.md` | À partir du Jour 4 |
| Docker et CI | voir le skill `docker-ci` | À partir des Jours 4 et 7 |

## 8. Cycle de travail quotidien

1. Lancer `/daily-delivery N`.
2. Claude lit la roadmap et le périmètre, vérifie les prérequis et propose un plan court.
3. Implémentation limitée au jour, avec tests.
4. `/pytest-workflow complet`.
5. `/code-review-madasource`, plus `security-auditor` ou `database-reviewer` selon le diff.
6. Correction des constats bloquants, mise à jour de la documentation.
7. Rapport dans `docs/backend/daily-reports/day-NN.md`, et ligne du jour mise à jour dans `check.md` (statut, date, résumé).
8. **Validation par l'utilisateur avant le jour suivant.**

## 9. Diagnostic

| Symptôme | Vérification |
|---|---|
| Un agent ou un skill n'apparaît pas | Redémarrer la session. Vérifier le frontmatter : YAML valide, descriptions entre guillemets, `name` identique au nom du fichier (agent) ou du dossier (skill). `claude --debug`, `/doctor`. |
| Un hook ne se déclenche pas | `/hooks` ; `python3 --version` ; `python3 .claude/tests/test_hooks.py` ; `jq -e . .claude/settings.json`. |
| Un hook bloque à tort | Lire la raison préfixée `[MadaSource guard]`. Ajouter le cas à `test_hooks.py`, corriger le motif, relancer l'auto-test. En urgence : `disableAllHooks` dans `settings.local.json`. |
| Le hook post-édition ne lance pas Ruff | Vérifier `backend/.venv/bin/ruff` (créé au Jour 4) ou `ruff` dans le PATH. |
| Claude ne respecte pas une règle | Vérifier qu'elle figure dans `CLAUDE.md` ou dans une règle dont le `paths` correspond au fichier. Garder `CLAUDE.md` sous 200 lignes. |

## 10. Maintenance

- Toute modification de `CLAUDE.md` ou de `.claude/` est reportée dans ce document. Le hook post-édition le rappelle.
- Pas de skill, plugin ou serveur MCP externe sans présentation préalable (origine, utilité, permissions, risques) et accord de l'utilisateur.
