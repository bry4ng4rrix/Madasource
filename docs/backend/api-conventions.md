# Conventions de l'API REST — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider

Ces conventions s'appliquent à tous les endpoints. Un écart doit être justifié dans la documentation du module.
Erreurs : [error-handling.md](error-handling.md). Sécurité : [security-design.md](security-design.md).

## 1. Principes

- API-first : l'API est le contrat du futur frontend et des intégrations (CdC §56).
- Ressources nommées par des noms au pluriel, actions métier explicites, formats stables et prévisibles.
- Chaque endpoint déclare son **audience** (public, acheteur, exportateur, admin) et son schéma de réponse propre à cette audience ([security-design.md](security-design.md)).

## 2. Versionnement

| Règle | Statut |
|---|---|
| Préfixe unique `/api/v1` (RJ section 1). | Retenu |
| Changements autorisés dans `v1` : ajout d'un endpoint, ajout d'un champ de réponse, ajout d'un paramètre facultatif, ajout d'une valeur d'énumération documentée. | Proposé |
| Un changement cassant passe par `/api/v2` : suppression ou renommage d'un champ, changement de type ou de sens, nouveau champ obligatoire en entrée, refus d'une requête jusque-là valide. | Proposé |
| Un endpoint déprécié est signalé dans l'OpenAPI et par les en-têtes `Deprecation` et `Sunset`. | Proposé |

## 3. Carte des domaines de l'API

Domaines du CdC §56, rattachés aux modules ([module-boundaries.md](module-boundaries.md)). Les chemins sont proposés ; les chemins définitifs sont fixés au jour d'implémentation de chaque module.

