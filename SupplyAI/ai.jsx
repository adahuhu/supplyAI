// AI panels — global (Dashboard) and per-SKU (detail).

function sanitizeAIVisibleText(value) {
  if (value == null) return '';
  let text = String(value);
  const replacements = [
    ['mk_supply_sku_daily_stat', '备货分析结果'],
    ['mk_purchase_draft', '采购计划草稿'],
    ['mk_holiday', '节日配置'],
    ['mk_sku_inbound_detail', '在途明细'],
    ['rl_fba_shipment_item', 'FBA 发货记录'],
    ['rl_amz_sales_daily_report', '销量记录'],
    ['rl_product', '商品资料'],
    ['calc_run_id', '系统快照'],
    ['listing_id', '商品编号'],
    ['mall_id', '店铺编号'],
    ['tenant_id', '账号信息'],
    ['holiday_id', '节日编号'],
    ['suggest_qty', '建议采购量'],
    ['suggest_amount', '建议采购金额'],
    ['coverage_demand', '覆盖周期需求'],
    ['sellable_days', '可售天数'],
    ['fba_sellable_days', '可售天数'],
    ['stockout_date', '预计断货日期'],
    ['purchase_date', '建议采购日期'],
    ['forecast_source', '预测来源'],
    ['unit_cost', '单位成本'],
  ];
  replacements.forEach(([raw, label]) => {
    text = text.replace(new RegExp(`\\b${raw}\\b`, 'g'), label);
  });
  return text
    .replace(/\b(?:mk|rl)_[A-Za-z0-9_]+\b/g, '系统数据')
    .replace(/\brisk_level\b/g, '风险等级')
    .replace(/\bimmediate\b/gi, '紧急')
    .replace(/\burgent\b/gi, '紧急')
    .replace(/\bsafe\b/gi, '安全')
    .replace(/([\u4e00-\u9fff])\s+(紧急|安全|风险等级)/g, '$1$2')
    .replace(/(紧急|安全|风险等级)\s+([\u4e00-\u9fff])/g, '$1$2')
    .replace(/\bSQL\b/gi, '数据查询');
}

function renderAIVisibleMarkdown(value) {
  const text = sanitizeAIVisibleText(value);
  return window.renderMarkdown ? window.renderMarkdown(text) : text;
}

// 思考折叠面板:流式期间默认展开看 AI 在想什么;思考完成后默认折叠,可手动展开。
function ReasoningPanel({ text, active }) {
  // active = true 时表示思考正在进行(还没有 content delta)
  const [open, setOpen] = React.useState(true);
  const wasActiveRef = React.useRef(active);
  const visibleText = sanitizeAIVisibleText(text);
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
          · {visibleText.length} 字
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
          {visibleText}
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
  const sellable = text.match(/(?:FBA\s*(?:侧)?(?:库存)?\s*)?(?:可售天数|可售|仅能支撑|仅剩|仅)?\s*([\d.]+)\s*天/);
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

  const sellableDays = adviceNumber(sellable?.[1] ?? skuMeta.sellableDays ?? skuMeta.sellable ?? skuMeta.fbaSellable);
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
      }} dangerouslySetInnerHTML={{ __html: renderAIVisibleMarkdown(text) }}/>
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
      : '缺少单位成本，需补充单价')
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
          可售天数仅 {adviceFormatFlexible(advice.sellableDays)} 天，需优先压缩运输时效。
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
        <div style={metricStyle}>
          <div className="label">可售天数</div>
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
            <li>当前参与库存只能支撑 {adviceFormatFlexible(advice.sellableDays)} 天，低于 P1 风险阈值。</li>
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
        <div style={{ textAlign: 'right' }}>可售天数</div>
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
          <div className="tabular" style={{ textAlign: 'right', fontSize: 12 }}>{adviceFormatFlexible(s.sellableDays ?? s.sellable ?? s.fbaSellable)} 天</div>
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

