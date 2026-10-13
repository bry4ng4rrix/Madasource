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

Les noms PostgreSQL sont limités à 63 caractères. Un nom plus long est raccourci explicitement dans la déclaration, jamais tronqué par la base. La traduction des violations d'intégrité ([error-handling.md](error-handling.md) §6) reconnaît une contrainte par son **nom** : un nom de contrainte ne change pas sans migration et sans mise à jour de cette correspondance.

## 2. Clés étrangères

| Règle | Détail |
|---|---|
| `ON DELETE RESTRICT` partout | Aucune suppression en cascade. Une suppression physique qui laisserait un historique orphelin échoue. |
| `ON UPDATE` | Sans objet : une clé primaire n'est jamais modifiée. |
| Direction | Vers une table du même module, d'un module de niveau inférieur ou du socle (D-07). Vérifié sur l'ERD par un script de contrôle (Jour 3), puis par le test d'architecture (Jour 7). |
| Index | Chaque colonne de clé étrangère est indexée, sauf si elle est la première colonne d'un autre index ou d'une contrainte d'unicité. PostgreSQL ne crée pas ces index automatiquement ; sans eux, `RESTRICT` et les jointures parcourent la table enfant. |
| Références polymorphes | `context_type`/`context_id` et `object_type`/`object_id` n'ont pas de clé étrangère. L'existence de l'objet est vérifiée par le module propriétaire (P-01) au moment de l'écriture. Index composite (`context_type`, `context_id`). |
| Identifiants d'acteur dans l'audit | `audit_logs.actor_user_id` n'a pas de clé étrangère : l'audit reste lisible et immuable même si le compte est anonymisé (Q-68). |

### 2.1 Clés étrangères composites (cohérence entre parties)

Elles garantissent qu'une organisation dénormalisée sur une ligne est bien celle de l'objet parent. Le `CHECK` de la même ligne garantit ensuite que l'acheteur et l'exportateur sont différents (S-36, Q-09).

| Table enfant | Colonnes | Table cible (unicité requise) | Effet |
|---|---|---|---|
| `rfq_recipients` | (`rfq_id`, `buyer_organization_id`) | `rfqs` (`id`, `buyer_organization_id`) | Le destinataire connaît l'acheteur réel de la RFQ |
| `quotations` | (`rfq_id`, `buyer_organization_id`) | `rfqs` (`id`, `buyer_organization_id`) | |
| `quotations` | (`recipient_id`, `rfq_id`, `exporter_organization_id`) | `rfq_recipients` (`id`, `rfq_id`, `exporter_organization_id`) | La quotation vient d'un destinataire de **cette** RFQ |
| `trades` | (`quotation_id`, `buyer_organization_id`, `exporter_organization_id`) | `quotations` (`id`, `buyer_organization_id`, `exporter_organization_id`) | Les parties du Trade sont celles de la quotation |
| `reviews` | (`trade_id`, `buyer_organization_id`, `exporter_organization_id`) | `trades` (`id`, `buyer_organization_id`, `exporter_organization_id`) | L'évaluation porte sur les parties du Trade |
| `product_attribute_values` | (`product_id`, `category_code`) et (`attribute_id`, `category_code`) | `products` (`id`, `category_code`), `category_attributes` (`id`, `category_code`) | L'attribut appartient à la catégorie du produit |
| `payment_records` | (`agreement_id`, `agreement_kind`) | `trade_agreements` (`id`, `kind`) | Le sens du paiement est cohérent avec la convention (`CHECK` en §3) |

Cohérence des lignes, **à arbitrer au Jour 24** : une ligne de quotation (`quotation_lines.rfq_item_id`) et une ligne de Trade (`trade_items.rfq_item_id`) doivent appartenir à la RFQ de leur parent. Deux options :
- règle applicative, testée (proposition par défaut) ;
- dénormalisation de `rfq_id` dans `quotation_versions`, `quotation_lines` et `trade_items`, avec des clés composites vers `rfq_items` (`id`, `rfq_id`). Plus sûr, mais trois clés composites de plus.

## 3. Contraintes `CHECK`

### 3.1 Formats et domaines

