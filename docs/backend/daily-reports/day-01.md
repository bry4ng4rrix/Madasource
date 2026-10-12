# Jour 1 — Analyse fonctionnelle backend

Date : 2026-10-12 · Statut : **TERMINÉ**. Les points `À VALIDER` attendent la réponse du client, ce qui est normal pour un jour d'analyse.

## Objectif du jour

Consigne de `roadmap_backend_fastapi.md`, Jour 1 : analyser le cahier des charges sans coder l'application, et produire une spécification exploitable qui couvre :
- acteurs, modules, entités, relations, statuts ;
- transitions RFQ, Quotation, Negotiation et Trade ;
- confidentialité, prix, matching, expiration, audit ;
- séparation V1 / futur / intégrations, décisions `À VALIDER`, risques et matrice de périmètre.

Le jour a été précédé d'une **préparation de Claude Code** (agents, skills, règles, hooks), demandée par l'utilisateur. Elle est décrite dans [claude-code-setup.md](../claude-code-setup.md) et [claude-code-audit.md](../claude-code-audit.md).

## 1. Sources analysées

| Source | Lecture |
|---|---|
| Cahier des charges « MadaSource — Complete Platform Architecture & Functional Requirements » (PDF, 34 p., `~/Téléchargements/`) | Intégrale, après extraction texte (`pdftotext -layout`) |
| `planning.md` | Intégrale |
| `roadmap_backend_fastapi.md` | Intégrale |
| `roadmap.md` | Intégrale |

## 2. Fichiers créés

