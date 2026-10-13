# Jour 3 — Modèle de données et ERD

Date : 2026-10-13 · Statut : **TERMINÉ AVEC RÉSERVES**. Jour documentaire : aucun code applicatif. Réserves :
- le modèle du Trade est **provisoire** : il attend la validation de Q-82 ;
- les réponses du responsable produit sont enregistrées comme **PROPOSED**, non approuvées ;
- la syntaxe de l'ERD n'a pas été validée par un moteur de rendu Mermaid.

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 3 : concevoir le modèle de données sans implémenter les modèles Python. Il fallait :
- produire quatre documents : modèle de données, ERD, classification des données, index et contraintes ;
- couvrir les 29 entités demandées, avec cardinalités, contraintes, index, statuts, champs sensibles et relations ;
- éviter les tables inutiles à la V1 ;
- stocker les montants en `NUMERIC` et figer les prix transactionnels.

En cours de journée, le responsable produit a transmis des réponses à 11 questions. Ses consignes :
- les traiter comme des propositions ;
- signaler les conflits avec le CdC ;
- créer un registre des décisions et un graphe de dépendances ;
- **demander validation avant de finaliser le modèle du Trade** (Q-82).

## Prérequis vérifiés

- Livrables des Jours 1 et 2 présents ; `check.md` : Jour 2 OK.
- Le cahier des charges a été réextrait du PDF versionné pour vérifier les points contestés (§28, format des références).
- L'utilisateur a fait quatre commits pendant la journée (`0c1bf4f`, `8f4619d`, `bb8a36a`, `66a95bc`), qui poussent les livrables en cours. L'arbre de travail était identique à ces commits : aucune modification de l'utilisateur n'a été écrasée. Les dernières corrections (section « Vérification finale ») ne sont pas encore commitées.

## Fichiers

**Créés** :

| Fichier | Contenu |
|---|---|
| [data-model.md](../data-model.md) | 72 tables, dont 4 conditionnelles, par module ; conventions de types ; invariants ; questions nées du Jour 3. Trade (§5.16) **provisoire** |
| [erd.mmd](../erd.mmd) | Diagramme entité-relation Mermaid : 72 entités, 107 relations, colonnes structurantes |
| [data-classification.md](../data-classification.md) | 10 classes (dont PRIX NET et PRIX FINAL), visibilités, champs par audience, clés interdites, valeurs sentinelles, audit, inventaire des données personnelles |
| [indexes-and-constraints.md](../indexes-and-constraints.md) | Nommage, 26 clés étrangères composites, `CHECK`, unicité, index de lecture, droits par colonne, effacement, ordre de verrouillage |
| [dependency-graph.md](../dependency-graph.md) | Graphe des modules, prérequis métier, prérequis par jour, comparaison avec l'ordre proposé (Q-93), points de séquence SQ-01 à SQ-06 |
| [../../decisions/architecture-decisions.md](../../decisions/architecture-decisions.md) | Registre des décisions : 11 réponses PROPOSED, conflits CF-01 à CF-10, décisions du Jour 2 concernées |

**Modifiés** (annotations, sans suppression de décision) :
- `risks-and-open-questions.md` : réponses annotées, R-32, Q-94 à Q-101, synthèse et §5 ;
- `architecture.md` : D-09, D-16, D-19, D-28, D-30 ;
- `security-design.md` : S-24, S-33, §18 ;
- `api-conventions.md` : codes en majuscules, en-tête `X-Organization-Id` ;
- `module-boundaries.md` : renvoi au modèle, compteur `MST`, socle ;
- `business-rules.md` : BR-REF-01, BR-REF-03 ;
- `requirements.md` : REQ-MSG-01 (CF-10) ;
- `domain-glossary.md` : 8 termes ;
- `workflows.md`, `claude-code-audit.md` : deux tableaux Markdown cassés réparés (contenu inchangé).

**Correction d'un document du Jour 1** : BR-REF-01 affirmait que le CdC exige une numérotation séquentielle. Le CdC ne donne que des exemples (`RFQ-2026-0012`, `MST-2026-000145`). La règle ne garde comme « Défini » que le préfixe et l'année.

## Démarche et revues

| Étape | Résultat |
|---|---|
| 1. Registre des décisions | 11 réponses enregistrées comme PROPOSED. Conflits avec le CdC signalés, sans remplacer l'exigence : CF-01 à CF-09 (statuts de vérification, statuts exportateur, rôles, références, frontend Flutter, champs par ligne, casse des codes, ordre des documents, code `CLOVES`) |
| 2. Rédaction des cinq documents | Voir ci-dessus |
| 3. **Relecture base de données** (agent `database-reviewer`) | 0 bloquant, 10 importants, 13 mineurs. Principaux : clés composites incomplètes sur la chaîne d'acceptation, séparation des tâches contournable sur les coordonnées bancaires, prise d'effet différée incompatible avec l'index unique, compte bénéficiaire non tracé, droits par colonne, ligne de RFQ bloquée après annulation, effacement des textes immuables, ordre de verrouillage, évolution des `CHECK` ignorée par Alembic. Tous traités |
| 4. **Relecture sécurité** (agent `security-auditor`) | 0 critique, 4 élevés, 11 moyens, 5 faibles. Élevés : fil de messages commun en Modèle A ; visibilité non bornée par la convention ; montants de même nom dans les deux conventions ; utilisateur membre des deux parties. Tous traités ; le premier a ouvert un conflit avec le CdC (CF-10, Q-99) |
| 5. **Revue finale** (skill `code-review-madasource`) | Verdict avant corrections : non prêt. 1 bloquant (CF-10 non signalé), 9 importants, 9 facultatifs. Tous traités |
| 6. **Vérification ciblée des corrections** (agent `code-reviewer`) | Verdict : prêt avec réserves. 9 points sur 10 corrects, 1 partiel, 0 bloquant, 1 important, 8 mineurs. Tous corrigés (section suivante) |

