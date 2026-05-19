// adapter.jsx — 后端 snake_case DTO → 前端 camelCase ViewModel.
// 字段对照表见技术文档 field-mapping-v2 §2。
// 缺失字段以合理默认填充,UI 容错。

(function () {
  const COUNTRY_TABLE = {
    US: { code: 'US', flag: '🇺🇸', name: '美国' },
    DE: { code: 'DE', flag: '🇩🇪', name: '德国' },
    UK: { code: 'UK', flag: '🇬🇧', name: '英国' },
    GB: { code: 'UK', flag: '🇬🇧', name: '英国' },
    JP: { code: 'JP', flag: '🇯🇵', name: '日本' },
    CA: { code: 'CA', flag: '🇨🇦', name: '加拿大' },
    FR: { code: 'FR', flag: '🇫🇷', name: '法国' },
  };

  const FALLBACK_COUNTRY = { code: '--', flag: '🏳️', name: '未知' };

  function toDate(v) {
    if (!v) return null;
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d;
  }

  function toCountry(code) {
    if (!code) return FALLBACK_COUNTRY;
    return COUNTRY_TABLE[code.toUpperCase()] || { ...FALLBACK_COUNTRY, code };
  }

  function normalizeNumberList(v) {
    return Array.isArray(v)
      ? v.map(x => Number(x || 0)).filter(x => Number.isFinite(x))
      : [];
  }

  function parseLabelIds(value) {
    if (Array.isArray(value)) return value.map(x => String(x || '').trim()).filter(Boolean);
    return String(value || '')
      .split(/[,，;；|\/]+/)
      .map(x => x.trim())
      .filter(Boolean);
  }

  function stockScopeLabel(scope) {
    const labels = {
      fba_available: 'FBA 可用',
      fba_inbound: '在途',
      local_actual: '本地实际',
      local_plan: '本地预计',
    };
    const values = Array.isArray(scope) && scope.length ? scope : ['fba_available'];
    return values.map(key => labels[key] || key).join(' + ');
  }

  function isRecentStockout7(row) {
    const fba7 = normalizeNumberList(
      row.fba_available_7d || row.fba_available_recent_7d || row.fba_available_history_7d
    );
    if (fba7.length >= 7) return fba7.slice(-7).every(v => v <= 0);
    if (row.stockout_recent_7 != null) return !!row.stockout_recent_7;
    return false;
  }

  function adaptSkuSummary(row) {
    const country = toCountry(row.country_code);
    const fbaInTransit = row.fba_inbound || 0;
    const fbaAvail = row.fba_available || 0;
    const localActual = row.local_actual || 0;
    const localPlan = row.local_plan || 0;
    const fbaAvailable7 = normalizeNumberList(
      row.fba_available_7d || row.fba_available_recent_7d || row.fba_available_history_7d
    );
    const stockoutRecent7 = isRecentStockout7(row);
    const tags = (Array.isArray(row.tags) && row.tags.length)
      ? parseLabelIds(row.tags)
      : parseLabelIds(row.label_ids);
    const stockScope = Array.isArray(row.stock_scope) && row.stock_scope.length
      ? row.stock_scope
      : ['fba_available'];
    return {
      // 标识 — id 用 String(listing_id) 保持路由兼容
      id: String(row.id),
      listingId: row.listing_id,
      mallId: row.mall_id,
      mall_id: row.mall_id,  // 别名,有些代码直接 s.mall_id 读
      msku: row.msku,
      sku: row.sku,
      asin: row.asin,
      fnsku: row.fnsku,
      name: row.product_name || '',
      category: row.category || '',
      image: row.image_url || `https://placehold.co/96x96/e2e8f0/64748b?text=${encodeURIComponent((row.msku || '?').slice(-3))}`,
      brand: row.brand || '',
      line: '',
      labelIds: row.label_ids || tags.join(','),
      tags,
      listingTags: tags,
      store: row.store_name || '—',
      country,
      owner: row.owner || '',
      status: row.listing_status === 'inactive' ? '已下架' : '在售',
      deliveryMethod: row.delivery_method || 'FBA',

      // 风险 / 销量
      priority: row.priority,
      yesterdaySales: row.yesterday_sales,
      futureDaily: row.future_daily ?? 0,
      forecastSource: row.forecast_source || 'default',
      coverageDemand: row.coverage_demand ?? 0,

      // 库存
      fbaAvail, fbaInTransit, localActual, localPlan,
      fbaAvailable7,
      stockoutRecent7,
      localTotal: localActual + localPlan,
      totalStock: row.total_stock ?? 0,
      planningStock: row.planning_stock ?? row.fba_available ?? 0,
      stockScope,
      stockScopeLabel: stockScopeLabel(stockScope),
      sellable: row.sellable_days != null ? +(+row.sellable_days).toFixed(2) : 0,
      fbaSellable: row.fba_sellable_days != null ? +(+row.fba_sellable_days).toFixed(2) : 0,
      localSellable: row.local_sellable_days != null ? +(+row.local_sellable_days).toFixed(2) : 0,

      // 时效 / 建议
      safeDays: row.safety_days ?? 14,
      purchaseLeadTime: row.lead_time_days ?? 0,
      totalCoverage: (row.lead_time_days ?? 0) + (row.safety_days ?? 0),
      stockoutDate: toDate(row.stockout_date),
      purchaseDate: toDate(row.purchase_date),

      // 新增运营字段 — 真实来自后端 (rl_fba_shipment_item / mk_purchase_draft / mk_sku_inbound_detail)
      lastShipmentAt: toDate(row.last_shipment_date),  // 上次发货时间
      lastPurchaseAt: toDate(row.last_purchase_date),  // 上次采购时间(来自最近的采购计划 confirmed_at)
      estimatedArrivalAt: toDate(row.estimated_arrival_date), // 最早一笔在途的预计到货
      suggest: !!row.suggest,
      suggestQty: row.suggest_qty || 0,
      suggestAmount: row.suggest_amount,
      suggestAmountBase: row.suggest_amount_base,
      baseCurrency: row.base_currency || 'USD',

      // 财务(部分字段缺失,UI 容错)
      revenue7: row.revenue_7d,
      expense7: row.expense_7d,
      cost7: row.cost_7d,
      grossProfit7: row.gross_profit_7d,
      grossMargin: row.gross_margin != null ? row.gross_margin * 100 : null,
      financialEstimateType: row.financial_estimate_type || 'hidden',

      // 列表 cell + 详情图初始数据 — 来自后端真实日报派生(过去 7 天)
      recent7: row.recent_7d || [],
      last7Daily: (row.recent_7d && row.recent_7d.length)
        ? +(row.recent_7d.reduce((a, b) => a + b, 0) / row.recent_7d.length).toFixed(1)
        : 0,
      last7Denoised: (row.recent_7d && row.recent_7d.length)
        ? +(row.recent_7d.reduce((a, b) => a + b, 0) / row.recent_7d.length * 0.94).toFixed(1)
        : 0,
      sales7d: row.sales_7d ?? null,
      // 历史完整序列 (90d) 仍在详情页通过 trends 端点拿
      histRaw: [],
      future14: [],
      future30: [],

      // 占位:这些在 mock 中存在,前端某些卡片读取
      price: null,
      cost: row.unit_cost ? Number(row.unit_cost) : null,
      purchaseDuration: 0,
      purchaseDelivery: 0,
      qcDays: 0,
      logistics: { mode: '—', days: 0 },

      // 元数据
      lastUpdated: toDate(row.last_updated) || new Date(),
      calcRunId: row.calc_run_id,
    };
  }

  function adaptFinance(financeResp) {
    if (!financeResp) return null;
    const m = (k) => ({
      value: financeResp[k]?.value ?? 0,
      pctChange: financeResp[k]?.pct_change ?? null,
    });
    return {
      asOfDate: financeResp.as_of_date,
      currency: financeResp.currency || 'USD',
      sales: m('sales'),
      gmv: m('gmv'),
      cost: m('cost'),
      expense: m('expense'),
      profit: m('profit'),
    };
  }

  function adaptStores(storesResp) {
    return (storesResp?.rows || []).map(r => ({
      mallId: r.mall_id,
      name: r.mall_name,
      countryCode: r.country_code,
      skuCount: r.sku_count,
      p1: r.p1_count,
      p2: r.p2_count,
      p3: r.p3_count,
      safe: r.safe_count,
      risk: r.p1_count,  // 侧栏只展示 P1 角标
    }));
  }

  function adaptFilters(filtersResp) {
    return {
      stores: filtersResp?.stores || [],
      countries: filtersResp?.countries || [],
      owners: filtersResp?.owners || [],
    };
  }

  function adaptAlerts(alertsResp) {
    return (alertsResp?.alerts || []).map(a => ({
      id: a.id,
      kind: a.kind,
      title: a.title,
      count: a.count,
      action: a.action,
    }));
  }

  function adaptHolidays(holidaysResp) {
    return (holidaysResp?.holidays || []).map(h => ({
      id: h.id,
      name: h.name,
      flag: h.flag,
      peak: h.peak_date,  // YYYY-MM-DD
      sb: h.days_before,
      sa: h.days_after,
      dm: h.sales_multiplier,  // demand multiplier
      color: h.color || '#3b82f6',
      countryCode: h.country_code || null,
    }));
  }

  function adaptMe(meResp) {
    if (!meResp) return null;
    return {
      tenantId: meResp.tenant_id,
      displayName: meResp.display_name,
      roleLabel: meResp.role_label,
      workspace: meResp.workspace,
      timezone: meResp.timezone,
    };
  }

  function adaptDashStats(snapshot, skus) {
    // 后端不返回的财务汇总在前端基于 SKU 列表派生,缺失字段置 0/null
    const counts = snapshot.risk_counts || { p1: 0, p2: 0, p3: 0, safe: 0 };
    const totalRev7 = skus.reduce((sum, s) => sum + (s.revenue7 || 0), 0);
    const overstockCount = skus.filter(s => s.sellable > 90).length;
    const overstockQty = skus.filter(s => s.sellable > 90).reduce((sum, s) => sum + s.totalStock, 0);
    const stockout7Actual = skus.filter(s => s.stockoutRecent7).length;
    return {
      counts,
      stockout7: stockout7Actual,
      suggestSkuCount: snapshot.suggest_sku_count || 0,
      suggestTotalQty: snapshot.suggest_total_qty || 0,
      suggestTotalAmountBase: snapshot.suggest_total_amount?.base?.amount || 0,
      suggestTotalAmountByCurrency: snapshot.suggest_total_amount?.by_currency || [],
      totalStock: snapshot.total_stock ?? skus.reduce((sum, s) => sum + s.totalStock, 0),
      totalSales7: snapshot.total_sales_7d ?? 0,
      asOf: toDate(snapshot.as_of) || new Date(),
      calcRunId: snapshot.calc_run_id,

      // 财务 — 后端 Phase 1 未派生,前端置 0,UI 显示 "—"
      salesY: 0,
      salesTrend: [],
      salesTrendPct: null,
      gmvY: Math.round(totalRev7 / 7), // 用 7 天均值估今日
      costY: 0,
      expenseY: 0,
      profitY: 0,
      gmvTrend: [],
      costTrend: [],
      expenseTrend: [],
      profitTrend: [],

      overstockCount,
      overstockQty,

      // 后端 stockout_trend 未派生时,按实际近 7 天断货标记兜底。
      stockoutTrend: (snapshot.stockout_trend && snapshot.stockout_trend.length)
        ? snapshot.stockout_trend.map(p => p.count)
        : [0, 0, 0, 0, 0, 0, stockout7Actual],
      stockoutTrendTotal: stockout7Actual,

      healthScore: 0, // 后端待补
    };
  }

  function adaptTrends(trendsResp) {
    return {
      history: (trendsResp.history || []).map(p => ({
        date: toDate(p.date), qty: p.qty,
      })),
      forecast: (trendsResp.forecast || []).map(p => ({
        date: toDate(p.date), qty: p.qty, mult: p.sales_multiplier ?? p.mult ?? 1,
      })),
    };
  }

  // 把 /skus/trends 的历史 + 预测序列合并到 SKU ViewModel,
  // 让 SKUDetail / SKUTrendPanel 等已存在组件无需改动地拿到 histRaw / future14 / future30。
  function mergeTrendsIntoSku(sku, trendsResp, detailResp) {
    const history = (trendsResp.history || []).map(p => Math.round(p.qty || 0));
    const forecast = (trendsResp.forecast || []).map(p => Math.round(p.qty || 0));
    const forecastSeries = (trendsResp.forecast || []).map(p => ({
      date: p.date,
      qty: Math.round(p.qty || 0),
      mult: Number(p.sales_multiplier ?? p.mult ?? 1) || 1,
    }));
    const inventoryOverrides = {};
    (trendsResp.inventory_overrides || []).forEach(row => {
      const day = Number(row.day_offset);
      const qty = Number(row.stock_qty);
      if (Number.isFinite(day) && day > 0 && Number.isFinite(qty) && qty >= 0) {
        inventoryOverrides[day] = qty;
      }
    });
    const recent7 = history.slice(-7);
    const last7Daily = recent7.length
      ? +(recent7.reduce((a, b) => a + b, 0) / recent7.length).toFixed(1)
      : 0;
    const merged = {
      ...sku,
      histRaw: history,
      recent7,
      last7Daily,
      last7Denoised: +(last7Daily * 0.94).toFixed(1),
      future14: forecast.slice(0, 14),
      future30: forecast.slice(0, 30),
      forecastSeries,
      forecastDates: (trendsResp.forecast || []).map(p => p.date),
      inventoryOverrides,
    };
    if (detailResp) {
      // detailResp.summary 是 SKU 的最新快照,可补一些列表里没有的字段
      const s = detailResp.summary || {};
      if (s.brand) merged.brand = s.brand;
      if (s.category) merged.category = s.category;
      if (s.image_url) merged.image = s.image_url;
      if (s.owner) merged.owner = s.owner;
      merged.dataQuality = detailResp.data_quality || null;
      merged.inboundList = detailResp.inbound_list || [];
      // 预计到货 = 最早一笔 in_transit/receiving 状态的 expected_arrival_date
      const next = (merged.inboundList || []).find(x => x.expected_arrival_date);
      merged.estimatedArrivalAt = next ? new Date(next.expected_arrival_date) : null;
    }
    return merged;
  }

  window.adapter = {
    adaptSkuSummary,
    adaptDashStats,
    adaptTrends,
    adaptFinance,
    adaptStores,
    adaptFilters,
    adaptAlerts,
    adaptHolidays,
    adaptMe,
    mergeTrendsIntoSku,
    isRecentStockout7,
    toCountry,
    toDate,
  };
})();
