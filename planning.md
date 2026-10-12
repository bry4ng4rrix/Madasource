# MADASOURCE — PLANNING CLIENT

Version : 1.0

## 1. Présentation du projet

MadaSource est une plateforme B2B dédiée au commerce international, avec un lancement initial centré sur les produits malgaches :

- Vanille
- Girofle
- Cacao

L'objectif est de permettre à un acheteur international de découvrir des exportateurs malgaches, demander une offre, comparer les propositions, négocier, confirmer une transaction et suivre son déroulement depuis une interface centralisée.

## 2. Périmètre initial

La première version est centrée sur :

### Utilisateurs principaux
- Acheteurs internationaux
- Exportateurs malgaches
- Administration MadaSource

### Parcours principal
Découverte
→ Demande de cotation
→ Matching
→ Réception des offres
→ Comparaison
→ Négociation
→ Acceptation
→ Création de transaction
→ Documents
→ Enregistrement du paiement
→ Expédition
→ Suivi
→ Livraison
→ Finalisation

## 3. Planning global

Durée indicative : 50 jours ouvrés de développement, sur une base de 8 à 9 heures de travail par jour.

Le planning est organisé en 10 étapes.

### Étape 1 — Cadrage et architecture
Jours 1 à 3

Objectifs :
- analyser les besoins
- définir les parcours
- définir les rôles
- définir l'organisation générale du système
- préparer la structure des données
- définir les règles de sécurité et de confidentialité

Livrable :
- architecture fonctionnelle et technique validée

---

### Étape 2 — Fondation de la plateforme
Jours 4 à 10

Objectifs :
- mettre en place la plateforme
- créer les comptes et accès
- gérer les organisations
- gérer les rôles et permissions
- mettre en place la sécurité et la traçabilité

Livrable :
- base fonctionnelle de la plateforme
- accès sécurisés
- administration des droits

---

### Étape 3 — Profils et marketplace
Jours 11 à 18

Objectifs :
- profils acheteurs
- inscription exportateurs
- profils exportateurs
- vérification des exportateurs
- catalogue produits
- marketplace
- passeport numérique exportateur
- site public

Livrable :
- marketplace fonctionnel avec Vanille, Girofle et Cacao
- profils professionnels
- recherche et filtres

---

### Étape 4 — Demandes de cotation et matching
Jours 19 à 23

Objectifs :
- création des RFQ
- gestion des demandes
- réception des demandes par les exportateurs
- matching entre besoins et exportateurs
- administration des correspondances

Livrable :
- parcours RFQ → Matching fonctionnel

---

### Étape 5 — Offres et négociation
Jours 24 à 28

Objectifs :
- création des quotations
- calcul commercial
- validité des offres
- comparaison des offres
- contre-offres
- historique des négociations

Livrable :
- parcours Quotation → Negotiation fonctionnel

---

### Étape 6 — Gestion des transactions
Jours 29 à 33

Objectifs :
- création automatique d'une transaction après acceptation
- génération d'un identifiant unique
- suivi des états
- tableau de bord de transaction
- historique et timeline

Livrable :
- Trade Dashboard
- identifiant central de transaction
- suivi de l'opération

---

### Étape 7 — Documents, messages et notifications
Jours 34 à 37

Objectifs :
- gestion des documents
- échanges entre acheteur et exportateur
- notifications
- demandes d'échantillons

Livrable :
- espace documentaire
- messagerie
- notifications
- workflow d'échantillons

---

### Étape 8 — Vérification, réputation et administration
Jours 38 à 40

Objectifs :
- évaluations
- indicateurs de performance
- gestion des exceptions
- gestion des litiges
- console d'administration

Livrable :
- administration centralisée
- suivi de performance
- gestion des incidents

---

### Étape 9 — Paiement et expédition
Jours 41 à 43

Objectifs :
- enregistrement des paiements
- suivi manuel des expéditions
- informations de transport
- mise à jour des statuts
- finalisation de la transaction

Livrable :
- parcours complet jusqu'à la livraison et la clôture

Important :
La première version prévoit un système d'enregistrement du paiement et une gestion initiale des expéditions. Elle ne suppose pas que MadaSource soit une banque ou qu'une intégration bancaire soit déjà disponible.

---

### Étape 10 — Finalisation et mise en production
Jours 44 à 50

Objectifs :
- anglais/français
- gestion des devises
- adaptation mobile/tablette/ordinateur
- amélioration de l'expérience utilisateur
- tests complets
- sécurité
- performance
- préparation de la production
- documentation
- vérification finale

Livrable :
- version V1 stabilisée et prête pour la mise en production

## 4. Fonctionnalités incluses dans la V1

### Marketplace
- recherche de produits
- catégories
- origine
- qualité
- grade
- certifications
- quantité
- MOQ
- emballage
- Incoterm
- exportateur
- statut de vérification
- indication de prix

