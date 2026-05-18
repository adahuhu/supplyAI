"""add sku label fields

Revision ID: 8b2fb5d0c9a4
Revises: 2f98b8b7b4a1
Create Date: 2026-05-18 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b2fb5d0c9a4"
down_revision: str | None = "2f98b8b7b4a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("mk_listing_product_sources", schema=None) as batch_op:
        batch_op.add_column(sa.Column("label_ids", sa.String(length=255), nullable=True))
    with op.batch_alter_table("mk_supply_sku_daily_stat", schema=None) as batch_op:
        batch_op.add_column(sa.Column("label_ids", sa.String(length=255), nullable=True))

    # Demo/backfill: varied operational tags while keeping some SKUs promo-eligible.
    op.execute(
        """
        UPDATE mk_listing_product_sources
        SET label_ids = CASE
            WHEN ((listing_id - 1000000) % 12) = 0 THEN CASE WHEN country_code = 'US' THEN '大促,Memorial Day,爆款,高复购' ELSE '大促,Prime Day,爆款,高复购' END
            WHEN ((listing_id - 1000000) % 12) = 1 THEN '新品,首批备货,高毛利,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 2 THEN '大促,Prime Day,季节款,夏季,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 3 THEN '清仓,尾货,低动销,低库存'
            WHEN ((listing_id - 1000000) % 12) = 4 THEN '大促,Prime Day,礼品款,节日礼盒,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 5 THEN '低库存,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 6 THEN CASE WHEN country_code = 'US' THEN '大促,Memorial Day,高毛利,广告款' ELSE '大促,Prime Day,高毛利,广告款' END
            WHEN ((listing_id - 1000000) % 12) = 7 THEN '长尾,稳定款'
            WHEN ((listing_id - 1000000) % 12) = 8 THEN '大促,Prime Day,套装款,组合销售,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 9 THEN '新品,测款,潜力款,低库存'
            WHEN ((listing_id - 1000000) % 12) = 10 THEN '清仓,降价款'
            ELSE '大促,Prime Day,黑五预备,低库存'
        END
        WHERE label_ids IS NULL
        """
    )
    op.execute(
        """
        UPDATE mk_supply_sku_daily_stat
        SET label_ids = CASE
            WHEN ((listing_id - 1000000) % 12) = 0 THEN CASE WHEN country_code = 'US' THEN '大促,Memorial Day,爆款,高复购' ELSE '大促,Prime Day,爆款,高复购' END
            WHEN ((listing_id - 1000000) % 12) = 1 THEN '新品,首批备货,高毛利,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 2 THEN '大促,Prime Day,季节款,夏季,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 3 THEN '清仓,尾货,低动销,低库存'
            WHEN ((listing_id - 1000000) % 12) = 4 THEN '大促,Prime Day,礼品款,节日礼盒,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 5 THEN '低库存,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 6 THEN CASE WHEN country_code = 'US' THEN '大促,Memorial Day,高毛利,广告款' ELSE '大促,Prime Day,高毛利,广告款' END
            WHEN ((listing_id - 1000000) % 12) = 7 THEN '长尾,稳定款'
            WHEN ((listing_id - 1000000) % 12) = 8 THEN '大促,Prime Day,套装款,组合销售,补货关注'
            WHEN ((listing_id - 1000000) % 12) = 9 THEN '新品,测款,潜力款,低库存'
            WHEN ((listing_id - 1000000) % 12) = 10 THEN '清仓,降价款'
            ELSE '大促,Prime Day,黑五预备,低库存'
        END
        WHERE label_ids IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("mk_supply_sku_daily_stat", schema=None) as batch_op:
        batch_op.drop_column("label_ids")
    with op.batch_alter_table("mk_listing_product_sources", schema=None) as batch_op:
        batch_op.drop_column("label_ids")
