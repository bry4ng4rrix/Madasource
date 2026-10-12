# Acteurs et permissions — backend MadaSource

Jour 1 · 2026-10-12 · Statut : brouillon à valider par le client

Ce document décrit **qui peut faire quoi et voir quoi**, au niveau fonctionnel. Le mécanisme technique (tokens, dépendances, vérifications) relève des Jours 2, 8, 9 et 10.

## 1. Acteurs

| Acteur | Description | Source | V1 |
|---|---|---|---|
| Visiteur anonyme | Consulte le site public, le marketplace, les profils publics et le Digital Exporter Passport ; s'inscrit. | CdC §4, §9 | Oui |
| International Buyer | Utilisateur d'une organisation acheteuse : recherche, RFQ, comparaison, négociation, suivi des trades, paiement enregistré, avis. | CdC §10, §48 | Oui |
| Malagasy Exporter | Utilisateur d'une organisation exportatrice : profil, produits, capacité, vérification, réponse aux RFQ, quotations, négociation, préparation, expédition, avis. | CdC §11, §49 | Oui |
| MadaSource Admin | Personnel MadaSource : vérification, supervision, intervention, configuration, paiements, exceptions, audit. | CdC §34-41 | Oui |
| Système | Traitements automatiques : matching après soumission, création du Trade à l'acceptation, suivi de la validité des quotations (Expiring, Expired ; mode de calcul : Jours 2-3), notifications, calcul des indicateurs. | Déduit de CdC §14, §18, §22, §29, §43 | Oui |
| Operations, Compliance, Finance et Logistics Admin, Super Admin | Rôles d'administration spécialisés. | CdC §53 | Non (préparés) |
| Partner | Prestataire tiers (banque, logistique, inspection…). | CdC §53, §57 | Non (préparé) |
| Producer, Collector, Cooperative | Acteurs amont de la filière. | CdC §71, Planning §10 | Non (flags désactivés) |

## 2. Modèle multi-organisation

Défini par le CdC §54 et RJ 9 :

- Toute personne agit en tant que **membre d'une organisation** (Organization → Users → Roles → Permissions). Une organisation peut avoir plusieurs utilisateurs aux permissions différentes.
- **Isolation** : un utilisateur n'accède qu'aux ressources de son organisation, ou à celles dont son organisation est **partie prenante** (RFQ adressée, Trade dont elle est l'acheteur ou l'exportateur, conversation dont elle est participante). Cette règle est vérifiée à chaque accès (RJ 9, RJ section 1).
- **Type d'organisation** : acheteuse, exportatrice, ou MadaSource (pour les administrateurs).
  - Hypothèse de travail, `À VALIDER` (Q-09) : une organisation n'a qu'un seul type en V1.
  - Proposition, `À VALIDER` (Q-74) : les comptes admin appartiennent à une organisation interne « MadaSource ».
- **Appartenance** : dans l'exemple du CdC §54, tous les employés d'une société appartiennent à la même organisation. Le cas d'un utilisateur membre de plusieurs organisations n'est pas traité par les sources (Q-74).
- **Rôles internes** à une organisation (directeur, commercial, opérations) : prévus par le CdC §54. Leur activation en V1 est `À VALIDER` (Q-10). Hypothèse minimale : tous les membres d'une organisation V1 ont le rôle de base de son type (Buyer ou Exporter).

Convention de nommage des permissions proposée, à confirmer au Jour 9 : `<ressource>:<action>`, par exemple `rfqs:create`, `quotations:submit`, `trades:transition`, `verification:decide`.

## 3. Matrice des actions

Légende :
- **Oui** : autorisé sans restriction particulière.
- **Propre** : limité à sa propre organisation.
- **Destinataire** : limité aux RFQ adressées à l'organisation, ou auxquelles elle est autorisée à répondre (RJ 21).
- **Partie** : limité aux objets (Trade, négociation, conversation) dont l'organisation est partie prenante.
- **Non** : interdit.
- **Q-NN** : question ouverte.

### 3.1 Comptes, organisations, vérification

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| S'inscrire comme acheteur ou exportateur | Oui | — | — | — | CdC §4, §10-11 |
| Consulter et modifier le profil de l'organisation | Non | Propre | Propre | Oui | RJ 13-14, CdC §35-36 |
| Gérer les membres de l'organisation | Non | Q-10 | Q-10 | Oui | CdC §54 |
| Approuver, suspendre ou bloquer un compte acheteur | Non | Non | Non | Oui | CdC §35 |
| Approuver, rejeter, suspendre ou réactiver un exportateur | Non | Non | Non | Oui | CdC §36 |
| Déposer les documents de vérification | Non | — | Propre | Oui | Déduit de CdC §36 |
| Attribuer un niveau de vérification, décider | Non | Non | Non | Oui | CdC §36, RJ 15 |
| Voir le niveau de vérification obtenu par un exportateur | Oui | Oui | Oui | Oui | CdC §61 (« Verification » dans les données publiques) |
| Voir une vérification en statut Pending, Rejected, Expired ou Suspended | Q-16 | Q-16 | Propre | Oui | — |
| Voir les notes de vérification et les documents examinés | Non | Non | Q-15 (motif de rejet) | Oui | CdC §8 |

