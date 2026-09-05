"""Add the user's last market-check timestamp.

Revision ID: 20260904_02
Revises: 20260904_01
Create Date: 2026-09-04 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260904_02"
down_revision: str | Sequence[str] | None = "20260904_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("last_market_check_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "last_market_check_at")
