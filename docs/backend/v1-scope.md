# Périmètre V1 du backend MadaSource

Jour 1 · 2026-10-12 · Statut : brouillon à valider par le client

## 1. Périmètre opérationnel V1

Défini par le CdC (« Final requirement » et §74) et le Planning §2.

Dans le PDF, la cellule « Core Journey » du « Final requirement » est tronquée (« … → Shipment → D ») et commence à la RFQ. Le CdC §74 donne le parcours complet : DISCOVER en tête, TRACKING entre SHIPMENT et DELIVERY. Le tableau reprend la formulation de la roadmap backend, où « Marketplace » correspond à DISCOVER et le suivi manuel de l'expédition à TRACKING.

| Dimension | V1 |
|---|---|
| Produits | Vanilla + Cloves + Cocoa |
| Acteurs principaux | International Buyer + Malagasy Exporter |
| Administration | MadaSource Admin |
| Parcours | Marketplace → RFQ → Matching → Quotation → Negotiation → Trade → Documents → Payment Record → Shipment → Delivery → Completion |
| Livrable de ce dépôt | Backend uniquement : API REST `/api/v1` et OpenAPI. Le frontend (site public, portails, responsive, interface multilingue) est développé après validation de l'API. |

Le CdC précise que le document ne doit pas être lu comme une demande de construire immédiatement tous les modules futurs. L'objectif est une fondation solide et évolutive (CdC, « Final requirement » ; Planning §12).

## 2. Catégories de périmètre

Le CdC §77 demande de séparer explicitement quatre catégories :

| Code | Catégorie |
|---|---|
| **A** | Inclus dans le développement initial (V1 active) |
| **B** | Préparé dans l'architecture mais non activé (feature flag désactivé ou extension prévue, sans fonctionnement simulé) |
| **C** | Intégration tierce requise plus tard |
| **D** | Fonctionnalité nécessitant un développement supplémentaire. Ici : décrit dans le CdC mais absent du planning et de la roadmap backend. Le classement commercial définitif revient au client. |

Les éléments dont le classement est incertain sont marqués `À VALIDER`, avec la question correspondante.

## 3. Matrice de périmètre

