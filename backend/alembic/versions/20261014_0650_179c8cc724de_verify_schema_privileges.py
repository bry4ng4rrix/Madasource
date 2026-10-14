"""verify schema privileges

Vérifie que le socle des droits (révision 03d1bd152b99) a réellement pris effet.

Exécutés par un rôle qui n'est ni superutilisateur ni membre de `pg_database_owner`,
`REVOKE` et `GRANT` sur le schéma `public` ne lèvent qu'un avertissement : la migration
précédente serait enregistrée sans effet. Cette révision échoue alors explicitement, ce
qui annule toute la montée de version (une seule transaction). Constat I1 de la relecture
base de données du Jour 6 ; révision distincte, car la précédente était déjà appliquée.

Risque : nul (lecture seule). Retour arrière : sans objet (aucune modification).

Revision ID: 179c8cc724de
Revises: 03d1bd152b99
Create Date: 2026-10-14 06:50:20.976735+00:00
"""

from collections.abc import Sequence

from alembic import op

# Identifiants de révision, utilisés par Alembic.
revision: str = "179c8cc724de"
down_revision: str | Sequence[str] | None = "03d1bd152b99"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# SQL de vérification, exposé pour être testé directement (tests/integration/test_migrations.py).
VERIFY_SCHEMA_PRIVILEGES_SQL = """
        DO $$
        BEGIN
            IF has_schema_privilege('public', 'public', 'USAGE')
                OR has_schema_privilege('public', 'public', 'CREATE') THEN
                RAISE EXCEPTION 'Le rôle PUBLIC garde des droits sur le schéma public : '
                    'les migrations doivent être exécutées par le propriétaire du schéma.';
            END IF;
            IF NOT has_schema_privilege('madasource_app', 'public', 'USAGE') THEN
                RAISE EXCEPTION 'madasource_app n''a pas l''usage du schéma public.';
            END IF;
            IF has_schema_privilege('madasource_app', 'public', 'CREATE') THEN
                RAISE EXCEPTION 'madasource_app ne doit pas pouvoir créer d''objet dans public.';
            END IF;
        END
        $$
        """


def upgrade() -> None:
    """Échoue si PUBLIC garde l'usage du schéma ou si le rôle applicatif a trop ou trop peu."""
    op.execute(VERIFY_SCHEMA_PRIVILEGES_SQL)


def downgrade() -> None:
    """Rien à annuler : la révision ne modifie rien."""
