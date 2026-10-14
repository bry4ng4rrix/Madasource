"""Frontières entre modules (module-boundaries.md §3, §6 et §9 ; architecture.md D-07).

`lint-imports` vérifie les couches et les niveaux. Ces tests ajoutent deux règles qu'il ne
couvre pas :
- un module n'importe d'un autre module que son interface publique, c'est-à-dire exactement
  `app.modules.<module>.service`, `.contracts` ou `.projections`
  (`.claude/rules/backend-python.md`) ;
- toute table appartient à un module, et une clé étrangère ne pointe que vers une table d'un
  module de niveau **inférieur** : ni supérieur, ni de même niveau (modules indépendants).

Les niveaux sont lus dans la configuration d'import-linter (`pyproject.toml`), seule
configuration exécutée, puis comparés à la table de module-boundaries.md §2. Chaque règle
est aussi testée sur un cas fabriqué qui la viole.
"""

import re
import sys
import tomllib
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import grimp
import pytest
from sqlalchemy import Column, ForeignKey, MetaData, Table, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.db.registry import MODULES_PACKAGE, import_all_models

pytestmark = pytest.mark.unit

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"
# L'ajout de `ports`, que suggère module-boundaries.md §5.2, est à valider (Q-104 c).
PUBLIC_SUBMODULES = frozenset({"service", "contracts", "projections"})
_PUBLIC_DEPTH = len(MODULES_PACKAGE.split(".")) + 2  # app.modules.<module>.<sous-module>

# module-boundaries.md §2 : une permutation de niveaux dans le contrat serait détectée.
EXPECTED_LEVELS = {
    "audit": 1,
    "auth": 2,
    "organizations": 3,
    "access_control": 4,
    "notifications": 5,
    "documents": 6,
    "messages": 7,
    "buyers": 8,
    "verification": 8,
    "exporters": 9,
    "products": 10,
    "rfqs": 11,
    "quotations": 12,
    "negotiations": 13,
    "trades": 14,
    "payment_records": 15,
    "shipments": 15,
    "samples": 15,
    "exceptions": 16,
    "reviews": 17,
    "matching": 18,
    "marketplace": 19,
    "admin": 20,
}


def _contract(contract_id: str) -> dict[str, Any]:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    contracts: list[dict[str, Any]] = config["tool"]["importlinter"]["contracts"]
    [contract] = [c for c in contracts if c["id"] == contract_id]
    return contract


def module_levels() -> dict[str, int]:
    """Niveau de chaque module métier, d'après le contrat « modules » d'import-linter."""
    layers: list[str] = _contract("modules")["layers"]
    levels: dict[str, int] = {}
    for position, layer in enumerate(layers):
        # `|` : modules indépendants ; `:` : modules de même couche non indépendants.
        for name in re.split(r"[|:]", layer):
            levels[name.strip().strip("()")] = len(layers) - position
    return levels


def _module_of(dotted: str) -> str | None:
    parts = dotted.split(".")
    if dotted.startswith(MODULES_PACKAGE + ".") and len(parts) >= _PUBLIC_DEPTH - 1:
        return parts[_PUBLIC_DEPTH - 2]
    return None


def _is_public_interface(dotted: str) -> bool:
    parts = dotted.split(".")
    return len(parts) == _PUBLIC_DEPTH and parts[-1] in PUBLIC_SUBMODULES


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
            if not _is_public_interface(imported):
                violations.append((importer, imported))
    return violations


def table_owners(models_modules: Iterable[ModuleType]) -> dict[str, str]:
    """Module propriétaire de chaque table déclarée dans un `models.py`.

    Une table appartient au module dont le `models.py` la définit : classe mappée définie
    dans ce fichier, ou objet `Table` brut (table d'association, par exemple) déclaré au
    niveau du fichier. Une classe importée d'un autre fichier n'est pas attribuée ; un
    `Table` importé d'un autre module serait déjà refusé par le contrôle des imports.
    """
    owners: dict[str, str] = {}
    for models in models_modules:
        module = _module_of(models.__name__)
        if module is None:
            continue
        for value in vars(models).values():
            if isinstance(value, Table):
                owners[value.name] = module
            elif isinstance(value, type) and value.__module__ == models.__name__:
                table = getattr(value, "__table__", None)
                if isinstance(table, Table):
                    owners[table.name] = module
    return owners


def tables_without_owner(tables: Iterable[Table], owners: Mapping[str, str]) -> list[str]:
    return sorted(table.name for table in tables if table.name not in owners)