| CdC §56 | Chemins proposés (sous `/api/v1`) | Module | Audience |
|---|---|---|---|
| `/auth` | `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/email-verification`, `/auth/password-reset` | auth | public / authentifié |
| `/users` | `/users/me` | auth | authentifié |
| `/organizations` | `/organizations/current`, `/organizations/current/members` (Q-10) | organizations | membre |
| `/buyers` | `/buyers/registrations` (inscription), `/buyers/me` | buyers | public / acheteur |
| `/exporters` | `/exporters/registrations`, `/exporters/me` | exporters | public / exportateur |
| — | `/verifications` (demandes de l'exportateur), `/admin/verifications` | verification | exportateur / admin |
| `/products` | `/categories` (catégories actives), `/products` (catalogue de l'exportateur) | products | public / exportateur |
| `/products`, `/exporters` (lecture publique) | `/marketplace/products`, `/marketplace/exporters/{public_id}`, `/marketplace/exporters/{public_id}/reviews` | marketplace | public |
| `/rfqs` | `/rfqs` (RFQ de l'acheteur), `/rfq-inbox` (RFQ adressées à l'exportateur) | rfqs | acheteur / exportateur |
| `/matches` | `/rfqs/{rfq_id}/matches` (visibilité : Q-31), `/admin/matching/...` | matching | acheteur ? / admin |
| `/quotes` | `/quotes` (quotations de l'exportateur), `/rfqs/{rfq_id}/quotes` (comparaison par l'acheteur) | quotations | exportateur / acheteur |
| `/negotiations` | `/quotes/{quote_id}/negotiation`, `/quotes/{quote_id}/negotiation/offers`, `/quotes/{quote_id}/accept` | negotiations | parties |
| `/trades` | `/trades`, `/trades/{trade_id}`, `/trades/{trade_id}/events`, `/trades/{trade_id}/transitions`, `/trades/{trade_id}/dashboard` | trades | parties / admin |
| `/payments` | `/trades/{trade_id}/payments`, `/admin/payments` | payment_records | parties / admin |
| `/shipments` | `/trades/{trade_id}/shipments`, `/shipments/{shipment_id}` | shipments | parties / admin |
| `/documents` | `/documents` (dépôt, liste par contexte), `/documents/{document_id}/download` | documents | selon le contexte |
| `/messages` | `/conversations`, `/conversations/{conversation_id}/messages` | messages | participants |
| `/notifications` | `/notifications` | notifications | destinataire |
| `/samples` | `/samples` | samples (Q-53) | acheteur / exportateur |
| `/reviews` | `/trades/{trade_id}/reviews` | reviews | parties |
| — | `/disputes`, `/admin/exceptions` | exceptions | parties / admin |
| `/admin` | `/admin/<domaine>/...` | module du domaine | admin |
| `/analytics` | `/admin/analytics` | admin (Q-62) | admin |
| — | `/health/live`, `/health/ready` | core | technique |

Écarts de nommage avec le CdC §56, proposés et à valider :
- `/messages` devient `/conversations`, car les messages sont rattachés à une conversation ;
- la lecture publique est regroupée sous `/marketplace`, pour séparer nettement les schémas publics des schémas privés ;
- `/payments` désigne des **enregistrements** de paiement, aucun traitement financier (CdC §30).

Les chemins sont en minuscules, avec un tiret entre les mots (`rfq-inbox`). Les paramètres de chemin sont des UUID (`{trade_id}`), sauf l'identifiant public du Passport (`{public_id}`, format : Q-17).

## 4. Méthodes et actions

| Opération | Forme | Réponse |
|---|---|---|
| Lister | `GET /ressources` | 200 et une page |
| Créer | `POST /ressources` | 201, en-tête `Location` et ressource créée |
| Lire | `GET /ressources/{id}` | 200 |
| Modifier partiellement | `PATCH /ressources/{id}` (champs modifiables seulement) | 200 et ressource |
| Action métier | `POST /ressources/{id}/<verbe>` : `submit`, `cancel`, `publish`, `unpublish`, `archive`, `decline`, `accept`, `reject`, `confirm` | 200 et ressource dans son nouvel état |
| Transition générique (machines à nombreux états : Trade, expédition) | `POST /trades/{id}/transitions` avec `{"to_status": "...", "comment": "..."}` ; `GET /trades/{id}/transitions` liste les transitions permises à l'acteur | 200 |
| Supprimer | `DELETE /ressources/{id}`, seulement si la suppression est autorisée par les règles (rare : archivage logique privilégié, BR-PRD-05) | 204 |

- `PUT` n'est pas utilisé.
- Un statut ne se modifie jamais par `PATCH` : uniquement par une action ou une transition (BR-RFQ-01, BR-TRD-06).
- `GET …/transitions` permet au frontend d'afficher les seules actions possibles (RFS J 28, RFS J 32).

## 5. Format JSON

| Règle | Statut |
|---|---|
| JSON UTF-8 en entrée et en sortie. Erreurs en `application/problem+json` ([error-handling.md](error-handling.md)). | Proposé |
| Noms de champs en `snake_case`, comme Python et Pydantic, sans alias. | Proposé |
| `id` : UUID technique. `reference` : identifiant lisible (`RFQ-…`, `MSQ-…`, `MST-…`). | Proposé |
| Horodatages `created_at`, `updated_at`, `expires_at`… ; booléens préfixés `is_` ou `has_`. | Proposé |
| Ressource unique renvoyée sans enveloppe. Listes : enveloppe de pagination (section 6). | Proposé |
| Les schémas d'entrée refusent les champs inconnus (`extra="forbid"`) : un champ réservé au serveur (`status`, `organization_id`, marge…) est rejeté en 422. | Retenu (skill `secure-api`) |

## 6. Pagination, tri et filtres

**Pagination par page**, par défaut :
- paramètres `page` (≥ 1, défaut 1) et `page_size` (1 à 100, défaut 20) ;
- réponse :

```json
{ "items": [], "page": 1, "page_size": 20, "total": 0 }
```

**Pagination par curseur**, pour les flux chronologiques volumineux (messages, notifications, journal d'audit) :
- paramètres `limit` (1 à 100, défaut 50) et `cursor` (opaque) ;
- réponse :

```json
{ "items": [], "next_cursor": null }
```

**Tri** :
- paramètre `sort`, liste séparée par des virgules, préfixe `-` pour l'ordre décroissant (`sort=-created_at`) ;
- seuls les champs déclarés par l'endpoint sont triables ;
- l'`id` sert toujours de critère final, pour un ordre stable.

**Filtres** :
- égalité : `?status=submitted` ; plusieurs valeurs : paramètre répété (`?category=vanilla&category=cocoa`) ;
- intervalles : suffixes `_min` et `_max` (`quantity_min`), `_after` et `_before` pour les dates ;
- texte : `q`.

| Règle de sécurité des filtres | Statut |
|---|---|
| Un endpoint ne filtre et ne trie **que** sur des champs visibles par son audience. Exemple : impossible de trier le marketplace ou les quotations acheteur par prix net fournisseur ou par marge, ce qui reconstituerait l'ordre des marges. | Proposé (R-01) |
| Un paramètre de requête inconnu est refusé (422) plutôt qu'ignoré, pour éviter un résultat faux en silence (modèles de paramètres avec `extra="forbid"`, à vérifier sur la version de FastAPI retenue au Jour 4). | Proposé |

## 7. Dates, montants, quantités

| Type | Format JSON | Exemple | Statut |
|---|---|---|---|
| Instant | ISO 8601 en UTC, suffixe `Z`. En entrée, un décalage est accepté et normalisé en UTC ; une date-heure sans fuseau est refusée. | `"2026-10-12T12:27:00Z"` | Proposé (D-13) |
| Date calendaire | `AAAA-MM-JJ` | `"2026-10-31"` | Proposé |
| Période (livraison cible « en octobre ») | `{"from": "…", "to": "…"}` | `{"from": "2026-10-01", "to": "2026-10-31"}` | Proposé (Q-22) |
| Montant | Objet `amount` (chaîne décimale) et `currency` (ISO 4217, majuscules) | `{"amount": "43.30", "currency": "USD"}` | Proposé (D-14) |
| Prix unitaire | Montant et unité de référence | `{"amount": "43.30", "currency": "USD", "per_unit": "kg"}` | Proposé |
| Quantité | `value` (chaîne décimale) et `unit` | `{"value": "20000", "unit": "kg"}` | Proposé (BR-PRD-03, Q-21) |
| Score de matching | Chaîne décimale de 0 à 100, avec détail par critère | `"94.0"` | Proposé |

- En entrée, montants et quantités sont des **chaînes**. Les nombres JSON sont refusés, pour éviter toute approximation en virgule flottante. Comportement exact à vérifier au Jour 5. Proposé.
- Aucune conversion de devise implicite (BR-CUR-02).
- Précision et arrondis par devise : Q-08.

## 8. Codes, statuts et références

| Élément | Convention | Exemple | Statut |
|---|---|---|---|
| Statuts | Codes en `snake_case` minuscule, stables, dérivés des noms du CdC | `sent_to_exporters`, `trade_confirmed`, `on_hold` | Proposé (D-19) |
| Catégories | Codes minuscules | `vanilla`, `cloves`, `cocoa` | Proposé |
| Incoterms | Abréviation officielle en majuscules | `FOB`, `CFR`, `CIF` | Proposé |
| Pays | ISO 3166-1 alpha-2 | `DE`, `MG` | Proposé |
| Ports | UN/LOCODE | `DEHAM` (Hambourg) | Proposé, référentiel à valider |
| Langues | ISO 639-1 | `en`, `fr` | Proposé |
| Recherche par référence lisible | Filtre `reference` sur la liste | `GET /trades?reference=MST-2026-000145` | Proposé |

Les libellés affichés (en anglais ou en français) sont produits par le frontend à partir de ces codes (D-19).

## 9. Données absentes

- Une donnée inconnue est renvoyée à `null`, champ présent. Jamais de valeur par défaut inventée (BR-SAFE-02).
- Quand l'absence doit être expliquée, par exemple pour un critère de matching sans donnée, l'élément porte un statut explicite : `{"criterion": "certification", "status": "not_available"}`. C'est l'équivalent du « INFORMATION NOT AVAILABLE » du CdC §46. Proposé.

## 10. Idempotence et concurrence

- Les actions critiques (acceptation, confirmation de paiement) sont idempotentes par leur état. Rejouer la même action renvoie le résultat existant (200) ; une action contradictoire renvoie 409 (D-09).
- Un conflit de concurrence renvoie 409 `CONCURRENT_MODIFICATION`, que le client peut retenter ([error-handling.md](error-handling.md)).
- `Idempotency-Key` : non requis en V1.

## 11. En-têtes

| En-tête | Sens | Statut |
|---|---|---|
| `Authorization: Bearer <jeton>` | Authentification ([security-design.md](security-design.md)) | Proposé |
| `X-Request-ID` | Corrélation : repris s'il est fourni et valide, sinon généré ; toujours renvoyé | Proposé |
| `Location` | URL de la ressource créée (201) | Proposé |
| `Retry-After` | Avec 429 et 503 | Proposé |
| `X-MadaSource-Mode: demo` | Réponse d'une instance DEMO (D-18) | Proposé |
| `Accept-Language` | Non exploité en V1 (D-19) | Proposé |

## 12. Codes de statut HTTP

| Code | Usage |
|---|---|
| 200 | Lecture, modification, action réussie |
| 201 | Création (avec `Location`) |
| 204 | Suppression ou action sans contenu (marquer une notification comme lue) |
| 401 | Non authentifié, ou jeton invalide, expiré ou révoqué |
| 403 | Authentifié mais permission insuffisante pour **l'action** |
| 404 | Ressource inexistante **ou** appartenant à une autre organisation (D-25) ; module désactivé |
| 409 | Transition d'état invalide, conflit d'unicité, quotation expirée, conflit de concurrence |
| 413 | Requête ou fichier trop volumineux |
| 415 | Type de contenu non accepté |
| 422 | Données invalides : schéma, ou règle métier sur les données saisies (sous le MOQ, catégorie désactivée…) |
| 429 | Limite de débit atteinte |
| 500 | Erreur interne, sans détail technique |
| 503 | Service indisponible (base injoignable, readiness en échec) |

## 13. OpenAPI

| Règle | Statut |
|---|---|
| Schéma servi sous `/api/v1/openapi.json`, documentation interactive sous `/api/v1/docs`. Exposition en production : à décider ([security-design.md](security-design.md)). | Proposé |
| Un tag par module ; `operationId` unique et stable au format `<module>_<action>` (exemple : `rfqs_submit`), pour la génération de clients. | Proposé |
| Noms de schémas : `<Entité><Audience><Usage>`, par exemple `RFQBuyerRead`, `RFQInboxItemExporterRead`, `ProductPublicRead`, `QuotationBuyerRead`, `QuotationExporterRead`, `QuotationAdminRead`. | Proposé |
| Chaque endpoint documente ses erreurs possibles (codes de [error-handling.md](error-handling.md)) et des exemples **fictifs** (domaines `example.com`, sociétés inventées). | Proposé |

## 14. Limites

| Limite | Valeur proposée | Statut |
|---|---|---|
| Corps JSON | 1 Mio (hors dépôt de fichiers) | Proposé |
| Taille de page | 100 éléments au plus | Proposé |
| Fichiers | Taille et formats : Q-48 (formats : PDF, JPG, PNG, DOCX, CdC §26) | À VALIDER |
| Longueurs de chaînes, nombre de lignes d'une RFQ ou d'une quotation | Fixées par champ au Jour 3 et dans chaque module | À définir |

## 15. Exemples illustratifs

Données fictives. La structure d'une RFQ (lignes, catégorie ou produit précis) dépend de Q-25 ; les champs exacts seront fixés aux Jours 19 à 25.

**Création d'un brouillon de RFQ** (acheteur) : `POST /api/v1/rfqs`

```json
{
  "items": [
    {
      "category": "vanilla",
      "quantity": {"value": "20000", "unit": "kg"},
      "grade": "A",
      "certifications": ["organic"],
      "packaging": null
    }
  ],
  "destination_country": "DE",
  "destination_port": "DEHAM",
  "incoterm": "CIF",
  "target_delivery": {"from": "2026-10-01", "to": "2026-10-31"},
  "target_price": {"amount": "42.00", "currency": "USD", "per_unit": "kg"},
  "payment_preference": null,
  "additional_requirements": "Example only."
}
```

Réponse `201`, en-tête `Location: /api/v1/rfqs/0199…` :

```json
{
  "id": "0199d3a4-6f1e-7c2a-9b1d-2f6e8a1c4b7e",
  "reference": "RFQ-2026-0001",
  "status": "draft",
  "created_at": "2026-10-12T12:27:00Z",
  "updated_at": "2026-10-12T12:27:00Z"
}
```

**Une même quotation, trois audiences** (séparation des schémas, BR-PRC-09) :

| Champ | `QuotationExporterRead` | `QuotationBuyerRead` | `QuotationAdminRead` |
|---|---|---|---|
| `reference`, `status`, validité, Incoterm, quantité, délai | oui | oui | oui |
| Prix net fournisseur (`supplier_unit_price`) | oui (le sien) | **non** | oui |
| Coûts externes détaillés | Q-04 | Q-04 | oui |
| Marge MadaSource | **non** | **non** | oui |
| Prix final acheteur (`unit_price`) | Q-05 | oui | oui |

## 16. Décisions ouvertes

- Écarts de nommage avec le CdC §56 (section 3).
- Visibilité des résultats de matching (Q-31) et des coûts externes (Q-04).
- Exposition de l'OpenAPI en production ([security-design.md](security-design.md)).
- Référentiels pays et ports (UN/LOCODE) : source et mise à jour.
