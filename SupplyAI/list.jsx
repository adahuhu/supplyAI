// 备货计划列表页 — full data table with filters, batch ops, column config.

function FilterBar({ filter, setFilter }) {
  const segs = [
  { v: 'all', label: '全部', count: 48 },
  { v: 'p1', label: 'P1 紧急', count: DASH_STATS.counts.p1, color: 'p1' },
  { v: 'p2', label: 'P2 重要', count: DASH_STATS.counts.p2, color: 'p2' },
  { v: 'p3', label: 'P3 关注', count: DASH_STATS.counts.p3, color: 'p3' },
  { v: 'safe', label: '安全', count: DASH_STATS.counts.safe, color: 'safe' },
  { v: 'suggest', label: '建议采购', count: DASH_STATS.suggestSkuCount },
  { v: 'stockout7', label: '7 天内断货', count: DASH_STATS.stockout7 }];

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 4,
      padding: '0 4px',
      borderBottom: '1px solid var(--border)',
      overflowX: 'auto'
    }}>
      {segs.map((s) => {
        const active = filter === s.v;
        return (
          <button key={s.v} onClick={() => setFilter(s.v)} style={{
            appearance: 'none', border: 0, background: 'transparent',
            padding: '10px 12px',
            fontSize: 12.5, color: active ? 'var(--text)' : 'var(--text-3)',
            fontWeight: active ? 600 : 400,
            cursor: 'pointer',
            borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 6,
            fontFamily: 'inherit',
            whiteSpace: 'nowrap'
          }}>
            {s.color && <span className={'dot ' + s.color} />}
            {s.label}
            <span className="tabular" style={{
              fontSize: 11, color: 'var(--text-4)', fontWeight: 500,
              background: active ? 'var(--accent-soft)' : 'var(--surface-hover)',
              padding: '1px 6px', borderRadius: 999
            }}>{s.count}</span>
          </button>);

      })}
    </div>);

}

