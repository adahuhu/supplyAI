// 采购草稿页 — 列表 + 状态机操作(confirm / redirect)
// 数据源: POST /purchase/draft/list, /confirm, /redirect

function DraftsPage({ setRoute, showToast, highlightDraftId }) {
  const [rows, setRows] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [statusFilter, setStatusFilter] = React.useState('all');
  const [actingId, setActingId] = React.useState(null);
  const highlightRef = React.useRef(null);

  React.useEffect(() => {
    if (highlightDraftId && highlightRef.current) {
      highlightRef.current.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }, [highlightDraftId, rows]);

  const reload = React.useCallback(async () => {
    if (!window.api) return;
    setLoading(true);
    try {
      const statuses = statusFilter === 'all' ? null : [statusFilter];
      const resp = await window.api.purchaseDraftList({
        statuses, page: 1, page_size: 200,
      });
      setRows(resp.rows || []);
    } catch (err) {
      showToast && showToast('加载失败:' + err.message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, showToast]);

  React.useEffect(() => { reload(); }, [reload]);

  const transition = async (draftId, target) => {
    if (!window.api) return;
    setActingId(draftId);
    try {
      const url = target === 'confirmed' ? '/purchase/draft/confirm' : '/purchase/draft/redirect';
      await fetch(window.api.base + url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: window.api.tenantId, draft_id: draftId }),
      }).then(r => r.ok ? r.json() : r.json().then(b => Promise.reject(new Error(b.detail?.message || r.statusText))));
      showToast && showToast(target === 'confirmed' ? '已确认' : '已转人工');
      await reload();
    } catch (err) {
      showToast && showToast('操作失败:' + err.message);
    } finally {
      setActingId(null);
    }
  };

  const totalQty = rows.reduce((s, r) => s + (r.suggest_qty || 0), 0);

  const STATUS_LABELS = {
    draft: { label: '草稿', cls: 'p3' },
    confirmed: { label: '已确认', cls: 'p2' },
    redirected: { label: '已转人工', cls: 'safe' },
  };

  return (
    <div style={{ padding: '24px 32px 48px', maxWidth: 1480, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div className="h1"><span className="marker"/>采购草稿</div>
          <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 4 }}>
            从备货建议生成的采购草稿,支持二次确认 / 转人工
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="btn ghost sm" onClick={reload} disabled={loading}>
            <Icon name="refresh" size={13}/>{loading ? '加载中…' : '刷新'}
          </button>
        </div>
      </div>

      {/* Status tabs */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 4,
        borderBottom: '1px solid var(--border)',
      }}>
        {[
          { v: 'all', label: '全部', count: rows.length },
          { v: 'draft', label: '草稿', count: rows.filter(r => r.status === 'draft').length, cls: 'p3' },
          { v: 'confirmed', label: '已确认', count: rows.filter(r => r.status === 'confirmed').length, cls: 'p2' },
          { v: 'redirected', label: '已转人工', count: rows.filter(r => r.status === 'redirected').length, cls: 'safe' },
        ].map(s => {
          const active = statusFilter === s.v;
          return (
            <button key={s.v} onClick={() => setStatusFilter(s.v)} style={{
              appearance: 'none', border: 0, background: 'transparent',
              padding: '10px 12px', fontSize: 12.5,
              color: active ? 'var(--text)' : 'var(--text-3)',
              fontWeight: active ? 600 : 400,
              borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
              fontFamily: 'inherit',
            }}>
              {s.cls && <span className={'dot ' + s.cls}/>}
              {s.label}
              <span className="tabular" style={{
                fontSize: 11, color: 'var(--text-4)', fontWeight: 500,
                background: active ? 'var(--accent-soft)' : 'var(--surface-hover)',
                padding: '1px 6px', borderRadius: 999,
              }}>{s.count}</span>
            </button>
          );
        })}
        <div style={{ flex: 1 }}/>
        <span style={{ fontSize: 11.5, color: 'var(--text-3)', padding: '0 12px' }}>
          共 <span className="tabular">{rows.length}</span> 条 · 合计 <span className="tabular">{totalQty.toLocaleString()}</span> 件
        </span>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflow: 'auto', maxHeight: 'calc(100vh - 280px)' }}>
          <table className="t" style={{ fontSize: 12.5 }}>
            <thead>
              <tr>
                <th style={{ width: 140 }}>Draft ID</th>
                <th>MSKU</th>
                <th>SKU</th>
                <th>店铺</th>
                <th className="num" style={{ width: 100 }}>建议数量</th>
                <th>供应商</th>
                <th>状态</th>
                <th>计算批次</th>
                <th>创建时间</th>
                <th style={{ width: 180 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && !loading && (
                <tr>
                  <td colSpan={10} style={{ padding: 40, textAlign: 'center', color: 'var(--text-3)' }}>
                    暂无草稿。可在 SKU 列表选中行后点击「生成采购计划」批量创建。
                  </td>
                </tr>
              )}
              {rows.map(r => {
                const meta = STATUS_LABELS[r.status] || { label: r.status, cls: '' };
                const acting = actingId === r.draft_id;
                const isHighlighted = highlightDraftId && r.draft_id === highlightDraftId;
                return (
                  <tr key={r.draft_id}
                    ref={isHighlighted ? highlightRef : null}
                    style={isHighlighted ? {
                      background: 'var(--accent-soft)',
                      boxShadow: 'inset 3px 0 0 var(--accent)',
                    } : undefined}>
                    <td className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.draft_id}</td>
                    <td className="mono" style={{ fontWeight: 500 }}>{r.msku || '—'}</td>
                    <td className="mono" style={{ color: 'var(--text-3)' }}>{r.sku || '—'}</td>
                    <td>{r.mall_id ? `mall ${r.mall_id}` : '—'}</td>
                    <td className="num tabular" style={{ fontWeight: 500 }}>{(r.suggest_qty || 0).toLocaleString()}</td>
                    <td>{r.supplier_name || <span style={{ color: 'var(--text-4)' }}>—</span>}</td>
                    <td>
                      <span className={'chip ' + (meta.cls || '')} style={{ fontSize: 11 }}>
                        {meta.cls && <span className={'dot ' + meta.cls}/>}{meta.label}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.calc_run_id || '—'}</td>
                    <td style={{ color: 'var(--text-3)', fontSize: 11.5 }}>
                      {r.created_at ? new Date(r.created_at).toLocaleString('zh-CN') : '—'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        {r.status === 'draft' && (
                          <button className="btn sm primary" disabled={acting}
                            onClick={() => transition(r.draft_id, 'confirmed')}>
                            <Icon name="check" size={11}/>确认
                          </button>
                        )}
                        {(r.status === 'draft' || r.status === 'confirmed') && (
                          <button className="btn sm" disabled={acting}
                            onClick={() => transition(r.draft_id, 'redirected')}>
                            转人工
                          </button>
                        )}
                        {r.status === 'redirected' && (
                          <span style={{ fontSize: 11, color: 'var(--text-4)' }}>已结案</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DraftsPage });
