"""Base déclarative : convention de nommage, types par défaut, identifiants UUIDv7."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Numeric, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateTable

from app.db.base import NAMING_CONVENTION, Base, UUIDPrimaryKeyMixin, new_id
from app.db.registry import import_all_models, load_metadata

pytestmark = pytest.mark.unit


class _ProbeBase(DeclarativeBase):
    """Base isolée : les tables d'essai n'entrent pas dans les métadonnées de l'application."""

    metadata = Base.metadata.__class__(naming_convention=NAMING_CONVENTION)
    type_annotation_map = Base.type_annotation_map


class _Parent(UUIDPrimaryKeyMixin, _ProbeBase):
    __tablename__ = "probe_parents"

    code: Mapped[str] = mapped_column(String(16), unique=True)
    created_at: Mapped[datetime]


class _Child(UUIDPrimaryKeyMixin, _ProbeBase):
    __tablename__ = "probe_children"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        Index(None, "parent_id", "status"),
    )

    parent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("probe_parents.id"))
    status: Mapped[str] = mapped_column(String(16))
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4))


PARENT = _ProbeBase.metadata.tables["probe_parents"]
CHILD = _ProbeBase.metadata.tables["probe_children"]


def test_new_id_is_a_time_ordered_uuid7() -> None:
    first, second = new_id(), new_id()

    assert first.version == 7
    assert first < second


def test_constraint_names_follow_the_project_convention() -> None:
    ddl = str(CreateTable(CHILD).compile())
    names = {constraint.name for constraint in CHILD.constraints}
    indexes = {index.name for index in CHILD.indexes}

    assert names == {
        "pk_probe_children",
        "fk_probe_children_parent_id_probe_parents",
        "ck_probe_children_amount_non_negative",
    }
    assert indexes == {"ix_probe_children_parent_id_status"}
    assert "CONSTRAINT ck_probe_children_amount_non_negative CHECK" in ddl
    assert {c.name for c in PARENT.constraints} >= {"uq_probe_parents_code"}


def test_annotations_map_to_timestamptz_and_uuid() -> None:
    created_at = PARENT.c.created_at.type
    identifier = PARENT.c.id.type

    assert isinstance(created_at, DateTime)
    assert created_at.timezone is True
    assert isinstance(identifier, Uuid)


def test_primary_key_is_generated_by_the_application() -> None:
    column = PARENT.c.id

    assert column.primary_key
    assert column.server_default is None
    assert column.default is not None


def test_no_module_is_registered_yet() -> None:
    # Jour 6 : aucun modèle métier (roadmap : pas de tables prématurées).
    assert import_all_models() == []
    assert load_metadata().tables == {}


def test_application_schema_type_policy() -> None:
    """Garde-fou pour les modèles futurs : D-13 (temps), D-14 (montants), D-15 (clés)."""
    for table in load_metadata().tables.values():
        for column in table.columns:
            assert not isinstance(column.type, Float), f"{table.name}.{column.name} : float"
            if isinstance(column.type, Numeric):
                assert column.type.precision is not None, f"{table.name}.{column.name}"
                assert column.type.scale is not None, f"{table.name}.{column.name}"
            if isinstance(column.type, DateTime):
                assert column.type.timezone, f"{table.name}.{column.name} : datetime naïf"
