# Registre des décisions d'architecture — MadaSource

Créé le 2026-10-13 (Jour 3), à partir du document « MadaSource — Réponses aux questions de clarification » transmis par l'utilisateur.

## Règles du registre

- Statuts : **PROPOSED** (proposition, non approuvée), **APPROVED** (approbation réelle, avec auteur et date), **SUPERSEDED** (remplacée, avec renvoi).
- `approved_by` et `approved_at` ne sont remplis **que** lorsqu'une approbation réelle a été donnée par le responsable produit.
- Une décision PROPOSED n'est pas implémentée silencieusement quand elle touche au modèle de données, aux contrats commerciaux, aux permissions ou à la conformité. Elle est documentée, et l'implémentation attend l'approbation ou un choix explicite du jour concerné.
- Une proposition qui contredit le cahier des charges (CdC) ne le remplace pas : le conflit est signalé (section 2).
- Les décisions techniques internes (D-NN, S-NN) restent dans [architecture.md](../backend/architecture.md) et [security-design.md](../backend/security-design.md). Ce registre porte les décisions issues des questions Q-NN.

À ce jour, **aucune décision n'est APPROVED**.

## 1. Décisions

### Q-09 — Organisation à la fois acheteuse et exportatrice

| Champ | Valeur |
|---|---|
| id | Q-09 |
| status | PROPOSED |
| context | Le CdC §54 organise la plateforme autour des organisations, mais ne dit pas si une même entreprise peut acheter et exporter. |
| decision | Une organisation peut avoir les **capacités** BUYER, EXPORTER ou les deux. Les capacités appartiennent à l'organisation, pas à l'utilisateur. Une seule organisation par entreprise, jamais deux organisations pour séparer les activités. |
| rationale | Reflète la réalité des entreprises et évite les doublons d'organisation. |
| affected_modules | organizations, access_control, buyers, exporters, verification, rfqs, quotations, trades |
| consequences | Table `organization_capabilities` (unicité organisation + capacité). Historiques d'achat et d'export distingués. **Invariant maintenu** : une organisation ne peut jamais être à la fois acheteuse et exportatrice d'une même RFQ, quotation ou Trade (S-36). L'accès aux fonctions d'exportateur reste soumis à la vérification (Q-12). |
| approved_by / approved_at | — |

### Q-10 — Rôles internes et invitations

| Champ | Valeur |
|---|---|
| id | Q-10 |
| status | PROPOSED |
| context | Le CdC §54 prévoit plusieurs utilisateurs par organisation avec des permissions différentes ; le CdC §53 cite les rôles minimaux Buyer, Exporter et MadaSource Admin. |
| decision | Rôles internes V1 : **OWNER** (profil, membres, invitations) et **MEMBER** (fonctions autorisées). **MADASOURCE_ADMIN** est un rôle de plateforme, jamais attribué comme rôle interne à une organisation cliente. Seul un OWNER invite en V1. Une invitation est liée à une organisation, porte un état et une expiration, et n'est acceptable qu'une fois. Invitations, acceptations, révocations et changements de rôle sont audités. Les rôles détaillés (directeur, commercial, opérations) sont reportés. |
| rationale | Couvre le besoin multi-utilisateur sans système de permissions complexe non validé. |
| affected_modules | organizations, access_control, auth, audit, admin |
| consequences | Rôle porté par l'adhésion (`organization_memberships.role`), table `organization_invitations`, table `platform_role_assignments` pour les admins. Permissions effectives = rôle d'adhésion × capacité de l'organisation, ou rôle de plateforme (S-11). Conflit terminologique avec le CdC §53 : section 2, CF-03. |
| approved_by / approved_at | — |

### Q-12 — Statut du compte exportateur et vérification

