"""schema privileges baseline

Socle des droits sur le schéma `public` (security-design.md §19, indexes-and-constraints.md
§6.1) : seuls le propriétaire du schéma (qui exécute les migrations) et le rôle applicatif
`madasource_app` peuvent l'utiliser ; personne d'autre n'y crée d'objet. Aucune table.

Le rôle applicatif doit exister avant cette migration : il porte un mot de passe et n'est
donc pas créé ici (`infrastructure/postgres/10-create-app-role.sh`). Son nom est écrit en
toutes lettres, et non importé de l'application, pour que cette révision reste figée.

Risque : faible (droits seulement, aucune donnée). Réversible.

Revision ID: 03d1bd152b99
Revises: aucune (première révision)
Create Date: 2026-10-14 06:24:12.320051+00:00
"""

from collections.abc import Sequence

from alembic import op

# Identifiants de révision, utilisés par Alembic.
revision: str = "03d1bd152b99"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Le nom du rôle applicatif est écrit en dur dans chaque instruction : une migration est
# figée, et aucune valeur n'y est interpolée.


def upgrade() -> None:
    """Retire au rôle PUBLIC l'usage du schéma et l'accorde au seul rôle applicatif."""
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'madasource_app') THEN
                RAISE EXCEPTION 'Le rôle madasource_app doit exister avant les migrations '
                    '(infrastructure/postgres/10-create-app-role.sh).';
            END IF;
        END
        $$
        """
    )
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA public TO madasource_app")


def downgrade() -> None:
    """Rétablit les droits par défaut de PostgreSQL sur le schéma public."""
    op.execute("REVOKE USAGE ON SCHEMA public FROM madasource_app")
    op.execute("GRANT USAGE ON SCHEMA public TO PUBLIC")
