# Classification des données — backend MadaSource

Jour 3 · 2026-10-13 · Statut : proposition à valider.

Ce document fixe, pour chaque champ sensible du [modèle de données](data-model.md) :
- sa classe ;
- les audiences qui peuvent le lire ;
- son traitement dans les journaux et l'audit.

Il complète [security-design.md](security-design.md) :
- §1 : actifs à protéger ;
- §5.2 : audiences (S-29) ;
- §6 : confidentialité commerciale ;
- §18 : journalisation et audit.

**Aucune conformité juridique n'est déclarée.** L'inventaire des données personnelles (section 5) est un outil technique ; la base légale, les finalités et les durées de conservation doivent être validées par un juriste (Q-68, Q-69).

## 1. Classes

| Classe | Définition | Exemples | Règles |
|---|---|---|---|
| **PUBLIC** | Peut être servi sans authentification | Passport publié, produit publié, libellés de catégorie | Seulement les champs listés pour l'audience `public` (section 3) |
| **INTERNE ORGANISATION** | Réservé aux membres de l'organisation propriétaire et à MadaSource | Brouillons, profil complet, adresses, liste des membres | Contrôle d'adhésion (S-28) |
| **PARTAGÉ** | Visible par les parties à un objet commun, selon la visibilité de l'objet | RFQ pour ses destinataires, Trade, messages, documents partagés | Audience calculée par P-01, plus valeur de visibilité (Q-82) |
| **INTERNE MADASOURCE** | Réservé aux admins MadaSource | Notes internes, résultats détaillés du matching, motifs de suspension internes | Valeur de visibilité `INTERNAL_ONLY` ; jamais servi à une organisation cliente |
| **FINANCE** | Composantes de prix internes | Marge, commission, total des coûts externes du Trade (Q-04) | Audience `madasource_finance` seulement (ensemble `FINANCE_READ`, S-12) ; tables séparées (`*_financials`) |
| **PRIX NET** | Prix net fournisseur | `supplier_unit_price`, `supplier_total_amount`, convention `SUPPLY` et ses paiements (`MADASOURCE_TO_EXPORTER`), `supplier_price_amount` des échantillons | Organisation exportatrice concernée et MadaSource ; jamais l'acheteur ni le public en Modèle A (S-18) |
| **PRIX FINAL** | Prix payé par l'acheteur | `buyer_unit_price`, `buyer_total_amount`, convention `SALE` et ses paiements (`BUYER_TO_MADASOURCE`), `buyer_price_amount` des échantillons, `target_price_*` de la RFQ, indication de prix `COMMERCIAL` | Organisation acheteuse concernée et MadaSource ; **jamais l'exportateur en Modèle A** (S-39), sauf décision contraire de Q-85 (prix cible) ou Q-06 (indication publique). Symétrique de PRIX NET : sans cette classe, ces champs tomberaient dans PARTAGÉ |
| **BANCAIRE** | Coordonnées bancaires | `bank_details`, `receiving_accounts` | Chiffré (S-22) ; affichage masqué ; lecture intégrale par action explicite et auditée |
| **SECRET** | Ne sort jamais de la base, ni de l'application | Hash de mot de passe, empreintes de jetons, clé de stockage, secret MFA, contenu de l'outbox | Jamais dans une réponse, un journal ou l'audit |
| **PERSONNEL** | Donnée relative à une personne identifiée ou identifiable | Email, nom, téléphone, adresse IP | Marqueur ajouté à la classe principale ; inventaire (section 5) |

Une donnée personnelle a toujours une autre classe. Par exemple, l'email d'un contact acheteur est INTERNE ORGANISATION et PERSONNEL.

## 2. Valeurs de visibilité et audiences

