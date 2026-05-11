// api.jsx — 后端 API fetch 封装。所有端点均为 POST。
// 后端默认地址: http://127.0.0.1:8000;通过 ?api=... query 参数或 window.SUPPLYAI_API_BASE 覆盖。

(function () {
  function resolveBase() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get('api');
    if (fromQuery) return fromQuery.replace(/\/$/, '');
    if (window.SUPPLYAI_API_BASE) return window.SUPPLYAI_API_BASE.replace(/\/$/, '');
    return 'http://127.0.0.1:8000/api/supplyai';
  }

  const TENANT_ID = 100228;
  const BASE = resolveBase();

  async function postJson(path, body) {
    const url = BASE + path;
    const t0 = performance.now();
    let resp;
    try {
      resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
      });
    } catch (err) {
      throw new ApiError('network', `网络错误: ${err.message}`, { url });
    }
    const elapsed = (performance.now() - t0).toFixed(0);
    let payload = null;
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try { payload = await resp.json(); } catch (_) { /* ignore */ }
    }
    if (!resp.ok) {
      const detail = payload && payload.detail;
      const code = (detail && detail.code) || `HTTP_${resp.status}`;
      const message = (detail && detail.message) || `请求失败 ${resp.status}`;
      throw new ApiError(code, message, { url, status: resp.status, elapsed });
    }
    if (window.SUPPLYAI_DEBUG) {
      console.log(`[api] ${path} ${elapsed}ms`, body, payload);
    }
    return payload;
  }

  class ApiError extends Error {
    constructor(code, message, meta) {
      super(message);
      this.name = 'ApiError';
      this.code = code;
      this.meta = meta || {};
    }
  }

  const api = {
    base: BASE,
    tenantId: TENANT_ID,
    ApiError,

    health() {
      return fetch(BASE + '/_health').then(r => r.json());
    },
    dashboardSnapshot(opts = {}) {
      return postJson('/dashboard/snapshot', { tenant_id: TENANT_ID, ...opts });
    },
    riskQueue(opts = {}) {
      return postJson('/dashboard/risk-queue', { tenant_id: TENANT_ID, limit: 10, ...opts });
    },
    dashboardFilters(opts = {}) {
      return postJson('/dashboard/filters', { tenant_id: TENANT_ID, ...opts });
    },
    dashboardStores(opts = {}) {
      return postJson('/dashboard/stores', { tenant_id: TENANT_ID, ...opts });
    },
    dashboardFinance(opts = {}) {
      return postJson('/dashboard/finance', { tenant_id: TENANT_ID, ...opts });
    },
    dashboardAlerts(opts = {}) {
      return postJson('/dashboard/data-quality-alerts', { tenant_id: TENANT_ID, ...opts });
    },
    dashboardHolidays(opts = {}) {
      return postJson('/dashboard/holidays', { tenant_id: TENANT_ID, ...opts });
    },
    holidayUpsert(body) {
      return postJson('/dashboard/holidays/upsert', { tenant_id: TENANT_ID, ...body });
    },
    authMe() {
      return postJson('/auth/me', {});
    },
    skusList(opts = {}) {
      return postJson('/skus/list', {
        tenant_id: TENANT_ID,
        page: 1,
        page_size: 100,
        ...opts,
      });
    },
    skuDetail(listingId, opts = {}) {
      return postJson('/skus/detail', {
        tenant_id: TENANT_ID,
        listing_id: listingId,
        ...opts,
      });
    },
    skuTrends(listingId, opts = {}) {
      return postJson('/skus/trends', {
        tenant_id: TENANT_ID,
        listing_id: listingId,
        history_days: 30,
        ...opts,
      });
    },
    calcLatest() {
      return postJson('/calc/latest', { tenant_id: TENANT_ID });
    },
    calcRun(opts = {}) {
      return postJson('/calc/run', { tenant_id: TENANT_ID, run_type: 'manual', ...opts });
    },
    rulesList(opts = {}) {
      return postJson('/rules/list', { tenant_id: TENANT_ID, ...opts });
    },
    rulesUpsert(body) {
      return postJson('/rules/upsert', { tenant_id: TENANT_ID, ...body });
    },
    rulesDisable(ruleId) {
      return postJson('/rules/disable', { tenant_id: TENANT_ID, rule_id: ruleId });
    },
    forecastRulesList(opts = {}) {
      return postJson('/rules/forecast/list', { tenant_id: TENANT_ID, ...opts });
    },
    forecastRulesUpsert(body) {
      return postJson('/rules/forecast/upsert', { tenant_id: TENANT_ID, ...body });
    },
    aiExplain(listingId) {
      return postJson('/ai/explain', { tenant_id: TENANT_ID, listing_id: listingId });
    },
    aiChat(messages, context = null) {
      const body = { tenant_id: TENANT_ID, messages };
      if (context) body.context = context;
      return postJson('/ai/chat', body);
    },
    purchaseDraftCreate(items, opts = {}) {
      return postJson('/purchase/draft/create', {
        tenant_id: TENANT_ID,
        items,
        ...opts,
      });
    },
    purchaseDraftList(opts = {}) {
      return postJson('/purchase/draft/list', { tenant_id: TENANT_ID, ...opts });
    },
    exportSkuList(opts = {}) {
      return postJson('/exports/sku-list', { tenant_id: TENANT_ID, ...opts });
    },
  };

  window.api = api;
})();
