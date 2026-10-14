"""Base déclarative SQLAlchemy 2.x (architecture.md D-07, D-15 ; indexes-and-constraints.md §1).

- Convention de nommage des contraintes et des index : des noms stables, sur lesquels
  s'appuient les migrations et la traduction des violations d'intégrité.
- Types par défaut des annotations : `datetime` → `timestamptz` ; `uuid.UUID` → `uuid`.
  Pour un montant, SQLAlchemy associerait `Decimal` à `Numeric()` sans précision : chaque
  colonne déclare donc `Numeric(p, s)` explicitement (D-14 ; précision : Q-08), et le test
  de politique du schéma refuse un `Numeric` sans précision.
- Identifiants : UUIDv7 générés par l'application (D-15, retenu le 2026-10-14).

Les modèles des modules héritent de `Base` ; aucun n'existe encore au Jour 6.
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
}


def new_id() -> uuid.UUID:
    """Identifiant technique : UUIDv7, ordonné dans le temps (D-15).

    Il révèle l'instant de création, rien d'autre (C30) ; la protection reste le contrôle
    d'accès. Généré par l'application, il est connu avant l'insertion.
    """
    return uuid.uuid7()


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        datetime: DateTime(timezone=True),
        uuid.UUID: Uuid(as_uuid=True, native_uuid=True),
    }


class UUIDPrimaryKeyMixin:
    """Clé primaire `id` de type uuid, valeur fixée par l'application (UUIDv7)."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_id)