La valeur de visibilité (Q-82, PROPOSED) **restreint** l'audience calculée par la politique d'accès ; elle ne l'étend jamais (S-14, S-24). Cette garantie dépend du **contexte** auquel l'objet est rattaché, car c'est lui qui fixe l'audience de départ (P-01) :
- contexte `TRADE` : l'audience de départ comprend les deux parties. La visibilité est alors le **seul** discriminant, d'où les règles ci-dessous ;
- contexte `TRADE_AGREEMENT` : l'audience de départ ne comprend que la partie de cette convention et MadaSource. Même marqué `BOTH_PARTIES` par erreur, un objet n'atteint pas l'autre partie ;
- contexte `PAYMENT_RECORD` : l'audience est celle du sens du paiement (S-40).

Règles du Modèle A (constat de sécurité E2) :
- un document déposé par une partie dans un Trade est rattaché à **sa** convention (`TRADE_AGREEMENT`), jamais au contexte `TRADE` ;
- le contexte `TRADE` est réservé aux documents déposés par MadaSource (documents d'expédition partagés, par exemple) ;
- seule l'audience `madasource` peut poser `BOTH_PARTIES` ;
- un document déposé par MadaSource est `INTERNAL_ONLY` par défaut ;
- un événement de Trade lié à une convention ne peut prendre que la visibilité de son côté ou `INTERNAL_ONLY` (`CHECK` en base, [indexes-and-constraints.md](indexes-and-constraints.md) §3.2) ;
- un justificatif de paiement prend la visibilité du sens du paiement, sans modification possible ([data-model.md](data-model.md) §5.17) ;
- `PUBLIC` n'est possible que pour un document de catégorie `MARKETPLACE_MEDIA` (`CHECK` en base) ;
- conversations : un canal par côté, jamais de fil commun acheteur–exportateur sur une quotation, une négociation ou un Trade ([data-model.md](data-model.md) §5.8, constat E1). Proposition **À VALIDER** : elle contredit le CdC §28, qui prévoit une messagerie Buyer ↔ Exporter (CF-10, Q-99).

| Valeur | Audiences de lecture | Objets |
|---|---|---|
| `PUBLIC` (à valider, Q-96) | Toutes, y compris `public` | Médias du marketplace (logo, photos de produits publiés) |
| `OWNER_ONLY` (à valider, Q-96) | Organisation propriétaire, `madasource` | Documents d'une seule organisation : société, vérification, catalogue |
| `BUYER_VISIBLE` | `buyer`, `madasource` | Documents de la vente en Modèle A (contrat de vente, facture MadaSource) |
| `EXPORTER_VISIBLE` | `exporter_owner`, `madasource` | Documents de l'approvisionnement en Modèle A (bon de commande, facture de l'exportateur) |
| `BOTH_PARTIES` | `buyer`, `exporter_owner`, `madasource` | Documents d'expédition partagés, commentaires de suivi communs |
| `INTERNAL_ONLY` | `madasource` (et `madasource_finance`) | Notes internes, pièces de contrôle |

Valeurs par défaut :
- document déposé par une organisation : la plus restrictive pour le déposant (`OWNER_ONLY` hors Trade ; `BUYER_VISIBLE` ou `EXPORTER_VISIBLE` dans un Trade, selon le côté du déposant) ;
- document déposé et texte saisi par MadaSource ou par le système : `INTERNAL_ONLY` (S-47) ;
- commentaires de négociation, événements de suivi, litiges : côté de l'auteur, `INTERNAL_ONLY` pour MadaSource ; colonne de visibilité toujours renseignée (`NOT NULL`) ;
- seule la catégorie `MARKETPLACE_MEDIA` peut être `PUBLIC` : les documents de société, de paiement, fiscaux, bancaires et d'onboarding exportateur ne le sont donc jamais (S-24).

## 3. Champs par audience

Notation :
- **L** : lu ;
- **M** : lu masqué ;
- **—** : jamais servi ;
- **(Q-NN)** : dépend de la question.

Les audiences `exporter_owner` et `exporter_recipient` sont regroupées quand leur traitement est identique.

### 3.1 Comptes et organisations

