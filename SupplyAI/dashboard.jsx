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

// Compact secondary stat — 用在 KPI 区右半 2x2 网格里，
// 紧凑、无 sparkline、可选 trend chip。
function MiniStat({ label, value, currency, unit, trendPct, sub }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
        <span style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 500, letterSpacing: '-0.005em' }}>{label}</span>
        {trendPct != null && <TrendChip value={trendPct}/>}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, flexWrap: 'wrap' }}>
        {currency && <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 500 }}>{currency}</span>}
        <span className="tabular" style={{ fontSize: 22, fontWeight: 540, letterSpacing: '-0.022em', lineHeight: 1 }}>{value}</span>
        {unit && <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{sub}</div>}
    </div>
  );
}

// FinancialSummary — 1 hero card + 2x2 小卡，5 张独立卡片用 grid gap 分开。
// 不是均等分（hero 占左 1.3fr 跨两行），也不是粘在一起（每张卡有自己的边框和呼吸）。
function FinancialSummary() {
  const stats = DASH_STATS;
  const grossRate = (stats.profitY / Math.max(1, stats.gmvY) * 100).toFixed(1);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'minmax(300px, 1.3fr) 1fr 1fr',
      gridTemplateRows: 'auto auto',
      gap: 12
    }}>

      {/* Hero — 今日利润 (左, span 2 行, 独立卡片) */}
      <div className="card" style={{
        gridRow: 'span 2',
        padding: '18px 22px',
        display: 'flex', flexDirection: 'column', gap: 14, justifyContent: 'space-between',
        minHeight: 168,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <span style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 500, letterSpacing: '-0.005em' }}>今日利润</span>
          {stats.profitTrendPct != null && <TrendChip value={stats.profitTrendPct}/>}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 18, color: 'var(--text-3)', fontWeight: 500 }}>$</span>
            <span className="tabular" style={{ fontSize: 36, fontWeight: 600, letterSpacing: '-0.026em', lineHeight: 1 }}>{fmt.num(stats.profitY)}</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6 }}>毛利率 {grossRate}% · 较昨日</div>
        </div>
        <Sparkline data={stats.profitTrend} width={260} height={36}
          color="var(--accent)" strokeWidth={1.5}/>
      </div>

      {/* 4 个独立小卡 — 销量 / 收入 / 成本 / 费用 */}
      <div className="card" style={{ padding: '14px 18px' }}>
        <MiniStat label="今日销量" value={fmt.num(stats.salesY)} unit="件"
          trendPct={stats.salesTrendPct} sub="全店铺合计 · 较昨日"/>
      </div>
      <div className="card" style={{ padding: '14px 18px' }}>
        <MiniStat label="今日收入" value={fmt.num(stats.gmvY)} currency="$"
          trendPct={stats.gmvTrendPct} sub="全店铺合计 · 较昨日"/>
      </div>
      <div className="card" style={{ padding: '14px 18px' }}>
        <MiniStat label="今日成本" value={fmt.num(stats.costY)} currency="$"
          trendPct={stats.costTrendPct} sub="采购 + 头程 · 较昨日"/>
      </div>
      <div className="card" style={{ padding: '14px 18px' }}>
        <MiniStat label="今日费用" value={fmt.num(stats.expenseY)} currency="$"
          trendPct={stats.expenseTrendPct} sub="平台 + 配送 · 较昨日"/>
      </div>
    </div>
  );
}

