# MadaSource — ROADMAP DE DÉVELOPPEMENT AVEC CLAUDE CODE

Version : 1.0
Point de départ : projet vide
Cadence : 8–9 h/jour
Durée indicative : 50 jours ouvrés
Approche : Modular Monolith + API-first

## 0. Stack de référence

- Backend : Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic
- Base de données : PostgreSQL
- Cache / jobs : Redis + Celery
- Frontend : Next.js, TypeScript, Tailwind CSS, shadcn/ui
- Data fetching : TanStack Query
- Forms : React Hook Form + Zod
- Stockage fichiers : S3-compatible
- Auth : JWT + refresh tokens, RBAC
- Tests : Pytest, Vitest, Playwright
- Dev : Docker Compose
- CI/CD : GitHub Actions
- Reverse proxy : Nginx ou Caddy
- Monitoring : logs structurés + Sentry-ready
- API : REST + OpenAPI

## 1. Règles permanentes à donner à Claude

Ces règles s'appliquent à TOUS les jours.

- Le dépôt est initialement vide.
- Lire les fichiers existants avant toute modification.
- Ne jamais supposer qu'une fonctionnalité existe.
- Ne jamais supprimer ou réécrire une fonctionnalité fonctionnelle sans justification.
- Ne jamais inventer de données métier.
- Respecter le cahier des charges MadaSource comme source fonctionnelle principale.
- Ne pas construire toutes les fonctionnalités futures dans la V1.
- Architecture modulaire, API-first, RBAC, feature flags et intégration future.
- Préférer un monolithe modulaire à des microservices prématurés.
- Code lisible, maintenable et compréhensible.
- Chaque module doit avoir ses responsabilités clairement séparées.
- Ne pas mettre la logique métier critique dans les routes HTTP.
- Toutes les transitions métier importantes doivent être validées côté backend.
- Toutes les opérations sensibles doivent être auditables.
- Les données privées ne doivent jamais être exposées par les endpoints publics.
- Les marges commerciales internes ne doivent jamais être exposées au buyer/exporter.
- Les prix historiques d'une transaction ne doivent pas changer à cause d'un changement de taux de change.
- Les scores de matching doivent être déterministes et basés sur des données réelles/configurables.
- Les quotations expirées ne doivent jamais être présentées comme actuelles.
- Les négociations doivent conserver leur historique.
- Les Trade ID doivent être uniques et centraux.
- Toute fonctionnalité doit avoir des tests adaptés.
- Après chaque tâche : lint/type-check/tests/migrations vérifiés selon le périmètre.
- Ne pas continuer vers le jour suivant si le jour courant est instable.
- Mettre à jour la documentation technique au fur et à mesure.
- Ne jamais intégrer une vraie banque, un vrai paiement ou une vraie logistique sans autorisation explicite.
- Les intégrations futures doivent passer par une couche d'intégration.
- Le DEMO MODE doit être explicitement identifié et ne doit jamais mélanger données simulées et réelles.

## 2. Architecture métier cible

Organisation
→ Users
→ Roles
→ Permissions

Buyer
→ RFQ
→ Matches
→ Quotations
→ Negotiations
→ Trade

Exporter
→ Company Profile
→ Verification
→ Products
→ RFQ responses
→ Quotations
→ Trade

Trade
→ Documents
→ Payment Record
→ Shipment
→ Timeline
→ Completion

Produits V1 :
- Vanilla
- Cloves
- Cocoa

Utilisateurs cœur V1 :
- International Buyer
- Malagasy Exporter

Administration :
- MadaSource Admin

## 3. Phase 0 — Analyse et architecture

### Jour 1 — Analyse complète du projet

PROMPT CLAUDE CODE :

