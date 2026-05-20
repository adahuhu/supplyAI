// Main app — wires routes, AI panel, modals, tweaks.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "dark",
  "density": "compact",
  "aiMode": "drawer"
}/*EDITMODE-END*/;

function initialRouteFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const page = params.get('page');
  if (page === 'sku') return { page: 'sku', skuId: params.get('skuId') || undefined };
  if (page === 'list') return { page: 'list', filter: params.get('filter') || 'all' };
  if (page === 'holiday') return { page: 'holiday', holidayId: params.get('holidayId') || undefined };
  if (page === 'notifications') return { page: 'notifications' };
  return { page: 'dashboard' };
}

const GLOBAL_AI_INTRO = '我会基于库存、销量、在途和规则给出补货决策。你可以直接问：今天哪些 SKU 必须补货？哪些订单需要先生成采购计划？';

const GLOBAL_AI_SCENARIOS = {
  riskQueue: [
    { role: 'user', text: '本周哪些 SKU 必须补货?按紧急度排序并说明原因。' },
    { role: 'ai', text: '正在读取后端风险队列。', card: { type: 'backend_decision', scenario: 'risk_queue' } },
  ],
  holidayReadiness: [
    { role: 'user', text: '下一个大促要为哪些 SKU 备货?缺口和建议采购量是多少?' },
    { role: 'ai', text: '正在读取后端节日和 SKU 快照。', card: { type: 'backend_decision', scenario: 'holiday_readiness' } },
  ],
  planComparison: [
    { role: 'user', text: '只海运 vs 海+空混合,成本和断货风险分别是什么?' },
    { role: 'ai', text: '正在读取后端 SKU 快照和物流方式配置。', card: { type: 'backend_decision', scenario: 'plan_comparison' } },
  ],
  ruleImpact: [
    { role: 'user', text: '安全天数改成 21 天会怎样?采购量和风险等级有什么变化?' },
    { role: 'ai', text: '正在通过后端计算安全天数影响。', card: { type: 'backend_decision', scenario: 'rule_impact', context: { target_safety_days: 21 } } },
  ],
  ms40060: [
    { role: 'user', text: '挑一个高风险 SKU,告诉我还能卖多久,要不要补、补多少?' },
    { role: 'ai', text: '正在读取后端 SKU 备货建议。', card: { type: 'backend_decision', scenario: 'single_sku_replenishment', context: { listing_id: 1000003 } } },
  ],
};

function initialGlobalAiHistoryFromUrl() {
  const base = [{ role: 'ai', text: GLOBAL_AI_INTRO }];
  const scenario = new URLSearchParams(window.location.search).get('aiScenario');
  const page = new URLSearchParams(window.location.search).get('page');
  return page !== 'sku' && scenario && GLOBAL_AI_SCENARIOS[scenario]
    ? [...base, ...GLOBAL_AI_SCENARIOS[scenario]]
    : base;
}

function initialSkuAiHistoryFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const scenario = params.get('aiScenario');
  const skuId = params.get('skuId');
  if (params.get('page') === 'sku' && skuId && scenario && GLOBAL_AI_SCENARIOS[scenario]) {
    return { [skuId]: GLOBAL_AI_SCENARIOS[scenario] };
  }
  return {};
}

function initialAiOpenFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.has('aiScenario') || params.get('ai') === '1' || params.get('ai') === 'open';
}