// Dashboard hero — "今日要做的事" 工作摘要。把分散在 4-up panels 里的关键信号
// 浓缩成一个动作驱动的陈述，放在第一屏视觉中心。下方所有 panel 保留不动。
function HeroSummary({ setRoute }) {
  const data = React.useMemo(() => {
    const suggested = SKUS.filter((s) => s.suggest);
    const urgent = SKUS.filter((s) => s.stockoutRecent7).length;
    const totalAmount = Math.round(
      suggested.reduce((sum, s) => sum + s.suggestQty * (s.cost || 0), 0)
    );
    const totalSuggestQty = suggested.reduce((sum, s) => sum + (s.suggestQty || 0), 0);
    const storeCount = new Set(suggested.map((s) => s.store)).size;
    // FBA 发货建议
    const shipSkus = SKUS.filter(s => s.shipQty > 0 && !s.isClearance);
    const totalShipQty = shipSkus.reduce((sum, s) => sum + (s.shipQty || 0), 0);
    const now = new Date();
    const urgentShipCount = shipSkus.filter(s => s.shipDate && Math.round((s.shipDate - now) / 86400000) <= 14).length;
    return { needCount: suggested.length, urgent, totalAmount, totalSuggestQty, storeCount, shipSkuCount: shipSkus.length, totalShipQty, urgentShipCount };
  }, []);

  return (
    <section
      className="card"
      style={{
        position: 'relative',
        padding: '0',
        background: 'linear-gradient(135deg, var(--accent-soft) 0%, transparent 60%), var(--surface)',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'stretch',
        minHeight: 100,
      }}>

      {/* Accent left rail */}
      <div style={{ width: 3, flex: 'none', background: 'var(--accent)', borderRadius: '6px 0 0 6px' }} />

      {/* Left: hero statement */}
      <div style={{ flex: 1, minWidth: 0, padding: '20px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 8 }}>
        <div className="label" style={{ letterSpacing: '0.04em' }}>今日工作摘要</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
          <span className="tabular" style={{ fontSize: 44, fontWeight: 660, lineHeight: 1, letterSpacing: '-0.03em', color: 'var(--text)' }}>
            {data.needCount}
          </span>
          <span style={{ fontSize: 16, fontWeight: 500, color: 'var(--text)', letterSpacing: '-0.01em' }}>
            个 SKU 需要立即下采购
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-3)' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span className="dot p1" style={{ width: 6, height: 6 }} />
            <span className="tabular" style={{ fontWeight: 600, color: 'var(--p1)' }}>{data.urgent}</span>
            <span>个 7 天内断货</span>
          </span>
          <span style={{ color: 'var(--border-strong)' }}>·</span>
          <span>涉及 <span className="tabular" style={{ fontWeight: 500, color: 'var(--text-2)' }}>{data.storeCount}</span> 个店铺</span>
        </div>
      </div>

      {/* Right: 两个语义分组卡片 */}
      <div style={{ display: 'flex', alignItems: 'stretch', flex: 'none', gap: 0 }}>

        {/* 组 1：采购建议 */}
        <div style={{
          borderLeft: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          padding: '14px 24px 12px',
          minWidth: 160,
          position: 'relative',
        }}>
          <div style={{ borderTop: '2px solid var(--p2)', position: 'absolute', top: 0, left: 24, right: 24 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 10 }}>
            <Icon name="package" size={11} color="var(--p2)" />
            <span style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--p2)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>采购建议</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 5 }}>
              <span className="tabular" style={{ fontSize: 28, fontWeight: 650, lineHeight: 1, letterSpacing: '-0.025em', color: 'var(--text)' }}>
                {fmt.num(data.totalSuggestQty)}
              </span>
              <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>件</span>
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>
              {data.totalAmount > 0
                ? <span>预计 <span className="tabular" style={{ color: 'var(--text-2)', fontWeight: 500 }}>{fmt.money(data.totalAmount)}</span></span>
                : <span style={{ color: 'var(--text-4)' }}>成本待录入</span>}
            </div>
          </div>
          <button
            onClick={() => setRoute({ page: 'list', filter: 'suggest' })}
            style={{ marginTop: 10, appearance: 'none', border: 'none', background: 'none', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 3, fontSize: 11, color: 'var(--p2)', fontFamily: 'inherit', fontWeight: 500 }}>
            查看采购 <span style={{ fontSize: 10 }}>→</span>
          </button>
        </div>

        {/* 组 2：FBA 发货建议 */}
        <div style={{
          borderLeft: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          padding: '14px 24px 12px',
          minWidth: 160,
          position: 'relative',
          background: data.urgentShipCount > 0 ? 'rgba(248,113,113,0.04)' : 'transparent',
        }}>
          <div style={{ borderTop: '2px solid var(--accent)', position: 'absolute', top: 0, left: 24, right: 24 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 10 }}>
            <Icon name="lightning" size={11} color="var(--accent)" />
            <span style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--accent-text)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>FBA 发货</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 5 }}>
              <span className="tabular" style={{ fontSize: 28, fontWeight: 650, lineHeight: 1, letterSpacing: '-0.025em', color: data.shipSkuCount > 0 ? 'var(--accent-text)' : 'var(--text-4)' }}>
                {data.shipSkuCount}
              </span>
              <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>个 SKU</span>
            </div>
            <div style={{ fontSize: 11.5 }}>
              {data.urgentShipCount > 0
                ? <span style={{ color: 'var(--p1)', fontWeight: 500 }}>
                    <span className="tabular">{data.urgentShipCount}</span> 个窗口 ≤14天
                  </span>
                : <span style={{ color: 'var(--text-4)' }}>暂无紧迫窗口</span>}
            </div>
          </div>
          <button
            onClick={() => setRoute({ page: 'list', filter: 'shipSuggest' })}
            style={{ marginTop: 10, appearance: 'none', border: 'none', background: 'none', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 3, fontSize: 11, color: 'var(--accent-text)', fontFamily: 'inherit', fontWeight: 500 }}>
            查看发货 <span style={{ fontSize: 10 }}>→</span>
          </button>
        </div>

      </div>
    </section>);

}

