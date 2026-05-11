"""SQLAlchemy ORM 模型 — rl_*(真实源表镜像)+ mk_*(项目派生表).

Phase 2 完成:21 张表全部建好(8 rl_* + 13 mk_*),通过 Alembic migration 在 SQLite 自动建表。
切到生产 MySQL 时仅改 DATABASE_URL,业务代码 0 修改。
"""
from supplyai.models.base import Base

# 子包已 import 各自全部模型;此处只需暴露 Base
# 各模型类名直接从子包按需 import,例如:
#   from supplyai.models.mk import MkSupplySkuDailyStat
#   from supplyai.models.rl import RlAmzAllListing

__all__ = ["Base"]
