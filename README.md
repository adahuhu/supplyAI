# SupplyAI · 供应链分析工作台

亚马逊电商 **MSKU + 店铺粒度** 备货决策辅助系统。系统把 Listing、销量、库存、在途、节假日、规则和 AI 工具链聚合成可执行的补货建议。

本仓库可以在任意一台新的 **Apple Silicon Mac** 上本地运行：前端是静态 React + Babel 页面，后端是 FastAPI + SQLite，默认不依赖 Docker、MySQL、Redis 或 Node 构建链。

---

## 1. 新 Mac 快速启动

### 1.1 安装基础工具

```bash
# Xcode Command Line Tools：提供 git / clang 等基础命令
xcode-select --install

# Homebrew。如果已经安装可跳过。
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Apple Silicon Homebrew 默认路径
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# 项目依赖工具
brew install git uv
```

校验：

```bash
git --version
uv --version
python3 --version
```

`uv` 会自动为后端创建匹配的 Python 虚拟环境，不要求系统 Python 版本精确一致。

### 1.2 获取项目

```bash
git clone <YOUR_REPO_URL> supplyAI
cd supplyAI
```

如果你拿到的是压缩包，解压后进入项目根目录即可。后续命令都在仓库根目录执行，除非特别说明。

### 1.3 初始化后端

```bash
cd supplyai-backend
uv sync

cp env.example .env
```

编辑 `supplyai-backend/.env`，至少确认这几项：

```dotenv
APP_ENV=local
DATABASE_URL=sqlite+aiosqlite:///./data/supplyai.db
SUPPLY_DASH_API_KEY=你的 DashScope API Key
SUPPLY_DASH_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 本地如果使用阿里云自部署 endpoint 且遇到证书 hostname mismatch，可临时关闭。
# 官方公网建议保持 true。
SUPPLY_DASH_VERIFY_SSL=true
```

没有 DashScope key 时，Dashboard、SKU、规则、采购计划等非 AI 页面仍可开发；但 `./start-dev.sh` 会阻止启动，避免误以为 AI 链路正常。临时只跑非 AI 后端可直接执行：

```bash
cd supplyai-backend
uv run uvicorn supplyai.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

### 1.4 建库和灌演示数据

```bash
cd supplyai-backend
mkdir -p data
uv run alembic upgrade head
uv run python scripts/seed.py
cd ..
```

默认会生成本地 SQLite 数据库：`supplyai-backend/data/supplyai.db`。演示租户 ID 是 `100228`。

### 1.5 一键启动

```bash
./start-dev.sh
```

启动成功后打开：

- 前端工作台：<http://127.0.0.1:5173/SupplyAI.html>
- API 文档：<http://127.0.0.1:8000/docs>
- API 调试页：<http://127.0.0.1:5173/api-smoke.html>

`start-dev.sh` 会自动：

- 读取 `supplyai-backend/.env`
- 清理本机 `8000 / 5173` 端口占用
- 启动 FastAPI 后端 `127.0.0.1:8000`
- 在 `SupplyAI/` 目录启动静态前端服务 `127.0.0.1:5173`

按 `Ctrl-C` 会同时停止前后端。

---

## 2. 常用开发命令

### 后端

```bash
cd supplyai-backend

# 启动后端
uv run uvicorn supplyai.main:app --host 127.0.0.1 --port 8000 --reload

# 默认测试：排除 browser / slow
uv run pytest

# AI 相关测试(Smart Decision + Tool + 决策卡 + 前端契约)
uv run pytest -q tests/test_smart_decision.py tests/test_ai_tools.py tests/test_ai_new_tools.py tests/test_ai_decision_card.py tests/test_frontend_ai_contracts.py

# 浏览器 E2E
uv run pytest -m browser

