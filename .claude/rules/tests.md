---
paths:
  - "backend/tests/**"
---

# Règles pour les tests

- Arborescence : `unit/` (sans base ni HTTP), `integration/` (base PostgreSQL de test isolée), `api/` (client HTTP de test), `e2e/` (parcours complets, Audit A). Base de test éphémère ; aucune base persistante n'est réinitialisée (`docs/backend/testing-strategy.md` §4).
- Ne jamais affaiblir une assertion, ajouter `skip`/`xfail` ou supprimer un test pour obtenir un passage. Modifier une attente seulement si elle est fausse, et le justifier.
- Chaque endpoint privé est testé pour : 401, 403, ressource d'une autre organisation, succès, absence des champs privés dans la réponse.
- Chaque machine d'état est testée : toutes les transitions permises et les transitions interdites représentatives.
- Les dates des tests sont timezone-aware et contrôlées (horloge injectée ou figée), sans dépendre de l'heure réelle.
- Les montants sont comparés en `Decimal`, jamais en `float`.
- Données factices identifiables (préfixe `test-`, domaine `example.com`). Aucune donnée réelle d'entreprise ou de personne, aucun appel réseau externe.
- Ne jamais pointer les tests vers une base de développement partagée ou de production.