function initialDingTalkAiDetailFromUrl() {
  return new URLSearchParams(window.location.search).get('ai') === '1';
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState(initialRouteFromUrl);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(() => window.innerWidth < 760);
  const [aiOpen, setAiOpen] = React.useState(initialAiOpenFromUrl);
  const dingTalkAiDetail = initialDingTalkAiDetailFromUrl();
  const [aiWide, setAiWide] = React.useState(false);
  const [rulesCtx, setRulesCtx] = React.useState(null);
  const [poIds, setPoIds] = React.useState(null);
  const [toast, setToast] = React.useState('');
  const [refreshing, setRefreshing] = React.useState(false);
  const [asOf, setAsOf] = React.useState(() => DASH_STATS.asOf || new Date());
  // 后端连接状态: 'connecting' → 'online' / 'error'(无降级 mock,失败即拒绝渲染)
  const [conn, setConn] = React.useState('connecting');
  const [connError, setConnError] = React.useState('');
  const [, bumpVersion] = React.useReducer((x) => x + 1, 0);
  // Dashboard 顶部过滤器:store=mall_id 字符串、country=country code、owner=owner 名
  const [dashFilters, setDashFilters] = React.useState({ store: null, country: null, owner: null });
  // AI 对话历史 — 提升到 App 层,抽屉关闭后再打开仍可见
  const [globalAiHistory, setGlobalAiHistory] = React.useState(initialGlobalAiHistoryFromUrl);
  const [skuAiHistoryMap, setSkuAiHistoryMap] = React.useState(initialSkuAiHistoryFromUrl); // listingId -> messages[]

  // 把 dashFilters 翻译成各端点参数
  const buildFilterArgs = React.useCallback((f) => {
    const args = {};
    if (f.store) args.mall_ids = [parseInt(f.store, 10)];
    if (f.country) args.country_codes = [f.country];
    if (f.owner) args.owners = [f.owner];
    return args;
  }, []);

  // ===== Backend bootstrap: 拉所有 dashboard 数据 =====
  const refreshFromBackend = React.useCallback(async (filtersOverride) => {
    if (!window.api) return;
    setConn('connecting');
    setConnError('');
    const f = filtersOverride || dashFilters;
    const filterArgs = buildFilterArgs(f);
    try {
      const [
        snapshot, listResp, financeResp, storesResp, filtersResp, alertsResp,
        holidaysResp, meResp,
      ] = await Promise.all([
        window.api.dashboardSnapshot(filterArgs),
        window.api.skusList({ page: 1, page_size: 200, ...filterArgs }),
        window.api.dashboardFinance(filterArgs).catch(() => null),
        window.api.dashboardStores().catch(() => null),
        window.api.dashboardFilters().catch(() => null),
        window.api.dashboardAlerts().catch(() => null),
        window.api.dashboardHolidays().catch(() => null),
        window.api.authMe().catch(() => null),
      ]);
      const skus = (listResp.rows || []).map(window.adapter.adaptSkuSummary);
      const stats = window.adapter.adaptDashStats(snapshot, skus);
      // 把 finance 的真实数字覆盖回 stats 的财务字段
      const finance = window.adapter.adaptFinance(financeResp);
      if (finance) {
        stats.salesY = finance.sales.value;
        stats.gmvY = finance.gmv.value;
        stats.costY = finance.cost.value;
        stats.expenseY = finance.expense.value;
        stats.profitY = finance.profit.value;
        stats.salesTrendPct = finance.sales.pctChange;
        stats.gmvTrendPct = finance.gmv.pctChange;
        stats.costTrendPct = finance.cost.pctChange;
        stats.expenseTrendPct = finance.expense.pctChange;
        stats.profitTrendPct = finance.profit.pctChange;
        stats.financeAsOf = finance.asOfDate;
      }

      window.SKUS.length = 0;
      window.SKUS.push(...skus);
      Object.keys(window.DASH_STATS).forEach((k) => delete window.DASH_STATS[k]);
      Object.assign(window.DASH_STATS, stats);
      window.STORES_DATA = window.adapter.adaptStores(storesResp);
      window.FILTERS_DATA = window.adapter.adaptFilters(filtersResp);
      window.TODAY_ACTIONS.length = 0;
      window.TODAY_ACTIONS.push(...window.adapter.adaptAlerts(alertsResp));
      window.HOLIDAYS_DATA = window.adapter.adaptHolidays(holidaysResp);
      window.ME_DATA = window.adapter.adaptMe(meResp);

      setConn('online');
      setAsOf(stats.asOf || new Date());
      bumpVersion();
    } catch (err) {
      console.error('[bootstrap] backend error:', err);
      setConnError(err.message || String(err));
      setConn('error');
    }
  }, [dashFilters, buildFilterArgs]);

  React.useEffect(() => {
    refreshFromBackend();
  }, [refreshFromBackend]);

  React.useEffect(() => {
    window.refreshSupplyAI = refreshFromBackend;
    return () => {
      if (window.refreshSupplyAI === refreshFromBackend) delete window.refreshSupplyAI;
    };
  }, [refreshFromBackend]);

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', t.theme);
    document.documentElement.setAttribute('data-density', t.density);
  }, [t.theme, t.density]);

  React.useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 760) setSidebarCollapsed(true);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'j') {
        e.preventDefault();
        setAiOpen(v => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const showToast = (m) => {
    setToast(m);
    setTimeout(() => setToast(''), 2400);
  };

  const openRules = (ctx) => setRulesCtx(ctx || {});
  const openCreatePO = (payload) => {
    const items = (payload || []).map((it) => (
      typeof it === 'object' && it !== null ? it : { id: it }
    ));
    setRoute({ page: 'drafts', ids: items.map(it => it.id), items });
  };

  // Determine which AI to show
  const aiContent = (() => {
    if (!aiOpen) return null;
    if (route.page === 'sku') {
      const sku = SKUS.find(s => s.id === route.skuId) || SKUS[0];
      if (!sku) {
        return (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-3)', fontSize: 12 }}>
            正在加载 SKU 数据…
          </div>
        );
      }
      const key = sku && (sku.listingId || sku.id);
      const history = (key && skuAiHistoryMap[key]) || [];
      const setHistory = (updater) => {
        setSkuAiHistoryMap(prev => {
          const cur = prev[key] || [];
          const next = typeof updater === 'function' ? updater(cur) : updater;
          return { ...prev, [key]: next };
        });
      };
      return <SKUAIPanel sku={sku} onClose={() => setAiOpen(false)} mode={t.aiMode} history={history} setHistory={setHistory} wide={aiWide} onToggleWide={() => setAiWide(v => !v)} openCreatePO={openCreatePO} openRules={openRules} refreshData={refreshFromBackend} showToast={showToast}/>;
    }
    return <GlobalAIPanel onClose={() => setAiOpen(false)} setRoute={(r) => { setRoute(r); }} openCreatePO={openCreatePO} openRules={openRules} dashFilters={dashFilters} history={globalAiHistory} setHistory={setGlobalAiHistory} wide={aiWide} onToggleWide={() => setAiWide(v => !v)} refreshData={refreshFromBackend} showToast={showToast}/>;
  })();

  const aiInDrawer = aiOpen && (t.aiMode === 'drawer' || route.page !== 'sku');
  const aiInSplit = aiOpen && t.aiMode === 'split' && route.page === 'sku';

  if (dingTalkAiDetail) {
    return (
      <div
        data-screen-label="DingTalkAIDetail"
        style={{
          width: '100vw',
          height: '100vh',
          minWidth: 0,
          minHeight: 0,
          overflow: 'hidden',
          background: 'var(--bg)',
          color: 'var(--text)',
        }}
      >
        <div style={{ width: '100%', height: '100%', minWidth: 0, minHeight: 0, overflow: 'hidden' }}>
          <ErrorBoundary>{aiContent}</ErrorBoundary>
        </div>
        <ErrorBoundary>
          <RulesModal open={!!rulesCtx} onClose={() => setRulesCtx(null)} ctx={rulesCtx} showToast={showToast} refreshData={refreshFromBackend}/>
        </ErrorBoundary>
        <ErrorBoundary>
          <CreatePOModal open={!!poIds} onClose={() => setPoIds(null)} ids={poIds || []} showToast={showToast} setRoute={setRoute}/>
        </ErrorBoundary>
        <Toast msg={toast} kind="success"/>
      </div>
    );
  }

  return (
    <div data-screen-label="App" style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg)' }}>
      <Sidebar route={route} setRoute={setRoute} collapsed={sidebarCollapsed}/>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Topbar
          onAI={() => setAiOpen(v => !v)}
          onRefresh={async () => {
            if (refreshing) return;
            setRefreshing(true);
            showToast('正在重新计算…');
            await refreshFromBackend();
            const now = new Date();
            setAsOf(now);
            setRefreshing(false);
            showToast('已刷新 · ' + fmt.time(now));
          }}
          refreshing={refreshing}
          onToggleSidebar={() => setSidebarCollapsed(v => !v)}
          asOf={asOf}
          conn={conn}
          onSearch={(kw) => setRoute({ page: 'list', keyword: kw })}
        />

        {/* Main + optional split AI */}
        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          <div style={{ flex: 1, overflow: 'auto', minWidth: 0 }} data-screen-label={route.page} key={conn /* 数据源切换时强制 remount,刷新 useMemo */}>
            {conn === 'connecting' && (
              <div style={{ padding: 80, textAlign: 'center', color: 'var(--text-3)' }}>
                <Icon name="refresh" size={20}/>
                <div style={{ marginTop: 12, fontSize: 13 }}>正在连接后端…</div>
              </div>
            )}
            {conn === 'error' && (
              <div style={{ maxWidth: 560, margin: '80px auto', padding: 32, border: '1px solid var(--border)', borderRadius: 12, background: 'var(--surface)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <span className="dot p1"/>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>无法连接后端</div>
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--text-3)', lineHeight: 1.6, marginBottom: 16 }}>
                  数据完全依赖后端,无 mock 兜底。请确认 <span className="mono">uvicorn</span> 已起在
                  <span className="mono"> 127.0.0.1:8000</span>,且 AI 已配置
                  <span className="mono"> SUPPLY_DASH_API_KEY</span>。
                </div>
                {connError && (
                  <pre style={{ fontSize: 11, padding: 10, background: 'var(--bg-sunken)', borderRadius: 6, overflow: 'auto' }}>{connError}</pre>
                )}
                <button className="btn primary" onClick={refreshFromBackend} style={{ marginTop: 12 }}>
                  <Icon name="refresh" size={13}/>重试
                </button>
              </div>
            )}
            {conn === 'online' && (
              <ErrorBoundary>
                {route.page === 'dashboard' && <Dashboard setRoute={setRoute} openAI={() => setAiOpen(true)} openCreatePO={openCreatePO} dashFilters={dashFilters} setDashFilters={setDashFilters}/>}
                {route.page === 'list' && <ListPage initialFilter={route.filter || 'all'} initialKeyword={route.keyword || ''} initialMallId={route.mallId || null} setRoute={setRoute} openRules={openRules} openCreatePO={openCreatePO}/>}
                {route.page === 'holiday' && <HolidaySkuPage holidayId={route.holidayId} setRoute={setRoute} openCreatePO={openCreatePO}/>}
                {route.page === 'sku' && <SKUDetail
                  skuId={route.skuId || (SKUS[0] && SKUS[0].id)}
                  setRoute={setRoute}
                  openRules={openRules}
                  openCreatePO={openCreatePO}
                  openAI={(v) => setAiOpen(v == null ? !aiOpen : v)}
                  aiOpen={aiInSplit}
                  aiMode={t.aiMode}
                />}
                {route.page === 'drafts' && <DraftsPage setRoute={setRoute} showToast={showToast} initialIds={route.ids || []} initialItems={route.items || []}/>}
                {route.page === 'notifications' && <NotificationPage setRoute={setRoute} showToast={showToast}/>}
              </ErrorBoundary>
            )}
          </div>
        </div>
      </div>

      {/* Drawer AI (overlay form) — 默认 720,宽屏模式扩到 980 让回答区有足够阅读空间 */}
      {aiInDrawer && (
        <Drawer open onClose={() => setAiOpen(false)} width={aiWide ? 980 : 720}>
          <ErrorBoundary>{aiContent}</ErrorBoundary>
        </Drawer>
      )}

      {/* Modals */}
      <ErrorBoundary>
        <RulesModal open={!!rulesCtx} onClose={() => setRulesCtx(null)} ctx={rulesCtx} showToast={showToast} refreshData={refreshFromBackend}/>
      </ErrorBoundary>
      <ErrorBoundary>
        <CreatePOModal open={!!poIds} onClose={() => setPoIds(null)} ids={poIds || []} showToast={showToast} setRoute={setRoute}/>
      </ErrorBoundary>

      <Toast msg={toast} kind="success"/>

      {/* 浮动 AI 入口 — 抽屉打开时隐藏避免遮挡;连接中/失败时也隐藏 */}
      {conn === 'online' && (
        <AIFab onOpen={() => setAiOpen(true)} hidden={aiOpen}/>
      )}

      {/* Tweaks */}
      <TweaksPanel title="Tweaks">
        <TweakSection label="主题"/>
        <TweakRadio label="模式" value={t.theme} options={['light', 'dark']}
          onChange={(v) => setTweak('theme', v)}/>
        <TweakSection label="密度"/>
        <TweakRadio label="表格密度" value={t.density} options={['compact', 'regular', 'comfy']}
          onChange={(v) => setTweak('density', v)}/>
        <TweakSection label="AI 面板"/>
        <TweakRadio label="形态" value={t.aiMode} options={['drawer', 'split']}
          onChange={(v) => setTweak('aiMode', v)}/>
        <TweakSection label="快捷"/>
        <TweakButton label="跳到 SKU 详情演示" onClick={() => setRoute({ page: 'sku', skuId: SKUS[0].id })}/>
        <TweakButton label="打开规则设置弹窗" secondary onClick={() => setRulesCtx({ sku: SKUS[0] })}/>
        <TweakButton label="打开采购计划页面" secondary onClick={() => openCreatePO([SKUS[0].id, SKUS[1].id, SKUS[2].id])}/>
        <TweakButton label="打开钉钉推送页面" secondary onClick={() => setRoute({ page: 'notifications' })}/>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