| Champ | public | buyer | exporter | madasource | self |
|---|---|---|---|---|---|
| `users.email`, `full_name` | — | — | — | L | L |
| `users.password_hash`, `mfa_secret_encrypted` | — | — | — | — | — |
| `sessions.ip_address`, `user_agent` | — | — | — | L (S-12, à valider) | L (ses sessions) |
| `refresh_tokens.token_hash`, `*_tokens.token_hash`, `organization_invitations.token_hash` | — | — | — | — | — |
| `organizations.legal_name`, `country_code` | L (exportateur publié) | L (sa propre organisation) | L (sa propre organisation) | L | — |
| Libellé de la contrepartie dans une RFQ ou un Trade | — | Q-27 | Q-27 | L | — |
| `organization_capabilities.account_status` | — | L (sa propre organisation) | L (sa propre organisation) | L | — |
| `organization_capabilities.status_reason` | — | Q-97 | Q-97 | L | — |
| `organization_memberships` | — | L (sa propre organisation) | L (sa propre organisation) | L | L |
| `organization_invitations.email` | — | L (OWNER de l'organisation) | L (OWNER de l'organisation) | L | — |
| `platform_role_assignments` | — | — | — | L (`ADMIN_ACCOUNTS`) | — |

### 3.2 Profils et vérification

| Champ | public | buyer (autre organisation) | exporter (autre organisation) | organisation propriétaire | madasource |
|---|---|---|---|---|---|
| `buyer_profiles` (tous champs) | — | — | — | L | L |
| `organizations.legal_name`, pays et région | L (exportateur publié) | L | L | L | L |
| `exporter_profiles.description`, `founded_year`, `export_markets`, logo | Q-86 | Q-86 | Q-86 | L | L |
| `exporter_profiles.contact_*`, adresse | — | Q-27 | — | L | L |
| `business_registration_number` | — | — | — | L | L |
| `tax_identifier_encrypted` | — | — | — | M (L sur action explicite, Q-81) | M (L sur action explicite) |
| `capacity_records` | Q-86 | Q-86 | — | L | L |
| `exporter_certifications` (code, validité) | L si vérifiée | L si vérifiée | L si vérifiée | L | L |
| `bank_details` | — | Modèle B seulement : Q-55 ; jamais en Modèle A | — | M (L sur action auditée) | M (L avec `BANK_DATA`, auditée) |
| Statut de vérification calculé et niveau | L (badge) | L (badge) | L (badge) | L | L |
| `verification_records.rejection_reason` | — | — | — | L | L |
| `verification_records.internal_notes` | — | — | — | — | L |
| Documents de vérification | — | — | — | L | L |

### 3.3 Catalogue

| Champ | public | buyer | exporter (autre organisation) | organisation propriétaire | madasource |
|---|---|---|---|---|---|
| Produit `PUBLISHED` : nom, catégorie, attributs, origine, quantités, MOQ, Incoterm, certifications | L | L | L | L | L |
| Produit `DRAFT`, `UNPUBLISHED`, `ARCHIVED` | — | — | — | L | L |
| `price_indication_*` | Q-06 | Q-06 | Q-06 | L | L |

Règles (S-18, S-19), constat de sécurité M11 :
- si `price_indication_basis = SUPPLIER_NET`, l'indication de prix n'est jamais publique en Modèle A, puisqu'elle révélerait le prix net ;
- si `price_indication_basis = COMMERCIAL`, l'indication n'est pas servie à l'exportateur propriétaire en Modèle A, puisqu'il connaît son prix net et en déduirait la marge. La colonne « organisation propriétaire » ci-dessus vaut donc seulement pour une indication `SUPPLIER_NET`.

### 3.4 RFQ et matching

