# Gestion des erreurs — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider (décision D-24 de [architecture.md](architecture.md#12-registre-des-décisions))

## 1. Objectifs

1. Un **format unique** pour toutes les erreurs de l'API, quel que soit leur origine : validation, règle métier, sécurité, erreur interne.
2. Un **code stable** et lisible par machine, sur lequel s'appuient le frontend et ses traductions (D-19).
3. **Aucune fuite** :
   - ni trace d'exécution, ni requête SQL, ni chemin de fichier ;
   - ni existence d'une ressource d'une autre organisation ;
   - ni valeur sensible saisie par l'utilisateur.
4. Une **corrélation** systématique avec les journaux grâce à l'identifiant de requête.
5. Toute erreur annule la transaction en cours : jamais d'écriture partielle (D-08).

## 2. Format de réponse

Format proposé : **Problem Details for HTTP APIs (RFC 9457)**, type de contenu `application/problem+json`, avec des membres d'extension propres à MadaSource :

```json
{
  "type": "urn:madasource:problem:invalid_state_transition",
  "title": "Invalid state transition",
  "status": 409,
  "detail": "This RFQ cannot be submitted in its current status.",
  "code": "INVALID_STATE_TRANSITION",
  "request_id": "6b0f2f8e-1c44-4a51-8f0e-9a7d2b3c1e55",
  "errors": []
}
```

| Membre | Contenu | Obligatoire |
|---|---|---|
| `type` | URN dérivé du code (`urn:madasource:problem:<code en minuscules>`) | Oui |
| `title` | Résumé court et fixe pour un code donné, en anglais (D-19) | Oui |
| `status` | Code HTTP, identique à celui de la réponse | Oui |
| `detail` | Explication propre à l'occurrence, **sans donnée sensible** | Non |
| `code` | Code stable en majuscules (section 4) : c'est le contrat pour le client | Oui |
| `request_id` | Identifiant de requête, identique à l'en-tête `X-Request-ID` | Oui |
| `errors` | Erreurs par champ, pour une validation (section 3) | Non |

Statut : Proposé (D-24). Les mêmes informations pourraient tenir dans un format maison plus simple. RFC 9457 est retenu parce qu'il est standard et outillé.

## 3. Erreurs de validation

Une donnée d'entrée invalide (schéma Pydantic, paramètre de chemin ou de requête) produit une réponse **422** `VALIDATION_ERROR` avec un élément par erreur :

```json
{
  "type": "urn:madasource:problem:validation_error",
  "title": "Validation error",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "request_id": "…",
  "errors": [
    {"field": "body.items.0.quantity.value", "code": "greater_than", "message": "Input should be greater than 0"},
    {"field": "body.status", "code": "extra_forbidden", "message": "Extra inputs are not permitted"}
  ]
}
```

| Règle | Statut |
|---|---|
| `field` : emplacement joint par des points, préfixé par `body`, `query` ou `path`. | Proposé |
| `code` : type d'erreur de Pydantic (`missing`, `greater_than`, `string_too_short`, `extra_forbidden`…). | Proposé |
| **La valeur saisie n'est jamais renvoyée.** Les erreurs de Pydantic contiennent la valeur fautive (`input`) ; vérifié le 2026-10-12 : un mot de passe trop court y apparaît en clair. Le gestionnaire par défaut de FastAPI relaie ces erreurs dans la réponse 422. Le gestionnaire MadaSource ne conserve donc que `field`, `code` et `message`. Il retire `input`, `ctx` et `url`. | Proposé (obligatoire pour la sécurité) |
| Une règle métier portant sur les données saisies (quantité sous le MOQ, catégorie désactivée, Incoterm non admis) renvoie aussi 422, mais avec son propre code (section 4) plutôt que `VALIDATION_ERROR`. | Proposé |

## 4. Catalogue initial des codes

Le catalogue s'enrichit module par module. Un code n'est jamais réutilisé avec un autre sens.

