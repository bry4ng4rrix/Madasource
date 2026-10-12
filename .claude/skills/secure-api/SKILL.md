---
name: secure-api
description: "Procédure et checklist pour sécuriser un endpoint ou un module de l'API MadaSource - identité, organisation, permission, appartenance de la ressource (anti-IDOR/BOLA), séparation des schémas public/privé/admin, validation d'entrée, audit et tests d'accès refusé. À utiliser pendant l'implémentation de tout endpoint privé ou admin, et avant de clore un jour qui ajoute des endpoints."
argument-hint: "<module ou endpoint>"
---

# Skill secure-api

Cible : $ARGUMENTS

## Modèle d'accès (rappel)

Organization → Membership (utilisateur, organisation, rôle) → Role → Permissions (CdC §53-54).
Rôles actifs en V1 : Buyer, Exporter, MadaSource Admin. Les rôles futurs (Operations, Compliance, Finance, Logistics, Super Admin, Partner) sont préparés mais inactifs.
Le mécanisme exact sera fixé au Jour 9 dans `docs/backend/security-design.md`. Dès qu'il existe, ce document prime sur ce rappel.

## Procédure pour chaque endpoint

1. **Classer** l'endpoint : public, authentifié, organisation ou admin.
2. **Authentification** : dépendance « utilisateur courant », compte dans un statut autorisé, token valide et non révoqué.
3. **Permission** : dépendance du type `require_permission("<ressource>:<action>")` (S-11). Pas de `if user.is_admin` dispersé dans le code. Permissions admin par ensembles (lecture financière, données bancaires, confirmation de paiement…, S-12).
3 bis. **Politique d'accès** : (acteur, action, ressource) → **audience** ou refus (S-28, S-29). Pour un document ou une conversation, P-01 renvoie l'audience du contexte ; l'audience propre du document ou de la version s'applique en plus (S-24). En Modèle A, acheteur et exportateur ne reçoivent pas les mêmes termes (S-39).
4. **Appartenance (BOLA)** : charger la ressource avec le filtre d'organisation dans la requête elle-même (`WHERE id = :id AND organization_id = :org_id`), ou vérifier la participation (RFQ adressée à cet exportateur, organisation partie au Trade). Code de réponse en cas d'échec : celui de `api-conventions.md` (404 recommandé pour ne pas révéler l'existence d'une ressource, `À VALIDER` au Jour 2).
5. **Entrée** : schéma Pydantic avec `extra="forbid"`. Les champs fixés par le serveur (`id`, `organization_id`, `status`, `created_by`, marge, niveau de vérification) ne sont jamais acceptés du client. Bornes explicites : longueurs, quantités > 0, précision `Decimal`.
4 bis. **Identifiants indirects** : tout identifiant reçu dans le corps ou les paramètres (document joint, produit cité, offre visée) passe par la même politique, avec l'action précise : lire, rattacher ou partager. Les collections imbriquées sont filtrées élément par élément (S-14).
6. **Sortie** : schéma de l'audience retournée par la politique, instancié explicitement, jamais d'union de schémas (D-32). Ensemble exact des clés vérifié. Aucune combinaison de valeurs ne permet de recalculer une composante de prix cachée (S-19). Aucun tri ni filtre sur un champ invisible pour l'audience (S-20).
7. **Transitions** : passer par le service, qui vérifie que cet acteur peut effectuer cette transition dans cet état.
8. **Audit** : une action sensible produit un événement d'audit (acteur, action, ressource, ancienne et nouvelle valeur), sans secret.
9. **Limites** : pagination bornée (taille maximale de page), taille de requête, rate limiting sur les endpoints d'authentification.
10. **Erreurs** : aucun détail interne dans les réponses (stack trace, SQL, existence d'un compte).

## Champs sensibles MadaSource

Ne jamais les exposer hors du rôle autorisé (CdC §11, §17, §61) :

- `password_hash` et tous les tokens (accès, refresh, reset, vérification d'email) ;
- informations bancaires et de paiement de l'exportateur, informations fiscales ;
- documents d'immatriculation, documents privés et clés de stockage ;
- prix net fournisseur, coûts externes (visibilité `À VALIDER`), marge MadaSource, commission ;
- notes internes, notes de vérification, notes admin ;
- coordonnées privées (le profil public n'expose qu'une localisation générale) ;
- communications privées.

## Tests obligatoires pour chaque endpoint privé

- 401 sans token.
- 403 avec un rôle qui n'a pas la permission.
- Ressource d'une autre organisation : 404 ou 403 selon la convention.
- Succès avec le bon rôle et la bonne organisation.
- Champs sensibles absents de la réponse.
- Champ réservé au serveur envoyé par le client : rejeté (422).

## Interdits

- Désactiver une vérification pour faire passer un test.
- Utiliser un compte admin dans les tests pour contourner une permission.
- Journaliser un token, un mot de passe ou des données bancaires.

## Résultat attendu

Tableau par endpoint : méthode | chemin | niveau | permission | contrôle d'appartenance | schéma de sortie | audit | tests présents (oui/non).
Puis la liste des écarts. Pour un audit approfondi, passer la main à l'agent `security-auditor`.