| Champ | Valeur |
|---|---|
| id | Q-12 |
| status | PROPOSED |
| context | Le CdC §10 définit les statuts du compte acheteur ; le CdC §8 définit les statuts de vérification ; rien ne définit le compte exportateur. |
| decision | Statut du compte et statut de vérification **séparés**. Compte exportateur proposé : PENDING_ACTIVATION, ACTIVE, SUSPENDED, CLOSED. Statut de vérification proposé : UNVERIFIED, IN_REVIEW, VERIFIED, REJECTED, EXPIRED. Exportateur non vérifié : il peut compléter son profil, préparer des produits en brouillon et consulter ses données et demandes de vérification ; il **ne peut pas** publier, apparaître dans le matching, recevoir des RFQ du système ni envoyer de quotation. Contrôles côté backend sur toutes les routes concernées. Décisions de vérification journalisées (acteur, date, état précédent, nouvel état, motif). |
| rationale | Un compte actif ne signifie pas une entreprise vérifiée (BR-VER-03). |
| affected_modules | organizations, verification, exporters, products, matching, rfqs, quotations |
| consequences | Statut de compte porté par la capacité EXPORTER de l'organisation ; statut de vérification dérivé des enregistrements de vérification. **Conflits avec le CdC** : section 2, CF-01 et CF-02. Le niveau minimal qui vaut « vérifié » reste à fixer (Q-16). |
| approved_by / approved_at | — |

### Q-74 — Appartenance multiple et administrateurs

| Champ | Valeur |
|---|---|
| id | Q-74 |
| status | PROPOSED |
| context | Les sources ne disent pas si un utilisateur peut appartenir à plusieurs organisations. |
| decision | Un utilisateur peut appartenir à **plusieurs** organisations ; chaque adhésion a son rôle et son statut. L'utilisateur choisit l'organisation active ; chaque requête est autorisée dans le contexte de cette organisation, après vérification de l'adhésion. Un `organization_id` envoyé par le client n'est jamais une preuve d'autorisation. Les administrateurs MadaSource ont des permissions de plateforme distinctes, ne sont pas membres d'une organisation cliente par défaut, et **aucune organisation interne « MadaSource » n'est créée** sans exigence métier validée. |
| rationale | Consultants, groupes et entreprises multi-entités. |
| affected_modules | auth, organizations, access_control, admin, toute l'API |
| consequences | Remplace (SUPERSEDED, si approuvée) la proposition S-33 du Jour 2 sur l'organisation interne MadaSource. L'acteur porte une organisation active, ou aucune pour un admin de plateforme. Contexte transmis par un en-tête, vérifié à chaque requête (proposition : `X-Organization-Id`). Point à valider : interdire qu'un compte admin détienne aussi une adhésion cliente (risque relevé par la relecture de sécurité, E-6). Relecture de sécurité du Jour 3 : un utilisateur membre des deux parties d'un même objet lirait en Modèle A les deux conventions, donc la marge (Q-98) ; une requête faite dans le contexte d'une organisation ne porte jamais de permission de plateforme (proposition, [data-classification.md](../backend/data-classification.md) §3.9). |
| approved_by / approved_at | — |

### Q-25 — Contenu et diffusion d'une RFQ

| Champ | Valeur |
|---|---|
| id | Q-25 |
| status | PROPOSED |
| context | Le CdC §12 décrit une RFQ et ses champs ; le CdC §55 prévoit des RFQItems. |
| decision | Une RFQ exprime le besoin de l'acheteur et peut contenir **plusieurs lignes** (catégorie, spécifications, quantité, unité, produit publié facultatif). Deux modes de diffusion : **ouverte au matching**, ou **adressée directement** à des exportateurs choisis. Seuls les exportateurs autorisés par les règles de compte et de vérification peuvent recevoir une RFQ ; le ciblage direct ne contourne aucune règle. Un exportateur n'est pas obligé de répondre à toutes les lignes. |
| rationale | Besoins multi-produits ; relation directe avec un exportateur repéré dans le marketplace. |
| affected_modules | rfqs, matching, quotations, negotiations, trades |
| consequences | `rfqs.distribution_mode`, `rfq_items` identifiables individuellement, `rfq_recipients.source`. Une quotation couvre une ou plusieurs lignes. Une RFQ peut donc donner lieu à **plusieurs Trades**, avec des exportateurs différents selon les lignes : cela touche la machine d'état de la RFQ (Q-24) et Q-26. Le CdC place destination, Incoterm et livraison au niveau de la RFQ : ils restent dans l'en-tête, avec une surcharge facultative par ligne (CF-06). |
| approved_by / approved_at | — |

