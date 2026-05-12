# SupplyAI 后端

供应链分析工作台后端服务 — **FastAPI + SQLAlchemy 2.0 async + Pydantic v2** 单服务。

业务能力:Dashboard 快照 / 备货计划列表 / SKU 详情 / 风险派生 / 采购草稿 / 规则中心 / AI 解释 + 流式对话 + 工具调度。

---

## 快速启动(本地,macOS / Linux)

### 1. 一次性配置

```bash
# 1) uv 包管理器
brew install uv          # macOS;Linux 用 https://docs.astral.sh/uv/

# 2) 依赖
cd supplyai-backend
uv sync

# 3) 环境变量
cp env.example .env
# 编辑 .env,至少填上 SUPPLY_DASH_API_KEY=sk-...

# 4) 建库 + 灌演示数据
mkdir -p data
uv run alembic upgrade head
uv run python scripts/seed.py
```

### 2. 启动后端

```bash
uv run uvicorn supplyai.main:app --reload --port 8000
```

或者从仓库根目录用一键脚本(同时拉前端):

```bash
cd ..
./start-dev.sh
```

### 3. 验证

```bash
curl -s http://localhost:8000/api/supplyai/_health
# {"status":"ok"}

# 工作台快照(真实派生数据)
curl -s -X POST http://localhost:8000/api/supplyai/dashboard/snapshot \
     -H "Content-Type: application/json" \
     -d '{"tenant_id":100228}' | head -c 200

# AI 流式对话(SSE)
curl -sN -X POST http://localhost:8000/api/supplyai/ai/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"tenant_id":100228,"messages":[{"role":"user","content":"列出 P1 风险最高的 3 个 SKU"}]}'
```

文档入口:
- Swagger: <http://localhost:8000/docs>
- ReDoc:   <http://localhost:8000/redoc>

---

## 配置体系

所有配置通过 `supplyai/config.py` 的 `Settings`(`pydantic-settings`)集中管理:

- **来源:** `.env` 文件 + 进程环境变量(进程优先)
- **示例:** [`env.example`](env.example)(每一项都有注释)
- **代码访问:** `from supplyai.config import settings; settings.dashscope_enable_thinking`

关键配置(完整说明见 `env.example`):

| Key | 默认 | 作用 |
|---|---|---|
| `APP_ENV` | `local` | 应用环境 — 切 `production` 时建议同时切 DATABASE_URL/CACHE/TASK |
| `DATABASE_URL` | SQLite | 本地 SQLite,生产 `mysql+aiomysql://...` |
| `AI_MODEL` | `qwen3.6-plus` | Qwen 模型名 |
| `SUPPLY_DASH_API_KEY` | _必填_ | DashScope key,缺失时 `/ai/*` 全报错 |
| `SUPPLY_DASH_ENABLE_THINKING` | `true` | 开思维链 — 前端有折叠面板展示;关掉首字 <1s 但答复质量略降 |
| `CACHE_BACKEND` | `memory` | 进程 LRU;生产改 `redis` |
| `TASK_RUNNER` | `local` | FastAPI BackgroundTasks;生产改 `celery` |

---

## 项目结构

```
supplyai-backend/
├── alembic/                # 数据库迁移(版本化 schema)
├── data/                   # SQLite 本地 DB + 导出文件(gitignored)
├── scripts/
│   ├── seed.py             # 演示数据生成器:48 SKU × 6 店铺 × 90 天销量
│   └── smoke_dashscope.py  # DashScope 连通性自检
└── src/supplyai/
    ├── main.py             # FastAPI app + CORS + 启动日志
    ├── config.py           # ★ pydantic-settings 配置中心
    ├── db.py               # SQLAlchemy AsyncEngine + Session 工厂
    │
    ├── api/v1/             # REST 路由(全 POST,详见 OpenAPI)
    │   ├── dashboard.py    # /dashboard/{snapshot,risk-queue,filters,...}
    │   ├── skus.py         # /skus/{list,detail,trends}
    │   ├── purchase.py     # /purchase/draft/{create,list,confirm,redirect}
    │   ├── rules.py        # /rules/{list,upsert,disable,forecast/*}
    │   ├── ai.py           # /ai/{explain,chat} + /ai/{explain,chat}/stream (SSE)
    │   ├── calc.py         # /calc/{run,latest,status}
    │   ├── exports.py      # /exports/sku-list + 同步/异步双模式
    │   ├── auth.py         # /auth/me(Phase 5 接 JWT)
    │   └── health.py       # /_health
    │
    ├── schemas/            # Pydantic DTO(snake_case → 前端 adapter 转 camelCase)
    ├── models/             # SQLAlchemy ORM
    │   ├── rl/             # 真实源表镜像(rl_amz_all_listing 等 9 表)
    │   └── mk/             # 项目派生表(mk_supply_sku_daily_stat 等 13 表)
    ├── repositories/       # 表查询封装(无业务规则)
    ├── services/           # 应用编排(API 与领域逻辑的胶水)
    ├── domain/
    │   ├── calc/           # 预测 / 风险 / 覆盖 / 建议派生
    │   └── ai/             # DashScope client + Orchestrator + 4 Tools + Foundation Skills
    ├── tasks/              # 任务运行器(local / celery)
    ├── cache/              # 缓存(in-memory / redis)抽象
    └── utils/              # 异常 + 日志
```

