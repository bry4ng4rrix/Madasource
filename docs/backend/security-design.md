# Conception de la sécurité — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider. Document vivant :
- primitives au Jour 8 ;
- organisations et RBAC au Jour 9 ;
- authentification au Jour 10 ;
- statuts de compte au Jour 11 ;
- audit au Jour 12 ;
- documents au Jour 29 ;
- vérification complète à l'Audit B.

Sources : CdC §2, §11, §17, §26, §30, §52-54, §60-61, §68 ; RJ section 1 ; OWASP API Security Top 10 (édition 2023) ; matrices de [actors-and-permissions.md](actors-and-permissions.md).
Ce document intègre la relecture de l'agent `security-auditor` du Jour 2 (section 22).
Décisions de sécurité : identifiants **S-NN** ; statuts Retenu / Proposé / À VALIDER, comme dans [architecture.md](architecture.md).

## 1. Actifs à protéger

| Actif | Exemples | Gravité d'une fuite ou d'une altération |
|---|---|---|
| Composantes de prix internes | Prix net fournisseur, coûts externes, marge, commission (CdC §2, §17, §61) | Critique : cœur du modèle commercial A (R-01) |
| Coordonnées bancaires | Exportateurs (CdC §11) **et MadaSource** (paramètres) | Critique : détournement de paiement |
| Comptes et sessions | Mots de passe, jetons, comptes admin | Critique |
| Documents privés | Immatriculation, contrats, factures, justificatifs, documents d'export (CdC §26, §61) | Élevée |
| Intégrité des transactions | Propositions, acceptation, Trade, statuts, paiements enregistrés | Élevée (fraude, litige) |
| Communications privées | Conversations, questions sur les RFQ (CdC §61) | Élevée |
| Données personnelles | Contacts des organisations | Élevée (Q-68) |
| Journal d'audit | Traçabilité (CdC §52) | Élevée |
| Confiance | Badges de vérification, Passport, avis, indicateurs (CdC §8-9, §42-43) | Élevée |

## 2. Acteurs de menace

1. **Visiteur anonyme** : collecte du catalogue, spam d'inscriptions et de RFQ, attaque des mots de passe, énumération des comptes.
2. **Utilisateur d'une autre organisation** : accès horizontal (BOLA), y compris par un identifiant glissé dans un corps de requête.
3. **Exportateur concurrent destinataire de la même RFQ** : lecture des questions, documents ou conversations d'un autre exportateur.
4. **Partie commerciale curieuse** : l'exportateur cherche la marge ou le prix acheteur, l'acheteur cherche le prix net, par lecture directe ou par recoupement.
5. **Membre d'une organisation** : action hors de son rôle (modifier l'IBAN, ajouter des membres).
6. **Compte compromis**, et en particulier **compte admin compromis** : impact transversal.
7. **Administrateur** : erreur, abus ou fraude interne (confirmation de paiement fictif).
8. **Fraudeur utilisant l'instance DEMO** : fausses confirmations présentées comme réelles.
9. **Contenu malveillant** : fichier piégé, texte injecté, métadonnées embarquées.
10. **Dépendance compromise** : chaîne d'approvisionnement logicielle.

## 3. OWASP API Security Top 10 (2023) : contrôles MadaSource

| Risque | Contrôles | Sections | Jours |
|---|---|---|---|
| API1 Broken Object Level Authorization | Politique d'accès par objet ; participation matérialisée ; identifiants du corps contrôlés ; collections imbriquées filtrées ; 404 | 5 | 9 et chaque module |
| API2 Broken Authentication | Argon2id, jetons courts, sessions révocables, détection de rejeu, réponses non énumérantes, second facteur admin | 4 | 8, 10, 11 |
| API3 Broken Object Property Level Authorization | Projections par audience, liste blanche des champs modifiables, non-déduction des prix | 6, 7 | Chaque module |
| API4 Unrestricted Resource Consumption | Pagination bornée, limites de taille, délais SQL, limites de débit | 15 | 5, 8 |
| API5 Broken Function Level Authorization | Refus par défaut, permission explicite par route, ensembles de permissions admin | 5 | 9 |
| API6 Unrestricted Access to Sensitive Business Flows | Quotas par organisation, plafond de destinataires, séparation des tâches sur les paiements, version de l'offre acceptée | 6, 8, 15 | 19 à 33 |
| API7 Server Side Request Forgery | Aucune requête sortante vers une URL fournie par un utilisateur | 14 | Tous |
| API8 Security Misconfiguration | Garde-fous de démarrage, en-têtes, CORS strict, OpenAPI non public en production | 16 | 4, 5 |
| API9 Improper Inventory Management | OpenAPI à jour, routes des modules désactivés non montées, routes admin hors de tout schéma public | 16 | 5, Audit D |
| API10 Unsafe Consumption of APIs | Réponses des tiers validées, délais d'expiration, couche d'intégration (D-21) | — | Intégrations futures |

## 4. Authentification

