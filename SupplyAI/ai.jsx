// AI panels — global (Dashboard) and per-SKU (detail).

// 思考折叠面板:流式期间默认展开看 AI 在想什么;思考完成后默认折叠,可手动展开。
function ReasoningPanel({ text, active }) {
  // active = true 时表示思考正在进行(还没有 content delta)
  const [open, setOpen] = React.useState(true);
  const wasActiveRef = React.useRef(active);
  // 从 active=true → false 时(思考结束)自动折叠
  React.useEffect(() => {
    if (wasActiveRef.current && !active) setOpen(false);
    wasActiveRef.current = active;
  }, [active]);
  if (!text) return null;
  return (
    <div style={{
      marginBottom: 8,
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-md)',
      background: 'var(--surface-2)',
      overflow: 'hidden',
    }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          width: '100%', appearance: 'none', border: 0,
          background: 'transparent', cursor: 'pointer',
          padding: '8px 10px',
          display: 'flex', alignItems: 'center', gap: 6,
          fontFamily: 'inherit', textAlign: 'left',
          color: 'var(--text-2)', fontSize: 11.5,
        }}
        title={open ? '收起思考过程' : '展开思考过程'}
      >
        <Icon name={active ? 'sparkles' : 'check'} size={11}
          color={active ? 'var(--accent)' : 'var(--text-3)'}/>
        <span style={{ fontWeight: 500 }}>
          {active ? '思考中…' : '已完成思考'}
        </span>
        <span style={{ color: 'var(--text-4)', fontSize: 10.5 }}>
          · {text.length} 字
        </span>
        <span style={{ flex: 1 }}/>
        <Icon name={open ? 'chevron-down' : 'chevron-right'} size={11} color="var(--text-3)"/>
      </button>
      {open && (
        <div style={{
          padding: '8px 12px 10px',
          borderTop: '1px solid var(--border)',
          fontSize: 11.5,
          color: 'var(--text-3)',
          fontFamily: 'var(--font-mono)',
          lineHeight: 1.55,
          whiteSpace: 'pre-wrap',
          maxHeight: 260,
          overflow: 'auto',
        }}>
          {text}
        </div>
      )}
    </div>
  );
}

function AIBubble({ role, children }) {
  if (role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <div style={{
          maxWidth: '85%', padding: '8px 12px',
          background: 'var(--accent-soft)', color: 'var(--accent-text)',
          border: '1px solid rgba(94,106,210,.22)',
          borderRadius: 'var(--r-md)', fontSize: 12.5,
        }}>{children}</div>
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
      <div style={{
        width: 22, height: 22, borderRadius: 5, flex: 'none',
        background: 'var(--surface-3)', color: 'var(--accent-text)',
        border: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginTop: 2,
      }}><Icon name="sparkles" size={12}/></div>
      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
    </div>
  );
}