| Champ | public | buyer (propriétaire) | exporter_recipient | autre exportateur | madasource |
|---|---|---|---|---|---|
| RFQ et lignes (`rfqs`, `rfq_items`) | — | L | L (Q-85 pour `target_price_*`) | — | L |
| Liste des destinataires (`rfq_recipients`) | — | L en mode `DIRECT` ; Q-31 en mode `OPEN_MATCHING` | — (sa propre ligne seulement) | — | L |
| `rfq_questions` | — | L | L (sa paire ; `ALL_RECIPIENTS` : toutes) | — | L |
| `rfq_matches.score` et raisons | — | Q-31 | Q-31 | — | L |
| `rfq_matches.criteria_results` | — | — | — | — | L |
| `match_runs`, `matching_configs` | — | — | — | — | L |

Oracle de prix (constat M11) : si le matching utilise un critère de prix et que la sélection ou le score sont visibles de l'acheteur (Q-31), l'acheteur pourrait retrouver le prix net en faisant varier son prix cible. Le prix n'est donc **pas** un critère de matching tant que ce risque n'est pas traité (Q-30, Q-31).

### 3.5 Quotations, négociations, Trades

Modèle A (revendeur). En Modèle B, la visibilité dépend des contrats (Q-82) : à définir avant le Jour 24.

| Champ | buyer | exporter_owner | madasource | madasource_finance |
|---|---|---|---|---|
| `quotation_versions.buyer_total_amount`, `quotation_lines.buyer_unit_price` | L | — (S-39) | L | L |
| `quotation_versions.supplier_total_amount`, `quotation_lines.supplier_unit_price` | — | L | L | L |
| `quotation_versions.external_costs_total`, `quotation_lines.external_costs_unit` | Q-04 | Q-04 | L | L |
| `quotation_version_costs`, `external_costs` | — | — | L | L |
| `quotation_version_financials` | — | — | — | L |
| `pricing_rule_versions` | — | — | L | L |
| `negotiation_offers.buyer_total_amount`, lignes `buyer_unit_price` | L | — | L | L |
| `negotiation_offers.supplier_total_amount`, lignes `supplier_unit_price` | — | L | L | L |
| `negotiation_offer_financials`, `offer_external_costs` | — | — | — | L |
| `negotiation_offers.comment` | Selon `comment_visibility` | Selon `comment_visibility` | L | L |
| `trade_agreements` `SALE` (prix, termes) | L | — | L | L |
| `trade_agreements` `SUPPLY` (prix, termes) | — | L | L | L |
| `trade_items` (produit, quantité, qualité) | L | L | L | L |
| `trades.status`, `shipment_summary` | L | L | L | L |
| `trade_agreements.payment_status` | Sa convention seulement | Sa convention seulement | L | L |
| `trade_financials` | — | — | — | L |
| `trade_events` | Selon `visibility` | Selon `visibility` | L | L |

L'audience `madasource` sans `FINANCE_READ` voit les prix de chaque convention, puisqu'elle opère le Trade, mais **pas** la marge ni la commission. Qu'elle puisse les recalculer par différence est accepté : c'est le principe de l'ensemble `FINANCE_READ` à valider (S-12, Q-89).

### 3.6 Paiements, expéditions, échantillons, exceptions, avis

| Champ | buyer | exporter_owner | madasource | madasource_finance |
|---|---|---|---|---|
| `payment_records` `BUYER_TO_MADASOURCE` | L | — (S-40) | L | L |
| `payment_records` `MADASOURCE_TO_EXPORTER` | — | L | L | L |
| `payment_records` `BUYER_TO_EXPORTER` (Modèle B) | L | L | L | L |
| `receiving_accounts` | M (coordonnées de virement : Q-55) | — | M (L avec `BANK_DATA`) | M |
| `shipments` | L (Q-82) | L (Q-82) | L | L |
| `tracking_events` | Selon `visibility` | Selon `visibility` | L | L |
| `sample_requests.buyer_price_amount` | L | — (Modèle A) | L | L |
| `sample_requests.supplier_price_amount` | — (Modèle A) | L | L | L |
| `exception_cases` | — (Q-60) | — (Q-60) | L | L |
| `exception_notes` | Selon `visibility` | Selon `visibility` | L | L |
| `disputes` | Selon `visibility` (Q-92) ; une résolution chiffrée sur une convention n'est servie qu'à la partie de cette convention | Idem | L | L |
| `reviews`, `review_ratings` publiés | L (public : Q-59) | L | L | L |
| Documents et justificatifs | Selon la visibilité de la version | Selon la visibilité de la version | L | L |

