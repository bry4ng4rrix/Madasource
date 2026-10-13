# Glossaire du domaine — MadaSource

Jour 1 · 2026-10-12

Le terme anglais est celui qui sera utilisé dans le code, l'API et les statuts. Le terme français est celui de la documentation et des échanges avec le client.

## 1. Acteurs et organisation

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Organization | Organisation | Entité juridique cliente (société acheteuse ou exportatrice). Unité d'isolation des données. Proposé : une organisation interne MadaSource pour les administrateurs (Q-74). | CdC §54 |
| User | Utilisateur | Personne disposant d'un compte, membre d'une organisation. Appartenance à plusieurs organisations : Q-74. | CdC §54 |
| Membership | Adhésion | Lien entre un utilisateur, une organisation et un rôle. | RJ 9 |
| Organization capability (`BUYER`, `EXPORTER`) | Capacité commerciale | (J3, PROPOSED) Fonction exercée par une organisation sur la plateforme : acheteuse, exportatrice, ou les deux. Porte le statut du compte pour cette fonction. À ne pas confondre avec la capacité de production (Capacity Record). | Q-09, Q-12 |
| Membership role (`OWNER`, `MEMBER`) | Rôle d'adhésion | (J3, PROPOSED) Rôle d'un utilisateur dans une organisation : OWNER gère le profil, les membres et les invitations ; MEMBER utilise les fonctions autorisées. | Q-10 |
| Invitation | Invitation | (J3, PROPOSED) Proposition d'adhésion envoyée par un OWNER, à usage unique, avec expiration. | Q-10 |
| Platform role (`MADASOURCE_ADMIN`) | Rôle de plateforme | (J3, PROPOSED) Rôle d'un administrateur MadaSource, indépendant de toute organisation cliente. | Q-10, Q-74 |
| Active organization | Organisation active | (J3, PROPOSED) Organisation dans le contexte de laquelle une requête est autorisée, pour un utilisateur membre de plusieurs organisations. | Q-74 |
| Role | Rôle | Ensemble de permissions. V1 : Buyer, Exporter, MadaSource Admin. | CdC §53 |
| Permission | Permission | Droit élémentaire d'effectuer une action sur un type de ressource. | CdC §53 |
| Buyer / International Buyer | Acheteur international | Organisation qui importe et achète des produits malgaches via la plateforme. | CdC §2, §10 |
| Exporter / Malagasy Exporter | Exportateur malgache | Organisation malgache qui vend et exporte des produits via la plateforme. | CdC §2, §11 |
| MadaSource Admin | Administrateur MadaSource | Membre du personnel MadaSource qui opère la plateforme. | CdC §34 |
| Partner | Partenaire | Prestataire tiers (banque, logistique, inspection, assurance…). Hors V1. | CdC §53, §57 |
| Producer / Collector / Cooperative | Producteur / Collecteur / Coopérative | Acteurs amont de la filière. Modules futurs. | CdC §71 |
| Buyer Profile | Profil acheteur | Informations de l'organisation acheteuse (CdC §10). | CdC §10 |
| Exporter Profile | Profil exportateur | Informations publiques et privées de l'organisation exportatrice (CdC §7, §11). | CdC §7 |
| Tenant / multi-tenant | Multi-organisation | Principe selon lequel les données de chaque organisation sont isolées. | CdC §54 |

## 2. Vérification et confiance

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Verification Record | Enregistrement de vérification | Décision de vérification : niveau, dates, documents examinés, administrateur, notes, statut. | CdC §8 |
| Verification Level | Niveau de vérification | 1 Profile Verified, 2 Business Verified, 3 Export Verified, 4 MadaSource Premium Verified. | CdC §8 |
| Profile Verified | Profil vérifié | Niveau 1 : informations de base de la société vérifiées. | CdC §8 |
| Business Verified | Entreprise vérifiée | Niveau 2 : immatriculation et documents de la société examinés. | CdC §8 |
| Export Verified | Exportateur vérifié | Niveau 3 : niveau 2 + capacité d'export et documents associés examinés. | CdC §8 |
| MadaSource Premium Verified | Vérification Premium MadaSource | Niveau 4 : vérification complémentaire (documents, inspections, due diligence). | CdC §8 |
| Digital Exporter Passport | Passeport numérique de l'exportateur | Profil public MadaSource à URL stable, accompagné d'un QR code unique. Référence de confiance indépendante pour l'exportateur. | CdC §9 |
| NEW ON MADASOURCE | Nouveau sur MadaSource | Mention affichée tant que l'historique de transactions est insuffisant pour des avis significatifs. | CdC §42 |