---

## 数据架构

### 表命名规约

| 前缀 | 含义 | 示例 |
|---|---|---|
| `rl_*` | 真实源表镜像 | `rl_amz_all_listing` / `rl_amz_sales_daily_report` / `rl_fba_shipment_item` |
| `mk_*` | SupplyAI 派生 / 配置 / 物化表 | `mk_supply_sku_daily_stat` / `mk_calc_run` / `mk_replenishment_rule` |

### 21 张表全景

```
rl_ (9 张,真实数据镜像)
├── rl_amz_all_listing                  # Listing 主表
├── rl_amz_listing_detail               # Listing 详情扩展
├── rl_amz_sales_daily_report           # 每日销量(过去 90 天)
├── rl_amz_manage_fba_inventory         # FBA 库存快照
├── rl_amz_finances_profit_mall_100228  # 店铺日财务
├── rl_fba_shipment_item                # FBA 发货货件明细
├── rl_inventory_detail                 # 本地仓库存
├── rl_mall                             # 店铺主数据
└── rl_product                          # 商品主数据

mk_ (13 张,项目派生)
├── mk_calc_run                         # 计算批次元数据
├── mk_tenant_config                    # 租户配置
├── mk_warehouse_mapping                # 仓库映射
├── mk_listing_product_sources          # 商品视图物化(FBA only)
├── mk_supply_sku_daily_stat            # ★ 核心快照表
├── mk_sku_forecast_daily               # 未来 45 天逐日预测
├── mk_sku_inbound_detail               # 在途明细
├── mk_stockout_event                   # 断货事件
├── mk_replenishment_rule               # 补货规则(三层:全局 / 批量 / 单)
├── mk_rule_logistics_method            # 物流方式规则
├── mk_forecast_rule                    # 销量预测规则
├── mk_purchase_draft                   # 采购草稿
├── mk_holiday                          # 节假日
└── mk_export_task                      # 导出任务
```

### Calc Run 模型

业务结论以 **`calc_run_id`** 锁定一致性 — 同一批次内,Dashboard / 列表 / 详情 / AI 看到的风险等级、断货日、建议采购量必须一致。

```
1) /calc/run              生成新 calc_run_id, 物化 mk_supply_sku_daily_stat 等
2) /dashboard/snapshot    读最新 calc_run_id(或指定批次)
3) /skus/list             同上,基于 calc_run_id 过滤
4) AI 解释                 注入 calc_run_id 到 system prompt 锁口径
```

---

## AI 流式架构

```
浏览器 EventSource ──── SSE ────►  POST /ai/chat/stream
                                    │
                                    └─► AiService.chat_stream()
                                          │
                                          └─► AiOrchestrator.run_stream()
                                                │  单次 chat_stream(stream=True, tools=[...])
                                                ▼
                                          DashScopeClient.chat_stream()
                                                │  httpx.stream("POST", compat/v1/chat/completions)
                                                ▼
                                          DashScope Qwen3.6-plus

事件协议:
  data: {"type":"reasoning_delta","text":"..."}      // 思考 token(可折叠)
  data: {"type":"delta","text":"..."}                // 答复 token
  data: {"type":"tool_start","name":"query_skus",...}
  data: {"type":"tool_end","name":"query_skus","ok":true,"summary":"返回 3 条"}
  data: {"type":"done","finish_reason":"stop","tool_iterations":1}
```

**4 个 AI Tools(orchestrator 调度):**
- `query_skus` — 多条件查 SKU 列表
- `query_stockout_risk` — 查风险队列
- `get_sku_detail` — 单 SKU 详情
- `generate_purchase_draft` — 生成采购草稿(支持 dry_run / confirmed)

---

## 平迁生产

只改 `.env`,业务代码 0 修改:

```dotenv
APP_ENV=production
DATABASE_URL=mysql+aiomysql://user:pwd@db:3306/supplyai?charset=utf8mb4
CACHE_BACKEND=redis
REDIS_URL=redis://:pwd@redis:6379/0
TASK_RUNNER=celery
SUPPLY_DASH_VERIFY_SSL=true
LOG_FORMAT=json
JWT_SECRET=$(openssl rand -hex 32)
```

生产依赖:

```bash
uv sync --extra prod   # 加 aiomysql / redis / celery
uv run alembic upgrade head
uvicorn supplyai.main:app --host 0.0.0.0 --port 8000 --workers 4
```

或 docker-compose / K8s — 任何能跑 Python 3.13 + uvicorn 的运行时都行。

---

## 开发命令

```bash
# 完整测试(216+1 浏览器,需 chromium)
uv run pytest

# 仅浏览器 e2e
uv run pytest -m browser

# 跳 AI 用例(无 DashScope key 时)
uv run pytest --ignore=tests/test_ai_agent.py

# Lint + 格式化
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# 数据库迁移
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
uv run alembic downgrade -1

# DashScope 连通性自检
uv run python scripts/smoke_dashscope.py
```
