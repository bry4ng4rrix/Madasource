---
paths:
  - "backend/app/**/*.py"
---

# Règles pour le code applicatif Python (backend/app)

- Couches : `router.py` (HTTP mince) → `service.py` (métier, transactions) → `repository.py` facultatif → `models.py`. Un service ne lève pas d'`HTTPException` : il lève des exceptions métier, traduites en HTTP par le gestionnaire central.
- Inter-modules : importer uniquement le service public ou les schémas exportés d'un module de **niveau inférieur** (`docs/backend/module-boundaries.md` §3), jamais ses modèles internes ni son repository. Un appel vers un niveau supérieur passe par un port déclaré (§5.2). Pas de `relationship()` entre modules.
- Transactions : seule la fonction de cas d'usage appelée par le router fait le commit, avant de retourner. Une fonction exposée aux autres modules ne fait jamais de commit (`docs/backend/architecture.md`, D-08).
- Erreurs : lever les exceptions de `app/core/exceptions.py`, au format de `docs/backend/error-handling.md`.
- SQLAlchemy 2.x async : style `Mapped[...]` / `mapped_column`, `select()` et non `session.query()`. Pas de lazy loading implicite en async : utiliser `selectinload`/`joinedload` ou `lazy="raise"`. Une session par requête, obtenue par dépendance.
- Pydantic v2 : `model_config = ConfigDict(...)`, `model_validate`, `model_dump`. Les schémas d'entrée ont `extra="forbid"`. Les schémas publics, privés et admin sont des classes distinctes.
- Montants : `Decimal` et `Numeric(p, s)`, avec la devise à côté. Aucun `float`. Les arrondis sont explicites (`quantize` avec un mode documenté).
- Temps : `datetime.now(UTC)` et `DateTime(timezone=True)`. Jamais de `datetime.utcnow()` ni de datetime naïf.
- Identifiants : UUID pour les clés. Les références lisibles (`MST-AAAA-NNNNNN`…) sont générées par un service dédié, concurrent-safe.
- Statuts : `Enum` Python plus contrainte en base. Les transitions passent par une table de transitions dans le service et sont refusées sinon.
- Logs : structurés, sans mot de passe, token, donnée bancaire ni contenu de document.
- Configuration : lue via l'objet settings (`app/core/config.py`), jamais `os.environ` dispersé. Toute nouvelle variable est ajoutée à `.env.example`.
- Règle métier absente des sources : `# À VALIDER: <question>`, plus une entrée dans `docs/backend/risks-and-open-questions.md`.
