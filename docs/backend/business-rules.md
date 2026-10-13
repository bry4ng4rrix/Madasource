# Règles métier — backend MadaSource

Jour 1 · 2026-10-12 · Statut : brouillon à valider par le client · **Mis à jour au Jour 2** : règles ajoutées après la relecture de sécurité, marquées « (J2) », toutes au statut Proposé ou À VALIDER

Les règles ci-dessous sont des **invariants** que le backend doit garantir côté serveur, quel que soit le client.
- **Défini** : écrit dans une source.
- **Déduit** : tiré d'un exemple ou d'un croisement de sources ; à confirmer.
- **À VALIDER** : à décider par le client (questions Q-NN dans [risks-and-open-questions.md](risks-and-open-questions.md)).
- **Proposé** (règles ajoutées au Jour 2, marquées « (J2) ») : proposition de l'équipe, absente des sources. Comme toute décision `À VALIDER`, elle est soumise au client et ne s'implémente pas comme définitive sans validation. Quand une question Q-NN est citée, la proposition attend sa réponse.

Les exemples chiffrés du CdC (USD 40/kg, marge de USD 3,30, validité de 7 jours…) sont **illustratifs** : aucun n'est une valeur par défaut à coder.

## 1. Organisation et accès

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-ORG-01 | Toute ressource métier privée appartient à une organisation ou est partagée entre des organisations parties prenantes identifiées. | CdC §54, RJ 9 | Déduit |
| BR-ORG-02 | Un utilisateur n'accède qu'aux ressources de son organisation ou à celles dont elle est partie prenante. | CdC §54, RJ 9 | Défini |
| BR-ORG-03 | Les permissions sont fondées sur les rôles. Aucune décision d'accès ne repose sur un indicateur isolé du type « est admin » dispersé dans le code. | CdC §53, RJ 9 | Défini |
| BR-ORG-04 | Les rôles futurs restent inactifs sans décision explicite de MadaSource. | CdC §53 | Défini |
| BR-ORG-05 | (J2) L'organisation acheteuse et l'organisation exportatrice d'une RFQ, d'une quotation ou d'un Trade sont toujours différentes. | S-36 | Proposé |

## 2. Comptes

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-ACC-01 | Statuts d'un compte acheteur : Pending, Active, Suspended, Blocked. Aucune autre valeur. | CdC §10 | Défini |
| BR-ACC-02 | L'admin peut approuver et suspendre un compte acheteur et gérer son statut. | CdC §35 | Défini |
| BR-ACC-03 | Droits d'un compte Pending ; différence entre Suspended et Blocked ; réactivation. | — | À VALIDER (Q-11) |
| BR-ACC-04 | Statuts du compte exportateur, distincts des statuts de vérification. | — | À VALIDER (Q-12) |
| BR-ACC-05 | Les erreurs de connexion ne révèlent pas l'existence d'un compte. Les tokens ne sont jamais journalisés. | RJ 10 | Défini |
| BR-ACC-06 | Le jeton de vérification d'email est à usage unique, expire, et ne peut être réutilisé. | RJ 11 | Défini |
| BR-ACC-07 | (J2) Inscription, réinitialisation et renvoi de vérification répondent de la même façon, que l'adresse soit connue ou non. | S-56 | Proposé |