function ListPage({ initialFilter = 'all', setRoute, openRules, openCreatePO }) {
  const [filter, setFilter] = React.useState(initialFilter);
  const [selected, setSelected] = React.useState(new Set());
  const [advFilters, setAdvFilters] = React.useState(false);
  const [columnsOpen, setColumnsOpen] = React.useState(false);

  const filtered = React.useMemo(() => {
    let rows = SKUS;
    if (filter === 'p1') rows = rows.filter((s) => s.priority === 'p1');else
    if (filter === 'p2') rows = rows.filter((s) => s.priority === 'p2');else
    if (filter === 'p3') rows = rows.filter((s) => s.priority === 'p3');else
    if (filter === 'safe') rows = rows.filter((s) => s.priority === 'safe');else
    if (filter === 'suggest') rows = rows.filter((s) => s.suggest);else
    if (filter === 'stockout7') rows = rows.filter((s) => s.fbaSellable <= 7);
    return rows;
  }, [filter]);

  const toggleAll = () => {
    if (selected.size === filtered.length) setSelected(new Set());else
    setSelected(new Set(filtered.map((s) => s.id)));
  };
  const toggleOne = (id) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);else next.add(id);
    setSelected(next);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Header */}
      <div style={{ padding: '20px 24px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <div>
            <div className="h1">备货计划</div>
            <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 4 }}>粒度：MSKU + 店铺 

            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button className="btn"><Icon name="download" size={13} />导出</button>
            <button className="btn"><Icon name="settings" size={13} />规则中心</button>
          </div>
        </div>

        {/* Filter row 1 */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', width: 280 }}>
            <Icon name="search" size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
            <input className="txt" placeholder="SKU / 品名 / MSKU / FNSKU / ASIN / 父 ASIN" style={{ width: '100%', paddingLeft: 30 }} />
          </div>
          <Filter label="国家" value="全部" />
          <Filter label="店铺" value="全部" />
          <Filter label="Listing 标签" value="全部" />
          <Filter label="是否建议采购" value="全部" />
          <Filter label="时间" value="近 7 天" />
          <button className="btn ghost" onClick={() => setAdvFilters(!advFilters)} style={{ color: 'var(--accent-text)' }}>
            <Icon name="filter" size={13} />高级筛选 {advFilters ? '收起' : '展开'}
          </button>
          <div style={{ flex: 1 }} />
          <button className="btn" onClick={() => setColumnsOpen(true)}><Icon name="columns" size={13} />列配置</button>
        </div>

        {advFilters &&
        <div className="fade-in" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', padding: '10px 12px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)' }}>
            <Filter label="负责人" value="全部 (6)" />
            <Filter label="品线" value="全部 (4)" />
            <Filter label="分类" value="全部" />
            <Filter label="品牌" value="全部 (4)" />
            <Filter label="状态" value="在售" />
            <Filter label="可售天数" value="任意" />
            <button className="btn ghost sm">清除全部</button>
          </div>
        }
      </div>

      <FilterBar filter={filter} setFilter={setFilter} />

      {/* Batch action bar */}
      {selected.size > 0 &&
      <div className="fade-in" style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 24px',
        background: 'var(--accent-soft)',
        borderBottom: '1px solid var(--border)'
      }}>
          <span style={{ fontSize: 12.5, fontWeight: 500 }}>已选 {selected.size} 项</span>
          <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>· 批量生成最多 50 条 · 批量特配最多 200 条</span>
          <div style={{ flex: 1 }} />
          <button className="btn sm" onClick={() => openRules({ batch: true, count: selected.size })}>
            <Icon name="settings" size={12} />批量规则设置
          </button>
          <button className="btn sm">
            <Icon name="download" size={12} />导出所选
          </button>
          <button className="btn sm primary" onClick={() => openCreatePO(Array.from(selected))}>
            <Icon name="lightning" size={12} />生成采购计划（{selected.size}）
          </button>
          <button className="btn sm ghost icon" onClick={() => setSelected(new Set())}><Icon name="x" size={13} /></button>
        </div>
      }

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
        <table className="t" style={{ minWidth: 1900 }}>
          <thead>
            <tr>
              <th style={{ width: 36, position: 'sticky', left: 0, background: 'var(--surface)', zIndex: 3 }}>
                <input type="checkbox" checked={selected.size === filtered.length && filtered.length > 0} onChange={toggleAll} />
              </th>
              <th style={{ position: 'sticky', left: 36, background: 'var(--surface)', zIndex: 3, minWidth: 280 }}>商品</th>
              <th>店铺/国家</th>
              <th>状态</th>
              <th>风险</th>
              <th className="num">近 7 天销量</th>
              <th className="num">预测日销</th>
              <th className="num">收入</th>
              <th className="num">毛利率</th>
              <th className="num">FBA 可用</th>
              <th className="num">FBA 在途</th>
              <th className="num">本地库存</th>
              <th className="num">本地在途</th>
              <th className="num">总库存</th>
              <th className="num">可售天数</th>
              <th>预计断货</th>
              <th className="num">采购时效</th>
              <th>建议采购</th>
              <th className="num">建议采购量</th>
              <th>建议采购时间</th>
              <th>最后更新</th>
              <th style={{ position: 'sticky', right: 0, background: 'var(--surface)', zIndex: 3, width: 80 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => {
              const sel = selected.has(s.id);
              return (
                <tr key={s.id} className={sel ? 'selected' : ''}
                style={{ cursor: 'pointer' }}
                onClick={() => setRoute({ page: 'sku', skuId: s.id })}>
                  <td style={{ position: 'sticky', left: 0, background: sel ? 'var(--accent-soft)' : 'var(--surface)', zIndex: 1 }} onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={sel} onChange={() => toggleOne(s.id)} />
                  </td>
                  <td style={{ position: 'sticky', left: 36, background: sel ? 'var(--accent-soft)' : 'var(--surface)', zIndex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, maxWidth: 280 }}>
                      <ProductImage label={s.msku.slice(-3)} size={36} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12.5 }}>{s.name}</div>
                        <div style={{ fontSize: 10.5, color: 'var(--text-3)', display: 'flex', gap: 6 }} className="mono">
                          <span>{s.msku}</span>·<span>{s.asin}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{s.country.flag}</span>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: 12 }}>{s.store}</span>
                        <span style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{s.country.name}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="chip" style={{ height: 20, fontSize: 10.5 }}>{s.status}</span>
                  </td>
                  <td><RiskCellWithTip level={s.priority} /></td>
                  <td className="num">
                    <SalesTrendCell data={s.recent7} />
                  </td>
                  <td className="num tabular">{s.futureDaily}</td>
                  <td className="num tabular">{fmt.money(s.revenue7)}</td>
                  <td className="num tabular" style={{ color: s.grossMargin < 0 ? 'var(--p1)' : 'inherit' }}>{fmt.pct(s.grossMargin)}</td>
                  <td className="num tabular">{fmt.num(s.fbaAvail)}</td>
                  <td className="num tabular muted">{fmt.num(s.fbaInTransit)}</td>
                  <td className="num tabular muted">{fmt.num(s.localTotal)}</td>
                  <td className="num tabular muted">{fmt.num(s.localPlan)}</td>
                  <td className="num tabular" style={{ fontWeight: 500 }}>{fmt.num(s.totalStock)}</td>
                  <td className="num tabular" style={{
                    color: s.priority === 'p1' ? 'var(--p1)' : s.priority === 'p2' ? 'var(--p2)' : 'inherit',
                    fontWeight: s.priority === 'p1' || s.priority === 'p2' ? 600 : 400
                  }}>{s.sellable} 天</td>
                  <td className="tabular">
                    <div style={{ fontSize: 12 }}>{fmt.dateLong(s.stockoutDate)}</div>
                    <div style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{fmt.rel(s.stockoutDate)}</div>
                  </td>
                  <td className="num tabular muted">{s.purchaseLeadTime}d</td>
                  <td>
                    {s.suggest ? <span className="chip p1" style={{ height: 20, fontSize: 10.5 }}>建议</span> : <span className="chip safe" style={{ height: 20, fontSize: 10.5 }}>无需</span>}
                  </td>
                  <td className="num tabular" style={{ fontWeight: 500 }}>{s.suggest ? fmt.num(s.suggestQty) : '—'}</td>
                  <td className="tabular muted">{s.suggest ? fmt.dateLong(s.purchaseDate) : '—'}</td>
                  <td className="tabular muted" style={{ fontSize: 11 }}>{fmt.time(s.lastUpdated)}</td>
                  <td style={{ position: 'sticky', right: 0, background: sel ? 'var(--accent-soft)' : 'var(--surface)', zIndex: 1 }} onClick={(e) => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: 2 }}>
                      <button className="btn ghost icon sm" title="规则设置" onClick={() => openRules({ sku: s })}><Icon name="settings" size={13} /></button>
                      <button className="btn ghost icon sm" title="生成采购计划" onClick={() => openCreatePO([s.id])}><Icon name="plus" size={13} /></button>
                    </div>
                  </td>
                </tr>);

            })}
          </tbody>
        </table>
      </div>

      {/* Footer / pagination */}
      <div style={{
        flex: 'none',
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 24px',
        borderTop: '1px solid var(--border)',
        background: 'var(--surface)',
        fontSize: 12, color: 'var(--text-3)'
      }}>
        <span>共 {filtered.length} 条</span>
        <span>·</span>
        <span>已选 {selected.size}</span>
        <div style={{ flex: 1 }} />
        <span>每页</span>
        <select className="sel" style={{ height: 26, padding: '0 8px' }}><option>50</option><option>100</option></select>
        <button className="btn sm ghost icon" disabled><Icon name="chevron-left" size={13} /></button>
        <span className="tabular">1 / 1</span>
        <button className="btn sm ghost icon" disabled><Icon name="chevron-right" size={13} /></button>
      </div>

      {/* Column config drawer */}
      <Drawer open={columnsOpen} onClose={() => setColumnsOpen(false)} width={360} title="列配置">
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="h3">列配置</div>
          <button className="btn ghost icon sm" onClick={() => setColumnsOpen(false)}><Icon name="x" size={14} /></button>
        </div>
        <div style={{ padding: 16, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[
          '商品', '店铺/国家', '状态', '标签', '风险', '近 7 天销量', '预测日销',
          '收入', '支出', '成本', '毛利润', '毛利率',
          'FBA 可用', 'FBA 在途', '本地实际', '本地预计', '本地库存', '总库存',
          '可售天数', '预计断货', '采购时效', '建议采购', '建议采购量', '建议采购时间', '最后更新'].
          map((c, i) =>
          <label key={c} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', fontSize: 12.5 }}>
              <input type="checkbox" defaultChecked={i < 18 || i > 19 ? true : true} />
              <span>{c}</span>
            </label>
          )}
        </div>
        <div style={{ padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="btn">重置</button>
          <button className="btn primary" onClick={() => setColumnsOpen(false)}>应用</button>
        </div>
      </Drawer>
    </div>);

}

function SalesTrendCell({ data }) {
  const [open, setOpen] = React.useState(false);
  const total = data.reduce((a, b) => a + b, 0);
  const today = new Date('2026-05-04');
  const max = Math.max(...data, 1);
  return (
    <div
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onClick={(e) => e.stopPropagation()}
      style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end', cursor: 'help' }}>
      <Sparkline data={data} width={48} height={18} color="var(--text-3)" />
      <span className="tabular">{total}</span>
      {open && (
        <div role="tooltip" style={{
          position: 'absolute', zIndex: 50,
          right: 0, top: 'calc(100% + 6px)',
          width: 240, padding: '10px 12px',
          background: 'var(--surface)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--r-md)',
          boxShadow: '0 8px 24px -6px rgba(0,0,0,0.18)',
          textAlign: 'left',
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6, fontWeight: 500 }}>近 7 天日销</div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 48, marginBottom: 8 }}>
            {data.map((v, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                <div className="tabular" style={{ fontSize: 10, color: 'var(--text-3)' }}>{v}</div>
                <div style={{ width: '100%', height: (v / max) * 32, background: 'var(--accent)', opacity: 0.7, borderRadius: 2, minHeight: 2 }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-4)' }}>
            {data.map((_, i) => {
              const d = new Date(today.getTime() - (6 - i) * 86400000);
              return <span key={i} style={{ flex: 1, textAlign: 'center' }}>{d.getMonth() + 1}/{d.getDate()}</span>;
            })}
          </div>
          <div style={{ borderTop: '1px solid var(--border)', marginTop: 8, paddingTop: 6, fontSize: 11, color: 'var(--text-3)', display: 'flex', justifyContent: 'space-between' }}>
            <span>合计</span>
            <span className="tabular" style={{ color: 'var(--text)', fontWeight: 500 }}>{total} 件</span>
          </div>
        </div>
      )}
    </div>
  );
}

function RiskCellWithTip({ level }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onClick={(e) => e.stopPropagation()}
      style={{ position: 'relative', display: 'inline-block', cursor: 'help' }}>
      <PriorityBadge level={level} />
      {open && (
        <div role="tooltip" style={{
          position: 'absolute', zIndex: 50,
          left: 0, top: 'calc(100% + 6px)',
          width: 220, padding: '10px 12px',
          background: 'var(--surface)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--r-md)',
          boxShadow: '0 8px 24px -6px rgba(0,0,0,0.18)',
          textAlign: 'left',
          display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 4, fontWeight: 500 }}>风险等级（按 FBA 可售天数）</div>
          {[
            ['p1', 'P1 紧急', '7 天内断货'],
            ['p2', 'P2 重要', '15 天内断货'],
            ['p3', 'P3 关注', '30 天内断货'],
            ['safe', '安全', '30 天以上断货'],
          ].map(([k, label, desc]) => (
            <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5 }}>
              <span className={'dot ' + k} style={{ flex: 'none' }} />
              <span style={{ color: 'var(--text-2)', fontWeight: level === k ? 600 : 400 }}>{label}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--text-3)' }}>{desc}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { ListPage, FilterBar, SalesTrendCell, RiskCellWithTip });