---
name: fastapi-module
description: "Crée ou complète un module métier du backend MadaSource conforme à l'architecture (models, schemas, service, router, permissions, tests), enregistre ses routes sous /api/v1 et documente les choix. À utiliser quand un jour de la roadmap demande d'implémenter un module (buyers, exporters, products, rfqs, quotations, trades…) ou d'ajouter une ressource à un module existant."
argument-hint: "<nom_du_module> [ressource]"
---

# Skill fastapi-module

Module visé : $ARGUMENTS

## Quand l'utiliser

- Le périmètre du jour exige un nouveau module métier ou une nouvelle ressource dans un module existant.
- Ne pas l'utiliser pour créer des modules futurs « au cas où », pour l'infrastructure (→ `docker-ci`) ou pour une migration seule (→ `database-migrations`).

## Prérequis (sinon s'arrêter et le signaler)

- Fondation présente : application factory, router `/api/v1`, session DB, gestion d'erreurs (Jours 4 à 6).
- Documents lus : `docs/backend/architecture.md`, `module-boundaries.md`, `api-conventions.md` (Jour 2), `data-model.md` (Jour 3).

## Procédure

1. **Lire** `CLAUDE.md`, les documents ci-dessus et un module existant pour reprendre son style.
2. **Plan court** : fichiers à créer ou modifier, entités, endpoints (méthode, chemin, permission requise), dépendances vers d'autres modules (via leur service public). Pour un module structurant, faire valider la conception par l'agent `backend-architect`.
3. **`models.py`** : SQLAlchemy 2.x (`Mapped[...]`, `mapped_column`), clé primaire UUID, `organization_id` si la ressource appartient à une organisation, timestamps `DateTime(timezone=True)`, `Numeric(p, s)` pour les montants, statuts contraints. Enregistrer le modèle pour la découverte Alembic.
4. **`schemas.py`** (Pydantic v2) :
   - `<X>Create` / `<X>Update` : uniquement les champs modifiables par le client, `model_config = ConfigDict(extra="forbid")`. Jamais `id`, `organization_id`, `status`, `created_by`, marge ou niveau de vérification en entrée.
   - Schémas de lecture **un par audience** : `<X><Audience>Read`, avec les audiences `Public`, `Buyer`, `ExporterOwner`, `ExporterRecipient`, `Admin` et `AdminFinance` (S-29). Chaque schéma hérite de la classe de base de son audience. Un schéma public n'hérite jamais d'un schéma privé.
   - Montants et quantités en entrée : type qui n'accepte que des chaînes (D-14).
5. **`permissions.py`** : la **politique d'accès** (acteur, action, ressource) → audience ou refus (S-28), et les permissions nommées `<ressource>:<action>` (S-11). Voir le skill `secure-api`.
6. **`service.py`** : logique métier, transitions d'état, transaction, audit, idempotence.
   - Il reçoit la session et l'acteur et ne connaît pas HTTP : pas de `Request`, pas d'`HTTPException`, mais les exceptions de `app/core/exceptions.py`.
   - Seul le cas d'usage appelé par le router fait le commit (D-08).
   - Transitions : verrou `FOR NO KEY UPDATE` avec `populate_existing`, parent avant toute insertion fille, ordre des niveaux (D-09).
7. **`contracts.py`** : DTO immuables renvoyés aux autres modules, jamais d'objet ORM ni de schéma HTTP (D-31). Seulement si d'autres modules appellent celui-ci.
8. **`repository.py`** : seulement si des requêtes sont réutilisées ou complexes. `get_for_actor` et `list_for_actor` appliquent la politique ; un accès non filtré porte un nom explicite (S-14).
9. **`projections.py`** : seulement si le module publie des lectures publiques ou transverses (pour `marketplace` ou `admin`). Ce sont des fonctions qui renvoient un `Select` limité aux colonnes et conditions autorisées. C'est la seule exception déclarée à D-31 ([module-boundaries.md](../../../docs/backend/module-boundaries.md) §6). Ce fichier fait partie de l'interface publique ; `repository.py` n'en fait pas partie.
10. **`router.py`** : endpoints minces (dépendances d'authentification et de permission, appel du service), codes HTTP explicites, pagination sur les listes.
    - Le router instancie **explicitement** le schéma de l'audience retournée par la politique. Jamais de `response_model` en union de schémas d'audiences différentes (D-32).
    - Enregistrer le router dans `app/api/v1/router.py`.
    - Pour les modules de niveau 1 à 3 (`audit`, `auth`, `organizations`), le router est placé dans `app/api/v1/endpoints/` ([module-boundaries.md](../../../docs/backend/module-boundaries.md) §4).
11. **Migration** : skill `database-migrations`.
12. **Tests** (directement ou via l'agent `test-engineer`) :
    - `unit/` : service, transitions ;
    - `integration/` : contraintes ;
    - `api/` : 401, 403, autre organisation, succès, ensemble exact des clés de chaque projection.
13. **Documentation** : skill `api-documentation`, documents `docs/backend/` du module, `.env.example` si une variable est ajoutée.
14. **Vérifications** : skill `pytest-workflow` en mode complet sur le module.

## Vérifications obligatoires

- [ ] Aucune logique métier dans `router.py`.
- [ ] Chaque endpoint privé vérifie organisation, permission et appartenance de la ressource.
- [ ] Schémas de réponse explicites. Aucun champ privé dans les schémas publics, Buyer ou Exporter.
- [ ] Statuts et transitions contrôlés par le service, transitions interdites testées.
- [ ] Montants en `Decimal`, dates UTC timezone-aware, identifiants UUID.
- [ ] Actions sensibles auditées (dès que le module audit existe, Jour 12).
- [ ] Migration relue, tests exécutés, résultats réels rapportés.
- [ ] Aucun import circulaire ni accès direct aux modèles internes d'un autre module.

## Interdits

- Créer des fichiers vides pour des modules futurs.
- Inventer une règle métier : la marquer `À VALIDER` dans la documentation, et dans le code avec `# À VALIDER: <question>`.
- Ajouter une dépendance sans justification écrite.

## Résultat attendu

- Arborescence créée ou modifiée.
- Tableau des endpoints : méthode | chemin | permission | schéma d'entrée | schéma de sortie.
- Décisions prises et points `À VALIDER`.
- Commandes exécutées avec leurs résultats réels.