## 3. Produits

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Vanilla | Vanille | Catégorie V1. | CdC §5 |
| Cloves | Girofle (clous de girofle) | Catégorie V1. | CdC §5 |
| Cocoa | Cacao | Catégorie V1. | CdC §5 |
| Product Category | Catégorie de produit | Famille de produits portant ses propres attributs qualité. | CdC §5-6 |
| Product / Product Listing | Produit / Offre catalogue | Offre d'un exportateur dans une catégorie : données générales, commerciales et qualité. La distinction Product / ProductListing (CdC §55) est à trancher au Jour 3. | CdC §6, §55 |
| Product Specification / Attribute | Spécification / Attribut | Caractéristique propre à une catégorie (grade, humidité, taille, pureté, traitement…). | CdC §6 |
| Grade | Grade | Classe de qualité commerciale. Valeurs admises par catégorie à définir (Q-18). | CdC §6 |
| Moisture | Humidité | Teneur en eau du produit. Unité et méthode à définir (Q-18). | CdC §6 |
| Size | Taille | Dimension caractéristique (par exemple la longueur des gousses pour la vanille). Définition par catégorie à valider (Q-18). | CdC §6 |
| Purity | Pureté | Proportion de produit conforme (absence de corps étrangers). Définition par catégorie à valider (Q-18). | CdC §6 |
| Processing type | Type de traitement | Mode de préparation ou de transformation du produit. | CdC §6 |
| Certification | Certification | Attestation tierce (par exemple Organic, citée en exemple). Liste à valider (Q-20). | CdC §6, §15 |
| Capacity / Capacity Record | Capacité | Quantité qu'un exportateur peut fournir, éventuellement par période. | CdC §7, §55 |
| Available quantity | Quantité disponible | Stock ou volume proposé pour une offre catalogue. | CdC §6 |
| MOQ (Minimum Order Quantity) | Quantité minimale de commande | Plus petite quantité qu'un exportateur accepte de vendre. | CdC §6 |
| Unit | Unité | Unité de quantité (kg, tonne). « T » dans les exemples du CdC, présumé tonne métrique (Q-21). | CdC §6, §19 |
| Packaging | Emballage | Conditionnement demandé ou proposé. | CdC §5, §12 |
| Price indication | Indication de prix | Prix indicatif affiché au catalogue, non engageant. Nature et visibilité : Q-06. | CdC §5-6 |
| Payment terms | Conditions de paiement | Modalités de règlement proposées ou acceptées. | CdC §6, §16 |
| Lead time | Délai | Délai entre la confirmation et la mise à disposition ou l'expédition. | CdC §14, §16 |