### 3.2 Produits et marketplace

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Créer, modifier, publier, dépublier, archiver un produit | Non | Non | Propre | Oui (modération : Q-19) | RJ 17, CdC §34 |
| Rechercher et consulter les produits publiés | Oui | Oui | Oui | Oui | CdC §5 |
| Voir l'indication de prix | Q-06 | Q-06 | Propre | Oui | CdC §5-6 |
| Consulter un profil exportateur public ou un Digital Passport | Oui | Oui | Oui | Oui | CdC §9 |
| Enregistrer des favoris | Non | Propre (Q-63) | — | — | CdC §51 |

### 3.3 RFQ et matching

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Créer un brouillon, modifier avant soumission, soumettre | Q-28 | Propre | Non | Q-40 | CdC §12, RJ 20 |
| Modifier ou annuler après soumission | Non | Q-23 | Non | Q-40 | RJ 20 |
| Consulter une RFQ | Non | Propre | Destinataire | Oui | RJ 21, CdC §37 |
| Respond, Decline, Ask Question | Non | Non | Destinataire | Non | CdC §15 |
| Lancer ou relancer le matching | Non | Non | Non | Oui (le Système le lance à la soumission) | RJ 23 |
| Voir les résultats du matching (scores, raisons) | Non | Q-31 | Propre match, Q-31 | Oui | CdC §14, RFS J 23 |
| Configurer les pondérations du matching | Non | Non | Non | Oui | CdC §14, RFS J 23 |
| Intervenir manuellement sur une RFQ | Non | Non | Non | Oui (périmètre : Q-40) | CdC §37 |

### 3.4 Quotations et négociation

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Créer et soumettre une quotation | Non | Non | Destinataire | Q-40 | CdC §16 |
| Modifier ou retirer une quotation | Non | Non | Propre (Q-34) | Q-40 | — |
| Consulter et comparer les quotations d'une RFQ | Non | Propre RFQ | Propre quotation | Oui | CdC §19, §38 |
| Configurer les règles de prix (marge, commission) | Non | Non | Non | Oui | CdC §17 |
| Saisir les coûts externes (fret, assurance…) | Non | Non | Q-04 | Q-04 | CdC §17, §33 |
| Valider une quotation avant présentation à l'acheteur | — | — | — | Q-07 | CdC §38 |
| Soumettre une contre-offre | Non | Partie | Partie | Q-40 | CdC §20 |
| Accepter la dernière proposition de l'autre partie | Non | Partie | Partie | Q-40 | CdC §19-20, §67 (déduit) |
| Refuser une proposition | Non | Partie | Partie | Q-40 | RJ 26 (Q-39) |
| Consulter l'historique de négociation | Non | Partie (vue acheteur) | Partie (vue exportateur) | Oui (complet) | CdC §21, §38 |

