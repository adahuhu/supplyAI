# SupplyAI 后端

供应链分析工作台后端服务（Python 单服务）。

## 相关文档

- [后端技术方案](../docs/supplyai-backend-python.md) — 21 章节完整设计
- [数据表设计](../docs/supplyai-data-table-design.md) — 14 张表 + SQLite 兼容
- [字段映射表 v2](../docs/supplyai-field-mapping-v2.md) — DB ↔ ViewModel
- [决策日志](../docs/supplyai-decisions.md) — 设计决策审计

## 本地启动（macOS 直跑，无 Docker）

### 一次性配置

```bash
# 1. 装 uv（包管理器）
brew install uv

# 2. 装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env

# 4. 准备 SQLite 数据库 + 演示数据
mkdir -p data
uv run alembic upgrade head
uv run python scripts/seed.py
```

### 每次启动

```bash
uv run uvicorn supplyai.main:app --reload --port 8000
```

打开：

- API: http://localhost:8000/api/supplyai/_health
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
src/supplyai/
├── main.py                # FastAPI app entry
├── config.py              # pydantic-settings
├── deps.py                # FastAPI 依赖注入
├── db.py                  # SQLAlchemy engine + session
├── api/v1/                # REST 路由
├── schemas/               # Pydantic DTO
├── models/                # SQLAlchemy ORM (rl_* + mk_*)
├── repositories/          # 查询封装
├── services/              # 应用服务
├── domain/                # 业务规则
│   ├── calc_engine/       # 销量预测、覆盖周期、风险派生
│   ├── rule_engine/       # 三层规则解析
│   └── ai/                # Qwen + 4 Tools + Foundation Skills
├── tasks/                 # 任务调度抽象（local / celery）
├── cache/                 # 缓存抽象（in-memory / redis）
└── utils/                 # 工具
```

## 平迁生产

仅修改 `.env`，业务代码 0 修改：

```bash
DATABASE_URL=mysql+aiomysql://user:pwd@db:3306/supplyai
AI_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-...
CACHE_BACKEND=redis
TASK_RUNNER=celery
```

并安装生产依赖：

```bash
uv sync --extra prod
```

## 开发命令

```bash
# 测试
uv run pytest

# 类型检查
uv run mypy src/

# Lint + 格式化
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# 数据库迁移
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
uv run alembic downgrade -1

# 导出 OpenAPI（给前端 zod 自动同步）
uv run python scripts/export_openapi.py > openapi.json
```

## Phase 实施进度

- [x] **Phase 1（前端）**：mock 数据自闭环
- [ ] **Phase 2（后端骨架）**：项目初始化、ORM 模型、空 API 骨架 ← 当前
- [ ] **Phase 3**：Calc Engine + Rule Engine + 演示数据生成
- [ ] **Phase 4**：API 完整实现 + AI Orchestrator + 前后端联调
- [ ] **Phase 5**：鉴权 / 监控 / 上线 MySQL