| Code | HTTP | Quand | Remarque |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | Données d'entrée invalides | Section 3 |
| `UNKNOWN_QUERY_PARAMETER` | 422 | Paramètre de requête non déclaré | [api-conventions.md](api-conventions.md) §6 |
| `AUTHENTICATION_REQUIRED` | 401 | Aucun jeton fourni | |
| `INVALID_TOKEN` | 401 | Jeton illisible, signature invalide, expiré ou révoqué | Pas de distinction fine renvoyée au client ; le motif exact est journalisé |
| `INVALID_CREDENTIALS` | 401 | Échec de connexion | Message identique que le compte existe ou non (BR-ACC-05) |
| `ACCOUNT_NOT_ACTIVE` | 403 | Compte Pending, Suspended ou Blocked pour une action non permise | Droits par statut : Q-11, Q-12 |
| `EMAIL_NOT_VERIFIED` | 403 | Action exigeant une adresse vérifiée | Q-13 |
| `PERMISSION_DENIED` | 403 | Rôle ou permission insuffisant pour l'**action** | Pas pour l'accès à un objet d'une autre organisation (voir `RESOURCE_NOT_FOUND`) |
| `RESOURCE_NOT_FOUND` | 404 | Ressource inexistante **ou** inaccessible à l'organisation de l'acteur | D-25 : même réponse dans les deux cas |
| `CATEGORY_DISABLED` | 422 | Création dans une catégorie dont le flag est désactivé | D-17 |
| `BUSINESS_RULE_VIOLATION` | 422 | Règle métier générique sur les données saisies | Préférer un code spécifique (par exemple `QUANTITY_BELOW_MOQ`) |
| `INVALID_STATE_TRANSITION` | 409 | Transition non permise depuis l'état courant, ou non permise à cet acteur dans cet état | BR-RFQ-01, BR-TRD-06 |
| `QUOTATION_EXPIRED` | 409 | Action sur une quotation ou une proposition expirée | BR-QUO-05 |
| `STALE_EXTERNAL_COST` | 409 | Calcul de prix fondé sur un coût externe expiré | BR-PRC-08 (comportement exact : Q-04) |
| `ALREADY_ACCEPTED` | 409 | Acceptation contradictoire alors qu'une autre proposition est déjà acceptée | La même acceptation rejouée renvoie 200 (D-09) |
| `DUPLICATE_RESOURCE` | 409 | Violation d'une contrainte d'unicité **anticipée** (par exemple un email déjà inscrit, si la politique l'autorise : Q-13) | |
| `CONCURRENT_MODIFICATION` | 409 | Interblocage ou conflit de sérialisation détecté par PostgreSQL | Le client peut retenter |
| `PAYLOAD_TOO_LARGE` | 413 | Corps ou fichier trop volumineux | |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Type de contenu ou de fichier refusé | BR-DOC-01 |
| `RATE_LIMITED` | 429 | Limite de débit atteinte | Avec `Retry-After` |
| `INTERNAL_ERROR` | 500 | Toute erreur non prévue | Aucun détail technique |
| `SERVICE_UNAVAILABLE` | 503 | Base de données ou stockage injoignable | Avec `Retry-After` si pertinent |

## 5. Hiérarchie d'exceptions

Proposée pour `app/core/exceptions.py` (implémentation au Jour 5) :

| Exception | HTTP | Usage |
|---|---|---|
| `AppError` (racine) | — | Porte `code`, `status`, `title`, `detail` et des données d'extension non sensibles |
| `ValidationAppError` | 422 | Règle métier sur des données saisies |
| `AuthenticationError` | 401 | Authentification absente ou invalide |
| `PermissionDeniedError` | 403 | Action interdite à ce rôle |
| `NotFoundError` | 404 | Ressource absente ou hors du périmètre de l'acteur |
| `ConflictError` | 409 | Conflit générique |
| `InvalidStateTransitionError` | 409 | Transition refusée par une machine d'état |
| `RateLimitedError` | 429 | Limite atteinte |
| `ServiceUnavailableError` | 503 | Dépendance indisponible |

Règles :
- Les **services** lèvent ces exceptions, jamais `HTTPException` : ils ne connaissent pas HTTP (CLAUDE.md, `.claude/rules/backend-python.md`).
- Un module peut définir des sous-classes avec un code spécifique (par exemple `QuotationExpiredError`, qui hérite de `ConflictError`).
- Les **routers** ne capturent pas les exceptions pour les reformater : c'est le rôle des gestionnaires centraux.

## 6. Gestionnaires centraux

| Exception interceptée | Traitement |
|---|---|
| `AppError` et sous-classes | Réponse Problem Details avec le code de l'exception |
| Erreur de validation de la requête (FastAPI) | 422 `VALIDATION_ERROR`, erreurs nettoyées (section 3) |
| Erreur HTTP de Starlette (route inconnue, méthode non permise) | 404 `RESOURCE_NOT_FOUND` ou 405, au même format |
| Violation d'intégrité de la base | Convertie en 409 seulement si le nom de la contrainte est connu et associé à un code (conventions de nommage, Jour 3). Sinon 500 `INTERNAL_ERROR`. |
| Interblocage ou conflit de sérialisation (SQLSTATE `40P01`, `40001`) | 409 `CONCURRENT_MODIFICATION` |
| Base de données injoignable | 503 `SERVICE_UNAVAILABLE` |
| Toute autre exception | 500 `INTERNAL_ERROR`, journalisée avec sa trace côté serveur, jamais renvoyée au client |

Dans tous les cas, la transaction est annulée avant la réponse, et `request_id` figure dans la réponse et dans le journal.

## 7. Règles de sécurité des messages

1. **Ressource d'une autre organisation** : même réponse qu'une ressource inexistante (`RESOURCE_NOT_FOUND`, 404), pour ne pas révéler son existence (D-25, BOLA).
2. **Connexion** : même message et même code (`INVALID_CREDENTIALS`) que le compte existe ou non (BR-ACC-05). Le temps de réponse doit aussi être comparable : hachage effectué même pour un compte inexistant ([security-design.md](security-design.md)).
3. `detail` ne contient jamais :
   - un identifiant d'objet d'une autre organisation ;
   - un prix net, une marge ou un coût interne ;
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

Les corps de requête ne sont jamais journalisés, et les filtres de nettoyage s'appliquent (D-12). Une action sensible refusée (tentative d'accès à un Trade d'une autre organisation, par exemple) peut aussi produire un événement d'**audit** avec le résultat « refusé » (RJ 12 : l'audit enregistre le résultat).

## 9. Comportement attendu du client

| Code | Le client peut-il retenter ? |
|---|---|
| `CONCURRENT_MODIFICATION`, `SERVICE_UNAVAILABLE`, `RATE_LIMITED` | Oui, après un délai (`Retry-After` le cas échéant) |
| `INVALID_TOKEN` | Oui, après rafraîchissement du jeton |
| Toutes les autres | Non : corriger la requête ou l'état |

## 10. Tests obligatoires

- Chaque code du catalogue a au moins un test API qui vérifie le statut HTTP, le `code` et le type de contenu `application/problem+json`.
- Une validation qui échoue sur un champ `password` ne renvoie pas la valeur saisie.
- Une ressource d'une autre organisation renvoie exactement la même réponse qu'un identifiant inexistant (hormis `request_id`).
- Une exception non prévue renvoie 500 sans trace ni message interne.
- Après une erreur, aucune écriture partielle ne subsiste en base.

Détails : [testing-strategy.md](testing-strategy.md).
