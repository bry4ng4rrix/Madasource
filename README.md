# MadaSource

Plateforme B2B de facilitation du commerce international, de Madagascar vers les marchés internationaux. Produits de la V1 : vanille, girofle, cacao. Acteurs : acheteurs internationaux, exportateurs malgaches, administrateurs MadaSource.

Ce dépôt contient pour l'instant **le backend seulement** : une API REST FastAPI. Le frontend sera développé après la validation de l'API.

## Contenu

| Chemin | Contenu |
|---|---|
| [`backend/`](backend/) | API FastAPI : code, tests, migrations, Dockerfile |
| [`docs/backend/`](docs/backend/) | Spécifications, architecture, modèle de données, sécurité, rapports journaliers |
| [`docs/decisions/`](docs/decisions/) | Registre des décisions issues des questions au client |
| `docker-compose.yml` | Environnement local : PostgreSQL 18, backend, base de test éphémère |
| [`infrastructure/postgres/`](infrastructure/postgres/) | Script de création du rôle applicatif `madasource_app` |
| `.env.example` | Modèle des variables d'environnement (valeurs factices) |
| `check.md` | Suivi d'avancement, jour par jour |

## Démarrage

Prérequis : Python 3.14, uv 0.13.0, Docker avec Compose. Installation, tests, serveur local, migrations et Docker Compose : **[`backend/README.md`](backend/README.md)**, seule source de vérité des commandes.

## État

Jour 6 de la roadmap backend : fondation de l'API (configuration validée, sondes, erreurs Problem Details, journaux JSON, CORS), base déclarative, migrations Alembic, deux rôles PostgreSQL, base de test isolée. Aucun workflow métier ni table métier n'est encore implémenté. Avancement détaillé : [`check.md`](check.md).

## Sécurité

- Aucun secret n'est versionné : seul `.env.example`, avec des valeurs factices. `.env` est ignoré par Git.
- Aucun déploiement en production n'est configuré à ce stade.