| Fichier | Contenu |
|---|---|
| `docs/backend/requirements.md` | 24 modules du CdC rattachés aux modules backend ; 115 exigences fonctionnelles (REQ-…) et 10 non fonctionnelles (NFR-…) tracées vers leur source ; modèle de domaine conceptuel |
| `docs/backend/v1-scope.md` | Périmètre V1, matrice A/B/C/D (CdC §77), feature flags, conciliation des phases, vérification finale du périmètre, correspondance des 22 livrables demandés par le CdC §77 |
| `docs/backend/actors-and-permissions.md` | Acteurs, modèle multi-organisation, matrice des actions par acteur, matrice de visibilité des données |
| `docs/backend/business-rules.md` | 120 règles métier (BR-…), statut Défini / Déduit / Proposé / À VALIDER |
| `docs/backend/workflows.md` | Parcours de bout en bout ; 15 machines d'état (diagrammes Mermaid et tables de transitions) ; événements de notification |
| `docs/backend/domain-glossary.md` | Glossaire anglais / français |
| `docs/backend/risks-and-open-questions.md` | 25 risques, 19 contradictions entre sources, 77 questions ouvertes, synthèse des questions bloquantes par jour |
| `docs/backend/daily-reports/day-01.md` | Ce rapport |
| `check.md` (racine, fichier créé par l'utilisateur) | Suivi d'avancement : une ligne par jour |

Aucun code applicatif n'a été créé.

## 3. Commandes exécutées et résultats réels

| Commande | Résultat |
|---|---|
| `pdftotext -layout "MadaSource Platform Architecture.pdf" …/scratchpad/spec/spec.txt` | 1 309 lignes extraites (copie dans le scratchpad de session, pas dans le dépôt) |
| `grep -nE '^## (Jour [0-9]+\|Audit [A-D]) — ' roadmap_backend_fastapi.md` | 35 jours + 4 audits, repris dans `check.md` |
| Revue indépendante en lecture seule (agent généraliste appliquant `.claude/agents/code-reviewer.md`) | PRÊT AVEC RÉSERVES, aucun bloquant (section 5) |
| `python3 …/scratchpad/hooktest/check_refs.py` (contrôle des identifiants et des liens, après corrections) | 77 Q, 25 R, 19 SRC, 115 REQ, 10 NFR, 120 BR ; 0 doublon, 0 référence non définie, 0 lien ou ancre cassé |

Jour documentaire : ni tests, ni lint, ni migrations à exécuter.

## 4. Critères de sortie

| Critère (roadmap §5) | État |
|---|---|
| Périmètre implémenté et cohérent | Oui : les 7 livrables couvrent tous les sujets de la consigne ; la revue n'a trouvé aucun bloquant |
| Tests appropriés et résultat connu | Sans objet : jour documentaire, aucun code |
| Migrations et contraintes cohérentes | Sans objet |
| Documentation et `.env.example` à jour | Documentation : oui. `.env.example` : sans objet (créé au Jour 4) |
| Aucun secret ajouté | Oui. La revue a cherché emails, URL, clés et secrets : aucune occurrence |
| Défauts critiques corrigés ou signalés | Oui : tous les constats de la revue ont été traités (section 5) |
| Décisions non définies marquées `À VALIDER` | Oui : 77 questions (Q-01 à Q-77) |

## 5. Revue

**Revue** : agent généraliste appliquant les instructions de l'agent `code-reviewer` du projet, en lecture seule. Elle a confronté les 7 documents au texte du CdC, au planning et aux deux roadmaps.

**Verdict** : PRÊT AVEC RÉSERVES, aucun constat bloquant.

**Points conformes relevés** :
- tous les sujets de la consigne sont présents ;
- références internes valides ;
- toutes les sections du CdC sont citées, sauf le §76 (schéma conceptuel, sans exigence propre) ;
- ni code ni secret.

**Constats traités** : 11 importants et une vingtaine de facultatifs.

1. **Contradiction non signalée dans le CdC.** Le matching (§14) inclut performance historique et taux de réponse, mais le §43 les réserve au « future matching » et le §69 place le matching avancé en Phase 4. Correction : ajout de SRC-16 ; critère passé en `À VALIDER` (Q-32 complétée).
2. **Statuts surévalués.** Des règles marquées « Défini » ont été rétrogradées en « Déduit » ou « Proposé » quand la source ne les écrit pas :
   - transitions de vérification ;
   - condition de création d'une RFQ ;
   - mode de calcul de la validité des quotations ;
   - formule de prix additive ;
   - extension à tout le système du principe de sûreté de l'IA (§46) ;
   - non-dérivation des schémas publics ;
   - atomicité incluant la RFQ ;
   - BR-ORG-01.
3. **Nouvelles contradictions** :
   - SRC-17 : « not monolithic » du §70 contre « monolithe modulaire » de la roadmap ;
   - SRC-18 : feature flags, mode DEMO, i18n et taux de change, classés V1 mais absents de la roadmap backend ;
   - SRC-19 : exceptions antérieures au Trade.
4. **Nouvelles questions** :
   - Q-74 : appartenance multi-organisation, organisation interne MadaSource ;
   - Q-75 : planification des éléments de SRC-18 ;
   - Q-76 : durée de vie des tokens, politique de mot de passe ;
   - Q-77 : tri des résultats de recherche.
5. **Cohérence entre documents** :
   - périmètre de l'inbox (« ou autorisé à répondre », RJ 21) ;
   - renvois Q-NN corrigés, statuts V1 harmonisés ;
   - formats d'identifiants laissés ouverts (Q-37) ;
   - visibilité publique des statuts de vérification négatifs (Q-16) ;
   - interdictions sans source remplacées par Q-40 et Q-41.
6. **Ajouts** :
   - correspondance des 22 livrables du CdC §77 ;
   - mention de la troncature du « Final requirement » dans le PDF ;
   - relations du modèle conceptuel marquées « Proposé ».

**Contrôle après corrections** : script de vérification des identifiants et des liens (section 3), sans erreur. Il n'y a pas eu de seconde revue complète par un agent.

**Recommandations de la revue, reportées aux jours concernés** :
- relecture de la matrice de visibilité par `security-auditor` avant le `security-design.md` du Jour 2 ;
- relecture des relations conceptuelles par `database-reviewer` au Jour 3.

## 6. Décisions À VALIDER les plus structurantes

| Question | Pourquoi c'est structurant | Jour bloqué |
|---|---|---|
| Q-01 | Modèle commercial A, B ou les deux | J24 |
| Q-05 | Traduction du prix négocié en Modèle A, sans révéler la marge | J26 |
| Q-06 | Nature et visibilité de l'« indication de prix » (risque de fuite de marge) | J16, J18 |
| Q-18 | Attributs qualité par catégorie (vanille, girofle, cacao) | J16 |
| Q-41, Q-42 | Acteurs des transitions du Trade et conditions de clôture | J28, J34 |
| Q-53 | Échantillons en V1 ou non | J32 |
| Q-54 | Qui reçoit et qui enregistre le paiement | J33 |
| Q-09, Q-10, Q-25, Q-37, Q-66, Q-67, Q-68, Q-74, Q-75 | À trancher avant les Jours 2 et 3 (architecture, données) | J2, J3 |

## 7. Risques et limites

- Le cahier des charges est hors du dépôt. L'archiver est soumis à l'accord du client (Q-71).
- Les règles « Déduit » et « Proposé » sont des hypothèses de travail : elles ne doivent pas être implémentées comme définitives sans validation.
- Le Jour 2 peut commencer sans les réponses du client, mais les questions de la ligne J2-J3 (section 4.18 de risks-and-open-questions.md) influencent l'architecture et le modèle de données.

## 8. Préparation du Jour 2 (non exécuté)

Jour 2 — Architecture modulaire et conventions API. Livrables :
- `architecture.md` ;
- `module-boundaries.md` ;
- `api-conventions.md` ;
- `error-handling.md` ;
- `testing-strategy.md` ;
- `security-design.md`.

Prérequis :
- documents du Jour 1, présents ;
- de préférence, les réponses à Q-09, Q-10, Q-66, Q-67, Q-74 et Q-75, faute de quoi les choix seront marqués `À VALIDER` ;
- agents `backend-architect` et `security-auditor`, désormais chargés.

Commande : `/daily-delivery 2`, après validation de ce rapport.
