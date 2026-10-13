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
| **PRIX NET** | Prix net fournisseur | `supplier_unit_price`, `supplier_total_amount`, convention `SUPPLY` | Organisation exportatrice concernée et MadaSource ; jamais l'acheteur ni le public en Modèle A (S-18) |
| **BANCAIRE** | Coordonnées bancaires | `bank_details`, `receiving_accounts` | Chiffré (S-22) ; affichage masqué ; lecture intégrale par action explicite et auditée |
| **SECRET** | Ne sort jamais de la base, ni de l'application | Hash de mot de passe, empreintes de jetons, clé de stockage, secret MFA | Jamais dans une réponse, un journal ou l'audit |
| **PERSONNEL** | Donnée relative à une personne identifiée ou identifiable | Email, nom, téléphone, adresse IP | Marqueur ajouté à la classe principale ; inventaire (section 5) |

Une donnée personnelle a toujours une autre classe. Par exemple, l'email d'un contact acheteur est INTERNE ORGANISATION et PERSONNEL.

## 2. Valeurs de visibilité et audiences

La valeur de visibilité (Q-82, PROPOSED) **restreint** l'audience calculée par la politique d'accès ; elle ne l'étend jamais (S-14, S-24).

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
- texte saisi par un admin : `INTERNAL_ONLY` (S-47) ;
- catégories de documents **jamais** `PUBLIC` : société, paiement, fiscalité, banque, onboarding exportateur (S-24).

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
| `bank_details` | — | Q-55 | — | M (L sur action auditée) | M (L avec `BANK_DATA`, auditée) |
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

Règle : si `price_indication_basis = SUPPLIER_NET`, l'indication de prix n'est jamais publique en Modèle A, puisqu'elle révélerait le prix net (S-18, S-19).

### 3.4 RFQ et matching

