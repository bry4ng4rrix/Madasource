# MadaSource

Plateforme B2B de facilitation du commerce international, de Madagascar vers les marchés internationaux. Produits de la V1 : vanille, girofle, cacao. Acteurs : acheteurs internationaux, exportateurs malgaches, administrateurs MadaSource.

Ce dépôt contient pour l'instant **le backend seulement** : une API REST FastAPI. Le frontend sera développé après la validation de l'API.

## Contenu

| Chemin | Contenu |
|---|---|
| [`backend/`](backend/) | API FastAPI : code, tests, migrations, Dockerfile. Commandes : [`backend/README.md`](backend/README.md) |
| [`docs/backend/`](docs/backend/) | Spécifications, architecture, modèle de données, sécurité, rapports journaliers |
| [`docs/decisions/`](docs/decisions/) | Registre des décisions issues des questions au client |
| `docker-compose.yml` | Environnement local : PostgreSQL 18 et backend |
| `.env.example` | Modèle des variables d'environnement (valeurs factices) |
| `check.md` | Suivi d'avancement, jour par jour |

## Démarrage rapide

Prérequis : Python 3.14, uv 0.13, Docker avec Compose.

```bash
# Backend seul, sans base (application minimale du Jour 4)
cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --port 8001

# Ou avec Docker Compose, depuis la racine
cp .env.example .env    # remplacer les valeurs factices
docker compose up -d --build
curl http://127.0.0.1:8001/health/live
```

## État

Jour 4 de la roadmap backend : squelette du dépôt, outillage et sonde de vivacité. Aucun workflow métier n'est encore implémenté. Avancement détaillé : [`check.md`](check.md).

## Sécurité

- Aucun secret n'est versionné : seul `.env.example`, avec des valeurs factices. `.env` est ignoré par Git.
- Aucun déploiement en production n'est configuré à ce stade.
