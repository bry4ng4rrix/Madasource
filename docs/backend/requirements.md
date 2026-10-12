# Exigences fonctionnelles et non fonctionnelles — backend MadaSource

Jour 1 · 2026-10-12 · Statut : brouillon à valider par le client

## 1. Objet et sources

Ce document transforme le cahier des charges en exigences backend identifiées et traçables. Il ne contient aucune décision technique : l'architecture est l'objet du Jour 2, le modèle de données du Jour 3.

| Abréviation | Source | Version |
|---|---|---|
| CdC §N | « MadaSource — Complete Platform Architecture & Functional Requirements » (PDF, 34 p., 77 sections + « Final requirement ») | généré le 2026-08-28 |
| Planning §N | `planning.md` — planning client | 1.0 |
| RJ N | `roadmap_backend_fastapi.md` — Jour N de la roadmap backend | non versionnée |
| RFS J N | `roadmap.md` — Jour N de la roadmap full-stack initiale | 1.0 |

Ordre de priorité en cas de conflit : CdC > Planning > roadmap backend. Les contradictions sont listées dans [risks-and-open-questions.md](risks-and-open-questions.md#3-contradictions-entre-sources), jamais tranchées ici.

Statut de chaque exigence :
- **Défini** : écrit explicitement dans une source.
- **Déduit** : tiré d'un exemple ou du croisement de deux sources ; à confirmer.
- **À VALIDER** : la source signale le besoin sans le définir. La question correspondante (Q-NN) figure dans [risks-and-open-questions.md](risks-and-open-questions.md).

Documents liés : [v1-scope.md](v1-scope.md) · [actors-and-permissions.md](actors-and-permissions.md) · [business-rules.md](business-rules.md) · [workflows.md](workflows.md) · [domain-glossary.md](domain-glossary.md).

## 2. Vision et objectif

- MadaSource n'est pas qu'un marketplace. La plateforme doit évoluer progressivement : marketplace → découverte fournisseurs → RFQ et matching → quotation et négociation → gestion des transactions → facilitation numérique du commerce → infrastructure numérique du commerce pour Madagascar (CdC §1, §73).
- Objectif fondamental : un acheteur international découvre un exportateur malgache, demande une quotation, compare, négocie, confirme une transaction et suit tout le parcours depuis une plateforme centralisée (CdC §1, Planning §1).
- Critère d'acceptation principal : un acheteur international et un exportateur malgache peuvent mener un parcours B2B structuré sans quitter la plateforme pour le flux principal (CdC §74).
- Principe UX : la complexité du commerce international reste dans la plateforme, pas dans l'expérience utilisateur (CdC §72). Côté backend, cela se traduit par une API qui orchestre les étapes, sans exiger du client qu'il les coordonne.

## 3. Modules du cahier des charges et correspondance backend

Le CdC décrit 24 modules (A à X, CdC §3). Le tableau indique le module backend prévu (structure de RJ, section 2) et le statut V1, détaillé dans [v1-scope.md](v1-scope.md).

| CdC | Module | Module backend | V1 |
|---|---|---|---|
| A | Public Website | `marketplace` (endpoints publics) ; pages = frontend | Partiel : endpoints publics seulement |
| B | Authentication & Identity | `auth`, `organizations`, `access_control` | Oui |
| C | Buyer Portal | `buyers` (+ agrégations de tableau de bord) | Oui ; agrégations de tableau de bord : Q-63 |
| D | Exporter Portal | `exporters` (+ agrégations de tableau de bord) | Oui ; agrégations de tableau de bord : Q-63 |
| E | Product Marketplace | `products`, `marketplace` | Oui |
| F | RFQ Engine | `rfqs` | Oui (hors RFQ en langage naturel) |
| G | Supplier Matching Engine | `matching` | Oui, déterministe |
| H | Quotation Engine | `quotations` | Oui |
| I | Negotiation Engine | `negotiations` | Oui |
| J | Trade Management Engine | `trades` | Oui |
| K | Trade Journey / Timeline | `trades` (TradeEvent) | Oui |
| L | Document Management | `documents` | Oui |
| M | Sample Request Management | `samples` | **À VALIDER** (Q-53) |
| N | Internal Messaging | `messages` | Oui |
| O | Notification System | `notifications` | Oui (in-app) |
| P | Payment Management | `payment_records` | Oui (enregistrement seulement) |
| Q | Logistics & Shipment Tracking | `shipments` | Oui (saisie manuelle) |
| R | Supplier Verification | `verification` | Oui |
| S | Reputation & Performance | `reviews` | Oui |
| T | MadaSource AI Assistant | — | Non (Phase 4) |
| U | Administration Console | `admin` | Oui (API) |
| V | Partner Management | — | Non (préparé) |
| W | Reporting & Analytics | `admin` | **À VALIDER** (Q-62) |
| X | Audit & Compliance | `audit` | Oui (audit) ; conformité réglementaire : non |

Sont aussi décrits sans lettre de module : exceptions et litiges (CdC §40-41, module `exceptions`), favoris (§51), recherche globale (§50), réapprovisionnement (§65), intelligence commerciale (§64), i18n (§58), devises (§59), mode DEMO (§68) et feature flags (§71).

## 4. Exigences fonctionnelles

### 4.1 Identité, organisations et accès (IAM)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-IAM-01 | Le système est organisé autour des organisations, pas seulement des utilisateurs : Organization → Users → Roles → Permissions. | CdC §54 | Défini |
| REQ-IAM-02 | Une organisation peut compter plusieurs utilisateurs aux permissions différentes (ex. : directeur, responsable commercial, responsable des opérations). | CdC §54 | Défini (activation V1 : Q-10) |
| REQ-IAM-03 | Rôles minimaux : Buyer, Exporter, MadaSource Admin. | CdC §53 | Défini |
| REQ-IAM-04 | L'architecture prévoit les rôles futurs Operations Admin, Compliance Admin, Finance Admin, Logistics Admin, Super Admin et Partner, sans les activer. | CdC §53, RJ 9 | Défini |
| REQ-IAM-05 | Les permissions sont fondées sur les rôles et vérifiées côté serveur. | CdC §53, §60 | Défini |
| REQ-IAM-06 | Inscription, connexion, rafraîchissement de session, déconnexion et révocation, utilisateur courant, changement et réinitialisation de mot de passe. | RJ 10 | Défini (durées de vie des tokens, politique de mot de passe : Q-76) |
| REQ-IAM-07 | Vérification d'email par jeton à usage unique avec expiration. | RJ 11 | Défini (lien avec le statut du compte : Q-13) |
| REQ-IAM-08 | Création sûre du premier administrateur, sans route publique de bootstrap. | RJ 10 | Défini |

### 4.2 Acheteurs (BUY)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-BUY-01 | Inscription acheteur : nom de société, pays, région, type d'activité, site web, personne de contact, email, téléphone, adresse professionnelle, marchés d'importation, produits d'intérêt. | CdC §10 | Défini (champs obligatoires : Q-22 par analogie, à préciser) |
| REQ-BUY-02 | Statuts du compte acheteur : Pending, Active, Suspended, Blocked. | CdC §10 | Défini (transitions : Q-11) |
| REQ-BUY-03 | L'acheteur ne modifie que le profil de sa propre organisation. | RJ 13 | Défini |
| REQ-BUY-04 | Indicateurs acheteur calculés sur données réelles : transactions terminées, fiabilité de paiement, taux d'annulation, taux de litige, note donnée par les exportateurs. | CdC §44, RJ 35 | Défini |
| REQ-BUY-05 | Favoris : produits, exportateurs, quotations. | CdC §51, §48 | **À VALIDER** (Q-63) |

### 4.3 Exportateurs (EXP)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-EXP-01 | Onboarding exportateur : société, contact, email, téléphone, adresse, région, immatriculation, informations fiscales, documents d'export, expérience à l'export, produits, capacité, certifications, informations bancaires et de paiement. | CdC §11 | Défini |
| REQ-EXP-02 | Profil professionnel : nom, logo, description, localisation, coordonnées, immatriculation, années d'activité, expérience et marchés d'export, produits, capacité disponible, certifications, statut de vérification, indicateurs de performance, avis. | CdC §7 | Défini |
| REQ-EXP-03 | Les documents sensibles ne sont jamais visibles publiquement. | CdC §11, §60 | Défini |
| REQ-EXP-04 | Séparation stricte du profil public et des informations privées (voir la matrice de visibilité). | CdC §61, RJ 14 | Défini |
| REQ-EXP-05 | Enregistrements de capacité (CapacityRecords). | CdC §55, §49 | Défini (structure : Jour 3) |
| REQ-EXP-06 | Indicateurs exportateur calculés sur données réelles : taux de réponse, délai moyen de réponse, taux d'acceptation des quotations, transactions terminées, taux d'annulation, taux de litige, note acheteur. Ils alimenteront le matching futur. | CdC §43 | Défini |

### 4.4 Vérification et Digital Exporter Passport (VER)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-VER-01 | Quatre niveaux : 1 Profile Verified, 2 Business Verified, 3 Export Verified, 4 MadaSource Premium Verified. | CdC §8 | Défini (critères : Q-15) |
| REQ-VER-02 | Enregistrer : niveau, date de vérification, date d'expiration le cas échéant, documents examinés, administrateur responsable, notes, statut. | CdC §8 | Défini |
| REQ-VER-03 | Statuts : Pending, Verified, Rejected, Expired, Suspended. | CdC §8 | Défini (transitions : voir workflows.md) |
| REQ-VER-04 | Seuls les utilisateurs autorisés décident d'une vérification. Une inscription ne rend jamais un exportateur vérifié automatiquement. | RJ 15 | Défini |
| REQ-VER-05 | Actions admin : examiner les candidatures et les documents, vérifier, attribuer un niveau, approuver, rejeter, suspendre, réactiver. | CdC §36 | Défini |
| REQ-VER-06 | Chaque exportateur vérifié dispose d'une URL de profil public stable (ex. `madasource.com/exporter/company-name`) et d'un QR code unique qui y redirige : le « Digital Exporter Passport ». | CdC §9, RJ 18 | Défini (niveau requis : Q-16 ; format de l'URL : Q-17) |

### 4.5 Produits et marketplace (PRD, MKT)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-PRD-01 | Catégories initiales : Vanilla, Cloves, Cocoa, activables par feature flag. | CdC §5, §71 | Défini |
| REQ-PRD-02 | Données générales : nom, catégorie, description, origine, région d'origine, spécifications, images, documents. | CdC §6 | Défini |
| REQ-PRD-03 | Données commerciales : quantité disponible, unité, MOQ, indication de prix, devise, Incoterm, conditions de paiement, validité de l'offre. | CdC §6 | Défini (visibilité du prix : Q-06) |
| REQ-PRD-04 | Données qualité : grade, paramètres qualité, humidité, taille, pureté, type de traitement, certification. | CdC §6 | Défini |
| REQ-PRD-05 | Attributs spécifiques par produit, car vanille, girofle et cacao n'ont pas les mêmes spécifications. Aucun attribut n'est imposé à toutes les catégories. | CdC §6, RJ 16 | Défini (liste : Q-18) |
| REQ-PRD-06 | Un exportateur ne gère que les produits de son organisation : création, lecture, modification, publication, dépublication, archivage logique. | RJ 17 | Défini (statuts : Q-19) |
| REQ-PRD-07 | Pas de suppression physique d'un produit lié à une RFQ ou à une transaction. | RJ 17 | Défini |
| REQ-MKT-01 | Recherche marketplace par catégorie, pays et origine, qualité, grade, certification, quantité disponible, MOQ, emballage, Incoterm, exportateur, statut de vérification, indication de prix. | CdC §5, RJ 18 | Défini |
| REQ-MKT-02 | Recherche orientée acheteur, priorités : produit, exportateur, qualité, certification, disponibilité, prix, vérification. | CdC §50 | Défini (règle de priorisation et de tri : Q-77) |
| REQ-MKT-03 | Recherche globale (produit, exportateur, RFQ, trade) selon les permissions de l'utilisateur. | CdC §50 | **À VALIDER** (Q-63) |
| REQ-MKT-04 | Les réponses publiques n'exposent jamais coordonnées confidentielles, informations bancaires, documents internes, notes internes ni marges. | CdC §61, RJ 18 | Défini |

### 4.6 RFQ (RFQ)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-RFQ-01 | Création par l'acheteur avec : produit, quantité, unité, qualité, grade, certification, emballage, pays de destination, port de destination, Incoterm, date de livraison cible, prix cible, préférence de paiement, exigences supplémentaires. | CdC §12 | Défini (champs obligatoires : Q-22) |
| REQ-RFQ-02 | Statuts : Draft → Submitted → Matching → Sent to Exporters → Quotations Received → Negotiating → Accepted → Closed. | CdC §12 | Défini (cas d'échec : Q-24) |
| REQ-RFQ-03 | Toute transition est contrôlée par un service serveur qui refuse les changements invalides. | RJ 19 | Défini |
| REQ-RFQ-04 | L'acheteur crée un brouillon, le consulte, le modifie avant soumission, le soumet et liste ses RFQ. Accès limité à l'organisation propriétaire. | RJ 20 | Défini |
| REQ-RFQ-05 | Une RFQ soumise ne peut pas être modifiée librement si cela invalide les matches ou les quotations. | RJ 20 | Défini (règle exacte : Q-23) |
| REQ-RFQ-06 | Inbox exportateur : l'exportateur ne voit que les RFQ qui lui sont adressées ou auxquelles il est autorisé à répondre. Actions : Respond, Decline, Ask Question. Réponses et questions conservées. | CdC §15, RJ 21 | Défini (identité de l'acheteur visible : Q-27) |
| REQ-RFQ-07 | RFQ en langage naturel convertie en champs structurés, avec détection des informations manquantes. | CdC §13 | Hors V1 proposé (Q-29) |
| REQ-RFQ-08 | Identifiant lisible du type `RFQ-2026-0012`. | CdC §66 | Défini (format exact : Q-37) |

### 4.7 Matching (MAT)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-MAT-01 | Après soumission d'une RFQ, identifier les exportateurs compatibles. | CdC §14 | Défini |
| REQ-MAT-02 | Critères du CdC : produit, quantité disponible, capacité, qualité, grade, certification, destination, Incoterm, vérification, prix, délai, performance historique, taux de réponse. RJ 22 ajoute le MOQ. | CdC §14, RJ 22 | Défini, sauf performance historique et taux de réponse : À VALIDER (SRC-16, Q-32) |
| REQ-MAT-03 | Score fondé sur les données réelles de la plateforme et des règles de pondération configurables. Aucun score arbitraire ou aléatoire. | CdC §14 | Défini (pondérations : Q-30) |
| REQ-MAT-04 | Résultat reproductible et explicable : critères utilisés, raisons, date d'exécution. Données manquantes traitées explicitement. | RJ 22, RJ 23, CdC §47 | Défini |
| REQ-MAT-05 | Exécution contrôlée et idempotente, sans doublons incohérents. Consultation et contrôle par l'admin, avec audit. | RJ 23 | Défini (envoi automatique ou validé : Q-31) |
| REQ-MAT-06 | Une IA future pourra assister le matching sans jamais contourner les règles déterministes sans autorisation. | CdC §47 | Hors V1 |

### 4.8 Quotations et prix (QUO, PRC)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-QUO-01 | L'exportateur crée une quotation : Quote ID, produit, quantité, prix unitaire, devise, qualité, grade, certification, emballage, Incoterm, destination, délai, conditions de paiement, validité, conditions supplémentaires. | CdC §16 | Défini |
| REQ-QUO-02 | Identifiant lisible du type `MSQ-2026-000145`. | CdC §16, §66 | Défini (nombre de chiffres incohérent : Q-37) |
| REQ-QUO-03 | Chaque quotation et chaque coût externe conserve : date de création, dernière mise à jour, date d'expiration, source, statut. | CdC §18 | Défini |
| REQ-QUO-04 | Statuts de validité : Active, Expiring, Expired. | CdC §18 | Défini (seuil « Expiring » : Q-35 ; cycle de vie : Q-34) |
| REQ-QUO-05 | Une quotation expirée n'est jamais présentée comme une offre actuelle. | CdC §18 | Défini |
| REQ-QUO-06 | Une quotation expirée ne peut pas être acceptée sans règle explicite et action auditée. | RJ 25 | Défini (règle : Q-36) |
| REQ-QUO-07 | Comparaison côté acheteur : exportateur, prix, qualité, MOQ, certification, Incoterm, délai. Actions : View Offer, Negotiate, Accept. | CdC §19 | Défini |
| REQ-PRC-01 | Moteur de prix distinguant : Supplier Cost, External Costs (logistique, assurance, autres coûts), MadaSource Margin, Final Buyer Price. | CdC §17, §32 | Défini |
| REQ-PRC-02 | Les règles de calcul sont configurables par les administrateurs MadaSource. Aucune marge ni taxe codée en dur. | CdC §17, RJ 24 | Défini (formules : Q-02, Q-03) |
| REQ-PRC-03 | Deux modèles commerciaux : A revendeur (prix net fournisseur + marge MadaSource = prix acheteur), B intermédiaire (commission ou frais de service contractuels). | CdC §2 | Défini (choix et articulation : Q-01) |
| REQ-PRC-04 | Incoterms initiaux FOB, CFR, CIF, extensibles. Base CIF = prix produit + fret + assurance ; les règles commerciales s'appliquent ensuite. | CdC §32 | Défini |
| REQ-PRC-05 | Tout prix fourni par un tiers conserve : source, fournisseur, date, validité, devise, unité, destination, Incoterm, statut de confirmation. Les données périmées ne sont jamais utilisées silencieusement. | CdC §33 | Défini |
| REQ-PRC-06 | Les schémas Buyer ne révèlent jamais les coûts fournisseurs confidentiels ni les marges internes. | CdC §61, RJ 24 | Défini |

### 4.9 Négociation (NEG)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-NEG-01 | L'acheteur soumet une contre-offre, l'exportateur répond par une contre-offre, l'une des parties accepte (exemple CdC §20). | CdC §20, §67, RJ 26 | Défini (champs négociables : Q-38) |
| REQ-NEG-02 | Chaque événement de négociation est stocké. Aucun historique n'est supprimé. | CdC §20 | Défini |
| REQ-NEG-03 | Historique : quotation d'origine, contre-offres, horodatages, utilisateurs, prix, quantités, conditions, messages, termes finaux acceptés. | CdC §21 | Défini |
| REQ-NEG-04 | Contrôle de qui peut agir dans quel état. Pas d'acceptation simultanée de propositions incompatibles (concurrence). | RJ 26 | Défini |
| REQ-NEG-05 | Traduction prix acheteur ↔ prix exportateur en Modèle A. | — | **À VALIDER** (Q-05) |

### 4.10 Trade (TRD)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-TRD-01 | L'acceptation d'une quotation crée automatiquement un Trade avec un Trade ID unique du type `MST-2026-000145`. | CdC §22 | Défini |
| REQ-TRD-02 | Le Trade ID est la référence centrale. RFQ, quotation, documents, messages, paiement et expédition s'y rattachent. | CdC §22, §66 | Défini |
| REQ-TRD-03 | Contenu d'un Trade : Trade ID, acheteur, exportateur, produit, quantité, qualité, prix, devise, Incoterm, destination, conditions de paiement, livraison cible, documents, messages, statut de paiement, statut d'expédition, statut du Trade, historique d'événements. | CdC §23 | Défini |
| REQ-TRD-04 | Machine d'état : Trade Confirmed → Payment Pending → Payment Confirmed → Preparation → Ready for Shipment → Shipped → In Transit → Delivered → Completed. Exceptions : Cancelled, Disputed, On Hold. | CdC §24 | Défini (acteurs et conditions : Q-41 à Q-44) |
| REQ-TRD-05 | Création idempotente et transactionnelle : un double appel ne crée pas deux Trades. Les termes commerciaux acceptés sont figés. | RJ 27 | Défini |
| REQ-TRD-06 | Timeline : chaque événement stocke date, heure, acteur, action, commentaire et document justificatif le cas échéant. Historique immuable via les opérations normales. | CdC §25, RJ 28 | Défini |
| REQ-TRD-07 | Tableau de bord admin des trades actifs : Trade ID, acheteur, exportateur, produit, quantité, valeur, paiement, documents, expédition, statut courant. | CdC §39 | Défini |

### 4.11 Documents (DOC)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-DOC-01 | Coffre documentaire centralisé. Documents rattachables à : société, RFQ, quotation, trade, expédition. | CdC §26 | Défini |
| REQ-DOC-02 | Catégories : commerciaux, société, qualité, export, expédition, paiement, certification. | CdC §26 | Défini |
| REQ-DOC-03 | Formats acceptés : PDF, JPG, PNG, DOCX. | CdC §26 | Défini (taille maximale : Q-48) |
| REQ-DOC-04 | Stocker : nom, type, propriétaire, date de dépôt, version, statut, Trade ID lié. | CdC §26 | Défini (valeurs de statut : Q-48) |
| REQ-DOC-05 | Stockage abstrait (local en développement, S3-compatible en production), binaires hors de PostgreSQL. Téléchargement privé après autorisation serveur ou URL signée à durée limitée. Type et taille validés, nom de fichier non fiable. | RJ 29, CdC §60 | Défini |

### 4.12 Messagerie et notifications (MSG, NOT)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-MSG-01 | Messagerie sécurisée Buyer ↔ Exporter, rattachable à : RFQ, quotation, négociation, trade, demande d'échantillon. | CdC §28 | Défini |
| REQ-MSG-02 | Historique des conversations préservé. Pièces jointes via le coffre documentaire. | CdC §28, RJ 30 | Défini |
| REQ-MSG-03 | REST suffit en V1, sans WebSocket. Cette limite est documentée. | RJ 30 | Défini |
| REQ-NOT-01 | Notifications automatiques : nouvelle RFQ, nouvelle quotation, contre-offre, quotation acceptée, nouveau Trade, paiement confirmé, nouveau document, statut du Trade modifié, échantillon expédié. | CdC §29 | Défini (destinataires : Q-52) |
| REQ-NOT-02 | In-app en V1. Architecture prête pour l'email et le push. Aucun envoi externe annoncé sans confirmation du fournisseur. | CdC §29, RJ 31 | Défini |

### 4.13 Échantillons (SMP)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-SMP-01 | Workflow : Request Sample → Sample Quotation → Sample Confirmed → Sample Payment → Sample Shipped → Sample Received → Sample Approved / Rejected. | CdC §27 | Défini (inclusion V1 : Q-53) |
| REQ-SMP-02 | Une demande d'échantillon peut être reliée plus tard à une RFQ. | CdC §27 | Défini |

### 4.14 Paiements (PAY)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-PAY-01 | Gestion des paiements sans intégration bancaire directe en V1. MadaSource n'est pas architecturé comme une banque. | CdC §30, Planning §7 | Défini |
| REQ-PAY-02 | Statuts : Pending, Processing, Confirmed, Failed, Refunded. | CdC §30 | Défini (transitions : voir workflows.md) |
| REQ-PAY-03 | Enregistrer : virement bancaire, référence de paiement, justificatif déposé, date, montant, devise, confirmation par l'admin. | CdC §30 | Défini (qui saisit : Q-54) |
| REQ-PAY-04 | Le dépôt d'un justificatif ne vaut pas confirmation automatique. Confirmation et remboursement sont autorisés et audités. | RJ 33 | Défini |
| REQ-PAY-05 | Architecture future : passerelles de paiement, partenaires bancaires, lettres de crédit, mécanismes de type escrow selon le cadre légal, partenaires de financement. | CdC §30 | Hors V1 |

### 4.15 Expéditions (SHP)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-SHP-01 | Saisie manuelle : méthode d'expédition, transporteur, référence, numéro de conteneur, numéro de suivi, origine, destination, départ estimé, arrivée estimée. | CdC §31 | Défini (qui saisit : Q-58) |
| REQ-SHP-02 | Statuts : Pending, Ready for Shipment, Shipped, In Transit, Arrived, Delivered. | CdC §31 | Défini |
| REQ-SHP-03 | Expédition liée au Trade, historique conservé, aucun suivi automatique inventé. | RJ 34 | Défini |
| REQ-SHP-04 | Intégrations futures avec les API des prestataires logistiques. | CdC §31, §57 | Hors V1 |

### 4.16 Réputation, exceptions et litiges (REP, EXC)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-REP-01 | Après une transaction terminée, l'acheteur note l'exportateur et l'exportateur note l'acheteur. | CdC §42 | Défini |
| REQ-REP-02 | Critères : communication, conformité du produit, livraison, documentation, réactivité, expérience de transaction. | CdC §42 | Défini (échelle : Q-59) |
| REQ-REP-03 | Aucune évaluation artificielle. Les nouvelles sociétés affichent « NEW ON MADASOURCE » tant que l'historique est insuffisant. | CdC §42 | Défini (seuil : Q-59) |
| REQ-EXC-01 | Centre d'exceptions. Exemples : paiement en retard, quotation expirée, exportateur sans réponse, document manquant, expédition en retard, litige acheteur, problème de qualité, écart de quantité, commande annulée. | CdC §40 | Défini (statuts : Q-60) |
| REQ-EXC-02 | Actions admin sur une exception : enquêter, assigner, commenter, changer le statut, résoudre, escalader. | CdC §40 | Défini |
| REQ-EXC-03 | Litige ouvert par l'acheteur ou l'exportateur : Trade ID, motif, description, preuves, documents, résolution demandée. Statuts : Open, Under Review, Resolution Proposed, Resolved, Closed. | CdC §41 | Défini |

### 4.17 Administration et audit (ADM, AUD)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-ADM-01 | Modules admin : Dashboard, Buyers, Exporters, Products, RFQs, Matching, Quotations, Negotiations, Trades, Samples, Documents, Payments, Shipments, Verification, Messages, Reviews, Partners, Reports, Settings, Audit Logs. | CdC §34 | Défini (Partners, Reports : Q-62, Q-64) |
| REQ-ADM-02 | Gestion acheteurs : consulter, approuver ou suspendre les comptes, voir société, RFQ, quotations, trades, litiges, gérer le statut. | CdC §35 | Défini |
| REQ-ADM-03 | Gestion RFQ : toutes les RFQ, statut, acheteur, produit, destination, exportateurs compatibles, quotations reçues, âge, RFQ non résolues. Intervention manuelle si nécessaire. | CdC §37 | Défini (périmètre de l'intervention : Q-40) |
| REQ-ADM-04 | Gestion quotations : quotation fournisseur, prix, validité, historique de négociation, statut final. Intervention pour les transactions exceptionnelles ou de forte valeur. | CdC §38 | Défini (seuil : Q-07) |
| REQ-ADM-05 | Indicateurs admin : acheteurs, exportateurs, exportateurs vérifiés, RFQ actives et ouvertes, quotations reçues, trades actifs et terminés, valeur des trades, marge commerciale brute MadaSource, délai moyen de réponse RFQ, top produits, top destinations, performance des exportateurs, exceptions non résolues. | CdC §63 | **À VALIDER** (Q-62) |
| REQ-AUD-01 | Toute action importante génère un événement d'audit. Exemples : RFQ créée, quotation soumise, contre-offre, acceptation, Trade créé, paiement confirmé, document déposé, statut du Trade modifié, exportateur vérifié par l'admin. | CdC §52 | Défini |
| REQ-AUD-02 | Contenu : acteur, action, objet, horodatage, ancienne et nouvelle valeur le cas échéant. | CdC §52 | Défini |
| REQ-AUD-03 | Non modifiable via les endpoints ordinaires. Jamais de mot de passe, de token ni de contenu intégral de document privé. | RJ 12 | Défini (conservation : Q-69) |

### 4.18 Configuration transverse (CFG)

| ID | Exigence | Source | Statut |
|---|---|---|---|
| REQ-CFG-01 | Feature flags : VANILLA_ENABLED, CLOVES_ENABLED, COCOA_ENABLED. Modules futurs désactivés : PRODUCER, COLLECTOR, COOPERATIVE, BANKING, LOGISTICS, INSPECTION, INSURANCE, CUSTOMS. | CdC §71 | Défini |
| REQ-CFG-02 | Langues : anglais et français ; malgache plus tard. Localisation sans reconstruire le frontend. | CdC §58, Planning §9 | Défini (rôle du backend : Q-66) |
| REQ-CFG-03 | Devises : USD et EUR ; MGA, GBP, AED, CNY plus tard. Conversion séparée des données transactionnelles. Un prix historique ne change jamais avec un taux de change. | CdC §59 | Défini (conversion en V1 : Q-65) |
| REQ-CFG-04 | Mode DEMO clairement identifié, capable de simuler confirmation de paiement, statut d'expédition, livraison et confirmation partenaire. Workflow identique au réel. Une transaction simulée n'est jamais affichée comme réelle. | CdC §68 | Défini (mécanisme : Q-67) |
| REQ-CFG-05 | Workflows configurables et couche d'intégration modulaire pour les API futures (banque, paiement, logistique, suivi, inspection, certification, douane, change). | CdC §57, §70 | Défini |

## 5. Exigences non fonctionnelles

| ID | Exigence | Source | Statut |
|---|---|---|---|
| NFR-01 | API-first. Domaines d'API : /auth, /users, /organizations, /products, /exporters, /buyers, /rfqs, /matches, /quotes, /negotiations, /trades, /documents, /samples, /messages, /notifications, /payments, /shipments, /reviews, /admin, /analytics. REST versionnée sous `/api/v1`, OpenAPI. | CdC §56, RJ section 1 | Défini (noms définitifs : Jour 2) |
| NFR-02 | Sécurité : mots de passe protégés, authentification sécurisée, autorisation par rôle, endpoints protégés, validation des entrées et des fichiers, stockage sécurisé des documents, sécurité des sessions, audit, rate limiting, sécurité de la base, stratégie de sauvegarde. Le CdC parle de mots de passe « encrypted » ; RJ 8 précise un hachage par bibliothèque maintenue, qui est la pratique sûre. | CdC §60, RJ 8 | Défini |
| NFR-03 | Séparation des données publiques et privées (voir [actors-and-permissions.md](actors-and-permissions.md#4-visibilité-des-données)). | CdC §61 | Défini |
| NFR-04 | Monolithe modulaire, rôles, workflows configurables, feature flags, modèle de données extensible, couche d'intégration. Pas de fonctionnalité future codée en dur dans la V1. | RJ section 1 (monolithe modulaire), CdC §70, Planning §10 | Défini (voir SRC-17) |
| NFR-05 | Architecture adaptable juridiquement : ne pas supposer que MadaSource est autorisé à exercer des activités réglementées (banque, paiement, assurance, courtage en douane, transit, inspection, certification, export réglementé). | CdC §75 | Défini |
| NFR-06 | Les données (demande, prix, capacités, saisonnalité…) deviendront un actif stratégique : les capturer de façon exploitable, sans construire l'intelligence en V1. | CdC §64 | Défini (analyses : Phase 4) |
| NFR-07 | Principe de sûreté appliqué à tout contenu généré par le système : ne jamais inventer fournisseurs, prix, capacités, certifications, documents, statuts logistiques, paiements ou transactions. Afficher « INFORMATION NOT AVAILABLE » en l'absence de donnée. | CdC §46 (énoncé pour l'IA), RJ 22 (aucun fournisseur inventé, aucune certification supposée) | Déduit : extension du principe de l'IA à tout le système |
| NFR-08 | Montants en Decimal/NUMERIC, dates en UTC timezone-aware, UUID techniques, statuts contraints. | RJ section 1 | Défini |
| NFR-09 | Volumétrie, temps de réponse, disponibilité, RPO/RTO. | — | **À VALIDER** (Q-72) |
| NFR-10 | Conformité aux lois sur les données personnelles (acheteurs européens, Madagascar). | — | **À VALIDER** (Q-68) |

## 6. Modèle de domaine conceptuel

Le CdC §55 liste les entités minimales par domaine. Le tableau ci-dessous en donne les relations conceptuelles. Ces relations sont des **propositions de travail** (statut Proposé), à confirmer au Jour 3. Les cardinalités marquées « ? » dépendent d'une question ouverte. Le modèle physique (tables, clés, index) est l'objet du Jour 3.

| Domaine | Entités (CdC §55) | Relations conceptuelles |
|---|---|---|
| Identity | Users, Organizations, Roles, Permissions (+ Membership, RJ 9) | Organization 1–N Membership N–1 User ; Membership N–1 Role ; Role N–N Permission ; Organization de type Buyer ou Exporter (cumul : Q-09) ; organisation interne MadaSource pour les admins et appartenance d'un utilisateur à plusieurs organisations : Q-74 |
| Buyers | BuyerProfiles | Organization 1–1 BuyerProfile |
| Exporters | Exporters, ExporterProfiles, VerificationRecords, Certifications, CapacityRecords | Organization 1–1 ExporterProfile ; ExporterProfile 1–N VerificationRecord ; 1–N CapacityRecord ; N–N Certification |
| Marketplace | Products, ProductCategories, ProductListings, ProductSpecifications | ProductCategory 1–N Product ; ExporterProfile 1–N Product ; Product 1–N ProductSpecification (attributs par catégorie) ; Product N–N Certification. La distinction Product / ProductListing est à trancher au Jour 3. |
| RFQ | RFQs, RFQItems, RFQMatches | Buyer Organization 1–N RFQ ; RFQ 1–N RFQItem (multi-produits : Q-25) ; RFQ 1–N RFQMatch N–1 Exporter Organization |
| Commercial | Quotes, QuoteItems, Negotiations, CounterOffers | RFQ 1–N Quote ; Exporter Organization 1–N Quote ; Quote 1–N QuoteItem ; Quote 1–0..1 Negotiation ; Negotiation 1–N CounterOffer ; Quote ou CounterOffer 1–N ExternalCost (CdC §33) |
| Trade | Trades, TradeItems, TradeEvents, TradeStatus | Quote acceptée 1–0..1 Trade (plusieurs Trades par RFQ : Q-26) ; Trade 1–N TradeItem ; Trade 1–N TradeEvent |
| Logistics | Shipments, TrackingEvents | Trade 1–N? Shipment (Q-57) ; Shipment 1–N TrackingEvent (saisie manuelle) |
| Payment | Payments, PaymentRecords, PaymentDocuments | Trade 1–N? PaymentRecord (Q-54) ; PaymentRecord 1–N Document (justificatifs) |
| Documents | Documents, DocumentVersions | Document N–1 Organization propriétaire ; Document → 0..1 contexte (Organization, RFQ, Quote, Trade, Shipment) ; Document 1–N DocumentVersion |
| Communication | Conversations, Messages, Notifications | Conversation → 1 contexte (RFQ, Quote, Negotiation, Trade, SampleRequest) ; Conversation 1–N Message ; User 1–N Notification |
| Samples | SampleRequests, SampleShipments | Buyer Org 1–N SampleRequest N–1 Exporter Org ; SampleRequest N–1 Product ; SampleRequest 0..1 → RFQ |
| Reputation | Reviews, Ratings, PerformanceMetrics | Trade terminé 1–0..2 Review (une par sens) ; Review 1–N Rating (critère) ; Organization 1–N PerformanceMetric |
| Administration | AuditLogs, Disputes, Exceptions | AuditLog → acteur et objet ; Exception → 0..1 Trade ou autre objet concerné (quotation, RFQ, exportateur : SRC-19) ; Trade 1–N? Dispute |
| Partners | Partners, PartnerServices, PartnerConfigurations | Hors V1 : aucune table créée sans besoin (RJ section 1) |

Entités transverses à prévoir en conception (Jour 3) : configuration des feature flags, règles de prix configurables (CdC §17), taux de change séparés (CdC §59), séquences des identifiants lisibles.