### Q-37 — Format des identifiants lisibles

| Champ | Valeur |
|---|---|
| id | Q-37 |
| status | PROPOSED, format final à valider |
| context | Le CdC §16, §22 et §66 donne des exemples d'apparence séquentielle (`MST-2026-000145`). Des références séquentielles révèlent le volume d'activité (S-54). |
| decision | Références **non séquentielles** : `RFQ-AAAA-XXXXXX`, `MSQ-AAAA-XXXXXX`, `MST-AAAA-XXXXXX`. AAAA est l'année de création ; XXXXXX est une suite aléatoire de 6 caractères majuscules et chiffres (exemples : `RFQ-2026-K7M4Q9`, `MST-2026-A6N9T3`). Générateur cryptographiquement robuste, unicité garantie en base, stabilité à vie, aucune remise à zéro annuelle. La référence n'est jamais une preuve d'autorisation. |
| rationale | Supprime la fuite de volume et la table de compteurs. |
| affected_modules | socle (génération), rfqs, quotations, trades |
| consequences | Remplace (SUPERSEDED, si approuvée) D-16 (compteur annuel). Plus de sérialisation des créations. Unicité garantie par contrainte, avec nouvelle tentative en cas de collision (rare : 36⁶ ≈ 2,2 milliards de valeurs par préfixe et par année). Écart avec les exemples du CdC : section 2, CF-04. |
| approved_by / approved_at | — |

### Q-82 — Modèle A : relations commerciales et visibilité

| Champ | Valeur |
|---|---|
| id | Q-82 |
| status | PROPOSED — **BLOQUANT pour le modèle de données du Trade** |
| context | Le CdC §2 décrit le Modèle A (revendeur avec marge) et le Modèle B (intermédiaire à commission), sans fixer la structure juridique (CdC §75). |
| decision | En Modèle A, deux relations distinctes, sous une référence centrale commune : **vente** Buyer ↔ MadaSource et **approvisionnement** MadaSource ↔ Exporter. Conditions, prix et documents contractuels propres à chaque relation. Le prix final n'est pas exposé à l'exportateur par défaut ; le prix net fournisseur n'est pas exposé à l'acheteur ; la marge est réservée aux admins disposant de permissions financières explicites. Payment Records rattachés à la relation financière concernée. Classification de visibilité : **BUYER_VISIBLE, EXPORTER_VISIBLE, BOTH_PARTIES, INTERNAL_ONLY**, jamais seule : le backend vérifie aussi l'organisation, la relation au Trade, le type d'objet et les permissions. En Modèle B, l'acheteur et l'exportateur peuvent être contreparties directes, avec une visibilité à définir selon les contrats. Le modèle commercial appliqué est enregistré et figé à l'acceptation. |
| rationale | Ne pas exposer de conditions confidentielles entre contreparties différentes (constat C-1 de la relecture de sécurité). |
| affected_modules | trades, payment_records, shipments, documents, messages, exceptions, quotations, negotiations |
| consequences | Modèle du Trade proposé à partir de « conventions » (une par relation commerciale), dont les parties se déduisent du type ; visibilité des événements bornée par la convention ; justificatifs de paiement à la visibilité du sens du paiement ; pas de fil de messages commun acheteur–exportateur en Modèle A : [data-model.md](../backend/data-model.md) §5.16, **marqué provisoire**. La structure juridique n'est pas choisie par l'équipe technique : validation du responsable produit, et si nécessaire d'un conseil juridique, **avant de finaliser** ce modèle. |
| approved_by / approved_at | — |

### Q-66 — Traductions

