# Modèle de données — backend MadaSource

Jour 3 · 2026-10-13 · Statut : proposition à valider. **La section Trade (§5.16) est provisoire** : elle attend la validation de Q-82 ([registre des décisions](../decisions/architecture-decisions.md)).

Documents liés :
- [erd.mmd](erd.mmd) : diagramme entité-relation ;
- [data-classification.md](data-classification.md) : sensibilité des champs et audiences ;
- [indexes-and-constraints.md](indexes-and-constraints.md) : clés, contraintes, index, droits ;
- [module-boundaries.md](module-boundaries.md) : propriétaires des tables et ordre des modules.

Ce document décrit le modèle **physique proposé** (PostgreSQL). Il ne contient aucun code : les modèles SQLAlchemy et les migrations seront écrits module par module, à partir du Jour 6.

## 1. Sources et statut des choix

| Source | Apport |
|---|---|
| CdC §55 et documents du Jour 1 | Entités et champs métier ([requirements.md](requirements.md), [workflows.md](workflows.md)) |
| Jour 2 | Conventions et frontières : [architecture.md](architecture.md), [module-boundaries.md](module-boundaries.md), [security-design.md](security-design.md) |
| Réponses du 2026-10-13 aux questions Q-09, Q-10, Q-12, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74, Q-82, Q-93 | **PROPOSED**, non approuvées ([registre](../decisions/architecture-decisions.md)) |

Statuts utilisés :
- **Défini** : imposé par le CdC ou la roadmap ;
- **Proposé** : choix de l'équipe ;
- **PROPOSED (Q-NN)** : réponse du responsable produit, à approuver ;
- **À VALIDER** : sans décision.

## 2. Conventions

