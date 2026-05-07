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
  if (page === 'arch') return { page: 'arch' };
  return { page: 'dashboard' };
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState(initialRouteFromUrl);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(() => window.innerWidth < 760);
  const [aiOpen, setAiOpen] = React.useState(false);
  const [rulesCtx, setRulesCtx] = React.useState(null);
  const [poIds, setPoIds] = React.useState(null);
  const [toast, setToast] = React.useState('');

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
  const openCreatePO = (ids) => setPoIds(ids || []);

  // Determine which AI to show
  const aiContent = (() => {
    if (!aiOpen) return null;
    if (route.page === 'sku') {
      const sku = SKUS.find(s => s.id === route.skuId) || SKUS[0];
      return <SKUAIPanel sku={sku} onClose={() => setAiOpen(false)} mode={t.aiMode}/>;
    }
    return <GlobalAIPanel onClose={() => setAiOpen(false)} setRoute={(r) => { setRoute(r); }}/>;
  })();

  const aiInDrawer = aiOpen && (t.aiMode === 'drawer' || route.page !== 'sku');
  const aiInSplit = aiOpen && t.aiMode === 'split' && route.page === 'sku';

  return (
    <div data-screen-label="App" style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg)' }}>
      <Sidebar route={route} setRoute={setRoute} collapsed={sidebarCollapsed}/>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Topbar
          onAI={() => setAiOpen(v => !v)}
          onRefresh={() => showToast('已重新计算 · ' + fmt.time(new Date()))}
          onToggleSidebar={() => setSidebarCollapsed(v => !v)}
          asOf={DASH_STATS.asOf}
        />

        {/* Main + optional split AI */}
        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          <div style={{ flex: 1, overflow: 'auto', minWidth: 0 }} data-screen-label={route.page}>
            {route.page === 'dashboard' && <Dashboard setRoute={setRoute} openAI={() => setAiOpen(true)} openCreatePO={openCreatePO}/>}
            {route.page === 'list' && <ListPage initialFilter={route.filter || 'all'} setRoute={setRoute} openRules={openRules} openCreatePO={openCreatePO}/>}
            {route.page === 'sku' && <SKUDetail
              skuId={route.skuId || SKUS[0].id}
              setRoute={setRoute}
              openRules={openRules}
              openCreatePO={openCreatePO}
              openAI={(v) => setAiOpen(v == null ? !aiOpen : v)}
              aiOpen={aiInSplit}
              aiMode={t.aiMode}
            />}
            {route.page === 'arch' && <ArchPage setRoute={setRoute}/>}
          </div>
        </div>
      </div>

      {/* Drawer AI (overlay form) */}
      {aiInDrawer && (
        <Drawer open onClose={() => setAiOpen(false)} width={460}>
          {aiContent}
        </Drawer>
      )}

      {/* Modals */}
      <RulesModal open={!!rulesCtx} onClose={() => setRulesCtx(null)} ctx={rulesCtx} showToast={showToast}/>
      <CreatePOModal open={!!poIds} onClose={() => setPoIds(null)} ids={poIds || []} showToast={showToast}/>

      <Toast msg={toast} kind="success"/>

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
        <TweakButton label="打开采购计划弹窗" secondary onClick={() => setPoIds([SKUS[0].id, SKUS[1].id, SKUS[2].id])}/>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
