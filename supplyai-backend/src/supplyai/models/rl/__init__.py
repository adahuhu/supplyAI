"""真实源表镜像（rl_*）.

Phase 1-3 通过 seed 脚本写入演示数据;Phase 4 切到 ETL/CDC 同步真实数据。
本地用 SQLAlchemy ORM 自动建表,生产由真实表 DDL 提供。
"""
from supplyai.models.rl.amz_all_listing import RlAmzAllListing
from supplyai.models.rl.amz_finances_profit import RlAmzFinancesProfit
from supplyai.models.rl.amz_listing_detail import RlAmzListingDetail
from supplyai.models.rl.amz_manage_fba_inventory import RlAmzManageFbaInventory
from supplyai.models.rl.amz_sales_daily_report import RlAmzSalesDailyReport
from supplyai.models.rl.fba_shipment_item import RlFbaShipmentItem
from supplyai.models.rl.inventory_detail import RlInventoryDetail
from supplyai.models.rl.mall import RlMall
from supplyai.models.rl.product import RlProduct

__all__ = [
    "RlAmzAllListing",
    "RlAmzFinancesProfit",
    "RlAmzListingDetail",
    "RlAmzManageFbaInventory",
    "RlAmzSalesDailyReport",
    "RlFbaShipmentItem",
    "RlInventoryDetail",
    "RlMall",
    "RlProduct",
]
