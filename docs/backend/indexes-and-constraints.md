# Index et contraintes — backend MadaSource

Jour 3 · 2026-10-13 · Statut : proposition, à implémenter module par module à partir du Jour 6. Les contraintes du Trade suivent le modèle **provisoire** de [data-model.md](data-model.md) §5.16 (Q-82).

Ce document fixe les règles d'intégrité appliquées **par la base**. Les règles applicatives (transitions, permissions) restent dans les services. Une contrainte de base est le dernier rempart : elle ne remplace jamais le contrôle du service, qui renvoie une erreur métier lisible avant que la base ne refuse ([error-handling.md](error-handling.md)).

## 1. Nommage

Convention passée à `MetaData(naming_convention=...)` de SQLAlchemy (Jour 6), pour que les migrations Alembic produisent des noms stables :

| Objet | Modèle | Exemple |
|---|---|---|
| Clé primaire | `pk_<table>` | `pk_rfqs` |
| Clé étrangère | `fk_<table>_<colonne>_<table cible>` | `fk_rfq_items_rfq_id_rfqs` |
| Unicité | `uq_<table>_<colonnes>` | `uq_rfqs_reference` |
| Contrôle | `ck_<table>_<nom>` | `ck_payment_records_confirmer_distinct` |
| Index | `ix_<table>_<colonnes>` | `ix_trade_events_trade_id_occurred_at` |
| Index unique partiel | `uq_<table>_<nom>` | `uq_negotiation_offers_one_pending` |

Points d'attention :
- La convention de SQLAlchemy applique le modèle `ix` à tout objet `Index`, même unique. Les index uniques partiels (`uq_…`) sont donc **nommés explicitement** dans leur déclaration.
- Les noms PostgreSQL sont limités à 63 caractères. Une clé étrangère composite dont le nom dépasserait cette limite est nommée explicitement, jamais tronquée par la base.
- La traduction des violations d'intégrité ([error-handling.md](error-handling.md) §6) reconnaît une contrainte par son **nom** : un nom de contrainte ne change pas sans migration et sans mise à jour de cette correspondance.

## 2. Clés étrangères

| Règle | Détail |
|---|---|
| `ON DELETE RESTRICT` partout | Aucune suppression en cascade. Une suppression physique qui laisserait un historique orphelin échoue. |
| `ON UPDATE` | Sans objet : une clé primaire n'est jamais modifiée. Les colonnes cibles d'une clé composite ne sont pas modifiables non plus (§6.2). |
| Direction | Vers une table du même module, d'un module de niveau inférieur ou du socle (D-07). Vérifié sur l'ERD par un script de contrôle (Jour 3), puis par le test d'architecture (Jour 7). |
| Index | Chaque colonne de clé étrangère est indexée, sauf si elle est la première colonne d'un autre index ou d'une contrainte d'unicité. PostgreSQL ne crée pas ces index automatiquement ; sans eux, `RESTRICT` et les jointures parcourent la table enfant. **Exception** : les colonnes d'acteur (`created_by_user_id`, `decided_by_user_id`…) ne sont pas indexées par défaut. Un utilisateur n'est jamais supprimé, donc `RESTRICT` ne les parcourt jamais ; un index n'est ajouté que pour une requête réelle (par exemple `assigned_to_user_id`). |
| Références polymorphes | `context_type`/`context_id` et `object_type`/`object_id` n'ont pas de clé étrangère. L'existence de l'objet est vérifiée par le module propriétaire (P-01) au moment de l'écriture. Index composite (`context_type`, `context_id`). |
| Identifiants d'acteur dans l'audit | `audit_logs.actor_user_id` n'a pas de clé étrangère : l'audit reste lisible et immuable même si le compte est anonymisé (Q-68). |
| Colonnes facultatives | Une clé composite dont une colonne est nulle n'est pas vérifiée (`MATCH SIMPLE`, comportement par défaut). Un `CHECK` impose que les colonnes d'une même clé facultative soient toutes nulles ou toutes renseignées. |

### 2.1 Clés étrangères composites (cohérence entre objets)

Elles garantissent qu'une valeur dénormalisée sur une ligne est bien celle de l'objet parent. Le `CHECK` de la même ligne garantit ensuite, par exemple, que l'acheteur et l'exportateur sont différents (S-36, Q-09).

