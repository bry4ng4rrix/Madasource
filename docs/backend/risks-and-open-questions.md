# Risques, contradictions et questions ouvertes — MadaSource

Jour 1 · 2026-10-12 · Statut : à revoir avec le client · **Mis à jour au Jour 2** : risques R-26 à R-31, contradictions SRC-16 à SRC-19, questions Q-78 à Q-93 (marquées « (J2) »)

Ce document est le point d'entrée des décisions `À VALIDER`. Chaque question indique le jour de la roadmap backend qu'elle bloque ou influence. Une question tranchée est déplacée en section 5 avec la décision et sa date, jamais supprimée.

## 1. Risques

Impact estimé : Élevé, Moyen ou Faible. L'impact est une estimation d'analyse, pas une donnée du client.

| ID | Risque | Type | Impact | Mitigation proposée | Questions |
|---|---|---|---|---|---|
| R-01 | Fuite de la marge MadaSource ou du prix net fournisseur : indication de prix du catalogue, négociation, documents, exports, messages d'erreur. | Sécurité / métier | Élevé | Schémas de réponse séparés par rôle, tests de non-exposition systématiques, audit `security-auditor`. | Q-05, Q-06 |
| R-02 | La négociation en Modèle A n'est pas définie : l'acheteur négocie un prix final, l'exportateur un prix net. Sans règle, le moteur de négociation est inconstructible. | Métier | Élevé | Trancher Q-01 avant le Jour 24 (moteur de prix) et Q-05 avant le Jour 26 (négociation). Proposition : prévoir dès le Jour 3 un modèle capable de stocker chaque proposition dans les deux vues. | Q-01, Q-05 |
| R-03 | Modèle commercial non arrêté (A, B ou les deux). Supporter les deux augmente la complexité du moteur de prix et des schémas. | Métier / planning | Élevé | Abstraction « règle de prix » configurable ; activer un seul modèle en V1 si le client le confirme. | Q-01 à Q-03 |
| R-04 | Cadre réglementaire : encaisser des fonds pour le compte de tiers ou revendre (Modèle A) peut relever d'activités réglementées à Madagascar ou dans les pays de destination. | Juridique | Élevé | V1 = enregistrement seulement (BR-PAY-01, BR-LEG-01) ; validation juridique hors périmètre technique. | Q-54, Q-55 |
| R-05 | Contournement de la plateforme : acheteur et exportateur échangent leurs coordonnées et concluent en direct, ce qui menace surtout le Modèle A. | Métier | Moyen | Politique de visibilité des coordonnées, éventuel filtrage des messages (à décider). | Q-27, Q-51 |
| R-06 | Données exportateurs incomplètes : matching peu pertinent ou injuste. | Métier / données | Moyen | Traitement explicite des données manquantes (BR-MAT-03), affichage des raisons du score. | Q-30, Q-32 |
| R-07 | Coûts externes ou quotations périmés utilisés silencieusement : prix faux. | Métier | Élevé | Validité calculée à la lecture, blocage ou signalement explicite (BR-QUO-03, BR-PRC-08). | Q-04, Q-35 |
| R-08 | Montants en devises différentes (RFQ en EUR, quotation en USD) comparés sans règle de conversion. | Métier / technique | Moyen | Devise explicite partout, aucune conversion implicite, taux séparés (BR-CUR-02). | Q-65 |
| R-09 | Concurrence : double acceptation, double création de Trade, collision de Trade ID. | Technique | Élevé | Transaction unique, contraintes d'unicité, verrouillage, tests de concurrence (RJ 26-27). | — |
| R-10 | Machine d'état du Trade fondée sur le prépaiement : inadaptée aux acomptes, au paiement contre documents ou aux lettres de crédit. | Métier | Moyen | Faire confirmer le schéma de paiement V1 ; machine d'état configurable (CdC §70). | Q-45 |
| R-11 | Périmètre très large (24 modules au CdC) pour 35 jours backend : dépassement probable si les modules conditionnels (échantillons, analytique, favoris, recherche globale) sont ajoutés. | Planning | Élevé | Matrice de périmètre validée (v1-scope.md), modules conditionnels derrière flags, aucun ajout sans validation. | Q-53, Q-62, Q-63 |
| R-12 | Sources contradictoires sur les phases et le périmètre (section 3). | Planning | Moyen | Validation client de v1-scope.md avant le Jour 2. | Q-53, Q-62 |
| R-13 | Documents sensibles : fuite (bancaires, immatriculation), fichiers malveillants (DOCX à macros, PDF piégés). | Sécurité | Élevé | Contrôle d'accès serveur, URL signées courtes, validation du type réel, analyse antivirus (à décider). | Q-48, Q-49 |
| R-14 | Données personnelles : acheteurs européens (RGPD) et loi malgache sur la protection des données personnelles. Le droit à l'effacement entre en tension avec l'audit en ajout seul et l'historique immuable. | Juridique | Élevé | Avis juridique ; minimisation des données personnelles dans l'audit ; politique de conservation. | Q-68, Q-69 |
| R-15 | Mode DEMO mélangé aux données réelles, ou transactions simulées perçues comme réelles. | Métier / sécurité | Élevé | Environnement séparé recommandé ; marquage explicite (BR-DEMO-02). | Q-67 |
| R-16 | Responsabilité liée au badge « vérifié » : un niveau attribué sans vérification documentaire réelle engage la confiance des acheteurs. | Juridique / métier | Moyen | Politique de vérification écrite, traçabilité des décisions (BR-VER-02), expiration. | Q-15 |
| R-17 | Mis à jour au Jour 2. Le cahier des charges a été versionné et poussé sur le dépôt distant le 2026-10-12 (commit c6e27d8) : sa perte n'est plus un risque, sa confidentialité en devient un (R-26). | Projet | Faible | Une seule copie de référence, celle du dépôt. | Q-71 |
| R-18 | Pièges techniques de SQLAlchemy async (lazy loading, sessions) : erreurs à l'exécution et problèmes N+1. | Technique | Moyen | Règles `.claude/rules/backend-python.md`, revue `database-reviewer`, chargement explicite. | — |
| R-19 | Aucun fournisseur d'email : vérification d'email et notifications externes impossibles en conditions réelles. | Technique / planning | Moyen | Adaptateur abstrait et mode local identifié (RJ 11) ; choix du fournisseur avant la mise en production. | Q-52 |
| R-20 | Mis à jour au Jour 2. Dépôt Git initialisé et poussé sur GitHub le 2026-10-12. Le `.gitignore` créé par l'utilisateur exclut `CLAUDE.md` et les roadmaps, mais **pas `.env`** ni les environnements virtuels : un `.env` créé avant le Jour 4 serait versionné et publié. Pas de CI avant le Jour 7. | Sécurité / projet | Moyen | Compléter le `.gitignore` avant tout `.env` (Jour 4, ou plus tôt sur accord). Les hooks refusent déjà l'écriture d'un `.env` par Claude. | — |
| R-21 | Spam et abus sur les endpoints publics (inscription, « Request a Quote », contact). | Sécurité | Moyen | Rate limiting (CdC §60), compte requis pour une RFQ (à décider). | Q-28 |
| R-22 | Attributs produits flexibles (variables par catégorie) : qualité des données et performance des filtres. | Technique | Moyen | Attributs typés et validés par catégorie, index sur les filtres réels (Jour 3). | Q-18 |
| R-23 | Ambiguïté sur les délais en jours (« validité 7 jours ») selon le fuseau (Madagascar UTC+3, acheteurs en Europe). | Métier / technique | Faible | Stockage UTC, instant d'expiration explicite. | Q-70 |
| R-24 | Indicateurs de performance et avis peu nombreux au lancement : matching biaisé contre les nouveaux exportateurs. | Métier | Faible | Mention « NEW ON MADASOURCE », traitement neutre de l'absence d'historique (à décider). | Q-32, Q-59 |
| R-25 | Exigences non fonctionnelles non chiffrées (volumétrie, disponibilité, sauvegarde) : dimensionnement et tests de performance sans cible. | Technique | Moyen | Obtenir des ordres de grandeur avant l'Audit C. | Q-72 |
| R-26 | (J2) Visibilité du dépôt distant (GitHub) non vérifiée. S'il est public, sont lisibles par tous : le cahier des charges, les règles de marge, la conception de sécurité, et l'historique de `CLAUDE.md` et des deux roadmaps. Ces trois fichiers ont été retirés de l'index (commit f598049) mais restent dans l'historique poussé (commit c6e27d8). | Sécurité / juridique | Élevé | Vérifier immédiatement que le dépôt est privé. Retirer le document de l'historique seulement avec un accord explicite : opération destructive, sans effet sur les clones existants. | Q-71 |
| R-27 | (J2) Compte admin compromis ou fraude interne : accès transversal aux marges et aux données bancaires, confirmation de paiements fictifs. | Sécurité | Élevé | Second facteur, ensembles de permissions admin, séparation des tâches, ré-authentification, audit des consultations (S-09, S-12, S-16, S-34, S-35). | Q-80, Q-88, Q-89 |
| R-28 | (J2) Détournement de paiement par modification des coordonnées bancaires (exportateur ou MadaSource). | Sécurité / métier | Élevé | Contrôle renforcé des modifications (S-44). | Q-55, Q-87 |
| R-29 | (J2) Fuite entre exportateurs concurrents destinataires d'une même RFQ : questions, documents, conversations. | Sécurité / métier | Élevé | Rattachement à la paire (RFQ, exportateur), participants explicites (S-31, S-46). | Q-84 |
| R-30 | (J2) Instance DEMO utilisée comme fausse preuve de paiement ou d'expédition. | Métier / sécurité | Moyen | Espace de noms d'identifiants distinct, marqueur dans chaque réponse et document, emails désactivés (S-57). | Q-67 |
| R-31 | (J2) Prix accepté différent du prix affiché, si l'offre ou les règles changent pendant la consultation. | Métier | Moyen | Version de l'offre présentée et acceptée (S-43). | Q-91 |

