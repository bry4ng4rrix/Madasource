# Conception de la sécurité — backend MadaSource

Jour 2 · 2026-10-12 · Statut : proposition à valider. Document vivant :
- primitives au Jour 8 ;
- organisations et RBAC au Jour 9 ;
- authentification au Jour 10 ;
- statuts de compte au Jour 11 ;
- audit au Jour 12 ;
- documents au Jour 29 ;
- vérification complète à l'Audit B.

Sources : CdC §11, §26, §52-54, §60-61 ; RJ section 1 ; OWASP API Security Top 10 (édition 2023) ; matrices de [actors-and-permissions.md](actors-and-permissions.md).
Décisions de sécurité : identifiants **S-NN** (section 17).

## 1. Actifs à protéger

| Actif | Exemples | Gravité d'une fuite ou d'une altération |
|---|---|---|
| Composantes de prix internes | Prix net fournisseur, coûts externes, marge, commission (CdC §2, §17, §61) | Critique : cœur du modèle commercial A (R-01) |
| Données bancaires et fiscales | Informations de l'exportateur (CdC §11) | Critique |
| Comptes et sessions | Mots de passe, jetons | Critique |
| Documents privés | Immatriculation, contrats, justificatifs de paiement, documents d'export (CdC §26, §61) | Élevée |
| Intégrité des transactions | Propositions, acceptation, Trade, statuts, paiements enregistrés | Élevée (fraude, litige) |
| Communications privées | Conversations entre acheteur et exportateur (CdC §61) | Élevée |
| Données personnelles | Noms, emails, téléphones, adresses des contacts | Élevée (Q-68) |
| Journal d'audit | Traçabilité des actions (CdC §52) | Élevée |
| Confiance | Badges de vérification, avis (CdC §8, §42) | Élevée |

## 2. Acteurs de menace

1. **Visiteur anonyme** : collecte automatisée du catalogue, spam d'inscriptions et de RFQ, attaque des mots de passe.
2. **Utilisateur d'une autre organisation** : accès horizontal à une RFQ, une quotation, un Trade ou un document (BOLA).
3. **Membre d'une organisation** : action hors de son rôle (élévation verticale).
4. **Partie commerciale curieuse** : l'exportateur cherche la marge ou le prix acheteur, l'acheteur cherche le prix net.
5. **Compte compromis** : vol de mot de passe ou de jeton.
6. **Administrateur** : erreur ou abus. Moindre privilège et traçabilité complète.
7. **Contenu malveillant** : fichier piégé, texte injecté.
8. **Dépendance compromise** : chaîne d'approvisionnement logicielle.

## 3. OWASP API Security Top 10 (2023) : contrôles MadaSource

| Risque | Contrôle principal | Section | Jour |
|---|---|---|---|
| API1 Broken Object Level Authorization | Accès aux objets par requêtes filtrées par l'acteur, 404 hors périmètre, tests inter-organisations | 5 | 9 et chaque module |
| API2 Broken Authentication | Hachage Argon2id, jetons courts, rotation et révocation des sessions, limites de débit | 4 | 8, 10, 11 |
| API3 Broken Object Property Level Authorization | Schémas par audience, entrée `extra="forbid"`, listes de champs autorisés, test statique de l'OpenAPI | 6 | Chaque module |
| API4 Unrestricted Resource Consumption | Pagination bornée, limites de taille, délais SQL, limites de débit | 9 | 5, 8 |
| API5 Broken Function Level Authorization | Permission explicite sur chaque route privée, refus par défaut, permissions admin granulaires | 5 | 9 |
| API6 Unrestricted Access to Sensitive Business Flows | Limites sur l'inscription, les RFQ et les propositions ; idempotence des actions critiques ; transitions contrôlées | 5, 9 | 19 à 33 |
| API7 Server Side Request Forgery | Aucun appel sortant vers une URL fournie par un utilisateur en V1 (par exemple le site web d'un acheteur n'est jamais appelé) | 8 | Tous |
| API8 Security Misconfiguration | Garde-fous de configuration en production, en-têtes, CORS strict, documentation désactivée en production | 10 | 4, 5 |
| API9 Improper Inventory Management | OpenAPI à jour, routes des modules désactivés non montées, versionnement | — | 5, Audit D |
| API10 Unsafe Consumption of APIs | Réponses des tiers validées, délais d'expiration, couche d'intégration (D-21) | — | Intégrations futures |

