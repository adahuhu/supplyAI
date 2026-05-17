"""add sku inventory override table

Revision ID: 2f98b8b7b4a1
Revises: d671d5b46602
Create Date: 2026-05-17 23:10:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f98b8b7b4a1"
down_revision: str | None = "d671d5b46602"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mk_sku_inventory_override",
        sa.Column("override_id", sa.String(length=96), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("listing_id", sa.BigInteger(), nullable=False),
        sa.Column("calc_run_id", sa.String(length=64), nullable=True),
        sa.Column("mall_id", sa.BigInteger(), nullable=True),
        sa.Column("msku", sa.String(length=64, collation="BINARY"), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("day_offset", sa.Integer(), nullable=False),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.String(length=50), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("override_id", name=op.f("pk_mk_sku_inventory_override")),
        sa.UniqueConstraint(
            "tenant_id",
            "listing_id",
            "forecast_date",
            name="uq_mk_sku_inventory_override_tlf",
        ),
    )
    with op.batch_alter_table("mk_sku_inventory_override", schema=None) as batch_op:
        batch_op.create_index(
            "ix_mk_sku_inventory_override_calc_run",
            ["calc_run_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_mk_sku_inventory_override_listing",
            ["tenant_id", "listing_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("mk_sku_inventory_override", schema=None) as batch_op:
        batch_op.drop_index("ix_mk_sku_inventory_override_listing")
        batch_op.drop_index("ix_mk_sku_inventory_override_calc_run")
    op.drop_table("mk_sku_inventory_override")
