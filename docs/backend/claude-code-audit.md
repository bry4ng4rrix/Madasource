# Audit de l'environnement et de la configuration Claude Code

Date : 2026-10-12 · Réalisé avant toute préparation, puis complété après vérification.
Ne sont rapportés que les éléments réellement inspectés. Les points non vérifiables sont signalés comme tels.

## 1. Environnement détecté

| Élément | Constat | Commande |
|---|---|---|
| Claude Code | 2.1.220 | `claude --version` |
| Système | Arch Linux (rolling), noyau 7.2.9, x86_64 | `uname -srm`, `/etc/os-release` |
| Shell | fish en interactif. L'outil Bash de Claude Code exécute bash. | erreur de syntaxe fish observée |
| Python système | 3.14.7 (`python`, `python3`) | `python3 --version` |
| Python 3.12 | 3.12.14, installé et géré par uv | `uv python list --only-installed` |
| uv | 0.12.23 | `uv --version` |
| Git | 2.56.0. **Le projet n'est pas un dépôt Git.** | `git rev-parse` |
| Docker / Compose | Docker 29.8.2 (démon accessible, aucun conteneur actif), Compose 5.6.0 | `docker info`, `docker ps` |
| PostgreSQL client | psql 18.6 | `psql --version` |
| Valkey (compatible Redis) | 9.1.2 | `redis-server --version` |
| Node / npm | 26.10.0 / 12.2.0 (inutiles pour le backend) | |
| jq | 1.8.2 | |
| Absents | ruff, mypy, pyright, poetry, pre-commit, pipx, gh, shellcheck, podman | `command -v` |
| Ports hôte occupés | 5432 (PostgreSQL natif), 6379 (Valkey), 8000 (uvicorn d'un autre projet) | `ss -ltnp` |
| Venv parent | `~/Dev/.venv` (Python 3.14, 87 paquets), trouvé par `uv run --no-project` depuis ce dossier. Aucun `VIRTUAL_ENV` actif. | |

> **Mise à jour du 2026-10-12, 15 h 27** :
> - l'utilisateur a initialisé un dépôt Git (branche `main`, remote GitHub `origin`, commit « preparations ») et ajouté le cahier des charges à la racine. Le fichier est identique à celui de `~/Téléchargements/` (même empreinte SHA-256) ;
> - aucun `.gitignore` n'existe encore (prévu au Jour 4). Seul `.claude/settings.local.json` est exclu, par le fichier global `~/.config/git/ignore` de l'utilisateur ;
> - Python système : 3.14.8.

## 2. État initial du projet

- Fichiers présents : `planning.md`, `roadmap.md`, `roadmap_backend_fastapi.md`. Aucun code, aucun `CLAUDE.md`, aucun `.claude/`, aucun `pyproject.toml`, aucun `README.md`.
- Cahier des charges trouvé hors du projet : `~/Téléchargements/MadaSource Platform Architecture.pdf`, « MadaSource — Complete Platform Architecture & Functional Requirements », 34 pages, généré le 2026-08-28. Lu intégralement après extraction texte avec `pdftotext` (copie dans le scratchpad de session uniquement, pas dans le dépôt).

## 3. Configuration Claude Code existante

| Niveau | Constat |
|---|---|
| Utilisateur `~/.claude/settings.json` | Thème, niveau d'effort par modèle, notifications. Aucune permission, aucun hook. |
| Agents utilisateur | Aucun (`~/.claude/agents` absent). |
| Règles et CLAUDE.md utilisateur | Aucun. |
| Skills utilisateur | Skills synchronisés depuis claude.ai (docx, pdf, pptx, xlsx, docs, deep-research, etc.). Aucun ne concerne FastAPI ou ce projet. Aucun conflit de nom avec les skills créés. |
| Plugins | `claude plugin list` répond « No plugins installed ». La session expose pourtant des skills `design:*` et `humanizer:*`, ainsi que des serveurs MCP `plugin:design:*` (Asana, Atlassian, Figma, Intercom, Linear, Notion, Slack) non authentifiés. Ils proviennent vraisemblablement de la synchronisation du compte claude.ai (**non vérifié**). Sans usage pour ce projet. |
| Serveurs MCP | Aucun dans `~/.claude.json`, aucun `.mcp.json` dans le projet. Disponibles dans la session : connecteur claude.ai « Claude Docs », MCP de l'IDE VS Code (`getDiagnostics`). |
| Skills intégrés pertinents | `/code-review` (revue, dont `ultra`), `/security-review`, `/simplify`, `/init`. |

## 4. Conflits, doublons et incohérences

| # | Constat | Traitement |
|---|---|---|
| C1 | Deux roadmaps : `roadmap.md` (full-stack, 50 jours, Jour 1 → `docs/*.md`) et `roadmap_backend_fastapi.md` (backend, 35 jours, Jour 1 → `docs/backend/*.md`). | La roadmap backend est la référence, conformément à la mission de préparation. Inscrit dans `CLAUDE.md`. |
| C2 | Le « prompt quotidien » de la roadmap backend cite `docs/backend/roadmap-backend-fastapi.md`. Le fichier réel est `roadmap_backend_fastapi.md`, à la racine. | Fichier non déplacé. Le skill `daily-delivery` pointe vers le fichier réel. Déplacement éventuel : **À VALIDER** (Jour 4). |
| C3 | Un skill de projet `code-review` remplacerait la commande intégrée `/code-review` (documentation officielle des skills). | Skill renommé `code-review-madasource`. |
| C4 | `/security-review` intégré et l'agent `security-auditor` se recouvrent en partie. | Conservés tous les deux : le premier relit le diff de branche, le second fait un audit ciblé avec les règles MadaSource. |
| C5 | La typographie française (« : ») rend invalide le YAML non quoté des descriptions. | Détecté par validation pyyaml, corrigé (descriptions entre guillemets), règle documentée. |
| C6 | Ports 5432, 6379 et 8000 occupés sur l'hôte. | Inscrit dans `CLAUDE.md`, l'agent `devops-engineer` et le skill `docker-ci`. Choix des ports Compose au Jour 4. |
| C7 | Python système 3.14, roadmap « 3.12+ ». | Version à figer au Jour 4 (**À VALIDER**). 3.12 est disponible via uv. |
| C8 | Cahier des charges hors dépôt (`~/Téléchargements`). | Archivage dans le dépôt (`docs/source/`) : **À VALIDER** (confidentialité du document client). |

## 5. Dépendances manquantes

Aucune installation globale nécessaire. À ajouter au Jour 4 comme dépendances de développement du projet, dans `backend/.venv` via uv : `ruff`, le vérificateur de types (mypy ou pyright, choix à documenter), `pytest`, `pytest-asyncio` (ou équivalent), `httpx`.
Facultatif, au Jour 7 : CLI `gh` pour GitHub Actions, si un dépôt GitHub est utilisé.

## 6. Configurations risquées

- Avant préparation : aucune (pas de permission large, pas de hook, pas de `bypassPermissions`).
- Après préparation : risques résiduels décrits en section 9.

## 7. MCP et plugins : évaluation

Rien n'a été installé.

| Candidat | Utilité pour MadaSource | Décision | Condition |
|---|---|---|---|
| GitHub (MCP) | Faible aujourd'hui : pas de dépôt Git, pas de remote. Au Jour 7, la CLI `gh` suffit pour les workflows et les PR. | Non installé | Réévaluer au Jour 7, avec accord. |
| Documentation de bibliothèques (MCP tiers type Context7) | Moyenne : vérifier les API FastAPI, SQLAlchemy et Pydantic à jour. WebFetch sur les documentations officielles couvre déjà ce besoin. | Non installé | Présenter origine, permissions et risques avant tout ajout. |
| PostgreSQL (MCP) | Faible, et risqué. | Non installé | Jamais sur une base de production. Éventuellement en lecture seule sur la base locale de développement, plus tard et avec accord. |
| Suivi de tâches (Linear, Asana, Notion…) | Aucun service utilisé par le projet. | Non installé | Seulement si le projet en adopte un. |
| Claude Docs (connecteur claude.ai) | Faible : la documentation du projet vit dans le dépôt. | Non utilisé | |
| MCP de l'IDE (`getDiagnostics`) | Utile pour lire les diagnostics de l'éditeur. | Déjà disponible | |

## 8. Hooks : évaluation

| Hook envisagé | Décision | Raison |
|---|---|---|
| Garde Bash (`PreToolUse`) | **Activé** | Seconde ligne de défense contre les commandes destructrices et la lecture des secrets. |
| Garde fichiers (`PreToolUse`) | **Activé** | Protège les secrets, la configuration Claude, la CI, la roadmap et les migrations existantes. |
| Ruff après édition (`PostToolUse`) | **Activé**, inopérant tant que Ruff est absent | Contrôle rapide d'un seul fichier : `format`, puis `check` sans `--fix`. |
| Suite de tests à chaque fin de réponse (`Stop`) | Rejeté | Trop lourd. La suite complète passe par `/pytest-workflow complet`. |
| `ruff check --fix` automatique | Rejeté | Corrections silencieuses du code. Seul le formatage est appliqué automatiquement. |
| Contexte au démarrage (`SessionStart`) | Rejeté | `CLAUDE.md` suffit. |

## 9. Validations exécutées

| Contrôle | Commande | Résultat |
|---|---|---|
| JSON de `settings.json` | `jq -e . .claude/settings.json` | Valide |
| Frontmatter des 6 agents, 8 skills et 4 règles | script pyyaml (`yaml.safe_load`, champs requis, `name` = nom du fichier ou du dossier) | 18/18 valides, après correction de C5 |
| Auto-test des hooks | `python3 .claude/tests/test_hooks.py` | 0 échec |
| Hook actif dans la session | `cat .env` lancé par Claude | Refusé par `guard_bash.py` (message `[MadaSource guard]`) |
| Hook post-édition actif | modification de `CLAUDE.md` et d'un skill par Claude | Rappel `[MadaSource post-edit]` reçu |
| Chargement des skills | liste des skills exposée par Claude Code pendant la session | **Vérifié** : les 8 skills du projet ont été détectés à chaud, sans redémarrage |
| Chargement des agents | appel de l'agent `code-reviewer` pendant la session | **Chargés avec délai** : un premier appel a échoué (« Agent type 'code-reviewer' not found »). Plus tard dans la même session, sans redémarrage, Claude Code a annoncé les 6 agents comme disponibles. |

**Non vérifié** :
- le passage réel de Ruff dans le hook, Ruff n'étant pas installé (chemin testé avec un faux binaire) ;
- l'exécution du skill `code-review-madasource` avec `context: fork`. L'agent `code-reviewer` est désormais chargé, mais le skill n'a pas encore été lancé. La revue du Jour 1 a été faite par un agent généraliste appliquant les instructions de `.claude/agents/code-reviewer.md`.

## 10. Risques et limites restants

1. Les agents « lecture seule » disposent de Bash : seuls leurs instructions et les hooks les empêchent de modifier des fichiers.
2. Les motifs des hooks et des permissions ne couvrent pas toutes les écritures possibles d'une commande, par exemple un script Python qui supprime des fichiers. Ils réduisent le risque sans l'éliminer.
3. Sans dépôt Git, aucun historique ne permet de revenir en arrière ; les revues travaillent sur des listes de fichiers. Recommandation : initialiser Git dès le Jour 4, ou plus tôt sur accord.
4. Les commandes de qualité indiquées dans les skills sont provisoires jusqu'aux Jours 4 à 7.
5. `docker compose config` affiche les valeurs résolues des variables d'environnement : ne pas l'exécuter avec un vrai `.env` dans un contexte partagé.

## 11. Éléments nécessitant l'accord de l'utilisateur

- Initialisation du dépôt Git (prévue au Jour 4).
- Archivage du cahier des charges dans le dépôt.
- Déplacement éventuel de la roadmap vers `docs/backend/`.
- Choix de la version Python (3.12 ou plus récente) et du vérificateur de types.
- Tout futur serveur MCP ou plugin.
