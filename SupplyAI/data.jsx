// Mock data layer — SKU rows, dashboard aggregates, AI canned responses.
// All values are illustrative — designed to read realistically at a glance.

const COUNTRIES = [
  { code: 'US', flag: '🇺🇸', name: '美国' },
  { code: 'DE', flag: '🇩🇪', name: '德国' },
  { code: 'UK', flag: '🇬🇧', name: '英国' },
  { code: 'JP', flag: '🇯🇵', name: '日本' },
  { code: 'CA', flag: '🇨🇦', name: '加拿大' },
  { code: 'FR', flag: '🇫🇷', name: '法国' },
];

const STORES = ['Aurora-US01', 'Aurora-DE02', 'Nordic-UK01', 'Sakura-JP01', 'Aurora-CA01', 'Aurora-FR01'];
const OWNERS = ['李婧', '王诚', '张默', '赵磊', '陈萌', '刘洋'];
const TAGS = [
  ['爆款', '主推'],
  ['新品'],
  ['长尾'],
  ['清仓'],
  ['节日'],
  ['主推'],
  [],
];

const PRODUCTS = [
  { name: '便携真空保温水杯 500ml 哑光黑', cat: '家居 / 厨房' },
  { name: '可调节人体工学桌面支架 V2', cat: '办公 / 配件' },
  { name: '硅胶折叠便携漏斗 4 件套', cat: '家居 / 厨房' },
  { name: '宠物自动喂食器 6L 智能版', cat: '宠物 / 喂食' },
  { name: '户外露营便携折叠椅 加固版', cat: '户外 / 装备' },
  { name: '车载手机磁吸支架 Pro', cat: '汽配 / 支架' },
  { name: 'LED 化妆镜 三色调光款', cat: '美妆 / 工具' },
  { name: '儿童硅胶围嘴防水款 2 件装', cat: '母婴 / 喂养' },
  { name: '不锈钢厨房收纳挂篮 大号', cat: '家居 / 收纳' },
  { name: '蓝牙运动耳机 IPX7 防水', cat: '数码 / 音频' },
  { name: '健身阻力带 5 件套 加厚', cat: '运动 / 健身' },
  { name: '便携式电动榨汁杯 USB 充', cat: '家居 / 厨房' },
  { name: '木质书桌收纳分隔架', cat: '办公 / 收纳' },
  { name: '可折叠瑜伽垫 6mm TPE', cat: '运动 / 健身' },
  { name: '汽车后备箱整理收纳箱', cat: '汽配 / 收纳' },
  { name: '宠物自动饮水器 4L 静音', cat: '宠物 / 饮水' },
  { name: '智能定时插座 WiFi 版', cat: '数码 / 智能家居' },
  { name: '便携式蒸汽挂烫机 1500W', cat: '家居 / 清洁' },
  { name: '不粘锅炒锅 28cm 麦饭石', cat: '家居 / 厨房' },
  { name: '婴儿便携餐椅 折叠款', cat: '母婴 / 喂养' },
  { name: '户外便携头灯 USB 充电', cat: '户外 / 装备' },
  { name: '亚麻沙发坐垫 45×45 4 件', cat: '家居 / 软装' },
  { name: '电动牙刷 声波震动 IPX7', cat: '美妆 / 个护' },
  { name: '硅胶冰格 球形 大颗 2 件', cat: '家居 / 厨房' },
  { name: '可降解垃圾袋 加厚 100 只', cat: '家居 / 清洁' },
];

function makeSeries(seed, base, drift = 0.08) {
  let v = base;
  const out = [];
  for (let i = 0; i < 30; i++) {
    seed = (seed * 9301 + 49297) % 233280;
    const r = (seed / 233280 - 0.5) * 2;
    v = Math.max(0, v + r * base * drift + (i > 20 ? -base * 0.02 : 0));
    out.push(Math.round(v));
  }
  return out;
}

function predictSeries(history, futureDaily, days = 14) {
  const out = [];
  for (let i = 0; i < days; i++) {
    out.push(Math.max(0, Math.round(futureDaily * (0.92 + (i % 5) * 0.04))));
  }
  return out;
}