function SalesLeadersCard({ card, setRoute, openCreatePO, onClose }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 12.5 }}>
      <div style={{
        padding: '13px 14px',
        border: '1px solid rgba(52,211,153,.26)',
        borderLeft: '3px solid var(--p3)',
        borderRadius: 'var(--r-md)',
        background: 'linear-gradient(180deg, rgba(52,211,153,.12), rgba(52,211,153,.035))',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Icon name="arrow-up" size={14} color="var(--p3-strong)"/>
          <span style={{ fontWeight: 700 }}>{card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>优先推热卖且库存可支撑的 SKU</div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>{card.summary}</div>
      </div>
      <MetricGrid items={card.metrics}/>
      <EvidenceGrid items={card.evidence}/>
      <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r)', overflow: 'hidden', background: 'var(--surface)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 70px 74px 74px 88px', gap: 8, padding: '8px 10px', borderBottom: '1px solid var(--border)', color: 'var(--text-3)', fontSize: 11 }}>
          <div>SKU</div>
          <div style={{ textAlign: 'right' }}>近7天</div>
          <div style={{ textAlign: 'right' }}>预测日销</div>
          <div style={{ textAlign: 'right' }}>可售天数</div>
          <div>建议</div>
        </div>
        {(card.rows || []).map((s) => (
          <button key={s.id} onClick={() => setRoute && setRoute({ page: 'sku', skuId: s.id })} style={{
            width: '100%',
            border: 0,
            borderBottom: '1px solid var(--border)',
            background: 'transparent',
            color: 'inherit',
            cursor: 'pointer',
            display: 'grid',
            gridTemplateColumns: '1fr 70px 74px 74px 88px',
            gap: 8,
            alignItems: 'center',
            padding: '10px',
            textAlign: 'left',
            fontFamily: 'inherit',
          }}>
            <div style={{ minWidth: 0 }}>
              <div className="mono" style={{ fontSize: 12, color: 'var(--text-1)', display: 'flex', alignItems: 'center', gap: 6 }}>
                {s.msku}<PriorityBadge level={s.priority} compact/>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name || s.sku}</div>
              <div style={{ fontSize: 10.5, color: 'var(--text-4)', marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {(s.reasons || []).slice(0, 2).join(' · ')}
              </div>
            </div>
            <div className="tabular" style={{ textAlign: 'right', fontWeight: 700 }}>{adviceFormatNum(s.sales7d)}</div>
            <div className="tabular" style={{ textAlign: 'right' }}>{adviceFormatFlexible(s.futureDaily)}</div>
            <div className="tabular" style={{ textAlign: 'right', color: Number((s.sellableDays ?? s.sellable ?? s.fbaSellable) || 0) < 7 ? 'var(--p1)' : 'inherit' }}>{adviceFormatFlexible(s.sellableDays ?? s.sellable ?? s.fbaSellable)} 天</div>
            <div style={{ color: s.recommendation === '优先加码' || s.recommendation === '重点推广' ? 'var(--p3)' : 'var(--p2)', fontWeight: 650 }}>{s.recommendation}</div>
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn sm" onClick={() => {
          if (setRoute) setRoute({ page: 'list' });
          if (onClose) onClose();
        }}>查看备货列表</button>
        <button className="btn primary sm" onClick={() => {
          if (openCreatePO) openCreatePO(card.actionItems);
          if (onClose) onClose();
        }} disabled={!card.actionItems?.length}>给需补货 SKU 建计划</button>
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

function RuleImpactCard({ card, setRoute, openRules, onClose, refreshData, showToast }) {
  const [applying, setApplying] = React.useState(false);
  const targetSafeDays = Number(card.targetSafeDays || card.sku?.targetSafeDays || 21);
  const mainSku = card.sku || card.rows?.[0] || null;
  const isGlobalScope = card.scope === 'global';
  const applyRuleAndRecalc = async () => {
    if (!window.api || !mainSku) return;
    setApplying(true);
    try {
      const mallId = mainSku.mall_id ?? mainSku.mallId ?? null;
      const msku = mainSku.msku;
      const existingResp = await window.api.rulesList({
        scope_types: ['sku'],
        mall_id: mallId,
        msku,
        enabled_only: true,
        page_size: 1,
      }).catch(() => null);
      const existing = existingResp?.rows?.[0] || null;
      const leadFallback = Number(mainSku.purchaseLeadTime || 0);
      await window.api.rulesUpsert({
        rule_id: existing?.rule_id || undefined,
        scope_type: 'sku',
        mall_id: mallId,
        msku,
        safety_days: targetSafeDays,
        purchase_duration_days: existing?.purchase_duration_days ?? leadFallback,
        delivery_days: existing?.delivery_days ?? 0,
        qc_days: existing?.qc_days ?? 0,
        enabled: true,
        updated_by: 'ai-assistant',
      });
      await window.api.calcRun({ run_type: 'rule_changed' });
      if (refreshData) await refreshData();
      else if (window.refreshSupplyAI) await window.refreshSupplyAI();
      if (showToast) showToast(isGlobalScope
        ? `已应用到主 SKU 并重新计算`
        : `已应用安全天数 ${targetSafeDays} 天并重新计算`);
    } catch (err) {
      if (showToast) showToast('规则应用失败:' + err.message);
    } finally {
      setApplying(false);
    }
  };
  const changeLabel = card.actionText || (targetSafeDays > Number(mainSku?.currentSafeDays || 14) ? '提高' : targetSafeDays < Number(mainSku?.currentSafeDays || 14) ? '降低' : '保持');
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
          <span style={{ fontWeight: 700 }}>规则影响 · {card.title}</span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', lineHeight: 1.45 }}>
          安全天数{changeLabel}到 {targetSafeDays} 天后，建议采购量将随覆盖周期同步变化。
        </div>
        <div style={{ color: 'var(--text-3)', lineHeight: 1.55, marginTop: 5 }}>
          当前为后端基于最新计算批次的影响预览；点击应用后会保存规则并触发重新计算。
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
        <button className="btn sm" onClick={applyRuleAndRecalc} disabled={applying || !mainSku}>
          {applying ? '重新计算中…' : (isGlobalScope && card.rows?.length > 1 ? '应用到主 SKU 并重新计算' : `应用 ${targetSafeDays} 天并重新计算`)}
        </button>
        <button className="btn primary sm" onClick={() => {
          if (openRules) openRules({ sku: card.sku, mode: 'replenish' });
          if (onClose) onClose();
        }}>打开规则设置</button>
      </div>
    </div>
  );
}

function BackendDecisionCard({ card, sku, setRoute, openCreatePO, openRules, onClose, onAction, onCreatePlan, refreshData, showToast }) {
  const [state, setState] = React.useState({ loading: true, error: '', payload: null });
  React.useEffect(() => {
    let cancelled = false;
    const context = { ...(card.context || {}) };
    if (sku && !context.listing_id) {
      context.listing_id = sku.listingId || sku.id;
      context.mall_id = sku.mallId || sku.mall_id || null;
      context.msku = sku.msku;
      context.country_code = sku.country?.code;
    }
    window.api.aiDecisionCard(card.scenario, context)
      .then(payload => {
        if (!cancelled) setState({ loading: false, error: '', payload });
      })
      .catch(err => {
        if (!cancelled) setState({ loading: false, error: err.message, payload: null });
      });
    return () => { cancelled = true; };
  }, [card.scenario, JSON.stringify(card.context || {}), sku?.listingId]);
  if (state.loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-3)', fontSize: 12 }}>
        <span className="pulse">●</span>
        正在通过后端真实链路生成决策卡片…
      </div>
    );
  }
  if (state.error) {
    return <div style={{ color: 'var(--p1)', fontSize: 12 }}>⚠️ 决策卡片生成失败:{state.error}</div>;
  }
  return (
    <StructuredAICard
      card={state.payload?.card}
      text={state.payload?.content || ''}
      sku={sku}
      setRoute={setRoute}
      openCreatePO={openCreatePO}
      openRules={openRules}
      onClose={onClose}
      onAction={onAction}
      onCreatePlan={onCreatePlan}
      refreshData={refreshData}
      showToast={showToast}
    />
  );
}

function StructuredAICard({ card, text, sku, setRoute, openCreatePO, openRules, onClose, onAction, onCreatePlan, refreshData, showToast }) {
  const built = card;
  if (built?.type === 'backend_decision') {
    return (
      <BackendDecisionCard
        card={built}
        sku={sku}
        setRoute={setRoute}
        openCreatePO={openCreatePO}
        openRules={openRules}
        onClose={onClose}
        onAction={onAction}
        onCreatePlan={onCreatePlan}
        refreshData={refreshData}
        showToast={showToast}
      />
    );
  }
  if (built?.type === 'risk_queue') return <RiskQueueCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'sales_leaders') return <SalesLeadersCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'holiday_readiness') return <HolidayReadinessCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'plan_comparison') return <PlanComparisonCard card={built} setRoute={setRoute} openCreatePO={openCreatePO} onClose={onClose}/>;
  if (built?.type === 'rule_impact') return <RuleImpactCard card={built} setRoute={setRoute} openRules={openRules} onClose={onClose} refreshData={refreshData} showToast={showToast}/>;
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

