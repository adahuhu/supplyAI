"""add stock scope to replenishment rules

Revision ID: 97a1c4c2d8e5
Revises: 8b2fb5d0c9a4
Create Date: 2026-05-18 20:30:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "97a1c4c2d8e5"
down_revision: str | None = "8b2fb5d0c9a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEFAULT_STOCK_SCOPE = '["fba_available"]'


def upgrade() -> None:
    with op.batch_alter_table("mk_replenishment_rule", schema=None) as batch_op:
        batch_op.add_column(sa.Column("stock_scope_json", sa.JSON(), nullable=True))

    with op.batch_alter_table("mk_supply_sku_daily_stat", schema=None) as batch_op:
        batch_op.add_column(sa.Column("planning_stock", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("stock_scope_json", sa.JSON(), nullable=True))

    op.execute(
        f"""
        UPDATE mk_replenishment_rule
        SET stock_scope_json = '{DEFAULT_STOCK_SCOPE}'
        WHERE stock_scope_json IS NULL
        """
    )
    op.execute(
        f"""
        UPDATE mk_supply_sku_daily_stat
        SET stock_scope_json = '{DEFAULT_STOCK_SCOPE}',
            planning_stock = COALESCE(fba_available, 0)
        WHERE stock_scope_json IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("mk_supply_sku_daily_stat", schema=None) as batch_op:
        batch_op.drop_column("stock_scope_json")
        batch_op.drop_column("planning_stock")
    with op.batch_alter_table("mk_replenishment_rule", schema=None) as batch_op:
        batch_op.drop_column("stock_scope_json")
