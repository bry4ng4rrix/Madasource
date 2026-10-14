"""Modules métier (module-boundaries.md §2), un sous-paquet par module.

Chaque module est créé au jour de son implémentation, jamais à l'avance. Ce paquet existe
dès le Jour 7 pour que le contrôle des frontières (`lint-imports`, contrat « modules »)
s'applique à tout module ajouté : niveau déclaré, dépendances vers les niveaux inférieurs.
"""