| Champ | Valeur |
|---|---|
| id | Q-66 |
| status | PROPOSED |
| context | Le CdC §58 demande l'anglais et le français, le malgache plus tard, sans reconstruire le frontend. |
| decision | Libellés d'interface, menus, formulaires, messages traduits et formats locaux dans le **frontend (Flutter)**. L'API renvoie des **codes stables**, indépendants de la langue (exemple : `verification_status = "IN_REVIEW"`). Les contenus à traduire (catégories, attributs) suivent une stratégie explicite, jamais une traduction improvisée par endpoint. Dates, nombres et montants sont formatés à l'affichage, sans altérer les valeurs stockées. |
| rationale | Séparation claire entre données et présentation. |
| affected_modules | tous ; products (libellés des catégories et attributs) |
| consequences | Libellés de référence stockés par langue (JSON par locale) dans `products`. Les codes sont en MAJUSCULES, à l'image des exemples de la réponse : cela remplace la casse minuscule proposée au Jour 2 (D-19), point à confirmer (CF-07). Le frontend mentionné est Flutter, alors que `roadmap.md` prévoit Next.js (CF-05). |
| approved_by / approved_at | — |

### Q-67 — Mode DEMO

| Champ | Valeur |
|---|---|
| id | Q-67 |
| status | PROPOSED |
| context | Le CdC §68 demande un mode DEMO clairement identifié, jamais mélangé aux données réelles. |
| decision | Environnement, base, stockage et secrets **séparés** de la production. Activation réservée à un admin MadaSource ou à un opérateur autorisé. Accès sur invitation ou par comptes de démonstration. Données synthétiques uniquement. Emails désactivés, ou redirigés vers une capture isolée. Simulations clairement identifiées, préfixe `DEMO-` possible, sans remplacer l'isolation. Aucun accès aux ressources de production. Bannière DEMO dans l'interface. Un indicateur envoyé par le frontend ne fait jamais basculer une session entre DEMO et production. |
| rationale | Isolation totale ; conforme à D-18 et S-57. |
| affected_modules | socle (configuration), toutes les simulations |
| consequences | Aucune colonne « démo » dans le modèle de données : l'isolation est physique. |
| approved_by / approved_at | — |

### Q-68 — Données personnelles

| Champ | Valeur |
|---|---|
| id | Q-68 |
| status | PROPOSED — validation juridique nécessaire |
| context | Acheteurs européens (RGPD) et loi malgache. Le CdC §60-61 demande sécurité et séparation public/privé. |
| decision | Mécanismes techniques prévus en V1, **sans déclaration de conformité** : minimisation ; documentation des finalités, catégories, destinataires et durées ; base légale à valider par un juriste ; conservation par catégorie ; procédures d'accès, de rectification, d'export et d'effacement ; pas de copie inutile de données personnelles dans l'audit ; gestion des incidents. En cas d'effacement : supprimer quand c'est applicable, anonymiser ou pseudonymiser les journaux, ne conserver que ce qu'une obligation légale ou un litige justifie, et garder une trace minimale de la décision sans recopier les données supprimées. **Aucune durée de conservation arbitraire.** |
| rationale | Respect des droits des personnes sans promettre une conformité non évaluée. |
| affected_modules | auth, organizations, buyers, exporters, messages, documents, audit, admin |
| consequences | Inventaire des données personnelles dans [data-classification.md](../backend/data-classification.md). Audit par identifiants seulement. Table proposée `privacy_requests` (suivi des demandes). Les durées restent `À VALIDER` (Q-69). |
| approved_by / approved_at | — |

### Q-93 — Ordre de construction

| Champ | Valeur |
|---|---|
| id | Q-93 |
| status | PROPOSED, avec un point non résolu |
| context | Des modules de bas niveau sont construits après des modules qui les utilisent ([module-boundaries.md](../backend/module-boundaries.md) §11). |
| decision | Construire les fondations avant les modules qui en dépendent et tenir un graphe explicite ([dependency-graph.md](../backend/dependency-graph.md)). Ordre proposé en 15 étapes, de l'analyse jusqu'aux tests de bout en bout. Avant chaque jour : vérifier les dépendances, confirmer que les prérequis existent et sont testés, ajuster l'ordre sans étendre silencieusement le périmètre, documenter tout changement de séquence. La création du Trade attend que la quotation, la négociation et les règles du modèle commercial soient stables. |
| rationale | Éviter de construire sur des fondations absentes. |
| affected_modules | tous |
| consequences | **Point non résolu** (CF-08) : l'ordre proposé place les documents (étape 12) après la vérification (étape 5), alors que la vérification examine des documents (CdC §8, RJ 15). Il faut soit un noyau minimal du coffre documentaire anticipé, soit un rétro-branchement au jour des documents. Décision attendue avant le Jour 14. |
| approved_by / approved_at | — |