| Sujet | Convention | Statut |
|---|---|---|
| Clé primaire | `id uuid`, générée par l'application (version : D-15). Exceptions : tables à clé naturelle ou partagée (`buyer_profiles`, `exporter_profiles`, `category_definitions`, `exporter_public_slugs`, tables `*_financials`) et tables d'association (clé composite). | Proposé |
| Colonnes communes | Toute table a `created_at timestamptz NOT NULL`. Une table entièrement modifiable a aussi `updated_at timestamptz NOT NULL`. Une table immuable, ou modifiable sur quelques colonnes seulement, n'a `updated_at` que s'il figure dans ses droits par colonne : la liste de [indexes-and-constraints.md](indexes-and-constraints.md) §6.2 fait foi, et la classe de base SQLAlchemy ne l'ajoute pas automatiquement. Horodatages fixés par l'application (horloge injectable, D-08). | Proposé |
| Dates | `timestamptz` pour les instants, `date` pour les dates calendaires. | Défini (RJ section 1) |
| Montants | `numeric(19,4)` avec une colonne de devise `char(3)` (ISO 4217) à côté. Jamais de `float`. | Défini / Proposé (précision : Q-08) |
| Quantités | `numeric(18,3)` avec une colonne d'unité `varchar(8)` (codes `KG`, `T`…, Q-21). | Proposé |
| Taux | `numeric(7,4)` pour un pourcentage (commission), `numeric(20,10)` pour un taux de change. | Proposé |
| Codes et statuts | `varchar` avec contrainte `CHECK` sur la liste des valeurs. Codes en MAJUSCULES (CF-07, Q-66). Pas de type `ENUM` PostgreSQL : il est plus difficile à faire évoluer par migration. | Proposé |
| Pays, ports, Incoterms | `char(2)` ISO 3166-1, `varchar(5)` UN/LOCODE, `varchar(8)` (`FOB`, `CFR`, `CIF`) (D-30). | Proposé |
| Listes de codes | Tableaux `varchar[]` pour les codes sans table de référence (catégories d'intérêt, marchés, certifications), avec index GIN si filtrés. | Proposé |
| Références lisibles | `reference varchar(24) UNIQUE`, format `PRÉFIXE-AAAA-XXXXXX` (6 caractères aléatoires), préfixe DEMO en environnement de démonstration. Plus de table de compteurs. | PROPOSED (Q-37) |
| Visibilité | Objets à plusieurs parties (documents de Trade, commentaires, événements, notes) : `BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`. Objets d'une seule organisation : `OWNER_ONLY` ou `PUBLIC` (médias du marketplace), valeurs ajoutées à valider. La visibilité ne remplace jamais le contrôle d'accès (S-14). | PROPOSED (Q-82) / À VALIDER (`OWNER_ONLY`, `PUBLIC`) |
| Textes libres | `text`, avec une longueur maximale contrôlée par l'application et par `CHECK (char_length(...) <= n)` pour les champs exposés. Texte brut, sans HTML. | Proposé |
| Données chiffrées | `bytea` (texte chiffré) et `encryption_key_id varchar(32)`, plus une colonne d'affichage masqué (`masked_display`). | Proposé (Q-81) |
| Suppression | Pas de suppression physique dans le workflow normal ; archivage par statut. Les tables d'historique sont en ajout seul. | Défini (BR-PRD-05, BR-NEG-02, BR-TRD-07) |
| Clés étrangères | Seulement vers une table du même module, d'un module de niveau inférieur ou du socle (D-07). `ON DELETE RESTRICT` par défaut ([indexes-and-constraints.md](indexes-and-constraints.md)). | Proposé |
| Références polymorphes | `context_type` et `context_id` (ou `object_type` et `object_id`) sans clé étrangère, pour `documents`, `messages`, `audit` et `notifications`. | Proposé |
| JSON | `jsonb` seulement pour des structures variables et validées par l'application : libellés par langue, résultats de matching, métadonnées non sensibles. Jamais pour contourner le schéma. | Proposé |

## 3. Vue d'ensemble

| Module (niveau) | Tables | Remarque |
|---|---|---|
| socle | `outbox_messages` | Conditionnelle : seulement avec un fournisseur d'email réel (D-20) |
| audit (1) | `audit_logs` | |
| auth (2) | `users`, `sessions`, `refresh_tokens`, `email_verification_tokens`, `password_reset_tokens` | |
| organizations (3) | `organizations`, `organization_capabilities`, `organization_memberships`, `organization_invitations` | Q-09, Q-10, Q-74 |
| access_control (4) | `roles`, `permissions`, `role_permissions`, `platform_role_assignments` | Q-10 |
| notifications (5) | `notifications` | |
| documents (6) | `documents`, `document_versions` | |
| messages (7) | `conversations`, `conversation_participants`, `messages`, `message_attachments` | |
| buyers (8) | `buyer_profiles` | |
| verification (8) | `verification_records`, `verification_reviewed_documents` | |
| exporters (9) | `exporter_profiles`, `exporter_public_slugs`, `capacity_records`, `exporter_certifications`, `bank_details` | |
| products (10) | `category_definitions`, `category_attributes`, `products`, `product_attribute_values` | |
| rfqs (11) | `rfqs`, `rfq_items`, `rfq_recipients`, `rfq_questions` | Q-25 |
| quotations (12) | `pricing_rule_versions`, `external_costs`, `quotations`, `quotation_versions`, `quotation_version_financials`, `quotation_lines`, `quotation_version_costs` ; `exchange_rates` conditionnelle (Q-65) | |
| negotiations (13) | `negotiations`, `negotiation_offers`, `negotiation_offer_lines`, `negotiation_offer_financials`, `offer_external_costs` | |
| trades (14) | `trades`, `trade_items`, `trade_agreements`, `trade_agreement_lines`, `trade_financials`, `trade_events` | **Provisoire (Q-82)** |
| payment_records (15) | `receiving_accounts`, `payment_records` | |
| shipments (15) | `shipments`, `tracking_events` | |
| samples (15) | `sample_requests` | Conditionnelle (Q-53) |
| exceptions (16) | `exception_cases`, `exception_notes`, `disputes` | |
| reviews (17) | `reviews`, `review_ratings` | |
| matching (18) | `matching_configs`, `match_runs`, `rfq_matches` | |
| marketplace (19) | Aucune | Projections publiées (module-boundaries §6) |
| admin (20) | `privacy_requests` | PROPOSED (Q-68) |
| favorites (≥ 13) | `favorites` | Conditionnelle (Q-63) |

Soit 72 tables, dont 4 conditionnelles (`outbox_messages`, `exchange_rates`, `sample_requests`, `favorites`). Les indicateurs de performance (CdC §43-44) sont **calculés à la lecture**, sans table en V1.

## 4. Correspondance avec les entités demandées (RJ 3)

| Entité RJ 3 | Tables |
|---|---|
| Organization, User, Role, Permission, OrganizationMembership | `organizations`, `organization_capabilities`, `users`, `roles`, `permissions`, `role_permissions`, `organization_memberships`, `platform_role_assignments` |
| BuyerProfile, ExporterProfile | `buyer_profiles`, `exporter_profiles` |
| Product, ProductCategory, ProductAttribute | `products`, `category_definitions`, `category_attributes`, `product_attribute_values` |
| Certification | Codes validés (D-30, Q-20) : `exporter_certifications` (société), `products.certification_codes` (produit) |
| VerificationRecord | `verification_records`, `verification_reviewed_documents` |
| RFQ, RFQMatch | `rfqs`, `rfq_items`, `rfq_recipients`, `rfq_questions` ; `match_runs`, `rfq_matches` |
| Quotation, QuotationLine | `quotations`, `quotation_versions`, `quotation_lines`, `quotation_version_financials`, `quotation_version_costs`, `external_costs`, `pricing_rule_versions` |
| Negotiation, NegotiationOffer | `negotiations`, `negotiation_offers`, `negotiation_offer_lines`, `negotiation_offer_financials`, `offer_external_costs` |
| Trade, TradeEvent | `trades`, `trade_items`, `trade_agreements`, `trade_agreement_lines`, `trade_financials`, `trade_events` |
| DocumentMetadata | `documents`, `document_versions` (binaires hors base, D-22) |
| PaymentRecord, Shipment | `payment_records`, `receiving_accounts` ; `shipments`, `tracking_events` |
| Notification, Conversation/Message | `notifications` ; `conversations`, `conversation_participants`, `messages`, `message_attachments` |
| SampleRequest, Review, Exception/Dispute, AuditLog | `sample_requests` ; `reviews`, `review_ratings` ; `exception_cases`, `exception_notes`, `disputes` ; `audit_logs` |

## 5. Tables par module

Notation :
- type PostgreSQL ;
- **NN** = `NOT NULL` ;
- **U** = unique ;
- **FK →** table cible ;
- les colonnes communes (§2) ne sont pas répétées.

### 5.1 Socle

**`outbox_messages`** (conditionnelle, Jours 11 et 31 ; D-20)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `channel` | varchar(16) | NN, CHECK (`EMAIL`) | |
| `template_code` | varchar(64) | NN | |
| `recipient_encrypted` | bytea | NN | Adresse, donnée personnelle |
| `payload_encrypted` | bytea | NN | Peut contenir un lien à jeton : **secret**, purgé après envoi ou abandon (`FAILED`) |
| `encryption_key_id` | varchar(32) | NN | Rotation des clés |
| `status` | varchar(16) | NN, CHECK (`PENDING`, `SENT`, `FAILED`) | |
| `attempts` | smallint | NN, défaut 0 | |
| `next_attempt_at`, `sent_at` | timestamptz | | |
| `last_error_code` | varchar(64) | | Jamais de détail sensible |

### 5.2 audit (niveau 1)

**`audit_logs`** (immuable, ajout seul)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `occurred_at` | timestamptz | NN | |
| `category` | varchar(16) | NN, CHECK (`BUSINESS`, `SECURITY`) | BR-AUD-05 |
| `actor_kind` | varchar(16) | NN, CHECK (`USER`, `SYSTEM`, `DEMO_SYSTEM`) | S-58 |
| `actor_user_id` | uuid | | Identifiant seul, sans clé étrangère (C12, Q-68) |
| `acting_organization_id` | uuid | | Organisation active de l'acteur |
| `on_behalf_of_organization_id` | uuid | | Intervention admin « pour le compte de » (S-32) |
| `action` | varchar(64) | NN | Exemple : `rfq.submit`, `payment.confirm`, `auth.login_failed` |
| `object_type`, `object_id` | varchar(48), uuid | | Référence polymorphe |
| `result` | varchar(16) | NN, CHECK (`SUCCESS`, `DENIED`, `FAILED`) | |
| `request_id` | uuid | | Corrélation avec les journaux |
| `previous_values`, `new_values` | jsonb | | Filtrées selon la classification : masquées ou réservées |
| `restricted_sets` | varchar(16)[] | NN, défaut vide ; valeurs `FINANCE`, `BANK` | Une entrée peut relever des deux ensembles ; la lecture des valeurs exige tous les ensembles listés |
| `metadata` | jsonb | | Non sensible ; **jamais** de donnée personnelle (ni adresse IP, ni email saisi lors d'un échec de connexion : identifiant de l'utilisateur s'il existe) |

### 5.3 auth (niveau 2)

**`users`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `email` | varchar(254) | NN, U sur `lower(email)` | Donnée personnelle |
| `password_hash` | text | NN | Argon2id (S-01), **secret** |
| `full_name` | varchar(200) | | Donnée personnelle |
| `status` | varchar(16) | NN, CHECK (`ACTIVE`, `DISABLED`) | État propre à l'utilisateur (D-28) |
| `email_verified_at` | timestamptz | | Q-13 |
| `mfa_enabled` | boolean | NN, défaut false | Q-80 |
| `mfa_secret_encrypted`, `mfa_secret_key_id` | bytea, varchar(32) | | **Secret**, seulement si Q-80 est retenue ; identifiant de clé pour la rotation |
| `failed_login_count` | integer | NN, défaut 0 | S-06, hors transaction (D-29) ; incrément atomique (`SET x = x + 1`) |
| `locked_until`, `last_login_at` | timestamptz | | |
| `anonymized_at` | timestamptz | | Effacement (Q-68) : identité remplacée, identifiant conservé ; l'email devient une valeur de remplacement unique (contrainte d'unicité) |

**`sessions`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `user_id` | uuid | NN, FK → `users` | |
| `last_seen_at`, `expires_at` | timestamptz | NN | |
| `authenticated_at` | timestamptz | NN | Dernière authentification complète (S-35) |
| `mfa_verified_at` | timestamptz | | Indicateur de second facteur (S-09) |
| `revoked_at` | timestamptz | | Révocation (S-05) |
| `revocation_reason` | varchar(32) | CHECK (`LOGOUT`, `PASSWORD_CHANGE`, `TOKEN_REUSE`, `ACCOUNT_SUSPENDED`, `MEMBERSHIP_REMOVED`, `ADMIN`) | |
| `ip_address` | inet | | Donnée personnelle ; conservation : Q-69 |
| `user_agent` | varchar(300) | | |

**`refresh_tokens`** (immuable, sauf consommation)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `session_id` | uuid | NN, FK → `sessions` | |
| `token_hash` | char(64) | NN, U | SHA-256 du jeton, **secret** (S-04) |
| `issued_at`, `expires_at` | timestamptz | NN | |
| `consumed_at` | timestamptz | | Un rejeu après consommation révoque la session |
| `replaced_by_id` | uuid | FK → `refresh_tokens` | Rotation |

**`email_verification_tokens`**, **`password_reset_tokens`** (même structure)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `user_id` | uuid | NN, FK → `users` | |
| `token_hash` | char(64) | NN, U | **Secret** |
| `expires_at` | timestamptz | NN | |
| `used_at` | timestamptz | | Usage unique (BR-ACC-06) |

### 5.4 organizations (niveau 3)

**`organizations`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `legal_name` | varchar(200) | NN | Champ couvert par la vérification pour un exportateur : modifiable seulement via `exporters` (S-53) |
| `trade_name` | varchar(200) | | |
| `country_code` | char(2) | NN | |
| `region` | varchar(120) | | |
| `website` | varchar(300) | | Jamais appelé par le serveur (SSRF) |
| `created_by_user_id` | uuid | NN, FK → `users` | |

**`organization_capabilities`** (Q-09, Q-12)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `organizations` | |
| `capability` | varchar(16) | NN, CHECK (`BUYER`, `EXPORTER`) | U (`organization_id`, `capability`) |
| `account_status` | varchar(24) | NN | CHECK par paire : BUYER : `PENDING`, `ACTIVE`, `SUSPENDED`, `BLOCKED` (CdC §10). EXPORTER : `PENDING_ACTIVATION`, `ACTIVE`, `SUSPENDED`, `CLOSED` (Q-12). Harmonisation : CF-02 |
| `status_changed_at` | timestamptz | NN | |
| `status_changed_by_user_id` | uuid | FK → `users` | |
| `status_reason` | text | | Motif interne ; motif communiqué : Q-97 (S-47) |
| `activated_at` | timestamptz | | |

**`organization_memberships`** (Q-10, Q-74)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `organizations` | U (`organization_id`, `user_id`) |
| `user_id` | uuid | NN, FK → `users` | Plusieurs adhésions par utilisateur (Q-74) |
| `role` | varchar(24) | NN, CHECK (`OWNER`, `MEMBER`) | Code de rôle, sans clé étrangère vers `access_control` (niveau supérieur) |
| `status` | varchar(16) | NN, CHECK (`ACTIVE`, `SUSPENDED`, `REMOVED`) | |
| `joined_at` | timestamptz | NN | |
| `removed_at` | timestamptz | | |

Invariant applicatif : une organisation garde toujours au moins un OWNER actif. Toute modification d'adhésion (rôle, statut, retrait) verrouille d'abord la ligne `organizations` (`FOR NO KEY UPDATE`), pour que deux OWNER ne se retirent pas en même temps.

**`organization_invitations`** (Q-10)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `organizations` | |
| `email` | varchar(254) | NN | Donnée personnelle |
| `role` | varchar(24) | NN, CHECK (`OWNER`, `MEMBER`) | |
| `token_hash` | char(64) | NN, U | **Secret** |
| `status` | varchar(16) | NN, CHECK (`PENDING`, `ACCEPTED`, `REVOKED`) | « Expirée » est calculé à partir de `expires_at` |
| `invited_by_user_id` | uuid | NN, FK → `users` | Doit être OWNER de l'organisation (règle applicative) |
| `expires_at` | timestamptz | NN | |
| `accepted_at`, `accepted_by_user_id` | timestamptz, uuid | FK → `users` | Une seule acceptation, et seulement par un utilisateur dont l'email **vérifié** est égal à `email` (sans tenir compte de la casse) : un lien transféré ne suffit pas |
| `revoked_at`, `revoked_by_user_id` | timestamptz, uuid | FK → `users` | |

### 5.5 access_control (niveau 4)

**`roles`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `code` | varchar(32) | NN, U | `OWNER`, `MEMBER`, `MADASOURCE_ADMIN` ; rôles futurs inactifs : `OPERATIONS_ADMIN`, `COMPLIANCE_ADMIN`, `FINANCE_ADMIN`, `LOGISTICS_ADMIN`, `SUPER_ADMIN`, `PARTNER` (CdC §53) |
| `scope` | varchar(16) | NN, CHECK (`ORGANIZATION`, `PLATFORM`) | U (`id`, `scope`) pour la clé composite de `role_permissions` |
| `is_active` | boolean | NN | |

**`permissions`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `code` | varchar(64) | NN, U | `<ressource>:<action>` (S-11) |
| `scope` | varchar(16) | NN, CHECK (`ORGANIZATION`, `PLATFORM`) | U (`id`, `scope`) |
| `required_capability` | varchar(16) | CHECK (`BUYER`, `EXPORTER`) ou nul | Permission utilisable seulement si l'organisation active a cette capacité |
| `permission_set` | varchar(32) | CHECK (`FINANCE_READ`, `BANK_DATA`, `PAYMENT_CONFIRM`, `PRICING_CONFIG`, `ADMIN_ACCOUNTS`, `CONVERSATION_READ`, `AUDIT_READ`) ou nul ; CHECK `permission_set IS NULL OR scope = 'PLATFORM'` | Ensembles admin (S-12) |

**`role_permissions`** : `role_id`, `permission_id`, `scope` ; FK composites (`role_id`, `scope`) → `roles` et (`permission_id`, `scope`) → `permissions` ; clé primaire (`role_id`, `permission_id`). Une permission de plateforme (`FINANCE_READ`…) ne peut donc jamais être liée à un rôle d'organisation comme OWNER.

**`platform_role_assignments`** (Q-10, Q-74)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `user_id` | uuid | NN, FK → `users` | |
| `role_id`, `role_scope` | | FK composite (`role_id`, `role_scope`) → `roles` (`id`, `scope`) ; CHECK `role_scope = 'PLATFORM'` | Seul un rôle de plateforme peut être attribué ici |
| `granted_by_user_id` | uuid | FK → `users` ; CHECK `granted_by_user_id IS DISTINCT FROM user_id` ; CHECK `granted_by_user_id IS NOT NULL OR is_bootstrap` | Pas d'auto-attribution |
| `is_bootstrap` | boolean | NN, défaut false ; index unique partiel `WHERE is_bootstrap` | Seule l'attribution initiale du premier admin (S-08, Q-14) peut se passer d'auteur |
| `granted_at` | timestamptz | NN | |
| `revoked_at`, `revoked_by_user_id` | timestamptz, uuid | | U (`user_id`, `role_id`) tant que non révoqué |

### 5.6 notifications (niveau 5)

**`notifications`** (S-52)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `recipient_user_id` | uuid | NN, FK → `users` | |
| `organization_id` | uuid | FK → `organizations` | Contexte d'adhésion ; nul pour un admin de plateforme |
| `type_code` | varchar(64) | NN | Pas de texte composé ni de montant |
| `object_type`, `object_id` | varchar(48), uuid | NN | Objet à relire par son endpoint |
| `read_at` | timestamptz | | |

### 5.7 documents (niveau 6)

**`documents`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `owner_kind` | varchar(16) | NN, CHECK (`ORGANIZATION`, `MADASOURCE`) | Un document émis par MadaSource n'a pas d'organisation propriétaire |
| `owner_organization_id` | uuid | FK → `organizations` | NN si `owner_kind = ORGANIZATION` |
| `category` | varchar(20) | NN, CHECK (`COMMERCIAL`, `COMPANY`, `QUALITY`, `EXPORT`, `SHIPPING`, `PAYMENT`, `CERTIFICATION`, `MARKETPLACE_MEDIA`) | CdC §26 ; `MARKETPLACE_MEDIA` ajoutée pour les médias publics (Q-96). Fixée à la création. U (`id`, `category`), U (`id`, `owner_organization_id`) pour les clés composites |
| `context_type` | varchar(32) | NN, CHECK (`ORGANIZATION`, `VERIFICATION_RECORD`, `PRODUCT`, `RFQ`, `RFQ_RECIPIENT`, `QUOTATION`, `NEGOTIATION`, `TRADE`, `TRADE_AGREEMENT`, `TRADE_EVENT`, `PAYMENT_RECORD`, `SHIPMENT`, `SAMPLE_REQUEST`, `CONVERSATION`, `EXCEPTION_CASE`, `DISPUTE`) | P-01 |
| `context_id` | uuid | NN | Sans clé étrangère |
| `related_trade_id` | uuid | | « Related Trade ID » (CdC §26), renseigné par le module appelant, sans clé étrangère (niveau supérieur) |
| `title` | varchar(200) | NN | Nom affiché nettoyé (S-24) |
| `status` | varchar(16) | NN, CHECK (`ACTIVE`, `ARCHIVED`) | Statuts définitifs : Q-48 |
| `current_version_no` | integer | NN | |
| `created_by_user_id` | uuid | NN, FK → `users` | |

**`document_versions`** (immuable, sauf visibilité et analyse)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `document_id`, `document_category` | uuid, varchar(20) | NN, FK composite → `documents` (`id`, `category`) | U (`document_id`, `version_no`) |
| `version_no` | integer | NN, CHECK > 0 | |
| `storage_key` | varchar(200) | NN, U | Clé aléatoire, **secret** (S-26) |
| `original_filename` | varchar(255) | | Métadonnée nettoyée, jamais un chemin ; peut contenir une donnée personnelle |
| `content_type` | varchar(100) | NN, CHECK (types PDF, JPEG, PNG, DOCX) | Type réel vérifié (S-25) |
| `size_bytes` | bigint | NN, CHECK > 0 | Maximum : Q-48 |
| `sha256` | char(64) | NN | |
| `uploaded_by_user_id` | uuid | NN, FK → `users` | |
| `uploaded_at` | timestamptz | NN | |
| `visibility` | varchar(20) | NN, CHECK (`BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`, `OWNER_ONLY`, `PUBLIC`) ; CHECK `visibility <> 'PUBLIC' OR document_category = 'MARKETPLACE_MEDIA'` | Par défaut, la plus restrictive pour le déposant (S-24) ; `INTERNAL_ONLY` pour un dépôt de MadaSource ; modification auditée. Règles du Modèle A : [data-classification.md](data-classification.md) §2 |
| `visibility_changed_at`, `visibility_changed_by_user_id` | timestamptz, uuid | | |
| `scan_status` | varchar(16) | NN, CHECK (`NOT_SCANNED`, `PENDING`, `CLEAN`, `INFECTED`) | Q-48 |
| `metadata_stripped` | boolean | NN | S-27 |

### 5.8 messages (niveau 7)

**`conversations`** : `context_type` varchar(32) NN, CHECK (`RFQ_RECIPIENT`, `QUOTATION`, `NEGOTIATION`, `TRADE_AGREEMENT`, `SAMPLE_REQUEST`) ; `context_id` uuid NN ; `channel` varchar(24) NN, CHECK (`BUYER_MADASOURCE`, `EXPORTER_MADASOURCE`, `DIRECT`) ; U (`context_type`, `context_id`, `channel`) ; `created_by_user_id` FK → `users` ; `closed_at`.

Règles :
- dans une RFQ, le contexte est la paire RFQ–exportateur (`RFQ_RECIPIENT`, S-31) ;
- pour un Trade, c'est une convention (`TRADE_AGREEMENT`), c'est-à-dire une relation commerciale (Q-82) ;
- **canal** (proposé après le constat de sécurité E1 ; **À VALIDER**, en conflit avec le CdC §28 : CF-10, Q-99) : en Modèle A, aucune conversation ne réunit l'acheteur et l'exportateur sur une quotation, une négociation ou un Trade, car un message sur le prix final révélerait la marge. L'acheteur échange avec MadaSource (`BUYER_MADASOURCE`), l'exportateur aussi (`EXPORTER_MADASOURCE`). Le canal `DIRECT` est réservé au contexte `RFQ_RECIPIENT` (risque résiduel R-05, Q-85) et au Modèle B. Les participants doivent correspondre au canal (règle du service, testée). Si le CdC est maintenu tel quel, la colonne `channel` reste en place avec la seule valeur `DIRECT`, et le risque R-05 est accepté.

**`conversation_participants`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `conversation_id` | uuid | NN, FK → `conversations` | U (`conversation_id`, `organization_id`) ; une seule ligne MadaSource par conversation (index unique partiel) |
| `organization_id` | uuid | FK → `organizations` | Nul pour MadaSource |
| `side` | varchar(16) | NN, CHECK (`BUYER`, `EXPORTER`, `MADASOURCE`) ; CHECK `(side = 'MADASOURCE') = (organization_id IS NULL)` | |
| `joined_at` | timestamptz | NN | |
| `left_at` | timestamptz | | L'accès suit la participation (S-30) |

**`messages`** (immuable, sauf `body` et `edited_at` si Q-50 autorise la modification par l'auteur)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `conversation_id` | uuid | NN, FK → `conversations` | |
| `author_user_id` | uuid | NN, FK → `users` | |
| `author_organization_id` | uuid | FK → `organizations` | Nul pour un admin (signé « MadaSource ») |
| `body` | text | NN, CHECK longueur ≤ 10 000 | |
| `edited_at` | timestamptz | | Q-50 |

**`message_attachments`** : `message_id` FK → `messages`, `document_id` FK → `documents`, clé primaire (`message_id`, `document_id`).

### 5.9 buyers (niveau 8)

**`buyer_profiles`** (une ligne par organisation acheteuse)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | Clé primaire, FK → `organizations` | |
| `business_type` | varchar(64) | | Liste de valeurs : À VALIDER |
| `contact_name`, `contact_email`, `contact_phone` | varchar | | Données personnelles, privées |
| `address_line1`, `address_line2`, `city`, `postal_code`, `address_country_code` | varchar | | Privé |
| `import_markets` | char(2)[] | NN, défaut vide | CdC §10 |
| `interest_category_codes` | varchar(16)[] | NN, défaut vide | Codes de catégories (D-30) |

### 5.10 verification (niveau 8)

**`verification_records`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `organizations` | Organisation exportatrice (C11) |
| `level` | smallint | NN, CHECK 1 à 4 | CdC §8 |
| `status` | varchar(16) | NN, CHECK (`PENDING`, `VERIFIED`, `REJECTED`, `SUSPENDED`) | CdC §8. « Expired » est **calculé** (`VERIFIED` et `expires_at` dépassé, D-23) |
| `requested_at` | timestamptz | NN | |
| `requested_by_user_id` | uuid | FK → `users` | |
| `decided_at`, `decided_by_user_id` | timestamptz, uuid | FK → `users` | NN si statut `VERIFIED`, `REJECTED` ou `SUSPENDED` (CHECK) |
| `expires_at` | timestamptz | | « Where applicable » (CdC §8) |
| `rejection_reason` | text | | Partagé avec l'exportateur (S-47) |
| `internal_notes` | text | | `INTERNAL_ONLY` |
| `supersedes_record_id` | uuid | FK → `verification_records` | Historique des décisions |

Statut de vérification **de l'organisation** (Q-12, CF-01), calculé à la lecture (D-23). Proposition, à valider avec Q-15 et Q-16 :
- s'il existe des enregistrements `VERIFIED` non expirés : `VERIFIED`, au plus haut de leurs niveaux. Une demande de niveau supérieur, en cours ou refusée, ne retire pas le niveau acquis ;
- sinon, selon le dernier enregistrement **décidé** : `SUSPENDED`, `EXPIRED` ou `REJECTED` ;
- sinon : `IN_REVIEW` si une demande est en cours, `UNVERIFIED` s'il n'y a aucun enregistrement ;
- la demande en cours est exposée à part (`pending_request`), sans masquer un niveau acquis ;
- une suspension vise l'organisation : elle passe tous ses enregistrements `VERIFIED` en `SUSPENDED` (à confirmer, Q-15).

**`verification_reviewed_documents`** : `verification_record_id` FK → `verification_records`, `document_id` FK → `documents`, clé primaire composite.

### 5.11 exporters (niveau 9)

**`exporter_profiles`** (une ligne par organisation exportatrice)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | Clé primaire, FK → `organizations` | |
| `public_slug` | varchar(80) | NN, U ; FK composite (`public_slug`, `organization_id`) → `exporter_public_slugs` (`slug`, `organization_id`) | URL du Passport (CdC §9) ; le slug appartient à l'organisation |
| `description` | text | | |
| `logo_document_id` | uuid | FK composite (`logo_document_id`, `organization_id`) → `documents` (`id`, `owner_organization_id`) | Document de l'organisation, catégorie `MARKETPLACE_MEDIA`, visibilité `PUBLIC` |
| `founded_year` | smallint | | « Years in business » calculé |
| `export_experience` | text | | |
| `export_markets` | char(2)[] | NN, défaut vide | |
| `contact_name`, `contact_email`, `contact_phone` | varchar | | Privés |
| `address_line1` … `address_country_code` | varchar | | Privés |
| `business_registration_number` | varchar(64) | | Privé, champ vérifié (S-53) |
| `tax_identifier_encrypted`, `tax_identifier_key_id` | bytea, varchar(32) | | Sensible (Q-81) ; identifiant de clé pour la rotation. Pour une entreprise individuelle, donnée personnelle |
| `tax_identifier_masked` | varchar(16) | | |

**`exporter_public_slugs`** (S-54, un slug n'est jamais réattribué) : `slug` varchar(80), clé primaire ; `organization_id` FK → `organizations` NN ; U (`slug`, `organization_id`) ; `retired_at`.

**`capacity_records`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `exporter_profiles` | |
| `category_code` | varchar(16) | NN | Code (D-30) ; `products` est d'un niveau supérieur |
| `quantity`, `unit` | numeric(18,3), varchar(8) | NN, CHECK quantité > 0 | |
| `period` | varchar(16) | NN, CHECK (`PER_MONTH`, `PER_YEAR`, `PER_SEASON`) | À VALIDER |
| `valid_from`, `valid_to` | date | | |

**`exporter_certifications`** : `organization_id` FK → `exporter_profiles` NN ; `certification_code` varchar(32) NN (Q-20) ; `certificate_number`, `issuer` ; `valid_until` date ; `proof_document_id`, FK composite (`proof_document_id`, `organization_id`) → `documents` (`id`, `owner_organization_id`) ; `verified_at`, `verified_by_user_id`.

**`bank_details`** (S-22, S-44)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `exporter_profiles` | |
| `account_holder_encrypted`, `account_number_encrypted`, `bic_encrypted` | bytea | NN (sauf BIC) | **Bancaire** ; le titulaire est une donnée personnelle |
| `encryption_key_id` | varchar(32) | NN | Rotation (Q-81) |
| `masked_display` | varchar(32) | NN | Exemple : `•••• 4821` |
| `bank_name`, `bank_country_code`, `currency` | varchar, char(2), char(3) | NN | |
| `status` | varchar(24) | NN, CHECK (`PENDING_VERIFICATION`, `VERIFIED`, `REJECTED`, `WITHDRAWN`, `RETIRED`) | Une demande en attente par organisation et par devise ; une nouvelle demande est refusée tant qu'une autre est en attente, et le demandeur peut retirer la sienne (`WITHDRAWN`). Le **compte courant** est calculé à la lecture (D-23) : la ligne `VERIFIED` au plus grand `effective_from` déjà atteint. L'ancien compte reste donc utilisé jusqu'à la prise d'effet du nouveau, sans tâche planifiée |
| `effective_from` | timestamptz | Voir le contrôle de statut ci-dessous | Prise d'effet différée (S-44) ; U (`organization_id`, `currency`, `effective_from`) pour les lignes `VERIFIED` ; U (`id`, `organization_id`) pour la clé composite des paiements |
| `created_by_user_id` | uuid | NN, FK → `users` | |
| `verified_by_user_id`, `verified_at` | uuid, timestamptz | CHECK `status IN ('PENDING_VERIFICATION', 'REJECTED', 'WITHDRAWN') OR (verified_by_user_id IS NOT NULL AND verified_at IS NOT NULL AND effective_from IS NOT NULL)` ; CHECK vérificateur différent du créateur | Une ligne vérifiée, puis éventuellement retirée (`RETIRED`), a toujours un vérificateur |
| `rejected_by_user_id`, `rejected_at` | uuid, timestamptz | | |

### 5.12 products (niveau 10)

**`category_definitions`** : `code` varchar(16), clé primaire (`VANILLA`, `CLOVES`, `COCOA`, CF-09) ; `labels` jsonb NN (`{"en": …, "fr": …}`, Q-66) ; `sort_order`. L'activation vient des flags (D-17), pas d'une colonne.

**`category_attributes`** (Q-18)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `category_code` | varchar(16) | NN, FK → `category_definitions` | U (`category_code`, `code`) |
| `code` | varchar(48) | NN | Exemples : `GRADE`, `MOISTURE`, `SIZE`, `PURITY`, `PROCESSING_TYPE` (CdC §6) ; liste réelle : Q-18 |
| `labels` | jsonb | NN | Par langue |
| `data_type` | varchar(16) | NN, CHECK (`DECIMAL`, `INTEGER`, `TEXT`, `ENUM`, `BOOLEAN`) | |
| `unit` | varchar(16) | | |
| `allowed_values` | jsonb | | Pour `ENUM` : codes et libellés |
| `is_required`, `is_filterable`, `is_matching_criterion` | boolean | NN | Aucun attribut n'est obligatoire pour toutes les catégories (BR-PRD-02) |
| `status` | varchar(16) | NN, CHECK (`ACTIVE`, `RETIRED`) | |

**`products`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `organization_id` | uuid | NN, FK → `organizations` | Exportateur propriétaire |
| `category_code` | varchar(16) | NN, FK → `category_definitions` | U (`id`, `category_code`) pour la cohérence des attributs ; fixée à la création (cible d'une clé composite) |
| `name` | varchar(200) | NN | |
| `description` | text | | |
| `origin_country_code`, `origin_region` | char(2), varchar(120) | NN pour le pays | |
| `available_quantity`, `quantity_unit` | numeric(18,3), varchar(8) | Ensemble ou nuls, CHECK > 0 | |
| `moq_quantity`, `moq_unit` | numeric(18,3), varchar(8) | Ensemble ou nuls | |
| `price_indication_amount`, `price_indication_currency`, `price_indication_unit` | numeric(19,4), char(3), varchar(8) | Ensemble ou nuls, CHECK ≥ 0 | Visibilité publique : Q-06 |
| `price_indication_basis` | varchar(16) | CHECK (`SUPPLIER_NET`, `COMMERCIAL`) | Q-06 : un prix net public révélerait le prix fournisseur |
| `incoterm` | varchar(8) | | |
| `payment_terms`, `packaging` | text | | |
| `offer_valid_until` | timestamptz | | « Quote validity » (CdC §6) |
| `certification_codes` | varchar(32)[] | NN, défaut vide | |
| `status` | varchar(16) | NN, CHECK (`DRAFT`, `PUBLISHED`, `UNPUBLISHED`, `ARCHIVED`) | Q-19 ; publication refusée si l'exportateur n'est pas vérifié (Q-12) |
| `published_at`, `archived_at` | timestamptz | | |
| `created_by_user_id` | uuid | NN, FK → `users` | |

**`product_attribute_values`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `product_id`, `category_code` | uuid, varchar(16) | NN, FK composite → `products` (`id`, `category_code`) | Clé primaire (`product_id`, `attribute_id`) |
| `attribute_id` | uuid | NN, FK composite → `category_attributes` (`id`, `category_code`) | L'attribut appartient à la catégorie du produit |
| `value_decimal`, `value_integer`, `value_text`, `value_boolean`, `value_enum_code` | typés | CHECK : une seule non nulle | |

### 5.13 rfqs (niveau 11)

**`rfqs`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `reference` | varchar(24) | NN, U | `RFQ-AAAA-XXXXXX` (Q-37) |
| `buyer_organization_id` | uuid | NN, FK → `organizations` | U (`id`, `buyer_organization_id`) pour les clés composites |
| `created_by_user_id` | uuid | NN, FK → `users` | |
| `status` | varchar(24) | NN, CHECK (`DRAFT`, `SUBMITTED`, `MATCHING`, `SENT_TO_EXPORTERS`, `QUOTATIONS_RECEIVED`, `NEGOTIATING`, `ACCEPTED`, `CLOSED`) | CdC §12 ; états manquants : Q-24 |
| `distribution_mode` | varchar(16) | NN, CHECK (`OPEN_MATCHING`, `DIRECT`) | Q-25 |
| `destination_country_code`, `destination_port_locode` | char(2), varchar(5) | NN pour le pays | |
| `incoterm` | varchar(8) | | |
| `target_delivery_from`, `target_delivery_to` | date | CHECK début ≤ fin | |
| `payment_preference`, `additional_requirements` | text | | |
| `target_price_amount`, `target_price_currency`, `target_price_unit` | numeric(19,4), char(3), varchar(8) | Ensemble ou nuls | Visible par les destinataires : Q-85 |
| `submitted_at`, `closed_at` | timestamptz | | |

**`rfq_items`** (Q-25)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `rfq_id` | uuid | NN, FK → `rfqs` | U (`rfq_id`, `line_no`) |
| `line_no` | smallint | NN, CHECK > 0 | |
| `category_code` | varchar(16) | NN, FK → `category_definitions` | |
| `product_id` | uuid | FK → `products` | Produit publié choisi, facultatif |
| `quantity`, `unit` | numeric(18,3), varchar(8) | NN, CHECK > 0 | |
| `grade_code` | varchar(48) | | Valeur de l'attribut `GRADE` (Q-18) |
| `quality_requirements`, `packaging` | text | | |
| `certification_codes` | varchar(32)[] | NN, défaut vide | |
| `attribute_requirements` | jsonb | | Exigences sur les attributs, validées par l'application ; le matching n'utilise que des données structurées |
| `override_destination_port_locode`, `override_incoterm`, `override_delivery_from`, `override_delivery_to` | | | Surcharge facultative de l'en-tête (CF-06) |
| `status` | varchar(16) | NN, CHECK (`OPEN`, `AWARDED`, `CLOSED`) | Proposé avec Q-95 : nécessaire pour calculer le statut Closed d'une RFQ à plusieurs lignes |

Une ligne peut être retirée d'une RFQ `DRAFT` (suppression physique autorisée tant que la RFQ n'est pas soumise).

**`rfq_recipients`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `rfq_id`, `buyer_organization_id` | uuid | NN, FK composite → `rfqs` (`id`, `buyer_organization_id`) | U (`id`, `rfq_id`) et U (`id`, `rfq_id`, `exporter_organization_id`) pour les clés composites |
| `exporter_organization_id` | uuid | NN, FK → `organizations` | CHECK ≠ acheteur (S-36) ; U (`rfq_id`, `exporter_organization_id`) |
| `source` | varchar(16) | NN, CHECK (`MATCHING`, `DIRECT`, `ADMIN`) | Q-25 |
| `status` | varchar(16) | NN, CHECK (`SENT`, `DECLINED`, `RESPONDED`, `REMOVED`) | Q-24 |
| `sent_at`, `declined_at`, `responded_at`, `removed_at` | timestamptz | | |
| `decline_reason` | text | | |

**`rfq_questions`** (Ask Question, S-31)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `rfq_id`, `recipient_id` | uuid | NN, FK composite (`recipient_id`, `rfq_id`) → `rfq_recipients` (`id`, `rfq_id`) | Paire RFQ–exportateur |
| `asked_by_user_id`, `answered_by_user_id` | uuid | FK → `users` | |
| `question`, `answer` | text | Question NN | |
| `asked_at`, `answered_at` | timestamptz | | |
| `visibility` | varchar(16) | NN, CHECK (`PAIR`, `ALL_RECIPIENTS`) | Diffusion à tous sur action de l'acheteur seulement (Q-84) |

### 5.14 quotations (niveau 12)

**`pricing_rule_versions`** (structure provisoire : Q-01 à Q-03)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `version_no` | integer | NN, U | |
| `commercial_model` | varchar(16) | NN, CHECK (`RESELLER`, `INTERMEDIARY`) | |
| `method` | varchar(16) | NN, CHECK (`FIXED_PER_UNIT`, `PERCENTAGE`) | |
| `value` | numeric(19,4) | NN, CHECK ≥ 0 ; CHECK `method <> 'PERCENTAGE' OR value <= 100` | |
| `value_currency`, `price_unit` | char(3), varchar(8) | CHECK `(method = 'FIXED_PER_UNIT') = (value_currency IS NOT NULL AND price_unit IS NOT NULL)` | Pour `FIXED_PER_UNIT` |
| `category_code` | varchar(16) | FK → `category_definitions` | Portée facultative |
| `exporter_organization_id` | uuid | FK → `organizations` | Portée facultative |
| `valid_from`, `valid_to` | timestamptz | `valid_from` NN | |
| `status` | varchar(16) | NN, CHECK (`DRAFT`, `ACTIVE`, `RETIRED`) | |
| `created_by_user_id` | uuid | NN, FK → `users` | |

**`external_costs`** (immuable ; CdC §33 ; une confirmation crée une nouvelle ligne `CONFIRMED`, référencée par les versions suivantes)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `cost_type` | varchar(16) | NN, CHECK (`FREIGHT`, `INSURANCE`, `OTHER`) | |
| `amount`, `currency` | numeric(19,4), char(3) | NN, CHECK ≥ 0 | |
| `basis` | varchar(16) | NN, CHECK (`PER_UNIT`, `PER_SHIPMENT`, `PER_CONTAINER`) | |
| `basis_unit` | varchar(8) | | Pour `PER_UNIT` |
| `source` | varchar(24) | NN, CHECK (`LOGISTICS_PARTNER`, `INSURER`, `MANUAL_ESTIMATE`, `OTHER`) | |
| `provider_name` | varchar(120) | | |
| `origin_port_locode`, `destination_port_locode`, `incoterm` | | | |
| `quoted_at`, `valid_until` | timestamptz | NN | Validité calculée à la lecture (D-23, BR-PRC-08) |
| `confirmation_status` | varchar(16) | NN, CHECK (`UNCONFIRMED`, `CONFIRMED`) | |
| `entered_by_user_id` | uuid | NN, FK → `users` | Qui saisit : Q-04 |

**`quotations`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `reference` | varchar(24) | NN, U | `MSQ-AAAA-XXXXXX` (Q-37) |
| `rfq_id`, `buyer_organization_id` | uuid | NN, FK composite → `rfqs` (`id`, `buyer_organization_id`) | |
| `recipient_id`, `exporter_organization_id` | uuid | NN, FK composite → `rfq_recipients` (`id`, `rfq_id`, `exporter_organization_id`) | La quotation vient d'un destinataire de la RFQ |
| `status` | varchar(16) | NN, CHECK (`DRAFT`, `SUBMITTED`, `WITHDRAWN`, `ACCEPTED`, `REJECTED`, `CLOSED`) | Cycle de vie : Q-34. Validité (Active, Expiring, Expired) calculée sur la version courante (D-23) |
| `current_version_no` | integer | | |
| `submitted_at`, `withdrawn_at` | timestamptz | | |
| `created_by_user_id` | uuid | NN, FK → `users` | |

Contraintes : CHECK acheteur ≠ exportateur (S-36) ; U (`rfq_id`, `exporter_organization_id`), une quotation par exportateur et par RFQ (Q-94) ; U (`id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id`) pour la clé composite des Trades.

**`quotation_versions`** (immuable, S-43)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `quotation_id`, `version_no` | uuid, integer | NN, U (`quotation_id`, `version_no`) ; U (`id`, `quotation_id`) | |
| `created_by_user_id` | uuid | NN, FK → `users` | |
| `expires_at` | timestamptz | NN | Validité (CdC §18) |
| `incoterm`, `destination_country_code`, `destination_port_locode` | | Incoterm NN | |
| `lead_time_days` | smallint | CHECK ≥ 0 | |
| `payment_terms`, `packaging`, `additional_conditions` | text | | |
| `currency` | char(3) | NN | Une seule devise par version ; des devises différentes pour la vente et l'approvisionnement exigeraient un taux figé (Q-65) |
| `commercial_model` | varchar(16) | NN, CHECK (`RESELLER`, `INTERMEDIARY`) | Q-01 |
| `pricing_rule_version_id` | uuid | FK → `pricing_rule_versions` | Règles appliquées, figées (S-43) |
| `supplier_total_amount` | numeric(19,4) | NN, CHECK ≥ 0 | Vue exportateur |
| `external_costs_total` | numeric(19,4) | CHECK ≥ 0 | Visibilité : Q-04 |
| `buyer_total_amount` | numeric(19,4) | NN, CHECK ≥ 0 | Vue acheteur, calculée à la création de la version |
| `priced_at` | timestamptz | NN | |

**`quotation_version_financials`** (`madasource_finance` uniquement) : `quotation_version_id` clé primaire, FK → `quotation_versions` ; `margin_total` numeric(19,4) ; `commission_rate` numeric(7,4) ; `commission_amount` numeric(19,4) ; `commission_payer` CHECK (`BUYER`, `EXPORTER`) (Q-03).

**`quotation_lines`** (immuable)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `quotation_version_id` | uuid | NN, FK → `quotation_versions` | U (`quotation_version_id`, `rfq_item_id`), U (`quotation_version_id`, `line_no`), U (`id`, `rfq_item_id`) |
| `line_no` | smallint | NN | |
| `rfq_item_id` | uuid | NN, FK → `rfq_items` | Une quotation peut couvrir une partie des lignes (Q-25) |
| `product_id` | uuid | FK → `products` | |
| `quantity`, `unit` | numeric(18,3), varchar(8) | NN, CHECK > 0 | |
| `grade_code`, `certification_codes` | | | |
| `supplier_unit_price` | numeric(19,4) | NN, CHECK ≥ 0 | Prix net fournisseur |
| `external_costs_unit` | numeric(19,4) | CHECK ≥ 0 | |
| `buyer_unit_price` | numeric(19,4) | NN, CHECK ≥ 0 | Prix final acheteur |

**`quotation_version_costs`** : `quotation_version_id` FK, `external_cost_id` FK → `external_costs`, `applied_amount` numeric(19,4) NN, `applied_currency` char(3) NN, clé primaire composite. Le montant appliqué est figé.

**`exchange_rates`** (conditionnelle, Q-65) : `base_currency`, `quote_currency` char(3) ; `rate` numeric(20,10) CHECK > 0 ; `source` varchar(64) ; `valid_from`, `valid_to` timestamptz. Jamais utilisée pour recalculer un montant figé (BR-CUR-02).

### 5.15 negotiations (niveau 13)

**`negotiations`** : `quotation_id` NN, U, FK → `quotations` ; `status` CHECK (`OPEN`, `ACCEPTED`, `REJECTED`, `EXPIRED`, `CANCELLED`) (Q-38, Q-39) ; `opened_at` NN ; `closed_at`. L'unicité empêche de rouvrir une négociation close : à revoir si Q-39 permet une reprise.

**`negotiation_offers`** (immuable, sauf statut)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `negotiation_id`, `sequence_no` | uuid, integer | NN, U (`negotiation_id`, `sequence_no`) | |
| `author_side` | varchar(16) | NN, CHECK (`BUYER`, `EXPORTER`, `MADASOURCE`) | |
| `author_user_id` | uuid | NN, FK → `users` | |
| `based_on_quotation_version_id` | uuid | NN, FK → `quotation_versions` | |
| `currency` | char(3) | NN | |
| `buyer_total_amount`, `supplier_total_amount` | numeric(19,4) | | Les deux vues ; traduction en Modèle A : Q-05 |
| `terms` | jsonb | | Termes négociés autres que le prix (Q-38) |
| `comment` | text | | |
| `comment_visibility` | varchar(20) | NN, CHECK (`BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`) | Q-82. Valeur fixée par le service selon l'auteur : côté de l'auteur, `INTERNAL_ONLY` pour MadaSource. Jamais `BOTH_PARTIES` en Modèle A |
| `status` | varchar(16) | NN, CHECK (`PENDING`, `SUPERSEDED`, `ACCEPTED`, `REJECTED`, `EXPIRED`) | Au plus une `PENDING` et au plus une `ACCEPTED` par négociation (index uniques partiels) |
| `expires_at` | timestamptz | | Q-38 |
| `decided_at`, `decided_by_user_id` | timestamptz, uuid | | |

**`negotiation_offer_lines`** : `offer_id` FK → `negotiation_offers` ; `quotation_line_id` FK → `quotation_lines` ; `quantity` numeric(18,3), `unit` varchar(8) ; `buyer_unit_price`, `supplier_unit_price` numeric(19,4) ; U (`offer_id`, `quotation_line_id`).

**`negotiation_offer_financials`** (`madasource_finance` uniquement) : `offer_id` clé primaire ; `margin_total`, `commission_amount` numeric(19,4).

**`offer_external_costs`** : `offer_id`, `external_cost_id`, `applied_amount`, `applied_currency`, clé primaire composite (C12).

### 5.16 trades (niveau 14) — PROVISOIRE, Q-82

Proposition qui suit Q-82 : un **Trade** est la référence centrale. Il regroupe une ou deux **conventions** (`trade_agreements`), chacune correspondant à une relation commerciale distincte :

| Modèle commercial | Conventions | Vendeur | Acheteur | Visible par |
|---|---|---|---|---|
| A, revendeur (`RESELLER`) | `SALE` | MadaSource | Organisation acheteuse | Côté acheteur, MadaSource |
| A, revendeur (`RESELLER`) | `SUPPLY` | Organisation exportatrice | MadaSource | Côté exportateur, MadaSource |
| B, intermédiaire (`INTERMEDIARY`) | `DIRECT` | Organisation exportatrice | Organisation acheteuse | Les deux parties, MadaSource (visibilité selon les contrats, Q-82) |

Le modèle commercial est figé à l'acceptation. Les parties d'une convention se **déduisent** de son type et des parties du Trade (tableau ci-dessus) : elles ne sont pas stockées une seconde fois, ce qui supprime un risque d'incohérence. **Ce modèle ne doit pas être implémenté avant la validation de Q-82** : la structure juridique n'est pas choisie par l'équipe technique.

**`trades`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `reference` | varchar(24) | NN, U | `MST-AAAA-XXXXXX` (Q-37) |
| `quotation_id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id` | uuid | NN, FK composite → `quotations` (`id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id`) ; U (`quotation_id`) | Un Trade par quotation (BR-TRD-03) ; plusieurs Trades possibles par RFQ (Q-25, Q-26) ; CHECK acheteur ≠ exportateur. U (`id`, `buyer_organization_id`, `exporter_organization_id`) et U (`id`, `commercial_model`) pour les clés composites |
| `accepted_quotation_version_id` | uuid | NN, FK composite (`accepted_quotation_version_id`, `quotation_id`) → `quotation_versions` (`id`, `quotation_id`) | La version acceptée appartient à la quotation (S-43) |
| `accepted_offer_id` | uuid | FK → `negotiation_offers` | Nul si acceptation directe de la quotation ; appartenance à la négociation de la quotation : règle applicative testée |
| `commercial_model` | varchar(16) | NN, CHECK (`RESELLER`, `INTERMEDIARY`) | Figé |
| `status` | varchar(24) | NN, CHECK (`TRADE_CONFIRMED`, `PAYMENT_PENDING`, `PAYMENT_CONFIRMED`, `PREPARATION`, `READY_FOR_SHIPMENT`, `SHIPPED`, `IN_TRANSIT`, `DELIVERED`, `COMPLETED`, `CANCELLED`, `DISPUTED`, `ON_HOLD`) | CdC §24 |
| `status_before_exception` | varchar(24) | CHECK : même liste que `status`, sauf `DISPUTED` et `ON_HOLD` | Retour après On Hold ou Disputed (Q-44) |
| `shipment_summary` | varchar(24) | NN, CHECK (`NONE`, `PENDING`, `READY_FOR_SHIPMENT`, `SHIPPED`, `IN_TRANSIT`, `ARRIVED`, `DELIVERED`) | Statut résumé (CdC §23, C35). Le statut résumé des paiements est porté par chaque convention (`trade_agreements.payment_status`), car en Modèle A les deux flux de paiement sont bilatéraux |
| `accepted_at`, `accepted_by_user_id` | timestamptz, uuid | NN | |
| `completed_at`, `cancelled_at` | timestamptz | | |

**`trade_items`** (immuable, sauf `released_at`) :
- `trade_id` FK → `trades` NN ; U (`id`, `trade_id`) ;
- `quotation_line_id`, `rfq_item_id` NN, FK composite → `quotation_lines` (`id`, `rfq_item_id`) : la ligne de Trade reprend la ligne de RFQ de la ligne de quotation ;
- `category_code` ; `product_id` ; `quantity` numeric(18,3), `unit` varchar(8) ; `grade_code` ; `certification_codes` ;
- `released_at` : ligne de RFQ libérée par l'annulation du Trade ;
- index unique partiel (`rfq_item_id`) `WHERE released_at IS NULL` : une ligne de RFQ n'est attribuée qu'à un Trade non annulé à la fois. À revoir si Q-26 autorise la répartition d'une même ligne entre exportateurs.

Ces données descriptives sont communes aux deux conventions.

**`trade_agreements`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id`, `commercial_model` | uuid, varchar(16) | NN, FK composite → `trades` (`id`, `commercial_model`) | U (`trade_id`, `kind`) ; U (`id`, `trade_id`) et U (`id`, `trade_id`, `kind`) pour les clés composites |
| `kind` | varchar(16) | NN, CHECK (`SALE`, `SUPPLY`, `DIRECT`) ; CHECK `(commercial_model = 'RESELLER' AND kind IN ('SALE', 'SUPPLY')) OR (commercial_model = 'INTERMEDIARY' AND kind = 'DIRECT')` | Les parties se déduisent du type |
| `currency` | char(3) | NN | |
| `total_amount` | numeric(19,4) | NN, CHECK ≥ 0 | Prix de **cette** convention : final pour `SALE`, net pour `SUPPLY` |
| `incoterm`, `destination_country_code`, `destination_port_locode` | | | |
| `payment_terms` | text | | |
| `delivery_from`, `delivery_to` | date | | |
| `frozen_at` | timestamptz | NN | Termes figés (BR-TRD-05) |
| `payment_status` | varchar(16) | NN, CHECK (`NONE`, `PENDING`, `PARTIAL`, `CONFIRMED`, `REFUNDED`) | Seule colonne modifiable ; servie à l'audience de la convention seulement (CdC §23) |

**`trade_agreement_lines`** (immuable) : `agreement_id`, `trade_item_id`, `trade_id` ; FK composites (`agreement_id`, `trade_id`) → `trade_agreements` (`id`, `trade_id`) et (`trade_item_id`, `trade_id`) → `trade_items` (`id`, `trade_id`) : la convention et la ligne appartiennent au même Trade ; `unit_price`, `line_total` numeric(19,4) NN ; clé primaire (`agreement_id`, `trade_item_id`).

**`trade_financials`** (immuable, `madasource_finance` uniquement) : `trade_id` clé primaire ; `margin_total` numeric(19,4) ; `commission_rate` numeric(7,4), `commission_amount` numeric(19,4), `commission_payer` (Q-03) ; `external_costs_total` numeric(19,4) ; `currency` char(3) ; `frozen_at`. Des devises différentes entre `SALE` et `SUPPLY` exigeraient ici un taux figé (Q-65).

**`trade_events`** (immuable)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id` | uuid | NN, FK → `trades` | |
| `occurred_at` | timestamptz | NN | |
| `actor_kind` | varchar(16) | NN, CHECK (`USER`, `SYSTEM`, `DEMO_SYSTEM`) | |
| `actor_user_id`, `actor_organization_id` | uuid | FK → `users`, `organizations` | Affichage selon S-48 |
| `event_type` | varchar(48) | NN | |
| `from_status`, `to_status` | varchar(24) | | |
| `comment` | text | | |
| `visibility` | varchar(20) | NN, CHECK (`BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`) ; CHECK `agreement_kind IS DISTINCT FROM 'SALE' OR visibility IN ('BUYER_VISIBLE', 'INTERNAL_ONLY')` ; CHECK `agreement_kind IS DISTINCT FROM 'SUPPLY' OR visibility IN ('EXPORTER_VISIBLE', 'INTERNAL_ONLY')` | Q-82 ; un événement d'une convention du Modèle A ne peut pas être servi à l'autre partie |
| `agreement_id`, `agreement_kind` | uuid, varchar(16) | FK composite (`agreement_id`, `trade_id`, `agreement_kind`) → `trade_agreements` (`id`, `trade_id`, `kind`) ; tous deux nuls ou tous deux renseignés | Événement propre à une relation |
| `document_id` | uuid | FK → `documents` | |
| `metadata` | jsonb | | Non sensible |

### 5.17 payment_records (niveau 15)

**`receiving_accounts`** (comptes de réception de MadaSource, S-44) : mêmes colonnes chiffrées que `bank_details`, plus `label` ; mêmes statuts (`PENDING_VERIFICATION`, `VERIFIED`, `REJECTED`, `WITHDRAWN`, `RETIRED`) et mêmes contraintes (vérificateur obligatoire et différent du créateur) ; `effective_from` ; `created_by_user_id` NN. Compte courant par devise calculé comme pour `bank_details`.

**`payment_records`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id`, `agreement_id`, `agreement_kind` | uuid, uuid, varchar(16) | NN, FK composite (`agreement_id`, `trade_id`, `agreement_kind`) → `trade_agreements` (`id`, `trade_id`, `kind`) | Relation financière concernée (Q-82) ; le paiement et sa convention appartiennent au même Trade |
| `direction` | varchar(32) | NN, CHECK (`BUYER_TO_MADASOURCE`, `MADASOURCE_TO_EXPORTER`, `BUYER_TO_EXPORTER`) | CHECK cohérent avec `agreement_kind` (S-40) |
| `amount`, `currency` | numeric(19,4), char(3) | NN, CHECK montant > 0 | |
| `method` | varchar(16) | NN, CHECK (`BANK_TRANSFER`) | V1 |
| `payment_reference` | varchar(120) | | |
| `payment_date` | date | | |
| `status` | varchar(16) | NN, CHECK (`PENDING`, `PROCESSING`, `CONFIRMED`, `FAILED`, `REFUNDED`) | CdC §30 |
| `receiving_account_id` | uuid | FK → `receiving_accounts` ; CHECK `(receiving_account_id IS NOT NULL) = (direction = 'BUYER_TO_MADASOURCE')` | Compte de MadaSource crédité |
| `exporter_organization_id` | uuid | NN, FK composite (`trade_id`, `exporter_organization_id`) → `trades` (`id`, `exporter_organization_id`) | Exportateur du Trade, dénormalisé |
| `beneficiary_bank_details_id` | uuid | FK composite (`beneficiary_bank_details_id`, `exporter_organization_id`) → `bank_details` (`id`, `organization_id`) ; CHECK `(beneficiary_bank_details_id IS NOT NULL) = (direction = 'MADASOURCE_TO_EXPORTER')` | Le compte appartient à l'exportateur du Trade (R-28) ; le service exige aussi qu'il soit le compte courant vérifié à la date du paiement (S-44). Compte de l'exportateur effectivement utilisé : preuve en cas de fraude au changement de coordonnées (S-44). En Modèle B (`BUYER_TO_EXPORTER`) : Q-55 |
| `recorded_by_user_id`, `recorded_at` | uuid, timestamptz | NN | |
| `processing_by_user_id`, `processing_at` | | | |
| `confirmed_by_user_id`, `confirmed_at` | | CHECK confirmateur ≠ auteur de la saisie et ≠ auteur du passage en Processing (S-34) | |
| `failed_by_user_id`, `failed_at`, `failure_reason` | | CHECK : renseignés si `FAILED` | |
| `refunded_by_user_id`, `refunded_at`, `refund_reason` | | CHECK : renseignés si `REFUNDED` ; remboursement par un autre que l'auteur de la saisie (S-34) et, proposé, que le confirmateur (Q-56, Q-88) | |

Colonnes figées après insertion (`trade_id`, convention, sens, montant, devise, comptes, saisie) : droits par colonne ([indexes-and-constraints.md](indexes-and-constraints.md) §6.2). Une colonne d'acteur ne peut pas être réécrite une fois renseignée : déclencheur d'écriture unique, à évaluer au Jour 33.

Justificatifs : `documents` de contexte `PAYMENT_RECORD` (BR-PAY-03). Leur visibilité **découle du sens du paiement** et n'est pas modifiable : `BUYER_TO_MADASOURCE` → `BUYER_VISIBLE`, `MADASOURCE_TO_EXPORTER` → `EXPORTER_VISIBLE`, `BUYER_TO_EXPORTER` → `BOTH_PARTIES` (S-40).

### 5.18 shipments (niveau 15)

**`shipments`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id` | uuid | NN, FK → `trades` | Plusieurs par Trade possibles (Q-57) ; affectation des lignes à une expédition (`shipment_items`) : seulement si Q-57 retient les livraisons partielles |
| `shipment_reference`, `carrier`, `tracking_number` | varchar | | CdC §31 |
| `shipping_method` | varchar(16) | CHECK (`SEA`, `AIR`, `ROAD`, `MULTIMODAL`) | À VALIDER |
| `container_number` | varchar(11) | | Format ISO 6346 |
| `origin_country_code`, `origin_port_locode`, `destination_country_code`, `destination_port_locode` | | | |
| `estimated_departure_at`, `estimated_arrival_at` | timestamptz | | |
| `status` | varchar(24) | NN, CHECK (`PENDING`, `READY_FOR_SHIPMENT`, `SHIPPED`, `IN_TRANSIT`, `ARRIVED`, `DELIVERED`) | |
| `created_by_user_id` | uuid | NN, FK → `users` | Qui saisit : Q-58 |

**`tracking_events`** (immuable) : `shipment_id` FK NN ; `occurred_at`, `recorded_at` NN ; `recorded_by_user_id` NN ; `status` ; `location` ; `comment` ; `visibility` NN (valeurs Q-82), défaut `INTERNAL_ONLY` pour MadaSource et le système, côté de l'auteur sinon.

Les données d'une expédition (transporteur, suivi, ports, dates) sont partagées entre les parties ; à confirmer avec Q-82.

### 5.19 samples (niveau 15) — conditionnelle, Q-53

**`sample_requests`** :
- `buyer_organization_id`, `exporter_organization_id` NN, CHECK différentes ;
- `product_id` FK, `rfq_id` FK (facultatifs) ;
- `status` CHECK (`SAMPLE_REQUESTED`, `SAMPLE_QUOTATION`, `SAMPLE_CONFIRMED`, `SAMPLE_PAYMENT`, `SAMPLE_SHIPPED`, `SAMPLE_RECEIVED`, `SAMPLE_APPROVED`, `SAMPLE_REJECTED`) (CdC §27) ;
- `quantity` numeric(18,3), `unit` varchar(8) ;
- deux prix, comme pour une quotation : `buyer_price_amount` et `supplier_price_amount` numeric(19,4), `price_currency` char(3). En Modèle A, chaque partie ne voit que le sien (S-19) ; décision : Q-53 ;
- `carrier`, `tracking_number` ;
- `requested_by_user_id` NN ; `decided_at`.

### 5.20 exceptions (niveau 16)

**`exception_cases`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `type` | varchar(32) | NN, CHECK (`PAYMENT_DELAYED`, `QUOTATION_EXPIRED`, `EXPORTER_NOT_RESPONDING`, `DOCUMENT_MISSING`, `SHIPMENT_DELAYED`, `BUYER_DISPUTE`, `QUALITY_ISSUE`, `QUANTITY_DISCREPANCY`, `CANCELLED_ORDER`) | CdC §40 |
| `trade_id` | uuid | FK → `trades` | Facultatif (SRC-19) |
| `object_type`, `object_id` | varchar(48), uuid | | Objet antérieur au Trade |
| `priority` | varchar(16) | NN, CHECK (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) | |
| `status` | varchar(16) | NN, CHECK (`OPEN`, `ASSIGNED`, `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `CLOSED`) | Q-60 |
| `assigned_to_user_id` | uuid | FK → `users` | |
| `opened_by_kind`, `opened_by_user_id` | varchar(16), uuid | CHECK (`SYSTEM`, `ADMIN`, `PARTY`) | |
| `opened_at`, `resolved_at`, `closed_at` | timestamptz | | |
| `resolution_summary` | text | | `INTERNAL_ONLY` par défaut |

**`exception_notes`** (immuable) : `exception_id` FK NN ; `author_user_id` NN ; `body` NN ; `visibility` NN, défaut `INTERNAL_ONLY` (S-47).

**`disputes`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id` | uuid | NN, FK → `trades` | |
| `agreement_id` | uuid | FK composite (`agreement_id`, `trade_id`) → `trade_agreements` (`id`, `trade_id`) | Relation concernée ; en Modèle A, un litige de l'acheteur porte sur la vente |
| `opened_by_organization_id`, `opened_by_user_id` | uuid | NN | Partie au Trade (règle applicative) |
| `reason_code` | varchar(48) | NN | |
| `description`, `requested_resolution`, `proposed_resolution` | text | Description NN | |
| `status` | varchar(24) | NN, CHECK (`OPEN`, `UNDER_REVIEW`, `RESOLUTION_PROPOSED`, `RESOLVED`, `CLOSED`) | CdC §41 |
| `visibility` | varchar(20) | NN, CHECK (valeurs Q-82) ; défaut : côté de la partie qui ouvre | Remplace un simple booléen : une résolution chiffrée sur le prix final, visible de l'exportateur, révélerait la marge. Visibilité par la contrepartie : Q-92 |
| `proposed_at`, `resolved_at`, `closed_at` | timestamptz | | |

Preuves : `documents` de contexte `DISPUTE`.

### 5.21 reviews (niveau 17)

**`reviews`**

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `trade_id`, `buyer_organization_id`, `exporter_organization_id` | uuid | NN, FK composite → `trades` | |
| `direction` | varchar(24) | NN, CHECK (`BUYER_TO_EXPORTER`, `EXPORTER_TO_BUYER`) | U (`trade_id`, `direction`) : une évaluation par sens (BR-REP-02) |
| `author_user_id` | uuid | NN, FK → `users` | |
| `comment` | text | | |
| `status` | varchar(16) | NN, CHECK (`PUBLISHED`, `HIDDEN`) | Modération : Q-59 |
| `submitted_at` | timestamptz | NN | Après Completed (règle applicative, BR-REP-01) |

**`review_ratings`** : `review_id` FK ; `criterion` CHECK (`COMMUNICATION`, `PRODUCT_CONFORMITY`, `DELIVERY`, `DOCUMENTATION`, `RESPONSIVENESS`, `TRANSACTION_EXPERIENCE`) (CdC §42) ; `score` smallint CHECK 1 à 5 (échelle : Q-59) ; clé primaire (`review_id`, `criterion`).

### 5.22 matching (niveau 18)

**`matching_configs`** : `version_no` NN, U ; `weights` jsonb NN (critère → poids) ; `thresholds` jsonb NN (score minimal, nombre maximal de destinataires, Q-30) ; `status` CHECK (`DRAFT`, `ACTIVE`, `RETIRED`) avec une seule `ACTIVE` (index unique partiel) ; `created_by_user_id` NN ; `activated_at`.

**`match_runs`** : `rfq_id` FK NN ; U (`id`, `rfq_id`) ; `matching_config_id` FK NN ; `trigger` CHECK (`SUBMISSION`, `ADMIN_RERUN`) ; `triggered_by_user_id` ; `status` CHECK (`SUCCEEDED`, `FAILED`) ; `started_at` NN, `finished_at` ; `input_digest` char(64), empreinte des données d'entrée pour la reproductibilité (BR-MAT-02) ; `error_code`.

**`rfq_matches`** (immuable)

| Colonne | Type | Contraintes | Remarque |
|---|---|---|---|
| `match_run_id` | uuid | NN, FK → `match_runs` | U (`match_run_id`, `exporter_organization_id`) |
| `rfq_id` | uuid | NN, FK → `rfqs` ; FK composite (`match_run_id`, `rfq_id`) → `match_runs` (`id`, `rfq_id`) | Même RFQ que l'exécution |
| `exporter_organization_id` | uuid | NN, FK → `organizations` | |
| `score` | numeric(5,2) | NN, CHECK 0 à 100 | |
| `criteria_results` | jsonb | NN | Résultat par critère et par ligne : satisfait, partiel, non disponible ; poids, contribution. Usage interne ; les projections filtrent (S-49). |
| `is_selected` | boolean | NN | |

### 5.23 admin (niveau 20) et modules conditionnels

**`privacy_requests`** (PROPOSED, Q-68) :
- `request_type` CHECK (`ACCESS`, `RECTIFICATION`, `EXPORT`, `ERASURE`) ;
- `subject_user_id` FK → `users` ;
- `status` CHECK (`RECEIVED`, `IN_PROGRESS`, `COMPLETED`, `REJECTED`) ;
- `received_at` NN ; `decided_at`, `decided_by_user_id` ;
- `decision_summary` text, **sans donnée personnelle** ;
- `legal_hold` boolean NN.

**`favorites`** (conditionnelle, Q-63 ; module `favorites`, niveau 13 ou plus) : `user_id` NN, `organization_id` NN, `target_type` CHECK (`PRODUCT`, `EXPORTER`, `QUOTATION`), `target_id` ; U (`user_id`, `organization_id`, `target_type`, `target_id`). Un favori ne donne aucun droit d'accès (S-14).

## 6. Invariants et intégrité

| Invariant | Mise en œuvre | Source |
|---|---|---|
| Acheteur ≠ exportateur sur une RFQ, une quotation, un Trade, un échantillon | Colonnes dénormalisées, clés étrangères composites et `CHECK` sur la même ligne | S-36, Q-09 |
| Une quotation vient d'un destinataire actif de la RFQ | Clé composite vers `rfq_recipients`, plus statut vérifié par le service | S-30 |
| Un Trade par quotation, une ligne de RFQ attribuée une seule fois | `UNIQUE` sur `trades.quotation_id` et `trade_items.rfq_item_id` | BR-TRD-03, Q-26 |
| Une seule acceptation par négociation | Index unique partiel sur `negotiation_offers` (`status = ACCEPTED`) | BR-NEG-04 |
| Prix présenté = prix accepté | Versions immuables (`quotation_versions`), acceptation par identifiant et version | S-43 |
| Termes figés | Conventions et lignes copiées à l'acceptation, jamais recalculées | BR-TRD-05 |
| Attribut cohérent avec la catégorie du produit | Clés étrangères composites (`category_code`) | BR-PRD-02 |
| Séparation des tâches sur les paiements | `CHECK` entre colonnes d'acteurs | S-34 |
| Coordonnées bancaires : vérificateur ≠ créateur, une ligne active par devise | `CHECK`, index unique partiel | S-44 |
| Historiques immuables | Pas de `updated_at`, pas de chemin de modification, droits restreints sur `audit_logs` | BR-AUD-02, BR-TRD-07 |
| Au moins un OWNER par organisation | Règle applicative (service `organizations`), sous verrou de la ligne `organizations` | Proposé, déduit de Q-10 |
| Cohérence de la chaîne RFQ → quotation → Trade → convention → paiement, événement, litige | Clés étrangères composites ([indexes-and-constraints.md](indexes-and-constraints.md) §2.1) | S-30, S-43 |
| Pas de fil commun acheteur–exportateur en Modèle A | Canal de conversation (§5.8), vérifié par le service | Proposé, **À VALIDER** : conflit avec le CdC §28 (CF-10, Q-99) |
| Visibilité d'un événement ou d'un justificatif bornée par sa convention | `CHECK` sur `trade_events` ; visibilité dérivée pour les justificatifs | S-40, Q-82 |
| Un utilisateur n'agit pas des deux côtés d'un même objet | Règle applicative : refus de soumettre, contre-proposer, accepter ou évaluer si l'acteur a aussi une adhésion active chez la contrepartie | S-36, Q-98 |
| Permissions de plateforme jamais liées à un rôle d'organisation | Clés composites sur la portée (`role_permissions`) | S-12 |

## 7. Questions ouvertes nées du Jour 3

| Question | Sujet |
|---|---|
| Q-94 | Un exportateur peut-il soumettre plusieurs quotations distinctes (variantes) pour une même RFQ ? Proposition : non, une quotation par exportateur, avec versions. |
| Q-95 | Avec des RFQ à plusieurs lignes et plusieurs Trades possibles (Q-25), que signifient les statuts Accepted et Closed de la RFQ (CdC §12) ? Proposition : Accepted dès la première acceptation, Closed quand toutes les lignes sont attribuées, déclinées ou expirées. |
| Q-96 | Ajout des valeurs de visibilité `OWNER_ONLY` et `PUBLIC` aux quatre valeurs de Q-82, pour les objets d'une seule organisation et les médias du marketplace. |
| Q-97 | Le motif d'un changement de statut de compte (suspension, blocage, clôture) est-il communiqué à l'organisation concernée ? Proposition : un motif communiqué distinct de la note interne, comme pour la vérification (S-47). |
| Q-98 | Un utilisateur membre à la fois de l'organisation acheteuse et de l'organisation exportatrice d'un même objet (Q-74) : interdire cette double adhésion, ou seulement bloquer ses actions sur ces objets ? En Modèle A, il lirait les deux conventions et donc la marge. |
| Q-99 | En Modèle A, les messages entre l'acheteur et l'exportateur sur une quotation, une négociation ou un Trade passent-ils par des canaux séparés avec MadaSource (proposition), ou restent-ils directs comme le prévoit le CdC §28 (CF-10) ? |
| Q-100 | Un compte administrateur MadaSource peut-il aussi détenir une adhésion à une organisation cliente ? Proposition : non (S-33 du Jour 2, constat E-6). |
| Q-101 | Combien d'administrateurs humains en V1 ? La séparation des tâches (paiements, comptes de réception, coordonnées bancaires) exige au moins deux personnes ; avec une seule, ces opérations sont bloquées par la base. |

Les autres points `À VALIDER` renvoient aux questions existantes (Q-03 à Q-06, Q-08, Q-18 à Q-21, Q-24, Q-26, Q-30, Q-34, Q-38, Q-39, Q-44, Q-48, Q-50, Q-53, Q-57 à Q-60, Q-63, Q-65, Q-69, Q-80, Q-81, Q-84, Q-85, Q-92).