| Domaine | Contrainte |
|---|---|
| Devise | `currency ~ '^[A-Z]{3}$'` ; liste des devises admises : application (Q-65) |
| Pays | `~ '^[A-Z]{2}$'` |
| Port | `~ '^[A-Z]{2}[A-Z2-9]{3}$'` (UN/LOCODE) |
| Référence lisible | `reference ~ '^(DEMO-)?(RFQ|MSQ|MST)-[0-9]{4}-[A-Z0-9]{6}$'`, préfixe propre à la table (Q-37, S-57) |
| Codes et statuts | `col IN (...)` avec la liste de [data-model.md](data-model.md) §5 |
| Montants | `>= 0` (prix, totaux, coûts) ; `> 0` (montant d'un Payment Record) |
| Quantités | `> 0` |
| Taux | `commission_rate BETWEEN 0 AND 100` ; `rate > 0` |
| Score | `score BETWEEN 0 AND 100` (matching) ; `score BETWEEN 1 AND 5` (avis, Q-59) |
| Textes exposés | `char_length(col) <= n`, avec `n` égal à la limite de validation de l'API |

### 3.2 Groupes et dépendances entre colonnes

| Règle | Exemple |
|---|---|
| Tout ou rien | `num_nulls(price_indication_amount, price_indication_currency, price_indication_unit) IN (0, 3)` ; idem pour le MOQ, le prix cible, les quantités |
| Intervalle | `target_delivery_from <= target_delivery_to` ; `valid_from < valid_to` |
| Une seule valeur | `product_attribute_values` : `num_nonnulls(value_decimal, value_integer, value_text, value_boolean, value_enum_code) = 1` |
| Champ obligatoire selon le statut | `verification_records` : `status = 'PENDING' OR (decided_at IS NOT NULL AND decided_by_user_id IS NOT NULL)` ; `payment_records` : `status <> 'CONFIRMED' OR (confirmed_at IS NOT NULL AND confirmed_by_user_id IS NOT NULL)` |
| Statut de compte par capacité | `organization_capabilities` : `(capability = 'BUYER' AND account_status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'BLOCKED')) OR (capability = 'EXPORTER' AND account_status IN ('PENDING_ACTIVATION', 'ACTIVE', 'SUSPENDED', 'CLOSED'))` (CF-02) |
| Propriétaire d'un document | `(owner_kind = 'ORGANIZATION') = (owner_organization_id IS NOT NULL)` |
| Parties d'une convention (provisoire) | `SALE` : vendeur `MADASOURCE`, acheteur `ORGANIZATION` ; `SUPPLY` : vendeur `ORGANIZATION`, acheteur `MADASOURCE` ; `DIRECT` : deux `ORGANIZATION` ; `(x_kind = 'ORGANIZATION') = (x_organization_id IS NOT NULL)` |
| Sens d'un paiement (provisoire) | `(agreement_kind, direction) IN (('SALE', 'BUYER_TO_MADASOURCE'), ('SUPPLY', 'MADASOURCE_TO_EXPORTER'), ('DIRECT', 'BUYER_TO_EXPORTER'))` (S-40) |

### 3.3 Parties distinctes (S-36)

`CHECK (buyer_organization_id <> exporter_organization_id)` sur `rfq_recipients`, `quotations`, `trades`, `reviews`, `sample_requests`. Avec les clés composites de §2.1, une organisation à double capacité (Q-09) ne peut jamais être les deux parties d'un même objet.

### 3.4 Séparation des tâches

| Table | Contrainte | Source |
|---|---|---|
| `payment_records` | `confirmed_by_user_id IS DISTINCT FROM recorded_by_user_id` et `confirmed_by_user_id IS DISTINCT FROM processing_by_user_id`, quand `confirmed_by_user_id` est renseigné ; même règle pour `refunded_by_user_id` | S-34 (double validation : Q-88) |
| `bank_details`, `receiving_accounts` | `verified_by_user_id IS DISTINCT FROM created_by_user_id`, quand `verified_by_user_id` est renseigné | S-44 |

`IS DISTINCT FROM` est la forme correcte en présence de valeurs nulles ; elle est combinée à `confirmed_by_user_id IS NULL OR ...`.

### 3.5 Évolution des listes de statuts

Une liste de valeurs change par migration :
- **ajout** d'une valeur : remplacement de la contrainte `CHECK` dans une même migration, sans effet sur les données ;
- **retrait** ou **renommage** : migration de données explicite d'abord, relue (skill `database-migrations`), jamais silencieuse. Les valeurs déjà présentes dans les historiques immuables (`trade_events.from_status`…) ne sont pas réécrites.

## 4. Unicité

### 4.1 Contraintes d'unicité simples

| Table | Colonnes | Raison |
|---|---|---|
| `users` | `lower(email)` (index unique sur expression) | Un compte par email, sans tenir compte de la casse |
| `refresh_tokens`, `email_verification_tokens`, `password_reset_tokens`, `organization_invitations` | `token_hash` | Recherche du jeton |
| `organization_capabilities` | (`organization_id`, `capability`) | Q-09 |
| `organization_memberships` | (`organization_id`, `user_id`) | Q-74 |
| `roles`, `permissions` | `code` | |
| `document_versions` | (`document_id`, `version_no`) ; `storage_key` | |
| `conversation_participants` | (`conversation_id`, `organization_id`) | |
| `exporter_profiles` | `public_slug` | S-54 |
| `category_attributes` | (`category_code`, `code`) ; (`id`, `category_code`) | Clé composite §2.1 |
| `products` | (`id`, `category_code`) | Clé composite §2.1 |
| `rfqs`, `quotations`, `trades` | `reference` | Q-37 |
| `rfqs` | (`id`, `buyer_organization_id`) | Clé composite §2.1 |
| `rfq_items` | (`rfq_id`, `line_no`) | |
| `rfq_recipients` | (`rfq_id`, `exporter_organization_id`) ; (`id`, `rfq_id`, `exporter_organization_id`) | Un envoi par exportateur ; clé composite |
| `quotations` | (`rfq_id`, `exporter_organization_id`) ; (`id`, `buyer_organization_id`, `exporter_organization_id`) | Une quotation par exportateur et par RFQ (Q-94) ; clé composite |
| `quotation_versions` | (`quotation_id`, `version_no`) | |
| `quotation_lines` | (`quotation_version_id`, `line_no`) ; (`quotation_version_id`, `rfq_item_id`) | |
| `pricing_rule_versions`, `matching_configs` | `version_no` | |
| `negotiations` | `quotation_id` | Une négociation par quotation |
| `negotiation_offers` | (`negotiation_id`, `sequence_no`) | Ordre des propositions |
| `negotiation_offer_lines` | (`offer_id`, `quotation_line_id`) | |
| `trades` | `quotation_id` ; (`id`, `buyer_organization_id`, `exporter_organization_id`) | Un Trade par quotation (BR-TRD-03), idempotence de l'acceptation ; clé composite |
| `trade_items` | `rfq_item_id` | Une ligne de RFQ attribuée une seule fois. **À revoir** si Q-26 autorise la répartition d'une même ligne entre exportateurs |
| `trade_agreements` | (`trade_id`, `kind`) ; (`id`, `kind`) | Une convention de chaque type ; clé composite |
| `reviews` | (`trade_id`, `direction`) | BR-REP-02 |
| `rfq_matches` | (`match_run_id`, `exporter_organization_id`) | |
| `favorites` | (`user_id`, `organization_id`, `target_type`, `target_id`) | |

### 4.2 Index uniques partiels

| Table | Index | Règle |
|---|---|---|
| `organization_invitations` | (`organization_id`, `lower(email)`) `WHERE status = 'PENDING'` | Une invitation en attente par email et par organisation (proposé) |
| `platform_role_assignments` | (`user_id`, `role_id`) `WHERE revoked_at IS NULL` | Une attribution active |
| `conversations` | (`context_type`, `context_id`) | Une conversation par contexte : paire RFQ–exportateur, convention de Trade… (proposé, S-31) |
| `conversation_participants` | (`conversation_id`) `WHERE organization_id IS NULL` | Une seule ligne MadaSource par conversation |
| `verification_records` | (`organization_id`) `WHERE status = 'PENDING'` | Une demande en cours à la fois |
| `bank_details` | (`organization_id`, `currency`) `WHERE status = 'ACTIVE'` ; idem `WHERE status = 'PENDING_VERIFICATION'` | Un compte actif et une modification en attente par devise (S-44) |
| `receiving_accounts` | (`currency`) `WHERE status = 'ACTIVE'` | |
| `negotiation_offers` | (`negotiation_id`) `WHERE status = 'PENDING'` ; (`negotiation_id`) `WHERE status = 'ACCEPTED'` | Une proposition en attente ; une seule acceptation (BR-NEG-04) |
| `matching_configs` | `((true))` `WHERE status = 'ACTIVE'` | Une configuration active |
| `pricing_rule_versions` | Aucun index simple ne suffit (chevauchement de périodes) | Non-chevauchement des règles actives d'une même portée : règle applicative ; contrainte `EXCLUDE` possible, mais elle exige l'extension `btree_gist`, à justifier au Jour 24 |
| `disputes` | (`trade_id`, `opened_by_organization_id`) `WHERE status NOT IN ('RESOLVED', 'CLOSED')` | Un litige ouvert par partie et par Trade (proposé, Q-92) |

### 4.3 Références lisibles (Q-37)

La référence est générée par l'application (suite aléatoire, générateur cryptographique). En cas de collision, `uq_<table>_reference` refuse l'insertion. Comme une violation de contrainte annule la transaction PostgreSQL entière, l'insertion est faite dans un **point de sauvegarde** (`begin_nested`). En cas de violation de **cette** contrainte, et d'elle seule, la transaction revient au point de sauvegarde et réessaie avec une nouvelle valeur (3 tentatives au plus). Toute autre violation remonte normalement.

## 5. Index de lecture

Index proposés pour les listes de la roadmap. Ils seront confirmés par `EXPLAIN` sur des données de test (Audit C), et aucun index n'est ajouté sans requête qui l'utilise.

| Table | Index | Requête |
|---|---|---|
| `audit_logs` | (`object_type`, `object_id`, `occurred_at`) ; (`actor_user_id`, `occurred_at`) ; (`occurred_at`) | Historique d'un objet, d'un acteur ; consultation admin par période |
| `sessions` | (`user_id`) `WHERE revoked_at IS NULL` | Sessions actives (révocation, S-05) |
| `notifications` | (`recipient_user_id`, `created_at`, `id`) ; (`recipient_user_id`) `WHERE read_at IS NULL` | Flux par curseur ; compteur non lus |
| `documents` | (`context_type`, `context_id`) ; (`owner_organization_id`) ; (`related_trade_id`) | Documents d'un objet, d'une organisation, d'un Trade |
| `messages` | (`conversation_id`, `created_at`, `id`) | Flux par curseur |
| `products` | (`category_code`, `published_at`) `WHERE status = 'PUBLISHED'` ; (`organization_id`, `status`) ; GIN (`certification_codes`) | Marketplace ; catalogue de l'exportateur ; filtre par certification |
| `product_attribute_values` | (`attribute_id`, `value_enum_code`) ; (`attribute_id`, `value_decimal`) | Filtres d'attributs du marketplace |
| `rfqs` | (`buyer_organization_id`, `status`, `created_at`) | Liste des RFQ de l'acheteur |
| `rfq_recipients` | (`exporter_organization_id`, `status`, `sent_at`) | Inbox de l'exportateur (RJ 21) |
| `quotations` | (`exporter_organization_id`, `status`) | Quotations de l'exportateur |
| `quotation_versions` | (`expires_at`) | Quotations proches de l'expiration (calcul à la lecture, D-23) |
| `trades` | (`buyer_organization_id`, `status`) ; (`exporter_organization_id`, `status`) ; (`status`, `created_at`) | Listes par partie ; vue admin |
| `trade_events` | (`trade_id`, `occurred_at`) | Timeline |
| `payment_records` | (`trade_id`) ; (`status`, `recorded_at`) `WHERE status IN ('PENDING', 'PROCESSING')` | Paiements d'un Trade ; file de confirmation admin |
| `shipments`, `tracking_events` | (`trade_id`) ; (`shipment_id`, `occurred_at`) | |
| `exception_cases` | (`status`, `priority`) `WHERE status NOT IN ('RESOLVED', 'CLOSED')` ; (`assigned_to_user_id`) | File des exceptions |
| `rfq_matches` | (`rfq_id`, `score`) | Classement des candidats |
| `outbox_messages` | (`status`, `next_attempt_at`) `WHERE status = 'PENDING'` | Envoi différé (conditionnel) |
| Tables à curseur | (`created_at`, `id`) ou (`occurred_at`, `id`) | Pagination stable ([api-conventions.md](api-conventions.md#6-pagination-tri-et-filtres)) |

## 6. Immuabilité et droits

### 6.1 Rôles PostgreSQL (security-design §19)

| Rôle | Droits | Usage |
|---|---|---|
| `madasource_migrator` | Propriétaire du schéma, DDL | Alembic seulement |
| `madasource_app` | DML sur les tables, sans DDL, sans droit de propriétaire | Application (API, tâches) |

Les noms de rôles sont des propositions ; ils seront fixés au Jour 4 ou au Jour 6. Aucun rôle superutilisateur n'est utilisé par l'application.

### 6.2 Tables immuables

| Table | `madasource_app` | Remarque |
|---|---|---|
| `audit_logs` | `INSERT`, `SELECT` seulement | BR-AUD-02 ; aucun `UPDATE` ni `DELETE` (Jour 12) |
| `trade_events`, `tracking_events`, `exception_notes`, `rfq_matches`, `quotation_versions`, `quotation_lines`, `quotation_version_costs`, `quotation_version_financials`, `external_costs`, `negotiation_offer_lines`, `negotiation_offer_financials`, `offer_external_costs`, `trade_agreement_lines`, `trade_financials` | `INSERT`, `SELECT` seulement | Historiques et termes figés (BR-NEG-02, BR-TRD-05, BR-TRD-07, S-43) |
| `trade_agreements` | `INSERT`, `SELECT` | Termes figés ; une modification contractuelle future passera par une nouvelle convention (À VALIDER) |
| `negotiation_offers` | `INSERT`, `SELECT`, `UPDATE` sur les colonnes `status`, `decided_at`, `decided_by_user_id` seulement | Droit `UPDATE` par colonne |
| `document_versions` | `INSERT`, `SELECT`, `UPDATE` sur `visibility`, `visibility_changed_at`, `visibility_changed_by_user_id`, `scan_status` seulement | |
| `refresh_tokens` | `INSERT`, `SELECT`, `UPDATE` sur `consumed_at`, `replaced_by_id` seulement | |
| Toutes les autres tables | `SELECT`, `INSERT`, `UPDATE` ; `DELETE` seulement sur les tables d'association et les données temporaires (`role_permissions`, `message_attachments`, `favorites`, jetons expirés, `outbox_messages` envoyés) | Pas de suppression physique dans le workflow normal |

Les droits par colonne sont pris en charge par PostgreSQL (`GRANT UPDATE (col, ...)`). Ils protègent contre une erreur de code, pas contre un administrateur de la base : ce n'est pas une preuve d'intégrité au sens juridique. Le chaînage du journal d'audit reste à évaluer (security-design §18).

Le droit à l'effacement (Q-68) s'applique par **anonymisation** de `users` et des profils, jamais par une modification des tables immuables, qui ne contiennent que des identifiants.

## 7. Concurrence

Rappel des règles du Jour 2 (D-09), appliquées au modèle :

| Opération | Ligne verrouillée (`FOR NO KEY UPDATE`) | Contrainte de dernier rempart |
|---|---|---|
| Envoi d'une RFQ aux exportateurs | `rfqs` | `uq_rfq_recipients_rfq_id_exporter_organization_id` |
| Nouvelle version de quotation | `quotations` | `uq_quotation_versions_quotation_id_version_no` |
| Contre-offre | `negotiations` | `uq_negotiation_offers_one_pending` |
| Acceptation et création du Trade | `rfqs`, puis `quotations`, puis `negotiations` (ordre des niveaux) | `uq_trades_quotation_id`, `uq_trade_items_rfq_item_id`, `uq_negotiation_offers_one_accepted` |
| Transition du Trade | `trades` | — |
| Confirmation d'un paiement | `trades`, puis `payment_records` | `ck_payment_records_confirmer_distinct` |
| Changement de coordonnées bancaires | `exporter_profiles` | `uq_bank_details_one_pending`, `uq_bank_details_one_active` |

Le verrou sur `rfqs` lors de l'acceptation sérialise les acceptations concurrentes de lignes d'une même RFQ (Q-25, Q-26).

## 8. Points à valider

| Sujet | Référence |
|---|---|
| Précision `numeric(19,4)` et arrondis | Q-08 |
| Une quotation par exportateur et par RFQ | Q-94 |
| Répartition d'une ligne de RFQ entre exportateurs | Q-26 |
| Clés composites de cohérence des lignes | Jour 24 |
| Contrainte `EXCLUDE` (extension `btree_gist`) | Jour 24 |
| Noms des rôles PostgreSQL | Jours 4 et 6 |
| Version de PostgreSQL | D-15 (Jour 4) ; ce document n'utilise rien au-delà de PostgreSQL 13 |
| Toutes les contraintes du Trade | Q-82 |