## 2. Matrice de périmètre (synthèse)

Détail complet : [v1-scope.md §3](v1-scope.md#3-matrice-de-périmètre).

| Catégorie | Contenu |
|---|---|
| **A — V1 active** | Auth, organisations, RBAC de base, audit, profils Buyer et Exporter, vérification, produits, marketplace, Digital Passport, RFQ structurée, inbox exportateur, matching déterministe, quotation et moteur de prix, validité, comparaison, négociation, Trade et Trade ID, machine d'état et timeline, documents, messagerie REST, notifications in-app, Payment Records, expéditions manuelles, clôture, avis et performance, exceptions et litiges, API admin, USD/EUR, codes de langue EN/FR, feature flags |
| **A à confirmer** | Échantillons (Q-53), rôles internes multiples (Q-10), mode DEMO (Q-67), analytique admin (Q-62), formulaires publics (Q-28) |
| **B — préparé, non activé** | Rôles admin spécialisés, Partner, RFQ en langage naturel, IA (assistant, matching), réapprovisionnement, intelligence commerciale, modules Producer, Collector et Cooperative, devises et langues supplémentaires, notifications email et push |
| **C — intégrations futures** | Banque, passerelles de paiement, lettres de crédit, escrow, financement, transporteurs, suivi automatique, inspection, certification externe, douane, assurance, fournisseur de taux de change, fournisseur d'email |
| **D — non planifié, à arbitrer** | Favoris, recherche globale, agrégations des tableaux de bord Buyer et Exporter (Q-63) |

## 3. Contradictions entre sources

| ID | Sources | Contradiction | Traitement provisoire |
|---|---|---|---|
| SRC-01 | CdC §69 vs CdC « Final requirement » et Planning étapes 3, 7, 8, 9 | §69 place Documents, Messagerie, Notifications, Échantillons, Vérification, Avis et Exceptions en Phase 2, Paiements et Logistique en Phase 3. Le périmètre final et le Planning les incluent en V1 (paiement et logistique sous forme d'enregistrement manuel). | Lecture conciliée dans v1-scope.md §5, à confirmer. |
| SRC-02 | CdC §16 (`MSQ-2026-000145`) vs CdC §66 (`MSQ-2026-0044`, `RFQ-2026-0012`) | Nombre de chiffres de la partie séquentielle (6 ou 4) incohérent. | Q-37. |
| SRC-03 | CdC §25 vs §24 | Le Trade Journey contient « Inspection », absente de la machine d'état. | Événement de timeline facultatif proposé (Q-46). |
| SRC-04 | CdC §31 vs §24 | L'expédition a un statut « Arrived » sans équivalent dans le Trade. | Correspondance proposée dans workflows.md §11 (Q-58). |
| SRC-05 | CdC §12 vs §19 | Le flux RFQ linéaire passe par « Negotiating » avant « Accepted », alors que le §19 permet « Accept » directement depuis la comparaison. | Transition directe Quotations Received → Accepted déduite (workflows.md §4). |
| SRC-06 | CdC §14 vs RJ 22 | Le CdC inclut prix, délai, performance historique et taux de réponse dans le matching ; RJ 22 ne les cite pas et ajoute le MOQ. | Le CdC prime sur RJ 22 pour les critères de compatibilité (produit, quantité, capacité, qualité, grade, certification, destination, Incoterm, vérification, prix, délai), selon les données disponibles. Performance historique et taux de réponse : contradiction interne au CdC, voir SRC-16. |
| SRC-07 | CdC §67 (paiement, étape 13, avant documents, étape 14) vs CdC §74 et Planning §2 (Documents → Payment Record) | Ordre des étapes. | Pas de contrainte d'ordre : les documents sont déposables tout au long du Trade. |
| SRC-08 | Planning étape 7 vs RJ 32 vs CdC §69 | Échantillons : V1 (Planning), conditionnel (RJ 32), Phase 2 (CdC). | Q-53, flag proposé `SAMPLES_MODULE_ENABLED`. |
| SRC-09 | CdC §34 (module admin « Partners ») vs Planning §10 (partenaires externes plus tard) | Module admin d'un domaine hors V1. | Classé B (Q-64). |
| SRC-10 | CdC §63 et Planning §4 (« rapports ») vs roadmap backend | Analytique et rapports admin attendus, sans jour backend dédié. | Q-62. |
| SRC-11 | CdC §50-51, §48-49 vs roadmap backend | Recherche globale, favoris et tableaux de bord décrits, non planifiés. | Classés D (Q-63). |
| SRC-12 | `roadmap.md` (50 j, Jour 1 → `docs/*.md`) vs `roadmap_backend_fastapi.md` (35 j, Jour 1 → `docs/backend/*.md`) | Deux plannings et deux jeux de livrables. | La roadmap backend est la référence (CLAUDE.md). Les livrables du Jour 1 full-stack sont couverts : roles-permissions → actors-and-permissions, domain-map → requirements §6, future-scope → v1-scope. |
| SRC-13 | RJ, prompt quotidien (`docs/backend/roadmap-backend-fastapi.md`) vs fichier réel (`roadmap_backend_fastapi.md`, racine) | Chemin de la roadmap. | Fichier non déplacé ; déplacement à décider au Jour 4. |
| SRC-14 | CdC §20 (seule la contre-offre de l'acheteur est notifiée, §29) vs alternance des contre-offres | Le CdC ne liste pas la notification d'une contre-offre de l'exportateur. | Notification proposée (workflows.md §16, Q-52). |
| SRC-15 | CdC §2 (USD 40 → USD 43) vs CdC §17 (USD 40 → USD 45 avec coûts) | Deux exemples chiffrés différents. | Pas une contradiction : exemples illustratifs, aucune valeur codée. |
| SRC-16 | CdC §14 vs CdC §43 et §69 (et Planning §10) | Le §14 cite la performance historique et le taux de réponse parmi les critères de matching. Le §43 dit que les indicateurs de performance « should contribute to future matching », et le §69 place « Advanced Matching » en Phase 4 (Planning §10 : « matching avancé » plus tard). | Non tranché : Q-32. |
| SRC-17 | CdC §70 vs RJ section 1 | Le §70 dit « Do not build a monolithic system where every future feature is hard-coded into the first version » ; la roadmap impose un « monolithe modulaire ». | Compatibles : le §70 rejette le codage en dur des fonctionnalités futures, pas une application unique découpée en modules. À expliquer au client pour éviter un malentendu. |
| SRC-18 | CdC §58, §59, §68, §71 (classés A) vs roadmap backend | Feature flags, mode DEMO, i18n et séparation des taux de change ne sont traités par aucun jour de la roadmap backend (seule mention : DEMO dans le prompt permanent). La roadmap full-stack plaçait i18n et devises aux Jours 44-45, et la vérification du mode DEMO au Jour 50. | Jours proposés dans v1-scope.md, à valider (Q-75). |
| SRC-19 | CdC §40 vs RJ 35 | Le CdC cite des exceptions antérieures au Trade (« Quotation expired », « Exporter not responding ») ; RJ 35 parle d'« exceptions/disputes liées à Trade ». | Rattachement facultatif au Trade proposé (requirements.md §6), à confirmer au Jour 3 (Q-60). |

## 4. Questions ouvertes

Format : question — contexte — jour bloqué ou influencé.

### 4.1 Modèle commercial et prix

- **Q-01** — Modèle commercial V1 : A (revendeur), B (intermédiaire) ou les deux ? Choix global, par exportateur ou par transaction ? — CdC §2, §75 — **bloque J24**.
- **Q-02** — Formule de marge en Modèle A : montant par unité, pourcentage, par catégorie, produit ou acheteur ? Qui la configure et avec quelle traçabilité ? Attention : une marge en pourcentage, combinée au détail des coûts visible de l'acheteur (Q-04), rend le taux de marge calculable (S-19). — CdC §17 — J24.
- **Q-03** — Commission en Modèle B : base de calcul, payeur (acheteur ou exportateur), visibilité pour chaque partie. — CdC §2 — J24.
- **Q-04** — Coûts externes en V1 : qui les saisit (admin, exportateur) ? Le détail est-il visible par l'acheteur, par l'exportateur ? Comportement si un coût est expiré (blocage ou avertissement) ? Voir Q-02 pour le risque de déduction du taux de marge. — CdC §17, §33 — J24.
- **Q-05** — Négociation en Modèle A : comment une contre-offre de l'acheteur (prix final) se traduit-elle pour l'exportateur (prix net) ? Marge constante, renégociée, validation admin ? L'exportateur voit-il le prix final acheteur ? S'il le voit, il calcule la marge (S-19). Un rejet automatique sous un prix plancher permettrait de découvrir ce plancher (S-42). — CdC §20, §61 — **bloque J26**.
- **Q-06** — Indication de prix du catalogue : prix net exportateur ou prix commercial MadaSource ? Visible publiquement ou seulement par les acheteurs connectés ? Une indication publique est vue par tous les exportateurs : nette, elle révèle le prix net à l'acheteur ; commerciale, elle révèle la marge à l'exportateur. Options : fourchette, ou aucun prix public. — CdC §5-6, §61 — J16, J18.
- **Q-07** — Validation admin d'une quotation avant présentation à l'acheteur : systématique, au-delà d'un seuil (« high-value »), ou jamais ? — CdC §38 — J24, J25.
- **Q-08** — Précision et arrondis des montants (décimales par devise, prix unitaire et total, mode d'arrondi). — RJ section 1 — J3, J24.
- **Q-91** — (J2) Une modification des règles de prix (marge, commission) s'applique-t-elle aux quotations déjà présentées à l'acheteur, ou seulement aux nouvelles ? — S-43 — J24, J25.

### 4.2 Comptes et organisations

- **Q-09** — Une organisation peut-elle être à la fois acheteuse et exportatrice ? — CdC §54 — J9. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-10** — Rôles internes à une organisation (directeur, commercial, opérations) : activés en V1 ou un seul rôle par organisation ? Qui invite les membres ? — CdC §54 — J9. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-11** — Compte acheteur : droits en Pending, validation admin obligatoire, différence entre Suspended et Blocked, réversibilité de Blocked. — CdC §10, §35 — J13.
- **Q-12** — Statuts du compte exportateur (distincts de la vérification). Un exportateur non vérifié peut-il publier, recevoir des RFQ, envoyer des quotations ? — CdC §11, §36 — J14, J15. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-13** — Lien entre la vérification d'email et le statut du compte. — RJ 11 — J11.
- **Q-14** — Procédure de création du premier administrateur et des comptes admin suivants. — RJ 10 — J10.
- **Q-74** — Un utilisateur peut-il appartenir à plusieurs organisations ? Les administrateurs appartiennent-ils à une organisation interne « MadaSource » ? Proposition : un admin n'est jamais membre d'une organisation cliente (S-33). — CdC §54 — J3, J9. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-76** — Durée de vie des tokens d'accès et de rafraîchissement, rotation, politique de mot de passe (longueur, complexité), verrouillage après échecs de connexion. — RJ 10 (« selon les règles validées ») — J8, J10.
- **Q-80** — (J2) Second facteur d'authentification obligatoire pour les administrateurs ? Proposé, ou obligatoire, pour les utilisateurs des organisations clientes ? — CdC §60 ; S-09 — J10.
- **Q-97** — (J3) Le motif d'un changement de statut de compte (suspension, blocage, clôture) est-il communiqué à l'organisation concernée ? Proposition : un motif communiqué distinct de la note interne, comme pour la vérification (S-47). — CdC §10, §35-36 ; data-classification.md — J11, J13.

### 4.3 Vérification

- **Q-15** — Critères et documents requis par niveau ; durée de validité ; passage automatique en Expired à la date d'expiration ; renouvellement ; communication du motif de rejet à l'exportateur ; nouvelle demande après rejet ou expiration. — CdC §8, Planning §13 — J15.
- **Q-16** — Niveau minimal pour le Digital Passport, l'apparition au marketplace et la réception de RFQ. Statuts de vérification affichés publiquement : seulement le niveau obtenu, ou aussi Pending, Rejected, Expired, Suspended ? — CdC §9, §14, §61 — J15, J18, J22.
- **Q-17** — Format de l'URL publique (slug, unicité, changement de nom), domaine définitif, contenu du QR code. Proposition : un slug n'est jamais réattribué (S-54). — CdC §9 — J18.
- **Q-90** — (J2) Les champs couverts par une vérification (raison sociale, immatriculation…) sont-ils gelés, ou leur modification renvoie-t-elle la vérification en revue avec badge suspendu ? — CdC §8-9 ; S-53 — J14, J15.

### 4.4 Produits et marketplace

- **Q-18** — Attributs spécifiques par catégorie (vanille, girofle, cacao) : liste, obligatoires ou facultatifs, unités, valeurs de grade admises. — CdC §6 — **bloque J16**.
- **Q-19** — Statuts d'un produit et modération admin avant publication. — RJ 17 — J17.
- **Q-20** — Liste des certifications reconnues et preuve exigée. — CdC §6 — J16.
- **Q-21** — Unités admises (kg, tonne) et normalisation ; « T » = tonne métrique ? — CdC §13, §19 — J16, J19.
- **Q-77** — Règle de priorisation et de tri des résultats de recherche acheteur (le CdC dit « should prioritize » : produit, exportateur, qualité, certification, disponibilité, prix, vérification). — CdC §50 — J18.
- **Q-78** — (J2) Effet de la désactivation d'une catégorie (feature flag) sur les produits, RFQ, quotations et Trades existants : seules les créations sont bloquées, ou autre traitement ? — CdC §71 ; D-17 — J16.
- **Q-86** — (J2) Liste blanche du profil public exportateur. Le CdC §61 ne rend publics que le nom, les produits, la vérification, la localisation générale et les certifications. Faut-il y ajouter logo, description, années d'activité, marchés d'export, capacité, avis, indicateurs ? Seuil d'activité minimal avant d'afficher un indicateur ? — CdC §7, §43, §61 ; S-51 — J18, J35.

### 4.5 RFQ

- **Q-22** — Champs obligatoires d'une RFQ (et du profil acheteur). — CdC §10, §12 — J13, J19.
- **Q-23** — Modification, annulation et expiration d'une RFQ après soumission. — RJ 20 — J20.
- **Q-24** — États manquants (annulée, aucun exportateur compatible, aucune quotation) ; déclencheur de « Quotations Received » (première ou toutes) et de « Closed » ; statuts côté destinataire (Sent, Responded, Declined). — CdC §12, §15 — J19, J21.
- **Q-25** — Une RFQ porte-t-elle sur une catégorie (« Vanilla ») ou sur un produit précis d'un exportateur ? Plusieurs produits par RFQ (RFQItems) ? RFQ adressée directement à un exportateur choisi ? — CdC §12, §55 — J19. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-26** — Plusieurs quotations acceptées pour une même RFQ (achat réparti entre exportateurs) ? — CdC §22 — J27.
- **Q-27** — Identité de l'acheteur visible par l'exportateur dans l'inbox (l'exemple du §15 ne montre que le pays) ; moment où elle est révélée. La règle vaut aussi pour les champs « auteur » des historiques et des documents (S-48). — CdC §15 — J21.
- **Q-28** — « Request a Quote » du site public : compte acheteur obligatoire ? Formulaire « Contact » géré par le backend ? — CdC §4 — J18, J20.
- **Q-29** — RFQ en langage naturel : confirmée hors V1 ? — CdC §13 — J19.
- **Q-95** — (J3) Avec des RFQ à plusieurs lignes et plusieurs Trades possibles (Q-25, PROPOSED), que signifient les statuts Accepted et Closed de la RFQ ? Proposition : Accepted dès la première acceptation ; Closed quand toutes les lignes sont attribuées, déclinées ou expirées. — CdC §12 ; data-model.md §7 — J19, J27.
- **Q-84** — (J2) Une question d'exportateur sur une RFQ reste-t-elle privée entre lui et l'acheteur, ou la réponse est-elle diffusée, anonymisée, à tous les destinataires ? — CdC §15, §28 ; S-31 — J21, J30.
- **Q-85** — (J2) Champs de la RFQ visibles par l'exportateur destinataire : prix cible (en Modèle A, c'est un prix final, qui renseigne sur la marge), préférence de paiement, port, exigences supplémentaires ? — CdC §12, §15 ; S-50 — J21.

### 4.6 Matching

- **Q-30** — Pondérations initiales, seuil minimal de score, nombre maximal d'exportateurs destinataires. — CdC §14 — J22.
- **Q-31** — Envoi aux exportateurs automatique ou après validation admin ? Scores et raisons visibles par l'acheteur ? Par l'exportateur ? Contenu des raisons : jamais de valeur privée d'un tiers (S-49). — CdC §14, RFS J 23 — J23.
- **Q-32** — La performance historique et le taux de réponse entrent-ils dans le score dès la V1 (CdC §14), ou seulement dans le matching futur (CdC §43, §69 ; SRC-16) ? Si c'est dès la V1 : traitement des exportateurs sans historique. — CdC §14, §43, §69 — J22.
- **Q-33** — Vérification : critère éliminatoire ou pondéré ? — CdC §14 — J22.

### 4.7 Quotations

- **Q-34** — Cycle de vie d'une quotation (brouillon, soumise, retirée, refusée…) ; modification ou retrait par l'exportateur. — CdC §18 — J24, J25.
- **Q-35** — Seuil de « Expiring » ; durée de validité par défaut éventuelle ; heure exacte d'expiration. — CdC §18 — J25.
- **Q-36** — Prolongation ou réactivation d'une quotation expirée : autorisée ? Par qui ? — RJ 25 — J25.
- **Q-37** — Format exact des identifiants (`RFQ-AAAA-NNNN` ou 6 chiffres ; `MSQ` sur 4 ou 6 chiffres) ; remise à zéro annuelle. Des références séquentielles révèlent le volume d'activité de la plateforme : est-ce acceptable (S-54) ? — CdC §16, §66 — J19, J24, J27. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-94** — (J3) Un exportateur peut-il soumettre plusieurs quotations distinctes (variantes) pour une même RFQ ? Proposition : non, une quotation par exportateur et par RFQ, modifiée par versions (S-43). — CdC §16-18 ; data-model.md §5.14 — J24.

### 4.8 Négociation

- **Q-38** — Champs négociables (prix, quantité, Incoterm, délai, conditions de paiement) ; nombre de tours ; durée de validité d'une contre-offre. — CdC §20-21 — J26.
- **Q-39** — Un refus clôt-il la négociation ou permet-il une nouvelle contre-offre ? — RJ 26 — J26.
- **Q-40** — Rôle et limites de l'intervention admin (créer, modifier ou accepter pour le compte d'une partie ?) sur RFQ, quotations et négociations. — CdC §37-38 — J20, J26, J35.

### 4.9 Trade

- **Q-41** — Acteur et conditions de chaque transition du Trade (Payment Pending, Ready for Shipment, Delivered…). — CdC §24, §67 — **bloque J28**.
- **Q-42** — Conditions de Completed : livraison confirmée par l'acheteur, paiement total confirmé, documents obligatoires, délai de contestation ? — CdC §24, Planning §13 — **bloque J34**.
- **Q-43** — Annulation : qui, depuis quels états, conséquences. — CdC §24, Planning §13 — J28.
- **Q-44** — On Hold et Disputed : depuis quels états, retour à l'état précédent ? — CdC §24 — J28.
- **Q-45** — Conditions de paiement autres que le prépaiement en V1 ? — CdC §16, §24 — J28, J33.
- **Q-46** — Inspection : simple événement de timeline en V1 ? — CdC §25 — J28.
- **Q-82** — (J2) En Modèle A, quels objets d'un Trade sont partagés entre acheteur et exportateur, et lesquels restent bilatéraux avec MadaSource : termes, documents commerciaux et de paiement, Payment Records, commentaires de timeline, litiges ? Quelle contrepartie est affichée à chacun (MadaSource ou l'autre partie) ? — CdC §2, §23, §30, §61 ; S-39, S-40 — J3, J24 à J33, **bloque J27**. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).