## 4. RFQ, matching, quotation, négociation

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| RFQ (Request for Quotation) | Demande de cotation | Besoin d'achat structuré émis par un acheteur. Identifiant du type `RFQ-2026-0012` (format exact : Q-37). | CdC §12, §66 |
| RFQ Item | Ligne de RFQ | Produit demandé dans une RFQ (entité du CdC §55 ; RFQ multi-produits : Q-25). | CdC §55 |
| Natural Language RFQ | RFQ en langage naturel | Saisie libre convertie en champs structurés. Hors V1 proposé (Q-29). | CdC §13 |
| Matching / Supplier Matching | Mise en correspondance | Identification déterministe des exportateurs compatibles avec une RFQ. | CdC §14 |
| RFQ Match / Match score | Correspondance / Score | Résultat du matching pour un exportateur : score en pourcentage et raisons. | CdC §14 |
| RFQ Inbox | Boîte de réception RFQ | Liste des RFQ adressées à un exportateur. Actions : Respond, Decline, Ask Question. | CdC §15 |
| Quotation / Quote | Offre de prix, quotation | Proposition commerciale d'un exportateur en réponse à une RFQ. Identifiant du type `MSQ-2026-000145` (format exact : Q-37). | CdC §16 |
| Quote Item / Quotation Line | Ligne de quotation | Détail d'une quotation (produit, quantité, prix unitaire…). | CdC §55, RJ 3 |
| Validity | Validité | Période pendant laquelle une quotation ou un coût est valable. Statuts : Active, Expiring, Expired. | CdC §18 |
| Supplier Cost / Exporter net price | Coût fournisseur / Prix net exportateur | Prix contractuel net fourni par l'exportateur. Confidentiel vis-à-vis de l'acheteur. | CdC §2, §17 |
| External Costs | Coûts externes | Logistique (fret), assurance, autres coûts applicables, chacun avec sa source et sa validité. | CdC §17, §33 |
| Cost source | Source de coût | Provenance d'un prix externe : source, fournisseur, date, validité, statut de confirmation. | CdC §33 |
| MadaSource Margin | Marge MadaSource | Marge commerciale ajoutée par MadaSource en Modèle A. Strictement interne. | CdC §2, §17 |
| Commission / Service fee | Commission / Frais de service | Rémunération contractuelle de MadaSource en Modèle B. | CdC §2 |
| Final Buyer Price / Commercial price | Prix final acheteur / Prix commercial | Prix présenté à l'acheteur. | CdC §2, §17 |
| Commercial Price Engine | Moteur de prix | Calcul configurable du prix final à partir des composantes. | CdC §17 |
| Model A — Commercial Reseller / Trader | Modèle A — Revendeur | MadaSource achète au prix net et revend avec sa marge. | CdC §2 |
| Model B — Intermediary | Modèle B — Intermédiaire | MadaSource met en relation et perçoit une commission ou des frais. | CdC §2 |
| Incoterm | Incoterm | Règle de la Chambre de commerce internationale qui répartit coûts et risques entre vendeur et acheteur. V1 : FOB, CFR, CIF. Version de référence (Incoterms® 2020 ?) : Q-73. | CdC §32 |
| FOB (Free On Board) | Franco à bord | Le vendeur livre la marchandise à bord du navire, au port d'embarquement convenu. Fret principal et assurance à la charge de l'acheteur. | CdC §32 |
| CFR (Cost and Freight) | Coût et fret | Le vendeur paie le fret jusqu'au port de destination. Le risque passe à l'acheteur au chargement à bord. | CdC §32 |
| CIF (Cost, Insurance and Freight) | Coût, assurance et fret | CFR + assurance souscrite par le vendeur jusqu'au port de destination. Base CIF = prix produit + fret + assurance. | CdC §32 |
| Negotiation | Négociation | Suite de propositions entre acheteur et exportateur, à partir d'une quotation. | CdC §20 |
| Counteroffer / Negotiation Offer | Contre-offre / Proposition | Proposition commerciale d'une partie dans une négociation. Immuable. | CdC §20-21 |
| Acceptance | Acceptation | Accord d'une partie sur la dernière proposition de l'autre, qui déclenche la création du Trade. | CdC §20, §22 |
| Negotiation History | Historique de négociation | Quotation d'origine, contre-offres, horodatages, auteurs, prix, quantités, conditions, messages, termes acceptés. | CdC §21 |

## 5. Trade et opérations

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Trade | Transaction | Opération commerciale confirmée entre un acheteur et un exportateur, née d'une acceptation. | CdC §22-23 |
| Trade ID | Identifiant de transaction | Référence centrale unique du type `MST-2026-000145` (format exact : Q-37), à laquelle se rattachent tous les objets du Trade. | CdC §22, §66 |
| Trade Item | Ligne de transaction | Détail produit d'un Trade. | CdC §55 |
| Trade Agreement (`SALE`, `SUPPLY`, `DIRECT`) | Convention | (J3, provisoire) Relation commerciale d'un Trade, avec ses propres prix et termes figés. Modèle A : vente acheteur ↔ MadaSource (`SALE`) et approvisionnement MadaSource ↔ exportateur (`SUPPLY`). Modèle B : relation directe (`DIRECT`). | Q-82 (PROPOSED) |
| Trade Status | Statut de transaction | État de la machine d'état du Trade (CdC §24). | CdC §24 |
| Trade Event | Événement de transaction | Entrée immuable de l'historique d'un Trade. | CdC §25, RJ 28 |
| Trade Journey / Timeline | Parcours de transaction / Chronologie | Vue chronologique des événements, de la RFQ à la clôture. | CdC §25 |
| Trade Dashboard | Tableau de bord de transaction | Vue centralisée d'un Trade : statut, timeline, documents, paiement, expédition, actions. | Planning étape 6 |
| Payment Record | Enregistrement de paiement | Trace d'un paiement (référence, montant, devise, date, justificatif, statut, confirmation admin), sans flux financier. | CdC §30 |
| Payment voucher | Justificatif de paiement | Document attestant un paiement (avis de virement…). | CdC §30 |
| Shipment | Expédition | Envoi physique lié à un Trade, saisi manuellement en V1. | CdC §31 |
| Tracking Event | Événement de suivi | Changement de statut d'une expédition, saisi manuellement en V1. | CdC §55 |
| Carrier | Transporteur | Compagnie qui achemine la marchandise. | CdC §31 |
| Shipping method | Mode d'expédition | Maritime, aérien, etc. Valeurs à définir. | CdC §31 |
| Container number | Numéro de conteneur | Identifiant du conteneur maritime. | CdC §31 |
| Tracking number | Numéro de suivi | Référence de suivi auprès du transporteur. | CdC §31 |
| Destination port | Port de destination | Port d'arrivée demandé (par exemple Hambourg). | CdC §12 |
| Sample Request | Demande d'échantillon | Demande d'un échantillon avant une commande importante. | CdC §27 |
| Inspection | Inspection | Contrôle de la marchandise par un tiers. Étape du Trade Journey ; intégration future. | CdC §25, §57 |

