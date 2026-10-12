---
name: code-review-madasource
description: "Revue de code en lecture seule des changements du backend MadaSource, exécutée par l'agent code-reviewer dans un contexte séparé. Présente les problèmes par gravité avec preuves fichier:ligne. À utiliser après chaque lot de développement et avant de clore un jour. Distinct de la commande intégrée /code-review, qui reste disponible."
argument-hint: "[fichiers, module ou jour]"
context: fork
agent: code-reviewer
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff *)
  - Bash(git status *)
  - Bash(git log *)
  - Bash(git show *)
---

# Revue de code MadaSource (lecture seule)

Périmètre demandé : $ARGUMENTS

Tu ne modifies aucun fichier pendant cette revue.

## Détermination du périmètre

1. Si un périmètre est donné ci-dessus, l'utiliser.
2. Sinon, s'il existe un dépôt Git : `git status`, `git diff`, `git diff --staged`.
3. Sinon : fichiers modifiés depuis moins de 24 h sous `backend/`, `docs/backend/`, `.claude/` et à la racine (`find … -mmin -1440 -type f`), en excluant `.venv`, les caches et `__pycache__`. Indiquer clairement dans le rapport que le périmètre a été déduit ainsi.

## Procédure

1. Lire `CLAUDE.md` et les règles de `.claude/rules/` qui s'appliquent aux fichiers du périmètre.
2. Lire chaque fichier modifié en entier, ainsi que ses appelants directs si un contrat (signature, schéma, endpoint) change.
3. Appliquer la checklist de l'agent `code-reviewer` : correction, régressions, conventions MadaSource, sécurité évidente, base de données, simplicité, tests.
4. Vérifier que les tests associés existent. Si possible, lancer ceux du module et rapporter le résultat réel.
5. Pour chaque problème : preuve (extrait de code ou raisonnement concret), impact, correction proposée.

## Règles

- Pas de faux positif : un constat incertain est marqué « à confirmer », avec ce qu'il faudrait vérifier.
- Pas de remarque de pur style déjà couverte par Ruff.
- Pour les documents (jours documentaires) : vérifier la cohérence avec les sources (CdC, planning, roadmap), les contradictions internes, les règles inventées au lieu d'être marquées `À VALIDER`.

## Résultat attendu

Le format de rapport de l'agent `code-reviewer` : Verdict, Bloquant, Important, Facultatif, Commandes exécutées, Revues spécialisées recommandées.