### 4.10 Documents

- **Q-47** — Documents obligatoires par étape (facture, certificat d'origine, phytosanitaire, connaissement…) et leur validation par l'admin. — CdC §26, Planning §13 — J29, J34.
- **Q-48** — Statuts de document, taille maximale, analyse antivirus, durée de conservation. — CdC §26 — J29.
- **Q-49** — Stockage : fournisseur S3-compatible, localisation géographique des données. — RJ 29 — J29.
- **Q-83** — (J2) Gouvernance de la visibilité des documents : qui fixe l'audience (déposant, admin) ? Valeur par défaut par catégorie ? Validation admin avant partage ? Retrait d'un partage ? Traitement des métadonnées embarquées des documents bureautiques (auteur, suivi des modifications) ? — CdC §26, §61 ; S-24, S-27 — J29.
- **Q-96** — (J3) Valeurs de visibilité à ajouter aux quatre valeurs de Q-82 : `OWNER_ONLY` (objets d'une seule organisation : société, vérification, catalogue) et `PUBLIC` (médias du marketplace : logo, photos de produits publiés) ? — Q-82 ; data-classification.md §2 — J14, J29.

### 4.11 Messagerie et notifications

- **Q-50** — L'admin peut-il lire les conversations ? Si oui, avec motif, audit et information des participants (S-46) ? Un auteur peut-il modifier ou supprimer son message ? — CdC §28, §34 — J30.
- **Q-51** — Échange de coordonnées directes : autorisé, masqué ou signalé ? Un prix écrit dans un message échappe à toute projection (R-05). — CdC §61 — J30.
- **Q-52** — Fournisseur d'email (V1 ou plus tard) ; destinataires de chaque notification ; notifications supplémentaires (contre-offre exportateur, vérification, expiration proche, litige). — CdC §29 — J11, J31.

### 4.12 Échantillons

- **Q-53** — Module inclus en V1 ? Paiement d'échantillon par le même mécanisme que les Payment Records ? Refus et annulation, échantillon gratuit ? — CdC §27, §69, Planning étape 7, RJ 32 — J32.

### 4.13 Paiements

- **Q-54** — Qui reçoit le paiement (MadaSource en Modèle A, l'exportateur en Modèle B ?) ; qui l'enregistre (acheteur, admin) ; paiements partiels ou multiples par Trade ; sens de chaque paiement et audience de chaque justificatif (S-40, Q-82). — CdC §30, Planning §13 — **bloque J33**.
- **Q-55** — Coordonnées bancaires présentées à l'acheteur pour le virement : celles de MadaSource ou de l'exportateur ? — CdC §11, §30 — J33.
- **Q-56** — Remboursement : enregistrement seul ? Qui l'autorise ? Séparation des tâches proposée : jamais l'auteur de la saisie (S-34). — CdC §30 — J33.
- **Q-81** — (J2) Chiffrement applicatif des coordonnées bancaires : gestion de la clé (variable d'environnement ou gestionnaire de secrets), rotation, rechiffrement ? — CdC §11, §60 ; S-22 — J14.
- **Q-87** — (J2) Modification des coordonnées bancaires, de l'exportateur comme de MadaSource : qui peut les modifier, quelle validation (re-vérification par MadaSource ?), quelles notifications, quel délai avant prise d'effet ? — CdC §11, §30 ; S-44 — J14, J33.
- **Q-88** — (J2) Confirmation et remboursement d'un paiement : double validation par deux admins, toujours ou au-delà d'un seuil ? — CdC §30 ; S-34 — J33.

### 4.14 Expéditions

- **Q-57** — Plusieurs expéditions par Trade (livraisons partielles) ? — CdC §31 — J34.
- **Q-58** — Qui saisit et met à jour l'expédition (exportateur, admin) ? Correspondance des statuts Shipment ↔ Trade, notamment « Arrived ». — CdC §31, §67 — J34.

### 4.15 Avis, exceptions, litiges

- **Q-59** — Échelle de notation ; seuil de « NEW ON MADASOURCE » ; une évaluation par sens ; modération ; délai pour évaluer ; visibilité des avis sur les acheteurs. — CdC §42, §44 — J35.
- **Q-60** — Statuts des exceptions ; exceptions détectées automatiquement et leurs seuils. — CdC §40 — J35.
- **Q-61** — Effet d'un litige sur le Trade et les paiements ; qui propose et accepte la résolution ; refus d'une résolution. — CdC §41, Planning §13 — J35.
- **Q-92** — (J2) Un litige (motif, preuves, montant de la résolution proposée) est-il visible de l'autre partie ? — CdC §41 — J35.

### 4.16 Administration et périmètre

- **Q-62** — Analytique et rapports admin (CdC §63) en V1 backend ? Quels indicateurs ? — CdC §63, Planning §4 — J35.
- **Q-63** — Favoris, recherche globale et agrégations des tableaux de bord Buyer et Exporter : V1 ou plus tard ? — CdC §48-51 — J13 à J35.
- **Q-64** — Module admin « Partners » : désactivé en V1 ? — CdC §34 — J35.
- **Q-89** — (J2) En V1, tous les admins voient-ils marges, données bancaires, documents privés et conversations, ou faut-il répartir les ensembles de permissions admin entre plusieurs personnes ? — CdC §53 ; S-12 — J9.

### 4.17 Transverse

- **Q-65** — Conversion de devises en V1 ? Source des taux (saisie manuelle par l'admin ?) ? Comparaison de quotations en devises différentes ? — CdC §59 — J24, J25.
- **Q-66** — i18n : libellés traduits (catégories, attributs, statuts, erreurs) servis par l'API ou gérés par le frontend ? — CdC §58 — J2, J16. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-67** — Mode DEMO : environnement séparé (recommandé) ou enregistrements marqués dans la même base ? Qui l'active ? Accès à l'instance (sur invitation ?), préfixe distinct des identifiants, emails désactivés (S-57) ? — CdC §68 — J2, J3. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-68** — Conformité des données personnelles (RGPD pour les acheteurs européens, loi malgache) : base légale, conservation, droit à l'effacement face à l'audit immuable. — CdC §60-61 — J3, J12. **Réponse reçue le 2026-10-13 : PROPOSED, non approuvée** ([registre des décisions](../decisions/architecture-decisions.md)).
- **Q-69** — Durée de conservation des journaux d'audit, documents, messages. — CdC §52 — J12, J29.
- **Q-70** — Fuseau de référence pour les échéances exprimées en jours (UTC, Madagascar, fuseau de l'acheteur). — CdC §18 — J25.
- **Q-71** — Mise à jour au Jour 2 : le cahier des charges a été versionné et poussé sur le dépôt distant le 2026-10-12 (commit c6e27d8). À confirmer **en urgence** : le dépôt est-il privé, et ce document client peut-il y rester ? Même question pour `CLAUDE.md` et les deux roadmaps, retirés de l'index mais présents dans l'historique poussé. — R-26 — immédiat.
- **Q-72** — Exigences non fonctionnelles chiffrées : nombre d'utilisateurs et de transactions, temps de réponse, disponibilité, RPO/RTO des sauvegardes. — CdC §60 — J2, Audit C.
- **Q-73** — Version de référence des Incoterms (Incoterms® 2020 ?). — CdC §32 — J24.
- **Q-75** — Feature flags, mode DEMO, i18n et séparation des taux de change ne sont prévus par aucun jour de la roadmap backend (SRC-18). Retenir les jours proposés dans v1-scope.md (Jours 2 à 5), ou ajouter des jours au planning ? — CdC §58-59, §68, §71 — J2.
- **Q-79** — (J2) Hébergement de production : fournisseur, pays et localisation des données, gestionnaire de secrets, existence d'un environnement de staging. — CdC §77 (point 7) ; D-11, architecture.md §11 — J4, Audit D.
- **Q-93** — (J2) Ordre de construction. Des modules de bas niveau sont construits **après** des modules qui les utilisent :
  - `audit` au Jour 12, utilisé dès le Jour 9 ;
  - `documents` au Jour 29, dès le Jour 14 ;
  - `messages` au Jour 30, dès le Jour 21 ;
  - `notifications` au Jour 31, dès le Jour 13.

  Accepter le rétro-branchement à leur jour (ajout des appels et des tests dans les modules antérieurs), ou anticiper un noyau minimal ? Recommandation : rétro-branchement pour `audit` et `notifications`, conforme à RJ 12 et RJ 31 ; noyau minimal du coffre documentaire au Jour 14. Cela alourdit le Jour 14 et allège le Jour 29. — module-boundaries.md §11 — **avant J9**. **Réponse reçue le 2026-10-13 : PROPOSED, avec un point non résolu (CF-08)** ([registre des décisions](../decisions/architecture-decisions.md) ; [dependency-graph.md](dependency-graph.md)).

### 4.18 Questions bloquantes par jour (synthèse)

| Jour | Questions à trancher avant le jour |
|---|---|
| Immédiat | **Q-71** (confidentialité du dépôt distant) |
| J2-J3 (architecture, données) | Q-09, Q-10, Q-12, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74, Q-82 : **réponses reçues le 2026-10-13, PROPOSED**, à approuver ([registre des décisions](../decisions/architecture-decisions.md)). Reste ouverte : Q-75. |
| Avant J9 (planification) | Q-93 : réponse PROPOSED reçue ; point non résolu CF-08 / SQ-02, à trancher **avant J14** ([dependency-graph.md](dependency-graph.md)) |
| J4 (initialisation du dépôt) | Q-79 |
| J8-J15 (sécurité, accès, comptes, vérification) | Q-11, Q-13, Q-14, Q-15, Q-16, Q-76, Q-80, Q-81, Q-87, Q-89, Q-90, Q-96, Q-97 ; approbation de Q-09, Q-10, Q-12, Q-74 ; SQ-01, **SQ-02** |
| J16-J18 (produits, marketplace) | Q-06, Q-17, Q-18, Q-19, Q-20, Q-21, Q-77, Q-78, Q-86 |
| J19-J23 (RFQ, matching) | Q-22, Q-23, Q-24, Q-27, Q-30, Q-31, Q-32, Q-84, Q-85, Q-95 ; approbation de Q-25, Q-37 ; **SQ-03** (avant J21), SQ-04 |
| J24-J27 (quotations, négociation, Trade) | **Q-01**, Q-02, Q-03, Q-04, **Q-05**, Q-26, Q-34, Q-35, Q-38, **Q-82** (approbation), Q-91, Q-94 ; **SQ-05** (avant J24) |
| J28-J35 (opérations) | **Q-41**, **Q-42**, Q-43, Q-47, Q-53, **Q-54**, Q-58, Q-59, Q-61, Q-62, Q-83, Q-88, Q-92, Q-96 |

## 5. Décisions prises

Aucune décision **approuvée** à ce jour.

Le 2026-10-13, le responsable produit a transmis des réponses à 11 questions (Q-09, Q-10, Q-12, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74, Q-82, Q-93). À sa demande, elles sont enregistrées comme **propositions (PROPOSED)**, non comme décisions, dans le [registre des décisions](../decisions/architecture-decisions.md), avec les conflits relevés face au CdC (CF-01 à CF-09). Ce tableau ne sera rempli qu'à l'approbation explicite de chacune.

Fait constaté le 2026-10-12 : l'utilisateur a versionné le cahier des charges dans le dépôt (commit c6e27d8). La question de confidentialité (Q-71) reste ouverte.

Format attendu :

| Date | Question | Décision | Décideur | Impact sur les documents |
|---|---|---|---|---|