| Table enfant | Colonnes | Table cible (unicité requise) | Effet |
|---|---|---|---|
| `rfq_recipients` | (`rfq_id`, `buyer_organization_id`) | `rfqs` (`id`, `buyer_organization_id`) | Le destinataire connaît l'acheteur réel de la RFQ |
| `rfq_questions` | (`recipient_id`, `rfq_id`) | `rfq_recipients` (`id`, `rfq_id`) | La question porte sur un destinataire de cette RFQ |
| `quotations` | (`rfq_id`, `buyer_organization_id`) | `rfqs` (`id`, `buyer_organization_id`) | |
| `quotations` | (`recipient_id`, `rfq_id`, `exporter_organization_id`) | `rfq_recipients` (`id`, `rfq_id`, `exporter_organization_id`) | La quotation vient d'un destinataire de **cette** RFQ |
| `trades` | (`quotation_id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id`) | `quotations` (`id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id`) | La RFQ et les parties du Trade sont celles de la quotation |
| `trades` | (`accepted_quotation_version_id`, `quotation_id`) | `quotation_versions` (`id`, `quotation_id`) | La version acceptée appartient à la quotation (S-43) |
| `trade_items` | (`quotation_line_id`, `rfq_item_id`) | `quotation_lines` (`id`, `rfq_item_id`) | La ligne de Trade reprend la ligne de RFQ de sa ligne de quotation |
| `trade_agreements` | (`trade_id`, `commercial_model`) | `trades` (`id`, `commercial_model`) | Le type de convention est cohérent avec le modèle commercial (`CHECK` en §3.2) |
| `trade_agreement_lines` | (`agreement_id`, `trade_id`) et (`trade_item_id`, `trade_id`) | `trade_agreements` (`id`, `trade_id`), `trade_items` (`id`, `trade_id`) | La convention et la ligne appartiennent au même Trade |
| `trade_events` | (`agreement_id`, `trade_id`, `agreement_kind`) | `trade_agreements` (`id`, `trade_id`, `kind`) | Facultative ; la visibilité est bornée par le type (§3.2) |
| `payment_records` | (`agreement_id`, `trade_id`, `agreement_kind`) | `trade_agreements` (`id`, `trade_id`, `kind`) | Le paiement porte sur une convention de **son** Trade ; le sens est cohérent avec le type (§3.2) |
| `payment_records` | (`trade_id`, `exporter_organization_id`) ; (`beneficiary_bank_details_id`, `exporter_organization_id`) | `trades` (`id`, `exporter_organization_id`) ; `bank_details` (`id`, `organization_id`) | Le compte bénéficiaire appartient à l'exportateur du Trade (R-28) |
| `disputes` | (`agreement_id`, `trade_id`) | `trade_agreements` (`id`, `trade_id`) | Facultative |
| `reviews` | (`trade_id`, `buyer_organization_id`, `exporter_organization_id`) | `trades` (`id`, `buyer_organization_id`, `exporter_organization_id`) | L'évaluation porte sur les parties du Trade |
| `rfq_matches` | (`match_run_id`, `rfq_id`) | `match_runs` (`id`, `rfq_id`) | Le résultat porte sur la RFQ de l'exécution |
| `product_attribute_values` | (`product_id`, `category_code`) et (`attribute_id`, `category_code`) | `products` (`id`, `category_code`), `category_attributes` (`id`, `category_code`) | L'attribut appartient à la catégorie du produit |
| `document_versions` | (`document_id`, `document_category`) | `documents` (`id`, `category`) | Permet de borner la visibilité `PUBLIC` aux médias (§3.2) |
| `exporter_profiles` | (`public_slug`, `organization_id`) ; (`logo_document_id`, `organization_id`) | `exporter_public_slugs` (`slug`, `organization_id`) ; `documents` (`id`, `owner_organization_id`) | Le slug et le logo appartiennent à l'organisation |
| `exporter_certifications` | (`proof_document_id`, `organization_id`) | `documents` (`id`, `owner_organization_id`) | La preuve est un document de l'organisation |
| `role_permissions` | (`role_id`, `scope`) et (`permission_id`, `scope`) | `roles` (`id`, `scope`), `permissions` (`id`, `scope`) | Une permission de plateforme n'est jamais liée à un rôle d'organisation (S-12) |
| `platform_role_assignments` | (`role_id`, `role_scope`) | `roles` (`id`, `scope`) | Seul un rôle de plateforme est attribué (`CHECK role_scope = 'PLATFORM'`) |

Règles applicatives, testées, **à réexaminer au Jour 24** (option : dénormaliser `rfq_id` et ajouter des clés composites) :
- `quotation_lines.rfq_item_id` appartient à la RFQ de la quotation ;
- `negotiation_offers.based_on_quotation_version_id` et `trades.accepted_offer_id` appartiennent à la quotation concernée ;
- `trade_items.quotation_line_id` appartient à la version acceptée ; `negotiation_offer_lines.quotation_line_id` appartient à la version de base de l'offre ;
- le canal d'une conversation est cohérent avec ses participants et avec le type de convention (data-model §5.8, sous réserve de Q-99).

