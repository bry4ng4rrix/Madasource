# Jour 8 — Primitives de sécurité

Date : 2026-10-16 · Statut : **TERMINÉ AVEC RÉSERVES**. Réserves :
- aucune primitive n'est encore utilisée par un endpoint : la connexion, l'inscription et la réinitialisation arrivent au Jour 10, avec les règles de limitation de débit ;
- valeurs proposées, `À VALIDER` : politique de mot de passe (Q-76), taille des corps, HSTS, limiteur par processus, contrôle de la clé de signature, concurrence Argon2id (Q-106) ;
- hérité : Q-104 f (protection de `main`, reportée avant la mise en production), Q-105 (laissée ouverte), Q-71 (dépôt public).

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 8 : implémenter les primitives transversales (hachage de mot de passe par une bibliothèque maintenue, utilitaires de sécurité, configuration des secrets, validation d'entrées, protection des journaux, réponses HTTP sûres, stratégie de limitation de débit), sans cryptographie maison ni secret réel, avec tests et mise à jour de `security-design.md`. L'authentification complète vient au Jour 10.

## Décisions prises avec l'utilisateur (2026-10-16)

| Sujet | Choix |
|---|---|
| Bibliothèque de hachage | **argon2-cffi** (implémentation de référence) |
| Paramètres Argon2id | **Profil OWASP** m = 19 MiB, t = 2, p = 1 (Password Storage Cheat Sheet, consultée le jour même) |
| Limitation de débit | **En mémoire, derrière une interface** ; Redis quand plusieurs instances seront déployées (D-20) |
| Clé de signature des jetons | **Configurée dès le Jour 8** (`AUTH_SIGNING_KEY`, obligatoire) |

## Prérequis vérifiés

- Jour 7 clos : CI verte sur GitHub (run `38860611486`, commit `5b6411c`) après l'addendum du 2026-10-16.
- Socle des Jours 5 à 7 présent : en-têtes de sécurité, masquage des journaux, Problem Details, `RateLimitedError`, `X-Request-ID` validé.
- Tu as commité le travail en cours de journée (`ba89ee7`, `d01d9ff`, `421f5e5`) ; les derniers correctifs sont dans l'arbre de travail, non commités.

## Fichiers créés et modifiés

| Fichier | Contenu |
|---|---|
| `backend/app/core/security.py` (nouveau) | `PasswordHasher` : Argon2id, NFKC, `needs_rehash`, calcul complet sur une empreinte factice pour un compte inexistant, une empreinte illisible ou aux paramètres démesurés, une saisie trop longue ou non encodable (S-06) ; variantes asynchrones dans un fil, au plus 4 calculs simultanés par processus, place gardée jusqu'à la fin du fil même si l'appelant est annulé, sémaphore par boucle, 503 au-delà de 5 s d'attente. `check_password_policy` (saisie bornée avant NFKC, minimum sur la forme la plus courte). Jetons opaques : `generate_token` (256 bits), `hash_token` (SHA-256), `token_matches` (temps constant) |
| `backend/app/core/rate_limit.py` (nouveau) | `RateLimiter` (interface), `InMemoryRateLimiter` (fenêtre glissante exacte, compteurs par règle, clés réduites à SHA-256, 100 000 clés par règle au plus), `rate_limit` (dépendance FastAPI, 429 avec `Retry-After`), `client_ip` et `normalize_ip` (IPv4 transportée en IPv6, IPv6 par /64) |
| `backend/app/core/middleware.py` | `BodySizeLimitMiddleware` (413 au-delà de 1 MiB, annoncé ou compté à la lecture ; `Content-Length` illisible : 400) ; `Content-Security-Policy: frame-ancestors 'none'`, `X-Frame-Options: DENY` ; HSTS en `staging`, `production`, `demo` |
| `backend/app/core/errors.py` | HSTS aussi sur les réponses 500 |
| `backend/app/core/config.py` | `AUTH_SIGNING_KEY` (obligatoire, ≥ 43 caractères ; en déploiement : pas de valeur d'exemple, ASCII imprimable sans espace, ≥ 16 caractères distincts) ; paramètres Argon2id bornés (plancher par profil OWASP, plafonds) ; concurrence ; longueurs de mot de passe ; `MAX_REQUEST_BODY_BYTES` ; `FORWARDED_ALLOW_IPS` (`*` et réseaux de préfixe nul refusés en déploiement) |
| `backend/app/core/exceptions.py` | `PasswordPolicyError` (422 `PASSWORD_POLICY_VIOLATION`), `PayloadTooLargeError` (413, pour les services : dépôts, Jour 29) |
| `backend/app/core/logging.py` | Clés masquées ajoutées : `signing_key`, `private_key`, `credential`, `pepper`, `otp`, `jwt`, `bearer`, `signature` |
| `backend/app/main.py` | Limiteur et `PasswordHasher` uniques par application (`app.state`) ; middleware de taille des corps, le plus interne |
| `backend/pyproject.toml`, `uv.lock` | `argon2-cffi` 25.1.0 (apporte `argon2-cffi-bindings` 26.1.0, `cffi` 2.1.1) ; `pycparser` retenu en 3.0 (`constraint-dependencies`) : 3.1 et 3.11 avaient moins de 14 jours (Q-104 b) |
| `.env.example`, `docker-compose.yml` | `AUTH_SIGNING_KEY` (valeur factice `changeme…`, obligatoire dans Compose) ; réglages facultatifs documentés |
| `backend/tests/unit/core/test_security.py`, `test_rate_limit.py` (nouveaux), `tests/api/test_security_primitives.py` (nouveau), `test_config.py`, `test_logging.py`, `tests/support.py` | Voir « Tests » |
| `backend/README.md` | Dépendance justifiée, variables, structure |
| `docs/backend/security-design.md` | S-01, S-02, S-06, §15, §16, §17, §18 : implémentation et statuts |
| `docs/backend/error-handling.md`, `architecture.md`, `risks-and-open-questions.md` | Code `PASSWORD_POLICY_VIOLATION`, nouvelles exceptions ; Redis ; Q-76 (valeurs proposées), **Q-106** |
| `docs/backend/daily-reports/day-08.md` | Ce rapport |

## Tests

- **Hachage** : format et paramètres de l'empreinte, sel aléatoire, bon et mauvais mot de passe, empreintes illisibles, tronquées ou aux paramètres démesurés (calcul factice prouvé par espion), compte inexistant, `needs_rehash`, équivalence Unicode, saisie trop longue ou non encodable, exécution dans un fil, concurrence bornée, 503 en saturation, place gardée après annulation, plusieurs boucles d'événements.
- **Politique** : bornes, messages fixes, refus avant normalisation (espion sur `unicodedata.normalize`), ligatures qui s'étendent en NFKC, surrogates.
- **Jetons** : longueur, unicité, empreinte, comparaison, entrée non encodable.
- **Limiteur** : fenêtre glissante, `Retry-After`, refus qui ne prolongent pas la fenêtre, indépendance des clés et des règles (y compris de même nom), saturation d'une règle sans effet sur une autre, clés longues, éviction, normalisation des adresses.
- **HTTP** (application réelle) : 413 annoncé et par morceaux, 400 pour un `Content-Length` illisible, 429 Problem Details avec `Retry-After`, en-têtes de cadre, HSTS sur 200, 404 et 500 en `staging`, `production`, `demo`, absent en local.
- **Configuration** : clé obligatoire, courte, d'exemple ou faite à la main refusée en déploiement sans recopie dans le message ; profils OWASP acceptés et valeurs juste en dessous refusées ; `FORWARDED_ALLOW_IPS`.

## Démarche et revues

| Étape | Résultat |
|---|---|
| Recherche | argon2-cffi 25.1.0 (2025-06-03, MIT, roues `abi3` pour 3.14) ; OWASP Password Storage Cheat Sheet ; pycparser 3.11 trop récent, retenu en 3.0 |
| Revue de code (`code-reviewer`) | Prêt avec réserves, 0 bloquant. Importants : plancher Argon2 plus lâche que la table OWASP ; HSTS absent des 500 ; éviction du limiteur exploitable. Facultatifs : code mort, `isdigit`, exception redondante, tests faibles (constante, attribut privé, dépendance à l'ordre). Corrigés |
| Audit sécurité (`security-auditor`) | 0 critique. Moyens : éviction partagée entre règles et clés non bornées ; adresse du client (proxy, IPv6) ; NFKC sur une entrée non bornée ; concurrence Argon2 non bornée. Faibles : surrogates (500), clé de signature triviale acceptée, HSTS sur les 500, écart de durée sur empreinte illisible, minimum satisfait par expansion NFKC, `Content-Length`. Corrigés ; risques résiduels en Q-106 |
| Vérification ciblée (`security-auditor`) | 5 correctifs confirmés, 4 partiels : sémaphore relâché à l'annulation (moyen), empreinte tronquée sans calcul, `0.0.0.0/0` accepté, sémaphore lié à une boucle, `hash_token` sur surrogate ; plus deux règles de même nom partageant leurs compteurs et empreintes stockées aux paramètres démesurés. Tous corrigés, avec tests |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `uv add argon2-cffi==25.1.0`, puis `uv lock` avec la contrainte `pycparser==3.0` | 4 paquets ajoutés ; pycparser 3.11 → 3.0 |
| `make check` (final) | Ruff, format, mypy (46 fichiers), import-linter (2 contrats) : OK ; **322 passed, 23 deselected** |
| Rejeu du job `tests` : projet Compose `madasource-ci`, `.env.example`, base neuve | `make migrations-check` : deux révisions, « No new upgrade operations detected. » ; `make test` : **345 passed**, couverture **99,21 %** ; aucun mot de passe dans les journaux du conteneur ; base arrêtée (`down` sans `-v`) |
| Rejeu du job `docker` | `docker compose config --quiet` OK (avec et sans profil `test`, `AUTH_SIGNING_KEY` obligatoire) ; image construite avec la nouvelle dépendance, utilisateur `10001:10001` |
| gitleaks 8.30.1 (binaire vérifié au Jour 7) | Historique (32 commits) et arbre de travail : aucune fuite. Une première clé de test factice détectée (`generic-api-key`) a été remplacée par une valeur sans aléa, plutôt qu'ajoutée aux exceptions |
| Sondes locales (`backend/.venv/bin/python`, sans base ni réseau) | `Content-Length` `-1`, `abc`, `5000` : 400, 400, 413 |
| Auto-test des hooks de Claude | 0 échec |

Non exécuté : la CI sur GitHub avec l'état final (les derniers correctifs ne sont pas commités) ; un vrai serveur uvicorn (`Expect: 100-continue`, HTTP/2, `Content-Length` invalides au niveau de h11) ; la recherche d'avis de sécurité sur argon2-cffi 25.1.0 et pycparser 3.0.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : hachage, jetons, secrets, validation (taille des corps, politique), journaux, en-têtes, limitation de débit ; pas de cryptographie maison |
| Tests appropriés et résultat connu | Oui : 345 tests, couverture 99,21 %, cas d'abus issus des revues |
| Migrations et contraintes cohérentes | Sans objet : aucun modèle ni migration ; montée depuis une base vide et `alembic check` sans écart |
| Documentation et `.env.example` à jour | Oui |
| Aucun secret ajouté | Oui : gitleaks sans fuite ; valeurs factices seulement |
| Défauts critiques corrigés ou signalés | Oui : aucun critique ; moyens et faibles corrigés ; risques résiduels en Q-106 |
| Décisions non définies marquées `À VALIDER` | Oui : Q-76, Q-106 |

## Décisions À VALIDER

| Sujet | Échéance |
|---|---|
| **Q-76** : longueur de mot de passe (12 à 128 proposés ; le NIST demande 15 sans second facteur), refus des mots de passe compromis (non implémenté), seuils de limitation par endpoint | Jour 10 |
| **Q-106 a** : taille maximale des corps (1 MiB) | Avant le Jour 10 |
| **Q-106 b** : HSTS `max-age=31536000; includeSubDomains`, sans `preload`, y compris en `demo` | Au déploiement |
| **Q-106 c** : limiteur par processus ; remise à zéro possible par saturation d'une règle ; au Jour 10, combiner adresse et compte | Jour 10 |
| **Q-106 d** : contrôle de la clé de signature en déploiement (plus strict que « longueur seule »), rotation | Audit D |
| **Q-106 e** : `FORWARDED_ALLOW_IPS` et topologie du proxy ; plusieurs workers multiplient la limite | Avant le premier endpoint limité (Jour 10) |
| **Q-106 f, g** : concurrence Argon2id (4) et limite mémoire du conteneur ; mémoire du limiteur (environ 100 MiB par règle saturée) | Au déploiement |
| Q-104 f, Q-105, Q-71 | Voir les rapports précédents |

## Risques et limites

- **Primitives non encore branchées** : leur efficacité dépendra de leur usage au Jour 10 (clés de limitation, `None` pour tout compte non connectable, une colonne d'empreinte par type de jeton).
- **Limiteur en mémoire** : une limite par processus ; derrière un proxy mal configuré, une seule limite pour tous ou une adresse choisie par le client.
- **Durée comparable** : une empreinte faite avec d'anciens paramètres reste distinguable jusqu'à son rehachage.
- **Tests plus lents** : chaque application de test calcule une empreinte factice au démarrage (suite sans base : environ 2 s → 6 s).

## Préparation du Jour 9 (non exécuté)

Jour 9 — Organizations et RBAC : modèles, schémas, services, migrations et tests pour Organization, User, Role, Permission et OrganizationMembership ; rôles actifs Buyer, Exporter, MadaSource Admin ; vérification des permissions côté serveur et isolation par organisation ; tests d'accès autorisé, refusé et inter-organisations.

Prérequis et questions :
- premières tables métier : première migration de schéma (skill `database-migrations`, agent `database-reviewer`) ;
- **Q-104 c** (conflit sur `ports` entre la règle `backend-python.md` et module-boundaries §5.2) et **Q-104 d** (dépendances HTTP d'`access_control`) : à trancher au Jour 9 ;
- modèle de données du Jour 3 (réserve sur le Trade, sans effet au Jour 9), questions de comptes et d'organisations ouvertes (Q-09, Q-10, Q-12, Q-74, Q-87, Q-89, Q-90) ;
- seuil de couverture (Q-104 a) : à confirmer avant le Jour 9.

**Le Jour 9 ne sera pas lancé sans ta validation explicite.**