def forbidden_foreign_keys(
    tables: Iterable[Table], owners: Mapping[str, str], levels: Mapping[str, int]
) -> list[str]:
    """Clés étrangères vers une table d'un module de niveau supérieur ou égal."""
    violations: list[str] = []
    for table in tables:
        source = owners.get(table.name)
        for foreign_key in table.foreign_keys:
            target = owners.get(foreign_key.column.table.name)
            if source is None or target is None or source == target:
                continue
            if levels[target] >= levels[source]:
                violations.append(f"{table.name} ({source}) -> {foreign_key.target_fullname}")
    return sorted(violations)


def _fake_models_module(
    module: str, *, defined: Mapping[str, object], imported: Mapping[str, object] | None = None
) -> ModuleType:
    """`app.modules.<module>.models` fabriqué : `defined` y est défini, `imported` importé."""
    fake = ModuleType(f"{MODULES_PACKAGE}.{module}.models")
    for name, value in defined.items():
        if isinstance(value, type):
            value.__module__ = fake.__name__
        setattr(fake, name, value)
    for name, value in (imported or {}).items():
        setattr(fake, name, value)
    return fake


def test_levels_follow_module_boundaries() -> None:
    contract = _contract("modules")

    assert contract["type"] == "layers"
    assert contract["containers"] == [MODULES_PACKAGE]
    assert contract["exhaustive"] is True
    assert module_levels() == EXPECTED_LEVELS


def test_modules_import_only_public_interfaces_of_other_modules() -> None:
    graph = grimp.build_graph("app", cache_dir=None)

    assert forbidden_cross_module_imports(graph) == []


def test_import_of_anything_but_a_public_interface_is_detected() -> None:
    importer = "app.modules.rfqs.service"
    imported = [
        "app.modules.audit.service",  # interface publique : permis
        "app.modules.audit.contracts",  # interface publique : permis
        "app.modules.rfqs.models",  # même module : permis
        "app.modules.audit.models",
        "app.modules.audit",  # paquet du module
        "app.modules.audit.service.helpers",  # sous-paquet d'une interface publique
        "app.modules.access_control.ports",  # Q-104 c
    ]
    graph = grimp.ImportGraph()
    graph.add_module(importer)
    for name in imported:
        graph.add_module(name)
        graph.add_import(importer=importer, imported=name)

    assert forbidden_cross_module_imports(graph) == [
        (importer, "app.modules.access_control.ports"),
        (importer, "app.modules.audit"),
        (importer, "app.modules.audit.models"),
        (importer, "app.modules.audit.service.helpers"),
    ]


def test_every_table_belongs_to_a_module_and_points_only_to_lower_levels() -> None:
    owners = table_owners(sys.modules[name] for name in import_all_models())
    tables = Base.metadata.tables.values()

    assert tables_without_owner(tables, owners) == []
    assert forbidden_foreign_keys(tables, owners, module_levels()) == []


def test_ownership_and_forbidden_foreign_keys_are_detected() -> None:
    class _ProbeBase(DeclarativeBase):
        metadata = MetaData()

    class _Rfq(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_rfqs"

    class _AuditEntry(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_audit_entries"

        rfq_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("probe_rfqs.id"))

    class _VerificationRecord(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_verification_records"

        audit_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("probe_audit_entries.id"))

    class _BuyerProfile(UUIDPrimaryKeyMixin, _ProbeBase):
        __tablename__ = "probe_buyer_profiles"

        verification_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("probe_verification_records.id")
        )

    audit_rfq_links = Table(
        "probe_audit_rfq_links",
        _ProbeBase.metadata,
        Column("rfq_id", Uuid, ForeignKey("probe_rfqs.id"), primary_key=True),
    )
    Table("probe_orphans", _ProbeBase.metadata, Column("id", Uuid, primary_key=True))

    modules = [
        _fake_models_module("rfqs", defined={"Rfq": _Rfq}),
        _fake_models_module(
            "audit",
            defined={"AuditEntry": _AuditEntry, "audit_rfq_links": audit_rfq_links},
            imported={"Rfq": _Rfq},
        ),
        _fake_models_module("verification", defined={"VerificationRecord": _VerificationRecord}),
        _fake_models_module("buyers", defined={"BuyerProfile": _BuyerProfile}),
    ]
    owners = table_owners(modules)
    tables = _ProbeBase.metadata.tables.values()

    assert owners == {
        "probe_rfqs": "rfqs",
        "probe_audit_entries": "audit",
        "probe_audit_rfq_links": "audit",
        "probe_verification_records": "verification",
        "probe_buyer_profiles": "buyers",
    }
    assert tables_without_owner(tables, owners) == ["probe_orphans"]
    # verification (8) -> audit (1) est permis ; les trois autres sont refusés.
    assert forbidden_foreign_keys(tables, owners, module_levels()) == [
        "probe_audit_entries (audit) -> probe_rfqs.id",
        "probe_audit_rfq_links (audit) -> probe_rfqs.id",
        "probe_buyer_profiles (buyers) -> probe_verification_records.id",
    ]