function AIAnswer({ a, onSkuClick }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12.5 }}>
      <div style={{
        padding: '10px 12px',
        background: 'var(--surface-2)',
        borderLeft: '2px solid var(--accent)',
        borderRadius: '0 var(--r) var(--r) 0',
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,.025)',
        lineHeight: 1.55,
      }}>
        <div style={{ fontSize: 10.5, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>结论</div>
        {a.conclusion}
      </div>

      {a.factors && (
        <div>
          <div className="label" style={{ marginBottom: 6 }}>关键因子</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {a.factors.map((f, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 8px', background: 'var(--bg-sunken)', borderRadius: 4, border: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-2)' }}>{f.k}</span>
                <span className="tabular" style={{ fontWeight: 500, fontFamily: 'var(--font-mono)', fontSize: 12 }}>{f.v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {a.list && (
        <div>
          <div className="label" style={{ marginBottom: 6 }}>相关 SKU</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {a.list.map((it, i) => (
              <button key={i} onClick={() => onSkuClick && onSkuClick(it)} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
                border: '1px solid var(--border)', textAlign: 'left',
              }}>
                <PriorityBadge level={it.priority}/>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', flex: 1, minWidth: 0 }}>
                  <span className="mono" style={{ fontSize: 11.5 }}>{it.msku} · {it.store}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{it.why}</span>
                </div>
                <Icon name="arrow-right" size={12} color="var(--text-3)"/>
              </button>
            ))}
          </div>
        </div>
      )}

      {a.basis && (
        <div>
          <div className="label" style={{ marginBottom: 6 }}>数据依据</div>
          <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--text-2)', display: 'flex', flexDirection: 'column', gap: 3 }}>
            {a.basis.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
      )}

      {a.caveats && (
        <div style={{ display: 'flex', gap: 6, padding: '8px 10px', background: 'var(--p2-soft)', borderRadius: 4, alignItems: 'flex-start' }}>
          <Icon name="alert" size={12} color="var(--p2-strong)" style={{ marginTop: 2, flex: 'none' }}/>
          <div style={{ fontSize: 11.5, color: 'var(--text-2)' }}>
            <div className="label" style={{ marginBottom: 2, color: 'var(--p2-strong)' }}>限制条件</div>
            {a.caveats.join('；')}
          </div>
        </div>
      )}

      {a.actions && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', paddingTop: 4 }}>
          {a.actions.map((act, i) => (
            <button key={i} className={'btn sm ' + (i === 0 ? 'primary' : '')}>{act}</button>
          ))}
        </div>
      )}
    </div>
  );
}

function adviceNumber(v) {
  if (v == null || v === '') return null;
  const n = Number(String(v).replace(/[$,\s]/g, ''));
  return Number.isFinite(n) ? n : null;
}

function adviceFormatNum(v, digits = 0) {
  const n = adviceNumber(v);
  if (n == null) return '—';
  return n.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function adviceFormatFlexible(v) {
  const n = adviceNumber(v);
  if (n == null) return '—';
  return n.toLocaleString('en-US', {
    minimumFractionDigits: Number.isInteger(n) ? 0 : 2,
    maximumFractionDigits: 2,
  });
}

function adviceFormatMoney(v, currency = 'USD') {
  const n = adviceNumber(v);
  if (n == null) return '—';
  const symbol = currency === 'USD' ? '$' : currency + ' ';
  return symbol + n.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function adviceFormatDate(v) {
  if (!v) return '';
  if (v instanceof Date) return fmt.dateLong(v);
  return String(v).replace(/\s+/g, '');
}

function adviceSkuPool() {
  return Array.isArray(window.SKUS) ? window.SKUS : [];
}

function findSkuForAdvice(advice) {
  const list = adviceSkuPool();
  return list.find((s) => {
    if (!advice?.msku || s.msku !== advice.msku) return false;
    return !advice.country || (s.country && s.country.code === advice.country);
  }) || null;
}

function extractRiskAdvice(text, fallbackSku) {
  if (!text) return null;
  const skuLine = text.match(/高风险 SKU[:：]\s*([^（(]+)[（(]([^)）]+)[)）]/);
  const compactSkuLine = text.match(/以\s*([A-Z0-9_-]+)\s*[（(]([A-Z]{2})[)）]\s*为例/);
  const anyMsku = text.match(/\bMS\d{4,}\b/);
  const sellable = text.match(/FBA\s*(?:侧)?(?:库存)?\s*(?:可售)?\s*(?:仅能支撑|仅剩|仅)?\s*([\d.]+)\s*天/);
  const stockout = text.match(/预计(?:于)?\s*(?:([\d]{4}-\d{1,2}-\d{1,2})|(\d{1,2}\s*月\s*\d{1,2}\s*日))\s*(?:即)?(?:面临)?断货/);
  const suggestQty = text.match(/(?:建议(?:立即)?(?:采购|补货)|紧急补货|补货)\s*([\d,]+(?:\.\d+)?)\s*件/);
  const inbound = text.match(/(?:一批\s*)?([\d,]+(?:\.\d+)?)\s*件(?:的)?在途库存预计\s*([^，,。；;]+?)到货/);
  const coverage = text.match(/(?:总覆盖需求约|覆盖周期需求|覆盖)\s*([\d,]+(?:\.\d+)?)\s*件/);
  const totalStock = text.match(/(?:当前)?总库存\s*([\d,]+(?:\.\d+)?)\s*件?/);
  const transport = text.match(/(?:优先评估|推荐|建议)(空运或海空混合|空运\s*\/\s*海空混合|海\+空混合|海空混合|空运|海运|快递)(?:方案)?/);
  const skuConfirm = text.match(/^\s*SKU[:：]\s*([^\n]+)/m) || text.match(/SKU\s+([A-Z0-9_-]+(?:-[A-Z]{2})?)/);
  const qtyConfirm = text.match(/^\s*数量[:：]\s*([^\n]+)/m);
  const supplierConfirm = text.match(/^\s*供应商[:：]\s*([^\n]+)/m);
  const amountMatch = text.match(/(?:采购金额|预计采购额|金额)\s*([\d,]+(?:\.\d+)?)\s*(USD|CNY|JPY|EUR|GBP)?/i);
  const unitMatch = text.match(/(?:参考单价|采购单价|unit[_ ]?cost|unit cost|单价)\s*[:：]?\s*([\d,]+(?:\.\d+)?)\s*(USD|CNY|JPY|EUR|GBP)?/i);
  const unitMissing = /unit[_ ]?cost\s*缺失|单价缺失|成本缺失/.test(text);

  const msku = (skuLine ? skuLine[2].trim() : '') || (compactSkuLine ? compactSkuLine[1].trim() : '') || (anyMsku ? anyMsku[0] : '') || fallbackSku?.msku || '';
  const countryHint = (compactSkuLine ? compactSkuLine[2].trim() : '') || fallbackSku?.country?.code || '';
  const skuMeta = fallbackSku || findSkuForAdvice({ msku, country: countryHint }) || {};
  const country = countryHint || skuMeta.country?.code || '';

  const sellableDays = adviceNumber(sellable?.[1] ?? skuMeta.fbaSellable);
  const stockoutAt = stockout ? (stockout[1] || stockout[2]) : adviceFormatDate(skuMeta.stockoutDate);
  const coverageDemand = adviceNumber(coverage?.[1] ?? skuMeta.coverageDemand);
  const currentTotalStock = adviceNumber(totalStock?.[1] ?? skuMeta.totalStock);
  const demandGap = coverageDemand != null && currentTotalStock != null
    ? Math.max(0, coverageDemand - currentTotalStock)
    : null;
  const suggestedQtyNumber = adviceNumber(suggestQty?.[1] ?? skuMeta.suggestQty ?? (demandGap != null ? Math.ceil(demandGap) : null));
  if (sellableDays == null || !stockoutAt || suggestedQtyNumber == null) return null;

  const normalizedTransport = transport
    ? transport[1].replace(/\s*或\s*/g, ' / ').replace(/\s*\/\s*/g, ' / ').replace('海+空混合', '海空混合')
    : '空运 / 海空混合';
  const currency = skuMeta.baseCurrency || unitMatch?.[2] || amountMatch?.[2] || 'USD';
  const parsedReference = adviceNumber(amountMatch?.[1]);
  const unitCost = adviceNumber(skuMeta.cost ?? unitMatch?.[1]);
  const skuAmount = adviceNumber(skuMeta.suggestAmountBase ?? skuMeta.suggestAmount);
  let amountValue = null;
  let amountMode = 'missing';
  if (skuAmount != null) {
    amountValue = skuAmount;
    amountMode = 'system';
  } else if (unitCost != null) {
    amountValue = unitCost * suggestedQtyNumber;
    amountMode = skuMeta.cost != null ? 'system' : 'reference';
  } else if (!unitMissing && parsedReference != null) {
    amountValue = parsedReference < suggestedQtyNumber ? parsedReference * suggestedQtyNumber : parsedReference;
    amountMode = 'reference';
  }

  return {
    level: text.match(/\bP1\b|风险极高|高风险/) ? 'p1' : (skuMeta.priority || 'p1'),
    product: (skuLine ? skuLine[1].trim() : '') || skuMeta.name || '高风险 SKU',
    msku,
    country,
    store: skuMeta.store || '',
    sellerSku: skuConfirm ? skuConfirm[1].trim().replace(/[，,].*$/, '') : (skuMeta.sku || ''),
    sellableDays,
    stockoutAt: adviceFormatDate(stockoutAt),
    suggestQty: suggestedQtyNumber,
    coverageDemand,
    totalStock: currentTotalStock,
    demandGap,
    roundedGap: demandGap != null ? Math.ceil(demandGap) : suggestedQtyNumber,
    inboundQty: adviceNumber(inbound?.[1] ?? skuMeta.fbaInTransit),
    inboundAt: inbound ? inbound[2].trim() : adviceFormatDate(skuMeta.estimatedArrivalAt),
    transport: normalizedTransport,
    amountValue,
    amountMode,
    currency,
    unitCost,
    referenceAmount: parsedReference,
    amountMissing: amountValue == null || unitMissing,
    qtyConfirm: qtyConfirm ? qtyConfirm[1].trim() : '',
    supplierConfirm: supplierConfirm ? supplierConfirm[1].trim() : '',
  };
}

function AIDecisionCard({ text, sku, onAction, onCreatePlan }) {
  const advice = extractRiskAdvice(text, sku);
  if (!advice) {
    return (
      <div style={{
        fontSize: 13,
        lineHeight: 1.7,
        color: 'var(--text-1)',
      }} dangerouslySetInnerHTML={{ __html: window.renderMarkdown ? window.renderMarkdown(text) : text }}/>
    );
  }
  const metricStyle = {
    minWidth: 0,
    padding: '11px 12px',
    background: 'var(--surface-2)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r)',
  };
  const metricValueStyle = { fontSize: 22, marginTop: 4, lineHeight: 1.15, color: 'var(--text-1)' };
  const titleParts = [advice.msku, advice.country, advice.store].filter(Boolean).join(' / ');
  const cardTitle = titleParts ? `${advice.product} · ${titleParts}` : advice.product;
  const amountText = advice.amountMissing
    ? '待确认'
    : adviceFormatMoney(advice.amountValue, advice.currency);
  const amountSub = advice.amountMissing
    ? (advice.referenceAmount != null
      ? `AI 返回基准参考 ${adviceFormatMoney(advice.referenceAmount, advice.currency)}，需采购确认`
      : '缺少 unit_cost，需补充单价')
    : (advice.unitCost != null
      ? `参考单价 ${adviceFormatMoney(advice.unitCost, advice.currency)}`
      : (advice.amountMode === 'reference' ? '基准币参考值，需采购确认' : '系统计算金额'));
  const calcRows = [
    ['覆盖周期需求', advice.coverageDemand != null ? `${adviceFormatFlexible(advice.coverageDemand)} 件` : '—'],
    ['当前总库存', advice.totalStock != null ? `${adviceFormatFlexible(advice.totalStock)} 件` : '—'],
    ['需求缺口', advice.demandGap != null ? `${adviceFormatFlexible(advice.demandGap)} 件` : '—'],
    ['取整规则', `${adviceFormatFlexible(advice.demandGap ?? advice.suggestQty)} → ${adviceFormatNum(advice.roundedGap ?? advice.suggestQty)} 件`],
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(255,85,85,.28)',
        borderLeft: '3px solid var(--p1)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(255,85,85,.10), rgba(255,85,85,.035))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 9 }}>
          <PriorityBadge level={advice.level}/>
          <span className="mono" style={{ fontWeight: 650, color: 'var(--text-1)' }}>{cardTitle}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>
          预计 {advice.stockoutAt} 断货，建议立即采购 {adviceFormatNum(advice.suggestQty)} 件
        </div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>
          FBA 可售仅 {adviceFormatFlexible(advice.sellableDays)} 天，需优先压缩运输时效。
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
        <div style={metricStyle}>
          <div className="label">FBA 可售</div>
          <div className="kpi" style={metricValueStyle}>{adviceFormatFlexible(advice.sellableDays)}<span style={{ fontSize: 12, marginLeft: 3 }}>天</span></div>
        </div>
        <div style={metricStyle}>
          <div className="label">预计断货</div>
          <div className="kpi" style={metricValueStyle}>{advice.stockoutAt}</div>
        </div>
        <div style={metricStyle}>
          <div className="label">建议采购</div>
          <div className="kpi" style={metricValueStyle}>{adviceFormatNum(advice.suggestQty)}<span style={{ fontSize: 12, marginLeft: 3 }}>件</span></div>
        </div>
        <div style={metricStyle}>
          <div className="label">预计采购额</div>
          <div className="kpi" style={{ ...metricValueStyle, fontSize: advice.amountMissing ? 18 : 21, paddingTop: 3 }}>{amountText}</div>
          <div style={{ color: 'var(--text-4)', fontSize: 10.5, marginTop: 5, lineHeight: 1.35 }}>{amountSub}</div>
        </div>
      </div>

      <div style={{
        border: '1px solid var(--border)',
        borderRadius: 'var(--r)',
        background: 'var(--surface)',
        overflow: 'hidden',
      }}>
        <div style={{ padding: '9px 11px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 7 }}>
          <Icon name="columns" size={13} color="var(--text-3)"/>
          <span style={{ fontWeight: 650 }}>计算依据</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}>
          {calcRows.map(([k, v], i) => (
            <div key={k} style={{
              padding: '10px 11px',
              borderRight: i === calcRows.length - 1 ? 0 : '1px solid var(--border)',
              background: i === 3 ? 'var(--accent-soft)' : 'transparent',
            }}>
              <div className="label">{k}</div>
              <div className="tabular" style={{ marginTop: 5, fontWeight: 700, fontSize: 13.5, color: i === 3 ? 'var(--accent-text)' : 'var(--text-1)' }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        padding: '10px 12px',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r)',
        background: 'var(--bg-sunken)',
        display: 'flex',
        gap: 10,
        alignItems: 'flex-start',
      }}>
        <Icon name="truck" size={15} color="var(--text-3)" style={{ marginTop: 2, flex: 'none' }}/>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 600, marginBottom: 5 }}>原因</div>
          <ul style={{ margin: 0, paddingLeft: 17, color: 'var(--text-3)', lineHeight: 1.55, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <li>FBA 库存只能支撑 {adviceFormatFlexible(advice.sellableDays)} 天，低于 P1 风险阈值。</li>
            {advice.inboundQty != null && advice.inboundQty > 0 && (
              <li>{advice.inboundAt ? `${adviceFormatNum(advice.inboundQty)} 件在途预计 ${advice.inboundAt} 到货，` : `${adviceFormatNum(advice.inboundQty)} 件在途，`}仍不能覆盖当前断货窗口。</li>
            )}
            <li>预计断货时间早于常规到货周期，建议优先评估 {advice.transport}。</li>
            {advice.coverageDemand != null && <li>全链路覆盖需求 {adviceFormatFlexible(advice.coverageDemand)} 件，扣减库存后缺口 {advice.demandGap != null ? adviceFormatFlexible(advice.demandGap) : '—'} 件。</li>}
          </ul>
        </div>
      </div>

      <div style={{
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-md)',
        overflow: 'hidden',
        background: 'var(--surface)',
      }}>
        <div style={{ padding: '9px 11px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>采购计划确认</div>
        <div style={{ padding: '10px 11px', display: 'grid', gridTemplateColumns: '92px 1fr', gap: '7px 10px' }}>
          <div className="label">SKU</div>
          <div className="mono">{advice.sellerSku || advice.msku || '-'}</div>
          <div className="label">数量</div>
          <div>{advice.qtyConfirm || (adviceFormatNum(advice.suggestQty) + ' 件')}</div>
          <div className="label">供应商</div>
          <div style={{ color: 'var(--p2-strong)' }}>{advice.supplierConfirm || '请选择供应商'}</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className="btn primary sm"
          onClick={() => {
            if (onCreatePlan) onCreatePlan(advice);
            else if (onAction) onAction('按上述 SKU、数量和默认供应商继续生成采购计划。');
          }}>
          生成采购计划
        </button>
      </div>
    </div>
  );
}

function aiSkus() {
  if (Array.isArray(window.SKUS)) return window.SKUS;
  if (typeof SKUS !== 'undefined' && Array.isArray(SKUS)) return SKUS;
  return [];
}

function aiStats() {
  if (window.DASH_STATS) return window.DASH_STATS;
  if (typeof DASH_STATS !== 'undefined') return DASH_STATS;
  return {};
}

function aiHolidays() {
  if (Array.isArray(window.HOLIDAYS_DATA)) return window.HOLIDAYS_DATA;
  return [];
}

function aiPriorityRank(level) {
  return ({ p1: 0, p2: 1, p3: 2, safe: 3 })[String(level || '').toLowerCase()] ?? 9;
}

function aiParseDate(v) {
  if (!v) return null;
  if (v instanceof Date) return Number.isNaN(v.getTime()) ? null : v;
  const d = new Date(String(v).slice(0, 10) + 'T00:00:00');
  return Number.isNaN(d.getTime()) ? null : d;
}

function aiDaysUntil(date, asOf) {
  const d = aiParseDate(date);
  if (!d) return null;
  const base = asOf instanceof Date && !Number.isNaN(asOf.getTime()) ? asOf : new Date();
  const a = new Date(base.getFullYear(), base.getMonth(), base.getDate()).getTime();
  const b = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  return Math.round((b - a) / 86400000);
}

function aiHolidayName(h) {
  const table = {
    mothers_day: '母亲节',
    'Mothers Day': '母亲节',
    "Mother's Day": '母亲节',
    prime_day: 'Prime Day',
    black_friday: '黑五',
    cyber_monday: '网一',
    christmas: '圣诞节',
    new_year: '新年',
  };
  return h ? (table[h.name] || h.name || '大促') : '大促';
}

function aiNextHoliday() {
  const stats = aiStats();
  const asOf = stats.asOf instanceof Date ? stats.asOf : new Date(stats.asOf || Date.now());
  const todayStart = new Date(asOf.getFullYear(), asOf.getMonth(), asOf.getDate()).getTime();
  return aiHolidays()
    .map(h => ({ ...h, peakDate: aiParseDate(h.peak || h.peakDate || h.peak_date) }))
    .filter(h => h.peakDate && h.peakDate.getTime() >= todayStart)
    .sort((a, b) => a.peakDate - b.peakDate)[0] || null;
}

function aiHolidayRelatedSkus(holiday) {
  if (!holiday) return [];
  const countryCode = holiday.countryCode || holiday.country_code || null;
  return aiSkus()
    .filter(s => !countryCode || s.country?.code === countryCode)
    .filter(s => s.suggest || s.priority === 'p1' || s.priority === 'p2')
    .sort((a, b) => aiPriorityRank(a.priority) - aiPriorityRank(b.priority)
      || (a.stockoutDate?.getTime?.() || 0) - (b.stockoutDate?.getTime?.() || 0));
}

function aiPrimaryRiskSku() {
  return aiSkus()
    .filter(s => s.suggest || s.priority === 'p1')
    .sort((a, b) => aiPriorityRank(a.priority) - aiPriorityRank(b.priority)
      || (a.stockoutDate?.getTime?.() || 0) - (b.stockoutDate?.getTime?.() || 0))[0]
    || aiSkus()[0]
    || null;
}

function aiAddDays(base, days) {
  const d = base instanceof Date && !Number.isNaN(base.getTime()) ? new Date(base) : new Date();
  d.setDate(d.getDate() + Number(days || 0));
  return d;
}

function buildRiskQueueCard() {
  const stats = aiStats();
  const rows = aiSkus()
    .filter(s => ['p1', 'p2', 'p3'].includes(String(s.priority || '').toLowerCase()))
    .sort((a, b) => aiPriorityRank(a.priority) - aiPriorityRank(b.priority)
      || (a.stockoutDate?.getTime?.() || 0) - (b.stockoutDate?.getTime?.() || 0))
    .slice(0, 6);
  const suggestedRows = rows.filter(s => s.suggest);
  const totalQty = suggestedRows.reduce((sum, s) => sum + Number(s.suggestQty || 0), 0);
  return {
    type: 'risk_queue',
    severity: 'p1',
    title: '高风险 SKU 队列',
    summary: `当前 ${stats.counts?.p1 || 0} 个 P1，优先处理预计断货最近的 SKU。`,
    metrics: [
      { label: 'P1 紧急', value: stats.counts?.p1 || 0, unit: '个' },
      { label: '7 天内断货', value: stats.stockout7 || 0, unit: '个' },
      { label: '建议采购', value: totalQty || stats.suggestTotalQty || 0, unit: '件' },
      { label: '预计采购额', value: stats.suggestTotalAmountBase || null, currency: 'USD' },
    ],
    riskCounts: stats.counts || {},
    rows,
    actionItems: suggestedRows.slice(0, 50).map(s => ({ id: s.id, qty: s.suggestQty })),
  };
}

function buildPlanComparisonCard() {
  const stats = aiStats();
  const sku = aiPrimaryRiskSku();
  const qty = Number(sku?.suggestQty || 0);
  const unitCost = Number(sku?.cost || 0);
  const baseAmount = Number(sku?.suggestAmountBase || sku?.suggestAmount || (unitCost ? unitCost * qty : 0));
  const asOf = stats.asOf instanceof Date ? stats.asOf : new Date(stats.asOf || Date.now());
  const sellableDays = Number(sku?.fbaSellable || 0);
  const options = [
    { key: 'sea', name: '海运', etaDays: 35, costFactor: 1.00, risk: '高', note: '成本最低，但无法覆盖断货窗口' },
    { key: 'air', name: '空运', etaDays: 7, costFactor: 1.80, risk: sellableDays < 7 ? '中' : '低', note: '最快到货，适合首批救急' },
    { key: 'hybrid', name: '海空混合', etaDays: 10, costFactor: 1.35, risk: sellableDays < 10 ? '中' : '低', note: '成本和断货风险更均衡', recommended: true },
  ].map(o => ({
    ...o,
    arrivalDate: aiAddDays(asOf, o.etaDays),
    amount: baseAmount ? baseAmount * o.costFactor : null,
    gapDays: Math.max(0, o.etaDays - sellableDays),
  }));
  const recommended = options.find(o => o.recommended) || options[0];
  return {
    type: 'plan_comparison',
    severity: 'p2',
    title: `${sku?.msku || '高风险 SKU'} 运输方案对比`,
    sku,
    recommended,
    metrics: [
      { label: '推荐方案', value: recommended.name },
      { label: '首批到货', value: recommended.etaDays, unit: '天' },
      { label: '缺货窗口', value: adviceFormatFlexible(recommended.gapDays), unit: '天' },
      { label: '建议采购', value: qty, unit: '件' },
    ],
    evidence: [
      { label: 'FBA 可售', value: `${adviceFormatFlexible(sellableDays)} 天` },
      { label: '预计断货', value: sku?.stockoutDate ? fmt.dateLong(sku.stockoutDate) : '—' },
      { label: '当前总库存', value: `${adviceFormatFlexible(sku?.totalStock)} 件` },
      { label: '覆盖需求', value: `${adviceFormatFlexible(sku?.coverageDemand)} 件` },
    ],
    options,
    actionItems: sku ? [{ id: sku.id, qty }] : [],
  };
}

function buildHolidayReadinessCard() {
  const stats = aiStats();
  const holiday = aiNextHoliday();
  const rows = aiHolidayRelatedSkus(holiday).slice(0, 6);
  const multiplier = Number(holiday?.dm || holiday?.sales_multiplier || 1);
  const baseDemand = rows.reduce((sum, s) => sum + Number(s.coverageDemand || 0), 0);
  const promoDemand = baseDemand * multiplier;
  const totalStock = rows.reduce((sum, s) => sum + Number(s.totalStock || 0), 0);
  const gap = Math.max(0, promoDemand - totalStock);
  const suggestQty = rows.filter(s => s.suggest).reduce((sum, s) => sum + Number(s.suggestQty || 0), 0);
  const d = aiDaysUntil(holiday?.peakDate, stats.asOf);
  return {
    type: 'holiday_readiness',
    severity: d != null && d <= 14 ? 'p2' : 'p3',
    title: holiday ? `${holiday.flag || ''} ${aiHolidayName(holiday)}` : '大促备货',
    summary: holiday
      ? `${aiHolidayName(holiday)} 距离 ${d == null ? '—' : `${Math.max(0, d)} 天`}，当前关联 ${rows.length} 个风险 SKU。`
      : '当前暂无已配置的大促节点。',
    holiday,
    metrics: [
      { label: '倒计时', value: d == null ? '—' : Math.max(0, d), unit: d == null ? '' : '天' },
      { label: '关联 SKU', value: rows.length, unit: '个' },
      { label: '销量系数', value: multiplier.toFixed(2).replace(/\.00$/, ''), prefix: '×' },
      { label: '建议采购', value: suggestQty || Math.ceil(gap), unit: '件' },
    ],
    evidence: [
      { label: '活动覆盖需求', value: `${adviceFormatFlexible(promoDemand)} 件` },
      { label: '当前总库存', value: `${adviceFormatFlexible(totalStock)} 件` },
      { label: '活动缺口', value: `${adviceFormatFlexible(gap)} 件` },
      { label: '峰值日期', value: holiday?.peakDate ? fmt.dateLong(holiday.peakDate) : '—' },
    ],
    rows,
    actionItems: rows.filter(s => s.suggest).slice(0, 50).map(s => ({ id: s.id, qty: s.suggestQty })),
  };
}

function buildRuleImpactCard() {
  const sku = aiPrimaryRiskSku();
  const rows = aiSkus()
    .filter(s => s.suggest || s.priority === 'p1' || s.priority === 'p2')
    .sort((a, b) => aiPriorityRank(a.priority) - aiPriorityRank(b.priority)
      || (a.stockoutDate?.getTime?.() || 0) - (b.stockoutDate?.getTime?.() || 0))
    .slice(0, 5)
    .map(s => {
      const currentSafeDays = Number(s.safeDays || 14);
      const targetSafeDays = 21;
      const lead = Number(s.purchaseLeadTime || 0);
      const daily = Number(s.futureDaily || 0);
      const totalStock = Number(s.totalStock || 0);
      const nextCoverageDemand = daily * (lead + targetSafeDays);
      const nextSuggestQty = Math.ceil(Math.max(0, nextCoverageDemand - totalStock));
      const currentSuggestQty = Number(s.suggestQty || 0);
      return {
        ...s,
        currentSafeDays,
        targetSafeDays,
        nextCoverageDemand,
        nextSuggestQty,
        qtyDelta: nextSuggestQty - currentSuggestQty,
      };
    });
  const target = rows.find(s => s.id === sku?.id) || rows[0] || null;
  const totalDelta = rows.reduce((sum, s) => sum + Math.max(0, s.qtyDelta), 0);
  return {
    type: 'rule_impact',
    severity: 'p3',
    title: '安全天数 21 天规则模拟',
    sku: target,
    metrics: [
      { label: '安全天数', value: `${target?.currentSafeDays ?? 14} → 21`, unit: '天' },
      { label: '采购量变化', value: totalDelta >= 0 ? `+${adviceFormatNum(totalDelta)}` : adviceFormatNum(totalDelta), unit: '件' },
      { label: '影响 SKU', value: rows.length, unit: '个' },
      { label: '主 SKU 新采购', value: target?.nextSuggestQty || 0, unit: '件' },
    ],
    evidence: [
      { label: '主 SKU', value: target?.msku || '—' },
      { label: '未来日销', value: `${adviceFormatFlexible(target?.futureDaily)} 件/天` },
      { label: '覆盖需求', value: `${adviceFormatFlexible(target?.coverageDemand)} → ${adviceFormatFlexible(target?.nextCoverageDemand)} 件` },
      { label: '风险等级', value: `${String(target?.priority || '').toUpperCase()} · 需复算确认` },
    ],
    rows,
  };
}

function MetricGrid({ items }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
      {items.map((m, i) => {
        const rawValue = m.currency ? adviceFormatMoney(m.value, m.currency) : `${m.prefix || ''}${m.value ?? '—'}`;
        return (
          <div key={i} style={{
            minWidth: 0,
            padding: '11px 12px',
            background: 'var(--surface-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
          }}>
            <div className="label">{m.label}</div>
            <div className="kpi" style={{ fontSize: 22, marginTop: 4, lineHeight: 1.15, color: 'var(--text-1)' }}>
              {rawValue}<span style={{ fontSize: 12, marginLeft: m.unit ? 3 : 0 }}>{m.unit || ''}</span>
            </div>
            {m.note && <div style={{ color: 'var(--text-4)', fontSize: 10.5, marginTop: 5 }}>{m.note}</div>}
          </div>
        );
      })}
    </div>
  );
}

function EvidenceGrid({ items }) {
  if (!items?.length) return null;
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', background: 'var(--surface)', overflow: 'hidden' }}>
      <div style={{ padding: '9px 11px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 7 }}>
        <Icon name="columns" size={13} color="var(--text-3)"/>
        <span style={{ fontWeight: 650 }}>计算依据</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(4, items.length)}, minmax(0, 1fr))` }}>
        {items.map((it, i) => (
          <div key={it.label} style={{
            padding: '10px 11px',
            borderRight: i === items.length - 1 ? 0 : '1px solid var(--border)',
            background: i === items.length - 1 ? 'var(--accent-soft)' : 'transparent',
          }}>
            <div className="label">{it.label}</div>
            <div className="tabular" style={{ marginTop: 5, fontWeight: 700, fontSize: 13.5, color: i === items.length - 1 ? 'var(--accent-text)' : 'var(--text-1)' }}>{it.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SkuMiniRows({ rows, onSkuClick }) {
  if (!rows?.length) return (
    <div style={{ padding: 16, border: '1px solid var(--border)', borderRadius: 'var(--r)', color: 'var(--text-3)', fontSize: 12 }}>
      暂无关联 SKU
    </div>
  );
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden', background: 'var(--surface)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 74px 82px 86px', padding: '8px 10px', borderBottom: '1px solid var(--border)', color: 'var(--text-3)', fontSize: 11 }}>
        <div>SKU</div>
        <div>风险</div>
        <div style={{ textAlign: 'right' }}>FBA 可售</div>
        <div style={{ textAlign: 'right' }}>建议采购</div>
      </div>
      {rows.map((s) => (
        <button key={s.id} onClick={() => onSkuClick && onSkuClick(s)} style={{
          width: '100%',
          border: 0,
          borderBottom: '1px solid var(--border)',
          background: 'transparent',
          color: 'inherit',
          cursor: 'pointer',
          display: 'grid',
          gridTemplateColumns: '1fr 74px 82px 86px',
          alignItems: 'center',
          padding: '9px 10px',
          textAlign: 'left',
          fontFamily: 'inherit',
        }}>
          <div style={{ minWidth: 0 }}>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-1)' }}>{s.msku}</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name || s.sku}</div>
          </div>
          <PriorityBadge level={s.priority} compact/>
          <div className="tabular" style={{ textAlign: 'right', fontSize: 12 }}>{adviceFormatFlexible(s.fbaSellable)} 天</div>
          <div className="tabular" style={{ textAlign: 'right', fontSize: 12, fontWeight: 650 }}>{s.suggest ? adviceFormatNum(s.suggestQty) : '—'}</div>
        </button>
      ))}
    </div>
  );
}

function RiskQueueCard({ card, setRoute, openCreatePO, onClose }) {
  const riskItems = [
    ['P1', card.riskCounts?.p1 || 0, 'var(--p1)'],
    ['P2', card.riskCounts?.p2 || 0, 'var(--p2)'],
    ['P3', card.riskCounts?.p3 || 0, 'var(--p3)'],
    ['安全', card.riskCounts?.safe || 0, 'var(--text-3)'],
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(255,85,85,.28)',
        borderLeft: '3px solid var(--p1)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(255,85,85,.10), rgba(255,85,85,.035))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <PriorityBadge level="p1"/>
          <span style={{ fontWeight: 700 }}>{card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>先处理预计断货最近的 P1 / P2 SKU</div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>{card.summary}</div>
      </div>
      <MetricGrid items={card.metrics}/>
      <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', background: 'var(--surface)', padding: '10px 12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 9 }}>
          <div style={{ fontWeight: 650 }}>风险分布</div>
          <div style={{ color: 'var(--text-4)', fontSize: 11 }}>按当前计算批次统计</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
          {riskItems.map(([label, value, color]) => (
            <div key={label} style={{ padding: '8px 9px', border: '1px solid var(--border)', borderRadius: 6, background: 'var(--surface-2)' }}>
              <div style={{ color, fontSize: 11, fontWeight: 650 }}>{label}</div>
              <div className="tabular" style={{ marginTop: 3, fontSize: 18, fontWeight: 750 }}>{value}<span style={{ fontSize: 11, color: 'var(--text-3)', marginLeft: 3 }}>个</span></div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ fontWeight: 650 }}>Top 风险 SKU</div>
        <div style={{ color: 'var(--text-4)', fontSize: 11 }}>按风险等级和断货时间排序</div>
      </div>
      <SkuMiniRows rows={card.rows} onSkuClick={(s) => setRoute && setRoute({ page: 'sku', skuId: s.id })}/>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn sm" onClick={() => {
          if (setRoute) setRoute({ page: 'list', filter: 'p1' });
          if (onClose) onClose();
        }}>查看高风险队列</button>
        <button className="btn primary sm" onClick={() => {
          if (openCreatePO) openCreatePO(card.actionItems);
          if (onClose) onClose();
        }} disabled={!card.actionItems?.length}>批量生成采购计划</button>
      </div>
    </div>
  );
}

function HolidayReadinessCard({ card, setRoute, openCreatePO, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(245,158,11,.30)',
        borderLeft: '3px solid var(--p2)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(245,158,11,.12), rgba(245,158,11,.035))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="calendar" size={14} color="var(--p2-strong)"/>
          <span style={{ fontWeight: 700 }}>大促备货 · {card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>{card.summary}</div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>优先检查关联 SKU 的活动缺口与采购计划。</div>
      </div>
      <MetricGrid items={card.metrics}/>
      <EvidenceGrid items={card.evidence}/>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ fontWeight: 650 }}>关联风险 SKU</div>
        <div style={{ color: 'var(--text-4)', fontSize: 11 }}>按国家/站点和当前风险关联</div>
      </div>
      <SkuMiniRows rows={card.rows} onSkuClick={(s) => setRoute && setRoute({ page: 'sku', skuId: s.id })}/>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn sm" onClick={() => {
          if (setRoute) setRoute({ page: 'holiday', holidayId: card.holiday?.id });
          if (onClose) onClose();
        }}>查看关联 SKU</button>
        <button className="btn primary sm" onClick={() => {
          if (openCreatePO) openCreatePO(card.actionItems);
          if (onClose) onClose();
        }} disabled={!card.actionItems?.length}>生成采购计划</button>
      </div>
    </div>
  );
}

function PlanComparisonCard({ card, setRoute, openCreatePO, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(94,106,210,.28)',
        borderLeft: '3px solid var(--accent)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(94,106,210,.12), rgba(94,106,210,.035))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="truck" size={14} color="var(--accent)"/>
          <span style={{ fontWeight: 700 }}>方案对比 · {card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>
          推荐 {card.recommended?.name}，兼顾断货窗口和物流成本。
        </div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>
          比较海运、空运、海空混合的到货时间、风险和成本。
        </div>
      </div>
      <MetricGrid items={card.metrics}/>
      <EvidenceGrid items={card.evidence}/>
      <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden', background: 'var(--surface)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 72px 82px 82px 1.2fr', padding: '8px 10px', borderBottom: '1px solid var(--border)', color: 'var(--text-3)', fontSize: 11 }}>
          <div>运输方案</div>
          <div>到货</div>
          <div>缺货窗口</div>
          <div>风险</div>
          <div>判断</div>
        </div>
        {card.options.map((o) => (
          <div key={o.key} style={{
            display: 'grid',
            gridTemplateColumns: '1fr 72px 82px 82px 1.2fr',
            alignItems: 'center',
            padding: '10px',
            borderBottom: '1px solid var(--border)',
            background: o.recommended ? 'var(--accent-soft)' : 'transparent',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontWeight: 650 }}>
              {o.name}
              {o.recommended && <span style={{ fontSize: 10.5, color: 'var(--accent-text)', border: '1px solid rgba(94,106,210,.25)', borderRadius: 999, padding: '1px 6px' }}>推荐</span>}
            </div>
            <div className="tabular">{o.etaDays} 天</div>
            <div className="tabular">{adviceFormatFlexible(o.gapDays)} 天</div>
            <div style={{ color: o.risk === '高' ? 'var(--p1)' : o.risk === '中' ? 'var(--p2)' : 'var(--p3)' }}>{o.risk}</div>
            <div style={{ color: 'var(--text-3)', fontSize: 11.5 }}>{o.note}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn sm" onClick={() => {
          if (setRoute && card.sku) setRoute({ page: 'sku', skuId: card.sku.id });
          if (onClose) onClose();
        }}>查看 SKU 分析</button>
        <button className="btn primary sm" onClick={() => {
          if (openCreatePO) openCreatePO(card.actionItems);
          if (onClose) onClose();
        }} disabled={!card.actionItems?.length}>采用推荐方案生成采购计划</button>
      </div>
    </div>
  );
}

function RuleImpactCard({ card, setRoute, openRules, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(34,197,94,.24)',
        borderLeft: '3px solid var(--p3)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(34,197,94,.10), rgba(34,197,94,.030))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="settings" size={14} color="var(--p3-strong)"/>
          <span style={{ fontWeight: 700 }}>规则模拟 · {card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>
          安全天数提高到 21 天后，建议采购量将增加。
        </div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>
          该模拟只展示影响预估，保存规则前仍需要重新计算确认。
        </div>
      </div>
      <MetricGrid items={card.metrics}/>
      <EvidenceGrid items={card.evidence}/>
      <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden', background: 'var(--surface)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 82px 92px 92px', padding: '8px 10px', borderBottom: '1px solid var(--border)', color: 'var(--text-3)', fontSize: 11 }}>
          <div>SKU</div>
          <div>安全天数</div>
          <div style={{ textAlign: 'right' }}>调整后采购</div>
          <div style={{ textAlign: 'right' }}>变化</div>
        </div>
        {card.rows.map((s) => (
          <button key={s.id} onClick={() => setRoute && setRoute({ page: 'sku', skuId: s.id })} style={{
            width: '100%',
            display: 'grid',
            gridTemplateColumns: '1fr 82px 92px 92px',
            alignItems: 'center',
            padding: '9px 10px',
            border: 0,
            borderBottom: '1px solid var(--border)',
            background: 'transparent',
            color: 'inherit',
            cursor: 'pointer',
            textAlign: 'left',
            fontFamily: 'inherit',
          }}>
            <div style={{ minWidth: 0 }}>
              <div className="mono" style={{ fontSize: 12 }}>{s.msku}</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name || s.sku}</div>
            </div>
            <div className="tabular">{s.currentSafeDays} → {s.targetSafeDays}</div>
            <div className="tabular" style={{ textAlign: 'right', fontWeight: 650 }}>{adviceFormatNum(s.nextSuggestQty)}</div>
            <div className="tabular" style={{ textAlign: 'right', color: s.qtyDelta > 0 ? 'var(--p2)' : 'var(--text-3)' }}>{s.qtyDelta >= 0 ? '+' : ''}{adviceFormatNum(s.qtyDelta)}</div>
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn sm" onClick={() => {
          if (setRoute) setRoute({ page: 'list', filter: 'suggest' });
          if (onClose) onClose();
        }}>查看影响 SKU</button>
        <button className="btn primary sm" onClick={() => {
          if (openRules) openRules({ sku: card.sku, mode: 'forecast' });
          if (onClose) onClose();
        }}>打开规则设置</button>
      </div>
    </div>
  );
}

function StructuredAICard({ card, text, sku, setRoute, openCreatePO, openRules, onClose, onAction, onCreatePlan }) {
  const built = card?.type === 'risk_queue' && !card.rows ? buildRiskQueueCard()
    : card?.type === 'holiday_readiness' && !card.rows ? buildHolidayReadinessCard()
    : card?.type === 'plan_comparison' && !card.options ? buildPlanComparisonCard()
    : card?.type === 'rule_impact' && !card.rows ? buildRuleImpactCard()
    : card;
  if (built?.type === 'risk_queue') return <RiskQueueCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'holiday_readiness') return <HolidayReadinessCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'plan_comparison') return <PlanComparisonCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'rule_impact') return <RuleImpactCard card={built} setRoute={setRoute} openRules={openRules} onClose={onClose}/>;
  return <AIDecisionCard text={text} sku={sku} onAction={onAction} onCreatePlan={onCreatePlan}/>;
}

function AIPanelHeader({ title, sub, onClose, onToggleWide, wide }) {
  return (
    <div style={{
      padding: '16px 16px 14px',
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: 11,
      background: 'linear-gradient(180deg, rgba(94,106,210,.10), var(--surface) 72%)',
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 7,
        background: 'var(--accent-soft)', color: 'var(--accent-text)',
        border: '1px solid rgba(94,106,210,.22)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none',
      }}><Icon name="bot" size={14}/></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="h3" style={{ fontSize: 15 }}>{title}</div>
        {sub && <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 3, lineHeight: 1.45 }}>{sub}</div>}
      </div>
      {onToggleWide && (
        <button className="btn ghost icon sm" onClick={onToggleWide} title={wide ? '收回宽屏' : '宽屏模式'}>
          <Icon name={wide ? 'arrow-right' : 'arrow-left'} size={14}/>
        </button>
      )}
      <button className="btn ghost icon sm" onClick={onClose}><Icon name="x" size={14}/></button>
    </div>
  );
}

function AIInput({ placeholder = '问我：今天哪些 SKU 必须补货？', onSend, disabled }) {
  const [v, setV] = React.useState('');
  const submit = () => {
    const text = v.trim();
    if (!text || disabled) return;
    onSend && onSend(text);
    setV('');
  };
  return (
    <div style={{ padding: 14, borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 6,
        background: 'var(--surface)',
        border: '1px solid var(--border-input)',
        borderRadius: 10,
        padding: 9,
      }}>
        <textarea
          value={v}
          onChange={e => setV(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); } }}
          placeholder={placeholder}
          rows={2}
          disabled={disabled}
          style={{
            flex: 1, border: 0, outline: 'none', resize: 'none',
            background: 'transparent', color: 'inherit',
            fontFamily: 'inherit', fontSize: 12.5, lineHeight: 1.5,
          }}/>
        <button className="btn icon" disabled={!v || disabled} onClick={submit}
          style={{ background: v ? 'var(--accent)' : '', color: v ? '#fff' : '', borderColor: v ? 'var(--accent)' : '' }}>
          <Icon name="send" size={13}/>
        </button>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, fontSize: 11, color: 'var(--text-4)' }}>
        <Icon name="info" size={11}/>
        <span>基于当前库存、销量、在途和补货规则生成建议，关键动作会要求二次确认。</span>
      </div>
    </div>
  );
}

// 工具名 → 中文标签(用于流式 thinking 占位)
const TOOL_LABEL = {
  query_skus: '查询 SKU 列表',
  get_sku_detail: '查询 SKU 详情',
  query_risk_queue: '查询风险队列',
  generate_purchase_draft: '生成采购计划',
  query_dashboard_snapshot: '查询工作台快照',
  query_finance: '查询财务',
  query_holidays: '查询节假日',
};

// ── Global AI ───────────────────────────────
// 7 个 AI 场景 — 按飞书产品文档需求。
// 每个场景对应一类决策:单 SKU/优先级/活动/风险/方案/新品/管理层。
const GLOBAL_AI_QUESTIONS = [
  { tag: '高风险队列', q: '本周哪些 SKU 必须补货?按紧急度排序并说明原因。' },
  { tag: '大促备货', q: '下一个大促要为哪些 SKU 备货?缺口和建议采购量是多少?' },
  { tag: '单 SKU 补货', q: '挑一个高风险 SKU,告诉我还能卖多久,要不要补、补多少?' },
  { tag: '方案对比', q: '只海运 vs 海+空混合,成本和断货风险分别是什么?' },
  { tag: '规则模拟', q: '安全天数改成 21 天会怎样?采购量和风险等级有什么变化?' },
];

function localCardForQuestion(text) {
  if (/挑一个|单\s*SKU|单品|一个高风险/.test(text)) return null;
  if (/方案对比|海运|空运|海空|海\+空|混合/.test(text)) {
    return {
      text: '已对比海运、空运、海空混合的到货时间、缺货风险和成本影响。',
      card: { type: 'plan_comparison' },
    };
  }
  if (/规则模拟|安全天数|改成|调整|规则影响|保存规则/.test(text)) {
    return {
      text: '已模拟安全天数调整后的采购量、覆盖需求和影响 SKU。',
      card: { type: 'rule_impact' },
    };
  }
  if (/高风险|必须补货|紧急度|风险队列|优先级/.test(text)) {
    return {
      text: '已按风险等级、预计断货时间和建议采购量整理高风险队列。',
      card: { type: 'risk_queue' },
    };
  }
  if (/大促|节日|Prime|活动备货|母亲节|黑五|圣诞/.test(text)) {
    return {
      text: '已按下一个大促节点关联风险 SKU，并测算活动备货缺口。',
      card: { type: 'holiday_readiness' },
    };
  }
  return null;
}

function GlobalAIWorkbench({ onAsk, disabled }) {
  const suggested = (window.SKUS || []).filter((s) => s.suggest);
  const quickStats = [
    { label: '需立即采购', value: DASH_STATS.suggestSkuCount || suggested.length || 0, suffix: '个 SKU', tone: 'var(--p1)' },
    { label: '7 天内断货', value: DASH_STATS.stockout7 || 0, suffix: '个', tone: 'var(--p1)' },
    { label: '涉及店铺', value: new Set(suggested.map((s) => s.store)).size || 0, suffix: '个', tone: 'var(--accent)' },
  ];
  return (
    <div style={{
      padding: 13,
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-md)',
      background: 'linear-gradient(180deg, rgba(94,106,210,.10), rgba(94,106,210,.035))',
      marginBottom: 14,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', marginBottom: 11 }}>
        <div>
          <div style={{ fontWeight: 650, fontSize: 14 }}>今天先处理什么？</div>
          <div style={{ color: 'var(--text-3)', fontSize: 11.5, marginTop: 3 }}>我会把库存风险翻译成可执行的采购动作。</div>
        </div>
        <button className="btn sm primary" onClick={() => onAsk(GLOBAL_AI_QUESTIONS[0].q)} disabled={disabled}>
          看补货优先级
        </button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8 }}>
        {quickStats.map((s, i) => (
          <div key={i} style={{ padding: '9px 10px', border: '1px solid var(--border)', borderRadius: 'var(--r)', background: 'var(--surface)' }}>
            <div className="label">{s.label}</div>
            <div style={{ marginTop: 4, fontWeight: 700, fontSize: 20, color: s.tone }}>
              {s.value}<span style={{ fontSize: 11, color: 'var(--text-3)', marginLeft: 4 }}>{s.suffix}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GlobalAIPanel({ onClose, setRoute, openCreatePO, openRules, dashFilters, history, setHistory, wide, onToggleWide }) {
  const [thinking, setThinking] = React.useState(false);
  const [toolStatus, setToolStatus] = React.useState(''); // 正在调用的 tool 名
  const sendToBackend = async (text) => {
    setHistory(h => [...h, { role: 'user', text }]);
    const localCard = localCardForQuestion(text);
    if (localCard) {
      setHistory(h => [...h, { role: 'ai', ...localCard }]);
      return;
    }
    setThinking(true);
    setToolStatus('');
    try {
      const msgs = [];
      for (const m of history) {
        if (m.role === 'user' && m.text) msgs.push({ role: 'user', content: m.text });
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: m.text });
      }
      msgs.push({ role: 'user', content: text });
      const context = { current_page: 'dashboard' };
      if (dashFilters) {
        const filters = {};
        if (dashFilters.store) filters.mall_id = parseInt(dashFilters.store, 10);
        if (dashFilters.country) filters.country_code = dashFilters.country;
        if (dashFilters.owner) filters.owner = dashFilters.owner;
        if (Object.keys(filters).length) context.filters = filters;
      }
      // 流式:先推一个空 ai bubble,每 delta 增量追加;reasoning 走独立字段
      setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true }]);
      const append = (key) => (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, [key]: (last[key] || '') + delta };
          }
          return next;
        });
      };
      const appendDelta = append('text');
      const appendReasoning = append('reasoning');
      await window.api.aiChatStream(msgs, context, (ev) => {
        if (ev.type === 'delta') appendDelta(ev.text || '');
        else if (ev.type === 'reasoning_delta') appendReasoning(ev.text || '');
        else if (ev.type === 'tool_start') setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        else if (ev.type === 'tool_end') setToolStatus('');
        else if (ev.type === 'error') appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            if (last && last.streaming) next[next.length - 1] = { ...last, streaming: false };
            return next;
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ 调用失败:' + err.message }]);
    } finally {
      setThinking(false);
      setToolStatus('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <AIPanelHeader
        title="SupplyAI 决策助手"
        sub="库存风险、补货优先级、活动备货和采购计划确认"
        onClose={onClose}
        onToggleWide={onToggleWide}
        wide={wide}
      />

      <div style={{ flex: 1, overflow: 'auto', padding: 14, background: 'var(--bg)' }}>
        <GlobalAIWorkbench onAsk={sendToBackend} disabled={thinking}/>
        {history.map((m, i) => (
          m.role === 'user'
            ? <AIBubble key={i} role="user">{m.text}</AIBubble>
            : (
              <AIBubble key={i} role="ai">
                {m.q && <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{m.q}</div>}
                {m.reasoning && (
                  <ReasoningPanel
                    text={m.reasoning}
                    active={!!m.streaming && !m.text}
                  />
                )}
                {m.text && (
                  <StructuredAICard
                    card={m.card}
                    text={m.text}
                    setRoute={setRoute}
                    openCreatePO={openCreatePO}
                    openRules={openRules}
                    onClose={onClose}
                    onAction={sendToBackend}
                    onCreatePlan={(advice) => {
                      const target = (window.SKUS || []).find((s) => {
                        if (!advice.msku || s.msku !== advice.msku) return false;
                        return !advice.country || (s.country && s.country.code === advice.country);
                      });
                      if (openCreatePO) openCreatePO(target ? [{ id: target.id, qty: advice.suggestQty, supplier: advice.supplierConfirm }] : []);
                      onClose && onClose();
                    }}
                  />
                )}
              </AIBubble>
            )
        ))}
        {thinking && (() => {
          const last = history[history.length - 1];
          const hasGrowing = last && last.role === 'ai' && (last.text || last.reasoning);
          // 已经在 stream(content 或 reasoning)时不再叠 placeholder
          if (hasGrowing && !toolStatus) return null;
          return (
            <AIBubble role="ai">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-3)', fontSize: 12 }}>
                <span className="pulse">●</span>
                正在分析库存、销量和补货规则…
              </div>
            </AIBubble>
          );
        })()}

        <div style={{ marginTop: 16 }}>
          <div className="label" style={{ marginBottom: 8 }}>常用决策</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: 8 }}>
            {GLOBAL_AI_QUESTIONS.map((item, i) => (
              <button key={i} onClick={() => sendToBackend(item.q)} disabled={thinking} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '10px 11px',
                textAlign: 'left', border: '1px solid var(--border)',
                background: 'var(--surface-2)',
                flexDirection: 'column', alignItems: 'flex-start', gap: 4,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                  <Icon name="lightning" size={11} color="var(--accent)"/>
                  <span style={{
                    fontSize: 10.5, fontWeight: 500,
                    color: 'var(--accent-text)',
                  }}>{item.tag}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.45, whiteSpace: 'normal', textAlign: 'left' }}>{item.q}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <AIInput onSend={sendToBackend} disabled={thinking}/>
    </div>
  );
}

// ── SKU AI ────────────────────────────────
const skuQuestions = (sku) => [
  `为什么 ${sku.msku} 是 ${(sku.priority || '').toUpperCase()}?`,
  '为什么建议这个采购数量?',
  '安全天数改成 21 会怎样?',
  '哪些因素影响最大?',
];

function SKUAIPanel({ sku, onClose, mode, history, setHistory, wide, onToggleWide, openCreatePO, openRules }) {
  const [thinking, setThinking] = React.useState(false);
  const [toolStatus, setToolStatus] = React.useState('');
  // 挂载后调 /ai/explain — 仅在该 SKU 历史为空时(首次打开),已有历史就跳过
  React.useEffect(() => {
    if (!window.api || !sku.listingId) return;
    if (history && history.length > 0) return; // 已有对话,不重复 explain
    let cancelled = false;
    setThinking(true);
    // 先 push 一个空 AI bubble,流式 delta 累积进它
    setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', q: 'AI 解释', streaming: true }]);
    const appendKey = (key) => (delta) => {
      if (cancelled) return;
      setHistory(h => {
        const next = h.slice();
        const last = next[next.length - 1];
        if (last && last.role === 'ai') {
          next[next.length - 1] = { ...last, [key]: (last[key] || '') + delta };
        }
        return next;
      });
    };
    const append = appendKey('text');
    const appendReasoning = appendKey('reasoning');
    window.api.aiExplainStream(sku.listingId, (ev) => {
      if (cancelled) return;
      if (ev.type === 'delta') append(ev.text || '');
      else if (ev.type === 'reasoning_delta') appendReasoning(ev.text || '');
      else if (ev.type === 'error') append('\n⚠️ ' + (ev.message || '获取失败'));
      else if (ev.type === 'done') {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.streaming) next[next.length - 1] = { ...last, streaming: false };
          return next;
        });
      }
    }).catch(err => {
      if (cancelled) return;
      append('\n⚠️ 解释获取失败:' + err.message);
    }).finally(() => { if (!cancelled) setThinking(false); });
    return () => { cancelled = true; };
  }, [sku.listingId]);

  const sendToBackend = async (text) => {
    setHistory(h => [...h, { role: 'user', text }]);
    setThinking(true);
    setToolStatus('');
    try {
      const msgs = [];
      for (const m of history) {
        if (m.role === 'user' && m.text) msgs.push({ role: 'user', content: m.text });
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: m.text });
      }
      msgs.push({ role: 'user', content: text });
      const context = {
        current_page: 'sku',
        sku: {
          msku: sku.msku,
          listing_id: sku.listingId,
          mall_id: sku.mallId,
          store_name: sku.store,
          country_code: sku.country?.code,
          priority: sku.priority,
        },
      };
      setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true }]);
      const append = (key) => (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, [key]: (last[key] || '') + delta };
          }
          return next;
        });
      };
      const appendDelta = append('text');
      const appendReasoning = append('reasoning');
      await window.api.aiChatStream(msgs, context, (ev) => {
        if (ev.type === 'delta') appendDelta(ev.text || '');
        else if (ev.type === 'reasoning_delta') appendReasoning(ev.text || '');
        else if (ev.type === 'tool_start') setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        else if (ev.type === 'tool_end') setToolStatus('');
        else if (ev.type === 'error') appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            if (last && last.streaming) next[next.length - 1] = { ...last, streaming: false };
            return next;
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ 调用失败:' + err.message }]);
    } finally {
      setThinking(false);
      setToolStatus('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <AIPanelHeader
        title="SKU 分析助手"
        sub={sku.msku + ' · ' + sku.store + ' · 快照 ' + fmt.time(DASH_STATS.asOf)}
        onClose={onClose}
        onToggleWide={onToggleWide}
        wide={wide}
      />

      <div style={{ flex: 1, overflow: 'auto', padding: 14, background: 'linear-gradient(180deg, rgba(255,255,255,.018), transparent 140px)' }}>
        {/* SKU summary chip */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: 10, marginBottom: 14,
          background: 'var(--surface)', borderRadius: 'var(--r)',
          border: '1px solid var(--border)',
        }}>
          <ProductImage label={sku.msku.slice(-3)} size={36}/>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{sku.name}</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>FBA 可售 {sku.fbaSellable}d · 建议采购 {sku.suggestQty}</div>
          </div>
          <PriorityBadge level={sku.priority}/>
        </div>

        {history.map((m, i) => (
          m.role === 'user'
            ? <AIBubble key={i} role="user">{m.text}</AIBubble>
            : (
              <AIBubble key={i} role="ai">
                {m.q && <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{m.q}</div>}
                {m.reasoning && (
                  <ReasoningPanel
                    text={m.reasoning}
                    active={!!m.streaming && !m.text}
                  />
                )}
                {m.text && (
                  <StructuredAICard
                    card={m.card}
                    text={m.text}
                    sku={sku}
                    openCreatePO={openCreatePO}
                    openRules={openRules}
                    onClose={onClose}
                    onAction={sendToBackend}
                    onCreatePlan={(advice) => {
                      if (openCreatePO) openCreatePO([{ id: sku.id, qty: advice.suggestQty, supplier: advice.supplierConfirm }]);
                      onClose && onClose();
                    }}
                  />
                )}
              </AIBubble>
            )
        ))}
        {thinking && (() => {
          const last = history[history.length - 1];
          const hasGrowing = last && last.role === 'ai' && (last.text || last.reasoning);
          if (hasGrowing && !toolStatus) return null;
          return (
            <AIBubble role="ai">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-3)', fontSize: 12 }}>
                <span className="pulse">●</span>
                {toolStatus ? `正在调用工具:${toolStatus}…` : '计算中…'}
              </div>
            </AIBubble>
          );
        })()}

        <div style={{ marginTop: 8 }}>
          <div className="label" style={{ marginBottom: 8 }}>常用问题</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {skuQuestions(sku).map((q, i) => (
              <button key={i} onClick={() => sendToBackend(q)} disabled={thinking} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
                textAlign: 'left', border: '1px solid var(--border)',
                background: 'var(--surface)',
              }}>
                <Icon name="sparkles" size={11} color="var(--text-3)"/>
                <span style={{ fontSize: 12 }}>{q}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <AIInput placeholder="向 AI 追问 SKU 风险、采购量、规则影响…" onSend={sendToBackend} disabled={thinking}/>
    </div>
  );
}

Object.assign(window, { GlobalAIPanel, SKUAIPanel, extractRiskAdvice });