### 3.5 Trade, documents, paiement, expédition

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Créer un Trade | Non | Non | Non | Non (le Système le crée à l'acceptation) | CdC §22 |
| Consulter un Trade et sa timeline | Non | Partie | Partie | Oui | CdC §23, §39 |
| Passer en Preparation | Non | Non | Partie (déduit) | Q-41 | CdC §67 étape 15 |
| Autres transitions du Trade | Non | Q-41 | Q-41 | Q-41 | CdC §24 |
| Mettre en attente, annuler | Non | Q-43, Q-44 | Q-43, Q-44 | Q-43, Q-44 | CdC §24 |
| Déposer un document | Non | Propre ou Partie | Propre ou Partie | Oui | CdC §26 |
| Consulter un document | Non (jamais pour un document sensible) | Propre ou Partie (visibilité du document) | Propre ou Partie (visibilité du document) | Oui | CdC §26, §61 |
| Enregistrer un paiement, déposer un justificatif | Non | Q-54 | Q-54 | Oui | CdC §30 |
| Confirmer un paiement, enregistrer un remboursement | Non | Non | Non | Oui | CdC §30, RJ 33 |
| Créer et mettre à jour une expédition | Non | Non | Q-58 | Q-58 | CdC §31, §67 étape 16 |
| Confirmer la livraison | Non | Q-41 | Q-41 | Q-41 | CdC §67 étape 18 (« Buyer receives goods ») |

### 3.6 Communication, réputation, exceptions, administration

| Action | Visiteur | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Lire et écrire dans une conversation | Non | Partie | Partie | Q-50 | CdC §28 |
| Lire ses notifications | Non | Propre utilisateur | Propre utilisateur | Propre utilisateur | CdC §29 |
| Demander un échantillon | Non | Oui (Q-53) | — | — | CdC §27 |
| Établir un devis d'échantillon, expédier | Non | Non | Partie (Q-53) | Q-53 | CdC §27 |
| Évaluer la contrepartie après un Trade Completed | Non | Partie (évalue l'exportateur) | Partie (évalue l'acheteur) | Non (pas d'avis fabriqué) | CdC §42 |
| Voir les avis et indicateurs d'un exportateur | Oui (profil public, déduit de CdC §7) | Oui | Oui | Oui | CdC §7 |
| Voir les avis et indicateurs d'un acheteur | Non | Propre | Q-59 | Oui | CdC §44 |
| Ouvrir un litige | Non | Partie | Partie | — | CdC §41 |
| Gérer exceptions et litiges (assigner, commenter, résoudre, escalader) | Non | Non | Non | Oui | CdC §40-41 |
| Consulter le journal d'audit | Non | Non | Non | Oui, en lecture seule | CdC §34, RJ 12 |
| Paramètres, feature flags, règles configurables | Non | Non | Non | Oui | CdC §34, §71 |

## 4. Visibilité des données

Base : CdC §61 (public / privé), §11, §17, §60. Légende :
- **Oui** : visible ;
- **Propre** : visible par l'organisation propriétaire ;
- **Partie** : visible par l'autre partie d'une RFQ ou d'un Trade ;
- **Non** : jamais visible ;
- **Q-NN** : question ouverte.

| Donnée | Public | Buyer | Exporter | Admin | Source |
|---|---|---|---|---|---|
| Nom de société, produits, vérification (niveau obtenu ; autres statuts : Q-16), localisation générale, certifications | Oui | Oui | Oui | Oui | CdC §61 |
| Logo, description, années d'activité, marchés d'export, capacité disponible | Oui (déduit du profil public, CdC §7) | Oui | Oui | Oui | CdC §7 |
| Coordonnées : contact, email, téléphone, adresse complète | Non | Propre ; Partie : Q-27, Q-51 | Propre ; Partie : Q-27, Q-51 | Oui | CdC §61 |
| Identité de l'acheteur dans l'inbox exportateur | — | — | Pays seulement dans l'exemple ; identité : Q-27 | Oui | CdC §15 |
| Informations bancaires et de paiement de l'exportateur | Non | Non (Q-55) | Propre | Oui | CdC §11, §61 |
| Informations fiscales, documents d'immatriculation, documents d'export | Non | Non | Propre | Oui | CdC §11, §61 |
| Documents internes, contrats | Non | Propre ou Partie selon la visibilité | Propre ou Partie selon la visibilité | Oui | CdC §61 |
| Communications privées | Non | Partie | Partie | Q-50 | CdC §61 |
| Prix net fournisseur (Supplier Cost) | Non | **Non** | Propre | Oui | CdC §2, §17, §61 |
| Coûts externes détaillés | Non | Q-04 | Q-04 | Oui | CdC §17, §33 |
| Marge MadaSource, commission | Non | **Non** | **Non** (Modèle B : Q-03) | Oui | CdC §2, §61 |
| Prix final acheteur | Non | Oui | Q-05 | Oui | CdC §2 |
| Indication de prix du catalogue | Q-06 | Q-06 | Propre | Oui | CdC §5-6 |
| Marge commerciale brute agrégée | Non | Non | Non | Oui | CdC §63 |
| Notes de vérification, notes internes et admin | Non | Non | Non | Oui | CdC §8, RJ 35 |
| Avis sur un exportateur, indicateurs de performance exportateur | Oui (déduit du profil, CdC §7) | Oui | Oui | Oui | CdC §7, §43 |
| Avis sur un acheteur, indicateurs acheteur | Non | Propre | Q-59 | Oui | CdC §44 |
| Scores et raisons du matching | Non | Q-31 | Q-31 | Oui | CdC §14 |
| Journal d'audit | Non | Non | Non | Oui (lecture seule) | CdC §52 |
| Hash de mot de passe, tokens | Non | Non | Non | **Non** (jamais via l'API) | RJ section 1 |

## 5. Règles d'accès transverses

1. Les permissions sont vérifiées côté serveur sur chaque endpoint privé, sans se fier au client (CdC §60, RJ section 1).
2. L'accès à un objet par identifiant vérifie l'appartenance ou la participation. Code de réponse en cas de refus (404 ou 403) : convention à fixer au Jour 2. Proposition : 404, pour ne pas révéler l'existence de l'objet.
3. Un même objet est servi par des schémas différents selon le rôle : public, Buyer, Exporter, Admin (RJ 14 : « Sépare clairement schémas publics, privés et admin »). Proposition de mise en œuvre : un schéma public ne dérive jamais d'un schéma privé.
4. Les actions admin sont auditées comme les autres (CdC §52). Même un administrateur ne modifie pas l'historique de négociation, les TradeEvent ni le journal d'audit par les opérations normales (CdC §20, RJ 12, RJ 28).
5. Un compte dans un statut restrictif (Suspended, Blocked) perd l'accès aux actions métier. Le détail par statut est `À VALIDER` (Q-11, Q-12).
6. Aucun rôle futur n'est activable sans décision explicite de MadaSource (CdC §53, §71).
