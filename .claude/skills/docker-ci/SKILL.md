---
name: docker-ci
description: "Vérifie et maintient la configuration Docker (Dockerfile, docker-compose.yml, .dockerignore), les variables d'environnement (.env.example), les contrôles qualité et la CI GitHub Actions du backend MadaSource. Détecte les incohérences de versions et les secrets exposés. À utiliser aux jours d'infrastructure (4 et 7) et dès qu'un de ces fichiers ou une dépendance change."
---

# Skill docker-ci

Pour un travail important sur ces fichiers, déléguer à l'agent `devops-engineer`.

## Procédure

1. **Inventaire** : Dockerfile(s), `docker-compose*.yml`, `.dockerignore`, `.env.example`, `backend/pyproject.toml`, lockfile, `.github/workflows/*`.
2. **Cohérence des versions** :
   - Python identique partout : `requires-python`, `.python-version`, image `python:X.Y-slim`, `python-version` de la CI ;
   - PostgreSQL identique dans Compose et dans le service de CI ;
   - lockfile à jour (avec uv : `uv lock --check`).
3. **Compose** :
   - `docker compose config --quiet` (validation de syntaxe) ;
   - healthchecks, volume nommé pour PostgreSQL, `depends_on` avec `condition: service_healthy` ;
   - ports hôte libres : 5432, 6379 et 8000 sont déjà occupés sur le poste de développement.
4. **Dockerfile** :
   - image de base épinglée, utilisateur non root ;
   - installation reproductible des dépendances (par exemple `uv sync --frozen --no-dev`) ;
   - aucun secret dans `ARG` ou `ENV` ;
   - `.dockerignore` excluant `.env`, `.git`, `.venv` et les caches.
5. **Build et démarrage** : `docker compose build`, `docker compose up -d`, `docker compose ps`, appel des endpoints de santé. Arrêt : `docker compose down`, **sans `-v`**.
6. **CI** :
   - déclenchée sur push et pull request ;
   - jobs lint, format, types, tests, migrations, build ;
   - service PostgreSQL éphémère pour les tests ;
   - aucun `|| true` ni `continue-on-error` sur un contrôle ;
   - secrets uniquement via `${{ secrets.X }}` ;
   - `permissions: contents: read` au minimum, actions épinglées (tag majeur au minimum, SHA de préférence).
7. **Secrets** :
   - rechercher dans les fichiers suivis les motifs `password=`, `secret`, `token`, `AKIA`, `BEGIN PRIVATE KEY` ;
   - vérifier que `.env` est ignoré (`git check-ignore .env`) ;
   - vérifier que `.env.example` ne contient aucune valeur réelle.
   Ne jamais recopier une valeur trouvée : citer seulement son emplacement.

## Interdits

- `docker compose down -v`, `docker volume rm`, `docker system prune` sans accord explicite de l'utilisateur.
- Pousser une image, déployer, se connecter à un environnement de production.
- Afficher les valeurs d'un fichier `.env`.
- Désactiver ou affaiblir un job de CI pour la rendre verte.

## Résultat attendu

| Contrôle | Commande | Résultat réel |
|---|---|---|

Puis : incohérences de versions, secrets détectés (emplacement seulement), corrections effectuées ou proposées.