## Choix structurants proposés

| Sujet | Choix |
|---|---|
| Types | `numeric(19,4)` et devise `char(3)` ; `numeric(18,3)` et unité pour les quantités ; `timestamptz` ; statuts en `varchar` + `CHECK`, sans `ENUM` PostgreSQL |
| Organisations | Capacités BUYER et EXPORTER avec un statut de compte chacune ; rôle OWNER ou MEMBER porté par l'adhésion ; invitations liées à l'email vérifié ; rôles de plateforme séparés, portée contrôlée par la base |
| Vérification | Statuts du CdC sur les enregistrements ; statut de l'organisation calculé, sans perte d'un niveau acquis |
| Références | Suffixe aléatoire, unicité en base, nouvelle tentative dans un point de sauvegarde ; plus de table de compteurs (si Q-37 est approuvée) |
| RFQ | Lignes multiples, mode de diffusion, destinataires avec source ; une quotation par exportateur et par RFQ (Q-94) |
| Prix | Versions de quotation immuables ; prix net et prix final dans des colonnes distinctes ; marge et commission dans des tables `*_financials` séparées |
| Trade (provisoire) | Référence centrale et conventions `SALE`, `SUPPLY` ou `DIRECT`, dont les parties se déduisent du type ; statut de paiement par convention ; paiements, événements et litiges rattachés à leur convention par clés composites |
| Cohérence | 26 clés étrangères composites (chaîne RFQ → quotation → Trade → convention → paiement) ; `CHECK` acheteur ≠ exportateur |
| Immuabilité | Droits par colonne pour le rôle applicatif ; aucune suppression en cascade |
| Confidentialité | Clés interdites par audience, schémas distincts par convention, valeurs sentinelles (montants et identifiants) dans les tests |

## Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `pdftotext -layout` du CdC (copie dans le répertoire temporaire de la session) | Texte extrait (1 309 lignes). §28 : « Participants: Buyer ↔ Exporter ». Références : exemples seulement, aucune exigence de séquence |
| `python3 -I …/check_erd.py .` (script de la session) | `entités : 72 ; relations : 107 ; tables §3 : 72` → OK : toute FK a une cible définie et une relation dessinée, **aucune FK vers un module de niveau supérieur**, tables identiques à `data-model.md`, colonnes présentes dans `data-model.md` |
| Même script sur une copie avec erreurs injectées | 28 erreurs détectées, dont les FK montantes et une relation supprimée : le contrôle fonctionne |
| `python3 -I …/check_refs.py .` | `identifiants définis : 525` → OK : Q, R, SRC, REQ, NFR, BR, D, S, P, CF et SQ tous définis ; liens et ancres valides |
| Même script sur une copie avec erreurs injectées | 5 erreurs détectées sur 5 (identifiants, lien et ancre) |
| `python3 -I …/check_tables.py .` | OK après correction de 3 tableaux (dont 2 défauts antérieurs au Jour 3) |
| `python3 -I .claude/tests/test_hooks.py` | 0 échec |
| Recherche de motifs de secrets dans les fichiers du jour | Aucun motif trouvé |
| `git status`, `git log`, `git show --stat` | Trois commits de l'utilisateur inspectés ; arbre de travail cohérent |

Non exécuté : rendu Mermaid de l'ERD (aucun outil `mmdc` installé, aucune installation sans accord) ; Ruff et Pytest (pas de code).

## Vérification finale

La vérification ciblée a confirmé :
- la correction des points de la revue finale, dont le bloquant (CF-10 et Q-99 signalés, REQ-MSG-01 annoté) ;
- la disparition des colonnes retirées dans toute la documentation ;
- la cohérence des colonnes ajoutées entre `data-model.md`, `erd.mmd` et `indexes-and-constraints.md`.

Constats restants, tous corrigés ensuite :
- **important** : `trade_events.document_id` exige le module `documents` dès le Jour 27. Le prérequis est déplacé au Jour 27, avec une migration additive au Jour 29 si SQ-02 diffère les documents ;
- **mineurs** :
  - index de `verification_records` aligné sur le nouveau calcul du statut ;
  - droits par colonne de `platform_role_assignments` ;
  - Q-101 corrigée : seuls les comptes de réception et la confirmation des paiements sont bloqués avec un admin unique ;
  - en-tête `X-Organization-Id` relié à Q-100 ;
  - invariant de `trade_items` aligné sur l'index partiel ;
  - ERD de `platform_role_assignments` complété ;
  - lien `confirms_external_cost_id` entre une confirmation de coût et son estimation ;
  - test des canaux de conversation conditionné à Q-99.