## 2. Conflits et écarts détectés

| ID | Proposition | Source contredite | Traitement proposé |
|---|---|---|---|
| CF-01 | Q-12 : statuts de vérification UNVERIFIED, IN_REVIEW, VERIFIED, REJECTED, EXPIRED | CdC §8 : Pending, Verified, Rejected, Expired, **Suspended** | Le CdC n'est pas remplacé. Les enregistrements de vérification gardent les statuts du CdC. Le statut de vérification **de l'organisation** est dérivé : UNVERIFIED en l'absence d'enregistrement ; IN_REVIEW correspond à Pending (nom à choisir) ; SUSPENDED est conservé. À valider. |
| CF-02 | Q-12 : compte exportateur PENDING_ACTIVATION, ACTIVE, SUSPENDED, CLOSED | CdC §10 : compte acheteur Pending, Active, Suspended, **Blocked** | Les deux listes sont conservées, chacune pour sa capacité (BUYER selon le CdC, EXPORTER selon Q-12). L'harmonisation (Blocked contre Closed, Pending contre PENDING_ACTIVATION) est à valider. |
| CF-03 | Q-10 : rôles OWNER et MEMBER ; Buyer et Exporter deviennent des capacités | CdC §53 : rôles minimaux Buyer, Exporter, MadaSource Admin ; « Permissions must be role-based » | Écart de terminologie, pas de fond : les permissions restent fondées sur des rôles (rôle d'adhésion × capacité, ou rôle de plateforme). À confirmer. |
| CF-04 | Q-37 : suffixe aléatoire | Exemples du CdC §16, §22, §66 d'apparence séquentielle | Les exemples du CdC ne sont pas une exigence de séquentialité, mais le format visible change : à valider (Q-37). |
| CF-05 | Q-66 : frontend Flutter | `roadmap.md` §0 : Next.js, TypeScript | Sans effet sur le backend. Technologie du frontend à confirmer. |
| CF-06 | Q-25 : destination, Incoterm et livraison par ligne | CdC §12 : ces champs sont ceux de la RFQ | Conservés dans l'en-tête de la RFQ (CdC), avec une surcharge facultative par ligne. |
| CF-07 | Q-66 : codes en MAJUSCULES (exemple `IN_REVIEW`) | D-19 et [api-conventions.md](../backend/api-conventions.md) §8 (Jour 2) : codes en minuscules | Proposition de l'équipe, pas du CdC : les codes en MAJUSCULES sont adoptés au Jour 3 (PROPOSED) et la convention est mise à jour. |
| CF-08 | Q-93 : documents à l'étape 12, après la vérification (étape 5) | CdC §8 (documents examinés), RJ 15 | Non résolu : décision attendue avant le Jour 14. |
| CF-09 | Q-25 : code de catégorie « CLOVE » | CdC §5 « CLOVES », §71 `CLOVES_ENABLED` | Le code `CLOVES` est conservé, aligné sur le CdC. |

## 3. Décisions du Jour 2 concernées

Si les propositions ci-dessus sont approuvées :

| Décision du Jour 2 | Effet |
|---|---|
| D-16 (compteur annuel des références) | SUPERSEDED par Q-37 |
| S-33 (organisation interne MadaSource pour les admins) | SUPERSEDED par Q-74 |
| D-28 (statut de compte porté par l'organisation) | Précisée : statut porté par chaque capacité de l'organisation (Q-09, Q-12), toujours dans `organizations` |
| D-19 (codes en minuscules) | SUPERSEDED par Q-66 (codes en MAJUSCULES, CF-07) |
| S-24, S-47 (valeurs de visibilité `owner`, `buyer_side`…) | Remplacées par la classification de Q-82, complétée par `PUBLIC` pour les médias du marketplace (à valider) |
| Attribution des rôles (`MembershipRole` dans `access_control`) | Remplacée par le rôle porté par l'adhésion et par les rôles de plateforme (Q-10) |