| ID | Décision | Statut |
|---|---|---|
| S-01 | Mots de passe hachés en **Argon2id** par une bibliothèque maintenue (choix au Jour 8). Paramètres alignés sur les recommandations OWASP en vigueur, vérifiées au Jour 8. Rehachage transparent si les paramètres changent. Aucune cryptographie maison. | Proposé |
| S-02 | Politique de mot de passe : longueur minimale, refus des mots de passe connus comme compromis. Valeurs : Q-76. | À VALIDER |
| S-03 | **Jeton d'accès** : JWT signé, durée courte (proposition : 15 minutes, Q-76), algorithme fixé côté serveur. Vérification de `iss`, `aud`, `exp`, `iat`, `sub` (utilisateur), `sid` (session) et `jti`. Le jeton ne transporte **ni rôle ni permission** : ils sont relus à chaque requête, pour qu'un retrait ou une suspension prenne effet immédiatement. | Proposé |
| S-04 | **Jeton de rafraîchissement** : valeur aléatoire opaque d'au moins 256 bits, stockée **hachée**, rattachée à une session. Rotation à chaque usage. Un jeton déjà consommé qui est réutilisé révoque toute la session (détection de vol). Durée : Q-76. | Proposé |
| S-05 | **Révocation immédiate** à la déconnexion, au changement ou à la réinitialisation du mot de passe, à la suspension du compte et au retrait d'adhésion. La session (`sid`) est vérifiée à chaque requête. | Proposé |
| S-06 | **Connexion** : réponse unique (BR-ACC-05), durée comparable (hachage effectué même pour un compte inexistant), limites par IP et par compte, ralentissement progressif plutôt que blocage définitif. | Proposé |
| S-07 | **Vérification d'email et réinitialisation** : jetons à usage unique, stockés hachés, de courte durée. Réinitialisation suivie d'une révocation des sessions (RJ 10, RJ 11). | Proposé |
| S-08 | **Premier administrateur** : jamais par une route publique (RJ 10 : « processus sûr », « pas de route publique de bootstrap »). Proposition : une commande en ligne exécutée sur le serveur. Les administrateurs suivants sont créés ou promus par une intervention orchestrée par `admin`, avec audit et notification aux autres admins. | Retenu (pas de route publique) / Proposé (commande en ligne, Q-14) |
| S-09 | **Second facteur obligatoire pour les administrateurs**, qui accèdent aux marges, aux données bancaires et aux confirmations de paiement. Mise en œuvre proposée :<br>- la session (`auth`) porte un indicateur « second facteur vérifié » ;<br>- à la construction de l'acteur, `access_control` n'accorde les permissions admin qu'à une session qui le porte.<br><br>Ainsi, `auth` n'a pas besoin de savoir qui est admin. Second facteur facultatif ou obligatoire pour les organisations clientes : à décider. | À VALIDER (Q-80) |
| S-10 | Transport des jetons pour le futur frontend web (cookie `HttpOnly`, `Secure`, `SameSite` avec protection CSRF, ou en-tête seul) : à décider avec l'architecture du frontend. L'API accepte `Authorization: Bearer`. | À VALIDER |
| S-35 | **Ré-authentification récente** (mot de passe, et second facteur s'il est actif) exigée pour les actions sensibles : changement d'email ou de mot de passe, modification des coordonnées bancaires, confirmation ou remboursement d'un paiement, gestion des comptes admin, modification des règles de prix. | Proposé |
| S-56 | **Réponses non énumérantes** pour l'inscription, la réinitialisation et le renvoi de vérification : même réponse, que l'adresse soit déjà connue ou non. La suite se fait par email. L'unicité d'un nom de société ou d'un slug ne doit pas révéler une inscription en attente (F-4). | Proposé |

## 5. Autorisation

### 5.1 Politique d'accès

| ID | Décision | Statut |
|---|---|---|
| S-28 | Pour chaque ressource, une **politique d'accès** côté serveur répond, pour un triplet (acteur, action, ressource), soit par une **audience** (section 5.2), soit par un **refus**. Refus par défaut. Elle est évaluée à chaque requête, à partir de l'adhésion, du statut du compte et des rôles **courants**. | Proposé |
| S-11 | Permissions nommées `<ressource>:<action>`. L'association rôles-permissions est une donnée (tables), pas du code. | Proposé |
| S-12 | Rôles actifs en V1 : Buyer, Exporter, MadaSource Admin. Permissions admin **regroupées en ensembles distincts** : lecture financière (marges, prix nets), données bancaires, confirmation et remboursement de paiement, règles de prix et de matching, comptes admin, lecture des conversations, journal d'audit. Cela prépare les rôles futurs (CdC §53). Faut-il les séparer entre admins dès la V1 ? Q-89. | Proposé |
| S-13 | Toute route est privée sauf déclaration explicite comme publique. Chaque route privée déclare sa permission. | Proposé |
| S-58 | Un acteur **Système** explicite, aux permissions minimales et audité, pour les traitements automatiques : matching, calcul des indicateurs, simulations DEMO (« Système DEMO », D-18). | Proposé |

### 5.2 Audiences : remplacement de la notion de « partie »

En Modèle A, une transaction implique **trois** acteurs : acheteur, MadaSource, exportateur. Une seule notion de « partie », où chacun voit ce que voit l'autre, conduit à exposer la marge (constat C-1).

| ID | Décision | Statut |
|---|---|---|
| S-29 | Toute lecture est servie pour une **audience explicite** : `public`, `buyer` (organisation acheteuse partie), `exporter_owner` (organisation exportatrice émettrice ou propriétaire), `exporter_recipient` (exportateur destinataire d'une RFQ), `madasource` (admin), `madasource_finance` (admin habilité aux données financières) et `self` (l'utilisateur sur son propre compte et ses notifications). La politique d'accès choisit l'audience, jamais le router. P-01 ([module-boundaries.md](module-boundaries.md)) renvoie une audience, pas un booléen. Correspondance avec les suffixes de schémas : [api-conventions.md](api-conventions.md#13-openapi). | Proposé |
| S-30 | **Participation matérialisée** : on n'est participant qu'à travers un enregistrement explicite et actif. Il s'agit du destinataire de RFQ avec son statut, des parties du Trade et des participants d'une conversation. Un destinataire retiré ou suspendu perd l'accès ; un destinataire qui a décliné ne voit plus que ses propres contributions (F-1). | Proposé |
| S-31 | Dans une RFQ adressée à plusieurs exportateurs, tout objet partagé est rattaché à la **paire (RFQ, exportateur destinataire)** : questions, réponses, documents, conversations. Un exportateur ne voit jamais les échanges d'un concurrent. La diffusion à tous les destinataires n'a lieu que sur une action explicite de l'acheteur (Q-84). | Proposé |
| S-36 | **Invariant** : l'organisation acheteuse et l'organisation exportatrice d'une RFQ, d'une quotation ou d'un Trade sont toujours différentes, quelle que soit la réponse à Q-09 (F-2). | Proposé |

### 5.3 Contrôle d'objet (BOLA)

| ID | Décision | Statut |
|---|---|---|
| S-14 | Tout accès à un objet passe par une requête filtrée par l'acteur (organisation propriétaire ou participation matérialisée), via des fonctions de repository `get_for_actor` et `list_for_actor`. Un accès non filtré n'existe que pour le Système et l'administration, sous un nom explicite. | Proposé |
| S-14 | **Tout identifiant reçu**, qu'il vienne du chemin, du corps ou des paramètres, passe par la politique d'accès avec l'action précise : lire, rattacher ou partager. Exemples : un document glissé dans un litige, un produit non publié cité dans une RFQ (E-5). | Proposé |
| S-14 | Les **collections imbriquées** (documents, messages, paiements d'un Trade) sont filtrées élément par élément. Les totaux de pagination portent sur l'ensemble autorisé. | Proposé |
| S-15 | Objet hors périmètre : **404**, identique à un objet inexistant (D-25). Code 403 réservé à une action interdite sur un objet visible. | Proposé |
| S-14 | **Détection des tentatives** d'accès inter-organisations, pour l'audit de sécurité (section 18) : après un refus, une lecture système non filtrée vérifie seulement l'existence de l'objet et son organisation. Elle est limitée en débit et son résultat n'est jamais renvoyé au client. C'est une exception déclarée à l'accès filtré. | Proposé |
| S-17 | Sécurité au niveau des lignes de PostgreSQL : défense en profondeur possible, **non retenue en V1**. Le filtrage S-14 est obligatoire. | Proposé |

### 5.4 Administration

| ID | Décision | Statut |
|---|---|---|
| S-16 | Accès admin étendu mais non illimité : permissions explicites (S-12), chaque action auditée, aucune modification de l'historique (propositions, TradeEvent, audit), même par un admin. | Proposé |
| S-16 | Les **consultations** sensibles sont auditées, comme les modifications : données bancaires, documents privés, conversations, journal d'audit, exports. | Proposé |
| S-32 | Une intervention admin « pour le compte de » une organisation (Q-40) est marquée comme telle, motivée, auditée et notifiée à l'organisation. Elle est orchestrée par le module `admin`, seul à pouvoir appeler les modules concernés et `notifications` sans import montant ([module-boundaries.md](module-boundaries.md) §4). **L'usurpation d'identité est interdite.** | Proposé |
| S-33 | Un administrateur appartient à l'organisation interne MadaSource et n'est **jamais membre d'une organisation cliente** (Q-74). | Proposé. **Jour 3 : remplacement PROPOSED** (Q-74) : aucune organisation interne ; rôles de plateforme (`platform_role_assignments`). L'interdiction d'une adhésion cliente pour un compte admin reste à confirmer ([registre](../decisions/architecture-decisions.md)). |
| S-34 | **Séparation des tâches sur les paiements** : l'admin qui a saisi un Payment Record ou l'a passé en Processing ne peut pas le confirmer. Même règle pour un remboursement. Une double validation au-delà d'un seuil est possible (Q-88). | Proposé |
| S-09, S-35 | Second facteur et ré-authentification (section 4). | À VALIDER, Proposé |
| — | Comptes admin nominatifs, jamais partagés. Création et promotion sous permission dédiée, orchestrées par `admin`, avec audit et notification aux autres admins (S-08, Q-14). Revue périodique des comptes, désactivation au départ. | Proposé |

## 6. Confidentialité commerciale

### 6.1 Projections et champs modifiables

| ID | Décision | Statut |
|---|---|---|
| S-37 | Chaque objet exposé déclare une **projection par audience** : une liste blanche de champs, implémentée par un schéma distinct qui hérite de la classe de base de son audience. La politique d'accès choisit l'audience ; le router instancie **explicitement** le schéma correspondant, sans union de schémas résolue automatiquement (D-32). Les tests vérifient l'**ensemble exact** des clés de chaque projection ([testing-strategy.md](testing-strategy.md)). | Proposé |
| S-38 | **Liste blanche des champs modifiables** par entité et par audience. Tout champ fixé par le serveur (statut, organisation, marge, niveau de vérification…) est refusé en 422 (constat M-8). | Proposé |

### 6.2 Composantes de prix (R-01)

| ID | Décision | Statut |
|---|---|---|
| S-18 | Le **prix net fournisseur** et la **marge MadaSource** ne sont jamais servis à l'audience `public` ni à l'audience `buyer`. La marge n'est jamais servie à une audience exportateur (BR-PRC-09). | Retenu (CdC §2 et §61 « Commercial margins » ; RJ 24 « coûts fournisseurs confidentiels », « marges internes ») |
| S-18 | **Coûts externes** détaillés et **commission** : leur visibilité pour l'acheteur et l'exportateur n'est pas fixée par les sources. Coûts externes : Q-04. Commission visible de son payeur : S-41, Q-03. | À VALIDER (Q-03, Q-04) |
| S-19 | **Non-déduction** : pour chaque audience, la liste des composantes de prix visibles est **fermée et documentée**. Il faut démontrer qu'elle ne permet pas de recalculer une composante cachée, par recoupement de champs, de prix FOB et CIF, de totaux, de paiements, de remboursements, de prix d'échantillon ou de tableaux de bord. Un champ public est visible de **tous** les exportateurs, y compris pour leurs propres produits (constat E-1). | Proposé |
| S-39 | En Modèle A, le Trade fige **deux jeux de termes** : les termes acheteur (prix final) et les termes fournisseur (prix net). Chaque audience ne reçoit que les siens. Quels objets du Trade sont partagés et lesquels restent bilatéraux avec MadaSource : Q-82. | Proposé (Q-01, Q-82) |
| S-40 | Les **Payment Records sont orientés** : acheteur → MadaSource et MadaSource → exportateur en Modèle A ; acheteur → exportateur en Modèle B. Chaque justificatif hérite de l'audience de son paiement (Q-54, Q-82). | Proposé |
| S-41 | La commission (Modèle B) est visible de **son payeur** seulement, et distincte de la marge (Q-03). | Proposé |
| S-20 | Filtres et tris permis seulement sur les champs visibles de l'audience ([api-conventions.md](api-conventions.md#6-pagination-tri-et-filtres)). | Proposé |
| S-42 | **Pas d'oracle** :<br>- aucune décision automatique fondée sur une valeur cachée à la contrepartie (par exemple le rejet automatique d'une contre-offre sous un prix plancher, qui permettrait de trouver ce plancher par essais successifs) ;<br>- messages d'erreur sans montant ni seuil ;<br>- limites de débit sur les actions de négociation. | Proposé |
| S-21 | Erreurs, journaux applicatifs et notifications ne contiennent aucune composante de prix. Le journal d'audit en contient, sous les conditions de la section 18. | Proposé |

### 6.3 Prix présenté et prix accepté

| ID | Décision | Statut |
|---|---|---|
| S-43 | Le prix présenté à l'acheteur est **calculé et stocké** au moment de la présentation, avec la version des règles de prix. Toute modification d'une offre crée une **nouvelle version**. L'acceptation transmet la version vue ; en cas d'écart, la réponse est 409 (`OFFER_VERSION_MISMATCH`). Le Trade copie les valeurs stockées, sans recalcul (constat E-11). Effet d'un changement de règle sur une offre déjà présentée : Q-91. | Proposé |

## 7. Coordonnées bancaires

| ID | Décision | Statut |
|---|---|---|
| S-22 | Coordonnées bancaires **chiffrées au niveau applicatif** par une bibliothèque cryptographique maintenue, clé hors de la base. Lecture intégrale réservée à l'organisation propriétaire et à l'ensemble de permissions « données bancaires », sur action explicite et auditée. Affichage masqué par défaut. | Proposé (Q-81) |
| S-44 | **Modification sous contrôle renforcé** : permission dédiée, ré-authentification (S-35), notification à tous les membres de l'organisation, re-vérification par MadaSource avant prise d'effet, délai de prise d'effet. Le même régime s'applique aux coordonnées bancaires de **MadaSource**, qui sont les comptes de réception détenus par `payment_records` (ce module les présente à l'acheteur selon Q-55, sans lecture montante). Modalités : Q-87 (constat E-4). | Proposé (Q-87) |
| S-23 | Coordonnées à présenter à l'acheteur pour un virement (MadaSource ou exportateur) : décision commerciale et juridique. | À VALIDER (Q-55) |

## 8. Intégrité des transactions

- Transitions uniquement par les services, sous verrou `FOR NO KEY UPDATE` avec relecture de la ligne (`populate_existing`), puis revérification de l'état (D-09).
- Actions critiques idempotentes, contraintes d'unicité en dernier rempart (D-09).
- Version de l'offre acceptée (S-43).
- Séparation des tâches sur les paiements (S-34).
- Historique immuable par les opérations normales (BR-NEG-02, BR-TRD-07, BR-AUD-02).
- Un justificatif ne confirme jamais un paiement (BR-PAY-03).

## 9. Documents (Jour 29)

| ID | Décision | Statut |
|---|---|---|
| S-24 | Chaque document **et chaque version** porte une **audience explicite**, vérifiée en plus de l'accès au contexte. La participation au contexte ne suffit pas. Valeur par défaut : la plus restrictive (organisation déposante et MadaSource). Exemple : une facture de l'exportateur à MadaSource en Modèle A révèle le prix net et ne doit jamais être servie à l'acheteur. Valeurs de visibilité d'un document ou d'un texte libre : `owner` (organisation déposante et MadaSource), `buyer_side`, `exporter_side`, `parties` (les deux côtés), `internal` (MadaSource seulement). Elles se traduisent en audiences de lecture (S-29) via P-01. | Proposé. **Jour 3** : valeurs remplacées par celles de Q-82 (PROPOSED) : `BUYER_VISIBLE`, `EXPORTER_VISIBLE`, `BOTH_PARTIES`, `INTERNAL_ONLY`, plus `OWNER_ONLY` et `PUBLIC` (Q-96) ; correspondance : [data-classification.md](data-classification.md) §2 |
| S-24 | Catégories **jamais publiques** : documents de société, de paiement, fiscaux, bancaires, et documents d'onboarding exportateur (ces derniers ne sont jamais partagés, constat F-5). Qui fixe l'audience, valeurs par défaut par catégorie, validation admin avant partage : Q-83. | Proposé |
| S-24 | Le retrait d'un partage est possible sans suppression, et audité. Les listes de documents sont filtrées par audience, avec des noms affichés nettoyés : l'existence d'un document invisible n'est jamais révélée. Un document généré par la plateforme (quotation, facture, récapitulatif) est rendu **pour chaque audience**. | Proposé |
| S-45 | Rattacher un document à un message, un litige, un TradeEvent ou un paiement exige le **droit de le partager** avec l'audience cible. | Proposé |
| S-25 | Formats admis PDF, JPG, PNG, DOCX (CdC §26), vérifiés sur le contenu réel. Refus des formats à macros et des archives. Taille maximale et analyse antivirus : Q-48. | Proposé |
| S-26 | Clé de stockage aléatoire, sans nom de fichier ni organisation. Stockage privé. URL signée courte, propre à un objet, **jamais journalisée ni placée dans une notification**. Contrôle d'accès à chaque téléchargement pour les documents bancaires et d'immatriculation. `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`. | Proposé |
| S-27 | **Métadonnées embarquées** : suppression des métadonnées des images (EXIF, dont la géolocalisation) au dépôt. Politique pour les métadonnées des documents bureautiques (auteur, société, suivi des modifications) : Q-83. | Proposé |

## 10. Messagerie et textes libres

| ID | Décision | Statut |
|---|---|---|
| S-46 | Une conversation = un contexte + une **liste explicite de participants**. Dans une RFQ, une conversation par paire acheteur–exportateur (S-31). Les questions des exportateurs sont privées par défaut (Q-84). L'accès suit l'évolution de la participation (S-30). | Proposé |
| S-46 | Lecture des conversations par l'admin : Q-50. Si elle est permise, elle est motivée, auditée et signalée aux participants. Les messages d'un admin sont signés « MadaSource ». | À VALIDER |
| S-47 | **Tout texte libre porte une audience** : commentaires de TradeEvent, notes d'exception et de litige, motif de rejet de vérification. Pour un texte saisi par un admin, l'audience par défaut est « interne ». Le motif de rejet communiqué à l'exportateur est un champ distinct de la note interne (constat M-5). | Proposé |
| — | Le texte saisi par les utilisateurs (prix, coordonnées) ne peut pas être contrôlé techniquement sans filtrage. Politique : Q-51 (R-05). | À VALIDER |

## 11. Autres projections sensibles

| ID | Décision | Statut |
|---|---|---|
| S-48 | **Identité de l'acteur** dans les historiques et les documents, rendue selon l'audience :<br>- libellé d'organisation selon Q-27 ;<br>- nom d'un utilisateur visible seulement au sein de sa propre organisation ;<br>- « MadaSource » pour un admin ;<br>- jamais d'email (constat M-6). | Proposé |
| S-49 | Les **raisons du matching** sont produites dans la projection du lecteur : critère satisfait ou non, jamais la valeur privée d'un tiers, comme « capacité : 12 t » montrée à l'acheteur. Visibilité : Q-31 (constat M-4). | Proposé |
| S-50 | **Projection de la RFQ pour l'exportateur destinataire** : liste fermée de champs (prix cible, préférence de paiement, port, exigences…), à fixer (constat M-3). | À VALIDER (Q-85) |
| S-51 | **Profil public exportateur** en liste blanche. Le CdC §61 ne rend publics que le nom, les produits, la vérification, la localisation générale et les certifications. Pour le reste du §7 (capacité, taux de litige…) et pour un seuil d'activité minimal avant d'afficher un indicateur (sur un seul Trade, « 100 % de litiges » révèle un fait privé) : Q-86 (constat M-2). | À VALIDER (Q-86) |

## 12. Notifications

| ID | Décision | Statut |
|---|---|---|
| S-52 | Une notification ne stocke que son **code de type**, la référence de l'objet et son destinataire : aucun texte composé, aucun montant, aucune URL signée. Le client affiche le libellé du type (D-19). Pour le détail, il lit l'objet par l'endpoint du module qui le possède, qui applique la projection et les droits **courants** du lecteur. `notifications` filtre sur l'adhésion courante : un utilisateur retiré d'une organisation ne voit plus les notifications de celle-ci (constats M-10, C7). | Proposé |

## 13. Vérification, Passport et références

| ID | Décision | Statut |
|---|---|---|
| S-53 | Les champs couverts par une vérification (raison sociale, immatriculation…) sont gelés, ou bien leur modification renvoie la vérification en revue, avec badge suspendu (constat M-11). Dans les deux cas, ils ne se modifient **que par `exporters`**, qui orchestre la remise en revue, et jamais par `/organizations/current`. | À VALIDER (Q-90) |
| S-54 | Un slug de Passport n'est **jamais réattribué** : des QR codes imprimés y pointent. Une référence lisible (`MST-…`) n'est jamais une clé d'accès sans contrôle. Les références séquentielles révèlent le volume d'activité : à faire accepter ou non (Q-37) (constat F-3). | Proposé |

## 14. Validation des entrées et injections

| Règle | Statut |
|---|---|
| Schémas Pydantic typés et bornés ; montants et quantités en chaînes décimales ([api-conventions.md](api-conventions.md#7-dates-montants-quantités)). | Proposé |
| SQL uniquement paramétré (SQLAlchemy) ; colonnes de tri choisies dans une liste blanche. | Proposé |
| Texte libre stocké en texte brut, sans HTML. L'échappement revient au frontend (XSS stocké). | Proposé |
| `X-Request-ID` reçu : format et longueur validés avant journalisation. | Proposé |
| Aucune requête sortante vers une URL fournie par un utilisateur (SSRF). Le QR code est produit à partir de l'URL publique connue. | Proposé |

## 15. Limites, quotas et abus

| ID | Décision | Statut |
|---|---|---|
| — | Limites de débit sur : connexion, rafraîchissement, inscription, réinitialisation, renvoi de vérification, création de RFQ, propositions de négociation, messages, dépôts, recherche publique (CdC §60). Clés : IP et compte pour la connexion ; utilisateur ailleurs. | Proposé |
| — | Emplacement : reverse proxy (limites grossières) et application (limites fines). Avec plusieurs instances, un stockage partagé (Redis) est nécessaire et doit être justifié au Jour 8. | À VALIDER (Jour 8) |
| S-55 | **Quotas métier** par organisation et par statut de compte (Q-11) : nombre de RFQ, plafond de destinataires par RFQ (Q-30). Les RFQ jugées abusives sont exclues des indicateurs de performance des exportateurs (constat M-13). | Proposé ; seuils À VALIDER (Q-30, Q-86) |
| — | Pagination bornée, taille maximale des requêtes, délai d'exécution maximal des requêtes SQL, 429 avec `Retry-After`. | Proposé |

## 16. Transport, en-têtes et configuration

| Règle | Statut |
|---|---|
| HTTPS obligatoire en production, HSTS. | Proposé |
| CORS : liste blanche des origines du frontend, jamais `*` en production (D-11). | Proposé |
| En-têtes `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` sur toute réponse privée ; aucune bannière de version. | Proposé |
| Documentation interactive et schéma OpenAPI **désactivés en production publique**. Les routes admin n'apparaissent dans aucun schéma public (constat F-6). | Proposé |
| Démarrage refusé en production en cas de configuration dangereuse (D-11). | Proposé |

## 17. Secrets et hygiène du dépôt

| Règle | Statut |
|---|---|
| Secrets uniquement dans les variables d'environnement ou le gestionnaire de secrets de l'hébergeur (Q-79). Jamais dans Git, une image Docker, un journal ou la configuration CI en clair. | Retenu (RJ section 1) |
| `.gitignore` : `.env`, `.env.*`, `*.env`, `.envrc` (sauf `.env.example`), environnements virtuels et `.claude/settings.local.json` exclus (Jour 4, motifs `*.env` et `.envrc` au Jour 7 ; R-20 clos). Contrôle CI (job `secrets`) : aucun de ces fichiers dans l'arbre suivi **ni dans l'historique** (ajout puis suppression compris). | Retenu (Jour 4) ; contrôle CI écrit au Jour 7 et rejoué en local ; sa forme étendue (historique, `*.env`, `.envrc`) s'exécutera sur GitHub au prochain push |
| Le cahier des charges est versionné et poussé sur le dépôt distant. `CLAUDE.md`, `roadmap.md` et `roadmap_backend_fastapi.md` ont été retirés de l'index le 2026-10-12 (commit f598049), mais ils restent dans l'**historique** poussé (commit c6e27d8). **Dépôt constaté public le 2026-10-13** : passage en privé requis, par l'utilisateur (R-26, Q-71). Retirer des fichiers de l'historique serait une opération destructive : seulement avec l'accord explicite de l'utilisateur, et sans effet sur les clones existants. | À VALIDER |
| Procédure de rotation documentée (Audit D). Une rotation de la clé de signature invalide les jetons en cours ; la rotation de la clé de chiffrement bancaire impose un rechiffrement (Q-81). | Proposé |
| Détection de secrets. **Sur le poste** : aucune analyse du contenu ; le hook `guard_files.py` bloque seulement les lectures et écritures de Claude sur des fichiers sensibles, d'après leur nom, et n'intercepte ni `git commit` ni `git push`. **En CI** : gitleaks 8.30.1 (choix de l'utilisateur), binaire officiel vérifié par sa somme SHA-256, sur tout l'historique Git, valeurs masquées (`--redact`). Configuration explicite `.github/gitleaks.toml` : règles par défaut, plus la règle `url-credentials` (mot de passe dans une URL, qu'aucune règle par défaut ne couvre). Exceptions, toutes dans ce fichier : préfixe `changeme` (valeurs de `.env.example`, refusées par la configuration en `staging`, `production` et `demo`) ; quatre valeurs factices exactes des tests, sous `backend/tests/` seulement, déjà présentes dans l'historique. Un `.gitleaksignore` ou un `.gitleaks.toml` suivi fait échouer la CI ; les commentaires `gitleaks:allow` sont ignorés. Un auto-test vérifie à chaque exécution qu'un mot de passe aléatoire dans une URL est détecté. | Écrit au Jour 7. Version intermédiaire (règles par défaut seulement) exécutée sur GitHub le 2026-10-14 : aucune fuite. Version actuelle rejouée en local (historique : aucune fuite ; auto-test : détection), à exécuter sur GitHub au prochain push |
| Limites de la détection en CI : elle a lieu **après** le push, et le dépôt est public (Q-71) : un secret poussé est exposé, il doit être changé immédiatement, le retirer de l'historique ne suffit pas. gitleaks n'analyse pas les PDF ni les documents bureautiques (exclus par ses règles par défaut, cahier des charges compris), ni le diff propre d'un commit de fusion, ni les commits retirés par un push forcé. Sur le poste, une analyse avant commit (hook gitleaks) et, sur GitHub, Secret Protection et la protection au push sont proposées (Q-104 f, g). | Constaté (Jour 7) ; mesures complémentaires À VALIDER |
| CI sans secret ni privilège : jeton GitHub en lecture seule, identifiants Git non conservés, jamais de `pull_request_target`, `workflow_run` ni `issue_comment`, aucun secret GitHub utilisé, aucune publication. Actions tierces épinglées par empreinte de commit, outils et images vérifiés par empreinte ; pas de cache de dépendances entre exécutions. Délai de carence de 14 jours appliqué aux actions et aux binaires de la CI, pas encore à uv ni aux paquets Python (Q-104 b). Tant que le dépôt est public (Q-71), les journaux de CI le sont aussi : ils ne contiennent que des valeurs factices. Sans protection de la branche `main` (statuts requis), un échec de la CI ne bloque ni push ni fusion (Q-104 f). | Écrit au Jour 7 ; première exécution sur GitHub le 2026-10-14 (commit `98dceb2`, version intermédiaire du workflow) : quatre jobs réussis ; la version corrigée après les revues s'exécutera au prochain push ; réglages GitHub À VALIDER |
| Mot de passe du rôle applicatif (`infrastructure/postgres/10-create-app-role.sh`) : lu par `psql` dans l'environnement (`\getenv`), jamais en argument ; journalisation du serveur coupée pour la session ; `psql` en mode `VERBOSITY terse`, pour qu'une erreur ne recopie pas la ligne contenant le mot de passe dans les journaux du conteneur (comportement vérifié au Jour 7 avec une valeur factice). | Implémenté (Jours 6 et 7) |

## 18. Journalisation et audit

| Règle | Statut |
|---|---|
| Journaux applicatifs nettoyés (D-12) : en plus des secrets, ni prix net, ni marge, ni coût, ni commission. Identifiants plutôt que noms ou emails. | Proposé |
| **Audit métier** (RJ 12, CdC §52) et **événements de sécurité** : échecs de connexion, réinitialisations, refus d'accès inter-organisations (tentatives BOLA), téléchargements sensibles, consultations de données bancaires, lectures admin de conversations, exports, changements de permissions et de feature flags. | Proposé |
| Les anciennes et nouvelles valeurs sont stockées **selon la classification des champs** ([data-classification.md](data-classification.md) §4) : en clair, masquées (coordonnées bancaires) ou réservées à l'ensemble de permissions « lecture financière » (composantes de prix). La consultation du journal d'audit est elle-même auditée. | Proposé |
| Ajout seul. Le rôle de base de données de l'application n'a pas les droits `UPDATE` et `DELETE` sur la table d'audit (Jour 12). Garantie d'intégrité supplémentaire (chaînage) : à évaluer. Conservation : Q-69. | Proposé |
| Données personnelles dans l'audit réduites aux identifiants, pour concilier immuabilité et droit à l'effacement (Q-68). | Proposé |

## 19. Base de données

| Règle | Statut |
|---|---|
| Deux rôles PostgreSQL : propriétaire du schéma pour les migrations (DDL) et `madasource_app` pour l'application (DML sans DDL, droits accordés table par table). | **Retenu et implémenté au Jour 6** ([indexes-and-constraints.md](indexes-and-constraints.md) §6.1) |
| Base jamais exposée publiquement ; connexion chiffrée en production ; sauvegardes chiffrées et restauration testée (Audit D). | Proposé |
| Aucun outil ni agent connecté à une base de production. | Retenu |

## 20. Mode DEMO

| ID | Décision | Statut |
|---|---|---|
| D-18 | Instance distincte, avec sa propre base, son propre stockage et ses propres secrets ; démarrage refusé en production avec `DEMO_MODE`. Les simulations exécutent les cas d'usage normaux par l'acteur « Système DEMO » (S-58), via des endpoints montés seulement en environnement `demo` ([architecture.md](architecture.md#82-mode-demo-cdc-68)). | Proposé (Q-67) |
| S-57 | Compléments, contre l'usage d'une capture d'écran DEMO comme preuve de paiement (constat E-10) :<br>- **espace de noms distinct** : préfixe DEMO dans toute référence lisible (`RFQ-`, `MSQ-`, `MST-`), donc visible dans chaque corps de réponse qui porte une référence et sur toute capture ;<br>- filigrane DEMO sur les documents générés ;<br>- en-tête `X-MadaSource-Mode: demo` ; bannière côté frontend ;<br>- emails désactivés, ou limités à une liste blanche ;<br>- accès sur invitation, aucune donnée réelle ;<br>- endpoints de simulation non montés hors de l'environnement `demo` (garde au démarrage, D-11). | Proposé |

## 21. Tests de sécurité

En plus de la matrice obligatoire et des contrôles de non-exposition de [testing-strategy.md](testing-strategy.md), la relecture du Jour 2 demande notamment :

| Test | Contrôle |
|---|---|
| `test_model_a_no_buyer_price_in_any_exporter_response` et son symétrique | C-1, S-19, S-39 |
| `test_margin_not_derivable_per_audience`, `test_exporter_public_view_equals_visitor_view` | E-1, S-19 |
| `test_exporter_b_cannot_read_exporter_a_rfq_question_or_document` | E-2, S-31 |
| `test_trade_document_list_hides_non_visible_items`, `test_superseded_version_keeps_own_audience`, `test_company_document_cannot_be_public` | E-3, S-24 |
| `test_bank_details_change_requires_reauth_and_notifies` | E-4, S-44 |
| `test_attach_foreign_document_returns_404`, `test_nested_trade_collections_filtered` | E-5, S-14, S-45 |
| `test_admin_without_finance_permission_gets_no_margin`, `test_admin_cannot_join_customer_org` | E-6, S-12, S-33 |
| `test_same_admin_cannot_record_and_confirm_payment` | E-7, S-34 |
| `test_public_filter_on_hidden_price_rejected`, `test_counteroffer_error_contains_no_amount` | E-9, S-20, S-42 |
| `test_demo_references_distinct_prefix`, `test_demo_payload_flagged` | E-10, S-57 |
| `test_accept_stale_version_returns_409` | E-11, S-43 |
| `test_notification_holds_only_type_and_reference`, `test_notification_hidden_after_membership_removed` | M-10, S-52 |
| `test_org_cannot_quote_on_own_rfq` | F-2, S-36 |
| `test_register_existing_email_same_response` | F-4, S-56 |

## 22. Relecture de sécurité du Jour 2

Relecture par l'agent `security-auditor`, en lecture seule, de la matrice de visibilité du Jour 1 et des premiers brouillons du Jour 2. Résultat : **1 constat critique, 11 élevés, 14 moyens, 6 faibles**. Tous sont traités par une décision de ce document, une question ouverte, ou les deux. Aucun n'est ignoré.

| Constat | Gravité | Traitement |
|---|---|---|
| C-1 Notion de « partie » bilatérale en Modèle A trilatéral | Critique | S-29, S-39, S-40 ; P-01 renvoie une audience ; matrice du Jour 1 corrigée ; Q-82 |
| E-1 Marge recalculable par recoupement | Élevée | S-19 ; Q-02, Q-04, Q-05, Q-06 précisées |
| E-2 Fuite entre exportateurs concurrents d'une RFQ | Élevée | S-31, S-46 ; Q-84 |
| E-3 Documents : audience, versions, noms, métadonnées | Élevée | S-24, S-26, S-27, S-45 ; Q-83 |
| E-4 Modification des coordonnées bancaires | Élevée | S-35, S-44 ; Q-87 |
| E-5 BOLA par identifiant dans le corps ou par collection imbriquée | Élevée | S-14 |
| E-6 Admin unique, sans second facteur ni audit des consultations | Élevée | S-09, S-12, S-16, S-32, S-33, S-35 ; Q-80, Q-89 |
| E-7 Confirmation de paiement par un seul admin | Élevée | S-34 ; Q-88 |
| E-8 Lecture directe des tables par `marketplace` et `admin` | Élevée | Projections publiées par le module propriétaire ([module-boundaries.md](module-boundaries.md)) |
| E-9 Oracles : filtres, rejets automatiques, erreurs | Élevée | S-20, S-42 ; [error-handling.md](error-handling.md) |
| E-10 Mode DEMO marqué seulement par un en-tête | Élevée | S-57 |
| E-11 Prix présenté différent du prix accepté | Élevée | S-43 ; Q-91 |
| M-1 Objets sans ligne dans la matrice de visibilité | Moyenne | Lignes ajoutées dans [actors-and-permissions.md](actors-and-permissions.md) ; Q-92 (litiges) |
| M-2 Profil public déduit au lieu d'une liste blanche | Moyenne | S-51 ; Q-86 |
| M-3 Champs de la RFQ visibles par l'exportateur | Moyenne | S-50 ; Q-85 |
| M-4 Contenu des raisons du matching | Moyenne | S-49 |
| M-5 Annotations internes et partagées confondues | Moyenne | S-47 |
| M-6 Identité révélée par les champs « acteur » | Moyenne | S-48 |
| M-7 Audit : valeurs sensibles, événements de sécurité | Moyenne | Section 18 |
| M-8 Pas de liste blanche des champs modifiables | Moyenne | S-38 |
| M-9 Actions sensibles absentes de la matrice | Moyenne | Lignes ajoutées dans [actors-and-permissions.md](actors-and-permissions.md) ; S-32, S-35 |
| M-10 Notifications construites une fois puis diffusées | Moyenne | S-52 |
| M-11 Champs vérifiés modifiables | Moyenne | S-53 ; Q-90 |
| M-12 Commission confondue avec la marge | Moyenne | S-41 |
| M-13 Flux métier sans quotas | Moyenne | S-55 |
| M-14 CdC poussé sur le dépôt distant, pas de `.gitignore` | Moyenne | Section 17 ; R-20 et R-26 mis à jour ; signalé à l'utilisateur |
| F-1 Destinataire « autorisé à répondre » non défini | Faible | S-30 |
| F-2 Même organisation des deux côtés | Faible | S-36 |
| F-3 Références séquentielles, slugs réattribuables | Faible | S-54 |
| F-4 Énumération de comptes hors connexion | Faible | S-56 |
| F-5 « Documents d'export » recouvre deux notions | Faible | S-24 |
| F-6 Exposition d'OpenAPI en production | Faible | Section 16 |

Risques résiduels relevés par l'audit, sans solution technique complète :
- prix ou coordonnées écrits dans un texte libre (R-05, Q-51) ;
- documents physiques accompagnant la marchandise, qui peuvent révéler le prix net hors plateforme (CdC §75, R-04, Q-01) ;
- futur assistant IA (CdC §45), dont les explications devront rester dans la projection acheteur ;
- tension entre droit à l'effacement et audit immuable (R-14) ;
- risque interne admin, réduit mais jamais nul.