## 3. Vérification des exportateurs

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-VER-01 | Niveaux ordonnés : 1 Profile Verified < 2 Business Verified < 3 Export Verified < 4 MadaSource Premium Verified. Le niveau 3 inclut le niveau 2 (« Business verified + export capability »). | CdC §8 | Défini (inclusion des niveaux 1 → 2 : déduit) |
| BR-VER-02 | Chaque décision conserve : niveau, date, expiration le cas échéant, documents examinés, administrateur responsable, notes, statut. | CdC §8 | Défini |
| BR-VER-03 | Une inscription ne rend jamais un exportateur vérifié. Seul un utilisateur autorisé décide. | RJ 15 | Défini |
| BR-VER-04 | Une vérification dont la date d'expiration est dépassée passe en Expired et n'est plus présentée comme valide. | CdC §8 (statut Expired) | Déduit (détection automatique : Q-15) |
| BR-VER-05 | Les badges et le Digital Passport n'affichent que des vérifications réellement prononcées. Aucune certification ni vérification n'est supposée. | CdC §46 (énoncé pour l'IA), RJ 22 (énoncé pour le matching) | Déduit |
| BR-VER-06 | Critères et documents par niveau, durée de validité, niveau minimal pour le Passport, le marketplace et la réception de RFQ. | Planning §13 | À VALIDER (Q-15, Q-16) |
| BR-VER-07 | (J2) La modification d'un champ couvert par une vérification (raison sociale, immatriculation…) est interdite, ou renvoie la vérification en revue avec badge suspendu. Un slug de Passport n'est jamais réattribué. | S-53, S-54 | À VALIDER (Q-90) |

## 4. Produits et marketplace

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-PRD-01 | Un produit appartient à une catégorie active. Vanilla, Cloves et Cocoa sont contrôlées par leur feature flag. | CdC §5, §71 | Défini |
| BR-PRD-02 | Les attributs qualité dépendent de la catégorie. Aucun attribut n'est obligatoire pour toutes les catégories. | CdC §6, RJ 16 | Défini (liste : Q-18) |
| BR-PRD-03 | Quantités et MOQ ont une unité explicite. Montants en Decimal avec devise. | RJ 16 | Défini (unités admises : Q-21) |
| BR-PRD-04 | Un exportateur ne gère que les produits de son organisation. | RJ 17 | Défini |
| BR-PRD-05 | Un produit lié à une RFQ ou à un Trade n'est jamais supprimé physiquement : archivage logique. | RJ 17 | Défini |
| BR-PRD-06 | Seuls les produits publiés d'organisations autorisées apparaissent dans le marketplace public. | RJ 17-18 | Déduit (conditions de vérification : Q-16) |
| BR-PRD-07 | L'« indication de prix » est une indication, pas une offre engageante. Sa nature (prix net ou prix commercial) et sa visibilité restent à définir. | CdC §5-6 | À VALIDER (Q-06) |
| BR-MKT-01 | Les filtres du marketplace n'utilisent que des données réellement saisies. Un produit sans valeur pour un critère n'est pas réputé y satisfaire. | RJ 18, CdC §46 | Défini (1re phrase, RJ 18) / Déduit (2e phrase) |

## 5. RFQ

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-RFQ-01 | Toute RFQ suit la machine d'état de [workflows.md §4](workflows.md#4-rfq). Une transition non prévue est refusée par le service. | CdC §12, RJ 19 | Défini |
| BR-RFQ-02 | Seule l'organisation acheteuse propriétaire crée, modifie (en Draft) et soumet sa RFQ. | RJ 20 | Défini |
| BR-RFQ-03 | Une RFQ soumise n'est pas modifiable librement lorsque cela invaliderait des matches ou des quotations. | RJ 20 | Défini (règle précise : Q-23) |
| BR-RFQ-04 | Un exportateur ne voit et ne traite que les RFQ qui lui ont été adressées ou auxquelles il est autorisé à répondre. | RJ 21 | Défini |
| BR-RFQ-05 | Les réponses, refus et questions des exportateurs sont conservés. | RJ 21 | Défini |
| BR-RFQ-06 | La quantité est stockée avec son unité d'origine. Toute normalisation (ex. 20 tonnes = 20 000 kg) est explicite et réversible. | CdC §13 (exemple) | Déduit (Q-21) |
| BR-RFQ-07 | Le prix cible est facultatif, exprimé en Decimal avec devise. | CdC §12, RJ 19 | Défini (caractère facultatif : RJ 19) |
| BR-RFQ-08 | (J2) L'accès d'un exportateur à une RFQ passe uniquement par un destinataire matérialisé et actif. Un destinataire retiré ou suspendu perd l'accès ; un destinataire qui a décliné ne voit que ses propres contributions. | S-30 | Proposé |
| BR-RFQ-09 | (J2) Dans une RFQ adressée à plusieurs exportateurs, chaque question, réponse, document et conversation est rattaché à la paire (RFQ, exportateur). Une diffusion à tous les destinataires n'a lieu que sur action explicite de l'acheteur. L'exportateur destinataire reçoit une projection fermée de la RFQ. | S-31, S-50 | À VALIDER (Q-84, Q-85) |

## 6. Matching

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-MAT-01 | Le score est calculé à partir des données réelles de la plateforme et de pondérations configurables. Aucun score aléatoire ou arbitraire. | CdC §14 | Défini |
| BR-MAT-02 | Même entrée (RFQ, données des exportateurs, pondérations) = même résultat. Le résultat conserve les critères, la version des pondérations, les raisons et la date d'exécution. | RJ 22-23 | Défini |
| BR-MAT-03 | Une donnée absente n'est jamais supposée satisfaite. Son traitement (critère neutre, pénalisé, éliminatoire) est explicite et documenté. | RJ 22 | Défini (choix par critère : Q-30, Q-32) |
| BR-MAT-04 | Aucun fournisseur inventé : seuls des exportateurs existants et autorisés peuvent être proposés. | CdC §46, RJ 22 | Défini |
| BR-MAT-05 | Relancer le matching sur une RFQ ne crée pas de doublons incohérents (idempotence). | RJ 23 | Défini |
| BR-MAT-06 | Une IA future ne contourne jamais les règles déterministes sans autorisation. | CdC §47 | Défini (hors V1) |

## 7. Quotations et validité

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-QUO-01 | Une quotation est émise par un exportateur destinataire de la RFQ. | CdC §15-16 | Déduit |
| BR-QUO-02 | Chaque quotation conserve : date de création, dernière mise à jour, date d'expiration, source, statut, devise, unité, destination, Incoterm. | CdC §18, RJ 25 | Défini |
| BR-QUO-03 | Statut de validité : Active, Expiring, Expired. Proposition : le déterminer par la date d'expiration comparée à l'instant présent (UTC), plutôt que par une valeur stockée qui pourrait devenir fausse. | CdC §18 | Défini (statuts) / Proposé (mode de calcul, à confirmer aux Jours 2-3) ; seuil Expiring : Q-35 |
| BR-QUO-04 | Une quotation expirée n'est jamais présentée comme une offre actuelle. | CdC §18 | Défini |
| BR-QUO-05 | Une quotation expirée ne peut pas être acceptée, sauf règle explicite et action auditée. | RJ 25 | Défini (règle : Q-36) |
| BR-QUO-06 | Cycle de vie de la quotation (brouillon, soumise, retirée, acceptée, refusée…). | — | À VALIDER (Q-34) |
| BR-QUO-07 | Les Incoterms admis en V1 sont FOB, CFR et CIF. La liste est extensible sans modification de structure. | CdC §32 | Défini |
| BR-QUO-08 | (J2) Le prix présenté à l'acheteur est stocké avec la version des règles de prix. Toute modification d'une offre crée une nouvelle version. L'acceptation porte sur la version vue ; en cas d'écart, elle est refusée. | S-43 | Proposé (effet d'un changement de règle : Q-91) |

## 8. Prix et modèles commerciaux

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-PRC-01 | Le système distingue Supplier Cost, External Costs, MadaSource Margin et Final Buyer Price, et stocke chaque composante séparément. En Modèle A, l'exemple du CdC §17 les additionne : Supplier Cost + External Costs + Margin = Final Buyer Price. En Modèle B, la commission n'est pas forcément ajoutée au prix acheteur (Q-03). | CdC §32, §17 | Défini (distinction, §32) / Déduit (formule additive, exemple du §17) |
| BR-PRC-02 | Les règles de calcul (marge, commission, coûts appliqués) sont configurables par l'admin. Aucune valeur n'est codée en dur. | CdC §17, RJ 24 | Défini (formules : Q-02, Q-03) |
| BR-PRC-03 | Modèle A : l'exportateur fournit un prix net contractuel, MadaSource ajoute sa marge, l'acheteur voit le prix commercial. Le système conserve prix net, marge et prix final. | CdC §2 | Défini |
| BR-PRC-04 | Modèle B : MadaSource perçoit une commission ou des frais de service définis contractuellement. | CdC §2 | Défini (base de calcul et payeur : Q-03) |
| BR-PRC-05 | Le choix et l'articulation des modèles A et B (global, par exportateur, par transaction) restent à définir. | CdC §2, §75 | À VALIDER (Q-01) |
| BR-PRC-06 | CIF : prix produit + fret + assurance = base CIF, puis application des règles commerciales du modèle retenu. CFR : prix produit + fret (déduit de la définition Incoterms). | CdC §32 | Défini (CIF) / Déduit (CFR) |
| BR-PRC-07 | Tout coût externe conserve : source, fournisseur, date, validité, devise, unité, destination, Incoterm, statut de confirmation. | CdC §33 | Défini |
| BR-PRC-08 | Un coût externe expiré n'est jamais utilisé silencieusement. Le calcul est bloqué, ou le prix est explicitement signalé comme fondé sur une donnée périmée. | CdC §33 | Défini (comportement exact : Q-04) |
| BR-PRC-09 | Le prix net fournisseur, les coûts internes et la marge ne sont jamais exposés à l'acheteur. La marge n'est jamais exposée à l'exportateur. | CdC §61, RJ 24 | Défini |
| BR-PRC-10 | Montants en Decimal/NUMERIC, jamais en float. Règles d'arrondi explicites. | RJ section 1 | Défini (précision : Q-08) |
| BR-PRC-11 | (J2) **Non-déduction** : aucune audience ne reçoit une combinaison de valeurs permettant de recalculer une composante cachée. Exemple : l'exportateur, qui connaît son prix net, ne reçoit pas le prix final acheteur. Cela vaut aussi pour les totaux, paiements, remboursements, échantillons et tableaux de bord. Un champ public est visible de tous les exportateurs. | S-19 | Proposé (Q-05) |
| BR-PRC-12 | (J2) La commission du Modèle B est visible de son seul payeur et distincte de la marge. Aucune décision automatique ne repose sur une valeur cachée à la contrepartie (par exemple un prix plancher). Les messages d'erreur ne contiennent ni montant ni seuil. | S-41, S-42 | Proposé (Q-03) |

## 9. Négociation

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-NEG-01 | Chaque proposition (offre initiale, contre-offre, acceptation, refus) est un événement horodaté avec son auteur, ses valeurs commerciales et son statut. | CdC §20-21, RJ 26 | Défini |
| BR-NEG-02 | Aucune proposition n'est modifiée ni supprimée par le workflow normal : une correction est une nouvelle proposition. | CdC §20, RJ 26 | Défini |
| BR-NEG-03 | Une partie accepte la dernière proposition **de l'autre partie** : l'acheteur accepte une offre de l'exportateur, l'exportateur une contre-offre de l'acheteur. | CdC §20 (« Buyer: ACCEPT »), §67 étape 10 (« Exporter accepts ») | Déduit |
| BR-NEG-04 | Au plus une acceptation aboutit pour une même négociation. Des requêtes simultanées ne peuvent pas accepter deux propositions incompatibles. | RJ 26 | Défini |
| BR-NEG-05 | Les termes finaux acceptés sont conservés tels quels dans l'historique. | CdC §21 | Défini |
| BR-NEG-06 | Correspondance entre le prix vu par l'acheteur et le prix net de l'exportateur en Modèle A. | — | À VALIDER (Q-05), **bloquant pour le Jour 26** |
| BR-NEG-07 | Champs négociables, nombre de tours, validité d'une contre-offre, effet d'un refus. | — | À VALIDER (Q-38, Q-39) |

## 10. Trade

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-TRD-01 | L'acceptation valide d'une quotation ou d'une contre-offre crée automatiquement un seul Trade. | CdC §22, RJ 27 | Défini |
| BR-TRD-02 | Création atomique : Trade, figement des termes, événement initial et changement de statut de la RFQ réussissent ou échouent ensemble. | RJ 27 | Défini (atomicité de la création, RJ 27) / Déduit (statut de la RFQ inclus) |
| BR-TRD-03 | Idempotence : un double appel ou des requêtes simultanées ne créent jamais deux Trades pour la même acceptation. | RJ 27 | Défini |
| BR-TRD-04 | Le Trade ID est unique, stable (jamais réattribué ni modifié), lisible, généré par le serveur. | CdC §22, RJ 27 | Défini (format : Q-37) |
| BR-TRD-05 | Les termes commerciaux acceptés (prix, devise, quantité, qualité, Incoterm, destination, conditions de paiement, livraison cible) sont copiés dans le Trade et ne changent plus, ni avec la quotation, ni avec un taux de change. (J2) En Modèle A, deux jeux de termes sont figés : termes acheteur (prix final) et termes fournisseur (prix net). Chaque partie ne reçoit que les siens. | RJ 27, CdC §59 ; S-39 | Défini / Proposé (deux jeux de termes, Q-82) |
| BR-TRD-06 | Le statut du Trade suit la machine d'état de [workflows.md §8](workflows.md#8-trade). Toute transition est validée par un service métier et produit un TradeEvent. | CdC §24, RJ 28 | Défini |
| BR-TRD-07 | Un TradeEvent conserve : horodatage UTC, acteur, action, ancien et nouveau statut, commentaire, document justificatif le cas échéant, métadonnées non sensibles. Il est immuable. | CdC §25, RJ 28 | Défini |
| BR-TRD-08 | Les objets rattachés au Trade (documents, messages, paiements, expéditions) référencent son Trade ID. | CdC §66 | Défini |
| BR-TRD-09 | Acteurs autorisés par transition, conditions de Completed, annulation, mise en attente. | — | À VALIDER (Q-41 à Q-45) |

## 11. Documents

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-DOC-01 | Formats acceptés : PDF, JPG, PNG, DOCX. Le type est vérifié sur le contenu, pas seulement sur l'extension ou le nom. | CdC §26, RJ 29 | Défini |
| BR-DOC-02 | Un document appartient à une organisation, a une catégorie parmi les sept du CdC, et peut être rattaché à une société, une RFQ, une quotation, un Trade ou une expédition. | CdC §26 | Défini |
| BR-DOC-03 | Un document sensible n'est jamais accessible publiquement. Le téléchargement privé exige une autorisation serveur ou une URL signée à durée limitée. | CdC §11, §60, RJ 29 | Défini |
| BR-DOC-04 | Un nouveau dépôt du même document crée une nouvelle version. Les versions précédentes sont conservées. | CdC §26 (« version ») | Déduit |
| BR-DOC-05 | Statuts de document, documents obligatoires par étape, taille maximale, analyse antivirus, conservation. | — | À VALIDER (Q-47, Q-48) |
| BR-DOC-06 | (J2) Chaque document et chaque version porte une audience explicite. Par défaut, c'est la plus restrictive : organisation déposante et MadaSource. La participation au contexte ne suffit pas pour y accéder. Les documents de société, de paiement, fiscaux, bancaires et d'onboarding ne sont jamais publics. Le retrait d'un partage est audité, sans suppression. | S-24 | Proposé (gouvernance : Q-83) |

## 12. Messagerie et notifications

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-MSG-01 | Seuls les participants autorisés d'une conversation la lisent et y écrivent. | CdC §28, RJ 30 | Défini |
| BR-MSG-02 | L'historique des conversations est préservé. Un message n'est pas supprimé par le workflow normal. | CdC §28 | Défini (édition et suppression par l'auteur : Q-50) |
| BR-MSG-03 | Les pièces jointes passent par le coffre documentaire et ses contrôles. | RJ 30 | Défini |
| BR-MSG-04 | (J2) Une conversation a une liste explicite de participants ; l'accès suit l'évolution de la participation. Tout texte libre (commentaire, note, motif) porte une audience ; pour un texte saisi par un admin, elle est « interne » par défaut. | S-46, S-47 | Proposé |
| BR-NOT-01 | Une notification est générée pour chaque événement listé au CdC §29. | CdC §29 | Défini (destinataires : Q-52) |
| BR-NOT-02 | Le système n'affirme jamais qu'un email ou un push a été envoyé sans confirmation du fournisseur. | RJ 11, RJ 31 | Défini |
| BR-NOT-03 | (J2) Une notification ne stocke que son code de type, la référence de l'objet et son destinataire, sans montant ni URL signée. Le détail est lu par l'endpoint du module propriétaire de l'objet, avec les droits courants du lecteur. | S-52 | Proposé |

## 13. Paiements

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-PAY-01 | Un Payment Record **enregistre** un paiement : aucun flux financier n'est exécuté par la plateforme. | CdC §30, Planning §7 | Défini |
| BR-PAY-02 | Statuts : Pending, Processing, Confirmed, Failed, Refunded. | CdC §30 | Défini (transitions : workflows.md §10) |
| BR-PAY-03 | Le dépôt d'un justificatif ne confirme pas le paiement. Seule une action admin autorisée et auditée le confirme. | CdC §30, RJ 33 | Défini |
| BR-PAY-04 | Montant en Decimal avec devise, rattaché à un Trade. | CdC §30, RJ 33 | Défini |
| BR-PAY-05 | Bénéficiaire, auteur de la saisie, paiements partiels ou multiples, coordonnées bancaires présentées à l'acheteur. | — | À VALIDER (Q-54, Q-55) |
| BR-PAY-06 | Un remboursement est enregistré et audité, sans flux réel. | CdC §30 | Défini (autorisation : Q-56) |
| BR-PAY-07 | (J2) **Séparation des tâches** : l'admin qui a saisi un Payment Record ou l'a passé en Processing ne peut pas le confirmer. Même règle pour un remboursement. | S-34 | Proposé (Q-56 ; seuil de double validation : Q-88) |
| BR-PAY-08 | (J2) Un Payment Record est orienté (payeur, bénéficiaire). En Modèle A : acheteur → MadaSource et MadaSource → exportateur ; en Modèle B : acheteur → exportateur. Chaque justificatif hérite de l'audience de son paiement. | S-40 | Proposé (Q-54, Q-82) |
| BR-PAY-09 | (J2) Toute modification de coordonnées bancaires (exportateur ou MadaSource) exige une permission dédiée, une ré-authentification, une notification et une re-vérification avant prise d'effet. | S-44 | Proposé (Q-87) |

## 14. Expéditions

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-SHP-01 | Les informations d'expédition sont saisies manuellement en V1. Aucun suivi automatique n'est inventé. | CdC §31, RJ 34 | Défini |
| BR-SHP-02 | Statuts : Pending, Ready for Shipment, Shipped, In Transit, Arrived, Delivered. Chaque changement est historisé. | CdC §31, RJ 34 | Défini |
| BR-SHP-03 | Correspondance entre les statuts d'expédition et ceux du Trade ; plusieurs expéditions par Trade. | — | À VALIDER (Q-57, Q-58) |

## 15. Réputation et performance

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-REP-01 | Une évaluation n'est possible qu'après un Trade Completed, par une partie de ce Trade, envers l'autre partie. | CdC §42 | Défini |
| BR-REP-02 | Une seule évaluation par sens et par Trade. | — | Déduit (Q-59) |
| BR-REP-03 | Aucune évaluation, note ou statistique artificielle. | CdC §42 | Défini |
| BR-REP-04 | « NEW ON MADASOURCE » s'affiche tant que l'historique de transactions est insuffisant. | CdC §42 | Défini (seuil : Q-59) |
| BR-REP-05 | Les indicateurs de performance sont calculés uniquement à partir de données réelles de la plateforme. | CdC §43-44 | Défini |
| BR-REP-06 | (J2) Un indicateur n'est affiché publiquement qu'au-delà d'un seuil d'activité : sur un seul Trade, « 100 % de litiges » révèle un fait privé. Les RFQ jugées abusives sont exclues du calcul. | S-51, S-55 | À VALIDER (Q-86) |

## 16. Exceptions et litiges

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-EXC-01 | Une exception peut être rattachée à un Trade. Elle est assignable, commentée, priorisée, résolue, escaladée, et chaque action est auditée. | CdC §40, RFS J 39 | Défini (statuts : Q-60) |
| BR-EXC-02 | Un litige est ouvert par l'acheteur ou l'exportateur du Trade, avec motif, description, preuves, documents et résolution demandée. | CdC §41 | Défini |
| BR-EXC-03 | Statuts d'un litige : Open, Under Review, Resolution Proposed, Resolved, Closed. | CdC §41 | Défini |
| BR-EXC-04 | Effet d'un litige sur le statut du Trade (Disputed) et sur les paiements. | CdC §24, §41 | À VALIDER (Q-61) |

## 17. Audit

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-AUD-01 | Toute action importante produit un événement d'audit : acteur, action, objet, horodatage, ancienne et nouvelle valeur le cas échéant. | CdC §52 | Défini |
| BR-AUD-02 | Le journal d'audit est en ajout seul : aucun endpoint ne le modifie ni ne le supprime. | RJ 12 | Défini |
| BR-AUD-03 | L'audit ne contient jamais mot de passe, token, données bancaires complètes ni contenu de document privé. | RJ 12 | Défini |
| BR-AUD-04 | Actions sensibles minimales : comptes, rôles, vérifications, produits, RFQ, offres, négociations, trades, documents, paiements, expéditions, administration. | RJ 12, CdC §52 | Défini |
| BR-AUD-05 | (J2) Sont aussi audités :<br>- les consultations sensibles : données bancaires, documents privés, conversations, journal d'audit, exports ;<br>- les événements de sécurité : échecs de connexion, refus d'accès inter-organisations.<br>Les valeurs enregistrées suivent la classification des champs : en clair, masquées, ou réservées à la lecture financière. | S-16, security-design.md §18 | Proposé |

## 18. Identifiants lisibles

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-REF-01 | RFQ, Quotation et Trade portent un identifiant lisible préfixé (`RFQ-`, `MSQ-`, `MST-`), suivi de l'année et d'un suffixe. Le CdC ne donne que des exemples d'apparence séquentielle (`RFQ-2026-0012`, `MST-2026-000145`), sans exiger de séquence (correction du Jour 3). | CdC §16, §22, §66 | Défini (préfixe, année) |
| BR-REF-02 | L'identifiant est généré par le serveur, unique, jamais réutilisé, sûr en cas de concurrence, et jamais codé en dur (y compris l'exemple `MST-2026-000145`). | RJ 27 | Défini |
| BR-REF-03 | Nombre de chiffres, remise à zéro annuelle, année de référence (création, UTC). Réponse du 2026-10-13 : suffixe aléatoire de 6 caractères, sans remise à zéro (`RFQ-2026-K7M4Q9`). | CdC §16 vs §66 | PROPOSED (Q-37, CF-04) |

## 19. Devises, temps et langues

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-CUR-01 | Devises V1 : USD et EUR. D'autres devises sont prévues sans changement de structure. | CdC §59 | Défini |
| BR-CUR-02 | Les taux de change sont stockés séparément des données transactionnelles. Un montant historique ne change jamais à cause d'un taux. | CdC §59 | Défini |
| BR-CUR-03 | Conversion en V1, source des taux, comparaison de montants en devises différentes. | — | À VALIDER (Q-65) |
| BR-TIM-01 | Toutes les dates sont stockées en UTC, timezone-aware. | RJ section 1 | Défini |
| BR-TIM-02 | Interprétation des délais exprimés en jours (validité « 7 jours ») : instant exact ou fin de journée, dans quel fuseau. | — | À VALIDER (Q-70) |
| BR-I18N-01 | Statuts, catégories et codes d'erreur sont des codes stables, indépendants de la langue. Leur libellé est traduit en anglais et en français. | CdC §58 | Déduit (où se fait la traduction : Q-66) |

## 20. Mode DEMO, feature flags, intégrations

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-DEMO-01 | Le mode DEMO est clairement identifié. Il peut simuler la confirmation de paiement, le statut d'expédition, la livraison et la confirmation partenaire. | CdC §68 | Défini |
| BR-DEMO-02 | Une transaction simulée n'est jamais présentée comme réelle. Données simulées et réelles ne se mélangent jamais. | CdC §68, RFS section 1 | Défini (mécanisme : Q-67) |
| BR-DEMO-03 | En mode DEMO, le workflow et le modèle de données sont identiques au fonctionnement réel. | CdC §68 | Défini |
| BR-FLG-01 | Un module ou une catégorie dont le flag est désactivé n'est ni exposé ni simulé. | CdC §71, RFS J 40 | Défini |
| BR-INT-01 | Toute intégration externe passe par une couche d'intégration dédiée. Aucune n'est active en V1 sans autorisation explicite. | CdC §57, RFS section 1 | Défini |
| BR-LEG-01 | Le logiciel ne présuppose pas que MadaSource exerce des activités réglementées. Ces fonctions passent par des tiers agréés. | CdC §75 | Défini |

## 21. Sûreté des données présentées

| ID | Règle | Source | Statut |
|---|---|---|---|
| BR-SAFE-01 | Le système n'invente jamais fournisseur, prix, capacité, certification, document, statut logistique, paiement ou transaction. | CdC §46 (énoncé pour l'IA), RJ 22 | Déduit : extension à tout le système |
| BR-SAFE-02 | Une donnée indisponible est signalée explicitement comme indisponible, et non remplacée par une valeur par défaut. Le CdC utilise pour l'IA la formule « INFORMATION NOT AVAILABLE » ; sa forme dans l'API est à fixer au Jour 2. | CdC §46 | Déduit |
| BR-SAFE-03 | La provenance d'une donnée est distinguable : donnée vérifiée, donnée plateforme, donnée estimée, saisie utilisateur, recommandation. | CdC §46 | Déduit (énoncé pour l'IA ; applicable aux coûts estimés : Q-04) |
