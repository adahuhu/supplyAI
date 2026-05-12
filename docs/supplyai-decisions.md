# SupplyAI 决策日志

更新时间：2026-05-09

本文用于记录 Phase 1 前的数据层、产品口径和工程实现决策。状态含义：

- `已决策`：可进入 Phase 1 开发。
- `待确认`：需要产品、后端或数据 owner 明确后再进入实现。
- `延后`：Phase 1 不处理，但保留后续追踪。

## 1. Phase 1 决策表

| 编号 | 问题 | 当前决策 | 决策人 | 决策时间 | 状态 | 备注 |
|-|-|-|-|-|-|-|
| N-3 | FBM 商品在 `mk_listing_product_sources` 是写入还是过滤？ | `mk_listing_product_sources` 保留 FBA / FBM 全量商品；`mk_supply_sku_daily_stat` 生成、备货列表、风险和采购建议仅过滤 `delivery_method = 'FBA'`。 | 产品 + 后端 | 待补 | 已决策 | 这样未来支持 FBM 时无需回填基础商品主表。 |
| N-4 | 商品基础信息变更同步策略是实时同步还是 `calc_run` 时同步？ | `mk_listing_product_sources` 按 `mk_calc_run` 前重建或刷新，不做每次请求实时 join。 | 后端 | 待补 | 已决策 | 性能更稳定；详情页需要最新原始信息时可补读 `rl_*`。 |
| N-5 | SKU 详情页直接访问 FBM URL 的兜底策略。 | Phase 1 若命中 FBM 商品，展示“暂不支持 FBM 备货分析”的兜底状态，不生成风险、断货和采购建议。 | 产品 | 待补 | 待确认 | 基础信息可展示，备货计算不展示。 |
| N-8 | 演示阶段非 USD 店铺的汇率来源。 | Phase 1 默认租户基准币种为 `USD`，演示可使用固定汇率 `1.0`；如需要真实多币种演示，由演示数据 owner 提供 mock 汇率。 | 产品 + 演示数据 owner | 待补 | 待确认 | 生产前需要接汇率服务或汇率表。 |
| P0-WH | 是否能提供真实仓库表或仓库类型映射？ | Phase 1 使用 `mk_warehouse_mapping` mock；生产前替换为 `rl_warehouse` 或真实仓库类型映射。 | 数据团队 + 后端 | 待补 | 待确认 | 影响 `local_actual` 精度。 |
| P1-FIN | SKU 级毛利是否允许展示分摊估算？ | 默认允许按店铺销售额占比分摊，并写 `financial_estimate_type = 'allocated'`；如果产品不接受估算，则 SKU 详情隐藏毛利字段。 | 产品 | 待补 | 待确认 | Dashboard 可展示店铺级真实费用/利润。 |
| P1-FBM | FBM 是否进入 Phase 1 备货计算？ | Phase 1 不进入备货计算；基础商品主表保留 FBM，备货快照只生成 FBA。 | 产品 | 待补 | 已决策 | 与 N-3 一致。 |
| P1-FX | Dashboard 多币种金额是否需要真实折算？ | Phase 1 可固定 USD + 1.0 汇率；真实折算生产前补汇率服务。 | 产品 + 后端 | 待补 | 待确认 | 影响预计采购金额跨店铺合计。 |
| **DB-001** | **本地开发使用什么数据库？** | **本地 SQLite（macOS 自带，零 daemon），生产 MySQL 8.0+；通过 SQLAlchemy ORM 抽象层切换；切换只改 `DATABASE_URL`，业务代码 0 修改。** | 工程 | 2026-05-09 | **已决策** | rl_* 表在本地 SQLite 通过 ORM 自动建表；大小写敏感字段（msku 用 BINARY collation）SQLAlchemy 已处理。 |
| **DB-002** | **本地开发是否引入 Docker / Redis / Celery？** | **本地不使用**。Docker / Redis / Celery 均推到 Phase 4 生产形态。本地缓存用 `cachetools.TTLCache`（进程内 LRU），后台任务用 FastAPI `BackgroundTasks`。 | 工程 | 2026-05-09 | **已决策** | 本地启动只需 `uv run uvicorn supplyai.main:app --reload` 一行命令。 |
| **DB-003** | **上游 rl_* 数据如何同步到 SupplyAI 本地 DB？** | 当前设计 = 离线数据表同步（无运行时调用 Amazon SP-API / 上游业务系统）。Phase 1-3 通过 `scripts/seed.py`（生成演示数据）或 `scripts/import_dump.py`（导入生产 dump）。Phase 4-5 改 Celery ETL。 | 工程 + 数据团队 | 2026-05-09 | **已决策** | 真实同步方式（CDC / API / 直读）仍待基础设施团队确认；不影响 Phase 1-3。 |
| **DB-004** | **AI 服务在本地是否需要真实 DashScope？** | 本地默认 `AI_PROVIDER=mock`（预录响应，完全离线）；演示 / 验证 AI 时切到 `AI_PROVIDER=dashscope` 并填 `DASHSCOPE_API_KEY`。 | 工程 + 产品 | 2026-05-09 | **已决策** | 抽象层在 `domain/ai/dashscope_client.py` 同接口的 `MockAiClient` 实现。 |
| **DB-005** | **本地切生产的最小改动是什么？** | 仅修改 `.env` 4 行：`DATABASE_URL`、`AI_PROVIDER`、`CACHE_BACKEND`、`TASK_RUNNER`。业务代码 0 修改。 | 工程 | 2026-05-09 | **已决策** | 所有差异都封装在 Protocol 接口背后（`CacheClient` / `TaskRunner` / `AiClient`）。 |
| **DB-006** | **SupplyAI 业务 API 使用 REST GET 还是全 POST？** | **坚持全 POST**。除健康检查 / OpenAPI 文档外，业务读写接口统一使用 `POST + JSON body`，避免复杂筛选、批量参数、前端 Adapter 和网关缓存策略在 query/path 上分叉。 | 工程 | 2026-05-10 | **已决策** | 前端 `HttpAdapter`、后端 FastAPI 路由和测试均以 `/list`、`/detail`、`/status`、`/create` 等命令式 POST 端点为准。 |

