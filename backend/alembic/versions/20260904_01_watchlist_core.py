"""Create watchlist core schema and demo instrument catalog.

Revision ID: 20260904_01
Revises:
Create Date: 2026-09-04 14:15:00
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "20260904_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INSTRUMENTS = [
    ("RELIANCE", "Reliance Industries Ltd.", "NSE", "Energy", "Oil & Gas Integrated"),
    ("TCS", "Tata Consultancy Services Ltd.", "NSE", "Information Technology", "IT Services"),
    ("INFY", "Infosys Ltd.", "NSE", "Information Technology", "IT Services"),
    ("HDFCBANK", "HDFC Bank Ltd.", "NSE", "Financial Services", "Private Banks"),
    ("ICICIBANK", "ICICI Bank Ltd.", "NSE", "Financial Services", "Private Banks"),
    ("SBIN", "State Bank of India", "NSE", "Financial Services", "Public Banks"),
    ("ITC", "ITC Ltd.", "NSE", "Consumer Defensive", "Tobacco"),
    ("LT", "Larsen & Toubro Ltd.", "NSE", "Industrials", "Engineering & Construction"),
    ("WIPRO", "Wipro Ltd.", "NSE", "Information Technology", "IT Services"),
    ("HCLTECH", "HCL Technologies Ltd.", "NSE", "Information Technology", "IT Services"),
]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False, unique=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "watchlist_id",
            sa.Uuid(),
            sa.ForeignKey("watchlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "instrument_id",
            sa.Uuid(),
            sa.ForeignKey("instruments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("watchlist_id", "instrument_id", name="uq_watchlist_item_instrument"),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])
    instruments = sa.table(
        "instruments",
        sa.column("id", sa.Uuid()),
        sa.column("symbol", sa.String()),
        sa.column("company_name", sa.String()),
        sa.column("exchange", sa.String()),
        sa.column("sector", sa.String()),
        sa.column("industry", sa.String()),
    )
    op.bulk_insert(
        instruments,
        [
            {
                "id": uuid4(),
                "symbol": symbol,
                "company_name": company_name,
                "exchange": exchange,
                "sector": sector,
                "industry": industry,
            }
            for symbol, company_name, exchange, sector, industry in INSTRUMENTS
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_watchlist_items_watchlist_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("ix_watchlists_user_id", table_name="watchlists")
    op.drop_table("watchlists")
    op.drop_index("ix_instruments_symbol", table_name="instruments")
    op.drop_table("instruments")
    op.drop_table("users")
