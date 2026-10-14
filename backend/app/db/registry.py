"""Découverte des modèles pour Alembic et pour les contrôles du schéma.

Chaque module métier déclare ses tables dans `app/modules/<module>/models.py`. Importer
ces fichiers enregistre leurs tables dans `Base.metadata` ; l'autogénération d'Alembic
compare ensuite ces métadonnées à la base. Aucun module n'existe au Jour 6 : la liste
des modules importés est vide, et c'est attendu.
"""

import importlib
import importlib.util
import pkgutil

from sqlalchemy import MetaData

from app.db.base import Base

MODULES_PACKAGE = "app.modules"


def import_all_models() -> list[str]:
    """Importe tous les `app.modules.<module>.models` existants ; renvoie leurs noms."""
    try:
        package = importlib.import_module(MODULES_PACKAGE)
    except ModuleNotFoundError as exc:
        if exc.name != MODULES_PACKAGE:
            raise
        return []
    imported: list[str] = []
    for module in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if not module.ispkg:
            continue
        name = f"{MODULES_PACKAGE}.{module.name}.models"
        if importlib.util.find_spec(name) is not None:
            importlib.import_module(name)
            imported.append(name)
    return imported


def load_metadata() -> MetaData:
    """Métadonnées complètes de l'application, après import de tous les modèles."""
    import_all_models()
    return Base.metadata