> Tu démarres le projet MadaSource depuis un dépôt totalement vide.
>
> Ne code pas encore.
>
> Analyse le cahier des charges MadaSource fourni au projet et transforme-le en spécification technique exploitable.
>
> Objectifs :
> 1. Identifier tous les modules fonctionnels.
> 2. Identifier les acteurs et leurs permissions.
> 3. Identifier les workflows et états.
> 4. Identifier les entités métier.
> 5. Identifier les relations entre entités.
> 6. Identifier les données publiques et privées.
> 7. Identifier les règles métier critiques.
> 8. Identifier les fonctionnalités V1 et les fonctionnalités futures.
> 9. Identifier les feature flags nécessaires.
> 10. Identifier les risques techniques et métier.
>
> Crée uniquement de la documentation :
> - docs/requirements.md
> - docs/roles-permissions.md
> - docs/workflows.md
> - docs/business-rules.md
> - docs/domain-map.md
> - docs/v1-scope.md
> - docs/future-scope.md
>
> Ne crée aucune application fonctionnelle aujourd'hui.
>
> À la fin, vérifie que le périmètre V1 reste :
> Vanilla + Cloves + Cocoa
> Buyer + Exporter + Admin
> Marketplace → RFQ → Matching → Quotation → Negotiation → Trade → Documents → Payment Record → Shipment → Delivery → Completion.

Livrable :
- documentation fonctionnelle initiale.

### Jour 2 — Architecture technique

PROMPT :

> À partir de la documentation du Jour 1, définis l'architecture technique complète de MadaSource.
>
> Utilise :
> Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, Redis, Celery, Next.js, TypeScript, Tailwind, shadcn/ui, TanStack Query, Docker Compose.
>
> Architecture : Modular Monolith + API-first.
>
> Produis :
> - docs/architecture.md
> - docs/backend-architecture.md
> - docs/frontend-architecture.md
> - docs/database-architecture.md
> - docs/api-architecture.md
> - docs/security-architecture.md
> - docs/file-storage.md
> - docs/integration-architecture.md
> - docs/testing-strategy.md
> - docs/deployment-architecture.md
>
> Définis les frontières exactes de chaque module.
> Ne code pas encore l'application.

### Jour 3 — Modèle de données

PROMPT :

> Conçois le modèle de données PostgreSQL complet pour la V1.
>
> Utilise SQLAlchemy 2.x et Alembic.
>
> Définis les entités, clés, contraintes, index, relations, statuts, timestamps, auditabilité et règles d'intégrité.
>
> Le modèle doit couvrir au minimum :
> Organization, User, Role, Permission, Membership, Buyer Profile, Exporter Profile, Product, Product Category, Product Attribute, Certification, RFQ, RFQ Match, Quote, Quote Item, Negotiation, Negotiation Offer, Trade, Trade Event, Document, Payment Record, Shipment, Notification, Message, Review, Verification, Audit Log.
>
> Prévois l'extensibilité sans ajouter des tables inutiles pour les phases futures.
>
> Produis un ERD/documentation avant de coder.

## 4. Phase 1 — Fondation technique

### Jour 4 — Initialisation repository

PROMPT :

> Implémente la fondation du projet à partir de l'architecture validée.
>
> Crée :
> backend/
> frontend/
> infrastructure/
> docs/
> tests/
>
> Configure Git, .gitignore, README, Docker Compose et variables d'environnement.
>
> Ne développe encore aucun workflow métier.
>
> Le projet doit démarrer proprement avec Docker.

### Jour 5 — Backend foundation

PROMPT :

> Implémente la base FastAPI.
>
> Configure :
> - application factory
> - configuration settings
> - PostgreSQL
> - SQLAlchemy async
> - Alembic
> - exception handling
> - logging
> - health endpoint
> - OpenAPI
> - structure modulaire
>
> Ajoute les premiers tests.
>
> Vérifie que migration + démarrage + tests fonctionnent.

### Jour 6 — Frontend foundation

PROMPT :

> Implémente la base Next.js + TypeScript.
>
> Configure :
> - routing
> - Tailwind
> - shadcn/ui
> - layout global
> - responsive design
> - API client
> - TanStack Query
> - gestion des erreurs
> - loading states
> - architecture features
>
> Crée seulement le shell de l'application, pas les écrans métier complets.

### Jour 7 — CI/CD et qualité

PROMPT :

> Configure la qualité du projet.
>
> Ajouter :
> - lint backend
> - format backend
> - type checking
> - tests backend
> - lint frontend
> - type checking frontend
> - tests frontend
> - GitHub Actions
> - Docker build checks
>
> Aucun merge ne doit être considéré valide si les checks échouent.

### Jour 8 — Authentification

PROMPT :