### Acheteur
- inscription
- profil entreprise
- recherche d'exportateurs
- création de RFQ
- réception et comparaison des offres
- négociation
- suivi des transactions
- documents
- paiement enregistré
- expédition et suivi

### Exportateur
- inscription
- profil entreprise
- produits
- informations commerciales
- capacité
- certifications
- processus de vérification
- réception des RFQ
- réponse aux demandes
- création d'offres
- négociation
- suivi des transactions
- documents
- expédition

### Administration MadaSource
- gestion des acheteurs
- gestion des exportateurs
- vérification
- produits
- RFQ
- matching
- quotations
- négociations
- transactions
- documents
- paiements
- expéditions
- messages
- évaluations
- exceptions
- rapports
- paramètres
- journal d'activité

## 5. Fonctionnement commercial

La plateforme doit pouvoir évoluer vers deux modèles :

### Modèle 1 — MadaSource comme revendeur/intermédiaire commercial
Le prix fournisseur et les éléments commerciaux internes sont gérés dans le système, tandis que le prix présenté à l'acheteur est calculé selon les règles commerciales définies.

### Modèle 2 — MadaSource comme intermédiaire
MadaSource peut fonctionner avec une commission ou des frais de service définis contractuellement.

La structure juridique, fiscale et contractuelle définitive doit être déterminée séparément.

## 6. Données sensibles

Certaines informations ne sont pas destinées à être publiques.

Exemples :
- informations bancaires
- documents internes
- contrats
- communications privées
- marges commerciales
- informations financières sensibles

Les informations publiques et privées sont séparées.

## 7. Paiements

La première version permet principalement d'enregistrer et suivre un paiement :

- montant
- devise
- référence
- date
- justificatif
- statut
- confirmation administrative

Les intégrations bancaires et de paiement pourront être ajoutées ultérieurement.

## 8. Logistique

La première version permet d'enregistrer manuellement :

- transporteur
- méthode d'expédition
- référence
- numéro de conteneur
- numéro de suivi
- origine
- destination
- départ prévu
- arrivée prévue
- statut

Les connexions automatiques avec des transporteurs pourront être ajoutées ultérieurement.

## 9. Langues et devises

Version initiale :
- Anglais
- Français

Devises initiales :
- USD
- EUR

L'architecture permettra l'ajout ultérieur d'autres langues et devises.

## 10. Ce qui est prévu pour plus tard

Ces fonctionnalités ne font pas partie du premier périmètre opérationnel :

- intégrations bancaires
- passerelles de paiement
- lettres de crédit
- mécanismes d'escrow selon le cadre légal
- intégrations transporteurs
- suivi automatique des expéditions
- inspection
- certification externe
- intégrations douanières
- assurance
- partenaires externes
- assistant IA
- matching avancé
- intelligence commerciale
- intelligence de la demande
- intelligence des prix
- outils prédictifs
- modules producteurs
- modules collecteurs
- modules coopératives

L'architecture sera préparée pour permettre ces évolutions sans refaire toute la plateforme.

## 11. Démonstration finale attendue

La démonstration finale devra montrer un scénario complet :

1. Un acheteur international crée son compte.
2. Il recherche de la Vanille de Madagascar.
3. Il consulte les exportateurs.
4. Il crée une demande de cotation.
5. La plateforme identifie les exportateurs compatibles.
6. Les exportateurs répondent.
7. L'acheteur compare les offres.
8. Une négociation est réalisée.
9. Une offre est acceptée.
10. Une transaction est créée.
11. Les documents sont ajoutés.
12. Le paiement est enregistré.
13. L'expédition est créée.
14. Le statut passe en transit.
15. La livraison est enregistrée.
16. La transaction est finalisée.

Le même principe doit être applicable aux trois catégories initiales : Vanille, Girofle et Cacao.

## 12. Résultat attendu de la V1

À la fin du projet, MadaSource doit disposer d'une première plateforme opérationnelle permettant de gérer le parcours commercial principal entre acheteurs internationaux et exportateurs malgaches, avec une architecture préparée pour les futures extensions.

Le projet ne vise pas à intégrer immédiatement tous les services du commerce international. Il vise d'abord à construire une base fiable permettant à MadaSource d'évoluer progressivement vers une infrastructure numérique de facilitation du commerce.

## 13. Points à valider avec le client

Avant la mise en production, les éléments suivants devront être validés :

- règles commerciales définitives
- modèle juridique de MadaSource
- conditions contractuelles
- politique de vérification des exportateurs
- politique de confidentialité
- règles de paiement
- responsabilités liées au transport
- responsabilités liées à l'assurance
- responsabilités liées aux documents d'exportation
- règles de litige et d'annulation
- contenu final du site public
- identité visuelle
- données réelles des premiers exportateurs et produits
