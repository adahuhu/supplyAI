// Dashboard page: risk overview, stockout, suggestions, health, queue, today actions.

function StatCard({ label, value, currency, unit, sub, accent, accentColor, onClick, trend, trendPct, trendData, footer }) {
  const sparkColor = accentColor || (
  accent === 'p1' ? 'var(--p1)' : accent === 'p2' ? 'var(--p2)' : accent === 'p3' ? 'var(--p3)' : 'var(--accent)');
  return (
    <button onClick={onClick} className={onClick ? 'card interactive' : 'card'} style={{
      appearance: 'none', textAlign: 'left', cursor: onClick ? 'pointer' : 'default',
      padding: '13px 14px 12px',
      display: 'flex', flexDirection: 'column', gap: 9,
      fontFamily: 'inherit', color: 'inherit',
      minWidth: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-3)', fontWeight: 500, letterSpacing: '-0.005em' }}>
          {accent && <span className={'dot ' + accent} />}
          {label}
        </div>
        {trendPct != null && <TrendChip value={trendPct} />}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
        <NumDisplay value={value} currency={currency} unit={unit} size={27} />
        {sub && <div style={{ fontSize: 11.5, color: 'var(--text-3)', letterSpacing: '-0.005em' }}>{sub}</div>}
      </div>
      {trendData ?
      <div style={{ marginTop: 2 }}>
          <Sparkline data={trendData} width={158} height={28} color={sparkColor} strokeWidth={1.25} />
        </div> :
      footer ?
      <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{footer}</div> :
      null}
    </button>);

}

function Dashboard({ setRoute, openAI }) {
  const stats = DASH_STATS;
  const queue = SKUS.filter((s) => s.priority === 'p1' || s.priority === 'p2').slice(0, 8);

  return (
    <div style={{ padding: '18px 22px 40px', display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1480, minWidth: 980, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 0, flex: '1 1 320px' }}>
          <div className="h1"><span className="marker" />分析工作台</div>
          <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 6, letterSpacing: '-0.005em' }}>
            扫描全部店铺与 SKU，识别断货风险并给出可执行采购建议
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <Filter label="店铺" value="全部 (6)" />
          <Filter label="国家" value="全部 (6)" />
          <Filter label="负责人" value="全部" />
        </div>
      </div>

      {/* Financial KPI row — yesterday's snapshot */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(208px, 1fr))', gap: 10 }}>
        <StatCard label="昨日销量" value={fmt.num(stats.salesY)} unit="件" sub="全店铺合计"
        trendPct={stats.salesTrendPct}
        trendData={stats.salesTrend} accentColor="var(--accent)" />
        <StatCard label="昨日利润" value={fmt.num(stats.profitY)} currency="$"
        sub={`毛利率 ${(stats.profitY / Math.max(1, stats.gmvY) * 100).toFixed(1)}%`}
        trendPct={2.4}
        trendData={stats.profitTrend} accentColor="var(--p3)" />
        <StatCard label="昨日收入" value={fmt.num(stats.gmvY)} currency="$" sub="全店铺合计"
        trendPct={-1.8}
        trendData={stats.gmvTrend} accentColor="var(--accent)" />
        <StatCard label="昨日成本" value={fmt.num(stats.costY)} currency="$" sub="采购+头程"
        trendPct={-0.6}
        trendData={stats.costTrend} accentColor="var(--text-3)" />
        <StatCard label="昨日费用" value={fmt.num(stats.expenseY)} currency="$" sub="平台配送"
        trendPct={0.3}
        trendData={stats.expenseTrend} accentColor="var(--text-3)" />
      </div>

      {/* Second row — 4 panels: 库存健康 / 断货趋势 / 积压库存 / 节日促销 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
        {/* 1. 库存健康概览 */}
        <Panel title="库存健康概览" sub="基于全部活跃 SKU + 店铺组合">
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{ position: 'relative', width: 96, height: 96, flex: 'none' }}>
              <Donut size={96} thickness={11}
              values={[stats.counts.p1, stats.counts.p2, stats.counts.p3, stats.counts.safe]}
              colors={['var(--p1)', 'var(--p2)', 'var(--p3)', 'var(--safe)']} />
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className="tabular" style={{ fontSize: 22, fontWeight: 540, letterSpacing: '-0.022em' }}>{stats.healthScore}</div>
                <div style={{ fontSize: 10, color: 'var(--text-3)' }}>健康分</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
              ['p1', 'P1 紧急', stats.counts.p1],
              ['p2', 'P2 重要', stats.counts.p2],
              ['p3', 'P3 关注', stats.counts.p3],
              ['safe', '安全', stats.counts.safe]].
              map(([k, l, v]) =>
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                  <span className={'dot ' + k} />
                  <span style={{ flex: 1, color: 'var(--text-2)' }}>{l}</span>
                  <span className="tabular" style={{ fontWeight: 500 }}>{v}</span>
                  <span className="tabular muted" style={{ fontSize: 11, width: 32, textAlign: 'right' }}>{(v / 48 * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </div>
          <div className="divider" style={{ margin: '14px 0' }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            <KV k="总库存" v={fmt.num(stats.totalStock) + ' 件'} />
            <KV k="近 7 天销量" v={fmt.num(stats.totalSales7) + ' 件'} />
            <KV k="平均可售天数" v="42 天" />
          </div>
        </Panel>

        {/* 2. 新增断货 SKU 合计趋势图 */}
        <Panel
          title="近七天断货 SKU"
          sub="当日库存 = 0"
          right={<button className="btn sm ghost" onClick={() => setRoute({ page: 'list', filter: 'p1' })}>查看 →</button>}>
          <button
            onClick={() => setRoute({ page: 'list', filter: 'p1' })}
            style={{
              appearance: 'none', textAlign: 'left', cursor: 'pointer',
              background: 'transparent', border: 0, padding: 0, width: '100%',
              fontFamily: 'inherit', color: 'inherit',
              display: 'flex', flexDirection: 'column', gap: 8
            }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <div className="tabular" style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1, color: 'var(--p1)' }}>{stats.stockoutTrendTotal}</div>
              <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>累计 SKU 数 </div>
            </div>
            {(() => {
              const data = stats.stockoutTrend;
              const max = Math.max(...data, 1);
              const today = stats.asOf || new Date();
              const labels = data.map((_, i) => {
                const d = new Date(today);
                d.setDate(d.getDate() - (data.length - 1 - i));
                return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`;
              });
              return (
                <div style={{ display: 'grid', gridTemplateColumns: `repeat(${data.length}, 1fr)`, columnGap: 6, width: '100%', alignItems: 'end' }}>
                  {data.map((v, i) =>
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                      <div className="tabular" style={{ fontSize: 11, color: 'var(--text-2)', fontWeight: 500, lineHeight: 1 }}>{v}</div>
                      <div style={{
                      width: '100%', height: Math.round(8 + v / max * 36),
                      background: 'var(--p1)', opacity: 0.22 + v / max * 0.6,
                      borderRadius: 2
                    }} />
                      <div className="tabular" style={{ fontSize: 10, color: 'var(--text-4)', lineHeight: 1 }}>{labels[i]}</div>
                    </div>
                  )}
                </div>);

            })()}
          </button>
        </Panel>

        {/* 3. 积压库存 */}
        <Panel
          title="积压库存"
          sub="库龄 > 90 天"
          right={<button className="btn sm ghost" onClick={() => setRoute({ page: 'list', filter: 'overstock' })}>查看 →</button>}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
            <NumDisplay value={stats.overstockCount} size={30} color="var(--p2)" />
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>积压 SKU 数</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 0', borderTop: '1px solid var(--border)' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: 'var(--text-3)' }}>占用库存量</div>
              <div className="tabular" style={{ fontSize: 14, fontWeight: 540, letterSpacing: '-0.012em' }}>{fmt.num(stats.overstockQty)} <span style={{ fontSize: 11, color: 'var(--text-4)', fontWeight: 400 }}>件</span></div>
            </div>
          </div>
        </Panel>

        {/* 4. 节日促销提示 */}
        <Panel
          title="节日促销提示"
          sub="未来 90 天大促节点"
          right={<button className="btn sm ghost">参考历史 →</button>}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {[
            { d: 'D-12', kind: 'p1', name: '母亲节', date: '5/17', count: 14 },
            { d: 'D-32', kind: 'p2', name: '父亲节', date: '6/16', count: 9 },
            { d: 'D-56', kind: 'p3', name: 'Prime Day', date: '7/10', count: 32 }].
            map((p, i) =>
            <div key={p.name} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px 0',
              borderTop: i > 0 ? '1px solid var(--border)' : 'none'
            }}>
                <div style={{
                width: 36, textAlign: 'center', padding: '3px 0',
                background: `var(--${p.kind}-soft)`, color: `var(--${p.kind}-strong)`,
                borderRadius: 4, fontSize: 10, fontWeight: 600
              }}>{p.d}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name} · {p.date}</div>
                </div>
                <span className="chip" style={{ height: 18, fontSize: 10.5 }}>{p.count}</span>
              </div>
            )}
          </div>
        </Panel>
      </div>

      {/* High-risk queue + Today actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 12 }}>
      <Panel
          title="高风险 SKU 队列"
          sub={<span>按 P1 → P2排序 · <span style={{ color: 'var(--p1)', fontWeight: 600 }}>{stats.stockout7}</span> 个 SKU 将在 7 天内断货</span>}
          right={
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn sm primary"><Icon name="lightning" size={12} />批量生成采购计划</button>
          </div>
          }
          noPad>

        <div className="tbl-wrap" style={{ borderLeft: 0, borderRight: 0, borderRadius: 0, borderTop: 0, borderBottom: 0 }}>
          <table className="t">
            <thead>
              <tr>
                <th style={{ width: 28 }}><input type="checkbox" /></th>
                <th>风险</th>
                <th>SKU</th>
                <th>店铺 / 国家</th>
                <th className="num">未来日销</th>
                <th className="num">总库存</th>
                <th className="num">FBA 可售</th>
                <th>预计断货</th>
                <th className="num">建议采购</th>
                <th>建议采购时间</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {queue.map((s) =>
                <tr key={s.id} style={{ cursor: 'pointer' }}
                onClick={() => setRoute({ page: 'sku', skuId: s.id })}>
                  <td><input type="checkbox" onClick={(e) => e.stopPropagation()} /></td>
                  <td><PriorityBadge level={s.priority} /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 260 }}>
                      <ProductImage label={s.msku.slice(-3)} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-3)' }} className="mono">{s.msku} · {s.sku}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{s.country.flag}</span>
                      <span style={{ fontSize: 12 }}>{s.store}</span>
                    </div>
                  </td>
                  <td className="num tabular">{s.futureDaily}</td>
                  <td className="num tabular">{fmt.num(s.totalStock)}</td>
                  <td className="num tabular" style={{ color: s.fbaSellable <= 7 ? 'var(--p1)' : 'inherit', fontWeight: s.fbaSellable <= 7 ? 600 : 400 }}>
                    {s.fbaSellable} 天
                  </td>
                  <td className="tabular">{fmt.dateLong(s.stockoutDate)}<span style={{ color: 'var(--text-3)', marginLeft: 6, fontSize: 11 }}>{fmt.rel(s.stockoutDate)}</span></td>
                  <td className="num tabular" style={{ fontWeight: 500 }}>{fmt.num(s.suggestQty)}</td>
                  <td className="tabular" style={{ color: 'var(--text-2)' }}>{fmt.dateLong(s.purchaseDate)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <button className="btn sm ghost"><Icon name="more" size={14} /></button>
                  </td>
                </tr>
                )}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="今日建议动作" sub={`基于 ${fmt.dateLong(stats.asOf)} 计算快照`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {TODAY_ACTIONS.map((a, i) =>
            <div key={a.id} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 0',
              borderBottom: i < TODAY_ACTIONS.length - 1 ? '1px solid var(--border)' : 'none'
            }}>
              <span className={'dot ' + (a.kind === 'urgent' ? 'p1' : a.kind === 'review' ? 'p2' : 'p3')} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12.5 }}>{a.title}</div>
              </div>
              <button className="btn sm ghost" style={{ color: 'var(--accent-text)' }}>{a.action} →</button>
            </div>
            )}
        </div>
      </Panel>
      </div>
    </div>);

}
function Filter({ label, value, onClick }) {
  return (
    <button className="btn" onClick={onClick} style={{ paddingRight: 8 }}>
      <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>{label}</span>
      <span style={{ fontWeight: 500 }}>{value}</span>
      <Icon name="chevron-down" size={12} color="var(--text-3)" />
    </button>);
}

function Panel({ title, sub, right, children, noPad, style }) {
  return (
    <section className="card" style={{
      overflow: 'hidden',
      ...style
    }}>
      <header style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '13px 14px 10px',
        borderBottom: '1px solid var(--border)'
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="h3" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>{title}</div>
          {sub && <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 2, letterSpacing: '-0.005em' }}>{sub}</div>}
        </div>
        {right}
      </header>
      <div style={{ padding: noPad ? 0 : '12px 14px 14px' }}>{children}</div>
    </section>);
}

Object.assign(window, { Dashboard, Panel, Filter });