> Implémente l'authentification sécurisée.
>
> Fonctionnalités :
> - inscription
> - connexion
> - logout
> - access token
> - refresh token
> - password hashing
> - password reset architecture
> - email verification architecture
> - session/security controls
>
> Écris les tests de sécurité essentiels.
>
> Ne donne encore aucun accès métier sans RBAC.

### Jour 9 — Organizations / RBAC

PROMPT :

> Implémente Organization, User, Membership, Role et Permission.
>
> Crée un RBAC extensible.
>
> Rôles V1 :
> - Buyer
> - Exporter
> - MadaSource Admin
>
> Prépare sans activer :
> - Operations
> - Compliance
> - Finance
> - Logistics
> - Super Admin
> - Partner
>
> Les permissions doivent être vérifiées côté backend.

### Jour 10 — Audit / sécurité

PROMPT :

> Implémente l'audit logging.
>
> Journaliser les opérations sensibles :
> comptes, vérifications, produits, RFQ, quotations, négociations, trades, documents, paiements, shipments, changements de statut et administration.
>
> L'audit doit être append-only côté application.
>
> Ajoute rate limiting, validation d'entrée et protections de base.
>
> Teste les permissions et accès interdits.

## 5. Phase 2 — Utilisateurs et marketplace

### Jour 11 — Buyer profile

PROMPT :

> Implémente le profil Buyer selon le cahier des charges.
>
> Crée API + modèles + validations + frontend.
>
> Respecte les champs :
> company, country, region, business type, website, contact, email, phone, address, import markets, products of interest.
>
> Statuts : Pending, Active, Suspended, Blocked.
>
> Ajoute tests et permissions.

### Jour 12 — Exporter onboarding

PROMPT :

> Implémente l'onboarding Exporter.
>
> Champs :
> company, contact, email, phone, address, region, business registration, tax information, export documentation, experience, products, capacity, certifications, bank/payment information.
>
> Les données sensibles doivent rester privées.
>
> Prépare les documents pour le futur système de vérification.

### Jour 13 — Exporter profile / verification

PROMPT :

> Implémente le profil public/privé Exporter et le système de vérification.
>
> Niveaux :
> Level 1 Profile Verified
> Level 2 Business Verified
> Level 3 Export Verified
> Level 4 MadaSource Premium Verified
>
> Statuts :
> Pending, Verified, Rejected, Expired, Suspended.
>
> Conserve date, expiration, documents, administrateur et notes.

### Jour 14 — Products backend

PROMPT :

> Implémente le module Product.
>
> Catégories V1 :
> Vanilla, Cloves, Cocoa.
>
> Structure :
> General, Commercial, Quality.
>
> Prévoir les attributs spécifiques à chaque produit.
>
> Implémente CRUD, validation, statut, images/document references, permissions et tests.

### Jour 15 — Product frontend

PROMPT :

> Crée les interfaces Product côté Exporter et Admin.
>
> Inclure :
> liste
> recherche
> filtres
> création
> modification
> détails
> publication
> statut
> images
> documents
> informations commerciales
> informations qualité.
>
> Responsive desktop/tablet/mobile.

### Jour 16 — Marketplace

PROMPT :

> Implémente le marketplace public.
>
> Recherche et filtres :
> category, origin, quality, grade, certification, quantity, MOQ, packaging, incoterm, exporter, verification status, price indication.
>
> Sépare strictement les données publiques des données privées.

### Jour 17 — Exporter Digital Passport

PROMPT :

> Implémente le Digital Exporter Passport.
>
> Crée :
> - profil public
> - URL unique
> - QR code
> - informations vérifiées
> - produits publics
> - certifications publiques
> - niveau de vérification.
>
> Ne jamais exposer les données privées.

### Jour 18 — Public website

PROMPT :

> Construis le site public MadaSource :
> Home, About, Products, Exporters, How MadaSource Works, Buyer Registration, Exporter Registration, Request a Quote, Contact, Terms, Privacy, Legal.
>
> UX B2B internationale, responsive et professionnelle.
>
> Prépare i18n English/French.

## 6. Phase 3 — RFQ et matching

### Jour 19 — RFQ backend

PROMPT :

> Implémente RFQ.
>
> Champs :
> product, quantity, unit, quality, grade, certification, packaging, destination country, destination port, incoterm, target delivery date, target price, payment preference, additional requirements.
>
> Statuts :
> Draft → Submitted → Matching → Sent to Exporters → Quotations Received → Negotiating → Accepted → Closed.
>
> Toutes les transitions doivent être contrôlées côté backend.