// action_hint 标签映射
const ACTION_HINT_META = {
  urgent_purchase: { label: '紧急采购', cls: 'p1' },
  follow_up:       { label: '跟进',     cls: 'p2' },
  review:          { label: '复核',     cls: 'p3' },
  ok:              { label: '正常',     cls: 'safe' },
};

const HOLIDAY_NAME_LABEL = {
  'Mothers Day': '母亲节',
  "Mother's Day": '母亲节',
  'Memorial Day': 'Memorial Day',
  'Prime Day': 'Prime Day',
};

function holidayLabel(h) {
  return h ? (HOLIDAY_NAME_LABEL[h.name] || h.name || '大促') : '大促';
}

function holidayDate(h) {
  if (!h?.peak) return null;
  const d = new Date(h.peak + 'T00:00:00');
  return Number.isNaN(d.getTime()) ? null : d;
}

function nextHolidayFromData(asOf) {
  const today = asOf instanceof Date && !Number.isNaN(asOf.getTime()) ? asOf : new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const list = (window.HOLIDAYS_DATA || [])
    .map(h => ({ ...h, peakDate: holidayDate(h) }))
    .filter(h => h.peakDate && h.peakDate.getTime() >= todayStart)
    .sort((a, b) => a.peakDate - b.peakDate);
  return list[0] || null;
}

function holidayRelatedSkus(holiday, skus = SKUS) {
  if (!holiday) return [];
  const countryCode = holiday.countryCode || null;
  const normalize = (v) => String(v || '').toLowerCase().replace(/[\s_\-]+/g, '');
  const holidayName = String(holiday.name || '');
  const keys = [
    holiday.id,
    holiday.name,
    '大促',
    holidayName.toLowerCase().includes('promo') ? 'promo' : '',
    holidayName.toLowerCase().includes('prime') ? 'Prime Day' : '',
    holidayName.toLowerCase().includes('memorial') ? 'Memorial Day' : '',
  ].map(normalize).filter(Boolean);
  return skus
    .filter(s => !countryCode || s.country?.code === countryCode)
    .filter(s => {
      const tags = [
        ...(s.tags || []),
        ...(s.listingTags || []),
        s.labelIds,
      ].flatMap(v => String(v || '').split(/[,，;；|\/]+/)).map(normalize).filter(Boolean);
      return tags.some(tag => keys.some(key => tag.includes(key) || key.includes(tag)));
    })
    .sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
      || (a.stockoutDate?.getTime?.() || 0) - (b.stockoutDate?.getTime?.() || 0));
}

function daysUntil(date, asOf) {
  if (!date) return null;
  const base = asOf instanceof Date && !Number.isNaN(asOf.getTime()) ? asOf : new Date();
  const a = new Date(base.getFullYear(), base.getMonth(), base.getDate()).getTime();
  const b = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  return Math.round((b - a) / 86400000);
}