function buildSku(i) {
  const country = COUNTRIES[i % COUNTRIES.length];
  const store = STORES[i % STORES.length];
  const owner = OWNERS[i % OWNERS.length];
  const product = PRODUCTS[i % PRODUCTS.length];
  const tags = TAGS[i % TAGS.length];
  const msku = 'MS' + String(40021 + i * 13).slice(-5);
  const sku = 'SKU-' + String(70000 + i * 7).slice(-5) + '-' + country.code;
  const asin = 'B0' + (i * 17 + 113).toString(36).toUpperCase().padEnd(7, 'X').slice(0, 8);
  const fnsku = 'X00' + (i * 31 + 417).toString(36).toUpperCase().padEnd(6, 'A').slice(0, 7);

  // Sales
  const baseDaily = [62, 38, 27, 19, 14, 11, 9, 7, 5, 4][i % 10] + (i % 3);
  const histRaw = makeSeries(i + 7, baseDaily);
  const recent7 = histRaw.slice(-7);
  const last7Daily = +(recent7.reduce((a, b) => a + b, 0) / 7).toFixed(1);
  const last7Denoised = +(last7Daily * 0.94).toFixed(1);
  const futureDaily = Math.max(1, Math.round(last7Denoised));
  const future14 = predictSeries(histRaw, futureDaily, 14);
  const future30 = predictSeries(histRaw, futureDaily, 30);

  // Inventory
  const fbaAvail = [220, 180, 95, 240, 60, 320, 110, 28, 410, 72][i % 10] + (i * 3) % 60;
  const fbaInTransit = [80, 0, 60, 0, 120, 0, 0, 0, 200, 0][i % 10];
  const localActual = [400, 260, 320, 0, 180, 220, 0, 110, 540, 30][i % 10];
  const localPlan = [200, 0, 0, 0, 80, 0, 0, 0, 0, 0][i % 10];
  const localTotal = localActual + localPlan;
  const totalStock = fbaAvail + fbaInTransit + localTotal;

  const safeDays = 14;
  const purchaseDuration = 12 + (i % 5);
  const purchaseDelivery = 5;
  const qcDays = 3;
  const logistics = (i % 3 === 0) ? { mode: '海运', days: 35 } : (i % 3 === 1 ? { mode: '空运', days: 8 } : { mode: '快船', days: 18 });
  const purchaseLeadTime = purchaseDuration + purchaseDelivery + qcDays + logistics.days;
  const totalCoverage = purchaseLeadTime + safeDays;

  const sellable = Math.round(totalStock / Math.max(1, futureDaily));
  // Stockout time uses FBA only
  const fbaSellable = Math.round((fbaAvail + fbaInTransit) / Math.max(1, futureDaily));

  let priority;
  if (sellable <= 7) priority = 'p1';
  else if (sellable <= 15) priority = 'p2';
  else if (sellable <= 30) priority = 'p3';
  else priority = 'safe';

  const coverageDemand = Math.round(totalCoverage * futureDaily);
  const suggestQty = Math.max(0, coverageDemand - totalStock);
  const suggest = suggestQty > 0;

  // Date math (relative to "today")
  const today = new Date('2026-05-04');
  const stockoutDate = new Date(today.getTime() + fbaSellable * 86400000);
  const purchaseDate = new Date(stockoutDate.getTime() - purchaseLeadTime * 86400000);

  const price = +(8.99 + (i % 9) * 1.7).toFixed(2);
  const cost = +(price * 0.42).toFixed(2);
  const revenue7 = +(price * recent7.reduce((a, b) => a + b, 0)).toFixed(0);
  const expense7 = +(revenue7 * 0.51).toFixed(0);
  const grossProfit7 = revenue7 - expense7 - cost * recent7.reduce((a, b) => a + b, 0);
  const grossMargin = +((grossProfit7 / Math.max(1, revenue7)) * 100).toFixed(1);

  return {
    id: msku + '-' + store,
    msku, sku, asin, fnsku,
    name: product.name,
    category: product.cat,
    image: `https://placehold.co/96x96/${i % 2 ? 'f1f5f9' : 'e2e8f0'}/64748b?text=${encodeURIComponent(msku.slice(-3))}`,
    store, country, owner, tags,
    status: i % 17 === 0 ? '已下架' : '在售',
    listingTags: i % 5 === 0 ? ['BSR Top 100'] : (i % 7 === 0 ? ['Coupon'] : []),
    brand: ['NORDIC', 'AURORA', 'SAKURA', 'MOMENT'][i % 4],
    line: ['家居线 A', '户外线', '母婴线', '数码线'][i % 4],

    // sales
    histRaw, recent7, last7Daily, last7Denoised, futureDaily, future14, future30,

    // financial
    price, cost,
    revenue7, expense7, grossProfit7, grossMargin,

    // inventory
    fbaAvail, fbaInTransit, localActual, localPlan, localTotal, totalStock,

    // metrics
    sellable, fbaSellable, safeDays, purchaseLeadTime, totalCoverage,
    purchaseDuration, purchaseDelivery, qcDays, logistics,
    coverageDemand,

    // result
    priority, suggest, suggestQty,
    stockoutDate, purchaseDate,

    lastUpdated: new Date(today.getTime() - (i * 1800 + 600) * 1000),
  };
}

