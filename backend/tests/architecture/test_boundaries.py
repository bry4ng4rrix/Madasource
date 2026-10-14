"""Frontières entre modules (module-boundaries.md §3 et §9 ; architecture.md D-07).

`lint-imports` vérifie les couches et les niveaux. Ces tests ajoutent deux règles qu'il ne
couvre pas :
- un module n'importe d'un autre module que son interface publique (`service`,
  `contracts`, `projections`, `ports`) ;
- une clé étrangère ne pointe jamais vers une table d'un module de niveau supérieur.

Les niveaux sont lus dans la configuration d'import-linter (`pyproject.toml`), seule
source de vérité. Chaque règle est aussi testée sur un cas fabriqué qui la viole.
"""

import tomllib
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path

import grimp
import pytest
from sqlalchemy import ForeignKey, MetaData, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.registry import import_all_models

pytestmark = pytest.mark.unit

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"
MODULES_PACKAGE = "app.modules"
PUBLIC_SUBMODULES = frozenset({"service", "contracts", "projections", "ports"})


def module_levels() -> dict[str, int]:
    """Niveau de chaque module métier, d'après le contrat « modules » d'import-linter."""
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    [contract] = [c for c in config["tool"]["importlinter"]["contracts"] if c["id"] == "modules"]
    layers: list[str] = contract["layers"]
    levels: dict[str, int] = {}
    for position, layer in enumerate(layers):
        for name in layer.split("|"):
            levels[name.strip().strip("()")] = len(layers) - position
    return levels


def _module_of(dotted: str) -> str | None:
    parts = dotted.split(".")
    if dotted.startswith(MODULES_PACKAGE + ".") and len(parts) >= 3:
        return parts[2]
    return None


def forbidden_cross_module_imports(graph: grimp.ImportGraph) -> list[tuple[str, str]]:
    """Imports d'un module vers un autre module qui ne visent pas son interface publique."""
    violations: list[tuple[str, str]] = []
    for importer in sorted(graph.modules):
        source = _module_of(importer)
        if source is None:
            continue
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            target = _module_of(imported)
            if target is None or target == source:
                continue
            submodule = imported.split(".")[3] if len(imported.split(".")) > 3 else None
            if submodule not in PUBLIC_SUBMODULES:
                violations.append((importer, imported))
    return violations


def upward_foreign_keys(
    tables: Iterable[Table], module_of_table: Mapping[str, str], levels: Mapping[str, int]
) -> list[str]:
    """Clés étrangères qui pointent vers une table d'un module de niveau supérieur."""
    violations: list[str] = []
    for table in tables:
        source = module_of_table.get(table.name)
        for foreign_key in table.foreign_keys:
            target = module_of_table.get(foreign_key.column.table.name)
            if source is None or target is None or source == target:
                continue
            if levels[target] > levels[source]:
                violations.append(f"{table.name} ({source}) -> {foreign_key.target_fullname}")
    return violations


def _module_of_tables(base: type[DeclarativeBase]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for mapper in base.registry.mappers:
        module = _module_of(mapper.class_.__module__)
        if module is not None and isinstance(mapper.local_table, Table):
            mapping[mapper.local_table.name] = module
    return mapping


def test_levels_follow_module_boundaries() -> None:
    levels = module_levels()

    assert len(levels) == 23
    assert levels["audit"] == 1
    assert levels["admin"] == 20
    assert levels["buyers"] == levels["verification"] == 8
    assert levels["payment_records"] == levels["shipments"] == levels["samples"] == 15


def test_modules_import_only_public_interfaces_of_other_modules() -> None:
    graph = grimp.build_graph("app")

    assert forbidden_cross_module_imports(graph) == []


def test_internal_import_of_another_module_is_detected() -> None:
    graph = grimp.ImportGraph()
    for name in (
        "app.modules.rfqs.service",
        "app.modules.audit.service",
        "app.modules.audit.models",
        "app.modules.access_control.ports",
    ):
        graph.add_module(name)
    graph.add_import(importer="app.modules.rfqs.service", imported="app.modules.audit.service")
    graph.add_import(importer="app.modules.rfqs.service", imported="app.modules.audit.models")
    graph.add_import(
        importer="app.modules.rfqs.service", imported="app.modules.access_control.ports"
    )

    assert forbidden_cross_module_imports(graph) == [
        ("app.modules.rfqs.service", "app.modules.audit.models")
    ]


def test_foreign_keys_point_only_to_lower_levels() -> None:
    import_all_models()

    assert (
        upward_foreign_keys(Base.metadata.tables.values(), _module_of_tables(Base), module_levels())
        == []
    )


def test_upward_foreign_key_is_detected() -> None:
    class _ProbeBase(DeclarativeBase):
        metadata = MetaData()

    class _Rfq(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_rfqs"

    class _AuditEntry(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_audit_entries"

        rfq_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("probe_rfqs.id"))

    module_of_table = {"probe_rfqs": "rfqs", "probe_audit_entries": "audit"}

    violations = upward_foreign_keys(
        _ProbeBase.metadata.tables.values(), module_of_table, module_levels()
    )

    assert violations == ["probe_audit_entries (audit) -> probe_rfqs.id"]