### Jour 20 — RFQ frontend Buyer

PROMPT :

> Construis le workflow Buyer de création et suivi d'un RFQ.
>
> Inclure brouillon, validation, soumission, détails, statut, historique.
>
> Le formulaire doit être clair pour un acheteur international et masquer la complexité technique inutile.

### Jour 21 — RFQ inbox Exporter

PROMPT :

> Construis l'espace Exporter RFQ Inbox.
>
> Actions :
> Respond
> Decline
> Ask Question
>
> Afficher uniquement les RFQ auxquels l'exporter est autorisé à accéder.

### Jour 22 — Matching engine

PROMPT :

> Implémente le moteur de matching déterministe.
>
> Critères :
> product compatibility, quantity/capacity, quality, grade, certification, destination, incoterm, MOQ, verification status et autres données réellement disponibles.
>
> Les poids doivent être configurables.
>
> Aucun score aléatoire.
> Aucun fournisseur inventé.
> Aucun matching basé sur une information absente.

### Jour 23 — Matching UI/Admin

PROMPT :

> Construis les interfaces de matching Buyer/Admin/Exporter.
>
> Afficher les raisons du matching de manière compréhensible.
>
> Admin doit pouvoir contrôler les paramètres autorisés.
>
> Tester les cas limites et les données manquantes.

## 7. Phase 4 — Quotations

### Jour 24 — Quote backend

PROMPT :

> Implémente le moteur de quotation.
>
> Séparer :
> Supplier Cost
> External Costs
> MadaSource Margin
> Final Buyer Price.
>
> Supporter :
> FOB, CFR, CIF.
>
> Le modèle doit supporter :
> commercial reseller/trader
> intermediary/commission.
>
> Les prix internes ne doivent jamais être exposés au buyer.

### Jour 25 — Quote validity / pricing

PROMPT :

> Implémente la gestion de validité des quotations.
>
> Conserver :
> creation date
> update date
> expiry date
> source
> status
> currency
> unit
> destination
> incoterm.
>
> Une quote expirée ne doit jamais être présentée comme actuelle.
>
> Tester tous les cas d'expiration.

### Jour 26 — Quote comparison

PROMPT :

> Construis la comparaison des quotations côté Buyer.
>
> Permettre de comparer prix, quantité, qualité, grade, certification, incoterm, livraison, validité et conditions.
>
> Ne jamais exposer les marges internes de MadaSource.

### Jour 27 — Negotiation backend

PROMPT :

> Implémente la négociation.
>
> Support :
> buyer offer
> exporter counteroffer
> acceptance
> rejection
> history.
>
> Aucune proposition historique ne doit être supprimée.
>
> Toutes les actions doivent être auditées.

### Jour 28 — Negotiation frontend

PROMPT :

> Construis l'interface de négociation Buyer/Exporter.
>
> Afficher clairement :
> proposition actuelle
> historique
> contre-proposition
> statut
> expiration
> actions autorisées.
>
> Prévenir les actions impossibles selon le statut.

## 8. Phase 5 — Trade Management

### Jour 29 — Trade creation / Trade ID

PROMPT :

> Lorsqu'une quotation est acceptée, créer automatiquement un Trade.
>
> Générer un identifiant central de type :
> MST-2026-000145
>
> Le Trade doit être lié à RFQ, quotation, négociation et organisations.
>
> L'identifiant doit être unique, stable et auditable.

### Jour 30 — Trade state machine

PROMPT :

> Implémente la machine d'état Trade :
> Trade Confirmed
> Payment Pending
> Payment Confirmed
> Preparation
> Ready for Shipment
> Shipped
> In Transit
> Delivered
> Completed
>
> Exceptions :
> Cancelled
> Disputed
> On Hold.
>
> Interdire toute transition invalide.

### Jour 31 — Trade dashboard backend

PROMPT :

> Implémente le Trade Dashboard backend.
>
> Un Trade doit centraliser :
> RFQ
> quote
> negotiation
> documents
> payment
> shipment
> events
> messages
> notifications.
>
> Le Trade ID doit permettre de retrouver toute la transaction.

### Jour 32 — Trade dashboard frontend

PROMPT :

