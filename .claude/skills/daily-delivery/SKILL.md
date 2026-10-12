---
name: daily-delivery
description: "Exécute un jour précis de la roadmap backend MadaSource (roadmap_backend_fastapi.md) - lit le prompt du jour, vérifie les prérequis des jours précédents, implémente uniquement ce périmètre, contrôle les critères de sortie et produit le rapport de fin de journée. À utiliser quand l'utilisateur demande d'exécuter le jour N. Ne passe jamais automatiquement au jour suivant."
argument-hint: "<numéro du jour, ex. 3>"
---

# Skill daily-delivery

Jour demandé : $ARGUMENTS

Si aucun numéro n'est fourni, demander lequel. Ne pas deviner.

## Procédure

1. **Lire** :
   - `CLAUDE.md` ;
   - dans `roadmap_backend_fastapi.md` : la section « 1. Prompt permanent », la section « Jour $ARGUMENTS » et la section 5 (« Un jour est terminé seulement si ») ;
   - l'étape correspondante de `planning.md` ;
   - les documents existants de `docs/backend/` et le dernier rapport de `docs/backend/daily-reports/`.
2. **État du dépôt** : `git status` s'il existe un dépôt, arborescence, tests existants. Ne pas recommencer le projet ni remplacer du code existant sans raison.
3. **Prérequis** : pour chaque jour antérieur dont dépend ce jour, vérifier que son livrable existe et est stable (fichiers présents, tests verts s'il y a du code). Si un prérequis échoue, le corriger d'abord ou s'arrêter et le signaler.
4. **Plan court** (15 lignes au plus) : objectifs, fichiers à créer ou modifier, vérifications prévues, ambiguïtés. En cas d'ambiguïté bloquante, poser la question avant d'implémenter.
5. **Implémenter uniquement le périmètre du jour**, avec les skills `fastapi-module`, `database-migrations`, `secure-api` et `docker-ci` selon le besoin. Ce qui dépasse le périmètre est noté pour un jour ultérieur.
6. **Tests** : skill `pytest-workflow` en mode complet en fin de jour, dès qu'il existe du code.
7. **Revue** : skill `code-review-madasource`, plus les agents `security-auditor`, `database-reviewer` ou `devops-engineer` selon le contenu. Corriger les constats bloquants.
8. **Documentation** : `docs/backend/`, README, `.env.example`, et skill `api-documentation` si des endpoints ont changé.
9. **Secrets** : vérifier qu'aucun secret n'a été ajouté.
10. **Critères de sortie** : cocher chacun avec sa preuve.
11. **Rapport** : écrire `docs/backend/daily-reports/day-NN.md` (NN sur deux chiffres) et le résumer à l'utilisateur.
    **Suivi** : mettre à jour `check.md` à la racine. Passer la ligne du jour à `OK`, `OK avec réserves` ou `Non terminé`, avec la date et un résumé de 1 à 3 lignes de ce qui est terminé, et un lien vers le rapport. Ne marquer `OK` que si tous les critères de sortie sont cochés.
12. **Jour suivant** : lister ses prérequis et les questions ouvertes, **sans l'exécuter**. Attendre la validation explicite de l'utilisateur.

## Critères de sortie (roadmap, section 5)

- [ ] Le périmètre est implémenté et cohérent.
- [ ] Les tests appropriés existent et leur résultat est connu (ou « sans objet » justifié pour un jour documentaire).
- [ ] Les migrations et contraintes sont cohérentes (ou « sans objet »).
- [ ] La documentation et `.env.example` sont à jour.
- [ ] Aucun secret n'a été ajouté au dépôt.
- [ ] Les défauts critiques sont corrigés ou explicitement signalés.
- [ ] Les décisions métier non définies sont marquées `À VALIDER`.

## Modèle de rapport (`docs/backend/daily-reports/day-NN.md`)

```markdown
# Jour N — <titre>

Date : AAAA-MM-JJ · Statut : TERMINÉ | TERMINÉ AVEC RÉSERVES | NON TERMINÉ

## Objectif du jour
## Fichiers créés et modifiés
## Commandes exécutées et résultats réels
## Critères de sortie
## Décisions À VALIDER
## Risques et limites
## Préparation du jour N+1 (non exécuté)
```

## Interdits

- Enchaîner sur le jour suivant sans validation.
- Élargir le périmètre du jour.
- Annoncer un résultat qui n'a pas été obtenu.
- Modifier la roadmap ou le planning sans validation.
