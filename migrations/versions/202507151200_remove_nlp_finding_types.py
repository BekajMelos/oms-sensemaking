"""Remove NLP finding types.

Revision ID: 202507151200
Revises: 202507101506
Create Date: 2025-07-15 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202507151200"
down_revision: Union[str, None] = "202507101506"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Previous options included NLP-related values; we are removing them
old_options = (
    "UNKNOWN",
    "GEO_COTRAVEL",
    "GEO_LOITER",
    "GEO_SIMILAR_TRACKS",
    "NLP_RECOGNIZED_ENTITY",
    "NLP_FINDINGS",
    "RESOLUTION_DUPLICATE",
    "INF_HAS_NAME",
    "INF_OUT_OF_GARRISON",
    "INF_INCURSION",
    "MIL_SYMBOL_UPDATE",
)
new_options = tuple(
    sorted(
        [
            "UNKNOWN",
            "GEO_COTRAVEL",
            "GEO_LOITER",
            "GEO_SIMILAR_TRACKS",
            "RESOLUTION_DUPLICATE",
            "INF_HAS_NAME",
            "INF_OUT_OF_GARRISON",
            "INF_INCURSION",
            "MIL_SYMBOL_UPDATE",
        ]
    )
)

old_type = sa.Enum(*old_options, name="findingtype")
new_type = sa.Enum(*new_options, name="findingtype")
tmp_type = sa.Enum(*new_options, name="_findingtype")

tcr = sa.sql.table("findings", sa.Column("finding_type", new_type, nullable=False))


def upgrade() -> None:
    """Upgrade the database schema by removing NLP enum values from findingtype."""
    # Create a temporary "_findingtype" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE findings ALTER COLUMN finding_type TYPE _findingtype USING finding_type::text::_findingtype"
    )
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" findingtype type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE findings ALTER COLUMN finding_type TYPE findingtype USING finding_type::text::findingtype")
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade() -> None:
    """Downgrade the database schema by restoring NLP enum values to findingtype."""
    # Recreate the previous enum with NLP values
    prev_type = sa.Enum(*old_options, name="_findingtype_old")
    prev_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        "ALTER TABLE findings ALTER COLUMN finding_type TYPE _findingtype_old "
        "USING finding_type::text::_findingtype_old"
    )
    new_type.drop(op.get_bind(), checkfirst=False)
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute("ALTER TABLE findings ALTER COLUMN finding_type TYPE findingtype USING finding_type::text::findingtype")
    prev_type.drop(op.get_bind(), checkfirst=False)
