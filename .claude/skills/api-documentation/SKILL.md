---
name: api-documentation
description: "Maintient la documentation de l'API REST MadaSource (endpoints, permissions, schémas, erreurs, exemples) et vérifie sa cohérence avec l'implémentation réelle et le schéma OpenAPI généré par FastAPI. À utiliser après l'ajout ou la modification d'endpoints, et avant de clore un jour qui change le contrat d'API."
argument-hint: "[module]"
---

# Skill api-documentation

Module : $ARGUMENTS (par défaut : tous les modules modifiés)

## Sources

- Implémentation : `backend/app/modules/<module>/router.py` et `schemas.py`.
- OpenAPI généré par FastAPI : chemin exact fixé au Jour 5 (par exemple `/api/v1/openapi.json`), ou export hors ligne via l'application factory.
- Conventions : `docs/backend/api-conventions.md` et `docs/backend/error-handling.md` (Jour 2).

## Où documenter

- `docs/backend/api/<module>.md` : un fichier par module, créé seulement quand le module existe.
- Dans le code : `summary`, `description`, `tags` et `responses` (erreurs) sur les routes ; exemples dans les schémas Pydantic (`Field(examples=[...])` ou `model_config["json_schema_extra"]`).

## Procédure

1. Lister les endpoints réels à partir du router et du schéma OpenAPI.
2. Pour chaque endpoint, documenter :
   - méthode et chemin ;
   - permission ou rôle requis ;
   - paramètres de chemin et de requête (pagination, filtres) ;
   - corps de requête (schéma) ;
   - réponses : succès et erreurs, avec codes et format d'erreur standard ;
   - un exemple de requête et de réponse avec des données factices clairement marquées.
3. Comparer la documentation et le code : endpoints manquants ou obsolètes, champs divergents, codes d'erreur non documentés.
4. Vérifier qu'aucun exemple de réponse publique, Buyer ou Exporter ne contient de champ privé (marge, coût fournisseur, banque, notes internes), ni de secret ou de donnée réelle.
5. Mettre à jour la documentation et les métadonnées FastAPI.

## Modèle d'entrée

```markdown
### `POST /api/v1/<ressource>` — <action>

- Permission : `<module>:<action>` (<rôle>)
- Corps : `<Schema>Create`
- Réponses : `201` `<Schema>Read` · `401` · `403` · `422` · `409` (<cas>)
- Notes : <règles métier, transitions, À VALIDER>
```

## Interdits

- Documenter un endpoint inexistant comme disponible, ou un module futur comme actif.
- Utiliser des données réelles (entreprises, personnes, prix) dans les exemples.

## Résultat attendu

| Endpoint | Code | OpenAPI | Documentation | Écart |
|---|---|---|---|---|

Puis la liste des fichiers mis à jour.