function Dashboard({ setRoute, openAI, openCreatePO, dashFilters, setDashFilters }) {
  const stats = DASH_STATS;
  // /dashboard/risk-queue 返回的 listing_id → action_hint 映射
  const [actionHintMap, setActionHintMap] = React.useState({});

  React.useEffect(() => {
    if (!window.api) return;
    let cancelled = false;
    window.api.riskQueue({ limit: 30 }).then(resp => {
      if (cancelled) return;
      const m = {};
      for (const r of (resp.rows || [])) m[r.listing_id] = r.action_hint;
      setActionHintMap(m);
    }).catch(() => { /* 静默降级,client-side filter 仍可用 */ });
    return () => { cancelled = true; };
  }, []);

  const queue = SKUS.filter((s) => s.priority === 'p1' || s.priority === 'p2').slice(0, 8);

  // 从真实数据动态生成「需关注」告警
  const attentionItems = React.useMemo(() => {
    const skus = window.SKUS || [];
    const items = [];

    // 1. P1 但建议采购量为 0（有风险、无规则或缺成本）
    const p1NoSuggest = skus.filter(s => s.priority === 'p1' && !s.suggest && !s.isClearance);
    if (p1NoSuggest.length > 0) {
      items.push({
        id: 'p1-no-suggest',
        kind: 'urgent',
        title: `${p1NoSuggest.length} 个 P1 风险但建议采购为 0，需检查规则或成本配置`,
        action: '查看',
        route: { page: 'list', filter: 'p1' },
      });
    }

    // 2. 近7天已实际断货
    const recentStockout = skus.filter(s => s.stockoutRecent7);
    if (recentStockout.length > 0) {
      items.push({
        id: 'recent-stockout',
        kind: 'urgent',
        title: `${recentStockout.length} 个 SKU 近 7 天 FBA 已断货，销售受损`,
        action: '查看',
        route: { page: 'list', filter: 'stockout7' },
      });
    }

    // 3. 3天内即将断货（极度紧急）
    const criticalSoon = skus.filter(s => !s.isClearance && s.fbaSellable > 0 && s.fbaSellable <= 3);
    if (criticalSoon.length > 0) {
      items.push({
        id: 'critical-soon',
        kind: 'urgent',
        title: `${criticalSoon.length} 个 SKU FBA 库存仅剩 ≤3 天，需立即处理`,
        action: '处理',
        route: { page: 'list', filter: 'p1' },
      });
    }

    // 4. 缺少单价数据导致无法计算采购金额
    const noCost = skus.filter(s => s.suggest && (!s.cost || s.cost === 0));
    if (noCost.length > 0) {
      items.push({
        id: 'no-cost',
        kind: 'review',
        title: `${noCost.length} 个建议采购 SKU 缺少成本数据，采购金额无法计算`,
        action: '补录',
        route: { page: 'list', filter: 'suggest' },
      });
    }

    // 5. 节日临近 + 对应 SKU 库存不足
    const holidays = window.HOLIDAYS_DATA || [];
    const asOf = stats.asOf instanceof Date ? stats.asOf : new Date();
    for (const h of holidays) {
      const peakDate = h.peak_date ? new Date(h.peak_date) : null;
      if (!peakDate) continue;
      const daysLeft = Math.round((peakDate - asOf) / 86400000);
      if (daysLeft < 0 || daysLeft > 45) continue;
      const holSkus = skus.filter(s =>
        s.isHoliday && s.holidayTag && h.name && h.name.includes(s.holidayTag) &&
        s.fbaSellable < 30
      );
      if (holSkus.length > 0) {
        items.push({
          id: `holiday-${h.id}`,
          kind: 'review',
          title: `${h.name} 还有 ${daysLeft} 天，${holSkus.length} 个关联 SKU 库存不足 30 天`,
          action: '查看',
          route: { page: 'list', filter: 'all' },
        });
      }
    }

    // 6. 严重积压（可售天数 > 90 天 且库存 > 200 件）
    const overstock = skus.filter(s => s.sellable > 90 && s.totalStock > 200 && !s.isClearance);
    if (overstock.length > 0) {
      items.push({
        id: 'overstock',
        kind: 'info',
        title: `${overstock.length} 个 SKU 库存压积 >90 天，占用资金需关注`,
        action: '查看',
        route: { page: 'list', filter: 'all' },
      });
    }

    // 7. 清货中 SKU 仍被标为 P1（说明清货进展慢、断货风险高）
    const clearanceP1 = skus.filter(s => s.isClearance && s.priority === 'p1');
    if (clearanceP1.length > 0) {
      items.push({
        id: 'clearance-p1',
        kind: 'review',
        title: `${clearanceP1.length} 个清货中 SKU 仍为 P1 风险，清货进展异常`,
        action: '查看',
        route: { page: 'list', filter: 'p1' },
      });
    }

    // 8. 本地有货、有发货建议、且发货窗口 ≤14 天即将关闭
    const logDays = window.FBA_LOGISTICS_DAYS || 35;
    const now = asOf;
    const urgentShip = skus.filter(s => {
      if (!s.shipQty || s.shipQty <= 0 || s.isClearance) return false;
      if (!s.shipDate) return false;
      const daysLeft = Math.round((s.shipDate - now) / 86400000);
      return daysLeft <= 14;
    });
    if (urgentShip.length > 0) {
      const overdue = urgentShip.filter(s => s.shipDate < now).length;
      const minDays = Math.min(...urgentShip.map(s => Math.round((s.shipDate - now) / 86400000)));
      const desc = overdue > 0
        ? `其中 ${overdue} 个已逾期，需立即发货`
        : `最早窗口还剩 ${minDays} 天`;
      items.push({
        id: 'urgent-ship',
        kind: overdue > 0 ? 'urgent' : 'review',
        title: `${urgentShip.length} 个 SKU 本地有货但发货窗口即将关闭（头程 ${logDays} 天），${desc}`,
        action: '查看',
        route: { page: 'list', filter: 'all' },
      });
    }

    return items;
  }, [SKUS.length, stats.calcRunId]);
  const nextHoliday = nextHolidayFromData(stats.asOf);
  const nextHolidaySkus = holidayRelatedSkus(nextHoliday);
  const nextHolidayD = daysUntil(nextHoliday?.peakDate, stats.asOf);
  const followHoliday = (window.HOLIDAYS_DATA || [])
    .map(h => ({ ...h, peakDate: holidayDate(h) }))
    .filter(h => h.peakDate && nextHoliday && h.id !== nextHoliday.id && h.peakDate > nextHoliday.peakDate)
    .sort((a, b) => a.peakDate - b.peakDate)
    .slice(0, 2)
    .map(h => 'D-' + Math.max(0, daysUntil(h.peakDate, stats.asOf)))
    .join(' / ');

  return (
    <div style={{ padding: '24px 32px 48px', maxWidth: 1480, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header — title only, no prose subtitle (Linear style) */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div className="h1" style={{ minWidth: 0 }}><span className="marker" />分析工作台</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <DashboardFilters filters={dashFilters} setFilters={setDashFilters}/>
        </div>
      </div>

      {/* Hero — 今日工作摘要 */}
      <HeroSummary setRoute={setRoute} />

      {/* Financial summary — 1 hero (利润) + 2x2 grid (销量/收入/成本/费用).
          不对称布局：利润有 sparkline 占大头，其他 4 项紧凑。
          共用一张外卡 + 内部 hairline 分隔，视觉是"一个有结构的整体"。 */}
      <FinancialSummary/>


      {/* ── Section: 运营信号 ──────────────────────────
          Eyebrow + 库存健康 horizontal hero + 3-up signal strip.
          运营性信号一律放在这个区段；财务 KPI 不掺杂进来。 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Eyebrow */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, paddingTop: 4 }}>
          <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: '-0.005em', color: 'var(--text)' }}>
            运营信号
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
            库存健康 · 断货 · 积压 · 大促
          </div>
        </div>

        {/* Hero panel — 库存健康概览 (full width, horizontal 3-zone) */}
        <Panel title="库存健康概览" sub="基于 MSKU + 店铺组合计算">
          <div style={{ display: 'flex', alignItems: 'center', gap: 28, flexWrap: 'wrap' }}>

            {/* Donut — 中间显示总 SKU 数,百分比分母用 counts 总和,与扇区严格自洽 */}
            {(() => {
              const c = stats.counts || {};
              const total = (c.p1 || 0) + (c.p2 || 0) + (c.p3 || 0) + (c.safe || 0);
              return (
                <>
                  <div style={{ position: 'relative', width: 116, height: 116, flex: 'none' }}>
                    <Donut size={116} thickness={13}
                      values={[c.p1, c.p2, c.p3, c.safe]}
                      colors={['var(--p1)', 'var(--p2)', 'var(--p3)', 'var(--safe)']} />
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <div className="tabular" style={{ fontSize: 28, fontWeight: 540, letterSpacing: '-0.022em', lineHeight: 1 }}>{total}</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text-3)', marginTop: 3 }}>SKU 总数</div>
                    </div>
                  </div>

                  {/* Risk distribution — 4 horizontal columns */}
                  <div style={{ flex: 1, minWidth: 280, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                    {[
                      ['p1', 'P1 紧急'],
                      ['p2', 'P2 重要'],
                      ['p3', 'P3 关注'],
                      ['safe', '安全']
                    ].map(([k, l]) => {
                      const v = c[k] || 0;
                      const pct = total > 0 ? Math.round((v / total) * 100) : 0;
                return (
                  <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11.5, color: 'var(--text-2)', fontWeight: 500 }}>
                      <span className={'dot ' + k} />
                      <span>{l}</span>
                    </div>
                    <div className="tabular" style={{ fontSize: 26, fontWeight: 540, letterSpacing: '-0.022em', lineHeight: 1 }}>{v}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{pct}% 占比</div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Right vertical stats */}
                  <div style={{
                    flex: 'none', minWidth: 132,
                    borderLeft: '1px solid var(--border)',
                    paddingLeft: 24,
                    display: 'flex', flexDirection: 'column', gap: 12
                  }}>
                    <KV k="总库存" v={fmt.num(stats.totalStock) + ' 件'} />
                    <KV k="近 7 天销量" v={fmt.num(stats.totalSales7) + ' 件'} />
                    <KV k="SKU 总数" v={total + ' 个'} />
                  </div>
                </>
              );
            })()}
          </div>
        </Panel>

        {/* 3-up signal strip — 弱化版本：更小标题 / 更小数字 / 更紧 padding，
            视觉权重低于上方 hero panel，不抢戏。 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>

          {/* 近七天断货 SKU */}
          <div className="card" style={{ padding: '12px 16px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ fontSize: 11.5, color: 'var(--text-2)', fontWeight: 500, letterSpacing: '-0.005em' }}>近七天断货 SKU</span>
              <button className="btn sm ghost" style={{ height: 22, padding: '0 6px', fontSize: 11.5 }}
                onClick={() => setRoute({ page: 'list', filter: 'stockout7' })}>查看 →</button>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div className="tabular" style={{
                fontSize: 26, fontWeight: 600, letterSpacing: '-0.022em',
                lineHeight: 1, color: 'var(--p1)'
              }}>
                {stats.stockoutTrendTotal}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <Sparkline data={stats.stockoutTrend} width={140} height={22}
                  color="var(--p1)" strokeWidth={1.5} />
              </div>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
              近 7 天实际 FBA 无可用量 · 排除更早断货
            </div>
          </div>

          {/* 积压库存 */}
          <div className="card" style={{ padding: '12px 16px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ fontSize: 11.5, color: 'var(--text-2)', fontWeight: 500, letterSpacing: '-0.005em' }}>积压库存</span>
              <button className="btn sm ghost" style={{ height: 22, padding: '0 6px', fontSize: 11.5 }}
                onClick={() => setRoute({ page: 'list', filter: 'overstock' })}>查看 →</button>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <div className="tabular" style={{
                fontSize: 26, fontWeight: 600, letterSpacing: '-0.022em',
                lineHeight: 1, color: 'var(--p2)'
              }}>
                {stats.overstockCount}
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>SKU</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
              占用库存 {fmt.num(stats.overstockQty)} 件 · 库龄 &gt; 90 天
            </div>
          </div>

          {/* 下一个大促 */}
          <button
            className="card interactive"
            onClick={() => nextHoliday && setRoute({ page: 'holiday', holidayId: nextHoliday.id })}
            style={{
              appearance: 'none',
              textAlign: 'left',
              fontFamily: 'inherit',
              color: 'inherit',
              cursor: nextHoliday ? 'pointer' : 'default',
              padding: '12px 16px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ fontSize: 11.5, color: 'var(--text-2)', fontWeight: 500, letterSpacing: '-0.005em' }}>下一个大促</span>
              {nextHoliday && <span style={{ fontSize: 11, color: 'var(--accent-text)' }}>查看 SKU →</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
              <div className="tabular" style={{
                fontSize: 26, fontWeight: 600, letterSpacing: '-0.022em',
                lineHeight: 1, color: 'var(--p2)'
              }}>{nextHolidayD == null ? '—' : 'D-' + Math.max(0, nextHolidayD)}</div>
              <span style={{ fontSize: 12, fontWeight: 500 }}>{nextHoliday ? `${nextHoliday.flag || ''} ${holidayLabel(nextHoliday)}` : '暂无大促'}</span>
              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>
                {nextHoliday?.peakDate ? `· ${nextHoliday.peakDate.getMonth() + 1}/${nextHoliday.peakDate.getDate()}` : ''}
              </span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
              待备货 SKU {nextHolidaySkus.length}
              {followHoliday ? ` · 后续 ${followHoliday}` : ''}
            </div>
          </button>
        </div>
      </div>

      {/* High-risk queue + Today actions */}
      {/* Left flex / right fixed 300 — 让表格优先完整展示 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: 12 }}>
      <Panel
          title="高风险 SKU 队列"
	          sub={<span>按 P1 → P2排序 · <span style={{ color: 'var(--p1)', fontWeight: 600 }}>{stats.stockout7}</span> 个 SKU 近 7 天实际断货</span>}
          right={
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn sm primary"
              onClick={() => openCreatePO(queue.map(s => s.id))}
              disabled={queue.length === 0}>
              <Icon name="lightning" size={12} />批量生成采购计划
            </button>
          </div>
          }
          noPad>

        <div className="tbl-wrap" style={{ borderLeft: 0, borderRight: 0, borderRadius: 0, borderTop: 0, borderBottom: 0 }}>
          <table className="t">
            <thead>
              <tr>
                <th style={{ width: 28 }}><input type="checkbox" /></th>
                <th style={{ width: 56 }}>风险</th>
                <th>SKU</th>
                <th>MSKU</th>
                <th>店铺 / 国家</th>
                <th className="num">未来日销</th>
                <th className="num">总库存</th>
                <th className="num">FBA 可售</th>
                <th>预计断货</th>
                <th className="num">建议采购</th>
                <th>建议采购时间</th>
                <th className="num">建议发货量</th>
                <th>建议发货时间</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((s) => {
                const shipOverdue = s.shipDate && s.shipDate < new Date();
                return (
                <tr key={s.id} style={{ cursor: 'pointer' }}
                onClick={() => setRoute({ page: 'sku', skuId: s.id })}>
                  <td><input type="checkbox" onClick={(e) => e.stopPropagation()} /></td>
                  <td><PriorityBadge level={s.priority} compact /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 260 }}>
                      <ProductImage label={s.msku.slice(-3)} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-3)' }} className="mono">{s.sku}</div>
                      </div>
                    </div>
                  </td>
                  <td className="mono" style={{ fontSize: 12, color: 'var(--text-2)' }}>{s.msku}</td>
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
                  <td className="num tabular" style={{ fontWeight: 500, color: (s.shipQty > 0) ? 'var(--accent-text)' : 'var(--text-4)' }}>
                    {s.shipQty > 0 ? fmt.num(s.shipQty) : '—'}
                  </td>
                  <td className="tabular" style={{ color: shipOverdue ? 'var(--p1)' : 'var(--text-2)', fontWeight: shipOverdue ? 600 : 400 }}>
                    {s.shipQty > 0 ? (shipOverdue ? '尽快' : fmt.dateLong(s.shipDate)) : '—'}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="需关注" sub={attentionItems.length > 0 ? `${attentionItems.length} 条待处理` : '暂无异常'}>
        {attentionItems.length === 0 ? (
          <div style={{ padding: '20px 4px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <Icon name="check" size={18} color="var(--p3)"/>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>所有指标正常，无需处理</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {attentionItems.map((a, i) =>
              <div key={a.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '10px 0',
                borderBottom: i < attentionItems.length - 1 ? '1px solid var(--border)' : 'none',
                minWidth: 0
              }}>
                <span className={'dot ' + (a.kind === 'urgent' ? 'p1' : a.kind === 'review' ? 'p2' : 'p3')}
                  style={{ flex: 'none', marginTop: 5 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12.5, lineHeight: 1.5, color: 'var(--text-1)' }}>{a.title}</div>
                </div>
                <button className="btn sm ghost"
                  onClick={() => a.route && setRoute(a.route)}
                  style={{ color: 'var(--accent-text)', flex: 'none' }}>{a.action || '查看'} →</button>
              </div>
              )}
          </div>
        )}
      </Panel>
      </div>
    </div>);

}

function HolidaySkuPage({ holidayId, setRoute, openCreatePO }) {
  const holidays = (window.HOLIDAYS_DATA || []).map(h => ({ ...h, peakDate: holidayDate(h) }));
  const holiday = holidays.find(h => h.id === holidayId) || nextHolidayFromData(DASH_STATS.asOf) || holidays[0] || null;
  const rows = holidayRelatedSkus(holiday);
  const d = daysUntil(holiday?.peakDate, DASH_STATS.asOf);
  const totalSuggestQty = rows.reduce((sum, s) => sum + (s.suggest ? (s.suggestQty || 0) : 0), 0);
  const totalStock = rows.reduce((sum, s) => sum + (s.totalStock || 0), 0);

  return (
    <div style={{ padding: '24px 32px 48px', maxWidth: 1480, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn ghost sm" onClick={() => setRoute({ page: 'dashboard' })}>
          <Icon name="chevron-left" size={13}/>返回工作台
        </button>
      </div>

      <section className="card" style={{ padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <div className="label">下一个大促</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
            <div className="tabular" style={{ fontSize: 34, fontWeight: 620, color: 'var(--p2)', lineHeight: 1 }}>
              {d == null ? '—' : 'D-' + Math.max(0, d)}
            </div>
            <div className="h1" style={{ fontSize: 26 }}>
              {holiday ? `${holiday.flag || ''} ${holidayLabel(holiday)}` : '暂无大促'}
            </div>
            <div style={{ color: 'var(--text-3)', fontSize: 13 }}>
              {holiday?.peakDate ? fmt.dateLong(holiday.peakDate) : ''}
            </div>
          </div>
        </div>
        <KV k="关联 SKU" v={rows.length + ' 个'} />
        <KV k="建议采购量" v={fmt.num(totalSuggestQty) + ' 件'} />
        <KV k="当前总库存" v={fmt.num(totalStock) + ' 件'} />
      </section>

      <Panel
        title="大促关联 SKU"
        sub="按 SKU 标签和国家/站点关联，点击行进入 SKU 分析"
        right={
          <button className="btn sm primary" onClick={() => openCreatePO(rows.filter(s => s.suggest).map(s => s.id))} disabled={!rows.some(s => s.suggest)}>
            <Icon name="lightning" size={12}/>生成采购计划
          </button>
        }
        noPad>
        {rows.length === 0 ? (
          <div style={{ padding: 28, textAlign: 'center', color: 'var(--text-3)', fontSize: 12 }}>
            当前大促暂无关联 SKU
          </div>
        ) : (
          <div className="tbl-wrap" style={{ border: 0, borderRadius: 0 }}>
            <table className="t">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>MSKU</th>
                  <th>标签</th>
                  <th>店铺 / 国家</th>
                  <th>风险</th>
                  <th className="num">未来日销</th>
                  <th className="num">总库存</th>
                  <th className="num">FBA 可售</th>
                  <th className="num">建议采购量</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(s => (
                  <tr key={s.id} style={{ cursor: 'pointer' }} onClick={() => setRoute({ page: 'sku', skuId: s.id })}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 320 }}>
                        <ProductImage label={s.msku.slice(-3)} />
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</div>
                          <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>{s.sku}</div>
                        </div>
                      </div>
                    </td>
                    <td className="mono" style={{ color: 'var(--text-2)' }}>{s.msku}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', maxWidth: 180 }}>
                        {(s.tags || []).slice(0, 3).map(tag => (
                          <span key={tag} className="chip" style={{ height: 20, fontSize: 10.5 }}>{tag}</span>
                        ))}
                      </div>
                    </td>
                    <td>{s.country.flag} {s.store}</td>
                    <td><PriorityBadge level={s.priority}/></td>
                    <td className="num tabular">{s.futureDaily}</td>
                    <td className="num tabular">{fmt.num(s.totalStock)}</td>
                    <td className="num tabular">{s.fbaSellable} 天</td>
                    <td className="num tabular" style={{ fontWeight: 500 }}>{s.suggest ? fmt.num(s.suggestQty) : '—'}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <button className="btn sm ghost" onClick={() => setRoute({ page: 'sku', skuId: s.id })}>查看 SKU 分析</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
// Dashboard 顶部三个过滤器 — 选中后通过 setDashFilters 触发 App 层重新拉数据.
function DashboardFilters({ filters, setFilters }) {
  const f = window.FILTERS_DATA || { stores: [], countries: [], owners: [] };
  const update = (key, value) => setFilters((cur) => ({ ...cur, [key]: value }));

  return (
    <>
      <Filter label="店铺" options={f.stores}
        selectedValue={filters.store}
        onChange={(v) => update('store', v)}/>
      <Filter label="国家" options={f.countries}
        selectedValue={filters.country}
        onChange={(v) => update('country', v)}/>
      <Filter label="负责人" options={f.owners}
        selectedValue={filters.owner}
        onChange={(v) => update('owner', v)}/>
    </>
  );
}

// 真下拉过滤器 — 两种用法:
//   新 API(实装): <Filter label="店铺" options={[...]} selectedValue={...} onChange={fn}/>
//   兼容旧调用(装饰):<Filter label="时间" value="近 7 天"/> — 灰色 + tooltip 标 "尚未接入"
function Filter({ label, options, selectedValue, onChange, value }) {
  const isPlaceholder = options === undefined && value !== undefined;
  if (isPlaceholder) {
    return (
      <button className="btn" disabled
        title="该筛选项尚未接入后端,占位中"
        style={{ paddingRight: 8, opacity: 0.55, cursor: 'not-allowed' }}>
        <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>{label}</span>
        <span style={{ fontWeight: 500 }}>{value}</span>
        <Icon name="chevron-down" size={12} color="var(--text-3)" />
      </button>
    );
  }

  const safeOptions = options || [];
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);

  React.useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const selected = safeOptions.find((o) => o.value === selectedValue);
  const valueText = selected
    ? `${selected.label}${selected.count != null ? ` (${selected.count})` : ''}`
    : '全部';

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button className="btn" onClick={() => setOpen((v) => !v)} style={{ paddingRight: 8 }}>
        <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>{label}</span>
        <span style={{ fontWeight: 500 }}>{valueText}</span>
        <Icon name="chevron-down" size={12} color="var(--text-3)" />
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0,
          minWidth: 220, maxHeight: 360, overflow: 'auto',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-md)', boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          padding: 4, zIndex: 100,
        }}>
          <div
            onClick={() => { onChange?.(null); setOpen(false); }}
            style={{
              padding: '8px 10px', fontSize: 12.5, cursor: 'pointer',
              color: !selectedValue ? 'var(--accent-text)' : 'var(--text-2)',
              fontWeight: !selectedValue ? 600 : 400,
              borderRadius: 4,
              background: !selectedValue ? 'var(--accent-soft)' : 'transparent',
            }}>
            全部
          </div>
          {safeOptions.length === 0 && (
            <div style={{ padding: '8px 10px', fontSize: 11.5, color: 'var(--text-4)' }}>无数据</div>
          )}
          {safeOptions.map((o) => {
            const active = o.value === selectedValue;
            return (
              <div
                key={o.value}
                onClick={() => { onChange?.(o.value); setOpen(false); }}
                style={{
                  padding: '8px 10px', fontSize: 12.5, cursor: 'pointer',
                  color: active ? 'var(--accent-text)' : 'var(--text-2)',
                  fontWeight: active ? 600 : 400,
                  borderRadius: 4,
                  background: active ? 'var(--accent-soft)' : 'transparent',
                  display: 'flex', alignItems: 'center', gap: 10,
                }}
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--surface-hover)'; }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{o.label}</span>
                {o.count != null && (
                  <span className="tabular" style={{
                    fontSize: 11,
                    color: active ? 'var(--accent-text)' : 'var(--text-4)',
                    background: active ? 'transparent' : 'var(--surface-hover)',
                    padding: '1px 6px',
                    borderRadius: 999,
                  }}>{o.count}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
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

Object.assign(window, { Dashboard, HolidaySkuPage, Panel, Filter });
