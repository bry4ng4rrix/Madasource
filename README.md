# MadaSource

Plateforme B2B de facilitation du commerce international, de Madagascar vers les marchés internationaux. Produits de la V1 : vanille, girofle, cacao. Acteurs : acheteurs internationaux, exportateurs malgaches, administrateurs MadaSource.

Ce dépôt contient pour l'instant **le backend seulement** : une API REST FastAPI. Le frontend sera développé après la validation de l'API.

## Contenu

| Chemin | Contenu |
|---|---|
| [`backend/`](backend/) | API FastAPI : code, tests, migrations, Dockerfile |
| [`docs/backend/`](docs/backend/) | Spécifications, architecture, modèle de données, sécurité, rapports journaliers |
| [`docs/decisions/`](docs/decisions/) | Registre des décisions issues des questions au client |
| `docker-compose.yml` | Environnement local : PostgreSQL 18 et backend |
| `.env.example` | Modèle des variables d'environnement (valeurs factices) |
| `check.md` | Suivi d'avancement, jour par jour |

## Démarrage

Prérequis : Python 3.14, uv 0.13.0, Docker avec Compose. Installation, tests, serveur local, migrations et Docker Compose : **[`backend/README.md`](backend/README.md)**, seule source de vérité des commandes.

## État

Jour 4 de la roadmap backend : squelette du dépôt, outillage, sonde de vivacité `GET /api/v1/health/live`. Aucun workflow métier n'est encore implémenté. Le démarrage par Docker Compose n'a pas encore été vérifié. Avancement détaillé : [`check.md`](check.md).

## Sécurité

- Aucun secret n'est versionné : seul `.env.example`, avec des valeurs factices. `.env` est ignoré par Git.
- Aucun déploiement en production n'est configuré à ce stade.