| Fonctionnalité | Source | Catégorie | Jour backend | Remarque |
|---|---|---|---|---|
| Authentification, sessions, mots de passe | CdC §60, RJ 10 | A | 8, 10 | |
| Vérification d'email | RJ 11 | A | 11 | Envoi réel conditionné à un fournisseur (Q-52) |
| Organisations, adhésions, RBAC (Buyer, Exporter, Admin) | CdC §53-54 | A | 9 | |
| Rôles futurs (Operations, Compliance, Finance, Logistics, Super Admin, Partner) | CdC §53 | B | 9 | Préparés, non activés |
| Rôles internes multiples par organisation | CdC §54 | A ou B, À VALIDER | 9 | Q-10 |
| Audit log | CdC §52 | A | 12 | |
| Profil et statuts Buyer | CdC §10 | A | 13 | |
| Onboarding et profil Exporter (public / privé) | CdC §7, §11 | A | 14 | |
| Vérification Exporter (niveaux 1 à 4) | CdC §8 | A | 15 | Critères : Q-15 |
| Catégories et catalogue produits, attributs par catégorie | CdC §5-6 | A | 16-17 | |
| Marketplace public et recherche filtrée | CdC §5, §50 | A | 18 | |
| Digital Exporter Passport (URL publique + QR code) | CdC §9 | A | 18 | |
| RFQ structurée | CdC §12 | A | 19-20 | |
| RFQ en langage naturel | CdC §13 | B, À VALIDER | — | Dépend d'un analyseur ou d'une IA, absent du planning (Q-29) |
| Inbox RFQ Exporter | CdC §15 | A | 21 | |
| Matching déterministe | CdC §14 | A | 22-23 | |
| Matching assisté par IA, matching avancé | CdC §47, Planning §10 | B | — | Phase 4 |
| Quotation, moteur de prix, modèles A et B | CdC §16-17, §2 | A | 24 | Modèle actif : Q-01 |
| Validité et comparaison des quotations | CdC §18-19 | A | 25 | |
| Négociation et historique | CdC §20-21 | A | 26 | Traduction des prix en Modèle A : Q-05 |
| Trade ID et création du Trade | CdC §22-23 | A | 27 | |
| Machine d'état et timeline du Trade | CdC §24-25 | A | 28 | |
| Tableau de bord du Trade (données agrégées) | Planning étape 6 | A | 28 et suivants | Agrégation par Trade ID |
| Coffre documentaire | CdC §26 | A | 29 | |
| Messagerie interne (REST) | CdC §28 | A | 30 | Temps réel : B |
| Notifications in-app | CdC §29 | A | 31 | |
| Notifications email et push | CdC §29 | B puis C | 31 | Architecture prête ; fournisseur à choisir (Q-52) |
| Demandes d'échantillons | CdC §27 | A, À VALIDER | 32 | Planning : V1 ; CdC §69 : Phase 2 ; RJ 32 : conditionnel (Q-53) |
| Payment Records (enregistrement, justificatif, confirmation admin) | CdC §30 | A | 33 | Aucun flux financier |
| Passerelles de paiement, banques, lettres de crédit, escrow, financement | CdC §30, §57 | C | — | Planning §10 |
| Expéditions manuelles | CdC §31 | A | 34 | |
| API transporteurs, suivi automatique | CdC §31, §57 | C | — | Planning §10 |
| Inspection (étape du Trade Journey) | CdC §25, §57 | C | — | Événement de timeline en V1 ? (Q-46) |
| Clôture du Trade (Completed) | CdC §24, §67 | A | 34 | Conditions : Q-42 |
| Avis et indicateurs de performance | CdC §42-44 | A | 35 | |
| Exceptions et litiges | CdC §40-41 | A | 35 | |
| API d'administration | CdC §34-39 | A | 35 | |
| Analytique et rapports admin | CdC §63, Planning §4 (« rapports ») | A ou D, À VALIDER | — | Aucun jour backend dédié (Q-62) |
| Gestion des partenaires (module admin Partners) | CdC §34, §57 | B | — | Planning §10 : partenaires externes plus tard (Q-64) |
| Favoris acheteur | CdC §51 | D, À VALIDER | — | Non planifié (Q-63) |
| Recherche globale selon permissions | CdC §50 | D, À VALIDER | — | Non planifié (Q-63) |
| Endpoints des tableaux de bord Buyer et Exporter | CdC §48-49 | A partiel, À VALIDER | 13-35 | Chaque module fournit ses listes ; agrégations non planifiées (Q-63) |
| Formulaires publics « Contact » et « Request a Quote » | CdC §4 | À VALIDER | — | Compte requis pour une RFQ ? (Q-28) |
| Moteur de réapprovisionnement (reorder) | CdC §65 | B | — | Données conservées dès la V1 |
| Intelligence commerciale, demande, prix, prédictif | CdC §64, §69, Planning §10 | B | — | Phase 4 ; données capturées dès la V1 |
| Assistant IA MadaSource | CdC §45-46 | B | — | Phase 4 |
| Internationalisation EN / FR | CdC §58 | A | Non planifié (proposé : Jour 2, SRC-18) | Rôle du backend : Q-66 ; malgache : B |
| Devises USD / EUR | CdC §59 | A | 24-25 (taux de change séparés : non planifié, SRC-18) | MGA, GBP, AED, CNY : B ; fournisseur de taux de change : C |
| Mode DEMO | CdC §68 | A, À VALIDER | Non planifié (proposé : Jours 2-3, SRC-18) | Mécanisme : Q-67 |
| Feature flags | CdC §71 | A | Non planifié (proposé : Jours 2 à 5, SRC-18) | Q-75 |
| Modules producteurs, collecteurs, coopératives | CdC §71, Planning §10 | B | — | Flags désactivés |
| Banque, logistique, inspection, assurance, douane | CdC §57, §71 | C | — | Flags désactivés |
| Certification externe, intégrations douanières, assurance | Planning §10 | C | — | |
| Responsive, accessibilité, interface multilingue | CdC §62, Planning étape 10 | Hors dépôt | — | Frontend |

## 4. Feature flags

### 4.1 Flags définis par le CdC §71

| Flag | État V1 | Effet attendu |
|---|---|---|
| `VANILLA_ENABLED` | activé | Catégorie disponible dans le catalogue, le marketplace et les RFQ |
| `CLOVES_ENABLED` | activé | Idem |
| `COCOA_ENABLED` | activé | Idem |
| `PRODUCER_MODULE_ENABLED` | désactivé | Module futur, non développé |
| `COLLECTOR_MODULE_ENABLED` | désactivé | Module futur, non développé |
| `COOPERATIVE_MODULE_ENABLED` | désactivé | Module futur, non développé |
| `BANKING_MODULE_ENABLED` | désactivé | Intégration future (C) |
| `LOGISTICS_MODULE_ENABLED` | désactivé | Intégration future (C) |
| `INSPECTION_MODULE_ENABLED` | désactivé | Intégration future (C) |
| `INSURANCE_MODULE_ENABLED` | désactivé | Intégration future (C) |
| `CUSTOMS_MODULE_ENABLED` | désactivé | Intégration future (C) |

Règle : un module futur reste désactivé tant que MadaSource ne décide pas de l'activer (CdC §71). Un flag désactivé ne doit jamais exposer un endpoint qui simule un fonctionnement (RFS J 40, RJ 35).

### 4.2 Flags supplémentaires proposés (À VALIDER)

Ces propositions ne figurent dans aucune source. Elles servent à couvrir les modules dont l'inclusion en V1 est incertaine :

