# MadaSource — Roadmap backend FastAPI avec Claude Code

**Départ :** dépôt vide · **Durée indicative :** 35 jours ouvrés · **Cadence :** 8–9 h/jour  
**Périmètre :** backend uniquement. Le frontend sera développé après validation de l'API.  
**Stack :** Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.x async, Pydantic v2, Alembic, Redis, Celery si nécessaire, Pytest, Ruff, Docker Compose.

> Le nombre de jours est indicatif. Ne passe pas au jour suivant si les critères de sortie ne sont pas atteints. Prévois du temps supplémentaire pour les corrections, les retours du client et la stabilisation.

---

# 1. Prompt permanent à donner à Claude Code

Copie ce prompt au début de chaque session, puis colle le prompt du jour.

Tu travailles sur **MadaSource**, une plateforme B2B de facilitation du commerce international, démarrée depuis un dépôt vide. Tu développes uniquement le backend. Le frontend sera créé plus tard et consommera l'API REST.

## Périmètre V1
- Produits : Vanilla, Cloves, Cocoa.
- Acteurs : Buyer, Exporter, MadaSource Admin.
- Parcours : Marketplace → RFQ → Matching → Quotation → Negotiation → Trade → Documents → Payment Record → Shipment → Delivery → Completion.
- Les paiements sont enregistrés dans la plateforme ; aucune intégration bancaire réelle n'est supposée en V1.
- Les intégrations avancées, l'assistant IA, l'intelligence commerciale et les intégrations externes restent hors périmètre tant qu'elles ne sont pas explicitement demandées.

## Stack obligatoire
- Python 3.12+
- FastAPI, Pydantic v2
- PostgreSQL, SQLAlchemy 2.x async, Alembic
- Redis/Celery uniquement pour les tâches asynchrones justifiées
- Pytest, Ruff, outil de vérification de types documenté
- Docker + Docker Compose
- REST versionnée sous `/api/v1`, OpenAPI/Swagger

## Principes d'architecture
- Utilise un **monolithe modulaire**, pas des microservices.
- Sépare routes, schémas, modèles, services métier, accès aux données et permissions.
- Les routes HTTP ne contiennent pas de logique métier complexe.
- Évite les imports circulaires et les dépendances entre modules non documentées.
- Toutes les transitions métier importantes sont validées côté serveur.
- Utilise des transactions DB pour les opérations multi-étapes et assure l'idempotence des actions critiques.
- Utilise UUID pour les identifiants techniques sauf justification documentée.
- Les dates sont timezone-aware et stockées en UTC.
- Les montants utilisent Decimal/Numeric, jamais float.
- Les statuts sont contraints et leurs transitions documentées.
- N'ajoute pas de dépendance sans expliquer son utilité.
- Ne développe aucun frontend.

## Sécurité et règles métier
- Vérifie les permissions côté serveur sur chaque endpoint privé.
- Isole les données par organisation et vérifie l'accès à chaque ressource.
- Sépare les schémas publics des schémas privés/admin.
- Ne révèle jamais mots de passe hashés, tokens, données bancaires privées, documents confidentiels ou marges internes.
- Ne stocke jamais les mots de passe en clair ; n'invente pas de cryptographie.
- Les actions sensibles sont auditées.
- L'historique de négociation et les événements de Trade ne doivent pas être effacés par le workflow normal.
- Le matching doit être déterministe, explicable et basé sur les données disponibles ; aucun score aléatoire ni fournisseur inventé.
- Une quotation expirée ne doit pas être présentée comme valide.
- Les prix historiques d'une transaction ne changent pas quand les taux de change changent.
- Ne simule jamais un paiement, une certification ou un tracking réel sans le signaler explicitement comme DEMO.
- MadaSource n'est pas une banque. La V1 enregistre les paiements et justificatifs sans traitement bancaire.
- Les décisions métier absentes du cahier des charges doivent être marquées `À VALIDER`, pas inventées.

