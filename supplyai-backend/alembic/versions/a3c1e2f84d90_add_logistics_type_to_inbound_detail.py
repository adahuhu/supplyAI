"""add logistics_type to mk_sku_inbound_detail

Revision ID: a3c1e2f84d90
Revises: 2f98b8b7b4a1
Create Date: 2026-05-18 12:30:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a3c1e2f84d90"
down_revision: str | None = "2f98b8b7b4a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("mk_sku_inbound_detail", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("logistics_type", sa.String(length=30), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("mk_sku_inbound_detail", schema=None) as batch_op:
        batch_op.drop_column("logistics_type")
