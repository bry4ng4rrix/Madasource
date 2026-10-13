# Gestion des erreurs — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider (décision D-24 de [architecture.md](architecture.md#12-registre-des-décisions)). Révisée après les revues `backend-architect` et `security-auditor` du Jour 2.

## 1. Objectifs

1. Un **format unique** pour toutes les erreurs de l'API, quelle que soit leur origine : validation, règle métier, sécurité, erreur interne.
2. Un **code stable** et lisible par machine, sur lequel s'appuient le frontend et ses traductions (D-19).
3. **Aucune fuite** :
   - ni trace d'exécution, ni requête SQL, ni chemin de fichier ;
   - ni existence d'une ressource d'une autre organisation ;
   - ni valeur saisie par l'utilisateur ;
   - ni montant, prix ou seuil caché (S-42).
4. Une **corrélation** systématique avec les journaux grâce à l'identifiant de requête, y compris pour les erreurs 500.
5. Toute erreur annule la transaction du cas d'usage : jamais d'écriture partielle (D-08). **Seule exception** : les écritures de sécurité qui doivent survivre au refus (révocation de session sur rejeu d'un jeton, compteurs d'échecs de connexion, audit des refus). Elles passent par l'unité de travail dédiée (D-29).

## 2. Format de réponse

Format proposé : **Problem Details for HTTP APIs (RFC 9457)**, type de contenu `application/problem+json`, avec des membres d'extension propres à MadaSource :

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "This RFQ cannot be submitted in its current status.",
  "code": "INVALID_STATE_TRANSITION",
  "request_id": "6b0f2f8e-1c44-4a51-8f0e-9a7d2b3c1e55",
  "errors": []
}
```

| Membre | Contenu | Obligatoire |
|---|---|---|
| `type` | **`about:blank`** pour toutes les erreurs (D-24, choix de l'utilisateur le 2026-10-13, Jour 5). Le domaine définitif de l'API n'étant pas connu (Q-17, Q-79), aucun URI propre n'est publié. Le sens précis est porté par `code`, contrat du client ; passer plus tard à des URI propres ne casse pas un client qui lit `code`. | Oui |
| `title` | Phrase HTTP standard du statut (`Conflict`, `Not Found`…), exigée par la RFC 9457 §4.2.1 quand `type` vaut `about:blank` | Oui |
| `status` | Code HTTP, identique à celui de la réponse | Oui |
| `detail` | Explication propre à l'occurrence, sans donnée sensible (section 7) | Non |
| `code` | Code stable en majuscules (section 4) : c'est le contrat pour le client | Oui |
| `request_id` | Identifiant de requête, identique à l'en-tête `X-Request-ID` | Oui |
| `errors` | Erreurs par champ, pour une validation (section 3) | Non |

Statut : **Retenu** (D-24, implémenté au Jour 5 dans `backend/app/core/errors.py`). RFC 9457 est retenu parce qu'il est standard et outillé.

## 3. Erreurs de validation

Une donnée d'entrée invalide (corps, paramètre de chemin ou de requête) produit une réponse **422** `VALIDATION_ERROR` avec un élément par erreur :

```json
{
  "type": "about:blank",
  "title": "Unprocessable Content",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "request_id": "…",
  "errors": [
    {"field": "body.items.0.quantity.value", "code": "greater_than", "message": "Input should be greater than 0"},
    {"field": "body.status", "code": "extra_forbidden", "message": "Extra inputs are not permitted"},
    {"field": "query.sort_by_margin", "code": "extra_forbidden", "message": "Extra inputs are not permitted"}
  ]
}
```

| Règle | Statut |
|---|---|
| `field` : emplacement joint par des points, préfixé par `body`, `query` ou `path`. Un paramètre de requête inconnu donne `extra_forbidden` sur `query.<nom>` ([api-conventions.md](api-conventions.md#6-pagination-tri-et-filtres)). | Proposé |
| `code` : type d'erreur de Pydantic (`missing`, `greater_than`, `string_too_short`, `extra_forbidden`…). | Proposé |
| **La valeur saisie n'est jamais renvoyée.** Les erreurs de Pydantic contiennent la valeur fautive (`input`) : vérifié le 2026-10-12, un mot de passe trop court y apparaît en clair. Le gestionnaire par défaut de FastAPI relaie ces erreurs dans la réponse 422. Le gestionnaire MadaSource ne conserve que `field`, `code` et `message` ; il retire `input`, `ctx` et `url`. | Proposé (obligatoire pour la sécurité) |
| Le message d'un validateur personnalisé ne cite jamais la valeur reçue ni une valeur cachée (seuil, plancher). | Proposé |
| Une règle métier sur les données saisies (quantité sous le MOQ, catégorie désactivée, Incoterm non admis) renvoie aussi 422, mais avec son propre code (section 4). | Proposé |

## 4. Catalogue initial des codes

Le catalogue s'enrichit module par module. Un code n'est jamais réutilisé avec un autre sens.

| Code | HTTP | Quand | Remarque |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | Données d'entrée invalides, dont paramètre de requête inconnu | Section 3 |
| `BAD_REQUEST` | 400 | Requête mal formée hors validation de schéma (par exemple en-tête `X-Organization-Id` requis et absent) | Ajouté au Jour 5 |
| `AUTHENTICATION_REQUIRED` | 401 | Aucun jeton fourni | |
| `INVALID_TOKEN` | 401 | Jeton illisible, signature invalide, expiré, révoqué, ou session révoquée | Pas de distinction fine renvoyée au client ; le motif est journalisé |
| `INVALID_CREDENTIALS` | 401 | Échec de connexion | Réponse identique que le compte existe ou non (BR-ACC-05) |
| `REAUTHENTICATION_REQUIRED` | 401 | Action sensible exigeant une authentification récente (S-35) | Le client redemande le mot de passe, et le second facteur s'il est actif |
| `ACCOUNT_NOT_ACTIVE` | 403 | Statut de compte de l'organisation qui ne permet pas l'action (acheteur : Pending, Suspended, Blocked ; exportateur : Q-12) | Statut porté par l'organisation (D-28) ; droits : Q-11, Q-12 |
| `EMAIL_NOT_VERIFIED` | 403 | Action exigeant une adresse vérifiée | Q-13 |
| `PERMISSION_DENIED` | 403 | Rôle ou permission insuffisant pour l'**action** sur un objet visible | Jamais pour un objet hors périmètre (voir `RESOURCE_NOT_FOUND`) |
| `SEPARATION_OF_DUTIES` | 403 | L'admin qui a saisi un paiement tente de le confirmer ou de le rembourser (S-34) | |
| `RESOURCE_NOT_FOUND` | 404 | Ressource inexistante **ou** hors du périmètre de l'acteur ; route inconnue ; module désactivé | D-25 : même réponse dans tous les cas |
| `METHOD_NOT_ALLOWED` | 405 | Méthode non permise sur ce chemin | |
| `CATEGORY_DISABLED` | 422 | Création dans une catégorie dont le flag est désactivé | D-17 |
| `BUSINESS_RULE_VIOLATION` | 422 | Règle métier générique sur les données saisies | Préférer un code spécifique (par exemple `QUANTITY_BELOW_MOQ`), sans montant ni seuil dans `detail` |
| `INVALID_STATE_TRANSITION` | 409 | Transition non permise depuis l'état courant, ou à cet acteur dans cet état | BR-RFQ-01, BR-TRD-06 |
| `QUOTATION_EXPIRED` | 409 | Action sur une quotation ou une proposition expirée | BR-QUO-05 |
| `OFFER_VERSION_MISMATCH` | 409 | La version de la proposition transmise n'est plus la version courante | S-43 ; le client relit la proposition |
| `STALE_EXTERNAL_COST` | 409 | Calcul de prix fondé sur un coût externe expiré | BR-PRC-08 (comportement : Q-04) |
| `CONFLICT` | 409 | Conflit générique avec l'état courant (`ConflictError`) | Ajouté au Jour 5 ; préférer un code précis |
| `ALREADY_ACCEPTED` | 409 | Acceptation contradictoire alors qu'une autre proposition est déjà acceptée | La même acceptation rejouée renvoie 200 (D-09) |
| `DUPLICATE_RESOURCE` | 409 | Violation d'une contrainte d'unicité **anticipée** sur une ressource de l'acteur | **Jamais** pour révéler qu'un email, une société ou un slug existe déjà (S-56) |
| `CONCURRENT_MODIFICATION` | 409 | Interblocage, conflit de sérialisation, attente de verrou expirée | Le client peut retenter |
| `PAYLOAD_TOO_LARGE` | 413 | Corps ou fichier trop volumineux | |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Type de contenu ou de fichier refusé | BR-DOC-01 |
| `RATE_LIMITED` | 429 | Limite de débit ou quota atteint | Avec `Retry-After` |
| `INTERNAL_ERROR` | 500 | Toute erreur non prévue | Aucun détail technique |
| `SERVICE_UNAVAILABLE` | 503 | Base de données ou stockage injoignable, requête trop longue | Avec `Retry-After` si pertinent |

## 5. Hiérarchie d'exceptions

Proposée pour `app/core/exceptions.py` (implémentation au Jour 5) :

| Exception | HTTP | Usage |
|---|---|---|
| `AppError` (racine) | — | Porte `code`, `status`, `title`, `detail` et des extensions non sensibles, jamais de `Decimal` brut (D-14) |
| `ValidationAppError` | 422 | Règle métier sur des données saisies |
| `AuthenticationError` | 401 | Authentification absente ou invalide, ou ré-authentification exigée |
| `PermissionDeniedError` | 403 | Action interdite (dont la séparation des tâches) |
| `NotFoundError` | 404 | Ressource absente ou hors périmètre |
| `ConflictError` | 409 | Conflit générique |
| `InvalidStateTransitionError` | 409 | Transition refusée par une machine d'état |
| `RateLimitedError` | 429 | Limite atteinte |
| `ServiceUnavailableError` | 503 | Dépendance indisponible |

Règles :
- Les **services** lèvent ces exceptions, jamais `HTTPException` : ils ne connaissent pas HTTP.
- Un module peut définir des sous-classes avec un code spécifique (par exemple `QuotationExpiredError`, qui hérite de `ConflictError`).
- Les **routers** ne capturent pas les exceptions pour les reformater.
- Une dépendance FastAPI qui intercepte une exception doit la relancer (exigé depuis FastAPI 0.110.0).

## 6. Gestionnaires centraux

| Exception interceptée | Traitement |
|---|---|
| `AppError` et sous-classes | Réponse Problem Details avec le code de l'exception |
| Erreur de validation de la requête (FastAPI) | 422 `VALIDATION_ERROR`, erreurs nettoyées (section 3) |
| Erreur HTTP de Starlette (route inconnue, méthode non permise) | 404 `RESOURCE_NOT_FOUND` ou 405 `METHOD_NOT_ALLOWED`, au même format |
| Violation d'intégrité de la base | 409 seulement si le nom de la contrainte est connu et associé à un code (conventions de nommage, Jour 3). Sinon 500 `INTERNAL_ERROR`. |
| SQLSTATE `40P01` (interblocage), `40001` (sérialisation, rare en READ COMMITTED), `55P03` (attente de verrou expirée) | 409 `CONCURRENT_MODIFICATION` |
| SQLSTATE `57014` (requête annulée par `statement_timeout`) | 503 `SERVICE_UNAVAILABLE` |
| Base de données injoignable | 503 `SERVICE_UNAVAILABLE` |
| Toute autre exception | 500 `INTERNAL_ERROR`, journalisée avec sa trace, jamais renvoyée au client |

Remarques :
- La lecture du code SQLSTATE dépend du pilote retenu (asyncpg, retenu au Jour 4, D-10). Elle est isolée dans le socle.
- **Réponses 500** : une exception non gérée remonte jusqu'au middleware d'erreur serveur de Starlette, en dehors des autres middlewares. Les en-têtes ajoutés par ceux-ci (`X-Request-ID`, CORS) manqueraient donc, et un frontend d'une autre origine ne pourrait pas lire la réponse. Correctif proposé (C31, revue finale) :
  - un middleware ASGI pur, placé à l'extérieur, place l'identifiant de requête dans l'état de la requête (`scope["state"]`) plutôt que dans une variable de contexte, qui pourrait être réinitialisée en sortie de middleware ;
  - le gestionnaire 500 relit cet identifiant pour poser l'en-tête et le membre `request_id` ;
  - il ajoute aussi les en-têtes CORS des origines autorisées.

  **Implémenté et testé au Jour 5** (`tests/api/test_errors.py`).
- **Réponses 401** : toujours avec un en-tête `WWW-Authenticate: Bearer`, exigé par la RFC 9110 (§15.5.2). Pour `REAUTHENTICATION_REQUIRED`, l'en-tête porte `error="insufficient_user_authentication"`, défini par la RFC 9470 (authentification renforcée).
- Dans tous les cas, la transaction du cas d'usage est annulée avant la réponse. Les seules écritures conservées sont celles de l'unité de travail de sécurité (D-29).

## 7. Règles de sécurité des messages

1. **Ressource hors périmètre** : même réponse qu'une ressource inexistante (`RESOURCE_NOT_FOUND`, 404). Cela vaut aussi pour un identifiant reçu dans le corps ou les paramètres, par exemple un document d'une autre organisation joint à un litige (S-14, S-15).
2. **Connexion, inscription, réinitialisation, renvoi de vérification** : réponse identique que le compte existe ou non, avec un temps de réponse comparable (S-06, S-56).
3. `detail` ne contient jamais :
   - un identifiant d'objet d'une autre organisation ;
   - un montant, un prix, un seuil, une marge ou un coût interne (S-42) ;
   - une donnée bancaire ;
   - un jeton ;
   - un nom de table, de contrainte ou de fichier.
4. Erreurs 500 : message générique fixe. Le diagnostic passe par `request_id` et les journaux.

## 8. Journalisation des erreurs

| Catégorie | Niveau | Contenu |
|---|---|---|
| 4xx attendues (validation, 404, 409) | `INFO` | Code, chemin, méthode, `request_id`, identifiants de l'acteur ; pas de trace |
| 401, 403, 429 répétés | `WARNING` | Mêmes champs, plus l'adresse IP, pour détecter les abus (Audit B) |
| 5xx | `ERROR` | Trace complète, `request_id` |

Les corps de requête ne sont jamais journalisés, et les filtres de nettoyage s'appliquent (D-12). Les refus de sécurité (accès à un objet d'une autre organisation, rejeu d'un jeton, échecs de connexion) sont aussi enregistrés comme **événements d'audit de sécurité**, exécutés après l'annulation de la transaction principale (D-29, BR-AUD-05). Une tentative inter-organisations n'est distinguée d'un identifiant inexistant que par une lecture système limitée (existence et organisation de l'objet), limitée en débit, dont le résultat n'est jamais renvoyé au client (S-14).

## 9. Comportement attendu du client

| Code | Le client peut-il retenter ? |
|---|---|
| `CONCURRENT_MODIFICATION`, `SERVICE_UNAVAILABLE`, `RATE_LIMITED` | Oui, après un délai (`Retry-After` le cas échéant) |
| `INVALID_TOKEN` | Oui, après rafraîchissement du jeton |
| `REAUTHENTICATION_REQUIRED` | Oui, après ré-authentification |
| `OFFER_VERSION_MISMATCH` | Oui, après relecture de la proposition courante |
| Toutes les autres | Non : corriger la requête ou l'état |

## 10. Tests obligatoires

- Chaque code du catalogue a au moins un test API qui vérifie le statut HTTP, le `code` et le type de contenu `application/problem+json`.
- Une validation qui échoue sur un champ `password` ne renvoie pas la valeur saisie.
- Une ressource hors périmètre renvoie exactement la même réponse qu'un identifiant inexistant (hormis `request_id`), y compris quand l'identifiant est passé dans le corps.
- Une exception non prévue renvoie 500 sans trace ni message interne, **avec** `X-Request-ID`.
- Après une erreur, aucune écriture partielle ne subsiste en base, sauf l'événement de sécurité attendu (par exemple, la session révoquée après un rejeu de jeton).
- Aucun message d'erreur de négociation ou de prix ne contient de montant (S-42).

Détails : [testing-strategy.md](testing-strategy.md).
