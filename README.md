# SupplyAI · 供应链分析工作台

亚马逊电商 **MSKU + 店铺粒度** 备货决策辅助系统。把分散在 Listing、销量、库存、发货、节假日、汇率里的信号聚合成"今天要做的事",让运营 5 分钟内识别风险 → 生成采购计划 → 决策可解释。

---

## 一眼看懂

```
┌─────────────────────────────────────────────────────────────────────┐
│  浏览器 (React 18 + Babel-in-browser,无 build)                     │
│  ┌───────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌─────────┐ │
│  │ 工作台    │  │ 备货计划 │  │ SKU    │  │ 草稿   │  │ AI 抽屉 │ │
│  │ Dashboard │  │ List     │  │ Detail │  │ Drafts │  │ (SSE)   │ │
│  └───────────┘  └──────────┘  └────────┘  └────────┘  └─────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  POST /api/supplyai/... (JSON)
                               │  POST /api/supplyai/ai/{chat,explain}/stream (SSE)
┌──────────────────────────────▼──────────────────────────────────────┐
│  FastAPI 后端                                                       │
│  ┌──────────────────┐ ┌──────────────┐ ┌─────────────────────────┐ │
│  │ Dashboard / SKU  │ │ Rules /      │ │ AI:                     │ │
│  │ /Calc/Exports    │ │ Purchase     │ │  Orchestrator           │ │
│  │  API + Service   │ │ Drafts API   │ │ + 4 Tools               │ │
│  │  + Repositories  │ │              │ │ + DashScope (Qwen3.6-p) │ │
│  └──────────────────┘ └──────────────┘ └─────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  SQLAlchemy 2.0 async
┌──────────────────────────────▼──────────────────────────────────────┐
│  数据层 — 21 张表                                                  │
│  rl_*  (9 真实源镜像)    +    mk_*  (13 项目派生 / 配置 / 物化)    │
│  本地 SQLite  ◀── DATABASE_URL ──▶  生产 MySQL 8                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 启动 — 一行命令

```bash
./start-dev.sh
```

这一行会:
1. 检查 `SUPPLY_DASH_API_KEY` 是否在环境(没有就退出并提示)
2. 释放端口 8000 / 5173
3. 起后端 `uvicorn supplyai.main:app --port 8000 --reload`
4. 起前端 `python3 -m http.server 5173` 在 `SupplyAI/` 下

打开 <http://127.0.0.1:5173/SupplyAI.html>。

> **首次需要 4 步初始化(下方"分步启动")**:装 uv / 同步依赖 / 配 .env / 灌 seed。

---

## 项目结构

```
supplyAI/
├── SupplyAI/                  # 前端 — 纯 React + Babel-in-browser,无 build
│   ├── SupplyAI.html          # 入口,所有 jsx 通过 <script type="text/babel"> 加载
│   ├── app.jsx                # 路由 + 全局 state(过滤器 + AI 历史)
│   ├── shell.jsx              # Sidebar + Topbar
│   ├── dashboard.jsx          # 工作台 — 摘要 + 财务 5 卡 + 健康环 + 风险队列
│   ├── list.jsx               # 备货计划列表(20+ 列,sticky + horizontal scroll)
│   ├── sku.jsx                # SKU 详情(关键指标 + 趋势图 + 库存构成 + 规则)
│   ├── drafts.jsx             # 采购草稿管理(状态机)
│   ├── rules.jsx              # 规则中心弹窗(补货 + 销量预测)
│   ├── ai.jsx                 # 全局 AI / SKU AI + 思考折叠 + 流式渲染
│   ├── ai-fab.jsx             # 浮动 AI 入口胶囊
│   ├── md.jsx                 # 轻量 markdown 渲染(表格 / list / P1-P3 chip)
│   ├── ui.jsx                 # 基础组件(Drawer/Modal/Sparkline/ChartArea/...)
│   ├── adapter.jsx            # snake_case → camelCase ViewModel 映射
│   ├── api.jsx                # POST 包装 + SSE 流式包装(streamSSE)
│   ├── data.jsx               # 国家 / 物流 / 状态等枚举
│   ├── tokens.css             # 设计 token(色 / 字号 / 间距 / 圆角)
│   └── api-smoke.html         # API 调试页
│
├── supplyai-backend/          # 后端 — FastAPI + SQLAlchemy 2.0 async
│   ├── .env.example           # ★ 所有配置项 + 注释(详见 supplyai-backend/README.md)
│   ├── src/supplyai/          # 主代码(api/schemas/models/repositories/services/domain)
│   ├── tests/                 # 216 in-process + 18 browser(Playwright)
│   ├── alembic/               # 数据库迁移
│   └── scripts/seed.py        # 演示数据生成(48 SKU × 6 店铺 × 90 天)
│
├── docs/                      # 架构合同(命名规约 / 字段映射 / 决策日志)
│   ├── supplyai-backend-python.md
│   ├── supplyai-data-table-design.md
│   ├── supplyai-field-mapping-v2.md
│   └── supplyai-decisions.md
│
├── start-dev.sh               # 一键启动脚本
└── README.md                  # 本文件
```

---

## 分步启动(首次)

### 1. 安装 uv(Python 包管理器)

```bash
brew install uv          # macOS
# 或 https://docs.astral.sh/uv/getting-started/installation/
```

### 2. 后端依赖

```bash
cd supplyai-backend
uv sync                  # 装 fastapi / sqlalchemy / pydantic / aiosqlite / openai-compat / playwright …
```

### 3. 配置 .env

```bash
cp .env.example .env
# 编辑 .env,至少填:
#   SUPPLY_DASH_API_KEY=sk-xxxx        (DashScope API key)
#   SUPPLY_DASH_URL=https://...        (默认走官方公网,自部署需填)
```

> 完整配置项参考 [`supplyai-backend/.env.example`](supplyai-backend/.env.example)。
> 也可以通过 shell 环境变量直接传(进程环境优先于 `.env`)。

### 4. 建库 + 灌演示数据

```bash
mkdir -p data
uv run alembic upgrade head
uv run python scripts/seed.py
```

生成 48 SKU / 6 店铺 / 5 国家 / 90 天历史销量 / 85 条 FBA 发货 / 48 条在途 / 一个 calc_run_id 物化快照,默认租户 `100228`。

### 5. 启动

```bash
# 在仓库根目录
./start-dev.sh
# 或分别启:
#   后端: cd supplyai-backend && uv run uvicorn supplyai.main:app --port 8000 --reload
#   前端: cd SupplyAI && python3 -m http.server 5173
```

打开:
- 工作台:<http://127.0.0.1:5173/SupplyAI.html>
- API:  <http://127.0.0.1:8000/docs>

---

## 后端 API 概览(详见 `/docs` Swagger)

| 资源 | 主要端点 |
|---|---|
| Dashboard | `/dashboard/snapshot` `/risk-queue` `/finance` `/filters` `/stores` `/data-quality-alerts` `/holidays` |
| SKU | `/skus/list` `/skus/detail` `/skus/trends` |
| Rules | `/rules/list` `/rules/upsert` `/rules/disable` `/rules/forecast/*` |
| Purchase | `/purchase/draft/{create,list,detail,confirm,redirect}` |
| Calc | `/calc/run` `/calc/latest` `/calc/status` |
| AI | `/ai/explain` `/ai/chat` + **`/ai/{explain,chat}/stream`(SSE)** |
| Exports | `/exports/sku-list` `/exports/status` `/exports/download` |
| Auth | `/auth/me`(Phase 5 接 JWT) |

**所有业务端点都是 POST + JSON body。** SSE 端点返 `text/event-stream`。

---

## 数据结构

### 表命名规约

| 前缀 | 含义 |
|---|---|
| **`rl_*`** | 真实源表镜像 — 字段名与上游一致 |
| **`mk_*`** | SupplyAI 派生 / 配置 / 物化表 |

### 21 张表的角色

```
┌────────── 真实源(rl_,9 张)──────────┐    ┌────────── 项目派生(mk_,13 张)──────────┐
│ rl_amz_all_listing       Listing 主    │    │ mk_calc_run             ★ 计算批次          │
│ rl_amz_listing_detail    详情扩展      │ →  │ mk_supply_sku_daily_stat ★ 核心快照表       │
│ rl_amz_sales_daily_report 90 天日销    │    │ mk_sku_forecast_daily    未来 45 天预测     │
│ rl_amz_manage_fba_inventory FBA 库存   │    │ mk_sku_inbound_detail    在途明细           │
│ rl_amz_finances_profit_* 店铺日财务    │    │ mk_stockout_event        断货事件           │
│ rl_fba_shipment_item     FBA 发货货件  │    │ mk_listing_product_sources 商品视图        │
│ rl_inventory_detail      本地仓库存    │    │ mk_replenishment_rule    补货规则           │
│ rl_mall                  店铺主数据    │    │ mk_rule_logistics_method 物流规则           │
│ rl_product               商品主数据    │    │ mk_forecast_rule         销量预测规则       │
└────────────────────────────────────────┘    │ mk_purchase_draft        采购草稿           │
                                              │ mk_tenant_config         租户配置           │
                                              │ mk_warehouse_mapping     仓库映射           │
                                              │ mk_holiday               节假日             │
                                              │ mk_export_task           导出任务           │
                                              └─────────────────────────────────────────────┘
```

### 业务结论的一致性 — Calc Run

所有派生结论(风险等级、断货日、建议采购量、覆盖周期需求等)都打 `calc_run_id`。同一批次内,Dashboard / 列表 / 详情 / AI 解释看到的数字必须严格一致。重新执行 `/calc/run` 会生成新批次,旧批次保留。

### 字段映射(Backend → Frontend)

- 后端返回 **snake_case** Pydantic DTO
- 前端 `SupplyAI/adapter.jsx` 统一映射为 **camelCase** ViewModel
- 详细对照见 [`docs/supplyai-field-mapping-v2.md`](docs/supplyai-field-mapping-v2.md)

---

## AI 体验

### 入口

- **全局 AI 抽屉**(任意页面右下浮球 / 顶栏按钮 / `⌘J`)
- **SKU AI 助手**(详情页右侧抽屉,打开自动调 `/ai/explain/stream`)

### 流式 + 思考可视

- DashScope 流(stream=true)→ 后端拆 `reasoning_content` / `content`
- 前端折叠面板实时显示思考过程(DeepSeek 风格,默认展开,完成后自动折叠)
- 答复区 markdown 渲染,P1/P2/P3 自动转风险 chip

### 工具调度

模型可主动调 4 个 Tool:`query_skus` / `query_stockout_risk` / `get_sku_detail` / `generate_purchase_draft`。前端实时显示"正在调用工具:查询风险队列…"。

### 思考开关

`.env` 里 `SUPPLY_DASH_ENABLE_THINKING=false` 直接跳过思考阶段:首字 <1s,代价答复质量略降。

---

## 平迁生产

只改 `.env`,业务代码 0 修改:

```dotenv
APP_ENV=production
DATABASE_URL=mysql+aiomysql://user:pwd@db:3306/supplyai?charset=utf8mb4
CACHE_BACKEND=redis
REDIS_URL=redis://:pwd@redis:6379/0
TASK_RUNNER=celery
LOG_FORMAT=json
JWT_SECRET=$(openssl rand -hex 32)
SUPPLY_DASH_VERIFY_SSL=true
```

生产依赖:

```bash
cd supplyai-backend
uv sync --extra prod                           # +aiomysql / +redis / +celery
uv run alembic upgrade head
uvicorn supplyai.main:app --host 0.0.0.0 --port 8000 --workers 4
```

前端:`SupplyAI/` 整目录是静态文件,nginx / CDN 直挂即可。生产建议预编译 jsx(目前是 Babel-in-browser,首次加载会有 1-2s 编译开销)。

---

## 测试

```bash
cd supplyai-backend

# 单元 + 集成(217 个)
uv run pytest

# 真浏览器 E2E(18 个,Playwright Chromium 子进程)
uv run pytest -m browser

# 跳 AI 用例(无 DashScope key 时)
uv run pytest --ignore=tests/test_ai_agent.py
```

测试覆盖:

- 21 表 ORM 模型校验
- 全部 API 路由 happy path + 边界
- Dashboard / SKU / Rules / Purchase / Exports / Calc / AI(stub)
- 风险派生 / 预测算法 / 覆盖周期 / 建议数量
- 真 Chromium 跑 SupplyAI.html,断言 DOM 状态机切换 + 历史 review 修复点回归
- AI SSE 协议(`/ai/chat/stream`、`/ai/explain/stream`)

---

## 文档导航

- **后端详细启动 / 配置:** [`supplyai-backend/README.md`](supplyai-backend/README.md)
- **后端架构:** [`docs/supplyai-backend-python.md`](docs/supplyai-backend-python.md)
- **数据表设计:** [`docs/supplyai-data-table-design.md`](docs/supplyai-data-table-design.md)
- **字段映射:** [`docs/supplyai-field-mapping-v2.md`](docs/supplyai-field-mapping-v2.md)
- **决策日志:** [`docs/supplyai-decisions.md`](docs/supplyai-decisions.md)
- **前端设计原则:** [`SupplyAI/DESIGN.md`](SupplyAI/DESIGN.md)

---

## License

Private project. 内部使用。
