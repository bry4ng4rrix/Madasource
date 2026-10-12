# MadaSource — règles permanentes (backend)

Plateforme B2B de facilitation du commerce international, Madagascar → marchés internationaux.
Ce dépôt contient **uniquement le backend** : une API REST FastAPI. Le frontend viendra après validation de l'API.

## Sources de référence

1. Cahier des charges client : « MadaSource — Complete Platform Architecture & Functional Requirements » (PDF de 34 pages, hors dépôt, actuellement dans `~/Téléchargements/`). Cité « CdC §N ».
2. `planning.md` : planning client (50 jours, 10 étapes).
3. `roadmap_backend_fastapi.md` : **roadmap backend de référence (35 jours + audits A–D)**. Les « jours » exécutés sont ceux de ce fichier.
4. `roadmap.md` : roadmap full-stack initiale (50 jours). Contexte uniquement.
5. `docs/backend/` : spécifications et décisions produites jour après jour.

En cas de conflit : CdC > planning > roadmap backend. Signaler le conflit, ne jamais trancher seul.

## Périmètre V1

- Produits : Vanilla, Cloves, Cocoa. Acteurs : Buyer, Exporter, MadaSource Admin.
- Parcours : Marketplace → RFQ → Matching → Quotation → Negotiation → Trade → Documents → Payment Record → Shipment → Delivery → Completion.
- Paiement = enregistrement et justificatif, pas de banque ni de passerelle. Expédition = saisie manuelle. Pas d'IA, aucune intégration externe active.
- Les fonctionnalités futures sont préparées par l'architecture, désactivées par feature flag, et jamais présentées comme actives.

## Stack

Python 3.12+ · FastAPI · Pydantic v2 · PostgreSQL · SQLAlchemy 2.x async · Alembic · Pytest · Ruff · vérificateur de types (choisi au Jour 4/7) · Docker Compose.
Gestionnaire d'environnement proposé : uv (installé sur le poste ; `À VALIDER` au Jour 4).
Redis/Celery uniquement si justifié. Toute nouvelle dépendance doit être justifiée par écrit.

## Architecture

- Monolithe modulaire : `backend/app/modules/<module>/` avec `models.py`, `schemas.py`, `service.py`, `router.py`, `permissions.py`, et `repository.py` si utile.
- Routes HTTP minces : validation → authentification/permission → appel du service → schéma de réponse. La logique métier vit dans `service.py`.
- Un module n'importe pas les internes d'un autre module : il passe par son service public. Les frontières sont définies dans `docs/backend/module-boundaries.md` (Jour 2).
- REST versionnée sous `/api/v1`, OpenAPI à jour.
- Ne pas créer de fichiers vides pour des modules futurs.

## Conventions de données

- UUID pour les identifiants techniques. Les identifiants lisibles (`RFQ-…`, `MSQ-…`, `MST-…`) sont générés côté serveur, uniques, jamais codés en dur.
- Dates timezone-aware, stockées en UTC.
- Montants en `Decimal` / `NUMERIC(p, s)` avec devise explicite, jamais en `float`.
- Statuts contraints (enum ou CHECK). Les transitions passent par un service dédié, jamais par affectation libre.
- Les termes d'un Trade sont figés à l'acceptation. Un changement de taux de change ne les modifie jamais.

## Sécurité (non négociable)

- Chaque endpoint privé vérifie, dans l'ordre : utilisateur authentifié → organisation → permission → appartenance de la ressource.
- Schémas séparés public / privé / admin. Ne jamais exposer : hash de mot de passe, tokens, données bancaires, documents privés, notes internes, coût fournisseur, marge MadaSource.
- Les actions sensibles sont auditées (append-only). L'historique de négociation et les TradeEvent ne sont jamais supprimés par le workflow normal.
- Matching déterministe et explicable : aucun score aléatoire, aucune donnée inventée.
- Une quotation expirée n'est jamais présentée comme valide.
- Le DEMO MODE est explicitement marqué et n'est jamais mélangé aux données réelles.
- Décision métier absente des sources → marquer `À VALIDER`, ne jamais l'inventer.
- Aucun secret dans le dépôt. Seul `.env.example` (valeurs factices) est versionné.

## Tests et vérifications

- Toute fonctionnalité a ses tests. Les endpoints privés ont des tests d'accès refusé et inter-organisations.
- Ne jamais affaiblir une assertion, ignorer une règle Ruff ou désactiver un test pour obtenir une CI verte.
- Les commandes officielles (lint, types, tests, migrations) seront fixées aux Jours 4 à 7 dans `backend/README.md`. Procédure : skill `pytest-workflow`.
- Ne jamais affirmer qu'une commande, un test ou un build a réussi sans l'avoir exécuté.

## Migrations et transactions

- Une migration Alembic par changement cohérent, relue avant application (skill `database-migrations`).
- Ne jamais modifier une migration déjà appliquée ou partagée : en créer une nouvelle.
- Pour « réparer », ne jamais réinitialiser ou supprimer une base, lancer `downgrade base` ou supprimer un volume Docker.
- Les opérations multi-étapes s'exécutent dans une transaction DB. Les actions critiques (acceptation, création de Trade, confirmation de paiement) sont idempotentes.

## Méthode de travail

- Un jour de roadmap à la fois, avec le skill `daily-delivery`. **Ne jamais passer au jour suivant sans validation explicite de l'utilisateur.**
- Lire avant de modifier. Présenter un plan court avant toute modification importante. Signaler les ambiguïtés bloquantes.
- Après chaque lot : agent `code-reviewer`, plus `security-auditor` ou `database-reviewer` selon le diff.
- Rapport de fin : fichiers modifiés, commandes réellement exécutées et leurs résultats, risques, décisions `À VALIDER`, prochaine étape.
- Suivi d'avancement : `check.md` (racine), une ligne par jour avec statut (`OK`, `OK avec réserves`, `Non terminé`, `À faire`), date et résumé court. Mis à jour à la fin de chaque jour. Rapports détaillés dans `docs/backend/daily-reports/`.

## Interdits

- Aucun déploiement en production, aucune connexion à une base de production.
- Aucune commande destructive (`rm -rf`, `docker compose down -v`, `docker volume rm`, `DROP`/`TRUNCATE`, `git reset --hard`, `git push --force`) sans avoir expliqué le risque et obtenu un accord explicite.
- Aucune vraie banque, passerelle de paiement, intégration logistique ou envoi d'email réel sans autorisation explicite.
- Ne pas modifier la roadmap, le planning ou le périmètre sans validation.

## Environnement local (audit du 2026-10-12)

- Shell interactif : fish. L'outil Bash de Claude Code exécute bash.
- Ports hôte déjà occupés : 5432 (PostgreSQL natif), 6379 (Valkey), 8000 (uvicorn d'un autre projet). Docker Compose doit utiliser d'autres ports hôte.
- Python système 3.14, Python 3.12 disponible via uv. Pas de dépôt Git initialisé pour l'instant (prévu au Jour 4).

Configuration Claude Code (agents, skills, hooks) : `docs/backend/claude-code-setup.md`.