| Flag proposé | Raison |
|---|---|
| `SAMPLES_MODULE_ENABLED` | Inclusion V1 incertaine (Q-53) |
| `DEMO_MODE` | Marquage explicite du mode démonstration (Q-67) |
| `EMAIL_NOTIFICATIONS_ENABLED` | Envoi réel conditionné à un fournisseur configuré (Q-52) |

Le mécanisme exact (variables d'environnement, table de configuration administrable, portée par organisation) reste à définir. Aucun jour de la roadmap backend ne le prévoit explicitement : il est proposé au Jour 2 (SRC-18, Q-75).

## 5. Phases du CdC et périmètre V1

Le CdC §69 propose quatre phases :

| Phase | Contenu (CdC §69) | Traitement V1 |
|---|---|---|
| 1 — Core | Authentification, Buyer, Exporter, Marketplace, Produits, RFQ, Matching, Quotation, Négociation, Trade, Trade ID, Trade Dashboard | Entièrement en V1 |
| 2 — Operations | Documents, Messagerie, Notifications, Échantillons, Vérification, Avis, Gestion des exceptions | En V1 selon le Planning (étapes 3, 7, 8) ; échantillons : Q-53 |
| 3 — Integrations | Paiements, Logistique, Suivi d'expédition, Inspection, Certification, Banque | V1 : **enregistrement** des paiements et **saisie manuelle** des expéditions seulement (CdC « Final requirement », Planning §7-8). Intégrations : C |
| 4 — Intelligence | Assistant IA, matching avancé, analytique, intelligence de la demande et des prix, outils prédictifs | Hors V1 (B) |

Cette lecture concilie le CdC §69 avec le périmètre final du CdC et le Planning. Elle reste à confirmer par le client (contradiction SRC-01).

## 6. Vérification de fin de Jour 1

| Contrôle | Résultat |
|---|---|
| Produits V1 = Vanilla + Cloves + Cocoa | Conforme : aucun autre produit n'est introduit (sections 1 et 4.1) |
| Acteurs V1 = Buyer + Exporter + Admin | Conforme : rôles futurs en B (section 3) |
| Parcours V1 = Marketplace → RFQ → Matching → Quotation → Negotiation → Trade → Documents → Payment Record → Shipment → Delivery → Completion | Conforme : chaque étape correspond à une ligne A de la matrice |
| Aucune intégration externe active | Conforme : paiement, logistique, inspection, change et email réel en C |
| Points dont le périmètre dépend d'une décision client | Q-01, Q-05, Q-10, Q-28, Q-29, Q-32, Q-53, Q-62, Q-63, Q-64, Q-67, Q-75 |

## 7. Livrables demandés par le CdC §77

Le CdC §77 demande 22 éléments au prestataire. Ce dépôt couvre la partie technique backend ; les éléments contractuels et financiers sont hors périmètre technique. Les catégories A à D sont traitées aux sections 2 et 3.

| # | Élément (CdC §77) | Traitement |
|---|---|---|
| 1 | Technical architecture | Jour 2 (`architecture.md`) |
| 2 | Recommended technology stack | `CLAUDE.md` et roadmap backend ; justification au Jour 2 |
| 3 | Frontend architecture | Hors de ce dépôt (backend uniquement) |
| 4 | Backend architecture | Jour 2 |
| 5 | Database architecture | Jour 3 |
| 6 | API architecture | Jour 2 (`api-conventions.md`) |
| 7 | Cloud / hosting architecture | Non planifié dans la roadmap backend (Audit D couvre le déploiement) : À VALIDER |
| 8 | Security architecture | Jour 2 (`security-design.md`), Jour 8, Audit B |
| 9 | File / document storage architecture | Jour 29 |
| 10 | Authentication architecture | Jours 8, 10 et 11 |
| 11 | Role & permission architecture | Jour 9 |
| 12 | Estimated development timeline | `planning.md`, roadmap backend |
| 13 | Development cost | Hors périmètre technique (contractuel) |
| 14 | Maintenance cost | Hors périmètre technique (contractuel) |
| 15 | Source-code ownership | Hors périmètre technique (contractuel) |
| 16 | Deployment process | Audit D |
| 17 | Database ownership | Hors périmètre technique (contractuel) |
| 18 | API documentation | OpenAPI (Jour 5) et skill `api-documentation` |
| 19 | Testing strategy | Jour 2 (`testing-strategy.md`) |
| 20 | Backup and disaster recovery | Audit D (sauvegarde et restauration) ; objectifs chiffrés : Q-72 |
| 21 | Scalability strategy | Non planifié explicitement ; proposé au Jour 2, mesuré à l'Audit C |
| 22 | Future integration strategy | Non planifié explicitement dans la roadmap backend (la roadmap full-stack prévoyait `integration-architecture.md` au Jour 2) ; proposé au Jour 2 |