## Méthode obligatoire à chaque tâche
1. Inspecte le dépôt et la documentation avant de modifier.
2. Résume le plan et les fichiers concernés.
3. Signale les ambiguïtés bloquantes.
4. Implémente uniquement le périmètre du jour.
5. Ajoute les tests unitaires, d'intégration ou API appropriés.
6. Exécute lint, vérification de types, tests et migrations applicables.
7. Corrige les échecs ; ne masque pas les erreurs en désactivant les contrôles.
8. Mets à jour README, documentation et `.env.example`.
9. Vérifie qu'aucun secret n'est ajouté à Git.
10. Termine par un rapport factuel : changements, fichiers, commandes réellement exécutées, résultats, limites et décisions à valider.

Ne prétends jamais qu'un test a réussi s'il n'a pas été exécuté. Ne passe pas au jour suivant si le jour courant est instable.

---

# 2. Structure cible du backend

```text
madasource/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── common/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── organizations/
│   │   │   ├── access_control/
│   │   │   ├── buyers/
│   │   │   ├── exporters/
│   │   │   ├── verification/
│   │   │   ├── products/
│   │   │   ├── marketplace/
│   │   │   ├── rfqs/
│   │   │   ├── matching/
│   │   │   ├── quotations/
│   │   │   ├── negotiations/
│   │   │   ├── trades/
│   │   │   ├── documents/
│   │   │   ├── messages/
│   │   │   ├── notifications/
│   │   │   ├── samples/
│   │   │   ├── payment_records/
│   │   │   ├── shipments/
│   │   │   ├── reviews/
│   │   │   ├── exceptions/
│   │   │   ├── audit/
│   │   │   └── admin/
│   │   └── tasks/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   ├── alembic/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── README.md
├── infrastructure/
├── docs/backend/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Un module commencé peut contenir `models.py`, `schemas.py`, `router.py`, `service.py`, `repository.py` si utile, `permissions.py` et ses tests. **Ne crée pas des fichiers vides pour tous les modules futurs.**

---

# 3. Prompts complets par jour

## Jour 1 — Analyse fonctionnelle backend

Tu démarres MadaSource depuis un dépôt vide. Aujourd'hui, ne code pas l'application. Analyse le cahier des charges et crée :
- `docs/backend/requirements.md`
- `docs/backend/v1-scope.md`
- `docs/backend/actors-and-permissions.md`
- `docs/backend/business-rules.md`
- `docs/backend/workflows.md`
- `docs/backend/domain-glossary.md`
- `docs/backend/risks-and-open-questions.md`

Documente les acteurs, modules, entités, relations, statuts, transitions RFQ/Quotation/Negotiation/Trade, règles de confidentialité, prix, matching, expiration et audit. Sépare explicitement V1, fonctionnalités futures et intégrations externes. Marque `À VALIDER` pour toute décision non définie ; n'invente pas de règles. Termine par une liste de risques et une matrice de périmètre.

**Sortie attendue :** spécification exploitable sans code métier.

## Jour 2 — Architecture modulaire et conventions API

À partir du Jour 1, définis l'architecture backend FastAPI. Crée :
- `docs/backend/architecture.md`
- `docs/backend/module-boundaries.md`
- `docs/backend/api-conventions.md`
- `docs/backend/error-handling.md`
- `docs/backend/testing-strategy.md`
- `docs/backend/security-design.md`

Définis la responsabilité de chaque module, les dépendances permises, la convention `/api/v1`, pagination, filtres, erreurs, logs, dates, devises, UUID, tests et gestion des transactions. Explique comment les modules communiquent sans imports circulaires. Ne code pas encore les fonctionnalités métier. Marque les décisions à confirmer.

## Jour 3 — Modèle de données et ERD

Conçois le modèle de données, sans encore implémenter tous les modèles Python. Crée :
- `docs/backend/data-model.md`
- `docs/backend/erd.mmd`
- `docs/backend/data-classification.md`
- `docs/backend/indexes-and-constraints.md`

Étudie les entités nécessaires : Organization, User, Role, Permission, OrganizationMembership, BuyerProfile, ExporterProfile, Product, ProductCategory, ProductAttribute, Certification, VerificationRecord, RFQ, RFQMatch, Quotation, QuotationLine, Negotiation, NegotiationOffer, Trade, TradeEvent, DocumentMetadata, PaymentRecord, Shipment, Notification, Conversation/Message, SampleRequest, Review, Exception/Dispute, AuditLog. Définis cardinalités, contraintes, indexes, statuts, champs sensibles et relations. Évite les tables inutiles à la V1. Montants en Decimal/Numeric et prix transactionnels figés.

## Jour 4 — Initialisation du dépôt

Initialise le repository depuis le dépôt vide. Crée le squelette `backend/app`, `backend/tests`, `backend/alembic`, `docs/backend`, `.gitignore`, `.env.example`, `README.md`, `backend/pyproject.toml`, `backend/Dockerfile` et `docker-compose.yml`.

Configure Python 3.12+, FastAPI, SQLAlchemy 2.x async, Pydantic v2, Alembic, PostgreSQL, Pytest et Ruff avec versions compatibles épinglées. Docker Compose doit démarrer le backend et PostgreSQL avec healthchecks et volume persistant. Ajoute un endpoint health minimal et un test smoke. Ne développe aucun workflow métier. Vérifie les commandes d'installation et de démarrage depuis un environnement propre.

## Jour 5 — Base FastAPI et gestion des erreurs

Implémente la fondation de l'application : configuration validée par environnement, application factory, router `/api/v1`, `/health/live`, `/health/ready`, gestion centralisée des erreurs, format de réponse d'erreur cohérent, logs structurés sans secrets, OpenAPI, CORS configurable, gestion propre du cycle de vie et dépendance de session DB.

Ne mets pas de logique métier dans `main.py`. Le readiness check doit vérifier la disponibilité de la base. Ajoute les tests API et documente comment démarrer le service. Exécute Ruff, vérification de types et Pytest.

## Jour 6 — PostgreSQL, SQLAlchemy et Alembic

Finalise SQLAlchemy 2.x async, la base déclarative, session factory, gestion de session, configuration Alembic et découverte des modèles. Configure une base de test isolée. Ajoute seulement les migrations réellement nécessaires à cette étape.

Vérifie migration vers la tête, rollback en cas d'exception, fermeture des sessions, erreurs de connexion et commandes Alembic. Documente `upgrade`, création de migration et downgrade prudent. Ne crée pas prématurément toutes les tables métier.

## Jour 7 — Qualité et intégration continue

Configure commandes reproductibles pour Ruff lint/format, vérification de types, Pytest unitaire/intégration, vérification des migrations et build Docker. Ajoute GitHub Actions sur push et pull request. Les tests utilisent une base isolée, jamais la production. Documente les commandes. N'ignore pas des règles ou tests uniquement pour rendre la CI verte.

## Jour 8 — Primitives de sécurité

Implémente les primitives transversales : hash de mot de passe avec bibliothèque maintenue, utilitaires de sécurité nécessaires, configuration des secrets, validation d'entrées, protection des logs, réponses HTTP sûres et stratégie de rate limiting. Ne crée pas de cryptographie maison. Ne stocke aucun secret réel dans le dépôt. Ajoute tests et `docs/backend/security-design.md` mis à jour. L'authentification complète viendra au Jour 10.

## Jour 9 — Organizations et RBAC

Implémente les modèles, schémas, services, migrations et tests pour Organization, User, Role, Permission et OrganizationMembership. Rôles actifs V1 : Buyer, Exporter, MadaSource Admin. Prépare l'extension future sans activer inutilement les rôles futurs.

Définis comment les permissions sont vérifiées côté serveur et comment chaque ressource est isolée par organisation. Évite les conditions éparpillées fondées seulement sur `is_admin`. Ajoute des tests d'accès autorisé et interdit, y compris entre deux organisations.

## Jour 10 — Authentification et sessions

Implémente inscription, login, refresh, logout/révocation, endpoint utilisateur courant et changement/réinitialisation de mot de passe selon les règles validées. Documente durée de vie et rotation des tokens. Ne journalise jamais les tokens. Les erreurs de login ne doivent pas divulguer inutilement si un compte existe.

Prévois un adaptateur d'email, sans prétendre envoyer de vrais emails si aucun fournisseur n'est configuré. Crée un processus sûr pour le premier admin ; ne laisse pas de route publique de bootstrap. Teste token expiré/invalide/révoqué, mot de passe incorrect, compte suspendu et permissions.

## Jour 11 — Vérification d'email et statuts de comptes

Implémente la vérification d'email avec jeton à usage unique, expiration et révocation/réutilisation interdite. Prévois un service d'envoi abstrait et un mode local clairement identifié. Définis les statuts de compte et les accès autorisés pour Buyer/Exporter. Ajoute tests et documentation de configuration. Ne prétends pas qu'un email a été envoyé si le service ne l'a pas envoyé.

## Jour 12 — Audit logging

Crée un module d'audit réutilisable. Enregistre acteur, action, ressource, ID, date UTC, résultat et métadonnées non sensibles. Couvre les changements sensibles de comptes, rôles, vérifications, produits, RFQ, offres, négociations, trades, documents, paiements, expéditions et administration.

Les événements d'audit ne doivent pas être modifiables via les endpoints ordinaires. Ne stocke jamais les mots de passe, tokens ou le contenu intégral de documents privés. Ajoute tests et une convention pour les futurs modules.

## Jour 13 — Buyer profile

Implémente le profil Buyer : entreprise, pays, région, type d'activité, site web, contact, email, téléphone, adresse, marchés d'importation et produits d'intérêt. Statuts : Pending, Active, Suspended, Blocked.

Crée modèles, schémas, services, routes, permissions, migration et tests. Un Buyer ne peut modifier que son propre profil/organisation selon les permissions. L'admin peut gérer les profils autorisés. Ne retourne que les champs autorisés.

## Jour 14 — Exporter onboarding et profil

Implémente l'onboarding Exporter : société, contact, email, téléphone, adresse, région, immatriculation, informations fiscales, documents export, expérience, produits, capacité, certifications et informations bancaires/de paiement si nécessaires.

Sépare clairement schémas publics, privés et admin. Les données bancaires et documents sensibles ne doivent jamais apparaître dans les endpoints publics. Ajoute les tests de non-exposition et marque `À VALIDER` pour les règles non définies.

## Jour 15 — Vérification Exporter

Implémente les niveaux Profile Verified, Business Verified, Export Verified et MadaSource Premium Verified. Statuts : Pending, Verified, Rejected, Expired, Suspended. Conserve niveau, dates, expiration si applicable, documents examinés, administrateur responsable et notes.

Seuls les utilisateurs autorisés peuvent prendre une décision de vérification. Une inscription ne rend jamais automatiquement l'exportateur vérifié. Ajoute routes admin, permissions, audit, tests de transition et documentation.

## Jour 16 — Catégories et catalogue produits

Implémente les catégories Vanilla, Cloves et Cocoa et le catalogue. Prévois des attributs variables par catégorie, car les caractéristiques de qualité ne sont pas identiques pour chaque produit.

Couvre nom, catégorie, description, origine/région, spécifications, images/références de documents, quantité, unité, MOQ, indication de prix, devise, Incoterm, conditions de paiement, validité, grade, qualité, humidité, taille, pureté, traitement et certifications selon pertinence. N'impose pas tous les attributs à tous les produits. Montants Decimal, unités explicites. Ajoute migration et tests.

## Jour 17 — CRUD produit et permissions

Termine les endpoints de création, lecture, modification, publication/dépublication, archivage logique, pagination, recherche et filtres des produits. Un exportateur ne peut gérer que les produits de son organisation. Les modifications importantes sont auditées.

Évite la suppression physique d'un produit lié à une RFQ ou transaction ; définis une stratégie cohérente. Ajoute tests de permissions, validation, filtres et contraintes d'intégrité.

## Jour 18 — Marketplace public et Digital Exporter Passport

Implémente les endpoints publics de recherche marketplace et les profils publics Exporter. Filtres : catégorie, origine, qualité, grade, certification, quantité, MOQ, emballage, Incoterm, exportateur, statut de vérification et indication de prix. Ajoute URL publique stable et QR code vers le profil public.

Les réponses publiques ne doivent jamais exposer coordonnées confidentielles, informations bancaires, documents internes, notes internes ou marges. Les filtres doivent utiliser les données réelles. Ajoute pagination, indexes utiles et tests de non-exposition.

## Jour 19 — Modèle et règles RFQ

Implémente le modèle RFQ avec produit, quantité/unité, qualité, grade, certification, emballage, pays/port de destination, Incoterm, date de livraison cible, prix cible facultatif, préférence de paiement et exigences supplémentaires.

Statuts prévus : Draft → Submitted → Matching → Sent to Exporters → Quotations Received → Negotiating → Accepted → Closed. Crée un service de transition qui refuse les changements invalides. Documente les champs obligatoires et marque les règles absentes `À VALIDER`. Ajoute tests unitaires de transitions.

## Jour 20 — RFQ API Buyer

Crée les endpoints Buyer pour créer un brouillon, consulter, modifier avant soumission, soumettre et lister les RFQ. Vérifie l'organisation propriétaire à chaque accès. Ajoute pagination, filtres, validation, audit et tests.

Une RFQ soumise ne doit pas pouvoir être modifiée librement si cela invalide les matches ou quotations. Si les règles de modification après soumission ne sont pas définies, documente une proposition et demande validation au lieu de l'inventer.

## Jour 21 — RFQ Inbox Exporter

Implémente l'inbox Exporter et les actions Respond, Decline, Ask Question. L'exportateur ne peut voir que les RFQ qui lui ont été adressées ou auxquelles il est autorisé à répondre. Conserve les réponses et questions. Ajoute RBAC, audit, pagination et tests d'accès croisé entre organisations. Aucun email réel sans fournisseur configuré.

## Jour 22 — Matching déterministe

Crée un service matching indépendant de HTTP. Critères selon données disponibles : compatibilité produit, capacité/quantité, qualité/grade, certifications requises, destination, Incoterm, MOQ et statut de vérification.

Les règles et pondérations doivent être documentées et configurables. Le résultat doit être reproductible et explicable. Aucun score aléatoire, fournisseur inventé ou certification supposée. Les données manquantes doivent être traitées explicitement. Ajoute tests unitaires pour matches parfaits, partiels, impossibles et données manquantes.

## Jour 23 — Workflow matching

Relie le matching à la soumission RFQ. Le traitement doit être contrôlé, idempotent et ne pas créer de doublons incohérents. Enregistre les critères utilisés, résultats, raisons et date d'exécution. Ajoute les endpoints de consultation et de contrôle admin avec audit. Teste les erreurs, répétitions et accès. N'implémente pas d'IA.

## Jour 24 — Quotation et modèle commercial

Implémente Quotation en distinguant Supplier Cost, External Costs, MadaSource Margin et Final Buyer Price. Supporte les deux modèles : revendeur/trader et intermédiaire/commission. Les formules doivent être configurables ; ne hardcode pas une marge ou des taxes non validées.

Support initial FOB, CFR et CIF. Utilise Decimal, devise, unité et conditions explicites. Les schémas Buyer ne doivent jamais révéler coûts fournisseurs confidentiels ni marges internes. Ajoute tests de calcul et de confidentialité.

## Jour 25 — Validité et comparaison des quotations

Conserve dates de création/modification/expiration, source, statut, devise, unité, destination et Incoterm. Une quotation expirée ne peut pas être acceptée comme valide sans règle explicite et action auditée.

Prépare les données nécessaires à la comparaison : prix final, quantité, qualité, grade, certification, Incoterm, délai et validité. N'expose pas les marges internes. Ajoute tests d'expiration, fuseaux horaires, autorisations et historique des offres acceptées.

## Jour 26 — Négociations et contre-offres

Implémente les propositions Buyer/Exporter, contre-offres, acceptation, refus, expiration et historique. Chaque offre conserve auteur, date, valeurs commerciales et statut. L'historique n'est pas supprimable via le workflow normal.

Valide qui peut agir selon l'état. Gère les appels concurrents pour empêcher l'acceptation simultanée de propositions incompatibles. Utilise transaction/contrôle de concurrence si nécessaire. Ajoute tests transitions, accès, concurrence et audit.

## Jour 27 — Acceptation et création Trade

À l'acceptation valide d'une quotation, crée un Trade lié au Buyer, Exporter, RFQ, quotation et historique de négociation. Génère un ID unique lisible de type `MST-2026-000145` sans coder l'exemple en dur. Assure unicité et idempotence même si plusieurs requêtes arrivent simultanément.

Fige les termes commerciaux acceptés et réalise la création dans une transaction DB. Un double appel ne doit pas créer deux Trades. Ajoute tests de concurrence, rollback et traçabilité.

## Jour 28 — Trade state machine et timeline

Implémente les statuts : Trade Confirmed, Payment Pending, Payment Confirmed, Preparation, Ready for Shipment, Shipped, In Transit, Delivered, Completed ; exceptions : Cancelled, Disputed, On Hold.

Chaque transition est validée par un service métier. Crée des TradeEvent avec timestamp UTC, acteur, événement, ancien/nouveau statut et métadonnées non sensibles. L'historique est immuable via les opérations normales. Ajoute tests de toutes les transitions permises/interdites.

## Jour 29 — Document Vault et stockage

Implémente métadonnées et upload de documents liés à Organization, RFQ, Quotation, Trade ou Shipment. Couvre catégorie, nom, type MIME, taille, clé de stockage, auteur, date, visibilité et relation métier.

Abstrais le stockage pour pouvoir utiliser un stockage local en développement et S3-compatible en production. Les téléchargements privés nécessitent une autorisation serveur ou une URL signée à durée limitée. Valide type et taille, ne fais pas confiance au nom du fichier et ne stocke pas les binaires dans PostgreSQL. Ajoute tests d'accès interdit.

## Jour 30 — Messagerie interne

Implémente les conversations Buyer ↔ Exporter associées à RFQ, quotation, négociation, Trade ou sample request. Conserve auteur, message et horodatage. Les pièces jointes passent par Document Vault.

Seuls les participants autorisés peuvent lire/écrire ; évite les accès croisés entre organisations. Ajoute pagination, validation, audit pertinent et tests. N'ajoute pas de WebSocket si REST suffit à la V1 ; documente cette limite.

## Jour 31 — Notifications et tâches asynchrones

Implémente notifications in-app pour nouveau RFQ, nouvelle quotation, contre-offre, acceptation, création Trade, paiement confirmé, document ajouté, changement d'état Trade et échantillon expédié.

Utilise Redis/Celery uniquement si nécessaire. La stratégie de retry doit éviter les doublons ; documente les erreurs et tâches échouées. L'envoi email est abstrait/configurable. Ne prétends pas qu'une notification externe a été envoyée sans confirmation du fournisseur.

## Jour 32 — Demandes d'échantillons

Si le périmètre V1 validé inclut ce module, implémente Sample Request : Request Sample → Sample Quotation → Sample Confirmed → Sample Payment → Sample Shipped → Sample Received → Sample Approved/Rejected.

Relie la demande à Buyer, Exporter, produit et RFQ éventuel. Contrôle les transitions, permissions et audit. Marque `À VALIDER` pour les règles inconnues. Si le module est reporté, documente-le et laisse-le désactivé plutôt que de simuler son fonctionnement.

## Jour 33 — Payment Records

Implémente la gestion d'enregistrement de paiement, sans passerelle bancaire. Statuts : Pending, Processing, Confirmed, Failed, Refunded. Champs : référence, justificatif, date, montant, devise, statut, confirmation admin et Trade associé.

Le justificatif utilise Document Vault. Un fichier téléchargé ne vaut pas confirmation automatique. Les actions de confirmation/remboursement sont autorisées et auditées. Montants Decimal. Ajoute tests de permissions, transitions et cohérence du Trade.

## Jour 34 — Shipments et clôture

Implémente les shipments manuels : méthode, transporteur, référence, numéro de conteneur, tracking number, origine, destination, départ/arrivée estimés. Statuts : Pending, Ready for Shipment, Shipped, In Transit, Arrived, Delivered.

Relie shipment au Trade et conserve l'historique. N'invente pas de suivi automatique. Définis les conditions de clôture Trade selon les règles validées ; marque les inconnues `À VALIDER`. Ajoute tests du workflow jusqu'à livraison et completion.

## Jour 35 — Reviews, litiges et API Admin

Implémente les endpoints V1 pour reviews/performance basées sur données réelles, exceptions/disputes liées à Trade et administration des Buyers, Exporters, Products, RFQs, Matches, Quotations, Negotiations, Trades, Documents, Payment Records, Shipments, Verification, Messages, Reviews et Audit Logs.

Seul l'Admin autorisé peut exécuter les actions d'administration. Les notes internes restent privées. Aucune review fabriquée. Ajoute RBAC, audit, pagination et tests. Si une fonctionnalité est trop risquée pour être incluse, marque-la explicitement non livrée au lieu de créer un faux endpoint fonctionnel.

---

# 4. Audits obligatoires après le développement

## Audit A — Parcours E2E complet

Audite le backend et teste avec des données de test clairement identifiées :
Buyer → Exporter → produit Vanilla → recherche marketplace → RFQ → matching → réponse Exporter → quotation → comparaison → négociation → acceptation → Trade ID → document privé → Payment Record → Shipment → In Transit → Delivered → Completed.

Répète les tests principaux pour Cloves et Cocoa. Corrige les défauts. Fournis un rapport des tests réellement exécutés et de leurs résultats. Ne prétends jamais qu'un test est passé sans l'avoir lancé.

## Audit B — Sécurité et isolation multi-organisation

Teste accès horizontal entre organisations, escalade de privilèges, endpoints admin, fuite des marges, données privées, documents non autorisés, tokens expirés/révoqués, rate limiting, validation fichiers, secrets/logs, transitions invalides et concurrence d'acceptation/Trade ID.

Ajoute un test de régression pour chaque vulnérabilité. Pour chaque problème, documente gravité, preuve, correction et risque résiduel.

## Audit C — Performance et robustesse

Vérifie pagination, indexes, requêtes N+1, taille des requêtes/fichiers, timeouts, connexions DB, tâches répétées, retries, transactions et gestion d'erreurs. Aucun test agressif sur la production. Si nécessaire, propose un test de charge local avec données synthétiques et rapporte seulement les résultats mesurés.

## Audit D — Documentation de livraison

Finalise README racine et backend, installation, variables d'environnement, commandes Docker, migrations, création sécurisée du premier admin, tests, architecture, OpenAPI, sauvegarde/restauration DB, stockage de fichiers, déploiement et checklist sécurité. Vérifie qu'aucun secret réel n'est dans `.env.example`. Teste le démarrage depuis un environnement propre en suivant la documentation. Liste les limites et fonctionnalités non implémentées.

---

# 5. Prompt quotidien de contrôle

Au début de chaque session, remplace `JOUR_N` :

> Aujourd'hui, nous exécutons le Jour JOUR_N de `docs/backend/roadmap-backend-fastapi.md`. Lis les règles permanentes, l'architecture, les décisions déjà documentées et l'état Git. Ne recommence pas le projet et ne remplace pas du code existant sans raison. Présente un plan court, implémente uniquement le périmètre du jour, ajoute les tests, exécute les vérifications et mets à jour la documentation. Si une dépendance d'un jour précédent échoue, corrige-la d'abord. Termine par un rapport factuel : fichiers modifiés, commandes exécutées, tests réussis/échoués, décisions à valider et critères de sortie. Ne prétends jamais avoir exécuté une commande ou un test si ce n'est pas le cas.

## Un jour est terminé seulement si
- le périmètre est implémenté et cohérent ;
- les tests appropriés existent et leur résultat est connu ;
- migrations et contraintes sont cohérentes ;
- documentation et `.env.example` sont à jour ;
- aucun secret n'a été ajouté au dépôt ;
- les défauts critiques sont corrigés ou explicitement signalés ;
- les décisions métier non définies sont marquées `À VALIDER`.

---

# 6. Décisions à valider avec le client

Le cahier des charges ne définit pas nécessairement toutes les règles contractuelles. Valide avant production :
- modèle revendeur/trader ou intermédiaire/commission et formules de prix ;
- règles de modification/expiration RFQ et quotation ;
- conditions d'acceptation et de clôture d'un Trade ;
- politique de vérification des exportateurs ;
- accès et conservation des documents ;
- annulations et litiges ;
- conservation et suppression des données ;
- responsabilités juridiques, fiscales, bancaires, logistiques et d'assurance.

Les intégrations futures peuvent être préparées par abstraction, mais ne doivent pas être présentées comme actives avant implémentation et validation.
