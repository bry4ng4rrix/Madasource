"""${message}

Revision ID: ${up_revision}
${"Revises: " + (down_revision if isinstance(down_revision, str) else ", ".join(down_revision)) if down_revision else "Revises: aucune (première révision)"}
Create Date: ${create_date}
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
% if imports:
${imports}
% endif

# Identifiants de révision, utilisés par Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Applique la migration."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Annule la migration, ou lève une exception si elle est irréversible."""
    ${downgrades if downgrades else "pass"}
