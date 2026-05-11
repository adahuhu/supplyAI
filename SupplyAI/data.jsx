// data.jsx — 空骨架,数据完全靠后端 bootstrap 填充。
// 历史:这里曾经是 mock SKU 生成器,2026-05-10 全面切到真实链路后清空。
//
// app.jsx 在挂载时会调 /dashboard/snapshot + /skus/list,
// 通过 adapter.jsx 把 DTO 转成 ViewModel 后,原地填进 window.SKUS / window.DASH_STATS。

const SKUS = [];

// 工作台聚合数据 — 字段集合见 adapter.adaptDashStats
const DASH_STATS = {
  counts: { p1: 0, p2: 0, p3: 0, safe: 0 },
  stockout7: 0,
  suggestSkuCount: 0,
  suggestTotalQty: 0,
  suggestTotalAmountBase: 0,
  suggestTotalAmountByCurrency: [],
  totalStock: 0,
  totalSales7: 0,
  asOf: new Date(),
  calcRunId: null,
  salesY: 0,
  salesTrend: [],
  salesTrendPct: null,
  gmvY: 0,
  costY: 0,
  expenseY: 0,
  profitY: 0,
  gmvTrend: [],
  costTrend: [],
  expenseTrend: [],
  profitTrend: [],
  overstockCount: 0,
  overstockQty: 0,
  stockoutTrend: [],
  stockoutTrendTotal: 0,
  healthScore: 0,
};

// 待"需关注"端点上线后填充;前端 dashboard 已做空状态处理
const TODAY_ACTIONS = [];

// 优先级排序 — 与后端列表默认排序一致(p1 > p2 > p3 > safe)
const PRIORITY_ORDER = { p1: 0, p2: 1, p3: 2, safe: 3 };

Object.assign(window, {
  SKUS,
  DASH_STATS,
  TODAY_ACTIONS,
  PRIORITY_ORDER,
});