| Champ | public | buyer (propriétaire) | exporter_recipient | autre exportateur | madasource |
|---|---|---|---|---|---|
| RFQ et lignes (`rfqs`, `rfq_items`) | — | L | L (Q-85 pour `target_price_*`) | — | L |
| Liste des destinataires (`rfq_recipients`) | — | L en mode `DIRECT` ; Q-31 en mode `OPEN_MATCHING` | — (sa propre ligne seulement) | — | L |
| `rfq_questions` | — | L | L (sa paire ; `ALL_RECIPIENTS` : toutes) | — | L |
| `rfq_matches.score` et raisons | — | Q-31 | Q-31 | — | L |
| `rfq_matches.criteria_results` | — | — | — | — | L |
| `match_runs`, `matching_configs` | — | — | — | — | L |

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
| `trades.status`, `payment_summary`, `shipment_summary` | L | L | L | L |
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
| `shipments`, `tracking_events` | L (selon `visibility`) | L (selon `visibility`) | L | L |
| `sample_requests.price_*` | Q-53 | Q-53 | L | L |
| `exception_cases` | — (Q-60) | — (Q-60) | L | L |
| `exception_notes` | Selon `visibility` | Selon `visibility` | L | L |
| `disputes` | L (partie à l'origine) ; contrepartie : `counterparty_visible` (Q-92) | Idem | L | L |
| `reviews`, `review_ratings` publiés | L (public : Q-59) | L | L | L |
| Documents et justificatifs | Selon la visibilité de la version | Selon la visibilité de la version | L | L |

### 3.7 Clés interdites par audience

Les tests de projection (S-37) vérifient l'ensemble **exact** des clés. En plus, aucune réponse servie à l'audience indiquée ne doit contenir une clé de cette liste, même imbriquée.

| Audience | Clés interdites |
|---|---|
| Toutes, y compris `madasource` et `madasource_finance` | `password_hash`, `token_hash`, `mfa_secret_encrypted`, `storage_key`, `payload_encrypted`, `encryption_key_id`, tout champ `*_encrypted`. Une donnée chiffrée n'est servie qu'en clair, après déchiffrement sur action explicite et auditée, par un endpoint dédié. |
| Toutes sauf `madasource_finance` | `margin_total`, `commission_rate`, `commission_amount`, `commission_payer`, toute clé d'une table `*_financials` |
| Audiences clientes : `public`, `buyer`, `exporter_owner`, `exporter_recipient`, `self` | `internal_notes`, `criteria_results`, `pricing_rule_version_id`, `external_cost_id`, `restricted_set`, tout objet de visibilité `INTERNAL_ONLY` |
| `public` | Toutes les clés précédentes, plus `supplier_unit_price`, `supplier_total_amount`, `buyer_unit_price`, `buyer_total_amount`, `external_costs_*`, `contact_*`, `email`, `address_*`, `business_registration_number`, `bank_*`, `masked_display`, `account_status`, `status_reason`, et tout champ de brouillon |
| `buyer` (Modèle A) | Les clés des trois premières lignes, plus `supplier_unit_price`, `supplier_total_amount`, `external_costs_*` (sauf si Q-04 l'autorise), la convention `SUPPLY` entière, les paiements `MADASOURCE_TO_EXPORTER` |
| `exporter_owner`, `exporter_recipient` (Modèle A) | Les clés des trois premières lignes, plus `buyer_unit_price`, `buyer_total_amount`, `target_price_*` (sauf si Q-85 l'autorise), la convention `SALE` entière, les paiements `BUYER_TO_MADASOURCE`, `receiving_account_id` |

Les noms de clés sont ceux du modèle de données. Si un schéma de réponse renomme un champ, la liste suit le nouveau nom, ce qui est vérifié par les tests de projection.

## 4. Journaux et audit

| Classe | Journaux applicatifs (D-12) | Valeurs dans l'audit (`previous_values`, `new_values`) |
|---|---|---|
| PUBLIC, INTERNE ORGANISATION, PARTAGÉ | Identifiants seulement | En clair, sauf champ PERSONNEL |
| INTERNE MADASOURCE | Identifiants seulement | En clair (l'audit n'est lu que par `AUDIT_READ`) |
| FINANCE, PRIX NET | **Jamais** | `restricted_set = FINANCE` : lisible seulement avec `FINANCE_READ` |
| BANCAIRE | **Jamais** | Valeur masquée seulement ; `restricted_set = BANK` |
| SECRET | **Jamais** | **Jamais**, pas même masquée : l'audit note seulement « modifié » |
| PERSONNEL | **Jamais** (identifiants à la place) | Identifiant de la personne, pas sa valeur (Q-68) |

## 5. Inventaire des données personnelles

Proposition technique, à faire valider par un juriste (Q-68). Les durées de conservation ne sont **pas fixées** : elles sont toutes `À VALIDER` (Q-69).

| Donnée | Tables | Personnes concernées | Finalité (proposée) | Destinataires | Effacement (proposé) |
|---|---|---|---|---|---|
| Email, nom | `users` | Utilisateurs | Compte, connexion, notifications | L'utilisateur, MadaSource | Anonymisation de `users` (`anonymized_at`) ; identifiant conservé pour l'audit et les historiques |
| Adresse IP, navigateur | `sessions` | Utilisateurs | Sécurité, détection d'abus | MadaSource | Purge à la fin de la durée de conservation |
| Email invité | `organization_invitations` | Personnes invitées | Invitation | OWNER de l'organisation, MadaSource | Purge après expiration ou révocation (durée : Q-69) |
| Contacts et adresses d'organisation | `buyer_profiles`, `exporter_profiles` | Contacts des entreprises | Relation commerciale | Organisation, MadaSource ; contrepartie selon Q-27 | Effacement ou remplacement par l'organisation |
| Contenus libres (messages, questions, commentaires, notes) | `messages`, `rfq_questions`, `negotiation_offers.comment`, `trade_events.comment`, `exception_notes`, `disputes`, `reviews` | Auteurs, personnes citées | Échanges commerciaux, traçabilité | Participants, selon la visibilité | Au cas par cas : conservation possible pour une obligation ou un litige (`legal_hold`) |
| Documents | `document_versions` et stockage | Personnes figurant dans les pièces | Preuve, conformité export | Selon la visibilité | Au cas par cas, sous les mêmes réserves |
| Identifiants dans l'audit | `audit_logs` | Utilisateurs | Traçabilité (CdC §52) | `AUDIT_READ` | Ni valeur personnelle, ni modification : l'identifiant ne renvoie plus qu'à un compte anonymisé |
| Demandes de droits | `privacy_requests` | Demandeurs | Suivi des demandes | `ADMIN_ACCOUNTS` | Trace minimale de la décision, sans recopie des données supprimées |
| Adresse d'envoi d'email | `outbox_messages` (conditionnelle) | Destinataires | Envoi | Fournisseur d'email (futur) | Purge après envoi |

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