const SKUS = Array.from({ length: 48 }, (_, i) => buildSku(i));

// Sort to match default ordering: P1 > P2 > P3 > safe; within tier: stockout date asc; then lastUpdated desc.
const PRIORITY_ORDER = { p1: 0, p2: 1, p3: 2, safe: 3 };
SKUS.sort((a, b) => {
  if (PRIORITY_ORDER[a.priority] !== PRIORITY_ORDER[b.priority]) {
    return PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
  }
  if (a.stockoutDate.getTime() !== b.stockoutDate.getTime()) {
    return a.stockoutDate.getTime() - b.stockoutDate.getTime();
  }
  return b.lastUpdated.getTime() - a.lastUpdated.getTime();
});

const DASH_STATS = (() => {
  const counts = { p1: 0, p2: 0, p3: 0, safe: 0 };
  let stockout7 = 0;
  let suggestSkuCount = 0;
  let suggestTotalQty = 0;
  let totalStock = 0;
  let totalSales7 = 0;
  for (const s of SKUS) {
    counts[s.priority]++;
    if (s.fbaSellable <= 7) stockout7++;
    if (s.suggest) {
      suggestSkuCount++;
      suggestTotalQty += s.suggestQty;
    }
    totalStock += s.totalStock;
    totalSales7 += s.recent7.reduce((a, b) => a + b, 0);
  }
  // Yesterday's financials aggregated across SKUs (last day of recent7 window)
  let salesY = 0, gmvY = 0, costY = 0, expenseY = 0, profitY = 0;
  for (const s of SKUS) {
    const qY = s.recent7[s.recent7.length - 1] || 0;
    const rev = qY * s.price;
    const exp = rev * 0.51;       // platform fees, ads, shipping
    const cogs = qY * s.cost;     // goods cost
    salesY += qY;
    gmvY += rev;
    costY += cogs;
    expenseY += exp;
    profitY += rev - exp - cogs;
  }
  // 7-day spark trends
  const trendOf = (fn) => Array.from({ length: 7 }, (_, i) =>
    SKUS.reduce((sum, s) => sum + fn(s, i), 0)
  );
  const salesTrend = trendOf((s, i) => s.recent7[i] || 0);
  const salesTrendPct = salesTrend.length > 1
    ? (salesTrend[salesTrend.length - 1] - salesTrend[salesTrend.length - 2]) / Math.max(1, salesTrend[salesTrend.length - 2]) * 100
    : null;
  const gmvTrend = trendOf((s, i) => (s.recent7[i] || 0) * s.price);
  const costTrend = trendOf((s, i) => (s.recent7[i] || 0) * s.cost);
  const expenseTrend = trendOf((s, i) => (s.recent7[i] || 0) * s.price * 0.51);
  const profitTrend = trendOf((s, i) => {
    const q = s.recent7[i] || 0;
    return q * s.price - q * s.price * 0.51 - q * s.cost;
  });

  // Aged inventory: SKUs with > 90 days of cover (proxy for >90d 库龄 — slow-mover risk)
  const overstockCount = SKUS.filter(s => s.sellable > 90).length;
  const overstockQty = SKUS
    .filter(s => s.sellable > 90)
    .reduce((sum, s) => sum + s.totalStock, 0);

  // 近 7 天每天的"新增断货 SKU 数" — 当日库存=0 即视为断货
  // 用 fbaSellable 反推：fbaSellable=0 表示今天已断货；fbaSellable=k 表示 k 天后断货
  // 历史日 d (d=0..6, 0=今天往前推 6 天)：把 sellable+ (今天-d) 等于 0 的近似为当日断货
  // 这里用一组合理的小数据填充
  const stockoutTrend = [2, 3, 5, 4, 7, 6, 9]; // 6 天前 → 今天
  const stockoutTrendTotal = stockoutTrend.reduce((a, b) => a + b, 0);

  return {
    counts, stockout7, suggestSkuCount, suggestTotalQty,
    totalStock, totalSales7,
    salesY,
    salesTrend,
    salesTrendPct,
    gmvY: Math.round(gmvY),
    costY: Math.round(costY),
    expenseY: Math.round(expenseY),
    profitY: Math.round(profitY),
    gmvTrend, costTrend, expenseTrend, profitTrend,
    overstockCount, overstockQty,
    stockoutTrend, stockoutTrendTotal,
    healthScore: 76, // composite
    asOf: new Date('2026-05-04T08:42:00'),
  };
})();