## 2. 已落地文档修订

| 编号 | 修订 | 落地位置 | 结果 |
|-|-|-|-|
| N-1 | `product_name` 补到 `mk_listing_product_sources`。 | `docs/supplyai-data-table-design.md` §4.2 | 来源 `rl_product.product_name`，缺失回退 `title`。 |
| N-2 | `local_plan` 派生公式。 | `docs/supplyai-data-table-design.md` §4.7 | 来源 `mk_sku_inbound_detail`，限定 `inbound_type` / `inbound_status`。 |
| N-6 | `fba_reserved` 用途。 | `docs/supplyai-data-table-design.md` §4.7 | 仅展示，不参与 `total_stock` 和 `fba_sellable_days`。 |
| N-7 | `risk_level` 全小写。 | `docs/supplyai-data-table-design.md` §4.7 | 存储 `p1` / `p2` / `p3` / `safe`，前端展示再映射。 |
| DB-001~005 | 本地轻量启动决策（SQLite / 进程内 LRU / BackgroundTasks / Mock AI / 4 行配置切生产） | `docs/supplyai-backend-python.md` §1 / §2 / §3 / §4 / §11 / §12 / §16.0 / §17 / §20 | 本地与生产形态完整文档化，业务代码 0 修改即可平迁。 |
| DB-006 | 业务 API 全 POST。 | 前后端约定 | 前端和后端统一以 POST body 传筛选、主键、分页、状态查询参数。 |

## 3. 后续文档动作

| 动作 | 目标 | 状态 |
|-|-|-|
| 字段映射表 v2 | 在本地补 DB 字段到 ViewModel 字段映射，交叉引用本数据表设计。 | 已处理：`docs/supplyai-field-mapping-v2.md` |
| 飞书同步 | 本地文档确认后，再统一同步到飞书知识库，避免半成品多轮覆盖。 | 待处理 |
