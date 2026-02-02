"""remove unused autoincrement

Revision ID: 202602021206
Revises: 202601161555
Create Date: 2026-02-02 12:06:06.073449

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "202602021206"
down_revision: Union[str, None] = "202601161555"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove autoincrement=True metadata (no-op for Postgres)."""

    # points.point_id
    op.alter_column(
        "points",
        "point_id",
        existing_type=sa.INTEGER(),
        existing_nullable=False,
        existing_server_default=sa.text("nextval('points_point_id_seq'::regclass)"),
        comment="The unique ID of the Sensemaking Point.",
    )

    # tracks.track_id
    op.alter_column(
        "tracks",
        "track_id",
        existing_type=sa.INTEGER(),
        existing_nullable=False,
        comment="The unique ID of the Track within the database only.",
    )


def downgrade() -> None:
    """Restore autoincrement flag metadata (no behavior change)."""

    op.alter_column(
        "tracks",
        "track_id",
        existing_type=sa.INTEGER(),
        existing_nullable=False,
        autoincrement=True,
        comment="The unique ID of the Track within the database only.",
    )

    op.alter_column(
        "points",
        "point_id",
        existing_type=sa.INTEGER(),
        existing_nullable=False,
        autoincrement=True,
        existing_server_default=sa.text("nextval('points_point_id_seq'::regclass)"),
        comment="The unique ID of the Sensemaking Point.",
    )