// Today's recommended actions
const TODAY_ACTIONS = [
  { id: 'a1', kind: 'urgent', title: '紧急采购：3 个 SKU 将在 5 天内断货', count: 3, action: '立即处理' },
  { id: 'a2', kind: 'review', title: '12 个 SKU 触发新风险等级（上次扫描后）', count: 12, action: '查看变化' },
  { id: 'a3', kind: 'rule', title: '4 个高销量 SKU 仍在使用全局规则', count: 4, action: '配置特配' },
  { id: 'a4', kind: 'forecast', title: '7 个 MSKU 的销量预测样本不足', count: 7, action: '检查预测' },
];

// AI canned responses keyed by question intent
const SKU_AI_PRESETS = (sku) => ([
  {
    q: '为什么它是 ' + sku.priority.toUpperCase() + '？',
    a: {
      conclusion: `${sku.msku} · ${sku.store} 当前为 ${sku.priority.toUpperCase()} 级风险，FBA 侧预计在 ${sku.fbaSellable} 天内断货。`,
      factors: [
        { k: 'FBA 可用 + 在途', v: `${sku.fbaAvail + sku.fbaInTransit} 件` },
        { k: '未来日销（最终）', v: `${sku.futureDaily} 件 / 天` },
        { k: '可售天数（FBA）', v: `${sku.fbaSellable} 天` },
        { k: '风险阈值', v: 'P1 ≤ 7d · P2 8–15d · P3 16–30d' },
      ],
      basis: [
        '近 7 天日销 ' + sku.last7Daily + '（去噪后 ' + sku.last7Denoised + '）',
        '当前规则下采用动态销量推算，未来日销取整为 ' + sku.futureDaily,
        'FBA 在途到货前预计已售罄，风险按 FBA 侧时间口径判定',
      ],
      caveats: ['本地库存与本地预计未参与断货时间判定，仅参与建议采购量计算'],
      actions: ['生成采购计划', '查看销量预测来源', '调整安全天数'],
    },
  },
  {
    q: '为什么建议采购这个数量？',
    a: {
      conclusion: `建议采购 ${sku.suggestQty} 件，覆盖 ${sku.totalCoverage} 天总覆盖周期所需库存。`,
      factors: [
        { k: '覆盖周期需求', v: `${sku.coverageDemand} 件 = ${sku.totalCoverage}d × ${sku.futureDaily}` },
        { k: '当前总库存', v: `${sku.totalStock} 件` },
        { k: '建议采购', v: `${sku.coverageDemand} − ${sku.totalStock} = ${sku.suggestQty}` },
        { k: '采购时效', v: `${sku.purchaseLeadTime} 天` },
        { k: '安全天数', v: `${sku.safeDays} 天` },
      ],
      basis: ['物流方式取最长项参与计算（' + sku.logistics.mode + ' · ' + sku.logistics.days + 'd）'],
      caveats: ['本期不考虑节日备货系数'],
      actions: ['生成采购计划', '微调安全天数', '修改物流方式'],
    },
  },
  {
    q: '如果安全天数改成 21 天会怎样？',
    a: {
      conclusion: `安全天数 14 → 21，建议采购量将从 ${sku.suggestQty} 增加至约 ${sku.suggestQty + sku.futureDaily * 7} 件。`,
      factors: [
        { k: '总覆盖周期', v: `${sku.totalCoverage} → ${sku.totalCoverage + 7} 天` },
        { k: '覆盖周期需求', v: `+${sku.futureDaily * 7} 件` },
        { k: '断货时间判定', v: '不变（仅采购量受影响）' },
      ],
      basis: ['假设其他参数与当前规则保持一致'],
      caveats: ['仅为模拟，未保存到规则'],
      actions: ['打开规则设置', '保存为特配规则'],
    },
  },
  {
    q: '哪些因素影响最大？',
    a: {
      conclusion: '当前 SKU 风险敏感度排序：未来日销 > FBA 在途到货时间 > 物流时长。',
      factors: [
        { k: '未来日销 ±10%', v: '风险等级可能跨档' },
        { k: 'FBA 在途到货 +3d', v: '影响 P1/P2 临界判定' },
        { k: '物流时长 ±5d', v: '改变建议采购时间' },
      ],
      basis: ['基于当前规则与最近一次计算快照'],
      actions: ['查看销量预测设置', '调整物流方式'],
    },
  },
]);

