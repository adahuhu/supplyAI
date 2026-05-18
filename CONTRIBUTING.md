# SupplyAI 协作开发指南

这份指南用于让多人在同一个 SupplyAI 仓库中稳定协作。目标是：每个人本地可独立启动，代码通过分支和 Pull Request 合并，配置、密钥和本地数据库不进入仓库。

## 本地启动

首次拉取项目后，在仓库根目录执行：

```bash
cd supplyai-backend
uv sync
cp env.example .env
mkdir -p data
uv run alembic upgrade head
uv run python scripts/seed.py
cd ..
./start-dev.sh
```

启动后访问：

- 前端工作台：http://127.0.0.1:5173/SupplyAI.html
- API 文档：http://127.0.0.1:8000/docs
- API 调试页：http://127.0.0.1:5173/api-smoke.html

`supplyai-backend/.env` 由每位开发者本地维护，至少需要确认：

```dotenv
APP_ENV=local
DATABASE_URL=sqlite+aiosqlite:///./data/supplyai.db
SUPPLY_DASH_API_KEY=自己的 DashScope API Key
```

如果只开发非 AI 页面，也可以单独启动后端：

```bash
cd supplyai-backend
uv run uvicorn supplyai.main:app --host 127.0.0.1 --port 8000 --reload
```

前端静态服务：

```bash
cd SupplyAI
python3 -m http.server 5173 --bind 127.0.0.1
```

## 不要提交的内容

以下内容必须保留在本地，不进入 Git：

- `supplyai-backend/.env`
- `supplyai-backend/data/`
- `supplyai-backend/.venv/`
- `.codex/`
- 日志、缓存、导出文件和本地临时文件

如果发现密钥或数据库文件被误提交，先停止继续推送，通知团队一起处理历史记录和密钥轮换。

## 分支流程

推荐保持 `main` 为稳定可运行版本。所有改动从新分支开始：

```bash
git checkout main
git pull
git checkout -b feature/short-description
```

常用分支命名：

- `feature/*`：新功能
- `fix/*`：问题修复
- `chore/*`：工具、文档、依赖维护
- `codex/*`：Codex 辅助开发

开发完成后：

```bash
git status
git add <changed-files>
git commit -m "简短说明本次改动"
git push origin <branch-name>
```

通过 Pull Request 合并到 `main`。PR 描述里说明改动范围、验证方式、是否涉及数据库迁移或配置变更。

## 模块分工建议

为了减少冲突，尽量按模块分工：

- Dashboard：`SupplyAI/dashboard.jsx`，`supplyai-backend/src/supplyai/api/v1/dashboard.py`
- SKU 列表/详情：`SupplyAI/list.jsx`，`SupplyAI/sku.jsx`，`supplyai-backend/src/supplyai/api/v1/skus.py`
- 规则中心：`SupplyAI/rules.jsx`，`supplyai-backend/src/supplyai/api/v1/rules.py`
- 采购草稿：`SupplyAI/purchase*.jsx`，`supplyai-backend/src/supplyai/api/v1/purchase.py`
- AI 能力：`SupplyAI/ai.jsx`，`supplyai-backend/src/supplyai/domain/ai/`
- 数据模型和迁移：`supplyai-backend/src/supplyai/models/`，`supplyai-backend/alembic/`

容易产生冲突的文件包括：

- `SupplyAI/app.jsx`
- `SupplyAI/api.jsx`
- `SupplyAI/adapter.jsx`
- `supplyai-backend/src/supplyai/config.py`
- `supplyai-backend/alembic/versions/`

修改这些文件前，先确认是否有人正在改同一区域。

## 数据库迁移

不要提交本地 SQLite 数据库。结构变化必须通过 Alembic 迁移提交：

```bash
cd supplyai-backend
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

迁移文件需要随代码一起提交。多人同时创建迁移时，合并前要确认 revision 链路没有冲突。

## 提交前检查

提交或开 PR 前至少运行：

```bash
cd supplyai-backend
uv run pytest
```

如果改动影响浏览器交互，再启动项目手动验证：

```bash
cd ..
./start-dev.sh
```

重点检查：

- Dashboard 是否正常加载
- SKU 列表和详情是否可打开
- 规则、采购、AI 相关入口是否没有控制台错误
- 后端健康检查是否返回 `status: ok`

## PR Review 关注点

Review 时优先看：

- 是否破坏现有 API 请求/响应结构
- 后端 DTO 是否仍然是 snake_case，前端是否通过 adapter 转 camelCase
- Dashboard、列表、详情、AI 决策卡是否使用同一 `calc_run_id` 口径
- 是否误提交了 `.env`、数据库、日志或本地缓存
- 是否补充了必要测试或手动验证说明

## 团队约定

- 小步提交，避免一次 PR 混合多个主题。
- 配置变更同步更新 `supplyai-backend/env.example` 和 README。
- 数据结构变更必须带迁移。
- 遇到大范围重构，先开 issue 或文档说明方案，再动手。