## 4. Authentification

| ID | Proposition | Statut |
|---|---|---|
| S-01 | Mots de passe hachés en **Argon2id** par une bibliothèque maintenue (choix au Jour 8). Paramètres alignés sur les recommandations OWASP en vigueur, vérifiées au Jour 8. Rehachage transparent à la connexion si les paramètres changent. Aucune cryptographie maison (RJ section 1). | Proposé |
| S-02 | Politique de mot de passe : longueur minimale, refus des mots de passe connus comme compromis. Valeurs : Q-76. | À VALIDER |
| S-03 | **Jeton d'accès** : JWT signé, durée courte (proposition : 15 minutes, Q-76), algorithme fixé côté serveur, `iss`, `aud`, `exp`, `iat`, `sub` (utilisateur), `sid` (session), `jti` vérifiés. Le jeton **ne transporte pas** les rôles ni les permissions : ils sont relus à chaque requête, pour qu'un changement de rôle ou une suspension prenne effet immédiatement. | Proposé |
| S-04 | **Jeton de rafraîchissement** : valeur aléatoire opaque d'au moins 256 bits, stockée **hachée** en base et rattachée à une session. Rotation à chaque usage. La réutilisation d'un jeton déjà consommé révoque toute la session (détection de vol). Durée : Q-76. | Proposé |
| S-05 | **Révocation** : déconnexion, changement ou réinitialisation de mot de passe, suspension du compte. La session (`sid`) est vérifiée à chaque requête, pendant la résolution de l'acteur. Un jeton d'accès d'une session révoquée est donc refusé immédiatement. | Proposé |
| S-06 | **Connexion** : message unique quel que soit le cas (BR-ACC-05) ; temps de réponse comparable (hachage effectué même si le compte n'existe pas) ; limites par adresse IP et par compte ; ralentissement progressif plutôt que blocage définitif, qui permettrait de bloquer le compte d'autrui. | Proposé |
| S-07 | **Vérification d'email et réinitialisation** : jetons à usage unique, stockés hachés, à durée courte. Réponse identique que l'adresse existe ou non. Les sessions sont révoquées après une réinitialisation (RJ 10, RJ 11). | Proposé |
| S-08 | **Premier administrateur** : commande en ligne exécutée sur le serveur, jamais une route HTTP (RJ 10). Les administrateurs suivants sont créés par un admin habilité, avec audit. | Retenu |
| S-09 | **Authentification multifacteur** pour les administrateurs, qui accèdent aux marges et aux données bancaires. Absente du CdC. | À VALIDER (Q-80) |
| S-10 | Transport des jetons pour le futur frontend web (cookie `HttpOnly`, `Secure`, `SameSite` pour le rafraîchissement, avec protection CSRF ; ou en-tête seul) : à décider avec l'architecture du frontend. L'API accepte `Authorization: Bearer`. | À VALIDER |

## 5. Autorisation

**Acteur** : pour chaque requête authentifiée, `access_control` construit un acteur à partir de la base :
- utilisateur et état de sa session ;
- organisation et son type ;
- statut du compte ;
- rôles et permissions.

Les services reçoivent cet acteur, jamais le jeton.

| ID | Proposition | Statut |
|---|---|---|
| S-11 | Permissions nommées `<ressource>:<action>` (par exemple `rfqs:submit`, `payments:confirm`, `verification:decide`, `pricing:configure`, `audit:read`). L'association rôles-permissions est une **donnée** (tables), pas du code. | Proposé |
| S-12 | Rôles actifs en V1 : Buyer, Exporter, MadaSource Admin. Les permissions admin sont **granulaires** dès la V1, même portées par un seul rôle, pour activer plus tard les rôles Operations, Compliance, Finance et Logistics sans réécriture (CdC §53). | Proposé |
| S-13 | **Refus par défaut** : toute route est privée sauf déclaration explicite comme publique. Chaque route privée déclare sa permission (`require_permission`). | Proposé |
| S-14 | **Contrôle d'objet (BOLA)** : tout accès à un objet passe par une requête filtrée par l'acteur : organisation propriétaire, ou **participation** (RFQ adressée, partie au Trade, participant à la conversation). Fonctions de repository `get_for_actor` et `list_for_actor`. Un accès non filtré n'existe que pour les traitements système et l'administration, sous un nom explicite qui le rend visible en revue. | Proposé |
| S-15 | Objet hors du périmètre de l'acteur : **404**, identique à un objet inexistant (D-25). Code 403 réservé au cas d'une action interdite sur un objet visible. | Proposé |
| S-16 | **Administration** : accès étendu mais non illimité. Permissions explicites ; chaque action admin est auditée ; aucune modification de l'historique (propositions, TradeEvent, audit), même par un admin ; consultation des données bancaires auditée. Intervention admin dans une négociation : Q-40. | Proposé |
| S-17 | Sécurité au niveau des lignes de PostgreSQL (Row-Level Security) : défense en profondeur possible, **non retenue en V1** (complexité avec un pool de connexions asynchrone). Le filtrage applicatif S-14 est obligatoire. | Proposé |

## 6. Confidentialité des données

### 6.1 Séparation des schémas

- Un objet est servi par un schéma **par audience** : public, acheteur, exportateur, admin. Ces schémas sont des classes distinctes ; un schéma public ou acheteur n'hérite jamais d'un schéma privé ([api-conventions.md](api-conventions.md#13-openapi)).
- Sortie : liste de champs autorisés (le schéma), jamais la sérialisation directe d'un modèle ORM.
- Entrée : `extra="forbid"` ; les champs fixés par le serveur ne sont jamais acceptés du client.
- Contrôles automatiques : assertion de non-exposition sur les réponses et contrôle statique de l'OpenAPI ([testing-strategy.md](testing-strategy.md#7-non-exposition-des-données-sensibles)).

### 6.2 Protection des composantes de prix (R-01)

| ID | Règle | Statut |
|---|---|---|
| S-18 | Les composantes internes (prix net, coûts externes, marge, commission) ne sont jamais sérialisées dans un schéma acheteur ou public. La marge n'est jamais sérialisée dans un schéma exportateur (BR-PRC-09). | Retenu (CdC §61, RJ 24) |
| S-19 | Règle de **non-déduction** : aucune audience ne reçoit une combinaison de valeurs qui permette de recalculer une composante cachée. Un exportateur qui connaît son prix net ne reçoit ni le prix final acheteur ni un total acheteur, faute de quoi la marge se déduit. Cette règle s'applique à la quotation, aux propositions, au Trade, aux documents commerciaux générés, aux notifications, aux agrégats et aux exports. Cas de la négociation : Q-05. | Proposé |
| S-20 | Aucun tri ni filtre sur un champ invisible pour l'audience ([api-conventions.md](api-conventions.md#6-pagination-tri-et-filtres)). | Proposé |
| S-21 | Messages d'erreur, journaux applicatifs et notifications ne contiennent aucune composante de prix. Le journal d'audit en contient (anciennes et nouvelles valeurs, CdC §52) et n'est donc lisible que par les admins habilités (`audit:read`). | Proposé |

### 6.3 Données bancaires et fiscales

| ID | Règle | Statut |
|---|---|---|
| S-22 | Informations bancaires de l'exportateur **chiffrées au niveau applicatif** avant stockage, par une bibliothèque cryptographique maintenue. Clé hors de la base (variable d'environnement ou gestionnaire de secrets). Accès réservé à l'organisation propriétaire et aux admins habilités, consultation auditée, affichage masqué par défaut. | Proposé (Q-81) |
| S-23 | Coordonnées bancaires à présenter à l'acheteur pour un virement (MadaSource ou exportateur) : décision commerciale et juridique. | À VALIDER (Q-55) |

### 6.4 Documents (Jour 29)

| ID | Règle | Statut |
|---|---|---|
| S-24 | Chaque document porte une **visibilité explicite**, en plus de son contexte : organisation propriétaire seule, partie acheteuse, partie exportatrice, MadaSource uniquement. La participation au contexte (P-01) **ne suffit pas**. Exemple : une facture de l'exportateur à MadaSource en Modèle A révèle le prix net et ne doit pas être visible par l'acheteur. | Proposé |
| S-25 | Formats admis PDF, JPG, PNG, DOCX (CdC §26), vérifiés sur le **contenu réel** (signature de fichier), pas seulement sur l'extension ou le type déclaré. Refus des formats à macros et des archives. Taille maximale et analyse antivirus : Q-48. | Proposé |
| S-26 | Nom d'origine conservé comme simple métadonnée nettoyée, jamais utilisé comme chemin. Clé de stockage aléatoire. Stockage privé. Téléchargement après autorisation serveur, par URL signée de courte durée (proposition : 5 minutes) ou par flux, avec `Content-Disposition: attachment` et `X-Content-Type-Options: nosniff`. | Proposé |
| S-27 | Suppression des métadonnées des images (EXIF, dont la géolocalisation) au dépôt. | Proposé |

### 6.5 Messagerie

- Seuls les participants d'une conversation la lisent et y écrivent (BR-MSG-01). L'accès admin est en attente de décision (Q-50).
- Le contenu tapé par les utilisateurs (prix, coordonnées) ne peut pas être contrôlé techniquement sans filtrage. Politique d'échange de coordonnées : Q-51.

## 7. Intégrité des transactions

- Transitions d'état uniquement par les services, sous verrou, avec revérification de l'état (D-09, BR-TRD-06).
- Actions critiques idempotentes, contraintes d'unicité en dernier rempart (D-09).
- Historique immuable par les opérations normales : propositions, TradeEvent, audit (BR-NEG-02, BR-TRD-07, BR-AUD-02).
- Le dépôt d'un justificatif ne confirme jamais un paiement (BR-PAY-03).

## 8. Validation des entrées et injections

| Règle | Statut |
|---|---|
| Schémas Pydantic typés et bornés (longueurs, valeurs positives, énumérations) ; montants et quantités en chaînes décimales ([api-conventions.md](api-conventions.md#7-dates-montants-quantités)). | Proposé |
| SQL uniquement par requêtes paramétrées (SQLAlchemy). Colonnes de tri choisies dans une liste blanche, jamais interpolées. | Proposé |
| Texte libre (descriptions, messages) stocké en texte brut, sans HTML. L'échappement à l'affichage revient au frontend, contre le XSS stocké. | Proposé |
| `X-Request-ID` reçu : format et longueur validés avant journalisation (injection dans les journaux). | Proposé |
| Aucune requête sortante vers une URL fournie par un utilisateur (SSRF). Le QR code du Passport est produit côté serveur, à partir de l'URL publique connue. | Proposé |

## 9. Limites de débit et consommation de ressources

| Règle | Statut |
|---|---|
| Limites sur : connexion, rafraîchissement, inscription, réinitialisation, renvoi de vérification d'email, création de RFQ, dépôt de documents, recherche publique (CdC §60). | Proposé |
| Clés de limitation : adresse IP et compte pour la connexion ; utilisateur pour les endpoints authentifiés. | Proposé |
| Emplacement : reverse proxy (limites grossières) et application (limites fines). Avec plusieurs instances, un stockage partagé (Redis) est nécessaire et doit être justifié au Jour 8. | À VALIDER (Jour 8) |
| Pagination bornée, taille maximale des requêtes, délai d'exécution maximal des requêtes SQL, réponse 429 avec `Retry-After`. | Proposé |

## 10. Transport, en-têtes et configuration

| Règle | Statut |
|---|---|
| HTTPS obligatoire en production (terminaison au reverse proxy), HSTS. | Proposé |
| CORS : liste blanche des origines du frontend, jamais `*` en production (D-11). | Proposé |
| En-têtes : `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` sur toute réponse privée. Aucune bannière de version serveur. | Proposé |
| Documentation interactive et schéma OpenAPI **désactivés en production publique** ; disponibles en local, en test et en staging. | Proposé |
| Démarrage refusé en production en cas de configuration dangereuse (D-11). | Proposé |

## 11. Secrets

| Règle | Statut |
|---|---|
| Secrets uniquement dans les variables d'environnement ou le gestionnaire de secrets de l'hébergeur (Q-79). Jamais dans Git, une image Docker, un journal ou la configuration CI en clair. | Retenu (RJ section 1) |
| `.env` en local seulement. **Aucun `.gitignore` aujourd'hui** (R-20) : il est à créer au Jour 4, avant tout `.env`. | Retenu |
| Procédure de rotation documentée (Audit D). Une rotation de la clé de signature invalide les jetons en cours (acceptable). La rotation de la clé de chiffrement bancaire impose un rechiffrement (Q-81). | Proposé |
| Détection de secrets : hook local (`guard_files.py`) et analyse en CI (outil à justifier au Jour 7). | Proposé |

## 12. Journalisation et audit

| Règle | Statut |
|---|---|
| Journaux applicatifs nettoyés (D-12), avec identifiants plutôt que noms ou emails. | Proposé |
| Audit des actions sensibles : connexion et échec répété, changement ou réinitialisation de mot de passe, changement de rôle ou de statut, décision de vérification, consultation des données bancaires, téléchargement de document sensible, action admin, accès refusé à un objet d'une autre organisation. Chaque événement enregistre : acteur, organisation, action, objet, horodatage, résultat, anciennes et nouvelles valeurs filtrées (RJ 12, CdC §52). | Proposé |
| Ajout seul : aucun endpoint ne modifie ni ne supprime un événement. Défense en profondeur proposée : le rôle de base de données de l'application n'a pas les droits `UPDATE` et `DELETE` sur la table d'audit (Jour 12). | Proposé |
| Données personnelles dans l'audit réduites aux identifiants (pseudonymisation), pour concilier immuabilité et droit à l'effacement (Q-68). | Proposé |

## 13. Base de données

| Règle | Statut |
|---|---|
| Deux rôles PostgreSQL : un pour les migrations (DDL), un pour l'application (DML sans DDL). | Proposé (Jours 4, 6) |
| Base jamais exposée publiquement ; connexion chiffrée en production. | Proposé |
| Sauvegardes chiffrées et restauration testée (Audit D). | Proposé |
| Aucun outil ni agent connecté à une base de production (règle de préparation). | Retenu |

## 14. Mode DEMO

Instance distincte, avec sa propre base et son propre stockage, sans connexion aux intégrations réelles. En-tête `X-MadaSource-Mode: demo`. Démarrage refusé en production avec `DEMO_MODE` (D-18, BR-DEMO-02).

## 15. Dépendances

- Versions épinglées et fichier de verrouillage (Jour 4).
- Analyse des vulnérabilités connues en CI (outil à justifier au Jour 7).
- Images Docker de base épinglées, exécution sans root (agent `devops-engineer`).
- Aucun ajout de skill, plugin ou serveur MCP externe sans accord.

## 16. Tests de sécurité

- Matrice obligatoire par endpoint privé et contrôles de non-exposition ([testing-strategy.md](testing-strategy.md#6-tests-obligatoires)).
- Authentification : jeton expiré, révoqué, falsifié, d'une session révoquée ; rafraîchissement rejoué (détection de vol) ; réponses de connexion indiscernables.
- Fichiers : type réel différent de l'extension, taille excessive, nom de fichier hostile.
- Audit B : accès horizontaux, élévation de privilèges, fuites, concurrence de l'acceptation.

## 17. Registre des décisions de sécurité

Les décisions S-01 à S-27 figurent dans les tableaux ci-dessus, avec leur statut. Synthèse des points à valider :

| Sujet | Question |
|---|---|
| Durées des jetons, politique de mot de passe, verrouillage | Q-76 |
| Authentification multifacteur des administrateurs | Q-80 |
| Chiffrement des données bancaires et gestion des clés | Q-81 |
| Hébergement, gestionnaire de secrets, localisation des données | Q-79 |
| Taille maximale et antivirus des fichiers | Q-48 |
| Lecture des conversations par l'admin ; échange de coordonnées | Q-50, Q-51 |
| Négociation en Modèle A (non-déduction de la marge) | Q-05 |
| Coordonnées bancaires présentées à l'acheteur | Q-55 |
| Données personnelles et conservation | Q-68, Q-69 |

## 18. Relecture de sécurité du Jour 2

_À compléter avec les constats de l'agent `security-auditor` sur la matrice de visibilité du Jour 1._
