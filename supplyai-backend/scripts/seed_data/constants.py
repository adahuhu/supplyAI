"""演示数据常量 — 店铺、仓库、负责人、产品池等."""
from __future__ import annotations

from datetime import date

# ===== 时间 =====
TODAY = date(2026, 5, 9)
RECENT_STOCKOUT_EVENT_ANCHOR = date(2026, 5, 18)
SEED = 42

# ===== 店铺(6 个,与前端 mock 对齐) =====
STORES = [
    {
        "mall_id": 1001,
        "name": "Aurora-US01",
        "account": "aurora-us",
        "country_code": "US",
        "country": "美国",
        "currency": "USD",
        "marketplace_id": "ATVPDKIKX0DER",
        "aws_region": "us-east-1",
        "region": "NA",
    },
    {
        "mall_id": 1002,
        "name": "Aurora-DE02",
        "account": "aurora-de",
        "country_code": "DE",
        "country": "德国",
        "currency": "EUR",
        "marketplace_id": "A1PA6795UKMFR9",
        "aws_region": "eu-west-1",
        "region": "EU",
    },
    {
        "mall_id": 1003,
        "name": "Nordic-UK01",
        "account": "nordic-uk",
        "country_code": "UK",
        "country": "英国",
        "currency": "GBP",
        "marketplace_id": "A1F83G8C2ARO7P",
        "aws_region": "eu-west-1",
        "region": "EU",
    },
    {
        "mall_id": 1004,
        "name": "Sakura-JP01",
        "account": "sakura-jp",
        "country_code": "JP",
        "country": "日本",
        "currency": "JPY",
        "marketplace_id": "A1VC38T7YXB528",
        "aws_region": "us-west-2",
        "region": "FE",
    },
    {
        "mall_id": 1005,
        "name": "Aurora-CA01",
        "account": "aurora-ca",
        "country_code": "CA",
        "country": "加拿大",
        "currency": "CAD",
        "marketplace_id": "A2EUQ1WTGCTBG2",
        "aws_region": "us-east-1",
        "region": "NA",
    },
    {
        "mall_id": 1006,
        "name": "Aurora-FR01",
        "account": "aurora-fr",
        "country_code": "FR",
        "country": "法国",
        "currency": "EUR",
        "marketplace_id": "A13V1IB3VIYZZH",
        "aws_region": "eu-west-1",
        "region": "EU",
    },
]

# ===== 仓库(5 个,覆盖 4 种类型) =====
WAREHOUSES = [
    {
        "warehouse_id": 9001,
        "warehouse_name": "Aurora-Local-CN-SZ",
        "warehouse_type": "local",
        "include_in_local_actual": 1,
    },
    {
        "warehouse_id": 9002,
        "warehouse_name": "Aurora-Local-CN-YW",
        "warehouse_type": "local",
        "include_in_local_actual": 1,
    },
    {
        "warehouse_id": 9003,
        "warehouse_name": "FBA-Transfer-US",
        "warehouse_type": "fba_transfer",
        "include_in_local_actual": 0,
    },
    {
        "warehouse_id": 9004,
        "warehouse_name": "Overseas-EU-DE",
        "warehouse_type": "overseas",
        "include_in_local_actual": 0,
    },
    {
        "warehouse_id": 9005,
        "warehouse_name": "Virtual-Reserved",
        "warehouse_type": "virtual",
        "include_in_local_actual": 0,
    },
]

LOCAL_WAREHOUSE_IDS = [w["warehouse_id"] for w in WAREHOUSES if w["include_in_local_actual"] == 1]

# ===== 负责人(6 人) =====
OWNERS = [
    {"user_id": 5001, "name": "李婧"},
    {"user_id": 5002, "name": "王诚"},
    {"user_id": 5003, "name": "张默"},
    {"user_id": 5004, "name": "赵磊"},
    {"user_id": 5005, "name": "陈萌"},
    {"user_id": 5006, "name": "刘洋"},
]