### 3.7 Clés interdites par audience

Les tests de projection (S-37) vérifient l'ensemble **exact** des clés. En plus, aucune réponse servie à l'audience indiquée ne doit contenir une clé de cette liste, même imbriquée.

| Audience | Clés interdites |
|---|---|
| Toutes, y compris `madasource` et `madasource_finance` | `password_hash`, `token_hash`, `mfa_secret_encrypted`, `storage_key`, `payload_encrypted`, `recipient_encrypted`, `encryption_key_id`, `tax_identifier_key_id`, `mfa_secret_key_id`, tout champ `*_encrypted`. Une donnée chiffrée n'est servie qu'en clair, après déchiffrement sur action explicite et auditée, par un endpoint dédié. |
| Toutes sauf `madasource_finance` | `margin_total`, `commission_rate`, `commission_amount`, `commission_payer` |
| Audiences clientes : `public`, `buyer`, `exporter_owner`, `exporter_recipient`, `self` | `internal_notes`, `criteria_results`, `pricing_rule_version_id`, `external_cost_id`, `applied_amount`, `restricted_sets`, `resolution_summary`, tout objet de visibilité `INTERNAL_ONLY` |
| `public` | Toutes les clés précédentes, plus `supplier_unit_price`, `supplier_total_amount`, `buyer_unit_price`, `buyer_total_amount`, `external_costs_*`, `target_price_*`, `contact_*`, `email`, `address_*`, `business_registration_number`, `tax_identifier_masked`, `certificate_number`, `bank_*`, `masked_display`, `account_status`, `status_reason`, `rejection_reason`, `decline_reason`, et tout champ de brouillon |
| `buyer` (Modèle A) | Les clés des trois premières lignes, plus `supplier_unit_price`, `supplier_total_amount`, `supplier_price_amount`, `external_costs_*` (sauf si Q-04 l'autorise), `business_registration_number`, `tax_identifier_masked`, `rejection_reason`, `bank_*` et `masked_display` d'un exportateur, la convention `SUPPLY` entière, les paiements `MADASOURCE_TO_EXPORTER` |
| `exporter_owner`, `exporter_recipient` (Modèle A) | Les clés des trois premières lignes, plus `buyer_unit_price`, `buyer_total_amount`, `buyer_price_amount`, `target_price_*` (sauf si Q-85 l'autorise), `buyer_organization_id` (tant que Q-27 est ouvert : sinon un exportateur pourrait relier entre elles les RFQ d'un même acheteur), `receiving_account_id`, la convention `SALE` entière, les paiements `BUYER_TO_MADASOURCE` |

Les colonnes non sensibles des tables `*_financials` (`trade_id`, `currency`) ne sont pas interdites par principe : la liste nomme les clés sensibles, pour qu'un test exact reste applicable sans être assoupli.

Les noms de clés sont ceux du modèle de données. Si un schéma de réponse renomme un champ, la liste suit le nouveau nom, ce qui est vérifié par les tests de projection.

### 3.8 Montants de même nom : schémas distincts et valeurs sentinelles

Une liste de clés interdites ne voit pas une convention `SALE` servie à l'exportateur : ses montants portent les mêmes noms (`total_amount`, `unit_price`, `line_total`, `amount`) que ceux de la convention `SUPPLY` (constat de sécurité E3). Deux règles complètent donc la section 3.7 :
- **schémas distincts** par convention et par audience (par exemple `SaleAgreementBuyerRead` et `SupplyAgreementExporterRead`), jamais une liste générique de conventions imbriquée dans la réponse d'un Trade ;
- **valeurs sentinelles** dans les tests : chaque montant caché d'une audience reçoit, dans les données de test, une valeur unique et reconnaissable (par exemple `987654.3210`). Le test parcourt toute réponse sérialisée de l'audience opposée, en-têtes et corps, et échoue si la valeur y apparaît.

Les sentinelles couvrent aussi les **identifiants** tant que Q-27 est ouvert : l'identifiant de l'organisation acheteuse et ceux de ses utilisateurs reçoivent des UUID sentinelles, recherchés dans toute réponse servie à un exportateur. Ils peuvent en effet circuler sous d'autres clés que `buyer_organization_id` : `conversation_participants.organization_id`, `messages.author_organization_id`, `documents.owner_organization_id`, colonnes `*_by_user_id`. L'identité d'un acteur est rendue selon S-48, jamais par son identifiant brut.

Tests prévus : `test_buyer_identifiers_absent_from_exporter_responses`, `test_sentinel_sale_amount_absent_from_exporter_responses`, `test_sentinel_supply_amount_absent_from_buyer_responses`, `test_supply_event_cannot_be_buyer_visible` ; `test_model_a_negotiation_conversation_never_has_both_parties`, seulement si Q-99 retient les canaux séparés.

### 3.9 Utilisateur membre de plusieurs organisations

Un utilisateur peut être membre de plusieurs organisations (Q-74, PROPOSED). S'il est membre à la fois de l'organisation acheteuse et de l'organisation exportatrice d'un même objet, il lirait en Modèle A les deux conventions, donc la marge, en changeant d'organisation active (constat de sécurité E4). Proposition, en attente de Q-98 :
- le service refuse à cet utilisateur de soumettre une quotation, de contre-proposer, d'accepter ou d'évaluer sur cet objet ;
- une requête faite dans le contexte d'une organisation n'a **jamais** de permission de plateforme, même si l'utilisateur est aussi administrateur.

Tests prévus : `test_user_member_of_both_parties_cannot_accept`, `test_admin_in_org_context_has_no_platform_permissions`.

## 4. Journaux et audit

| Classe | Journaux applicatifs (D-12) | Valeurs dans l'audit (`previous_values`, `new_values`) |
|---|---|---|
| PUBLIC, INTERNE ORGANISATION, PARTAGÉ | Identifiants seulement | En clair, sauf champ PERSONNEL |
| INTERNE MADASOURCE | Identifiants seulement | En clair (l'audit n'est lu que par `AUDIT_READ`) |
| FINANCE, PRIX NET, PRIX FINAL | **Jamais** | `FINANCE` dans `restricted_sets` : lisible seulement avec `FINANCE_READ` |
| BANCAIRE | **Jamais** | Valeur masquée seulement ; `BANK` dans `restricted_sets`. Une entrée peut porter les deux ensembles, et la lecture exige alors les deux |
| SECRET | **Jamais** | **Jamais**, pas même masquée : l'audit note seulement « modifié » |
| PERSONNEL | **Jamais** (identifiants à la place) | Identifiant de la personne, pas sa valeur (Q-68). La colonne `metadata` de l'audit ne contient jamais de donnée personnelle : ni adresse IP, ni email saisi lors d'un échec de connexion |

## 5. Inventaire des données personnelles

Proposition technique, à faire valider par un juriste (Q-68). Les durées de conservation ne sont **pas fixées** : elles sont toutes `À VALIDER` (Q-69).

| Donnée | Tables | Personnes concernées | Finalité (proposée) | Destinataires | Effacement (proposé) |
|---|---|---|---|---|---|
| Email, nom | `users` | Utilisateurs | Compte, connexion, notifications | L'utilisateur, MadaSource | Anonymisation de `users` (`anonymized_at`) ; identifiant conservé pour l'audit et les historiques |
| Adresse IP, navigateur | `sessions` | Utilisateurs | Sécurité, détection d'abus | MadaSource | Purge à la fin de la durée de conservation |
| Titulaire d'un compte bancaire | `bank_details`, `receiving_accounts` | Titulaires, souvent des personnes pour une entreprise individuelle | Paiements | Organisation, `BANK_DATA` | Conservation liée aux obligations comptables (à valider) |
| Identifiants d'entreprise | `exporter_profiles.business_registration_number`, `tax_identifier_encrypted` | Entrepreneurs individuels | Vérification | Organisation, MadaSource | Effacement ou remplacement, sous réserve d'obligation légale |
| Email invité | `organization_invitations` | Personnes invitées | Invitation | OWNER de l'organisation, MadaSource | Purge après expiration ou révocation (durée : Q-69) |
| Contacts et adresses d'organisation | `buyer_profiles`, `exporter_profiles` | Contacts des entreprises | Relation commerciale | Organisation, MadaSource ; contrepartie selon Q-27 | Effacement ou remplacement par l'organisation |
| Contenus libres (messages, questions, commentaires, notes, motifs) | `messages`, `rfq_questions`, `rfqs.additional_requirements`, `rfq_recipients.decline_reason`, `negotiation_offers.comment`, `quotation_versions.additional_conditions`, `trade_events.comment`, `tracking_events.comment` et `location`, `exception_notes`, `disputes`, `reviews`, champs `*_reason`, `payment_records.payment_reference` | Auteurs, personnes citées | Échanges commerciaux, traçabilité | Participants, selon la visibilité | Au cas par cas : conservation possible pour une obligation ou un litige (`legal_hold`). Plusieurs de ces tables sont immuables : procédure d'effacement exceptionnelle proposée ([indexes-and-constraints.md](indexes-and-constraints.md) §6.3), à valider avec un juriste |
| Documents et noms de fichiers | `document_versions` (dont `original_filename`) et stockage | Personnes figurant dans les pièces | Preuve, conformité export | Selon la visibilité | Au cas par cas, sous les mêmes réserves |
| Identifiants dans l'audit | `audit_logs` | Utilisateurs | Traçabilité (CdC §52) | `AUDIT_READ` | Ni valeur personnelle, ni modification : l'identifiant ne renvoie plus qu'à un compte anonymisé |
| Demandes de droits | `privacy_requests` | Demandeurs | Suivi des demandes | `ADMIN_ACCOUNTS` | Trace minimale de la décision, sans recopie des données supprimées |
| Adresse d'envoi d'email | `outbox_messages` (conditionnelle) | Destinataires | Envoi | Fournisseur d'email (futur) | Purge après envoi ou abandon |

Données sensibles au sens juridique (santé, opinions…) : aucune n'est collectée par le modèle. Un contenu libre ou un document peut néanmoins en contenir ; ce risque est noté pour la revue juridique.

## 6. Points à valider

| Sujet | Question |
|---|---|
| Valeurs `OWNER_ONLY` et `PUBLIC` | Q-96 |
| Identité de la contrepartie et contacts visibles | Q-27 |
| Prix indicatif public | Q-06 |
| Prix cible visible par les exportateurs | Q-85 |
| Coûts externes visibles | Q-04 |
| Profil public de l'exportateur (description, logo, capacités…) | Q-86 |
| Destinataires, scores et raisons du matching visibles | Q-31 |
| Motif d'un changement de statut de compte communiqué | Q-97 |
| Coordonnées de virement présentées à l'acheteur | Q-55 |
| Admins habilités aux données financières | Q-89 |
| Conservation de chaque catégorie | Q-69 |
| Base légale, finalités, procédures | Q-68 (juriste) |
| Visibilité en Modèle B | Q-82 |
| Utilisateur membre des deux parties | Q-98 |
| Prix comme critère de matching | Q-30, Q-31 |
