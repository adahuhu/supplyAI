// App shell: sidebar + topbar + route container.

function Sidebar({ route, setRoute, collapsed }) {
  const items = [
    { id: 'dashboard', label: '工作台', icon: 'home' },
    { id: 'list', label: '备货计划', icon: 'list' },
    { id: 'sku', label: 'SKU 分析', icon: 'box' },
    { id: 'drafts', label: '采购草稿', icon: 'package' },
  ];
  return (
    <aside style={{
      width: collapsed ? 56 : 220,
      borderRight: '1px solid var(--border)',
      background: 'linear-gradient(180deg, var(--surface-2), var(--bg-sunken))',
      display: 'flex', flexDirection: 'column',
      flex: 'none',
      transition: 'width .18s',
    }}>
      <div style={{ height: 52, display: 'flex', alignItems: 'center', gap: 10, padding: '0 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{
          width: 22, height: 22, borderRadius: 5,
          background: 'var(--accent)',
          boxShadow: '0 0 0 1px rgba(255,255,255,.16), 0 10px 24px -16px var(--accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 11, fontWeight: 700,
        }}>S</div>
        {!collapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
            <div style={{ fontWeight: 600, fontSize: 13 }}>SupplyAI</div>
            <div style={{ fontSize: 10.5, color: 'var(--text-3)' }}>供应链分析工作台</div>
          </div>
        )}
      </div>

      <div style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 2, flex: 1 }}>
        {!collapsed && <div className="label" style={{ padding: '6px 8px 4px' }}>工作区</div>}
        {items.map(it => {
          const active = route.page === it.id;
          return (
            <button key={it.id} onClick={() => setRoute({ page: it.id })}
              style={{
                appearance: 'none',
                border: '1px solid ' + (active ? 'var(--border-strong)' : 'transparent'),
                background: active ? 'var(--accent-soft)' : 'transparent',
                color: active ? 'var(--accent-text)' : 'var(--text-2)',
                padding: '7px 10px', borderRadius: 6, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left',
                fontSize: 12.5, fontWeight: active ? 500 : 400,
                fontFamily: 'inherit',
                boxShadow: active ? 'inset 2px 0 0 var(--accent)' : 'none',
                transition: 'background .14s ease, border-color .14s ease, color .14s ease',
              }}>
              <Icon name={it.icon} size={15}/>
              {!collapsed && <span style={{ flex: 1 }}>{it.label}</span>}
              {!collapsed && it.sub && <span style={{ fontSize: 10.5, color: 'var(--text-4)' }}>{it.sub}</span>}
            </button>
          );
        })}

        {!collapsed && (
          <>
            <div className="label" style={{ padding: '14px 8px 4px' }}>店铺空间</div>
            {(window.STORES_DATA || []).slice(0, 6).map(s => (
              <button
                key={s.mallId}
                onClick={() => setRoute({ page: 'list', filter: 'all', mallId: s.mallId, mallName: s.name })}
                title={`查看 ${s.name} 的备货列表`}
                style={{
                  appearance: 'none', border: 0, background: 'transparent',
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 10px', fontSize: 12, color: 'var(--text-2)',
                  cursor: 'pointer', borderRadius: 6, fontFamily: 'inherit', textAlign: 'left',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--surface-hover)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                <Icon name="store" size={13}/>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</span>
                {s.risk > 0 && <span className="chip p1" style={{ height: 16, padding: '0 5px', fontSize: 10 }}>{s.risk}</span>}
              </button>
            ))}
            {(!window.STORES_DATA || window.STORES_DATA.length === 0) && (
              <div style={{ padding: '6px 10px', fontSize: 11, color: 'var(--text-4)' }}>—</div>
            )}
          </>
        )}
      </div>

      {!collapsed && (
        <div style={{ padding: 12, borderTop: '1px solid var(--border)', background: 'rgba(255,255,255,0.015)' }}>
          {(() => {
            const me = window.ME_DATA || { displayName: '—', roleLabel: '', workspace: '—', timezone: '' };
            const initial = (me.displayName || '·').slice(0, 1);
            return (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 28, height: 28, borderRadius: 7, background: 'var(--surface-3)', color: 'var(--text)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600 }}>{initial}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {me.displayName}{me.roleLabel ? ` · ${me.roleLabel}` : ''}
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{me.workspace} / {me.timezone}</div>
                </div>
                <Icon name="settings" size={14} color="var(--text-3)"/>
              </div>
            );
          })()}
        </div>
      )}
    </aside>
  );
}

function Topbar({ onAI, onRefresh, onToggleSidebar, asOf, conn = 'connecting', onSearch }) {
  const connMeta = {
    connecting: { color: 'var(--text-3)', label: '连接中…' },
    online:     { color: 'var(--success)', label: '后端已连接' },
    error:      { color: 'var(--p1)', label: '连接失败 · 点击重试' },
  }[conn] || { color: 'var(--text-3)', label: conn };
  const [q, setQ] = React.useState('');
  const inputRef = React.useRef(null);

  // ⌘K / Ctrl+K 全局聚焦搜索框
  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  const [narrow, setNarrow] = React.useState(() => window.innerWidth < 760);
  React.useEffect(() => {
    const onResize = () => setNarrow(window.innerWidth < 760);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <div style={{
      height: 52, flex: 'none',
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '0 16px',
      borderBottom: '1px solid var(--border)',
      background: 'color-mix(in srgb, var(--surface) 86%, transparent)',
      backdropFilter: 'blur(14px)',
      WebkitBackdropFilter: 'blur(14px)',
    }}>
      <button className="btn ghost icon sm" onClick={onToggleSidebar}><Icon name="menu" size={15}/></button>

      {!narrow && <div style={{
        position: 'relative', flex: 1, maxWidth: 360,
      }}>
        <Icon name="search" size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }}/>
        <input
          ref={inputRef}
          className="txt"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && q.trim()) { onSearch?.(q.trim()); setQ(''); }
            if (e.key === 'Escape') setQ('');
          }}
          placeholder="搜索 SKU、MSKU、ASIN、品名…(Enter 跳列表)"
          style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 12.5 }}/>
        <span className="kbd" style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)' }}>⌘K</span>
      </div>}

      <div style={{ flex: 1 }}/>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-3)' }} title={connMeta.label}>
        <span className="dot" style={{ background: connMeta.color }}/>
        {!narrow && <>{connMeta.label} · {fmt.dateLong(asOf)} {fmt.time(asOf)}</>}
        <button className="btn ghost icon sm" onClick={onRefresh} title="重新计算"><Icon name="refresh" size={13}/></button>
      </div>

      <button className={narrow ? 'btn icon sm' : 'btn'} onClick={onAI} style={{ gap: 6 }} title="AI 分析">
        <Icon name="bot" size={14}/>
        {!narrow && <span>AI 分析</span>}
        {!narrow && <span className="kbd">⌘J</span>}
      </button>
    </div>
  );
}

Object.assign(window, { Sidebar, Topbar });