const GLOBAL_AI_PRESETS = [
  {
    q: '今天该关注什么？',
    a: {
      conclusion: '今日有 3 个 SKU 在 5 天内将断货，建议优先处理。',
      list: [
        { msku: 'MS40034', store: 'Aurora-US01', why: 'FBA 可售 4 天，在途未到', priority: 'p1' },
        { msku: 'MS40047', store: 'Aurora-DE02', why: '德国仓清零，本地无补给', priority: 'p1' },
        { msku: 'MS40060', store: 'Nordic-UK01', why: '近 7 天销量 +38% 突增', priority: 'p1' },
      ],
      actions: ['生成采购计划（3 项）', '一键打开高风险队列'],
    },
  },
  {
    q: '哪些 SKU 快断货了？',
    a: {
      conclusion: '7 天内将断货的 SKU 共 9 个，其中 3 个采购时效大于剩余天数。',
      list: [
        { msku: 'MS40034', store: 'Aurora-US01', why: '剩 4d，需空运补救', priority: 'p1' },
        { msku: 'MS40047', store: 'Aurora-DE02', why: '剩 5d，需空运补救', priority: 'p1' },
        { msku: 'MS40060', store: 'Nordic-UK01', why: '剩 6d，可常规采购', priority: 'p1' },
      ],
      actions: ['批量勾选并生成采购计划'],
    },
  },
  {
    q: '哪些规则还没配置？',
    a: {
      conclusion: '4 个高销量 MSKU 当前使用全局规则，建议配置特配。',
      list: [
        { msku: 'MS40021', store: 'Aurora-US01', why: '日销 62，超均值 7×', priority: 'p3' },
        { msku: 'MS40060', store: 'Nordic-UK01', why: '波动大，建议固定日销', priority: 'p1' },
      ],
      actions: ['批量打开规则设置'],
    },
  },
];

Object.assign(window, {
  SKUS, DASH_STATS, TODAY_ACTIONS,
  COUNTRIES, STORES, OWNERS,
  SKU_AI_PRESETS, GLOBAL_AI_PRESETS,
  PRIORITY_ORDER,
});
