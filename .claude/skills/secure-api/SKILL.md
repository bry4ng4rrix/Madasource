---
name: secure-api
description: "Procédure et checklist pour sécuriser un endpoint ou un module de l'API MadaSource - identité, organisation, permission, appartenance de la ressource (anti-IDOR/BOLA), séparation des schémas public/privé/admin, validation d'entrée, audit et tests d'accès refusé. À utiliser pendant l'implémentation de tout endpoint privé ou admin, et avant de clore un jour qui ajoute des endpoints."
argument-hint: "<module ou endpoint>"
---

# Skill secure-api

Cible : $ARGUMENTS

## Modèle d'accès (rappel)

Organization → Membership (utilisateur, organisation) → attribution des rôles (`access_control`) → Role → Permissions (CdC §53-54).
Rôles actifs en V1 : Buyer, Exporter, MadaSource Admin. Les rôles futurs (Operations, Compliance, Finance, Logistics, Super Admin, Partner) sont préparés mais inactifs.
Référence : `docs/backend/security-design.md` (Jour 2, complété aux Jours 8 à 12). Ce document prime sur ce rappel.

## Procédure pour chaque endpoint

1. **Classer** l'endpoint : public, authentifié, organisation ou admin. Toute route est privée sauf déclaration explicite (S-13).
2. **Authentification** : acteur courant (`access_control`), session valide et non révoquée, statut de compte de l'organisation qui permet l'action (D-28). Pour une permission admin, la session doit porter le second facteur vérifié si Q-80 l'impose (S-09).
3. **Permission** : dépendance du type `require_permission("<ressource>:<action>")` (S-11). Pas de `if user.is_admin` dispersé dans le code. Permissions admin par ensembles : lecture financière, données bancaires, confirmation de paiement… (S-12).
4. **Politique d'accès** : (acteur, action, ressource) → **audience** ou refus (S-28, S-29). Pour un document ou une conversation, P-01 renvoie l'audience du contexte, et l'audience propre du document ou de la version s'applique en plus (S-24). En Modèle A, acheteur et exportateur ne reçoivent pas les mêmes termes (S-39).
5. **Appartenance (BOLA)** : charger la ressource avec le filtre d'organisation ou de participation dans la requête elle-même (`get_for_actor`). En cas de refus : **404**, identique à une ressource inexistante (D-25, S-15).
6. **Identifiants indirects** : tout identifiant reçu dans le corps ou les paramètres (document joint, produit cité, offre visée) passe par la même politique, avec l'action précise : lire, rattacher ou partager. Les collections imbriquées sont filtrées élément par élément (S-14).
7. **Entrée** : schéma Pydantic avec `extra="forbid"`. Les champs fixés par le serveur (`id`, `organization_id`, `status`, `created_by`, marge, niveau de vérification) ne sont jamais acceptés du client (S-38). Bornes explicites : longueurs, quantités > 0. Montants en chaînes seulement (D-14).
8. **Sortie** : schéma de l'audience retournée par la politique, instancié explicitement, jamais d'union de schémas (D-32). Ensemble exact des clés vérifié. Aucune combinaison de valeurs ne permet de recalculer une composante de prix cachée (S-19). Aucun tri ni filtre sur un champ invisible pour l'audience (S-20).
9. **Transitions** : passer par le service, qui vérifie que cet acteur peut effectuer cette transition dans cet état.
10. **Audit** : une action sensible produit un événement d'audit (acteur, action, ressource, ancienne et nouvelle valeur filtrées), sans secret. Les refus de sécurité sont enregistrés après l'annulation de la transaction (D-29).
11. **Limites** : pagination bornée, taille de requête, limites de débit sur les endpoints d'authentification et les flux métier sensibles (S-55).
12. **Erreurs** : aucun détail interne dans les réponses (trace, SQL, existence d'un compte, montant ou seuil caché).

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