Après ces corrections, les contrôles automatiques (références, ERD, tableaux) sont de nouveau à 0 erreur. Elles n'ont pas fait l'objet d'une troisième revue par un agent.

## Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui, avec réserves : les quatre livrables couvrent les 29 entités demandées ; le Trade est provisoire (Q-82) |
| Tests appropriés et résultat connu | Sans objet : jour documentaire. Contrôles automatiques de cohérence exécutés (ci-dessus) ; tests de projection et de sentinelles spécifiés pour les jours d'implémentation |
| Migrations et contraintes cohérentes | Contraintes spécifiées et relues ; aucune migration (Jour 6) |
| Documentation et `.env.example` à jour | Documentation : oui. `.env.example` : sans objet (Jour 4) |
| Aucun secret ajouté | Oui |
| Défauts critiques corrigés ou signalés | Oui : tous les constats des trois revues sont corrigés ; les conflits avec le CdC sont signalés (CF-01 à CF-10) |
| Décisions non définies marquées `À VALIDER` | Oui : 8 nouvelles questions (Q-94 à Q-101), 6 points de séquence (SQ-01 à SQ-06), 1 nouveau risque (R-32) |

## Décisions À VALIDER

| Question | Sujet | Échéance |
|---|---|---|
| **Q-82** | Structure du Modèle A (conventions `SALE` et `SUPPLY`), contreparties, visibilité : **bloque la finalisation du modèle du Trade** | Avant le Jour 24, bloque le Jour 27 |
| **Q-71** | Visibilité du dépôt GitHub : les livrables y sont poussés | **Immédiat** |
| Q-09, Q-10, Q-12, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74, Q-93 | Approbation des réponses PROPOSED | Avant le Jour 9 (Q-09, Q-10, Q-74) ; Jours 14-19 pour les autres |
| CF-01 à CF-10 | Conflits avec le CdC, dont **CF-10** (messagerie directe, CdC §28) | Avant les jours concernés |
| Q-99 | Canaux de messagerie séparés en Modèle A | Avant le Jour 24 |
| Q-98, Q-100, Q-101 | Utilisateur des deux côtés ; admin titulaire d'une adhésion cliente ; nombre minimal d'admins | Jour 9 ; Jour 33 pour Q-101 |
| Q-94 à Q-97 | Une quotation par exportateur ; statuts Accepted et Closed d'une RFQ multi-lignes ; valeurs `OWNER_ONLY` et `PUBLIC` ; motif de suspension communiqué | Jours 11 à 29 |
| SQ-02, SQ-03, SQ-05 | Documents avant le Jour 14 ; Respond avant le Jour 21 ; modèle commercial avant le Jour 24 | Jours 14, 21, 24 |
| Q-08 | Précision des montants, avant la première migration monétaire | Jour 6 |

## Risques et limites

- **Modèle du Trade provisoire** : à ne pas implémenter avant Q-82 ; la structure juridique n'est pas un choix technique.
- **Une seule personne admin (R-32)** : les contrôles de séparation des tâches bloqueraient tout paiement en Modèle A.
- **Utilisateur membre des deux parties (Q-98)** : en Modèle A, il lirait la marge ; protection applicative seulement.
- **Messagerie (CF-10)** : si le CdC §28 est maintenu, des messages directs peuvent révéler la marge (R-05).
- **Dépôt distant** (R-26, Q-71) : les livrables du Jour 3 ont été poussés par l'utilisateur ; visibilité inconnue. `.gitignore` sans `.env` (R-20).
- **Droits par colonne** : ils protègent contre une erreur de code, pas contre un administrateur de la base.
- **ERD** : contrôlé par un script structurel, pas par un moteur de rendu.
- **Aucune conformité juridique déclarée** : l'inventaire des données personnelles est un outil technique ; base légale et durées à valider (Q-68, Q-69).

## Préparation du Jour 4 (non exécuté)

Jour 4 — Initialisation du dépôt :
- squelette `backend/app`, `backend/tests`, `backend/alembic` ;
- `.gitignore`, `.env.example`, `README.md`, `backend/pyproject.toml`, `backend/Dockerfile`, `docker-compose.yml` ;
- endpoint health et test smoke.

Prérequis et décisions à prendre avant ou pendant le Jour 4 :
- **Q-71** (dépôt privé ?) et complément du `.gitignore` (`.env`, environnements virtuels) **avant** de créer un `.env` ;
- version de Python (D-27 : 3.12 ou 3.14), version d'UUID (D-15), pilote PostgreSQL (D-10), version de PostgreSQL ;
- confirmation de `uv` comme gestionnaire d'environnement ;
- ports hôte : 5432, 6379 et 8000 sont occupés ; Docker Compose utilisera d'autres ports ;
- toute installation de dépendance sera présentée avant d'être faite.

**Le Jour 4 ne sera pas lancé sans ta validation explicite.**