> Construis le Trade Dashboard Buyer/Exporter/Admin.
>
> UX :
> statut actuel
> timeline
> informations commerciales autorisées
> documents
> paiement
> shipment
> événements
> actions disponibles.
>
> Masquer les informations privées selon le rôle.

### Jour 33 — Timeline / events

PROMPT :

> Implémente la timeline Trade.
>
> Chaque événement doit conserver :
> type
> timestamp
> actor
> description
> status
> metadata pertinente.
>
> La timeline doit être immuable pour les événements historiques.

## 9. Phase 6 — Documents, messaging, notifications

### Jour 34 — Document management

PROMPT :

> Implémente le Document Vault.
>
> Documents liés à :
> organization, RFQ, quote, trade, shipment.
>
> Prévoir catégories, permissions, versionnement/metadata, upload sécurisé, validation type/taille et stockage S3-compatible.
>
> Les documents privés ne doivent jamais être accessibles publiquement.

### Jour 35 — Messaging

PROMPT :

> Implémente la messagerie interne Buyer ↔ Exporter.
>
> Une conversation peut être liée à RFQ, quote, negotiation, trade ou sample request.
>
> Préserver l'historique.
>
> Ajouter permissions et audit.

### Jour 36 — Notifications

PROMPT :

> Implémente le système de notifications.
>
> Événements :
> new RFQ
> new quotation
> counteroffer
> quote accepted
> new trade
> payment confirmed
> document uploaded
> trade status changed
> sample shipped.
>
> In-app en V1.
> Email/push-ready architecture pour la suite.

### Jour 37 — Sample requests

PROMPT :

> Implémente les demandes d'échantillons.
>
> Workflow :
> Request Sample
> Sample Quotation
> Sample Confirmed
> Sample Payment
> Sample Shipped
> Sample Received
> Sample Approved/Rejected.
>
> Préparer le lien avec RFQ.

## 10. Phase 7 — Verification, reviews, exceptions

### Jour 38 — Reviews / performance

PROMPT :

> Implémente les reviews et performance metrics.
>
> Ne pas créer de fausses évaluations.
> Les indicateurs doivent provenir de données réelles :
> response time, fulfillment, completed trades, etc.
>
> Respecter les permissions public/private.

### Jour 39 — Exception management

PROMPT :

> Implémente les exceptions et disputes.
>
> Un problème peut être lié à un Trade.
>
> Support :
> creation
> assignment
> status
> priority
> notes
> resolution
> audit.
>
> Prévoir Cancelled, Disputed et On Hold.

### Jour 40 — Admin console

PROMPT :

> Construis la console Admin complète V1.
>
> Modules :
> Dashboard
> Buyers
> Exporters
> Products
> RFQs
> Matching
> Quotations
> Negotiations
> Trades
> Samples
> Documents
> Payments
> Shipments
> Verification
> Messages
> Reviews
> Reports
> Settings
> Audit Logs.
>
> Les modules non implémentés doivent rester clairement désactivés, pas simulés comme fonctionnels.

## 11. Phase 8 — Payments et logistics

### Jour 41 — Payment records

PROMPT :

> Implémente Payment Management V1 sans intégration bancaire.
>
> Statuts :
> Pending, Processing, Confirmed, Failed, Refunded.
>
> Champs :
> payment reference
> voucher
> date
> amount
> currency
> admin confirmation.
>
> Ce module enregistre les paiements ; il ne transforme pas MadaSource en banque.

### Jour 42 — Shipment

PROMPT :

> Implémente la gestion manuelle des shipments.
>
> Champs :
> shipping method
> carrier
> shipment reference
> container number
> tracking number
> origin
> destination
> estimated departure
> estimated arrival.
>
> Statuts :
> Pending, Ready for Shipment, Shipped, In Transit, Arrived, Delivered.

### Jour 43 — Trade completion

PROMPT :

> Termine le workflow complet Payment → Preparation → Shipment → Delivery → Completion.
>
> Vérifie toutes les transitions.
>
> Une transaction ne doit être Completed que lorsque les conditions métier définies sont satisfaites.
>
> Ajoute les tests end-to-end.

## 12. Phase 9 — i18n, currency, UX

### Jour 44 — Internationalisation

PROMPT :