## 3. Contraintes `CHECK`

### 3.1 Formats et domaines

| Domaine | Contrainte |
|---|---|
| Devise | `currency ~ '^[A-Z]{3}$'` ; liste des devises admises : application (Q-65) |
| Pays | `~ '^[A-Z]{2}$'` |
| Port | `~ '^[A-Z]{2}[A-Z2-9]{3}$'` (UN/LOCODE) |
| Référence lisible | `reference ~ '^(DEMO-)?(RFQ\|MSQ\|MST)-[0-9]{4}-[A-Z0-9]{6}$'`, préfixe propre à la table (Q-37, S-57) |
| Codes et statuts | `col IN (...)` avec la liste de [data-model.md](data-model.md) §5 |
| Montants | `>= 0` (prix, totaux, coûts) ; `> 0` (montant d'un Payment Record) |
| Quantités | `> 0` |
| Taux | `commission_rate BETWEEN 0 AND 100` ; `rate > 0` ; règle de prix en pourcentage : `value <= 100` |
| Score | `score BETWEEN 0 AND 100` (matching) ; `score BETWEEN 1 AND 5` (avis, Q-59) |
| Textes exposés | `char_length(col) <= n`, avec `n` égal à la limite de validation de l'API |

### 3.2 Dépendances entre colonnes

| Règle | Exemple |
|---|---|
| Tout ou rien | `num_nulls(price_indication_amount, price_indication_currency, price_indication_unit) IN (0, 3)` ; idem pour le MOQ, le prix cible, les quantités, les clés composites facultatives |
| Intervalle | `target_delivery_from <= target_delivery_to` ; `valid_from < valid_to` |
| Une seule valeur | `product_attribute_values` : `num_nonnulls(value_decimal, value_integer, value_text, value_boolean, value_enum_code) = 1` |
| Règle de prix | `(method = 'FIXED_PER_UNIT') = (value_currency IS NOT NULL AND price_unit IS NOT NULL)` |
| Champs obligatoires selon le statut | `verification_records` : `status = 'PENDING' OR (decided_at IS NOT NULL AND decided_by_user_id IS NOT NULL)`. `payment_records` : `CONFIRMED` ⇒ `confirmed_*` ; `FAILED` ⇒ `failed_*` ; `REFUNDED` ⇒ `refunded_*`. `bank_details`, `receiving_accounts` : `status IN ('PENDING_VERIFICATION', 'REJECTED', 'WITHDRAWN') OR (verified_by_user_id IS NOT NULL AND verified_at IS NOT NULL AND effective_from IS NOT NULL)` |
| Statut de compte par capacité | `organization_capabilities` : `(capability = 'BUYER' AND account_status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'BLOCKED')) OR (capability = 'EXPORTER' AND account_status IN ('PENDING_ACTIVATION', 'ACTIVE', 'SUSPENDED', 'CLOSED'))` (CF-02) |
| Propriétaire d'un document | `(owner_kind = 'ORGANIZATION') = (owner_organization_id IS NOT NULL)` |
| Visibilité publique | `document_versions` : `visibility <> 'PUBLIC' OR document_category = 'MARKETPLACE_MEDIA'` |
| Participant MadaSource | `conversation_participants` : `(side = 'MADASOURCE') = (organization_id IS NULL)` |
| Portée des permissions | `permissions` : `permission_set IS NULL OR scope = 'PLATFORM'` |
| Type de convention (provisoire) | `(commercial_model = 'RESELLER' AND kind IN ('SALE', 'SUPPLY')) OR (commercial_model = 'INTERMEDIARY' AND kind = 'DIRECT')` |
| Visibilité d'un événement (provisoire) | `agreement_kind IS DISTINCT FROM 'SALE' OR visibility IN ('BUYER_VISIBLE', 'INTERNAL_ONLY')`, et symétriquement pour `SUPPLY` (`EXPORTER_VISIBLE`) |
| Sens d'un paiement (provisoire) | `(agreement_kind, direction) IN (('SALE', 'BUYER_TO_MADASOURCE'), ('SUPPLY', 'MADASOURCE_TO_EXPORTER'), ('DIRECT', 'BUYER_TO_EXPORTER'))` (S-40) |
| Compte d'un paiement | `(receiving_account_id IS NOT NULL) = (direction = 'BUYER_TO_MADASOURCE')` ; `(beneficiary_bank_details_id IS NOT NULL) = (direction = 'MADASOURCE_TO_EXPORTER')` |
| Retour après exception | `status_before_exception` : même liste que `status`, sauf `DISPUTED` et `ON_HOLD` |

### 3.3 Parties distinctes (S-36)

`CHECK (buyer_organization_id <> exporter_organization_id)` sur `rfq_recipients`, `quotations`, `trades`, `reviews`, `sample_requests`. Avec les clés composites de §2.1, une organisation à double capacité (Q-09) ne peut jamais être les deux parties d'un même objet.

Limite : ce contrôle porte sur les **organisations**. Un **utilisateur** membre des deux organisations (Q-74) est refusé par le service, pas par la base (Q-98).

### 3.4 Séparation des tâches

| Table | Contrainte | Source |
|---|---|---|
| `payment_records` | `confirmed_by_user_id IS NULL OR (confirmed_by_user_id IS DISTINCT FROM recorded_by_user_id AND confirmed_by_user_id IS DISTINCT FROM processing_by_user_id)` ; `refunded_by_user_id IS NULL OR refunded_by_user_id IS DISTINCT FROM recorded_by_user_id` ; remboursement par un autre que le confirmateur : proposé | S-34 ; Q-56, Q-88 |
| `bank_details`, `receiving_accounts` | `verified_by_user_id IS NULL OR verified_by_user_id IS DISTINCT FROM created_by_user_id`, combiné au contrôle de statut de §3.2 (une ligne vérifiée a toujours un vérificateur) | S-44 |
| `platform_role_assignments` | `granted_by_user_id IS DISTINCT FROM user_id` (pas d'auto-attribution) ; `granted_by_user_id IS NOT NULL OR is_bootstrap`, avec une seule ligne `is_bootstrap` (index unique partiel) | S-08 |

Ces contrôles ne valent que si les colonnes d'acteur ne peuvent pas être réécrites après coup : droits par colonne (§6.2) et, à évaluer au Jour 33, déclencheur d'écriture unique.

Avec un seul administrateur humain, ces contrôles **bloquent** l'activité au lieu de la protéger : un compte de réception ne peut pas être vérifié par son créateur, donc aucun paiement acheteur n'est enregistrable en Modèle A (`receiving_account_id` obligatoire), et aucun paiement ne peut être confirmé. Le nombre minimal d'administrateurs est donc une décision à prendre avant le Jour 33 (R-32, Q-101).

### 3.5 Évolution des listes de statuts

L'autogénération d'Alembic **ne compare pas** les contraintes `CHECK` : modifier une liste de statuts dans le code ne produit aucune migration, et une vérification automatique d'Alembic resterait verte. Règles :
- toute modification d'une liste de valeurs fait l'objet d'une **migration écrite à la main**, relue (skill `database-migrations`) ;
- un test compare les listes de l'application aux contraintes présentes en base (`pg_constraint`) ;
- **ajout** d'une valeur : remplacement de la contrainte dans une même migration ; sur les grosses tables (`audit_logs`, `trade_events`, `documents`), `ADD CONSTRAINT … NOT VALID`, puis `VALIDATE CONSTRAINT` ;
- **retrait** ou **renommage** : migration de données explicite d'abord, jamais silencieuse. Les valeurs déjà présentes dans les historiques immuables (`trade_events.from_status`…) ne sont pas réécrites.

L'échelle des montants (Q-08) doit être fixée avant la première migration monétaire : changer l'échelle d'une colonne `numeric` réécrit la table.

## 4. Unicité

### 4.1 Contraintes d'unicité

| Table | Colonnes | Raison |
|---|---|---|
| `users` | `lower(email)` (index unique sur expression) | Un compte par email, sans tenir compte de la casse ; l'anonymisation écrit une valeur de remplacement unique |
| `refresh_tokens`, `email_verification_tokens`, `password_reset_tokens`, `organization_invitations` | `token_hash` | Recherche du jeton |
| `organization_capabilities` | (`organization_id`, `capability`) | Q-09 |
| `organization_memberships` | (`organization_id`, `user_id`) | Q-74 |
| `roles`, `permissions` | `code` ; (`id`, `scope`) | Clé composite §2.1 |
| `documents` | (`id`, `category`) ; (`id`, `owner_organization_id`) | Clés composites §2.1 |
| `document_versions` | (`document_id`, `version_no`) ; `storage_key` | |
| `conversations` | (`context_type`, `context_id`, `channel`) | Un fil par contexte et par canal (data-model §5.8) |
| `conversation_participants` | (`conversation_id`, `organization_id`) | |
| `exporter_public_slugs` | (`slug`, `organization_id`) | Clé composite §2.1 |
| `bank_details` | (`id`, `organization_id`) | Clé composite §2.1 (paiements) |
| `exporter_profiles` | `public_slug` | S-54 |
| `category_attributes` | (`category_code`, `code`) ; (`id`, `category_code`) | Clé composite §2.1 |
| `products` | (`id`, `category_code`) | Clé composite §2.1 |
| `rfqs`, `quotations`, `trades` | `reference` | Q-37 |
| `rfqs` | (`id`, `buyer_organization_id`) | Clé composite §2.1 |
| `rfq_items` | (`rfq_id`, `line_no`) | |
| `rfq_recipients` | (`rfq_id`, `exporter_organization_id`) ; (`id`, `rfq_id`) ; (`id`, `rfq_id`, `exporter_organization_id`) | Un envoi par exportateur ; clés composites |
| `quotations` | (`rfq_id`, `exporter_organization_id`) ; (`id`, `rfq_id`, `buyer_organization_id`, `exporter_organization_id`) | Une quotation par exportateur et par RFQ (Q-94) ; clé composite |
| `quotation_versions` | (`quotation_id`, `version_no`) ; (`id`, `quotation_id`) | Clé composite |
| `quotation_lines` | (`quotation_version_id`, `line_no`) ; (`quotation_version_id`, `rfq_item_id`) ; (`id`, `rfq_item_id`) | Clé composite |
| `pricing_rule_versions`, `matching_configs` | `version_no` | |
| `negotiations` | `quotation_id` | Une négociation par quotation ; à revoir si Q-39 permet une reprise |
| `negotiation_offers` | (`negotiation_id`, `sequence_no`) | Ordre des propositions |
| `negotiation_offer_lines` | (`offer_id`, `quotation_line_id`) | |
| `trades` | `quotation_id` ; (`id`, `buyer_organization_id`, `exporter_organization_id`) ; (`id`, `exporter_organization_id`) ; (`id`, `commercial_model`) | Un Trade par quotation (BR-TRD-03), idempotence de l'acceptation ; clés composites |
| `trade_items` | (`id`, `trade_id`) | Clé composite |
| `trade_agreements` | (`trade_id`, `kind`) ; (`id`, `trade_id`) ; (`id`, `trade_id`, `kind`) | Une convention de chaque type ; clés composites |
| `match_runs` | (`id`, `rfq_id`) | Clé composite |
| `reviews` | (`trade_id`, `direction`) | BR-REP-02 |
| `rfq_matches` | (`match_run_id`, `exporter_organization_id`) | |
| `favorites` | (`user_id`, `organization_id`, `target_type`, `target_id`) | |

### 4.2 Index uniques partiels

| Table | Index | Règle |
|---|---|---|
| `organization_invitations` | (`organization_id`, `lower(email)`) `WHERE status = 'PENDING'` | Une invitation en attente par email et par organisation (proposé). Une invitation expirée reste `PENDING` (expiration calculée, D-23) : le service la révoque sous verrou avant d'en créer une nouvelle |
| `platform_role_assignments` | (`user_id`, `role_id`) `WHERE revoked_at IS NULL` ; `((true))` `WHERE is_bootstrap` | Une attribution active ; une seule attribution initiale sans auteur |
| `conversation_participants` | (`conversation_id`) `WHERE organization_id IS NULL` | Une seule ligne MadaSource par conversation |
| `verification_records` | (`organization_id`) `WHERE status = 'PENDING'` | Une demande en cours à la fois |
| `bank_details` | (`organization_id`, `currency`) `WHERE status = 'PENDING_VERIFICATION'` ; (`organization_id`, `currency`, `effective_from`) `WHERE status = 'VERIFIED'` | Une modification en attente par devise ; pas deux comptes vérifiés à la même date de prise d'effet. Le compte courant est calculé à la lecture (data-model §5.11) |
| `receiving_accounts` | (`currency`) `WHERE status = 'PENDING_VERIFICATION'` ; (`currency`, `effective_from`) `WHERE status = 'VERIFIED'` | Idem |
| `negotiation_offers` | (`negotiation_id`) `WHERE status = 'PENDING'` ; (`negotiation_id`) `WHERE status = 'ACCEPTED'` | Une proposition en attente ; une seule acceptation (BR-NEG-04) |
| `trade_items` | (`rfq_item_id`) `WHERE released_at IS NULL` | Une ligne de RFQ attribuée à un seul Trade non annulé ; à revoir avec Q-26 |
| `matching_configs` | `((true))` `WHERE status = 'ACTIVE'` | Une configuration active |
| `pricing_rule_versions` | Aucun index simple ne suffit (chevauchement de périodes) | Non-chevauchement des règles actives d'une même portée : règle applicative ; contrainte `EXCLUDE` possible, mais elle exige l'extension `btree_gist`, à justifier au Jour 24 |
| `disputes` | (`trade_id`, `opened_by_organization_id`) `WHERE status NOT IN ('RESOLVED', 'CLOSED')` | Un litige ouvert par partie et par Trade (proposé, Q-92) |

### 4.3 Références lisibles (Q-37)

La référence est générée par l'application (suite aléatoire, générateur cryptographique). En cas de collision, `uq_<table>_reference` refuse l'insertion. Comme une violation de contrainte annule toute la transaction PostgreSQL, l'**instruction `INSERT` seule** est placée dans un point de sauvegarde (`begin_nested`). Un retour au point de sauvegarde libère les verrous pris après lui : aucun verrou n'est donc pris entre l'ouverture du point de sauvegarde et l'insertion. En cas de violation de **cette** contrainte, et d'elle seule, la transaction revient au point de sauvegarde et réessaie avec une nouvelle valeur (3 tentatives au plus). Toute autre violation remonte normalement.

## 5. Index de lecture

Index proposés pour les listes de la roadmap. Ils seront confirmés par `EXPLAIN` sur des données de test (Audit C), et aucun index n'est ajouté sans requête qui l'utilise.

| Table | Index | Requête |
|---|---|---|
| `audit_logs` | (`object_type`, `object_id`, `occurred_at`) ; (`actor_user_id`, `occurred_at`) ; (`occurred_at`) | Historique d'un objet, d'un acteur ; consultation admin par période |
| `sessions` | (`user_id`) `WHERE revoked_at IS NULL` | Sessions actives (révocation, S-05) |
| `notifications` | (`recipient_user_id`, `created_at`, `id`) ; (`recipient_user_id`) `WHERE read_at IS NULL` | Flux par curseur ; compteur non lus |
| `documents` | (`context_type`, `context_id`) ; (`owner_organization_id`) ; (`related_trade_id`) | Documents d'un objet, d'une organisation, d'un Trade |
| `messages` | (`conversation_id`, `created_at`, `id`) | Flux par curseur |
| `verification_records` | (`organization_id`, `level`) `WHERE status = 'VERIFIED'` ; (`organization_id`, `decided_at` DESC) | Niveau acquis le plus haut et dernière décision (statut calculé, data-model §5.10), lus par le matching et le marketplace ; à confirmer par `EXPLAIN` (Audit C) |
| `products` | (`category_code`, `published_at`) `WHERE status = 'PUBLISHED'` ; (`organization_id`, `status`) ; GIN (`certification_codes`) | Marketplace ; catalogue de l'exportateur ; filtre par certification |
| `product_attribute_values` | (`attribute_id`, `value_enum_code`) ; (`attribute_id`, `value_decimal`) | Filtres d'attributs du marketplace |
| `rfqs` | (`buyer_organization_id`, `status`, `created_at`) | Liste des RFQ de l'acheteur |
| `rfq_recipients` | (`exporter_organization_id`, `status`, `sent_at`) | Inbox de l'exportateur (RJ 21) |
| `quotations` | (`exporter_organization_id`, `status`) | Quotations de l'exportateur |
| `trades` | (`buyer_organization_id`, `status`) ; (`exporter_organization_id`, `status`) ; (`status`, `created_at`) | Listes par partie ; vue admin |
| `trade_events` | (`trade_id`, `occurred_at`) | Timeline |
| `payment_records` | (`trade_id`) ; (`status`, `recorded_at`) `WHERE status IN ('PENDING', 'PROCESSING')` | Paiements d'un Trade ; file de confirmation admin |
| `shipments`, `tracking_events` | (`trade_id`) ; (`shipment_id`, `occurred_at`) | |
| `exception_cases` | (`status`, `priority`) `WHERE status NOT IN ('RESOLVED', 'CLOSED')` ; (`assigned_to_user_id`) | File des exceptions |
| `rfq_matches` | (`rfq_id`, `score`) | Classement des candidats |
| `outbox_messages` | (`status`, `next_attempt_at`) `WHERE status = 'PENDING'` | Envoi différé (conditionnel) |
| Tables à curseur | (`created_at`, `id`) ou (`occurred_at`, `id`) | Pagination stable ([api-conventions.md](api-conventions.md#6-pagination-tri-et-filtres)) |

Pas d'index sur `quotation_versions.expires_at` : il couvrirait toutes les versions historiques. La liste des quotations proches de l'expiration part de la version courante ; un index est ajouté seulement si `EXPLAIN` le justifie.

## 6. Immuabilité et droits

### 6.1 Rôles PostgreSQL (security-design §19)

| Rôle | Droits | Usage |
|---|---|---|
| `madasource_migrator` | Propriétaire du schéma, DDL | Alembic seulement |
| `madasource_app` | DML sur les tables, sans DDL, sans droit de propriétaire | Application (API, tâches) |

Les noms de rôles sont des propositions ; ils seront fixés au Jour 4 ou au Jour 6. Aucun rôle superutilisateur n'est utilisé par l'application.

### 6.2 Droits de `madasource_app`

Les droits par colonne sont pris en charge par PostgreSQL (`GRANT UPDATE (col, ...)`). Une table verrouillée par `FOR NO KEY UPDATE` doit garder au moins une colonne modifiable : ce verrou exige le droit `UPDATE`.

| Table | Droits | Remarque |
|---|---|---|
| `audit_logs` | `INSERT`, `SELECT` | BR-AUD-02 ; aucun `UPDATE` ni `DELETE` (Jour 12) |
| `trade_events`, `tracking_events`, `exception_notes`, `rfq_matches`, `quotation_versions`, `quotation_lines`, `quotation_version_costs`, `quotation_version_financials`, `external_costs`, `negotiation_offer_lines`, `negotiation_offer_financials`, `offer_external_costs`, `trade_agreement_lines`, `trade_financials` | `INSERT`, `SELECT` | Historiques et termes figés (BR-NEG-02, BR-TRD-05, BR-TRD-07, S-43) |
| `trade_items` | `INSERT`, `SELECT`, `UPDATE (released_at)` | Termes figés ; libération d'une ligne de RFQ après annulation |
| `trade_agreements` | `INSERT`, `SELECT`, `UPDATE (payment_status, updated_at)` | Termes figés ; une modification contractuelle future passera par une nouvelle convention (À VALIDER) |
| `trades` | `INSERT`, `SELECT`, `UPDATE` sur les colonnes de cycle de vie seulement (`status`, `status_before_exception`, `shipment_summary`, `completed_at`, `cancelled_at`, `updated_at`) | Parties, quotation, version, modèle commercial et référence figés |
| `negotiation_offers` | `INSERT`, `SELECT`, `UPDATE (status, decided_at, decided_by_user_id)` | |
| `payment_records` | `INSERT`, `SELECT`, `UPDATE` sur `status` et les colonnes `processing_*`, `confirmed_*`, `failed_*`, `refunded_*`, `updated_at` | Convention, sens, montant, devise, comptes et saisie figés (S-34) |
| `bank_details`, `receiving_accounts` | `INSERT`, `SELECT`, `UPDATE` sur `status`, `verified_*`, `rejected_*`, `effective_from`, `updated_at` | Les colonnes chiffrées ne se réécrivent jamais sur place : un changement crée une nouvelle ligne, soumise à S-44 |
| `document_versions` | `INSERT`, `SELECT`, `UPDATE (visibility, visibility_changed_at, visibility_changed_by_user_id, scan_status)` | La visibilité d'un justificatif de paiement n'est pas modifiable (règle du service, data-model §5.17) |
| `refresh_tokens` | `INSERT`, `SELECT`, `UPDATE (consumed_at, replaced_by_id)` | |
| `platform_role_assignments` | `INSERT`, `SELECT`, `UPDATE (revoked_at, revoked_by_user_id)` | Rôle, auteur et attribution initiale figés : les contrôles de §3.4 ne sont pas contournables par réécriture |
| `messages` | `INSERT`, `SELECT` ; `UPDATE (body, edited_at)` seulement si Q-50 autorise la modification par l'auteur | |
| Colonnes cibles d'une clé composite | Exclues de tout droit `UPDATE` (`rfqs.buyer_organization_id`, parties des quotations et des Trades, `trade_agreements.kind`, `documents.category`, `products.category_code`, `roles.scope`, `permissions.scope`…) | PostgreSQL les traite comme des colonnes de clé : leur modification prendrait un verrou `FOR UPDATE` qui bloque les insertions filles |
| `DELETE` | Seulement sur : tables d'association (`role_permissions`, `message_attachments`, `favorites`) ; lignes d'un brouillon (`rfq_items` d'une RFQ `DRAFT`, `product_attribute_values` facultatives) ; données temporaires (jetons expirés, `outbox_messages` envoyés ou abandonnés) | Pas de suppression physique dans le workflow normal |
| Toutes les autres tables | `SELECT`, `INSERT`, `UPDATE` | |

Ces droits protègent contre une erreur de code, pas contre un administrateur de la base : ce n'est pas une preuve d'intégrité au sens juridique. Le chaînage du journal d'audit reste à évaluer (security-design §18).

### 6.3 Effacement et tables immuables

Le droit à l'effacement (Q-68) s'applique d'abord par **anonymisation** de `users` et des profils. Mais plusieurs tables immuables contiennent du **texte libre** qui peut citer une personne :
- `trade_events.comment`, `tracking_events.comment` et `location`, `exception_notes.body` ;
- `negotiation_offers.comment`, `quotation_versions.additional_conditions` ;
- `document_versions.original_filename`.

Le rôle applicatif ne peut pas les modifier. Proposition, **À VALIDER avec un juriste (Q-68)** : une procédure d'effacement exceptionnelle, exécutée par un rôle dédié disposant d'un `UPDATE` limité à ces colonnes, déclenchée par une demande `privacy_requests` approuvée, et auditée (trace minimale, sans recopie du texte effacé).

## 7. Concurrence

Règles du Jour 2 (D-09), appliquées au modèle. L'ordre suit les niveaux des modules : la ligne de plus bas niveau est verrouillée en premier.

| Opération | Lignes verrouillées (`FOR NO KEY UPDATE`), dans l'ordre | Contrainte de dernier rempart |
|---|---|---|
| Modification d'adhésion (rôle, retrait, statut) | `organizations` | Invariant « au moins un OWNER » vérifié sous verrou |
| Révocation d'un rôle de plateforme | Ligne de l'administrateur concerné, puis relecture des administrateurs actifs | Au moins un administrateur actif (règle applicative) |
| Changement de coordonnées bancaires | `exporter_profiles` | `uq_bank_details_one_pending` ; une nouvelle demande est refusée tant qu'une autre est en attente, le demandeur peut retirer la sienne (`WITHDRAWN`) |
| Envoi d'une RFQ aux exportateurs | `rfqs` | `uq_rfq_recipients_rfq_id_exporter_organization_id` |
| Création d'une quotation ou d'une version | `rfqs`, puis `quotations` | `uq_quotations_rfq_id_exporter_organization_id`, `uq_quotation_versions_quotation_id_version_no` |
| Contre-offre | `rfqs` (si son statut change), puis `negotiations` ; relecture des offres **après** le verrou (`populate_existing`) | `uq_negotiation_offers_one_pending` |
| Acceptation et création du Trade | `rfqs`, puis `quotations`, puis `negotiations` | `uq_trades_quotation_id`, `uq_trade_items_rfq_item_active`, `uq_negotiation_offers_one_accepted` |
| Transition du Trade | `trades` | — |
| Paiement (saisie, confirmation, échec, remboursement) | `trades`, puis `payment_records` | `ck_payment_records_confirmer_distinct` |
| Expédition, suivi, exception, litige qui modifient le Trade | `trades`, puis `shipments`, `exception_cases` ou `disputes` | — |

Règle générale : toute écriture du statut d'une RFQ (`QUOTATIONS_RECEIVED`, `NEGOTIATING`, `ACCEPTED`, `CLOSED`, Q-95) verrouille `rfqs` **en premier**. Sans cela, une contre-offre qui verrouillerait `negotiations` puis écrirait `rfqs` entrerait en interblocage avec une acceptation (`rfqs` → `quotations` → `negotiations`). Le verrou sur `rfqs` sérialise aussi les acceptations concurrentes de lignes d'une même RFQ (Q-25, Q-26).

Compteurs : `failed_login_count` est incrémenté par une instruction atomique (`SET failed_login_count = failed_login_count + 1`), hors transaction principale (D-29).

## 8. Points à valider

| Sujet | Référence |
|---|---|
| Précision `numeric(19,4)` et arrondis, avant la première migration monétaire | Q-08 |
| Une quotation par exportateur et par RFQ | Q-94 |
| Répartition d'une ligne de RFQ entre exportateurs ; libération après annulation | Q-26 |
| Reprise d'une négociation close | Q-39 |
| Clés composites de cohérence des lignes et des offres | Jour 24 |
| Contrainte `EXCLUDE` (extension `btree_gist`) | Jour 24 |
| Déclencheur d'écriture unique sur les colonnes d'acteur des paiements | Jour 33 |
| Devises différentes entre vente et approvisionnement (taux figé) | Q-65 |
| Lignes affectées à chaque expédition (`shipment_items`) | Q-57 |
| Statut des lignes de RFQ | Q-95 |
| Procédure d'effacement des textes immuables | Q-68 |
| Utilisateur membre des deux parties | Q-98 |
| Canaux de messagerie en Modèle A (conflit avec le CdC §28) | Q-99, CF-10 |
| Compte admin titulaire d'une adhésion cliente | Q-100 |
| Nombre minimal d'administrateurs (séparation des tâches) | Q-101, R-32 |
| Noms des rôles PostgreSQL | Jours 4 et 6 |
| Version de PostgreSQL | D-15 (Jour 4) ; ce document n'utilise rien au-delà de PostgreSQL 13 |
| Toutes les contraintes du Trade | Q-82 |