# 数据库迁移
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
uv run alembic downgrade -1
```

### 前端

前端没有构建步骤，直接静态服务即可：

```bash
cd SupplyAI
python3 -m http.server 5173 --bind 127.0.0.1
```

打开 <http://127.0.0.1:5173/SupplyAI.html>。

如果需要指定后端地址：

```text
http://127.0.0.1:5173/SupplyAI.html?api=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fsupplyai
```

---

## 3. 项目结构

```text
supplyAI/
├── SupplyAI/                    # 前端：React 18 + Babel-in-browser，无 build
│   ├── SupplyAI.html            # 入口 HTML
│   ├── app.jsx                  # 路由和全局状态
│   ├── dashboard.jsx            # 分析工作台
│   ├── list.jsx                 # 备货计划列表
│   ├── sku.jsx                  # SKU 分析详情
│   ├── rules.jsx                # 规则配置 / 节日设置
│   ├── ai.jsx                   # 全局 AI / SKU AI 抽屉
│   ├── api.jsx                  # API / SSE 封装
│   ├── adapter.jsx              # snake_case DTO → camelCase ViewModel
│   └── tokens.css               # 设计 token
│
├── supplyai-backend/            # 后端：FastAPI + SQLAlchemy async + Pydantic v2
│   ├── env.example              # 本地环境变量模板
│   ├── pyproject.toml           # uv 依赖配置
│   ├── src/supplyai/            # 后端主代码
│   ├── alembic/                 # 数据库迁移
│   ├── scripts/seed.py          # 演示数据
│   └── tests/                   # 单元 / 集成 / 浏览器 E2E 测试
│
├── docs/                        # 产品、数据、技术方案文档
├── start-dev.sh                 # 一键启动脚本
└── README.md
```

---

## 4. 系统架构

```text
Browser (React 18 + Babel-in-browser, no build)
  └─ SupplyAI.html + *.jsx static files
       ├─ POST /api/supplyai/*          (JSON)
       ├─ SSE  /ai/smart-decision/stream (主 AI 入口: 分类→卡片→解释→chat退化)
       └─ SSE  /ai/explain/stream        (SKU 自动解释)

FastAPI
  ├─ Dashboard / SKU / Rules / Purchase / Calc / Export APIs
  ├─ SmartDecisionService  → 两级意图分类 → 决策卡片 → LLM 解释
  ├─ AiService             → explain / chat / decision_card
  ├─ AiOrchestrator        → LLM + 6 Tool 调度循环
  ├─ SQLAlchemy async repositories
  └─ SQLite (local) / MySQL 8 (production)

Data (21 tables)
  ├─ rl_*  (9)：真实源表镜像
  └─ mk_* (13)：SupplyAI 派生、配置、物化表
```

核心原则：

- 后端返回 snake_case DTO，前端统一在 `SupplyAI/adapter.jsx` 转 camelCase。
- Dashboard、列表、详情、AI 决策卡都以同一个 `calc_run_id` 锁定口径，数字严格一致。
- 决策卡片走后端真实服务链路（直查库，不经 LLM），保证精确性和速度。
- LLM 解释异步追加在卡片下方，负责归因和建议（可通过 `SUPPLY_CARD_EXPLAIN` 关闭）。
- 意图分类永远执行：正则命中直接出卡，LLM 分类带对话上下文区分追问和新场景。

---

## 5. 主要 API

所有业务端点默认是 `POST + JSON body`。

| 模块 | 端点 |
|---|---|
| Health | `GET /api/supplyai/_health` |
| Dashboard | `/dashboard/snapshot` `/dashboard/risk-queue` `/dashboard/finance` `/dashboard/filters` `/dashboard/holidays` |
| SKU | `/skus/list` `/skus/detail` `/skus/trends` |
| Rules | `/rules/list` `/rules/upsert` `/rules/disable` `/rules/forecast/*` |
| Purchase | `/purchase/draft/create` `/purchase/draft/list` `/purchase/draft/detail` `/purchase/draft/confirm` |
| Calc | `/calc/run` `/calc/latest` `/calc/status` |
| AI | `/ai/explain` `/ai/explain/stream` `/ai/chat` `/ai/chat/stream` `/ai/decision-card` `/ai/smart-decision/stream` |
| Exports | `/exports/sku-list` `/exports/status` `/exports/download` |

Swagger：<http://127.0.0.1:8000/docs>

---

## 6. AI 架构

### 三条 AI 链路

```text
1. SKU 解释    POST /ai/explain/stream
               → 构造 prompt(含 SKU 快照) → LLM 流式生成解释
               → 前端 extractRiskAdvice() 提取数据渲染建议卡片

2. Smart Decision  POST /ai/smart-decision/stream（主链路）
               → 两级意图分类(正则 → LLM 兜底)
               → 命中 5 种场景之一 → 后端直查库生成结构化卡片(不经 LLM)
               → 可选: LLM 流式追加 2-3 句归因解释(SUPPLY_CARD_EXPLAIN 控制)
               → 未命中 → 退化到 Orchestrator chat(LLM + Tool 调度)

3. Chat        POST /ai/chat/stream
               → Orchestrator: LLM + 工具调度循环(最多 5 轮)
               → 工具查库 → LLM 生成最终回答
```

前端 `GlobalAIPanel` 和 `SKUAIPanel` 的用户追问统一走 Smart Decision 链路。

### 5 种决策卡片场景

| 场景 | 触发正则 | 数据来源 |
|------|---------|---------|
| `risk_queue` | 高风险/必须补货/紧急度/风险队列/优先级 | Dashboard snapshot + risk queue |
| `holiday_readiness` | 大促/节日/Prime/活动备货/母亲节/黑五/圣诞 | Holiday config + SKU list |
| `plan_comparison` | 方案对比/海运/空运/海空/混合 | SKU detail + 物流方式配置表 |
| `rule_impact` | 规则模拟/安全天数/改成/调整/规则影响 | SKU list + 规则参数重算 |
| `single_sku_replenishment` | 挑一个/单个SKU/还能卖多久/要不要补 | SKU detail |

正则未命中时，LLM 分类器带对话上下文判断是新场景还是追问。追问返回 `none`，走 chat。

### Orchestrator 工具

```text
query_stockout_risk          查询风险队列
query_replenishment_advice   查询补货建议
query_sku_detail             查询 SKU 详情
compare_logistics_options    物流方案对比(基于真实配置,无硬编码兜底)
simulate_event_demand        模拟大促需求
generate_purchase_draft      生成采购计划(需前端二次确认)
```

### 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `SUPPLY_DASH_API_KEY` | 必填 | DashScope API key |
| `SUPPLY_DASH_ENABLE_THINKING` | `true` | LLM 思维链(折叠面板实时展示,关闭可降首字延迟) |
| `SUPPLY_CARD_EXPLAIN` | `true` | 决策卡片后是否追加 LLM 归因解释 |

---

## 7. 常见问题

### `./start-dev.sh` 提示没有 API key

确认已经创建并填写：

```bash
supplyai-backend/.env
```

至少需要：

```dotenv
SUPPLY_DASH_API_KEY=sk-...
```

`start-dev.sh` 会自动读取这个文件，不需要手动 `export`。

### 端口被占用

`start-dev.sh` 会自动清理 `8000 / 5173`。如果手动启动，可执行：

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

### Apple Silicon 上依赖安装慢或失败

优先确认使用的是 `/opt/homebrew`：

```bash
which brew
which uv
uname -m
```

期望：

```text
/opt/homebrew/bin/brew
/opt/homebrew/bin/uv
arm64
```

然后重试：

```bash
cd supplyai-backend
uv sync --reinstall
```

### 修改 `.env` 后不生效

重启后端。配置只在进程启动时读取。

### SQLite 想重置

```bash
cd supplyai-backend
rm -f data/supplyai.db
uv run alembic upgrade head
uv run python scripts/seed.py
```

---

## 8. 生产部署提示

本地默认 SQLite + memory cache + local task runner。生产可只改 `.env`：

```dotenv
APP_ENV=production
DATABASE_URL=mysql+aiomysql://user:pwd@db:3306/supplyai?charset=utf8mb4
CACHE_BACKEND=redis
REDIS_URL=redis://:pwd@redis:6379/0
TASK_RUNNER=celery
LOG_FORMAT=json
JWT_SECRET=<openssl rand -hex 32>
SUPPLY_DASH_VERIFY_SSL=true
```

生产依赖：

```bash
cd supplyai-backend
uv sync --extra prod
uv run alembic upgrade head
uv run uvicorn supplyai.main:app --host 0.0.0.0 --port 8000 --workers 4
```

前端 `SupplyAI/` 是静态文件目录，可由 nginx / CDN 托管。当前开发态使用 Babel-in-browser，生产建议预编译或继续按静态 Demo 方式部署。

---

## 9. 文档导航

- 后端详细说明：[supplyai-backend/README.md](supplyai-backend/README.md)
- 后端架构：[docs/supplyai-backend-python.md](docs/supplyai-backend-python.md)
- 数据表设计：[docs/supplyai-data-table-design.md](docs/supplyai-data-table-design.md)
- 字段映射：[docs/supplyai-field-mapping-v2.md](docs/supplyai-field-mapping-v2.md)
- 决策日志：[docs/supplyai-decisions.md](docs/supplyai-decisions.md)
- 前端设计原则：[SupplyAI/DESIGN.md](SupplyAI/DESIGN.md)

---

## License

Private project. Internal use only.