# ===== 产品池(25 个,与前端 mock 对齐) =====
PRODUCTS = [
    ("便携真空保温水杯 500ml 哑光黑", "家居 / 厨房", "AURORA"),
    ("可调节人体工学桌面支架 V2", "办公 / 配件", "NORDIC"),
    ("硅胶折叠便携漏斗 4 件套", "家居 / 厨房", "AURORA"),
    ("宠物自动喂食器 6L 智能版", "宠物 / 喂食", "SAKURA"),
    ("户外露营便携折叠椅 加固版", "户外 / 装备", "MOMENT"),
    ("车载手机磁吸支架 Pro", "汽配 / 支架", "AURORA"),
    ("LED 化妆镜 三色调光款", "美妆 / 工具", "NORDIC"),
    ("儿童硅胶围嘴防水款 2 件装", "母婴 / 喂养", "SAKURA"),
    ("不锈钢厨房收纳挂篮 大号", "家居 / 收纳", "AURORA"),
    ("蓝牙运动耳机 IPX7 防水", "数码 / 音频", "MOMENT"),
    ("健身阻力带 5 件套 加厚", "运动 / 健身", "NORDIC"),
    ("便携式电动榨汁杯 USB 充", "家居 / 厨房", "AURORA"),
    ("木质书桌收纳分隔架", "办公 / 收纳", "NORDIC"),
    ("可折叠瑜伽垫 6mm TPE", "运动 / 健身", "MOMENT"),
    ("汽车后备箱整理收纳箱", "汽配 / 收纳", "AURORA"),
    ("宠物自动饮水器 4L 静音", "宠物 / 饮水", "SAKURA"),
    ("智能定时插座 WiFi 版", "数码 / 智能家居", "MOMENT"),
    ("便携式蒸汽挂烫机 1500W", "家居 / 清洁", "AURORA"),
    ("不粘锅炒锅 28cm 麦饭石", "家居 / 厨房", "NORDIC"),
    ("婴儿便携餐椅 折叠款", "母婴 / 喂养", "SAKURA"),
    ("户外便携头灯 USB 充电", "户外 / 装备", "MOMENT"),
    ("亚麻沙发坐垫 45×45 4 件", "家居 / 软装", "AURORA"),
    ("电动牙刷 声波震动 IPX7", "美妆 / 个护", "NORDIC"),
    ("硅胶冰格 球形 大颗 2 件", "家居 / 厨房", "AURORA"),
    ("可降解垃圾袋 加厚 100 只", "家居 / 清洁", "MOMENT"),
]

# ===== 物流方式 =====
LOGISTICS_METHODS = [
    {"mode": "海运", "days": 35},
    {"mode": "空运", "days": 8},
    {"mode": "快船", "days": 18},
    {"mode": "快递", "days": 5},
]

# ===== 风险等级目标分布(48 SKU) =====
RISK_DISTRIBUTION = {
    "p1": 12,   # FBA 可售 ≤ 7 天
    "p2": 14,   # 8-15 天
    "p3": 12,   # 16-30 天
    "safe": 10,  # > 30 天
}

# ===== 总 SKU 数 =====
TOTAL_SKUS = sum(RISK_DISTRIBUTION.values())  # 48

# ===== 默认采购规则 =====
DEFAULT_RULE = {
    "rule_id": "RULE-GLOBAL-DEFAULT",
    "scope_type": "global",
    "safety_days": 14,
    "purchase_duration_days": 12,
    "delivery_days": 5,
    "qc_days": 3,
    # 物流时效(取最长): 海运 35 天
    "max_logistics_days": 35,
    "rule_version": "v1",
}
DEFAULT_LEAD_TIME = (
    DEFAULT_RULE["purchase_duration_days"]
    + DEFAULT_RULE["delivery_days"]
    + DEFAULT_RULE["qc_days"]
    + DEFAULT_RULE["max_logistics_days"]
)  # = 55 天
DEFAULT_TOTAL_COVERAGE = DEFAULT_LEAD_TIME + DEFAULT_RULE["safety_days"]  # = 69 天

# ===== 默认预测规则 =====
DEFAULT_FORECAST = {
    "rule_id": "FORECAST-GLOBAL-DEFAULT",
    "scope_type": "global",
    "forecast_mode": "default",
    "default_daily_sales": 10,
    "denoise_enabled": 0,
}

# ===== 演示固定 calc_run =====
DEFAULT_CALC_RUN_ID = f"DEMO-{TODAY.strftime('%Y%m%d')}-080000"
