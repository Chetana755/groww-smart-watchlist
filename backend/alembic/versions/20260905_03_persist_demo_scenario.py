"""Persist the selected demo market scenario.

Revision ID: 20260905_03
Revises: 20260904_02
Create Date: 2026-09-05 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260905_03"
down_revision: str | Sequence[str] | None = "20260904_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "demo_scenario",
            sa.String(length=40),
            nullable=False,
            server_default="NORMAL_DAY",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "demo_scenario")