> Implémente l'architecture i18n.
>
> Langues V1 :
> English
> French
>
> Préparer Malagasy pour le futur.
>
> Aucun texte métier important ne doit être codé en dur dans les composants.

### Jour 45 — Currency

PROMPT :

> Implémente l'architecture currency.
>
> V1 :
> USD
> EUR
>
> Préparer MGA, GBP, AED, CNY.
>
> Séparer taux de change et données transactionnelles.
> Une transaction historique ne doit jamais changer parce qu'un taux FX change.

### Jour 46 — UX / responsive / accessibility

PROMPT :

> Fais un audit UX complet.
>
> Corrige :
> responsive desktop/tablet/mobile
> navigation
> loading
> empty states
> error states
> confirmation actions
> formulaires
> accessibilité
> cohérence visuelle.
>
> Ne change pas les règles métier.

## 13. Phase 10 — Tests complets et production

### Jour 47 — Tests backend complets

PROMPT :

> Fais une campagne de tests backend complète.
>
> Couvrir :
> auth
> RBAC
> organizations
> products
> marketplace
> RFQ
> matching
> quotes
> negotiation
> trade
> documents
> payment records
> shipments
> notifications
> audit
> permissions.
>
> Corriger les défauts trouvés sans casser les modules existants.

### Jour 48 — E2E complet

PROMPT :

> Implémente et exécute le parcours E2E complet :
>
> Buyer registration
> → search Madagascar Vanilla
> → exporter comparison
> → RFQ
> → matching
> → exporter response
> → quotation
> → comparison
> → counteroffer
> → acceptance
> → Trade ID
> → Trade dashboard
> → payment record
> → documents
> → preparation
> → shipment
> → in transit
> → delivery
> → completion.
>
> Ajouter le même principe pour Cloves et Cocoa.

### Jour 49 — Security / performance / deployment

PROMPT :

> Fais un audit production.
>
> Vérifier :
> authentication
> authorization
> rate limiting
> input validation
> file security
> secret management
> database permissions
> backups
> logs
> Docker
> reverse proxy
> HTTPS
> CORS
> headers
> performance
> indexes
> N+1 queries
> pagination.
>
> Produis docs/deployment.md et docs/security-checklist.md.

### Jour 50 — Release V1

PROMPT :

> Prépare la release V1 MadaSource.
>
> Vérifie :
> - fonctionnalité complète
> - tests verts
> - migrations propres
> - documentation
> - variables d'environnement
> - Docker production
> - backup
> - monitoring
> - seed/demo data clairement identifiée
> - DEMO MODE séparé des données réelles
> - README installation
> - README déploiement
> - API documentation.
>
> Ne développe aucune nouvelle fonctionnalité.
>
> Fais uniquement stabilisation, corrections, documentation et préparation de livraison.
>
> Génère un rapport final :
> - fonctionnalités terminées
> - fonctionnalités non activées
> - bugs connus
> - dette technique
> - recommandations V1.1
> - étapes futures.

# 4. Fonctionnalités futures — NE PAS implémenter dans ces 50 jours

Architecture seulement, activation ultérieure :

- Banking integrations
- Payment gateways
- Letters of credit
- Escrow-like mechanisms selon cadre légal
- Logistics provider APIs
- Shipment tracking APIs
- Inspection integrations
- Certification integrations
- Customs/trade data APIs
- Currency provider APIs
- AI Assistant
- Advanced Matching
- Trade Analytics
- Demand Intelligence
- Price Intelligence
- Predictive Tools
- Producer module
- Collector module
- Cooperative module
- Insurance integration
- Partner ecosystem

Le cahier des charges prévoit explicitement une progression Core → Operations → Integrations → Intelligence. Les fonctionnalités futures doivent rester désactivées tant qu'elles ne sont pas activées par MadaSource.

# 5. Critère de fin de projet

La V1 est considérée comme techniquement prête lorsque ce parcours fonctionne réellement de bout en bout :

Discover
→ Buyer registration
→ Exporter discovery
→ RFQ
→ Matching
→ Quotation
→ Negotiation
→ Acceptance
→ Trade ID
→ Documents
→ Payment Record
→ Shipment
→ Tracking
→ Delivery
→ Completion

et lorsque les permissions Buyer / Exporter / Admin, l'audit, la sécurité, les tests et la séparation public/privé sont vérifiés.