// 场景名 → 中文标签(用于 classify 事件占位)
const SCENARIO_LABEL = {
  risk_queue: '高风险队列',
  sales_leaders: '销量主推',
  holiday_readiness: '大促备货',
  plan_comparison: '方案对比',
  rule_impact: '规则影响',
  single_sku_replenishment: '单SKU补货',
};

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
  { tag: '规则影响', q: '安全天数改成 21 天会怎样?采购量和风险等级有什么变化?' },
];


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

function GlobalAIPanel({ onClose, setRoute, openCreatePO, openRules, dashFilters, history, setHistory, wide, onToggleWide, refreshData, showToast }) {
  const [thinking, setThinking] = React.useState(false);
  const [toolStatus, setToolStatus] = React.useState(''); // 正在调用的 tool 名
  const sendToBackend = async (text) => {
    setHistory(h => [...h, { role: 'user', text }]);
    setThinking(true);
    setToolStatus('');
    try {
      const msgs = [];
      for (const m of history) {
        if (m.role === 'user' && m.text) msgs.push({ role: 'user', content: m.text });
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: sanitizeAIVisibleText(m.text) });
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

      let explanationStarted = false;
      let cardSeen = false;
      const startExplanationBubble = () => {
        if (!explanationStarted) {
          explanationStarted = true;
          setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true, explain: true }]);
        }
      };
      const appendDelta = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, text: (last.text || '') + delta };
          }
          return next;
        });
      };
      const appendReasoning = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, reasoning: (last.reasoning || '') + delta };
          }
          return next;
        });
      };

      await window.api.aiSmartDecisionStream(msgs, context, (ev) => {
        if (ev.type === 'classify') {
          setToolStatus(SCENARIO_LABEL[ev.scenario] || ev.scenario);
        } else if (ev.type === 'card') {
          setToolStatus('');
          cardSeen = true;
          setHistory(h => [...h, { role: 'ai', text: ev.summary, card: ev.card }]);
        } else if (ev.type === 'reasoning_delta') {
          startExplanationBubble();
          appendReasoning(ev.text || '');
        } else if (ev.type === 'delta') {
          startExplanationBubble();
          appendDelta(ev.text || '');
        } else if (ev.type === 'tool_start') {
          setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        } else if (ev.type === 'tool_end') {
          setToolStatus('');
        } else if (ev.type === 'error') {
          startExplanationBubble();
          appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        } else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            if (last && last.streaming && !last.text && !last.reasoning) {
              return next.slice(0, -1);
            }
            return next.map(m => m.streaming ? { ...m, streaming: false } : m);
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ ' + err.message }]);
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
                {m.text && (m.explain
                  ? <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-1)' }} dangerouslySetInnerHTML={{ __html: renderAIVisibleMarkdown(m.text) }}/>
                  : <StructuredAICard
                      card={m.card}
                      text={sanitizeAIVisibleText(m.text)}
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
                      refreshData={refreshData}
                      showToast={showToast}
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

function SKUAIPanel({ sku, onClose, mode, history, setHistory, wide, onToggleWide, openCreatePO, openRules, refreshData, showToast }) {
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
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: sanitizeAIVisibleText(m.text) });
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
        },
      };

      let explanationStarted = false;
      let cardSeen = false;
      const startExplanationBubble = () => {
        if (!explanationStarted) {
          explanationStarted = true;
          setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true, explain: true }]);
        }
      };
      const appendDelta = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, text: (last.text || '') + delta };
          }
          return next;
        });
      };
      const appendReasoning = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, reasoning: (last.reasoning || '') + delta };
          }
          return next;
        });
      };

      await window.api.aiSmartDecisionStream(msgs, context, (ev) => {
        if (ev.type === 'classify') {
          setToolStatus(SCENARIO_LABEL[ev.scenario] || ev.scenario);
        } else if (ev.type === 'card') {
          setToolStatus('');
          cardSeen = true;
          setHistory(h => [...h, { role: 'ai', text: ev.summary, card: ev.card }]);
        } else if (ev.type === 'reasoning_delta') {
          startExplanationBubble();
          appendReasoning(ev.text || '');
        } else if (ev.type === 'delta') {
          startExplanationBubble();
          appendDelta(ev.text || '');
        } else if (ev.type === 'tool_start') {
          setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        } else if (ev.type === 'tool_end') {
          setToolStatus('');
        } else if (ev.type === 'error') {
          startExplanationBubble();
          appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        } else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            if (last && last.streaming && !last.text && !last.reasoning) {
              return next.slice(0, -1);
            }
            return next.map(m => m.streaming ? { ...m, streaming: false } : m);
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ ' + err.message }]);
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
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>可售天数 {sku.sellable}d · 建议采购 {sku.suggestQty}</div>
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
                {m.text && (m.explain
                  ? <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text-1)' }} dangerouslySetInnerHTML={{ __html: renderAIVisibleMarkdown(m.text) }}/>
                  : <StructuredAICard
                      card={m.card}
                      text={sanitizeAIVisibleText(m.text)}
                      sku={sku}
                      openCreatePO={openCreatePO}
                      openRules={openRules}
                      onClose={onClose}
                      onAction={sendToBackend}
                      onCreatePlan={(advice) => {
                        if (openCreatePO) openCreatePO([{ id: sku.id, qty: advice.suggestQty, supplier: advice.supplierConfirm }]);
                        onClose && onClose();
                      }}
                      refreshData={refreshData}
                      showToast={showToast}
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