## 6. Documents et communication

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Document Vault | Coffre documentaire | Stockage centralisé et contrôlé des documents. | CdC §26 |
| Document Category | Catégorie de document | Commercial, Company, Quality, Export, Shipping, Payment, Certification. | CdC §26 |
| Document Version | Version de document | Version successive d'un même document. | CdC §26, §55 |
| Conversation | Conversation | Fil de messages entre acheteur et exportateur, rattaché à un contexte (RFQ, quotation, négociation, Trade, échantillon). | CdC §28 |
| Message | Message | Élément d'une conversation : auteur, contenu, horodatage. | CdC §28 |
| Notification | Notification | Avis in-app généré par un événement. Email et push préparés. | CdC §29 |

## 7. Réputation, exceptions, administration

| Terme (code) | Français | Définition | Source |
|---|---|---|---|
| Review / Rating | Avis / Note | Évaluation réciproque après un Trade terminé, sur six critères. | CdC §42 |
| Performance Metrics | Indicateurs de performance | Mesures calculées sur données réelles (taux de réponse, délais, annulations, litiges…). | CdC §43-44 |
| Exception | Exception | Anomalie opérationnelle suivie dans l'Exception Center (paiement en retard, document manquant…). | CdC §40 |
| Exception Center | Centre d'exceptions | Espace admin de traitement des exceptions. | CdC §40 |
| Dispute | Litige | Contestation formelle ouverte par une partie sur un Trade. | CdC §41 |
| Audit Log | Journal d'audit | Trace non modifiable des actions importantes. | CdC §52 |
| Favorites | Favoris | Produits, exportateurs et quotations enregistrés par un acheteur. | CdC §51 |
| Repeat Order / Reorder | Réapprovisionnement | Suggestion de nouvelle RFQ à partir de l'historique. Futur. | CdC §65 |

## 8. Plateforme et conventions

| Terme | Définition | Source |
|---|---|---|
| Feature flag | Interrupteur de configuration qui active ou désactive une catégorie ou un module. | CdC §71 |
| Visibility (`BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`) | (J3, PROPOSED) Classification d'un document ou d'un texte partagé, qui restreint l'audience de lecture sans jamais l'étendre. Voir [data-classification.md](data-classification.md). | Q-82 |
| PROPOSED / APPROVED / SUPERSEDED | Statuts du [registre des décisions](../decisions/architecture-decisions.md) : proposition non approuvée, décision approuvée, décision remplacée. | Q-NN |
| DEMO MODE | Mode démonstration clairement identifié, qui simule certains services externes sans jamais présenter une donnée simulée comme réelle. | CdC §68 |
| Integration layer | Couche d'intégration par laquelle passeront les API tierces futures. | CdC §57 |
| API-first | Conception où toute fonctionnalité est d'abord exposée par l'API. | CdC §56 |
| V1 | Premier périmètre opérationnel (voir [v1-scope.md](v1-scope.md)). | CdC « Final requirement » |
| Phase 1 à 4 | Core, Operations, Integrations, Intelligence. | CdC §69 |
| `À VALIDER` | Décision absente des sources, à trancher par le client avant implémentation. | RJ section 1 |
| Défini / Déduit / Proposé | Statut de traçabilité d'une règle : écrite dans une source, tirée d'un exemple, ou absente et proposée. | Ce dossier |
| CdC §N | Section N du cahier des charges client. | Ce dossier |
| RJ N / RFS J N | Jour N de la roadmap backend / de la roadmap full-stack. | Ce dossier |
