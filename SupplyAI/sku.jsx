// SKU 分析详情页

const SKU_TREND_TODAY = new Date('2026-05-04T00:00:00');
const SKU_TREND_RANGES = [
  { id: '7d', label: '7天', histDays: 7, futDays: 14 },
  { id: '30d', label: '30天', histDays: 30, futDays: 30 },
  { id: '90d', label: '90天', histDays: 60, futDays: 60 },
  { id: 'thisYear', label: '今年', histDays: 124, futDays: 120 },
  { id: 'lastYear', label: '去年', histDays: 180, futDays: 0 },
  { id: 'all', label: '全部', histDays: 180, futDays: 90 },
];

function trendDateAdd(d, days) {
  return new Date(d.getTime() + days * 86400000);
}

function trendDateDiff(a, b) {
  return Math.round((b.getTime() - a.getTime()) / 86400000);
}

function trendMD(d) {
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`;
}

function trendYMD(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function extendTrendHistory(histRaw, targetDays, seedBase = 41) {
  const base = histRaw && histRaw.length ? histRaw : [0];
  const out = [];
  let seed = seedBase;
  while (out.length < targetDays) {
    for (const v of base) {
      seed = (seed * 9301 + 49297) % 233280;
      const noise = (seed / 233280 - 0.5) * 0.18;
      out.push(Math.max(0, Math.round(v * (1 + noise))));
      if (out.length >= targetDays) break;
    }
  }
  return out.slice(-targetDays);
}

function buildTrendForecast(sku, futDays, salesMultipliers) {
  return Array.from({ length: futDays }, (_, i) => {
    const base = i < sku.future30.length ? sku.future30[i] : sku.futureDaily;
    const mult = salesMultipliers[i] || 1;
    return {
      value: Math.max(0, Math.round(base * mult)),
      mult,
    };
  });
}

function buildTrendInventory(startStock, forecastValues, inventoryOverrides) {
  let inv = startStock;
  return forecastValues.map((daily, i) => {
    if (inventoryOverrides[i] != null) inv = inventoryOverrides[i];
    inv = Math.max(0, inv - daily);
    return inv;
  });
}

function SKUTrendPanel({ sku }) {
  const [rangeId, setRangeId] = React.useState('30d');
  const [salesMultipliers, setSalesMultipliers] = React.useState({});
  const [inventoryOverrides, setInventoryOverrides] = React.useState({});
  const range = SKU_TREND_RANGES.find(r => r.id === rangeId) || SKU_TREND_RANGES[1];
  const forecast = React.useMemo(
    () => buildTrendForecast(sku, range.futDays, salesMultipliers),
    [sku.id, sku.futureDaily, range.futDays, JSON.stringify(salesMultipliers)]
  );
  const forecastValues = forecast.map(f => f.value);
  const adjustedAvg = forecastValues.length
    ? Math.round(forecastValues.reduce((sum, v) => sum + v, 0) / forecastValues.length)
    : sku.futureDaily;
  const hasAdjustments = Object.keys(salesMultipliers).length > 0 || Object.keys(inventoryOverrides).length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11.5, color: 'var(--text-3)', marginRight: 2 }}>时间范围</span>
        {SKU_TREND_RANGES.map(r => (
          <button
            key={r.id}
            className={`btn sm ${rangeId === r.id ? 'primary' : ''}`}
            style={{ fontSize: 11 }}
            onClick={() => setRangeId(r.id)}
          >
            {r.label}
          </button>
        ))}
        <span style={{ flex: 1 }}/>
        {hasAdjustments && (
          <button
            className="btn sm ghost"
            style={{ color: 'var(--text-3)' }}
            onClick={() => { setSalesMultipliers({}); setInventoryOverrides({}); }}
          >
            重置调整
          </button>
        )}
      </div>

      <SKUTrendChart
        sku={sku}
        range={range}
        forecast={forecast}
        salesMultipliers={salesMultipliers}
        setSalesMultipliers={setSalesMultipliers}
        inventoryOverrides={inventoryOverrides}
        setInventoryOverrides={setInventoryOverrides}
      />

      <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', fontSize: 11.5, color: 'var(--text-3)' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 16, height: 2, background: 'var(--accent)', display: 'inline-block', borderRadius: 2 }}/>
          历史销量
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 16, height: 0, borderTop: '2px dashed var(--accent)', display: 'inline-block' }}/>
          预测日销
        </span>
        {range.futDays > 0 && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 16, height: 2, background: 'var(--p3)', display: 'inline-block', borderRadius: 2 }}/>
            预计库存
          </span>
        )}
        <span style={{ flex: 1 }}/>
        {hasAdjustments && range.futDays > 0 && (
          <span style={{ color: adjustedAvg >= sku.futureDaily ? 'var(--p3-strong)' : 'var(--p2-strong)', fontWeight: 600 }}>
            调整后均日销 {(+adjustedAvg).toFixed(2)} 件
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <KV k="近 7 天日销（原始）" v={sku.last7Daily}/>
        <KV k="近 7 天日销（去噪）" v={sku.last7Denoised}/>
        <KV k="未来平均日销" v={hasAdjustments && range.futDays > 0 ? `${(+adjustedAvg).toFixed(2)} (调后)` : (+sku.futureDaily).toFixed(2)}/>
        <KV k="未来 14 天合计" v={fmt.num(forecastValues.slice(0, 14).reduce((a, b) => a + b, 0))}/>
      </div>
    </div>
  );
}

function SKUTrendChart({
  sku,
  range,
  forecast,
  salesMultipliers,
  setSalesMultipliers,
  inventoryOverrides,
  setInventoryOverrides,
}) {
  const svgRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const [tip, setTip] = React.useState(null);
  const [editor, setEditor] = React.useState(null);
  const [editValue, setEditValue] = React.useState('');
  const histDays = range.histDays;
  const futDays = range.futDays;
  const isHistoryOnly = futDays === 0;
  const history = React.useMemo(
    () => extendTrendHistory(sku.histRaw, histDays, sku.msku.charCodeAt(2) || 41),
    [sku.id, histDays]
  );
  const forecastValues = forecast.map(f => f.value);
  const inventory = React.useMemo(
    () => buildTrendInventory(sku.totalStock, forecastValues, inventoryOverrides),
    [sku.totalStock, JSON.stringify(forecastValues), JSON.stringify(inventoryOverrides)]
  );

  const W = 960;
  const H = 320;
  const PAD = { top: 30, right: isHistoryOnly ? 22 : 72, bottom: 36, left: 52 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const totalLen = history.length + forecastValues.length;
  const salesMax = Math.max(...history, ...forecastValues, 1) * 1.22;
  const invMax = Math.max(...inventory, sku.totalStock, 1) * 1.08;
  const toX = (idx) => PAD.left + (idx / Math.max(1, totalLen - 1)) * plotW;
  const toSalesY = (v) => PAD.top + plotH - (v / salesMax) * plotH;
  const toInvY = (v) => PAD.top + plotH - (v / invMax) * plotH;
  const todayX = isHistoryOnly ? null : toX(history.length);
  const pathOf = (points) => points.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const areaOf = (points) => points.length < 2 ? '' : `${pathOf(points)} L${points[points.length - 1][0].toFixed(1)},${PAD.top + plotH} L${points[0][0].toFixed(1)},${PAD.top + plotH} Z`;
  const historyPoints = history.map((v, i) => [toX(i), toSalesY(v)]);
  const forecastPoints = forecastValues.map((v, i) => [toX(history.length + i), toSalesY(v)]);
  const inventoryPoints = inventory.map((v, i) => [toX(history.length + i), toInvY(v)]);
  const salesTicks = [0, 0.25, 0.5, 0.75, 1].map(p => ({
    y: PAD.top + plotH * (1 - p),
    sales: Math.round(salesMax * p),
    inventory: Math.round(invMax * p),
  }));
  const xStep = Math.max(1, Math.round(totalLen / 9));
  const xLabels = Array.from({ length: totalLen }, (_, i) => i)
    .filter(i => i === 0 || i === history.length || i === totalLen - 1 || i % xStep === 0)
    .map(i => {
      const offset = i < history.length ? -(history.length - i) : i - history.length;
      const d = trendDateAdd(SKU_TREND_TODAY, offset);
      return { i, x: toX(i), d, isToday: i === history.length && !isHistoryOnly, isFuture: i >= history.length };
    });
  const stockoutOffset = sku.fbaSellable;
  const stockoutX = !isHistoryOnly && stockoutOffset >= 0 && stockoutOffset < futDays
    ? toX(history.length + stockoutOffset)
    : null;
  const purchaseOffset = trendDateDiff(SKU_TREND_TODAY, sku.purchaseDate);
  const purchaseX = !isHistoryOnly && purchaseOffset >= 0 && purchaseOffset < futDays
    ? toX(history.length + purchaseOffset)
    : null;

  const clientToIndex = (clientX) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return 0;
    const x = (clientX - rect.left) * (W / rect.width);
    return Math.max(0, Math.min(totalLen - 1, Math.round((x - PAD.left) / (plotW / Math.max(1, totalLen - 1)))));
  };

  const showTip = (e) => {
    if (editor) return;
    const idx = clientToIndex(e.clientX);
    const isFuture = idx >= history.length;
    const fi = idx - history.length;
    const sales = isFuture ? forecastValues[fi] : history[idx];
    const inv = isFuture ? inventory[fi] : null;
    const d = trendDateAdd(SKU_TREND_TODAY, isFuture ? fi : -(history.length - idx));
    setTip({
      idx,
      fi,
      x: toX(idx),
      y: toSalesY(sales),
      sales,
      inv,
      d,
      isFuture,
      mult: isFuture ? forecast[fi]?.mult : null,
    });
  };

  const openEditor = (e) => {
    const idx = clientToIndex(e.clientX);
    if (idx < history.length || isHistoryOnly) return;
    const fi = idx - history.length;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const clickY = (e.clientY - rect.top) * (H / rect.height);
    const salesY = toSalesY(forecastValues[fi] || 0);
    const invY = toInvY(inventory[fi] || 0);
    const editType = Math.abs(clickY - salesY) <= Math.abs(clickY - invY) + 16 ? 'sales' : 'inventory';
    const px = (toX(idx) / W) * rect.width + rect.left;
    const py = ((editType === 'sales' ? salesY : invY) / H) * rect.height + rect.top;
    setTip(null);
    setEditor({ type: editType, fi, x: px, y: py, date: trendDateAdd(SKU_TREND_TODAY, fi) });
    setEditValue(editType === 'sales'
      ? String((salesMultipliers[fi] || forecast[fi]?.mult || 1).toFixed(2))
      : String(inventoryOverrides[fi] != null ? inventoryOverrides[fi] : inventory[fi] || 0)
    );
    setTimeout(() => editorRef.current?.focus(), 30);
  };

  const commitEditor = () => {
    if (!editor) return;
    if (editor.type === 'sales') {
      const next = Number(editValue);
      if (Number.isFinite(next) && next > 0) {
        setSalesMultipliers(prev => ({ ...prev, [editor.fi]: next }));
      }
    } else {
      const next = Number.parseInt(editValue, 10);
      if (Number.isFinite(next) && next >= 0) {
        setInventoryOverrides(prev => ({ ...prev, [editor.fi]: next }));
      }
    }
    setEditor(null);
  };

  return (
    <div style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        width="100%"
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ display: 'block', overflow: 'visible', cursor: isHistoryOnly ? 'default' : 'crosshair' }}
        onPointerMove={showTip}
        onPointerLeave={() => setTip(null)}
        onClick={openEditor}
      >
        <defs>
          <linearGradient id="skuSalesHistGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.16"/>
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="skuSalesFutureGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.08"/>
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="skuInvGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--p3)" stopOpacity="0.18"/>
            <stop offset="100%" stopColor="var(--p3)" stopOpacity="0.01"/>
          </linearGradient>
          <clipPath id="skuTrendClip">
            <rect x={PAD.left} y={PAD.top - 4} width={plotW} height={plotH + 8}/>
          </clipPath>
        </defs>

        {salesTicks.slice(1).map(({ y }) => (
          <line key={y} x1={PAD.left} y1={y} x2={PAD.left + plotW} y2={y} stroke="var(--border)" strokeDasharray="3 6" strokeWidth="0.8"/>
        ))}
        {salesTicks.map(({ y, sales, inventory }) => (
          <g key={y}>
            <text x={PAD.left - 8} y={y + 3.5} fontSize="9.5" fill="var(--accent)" textAnchor="end" fontFamily="var(--font-mono)">{sales}</text>
            {!isHistoryOnly && (
              <text x={PAD.left + plotW + PAD.right - 8} y={y + 3.5} fontSize="9.5" fill="var(--p3-strong)" textAnchor="end" fontFamily="var(--font-mono)">{inventory}</text>
            )}
          </g>
        ))}
        <text x="16" y={PAD.top + plotH / 2} fontSize="10" fill="var(--accent)" textAnchor="middle" transform={`rotate(-90,16,${PAD.top + plotH / 2})`}>日销量</text>
        {!isHistoryOnly && (
          <text x={W - 12} y={PAD.top + plotH / 2} fontSize="10" fill="var(--p3-strong)" textAnchor="middle" transform={`rotate(90,${W - 12},${PAD.top + plotH / 2})`}>库存量</text>
        )}

        {!isHistoryOnly && (
          <rect x={todayX} y={PAD.top} width={PAD.left + plotW - todayX} height={plotH} fill="var(--bg-sunken)" opacity="0.45"/>
        )}

        <g clipPath="url(#skuTrendClip)">
          <path d={areaOf(historyPoints)} fill="url(#skuSalesHistGrad)"/>
          <path d={pathOf(historyPoints)} fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/>
          {!isHistoryOnly && (
            <>
              <path d={areaOf(forecastPoints)} fill="url(#skuSalesFutureGrad)"/>
              <path d={pathOf(forecastPoints)} fill="none" stroke="var(--accent)" strokeWidth="1.8" strokeDasharray="5 3" strokeLinejoin="round" strokeLinecap="round" opacity="0.9"/>
              <path d={areaOf(inventoryPoints)} fill="url(#skuInvGrad)"/>
              <path d={pathOf(inventoryPoints)} fill="none" stroke="var(--p3)" strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" opacity="0.82"/>
              {forecast.map((p, i) => Math.abs((p.mult || 1) - 1) >= 0.01 && (
                <circle key={i} cx={toX(history.length + i)} cy={toSalesY(p.value)} r="3.8" fill={p.mult > 1 ? 'var(--p3)' : 'var(--p2)'} stroke="var(--surface)" strokeWidth="1.5"/>
              ))}
              {Object.entries(inventoryOverrides).map(([fi, value]) => (
                <circle key={fi} cx={toX(history.length + Number(fi))} cy={toInvY(value)} r="4.8" fill="#7c3aed" stroke="var(--surface)" strokeWidth="2"/>
              ))}
            </>
          )}
          {tip && !editor && (
            <>
              <line x1={tip.x} y1={PAD.top} x2={tip.x} y2={PAD.top + plotH} stroke="var(--text-3)" strokeWidth="1" strokeDasharray="2 2" opacity="0.32"/>
              <circle cx={tip.x} cy={tip.y} r="4.5" fill="var(--accent)" stroke="var(--surface)" strokeWidth="2"/>
              {tip.inv != null && <circle cx={tip.x} cy={toInvY(tip.inv)} r="4.3" fill="var(--p3)" stroke="var(--surface)" strokeWidth="2"/>}
            </>
          )}
        </g>

        {!isHistoryOnly && (
          <>
            <line x1={todayX} y1={PAD.top - 8} x2={todayX} y2={PAD.top + plotH} stroke="var(--text-3)" strokeWidth="1.2" strokeDasharray="3 2"/>
            <rect x={todayX - 14} y={PAD.top - 22} width="28" height="15" rx="3" fill="var(--surface-2)" stroke="var(--border)"/>
            <text x={todayX} y={PAD.top - 11} fontSize="9.5" fill="var(--text-3)" textAnchor="middle" fontWeight="600">今天</text>
          </>
        )}
        {stockoutX != null && (
          <g>
            <line x1={stockoutX} y1={PAD.top} x2={stockoutX} y2={PAD.top + plotH} stroke="var(--p1)" strokeWidth="1.4" strokeDasharray="4 3"/>
            <rect x={stockoutX - 24} y={PAD.top + 3} width="48" height="16" rx="4" fill="var(--p1-soft)"/>
            <text x={stockoutX} y={PAD.top + 15} fontSize="9.5" fill="var(--p1-strong)" textAnchor="middle" fontWeight="700">预计断货</text>
          </g>
        )}
        {purchaseX != null && (
          <g>
            <line x1={purchaseX} y1={PAD.top} x2={purchaseX} y2={PAD.top + plotH} stroke="var(--p3-strong)" strokeWidth="1.4" strokeDasharray="4 3"/>
            <rect x={purchaseX - 24} y={PAD.top + plotH - 21} width="48" height="16" rx="4" fill="var(--p3-soft)"/>
            <text x={purchaseX} y={PAD.top + plotH - 9} fontSize="9.5" fill="var(--p3-strong)" textAnchor="middle" fontWeight="700">建议补货</text>
          </g>
        )}
        <line x1={PAD.left} y1={PAD.top + plotH} x2={PAD.left + plotW} y2={PAD.top + plotH} stroke="var(--border)" strokeWidth="1"/>
        {xLabels.map(({ i, x, d, isToday, isFuture }) => {
          const anchor = i === 0 ? 'start' : i === totalLen - 1 ? 'end' : 'middle';
          return (
            <g key={`${i}-${trendMD(d)}`}>
              <line x1={x} y1={PAD.top + plotH} x2={x} y2={PAD.top + plotH + 4} stroke={isToday ? 'var(--accent)' : 'var(--border-strong)'} strokeWidth="1"/>
              <text x={x} y={PAD.top + plotH + 17} fontSize="10" textAnchor={anchor} fill={isToday ? 'var(--accent)' : isFuture ? 'var(--text-3)' : 'var(--text-4)'} fontWeight={isToday ? 600 : 400} fontFamily="var(--font-mono)">
                {isToday ? '今天 ' : ''}{trendMD(d)}
              </text>
            </g>
          );
        })}
      </svg>

      {tip && !editor && (() => {
        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) return null;
        const px = (tip.x / W) * rect.width + rect.left;
        const py = (tip.y / H) * rect.height + rect.top;
        const flip = px > rect.left + rect.width * 0.62;
        return (
          <div style={{
            position: 'fixed', zIndex: 280, pointerEvents: 'none',
            left: flip ? px - 190 : px + 14,
            top: Math.max(8, py - 16),
            minWidth: 170,
            padding: '9px 12px',
            background: 'var(--surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--sh-pop)',
            fontSize: 12,
          }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-3)', marginBottom: 6 }}>{trendYMD(tip.d)}{tip.isFuture && <span style={{ marginLeft: 6, color: 'var(--text-4)' }}>预测</span>}</div>
            <TooltipMetric color="var(--accent)" label="日销量" value={tip.sales} unit="件"/>
            {tip.inv != null && <TooltipMetric color="var(--p3)" label="预计库存" value={fmt.num(tip.inv)} unit="件" strongColor={tip.inv < sku.futureDaily * 7 ? 'var(--p1)' : 'var(--p3-strong)'}/>}
            {tip.isFuture && tip.mult && Math.abs(tip.mult - 1) >= 0.01 && (
              <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid var(--border)', color: tip.mult >= 1 ? 'var(--p3-strong)' : 'var(--p2-strong)', fontSize: 11 }}>
                系数 x{tip.mult.toFixed(2)}
              </div>
            )}
          </div>
        );
      })()}

      {editor && (() => {
        const flip = editor.x > window.innerWidth * 0.58;
        const isSales = editor.type === 'sales';
        return (
          <div
            style={{
              position: 'fixed', zIndex: 360,
              left: Math.max(8, flip ? editor.x - 250 : editor.x + 12),
              top: Math.max(8, editor.y - 20),
              width: 238,
              padding: '12px 14px',
              background: 'var(--surface)',
              border: `1.5px solid ${isSales ? 'var(--accent)' : 'var(--p3)'}`,
              borderRadius: 'var(--r-md)',
              boxShadow: 'var(--sh-pop)',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 12.5 }}>{isSales ? '调整预测系数' : '调整预计库存'}</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 1 }}>{trendMD(editor.date)}</div>
              </div>
              <button className="btn ghost icon sm" onClick={() => setEditor(null)}><Icon name="x" size={12}/></button>
            </div>
            {isSales ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-3)' }}>系数</span>
                  <span className="tabular" style={{ fontSize: 20, fontWeight: 700, color: Number(editValue) >= 1 ? 'var(--p3-strong)' : 'var(--p2-strong)' }}>x{(Number(editValue) || 1).toFixed(2)}</span>
                </div>
                <input
                  ref={editorRef}
                  type="range"
                  min="0.2"
                  max="3"
                  step="0.05"
                  value={editValue}
                  onChange={e => setEditValue(e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--accent)' }}
                />
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                  {[0.7, 0.85, 1, 1.2, 1.5, 2].map(v => (
                    <button
                      key={v}
                      className="btn sm ghost"
                      style={{
                        height: 24,
                        fontSize: 11,
                        background: Math.abs(Number(editValue) - v) < 0.01 ? 'var(--accent-soft)' : 'transparent',
                        color: v >= 1 ? 'var(--p3-strong)' : 'var(--p2-strong)',
                      }}
                      onClick={() => setEditValue(String(v))}
                    >
                      {v === 1 ? '基准' : `${Math.round((v - 1) * 100)}%`}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--text-3)' }}>库存数量</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    ref={editorRef}
                    className="txt"
                    type="number"
                    min="0"
                    value={editValue}
                    onChange={e => setEditValue(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') commitEditor();
                      if (e.key === 'Escape') setEditor(null);
                    }}
                    style={{ flex: 1, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}
                  />
                  <span style={{ fontSize: 12, color: 'var(--text-3)' }}>件</span>
                </div>
              </div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn primary sm" style={{ flex: 1 }} onClick={commitEditor}>确认</button>
              <button className="btn sm" onClick={() => setEditor(null)}>取消</button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

function TooltipMetric({ color, label, value, unit, strongColor }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 4 }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block', flex: 'none' }}/>
      <span style={{ color: 'var(--text-3)', fontSize: 11 }}>{label}</span>
      <span className="tabular" style={{ marginLeft: 'auto', fontSize: 16, fontWeight: 700, color: strongColor || 'var(--text)' }}>{value}<span style={{ fontSize: 11, fontWeight: 400, color: 'var(--text-3)', marginLeft: 2 }}>{unit}</span></span>
    </div>
  );
}

// ── V7 trend panel: sales + inventory + holiday bands ───────────────────────
const TODAY_V7 = new Date('2026-05-04T00:00:00');

// 节日数据来自后端 /dashboard/holidays(挂在 window.HOLIDAYS_DATA)。
// SKU 分析页允许维护自定义节日,并同步到全局大促提醒和趋势计算。
const HOLIDAY_COLORS_V7 = ['#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];

function holidayPeakDateV7(value) {
  if (!value) return null;
  const d = new Date(String(value).includes('T') ? value : `${value}T00:00:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

function holidayAbsRangeV7(h) {
  const peakDate = holidayPeakDateV7(h.peak || h.peak_date);
  if (!peakDate) return { fromAbs: 1, toAbs: 1 };
  const sb = Math.max(0, parseInt(h.sb ?? h.days_before ?? 0, 10) || 0);
  const sa = Math.max(0, parseInt(h.sa ?? h.days_after ?? 0, 10) || 0);
  const peakAbs = dateDiffV7(TODAY_V7, peakDate);
  return { fromAbs: peakAbs - sb, toAbs: peakAbs + sa };
}

function normalizeHolidayV7(h, index = 0) {
  const fallbackPeak = fmtYMDV7(dateAddV7(TODAY_V7, 14 + index));
  const peak = h.peak || h.peak_date || fallbackPeak;
  const mult = Number(h.mult ?? h.dm ?? h.sales_multiplier ?? 1) || 1;
  const countryCode = h.countryCode ?? h.country_code ?? null;
  const normalized = {
    ...h,
    id: h.id || h.holiday_id || `custom-holiday-${Date.now()}-${index}`,
    name: h.name || '自定义大促',
    flag: h.flag || '🎯',
    peak,
    sb: Math.max(0, parseInt(h.sb ?? h.days_before ?? 0, 10) || 0),
    sa: Math.max(0, parseInt(h.sa ?? h.days_after ?? 0, 10) || 0),
    dm: mult,
    mult,
    color: h.color || HOLIDAY_COLORS_V7[index % HOLIDAY_COLORS_V7.length],
    countryCode,
    country_code: countryCode,
  };
  const explicitRange = (h.isPointOverride || h.__useAbsRange)
    && Number.isFinite(Number(h.fromAbs))
    && Number.isFinite(Number(h.toAbs));
  const range = explicitRange
    ? { fromAbs: Number(h.fromAbs), toAbs: Number(h.toAbs) }
    : holidayAbsRangeV7(normalized);
  return { ...normalized, ...range };
}

function normalizeHolidayListV7(list) {
  return (list || [])
    .filter(Boolean)
    .map((h, i) => normalizeHolidayV7(h, i))
    .sort((a, b) => String(a.peak).localeCompare(String(b.peak)));
}

function setGlobalHolidaysV7(list) {
  const normalized = normalizeHolidayListV7(list).filter(h => !h.isPointOverride);
  window.HOLIDAYS_DATA = normalized.map(h => ({
    id: h.id,
    name: h.name,
    flag: h.flag,
    peak: h.peak,
    sb: h.sb,
    sa: h.sa,
    dm: h.mult ?? h.dm ?? 1,
    color: h.color,
    countryCode: h.countryCode ?? null,
    country_code: h.countryCode ?? null,
  }));
  return normalized;
}

function getHolidays() {
  return normalizeHolidayListV7(window.HOLIDAYS_DATA || []);
}

const TIME_RANGES_V7 = [
  { id: '7d', label: '7天', histDays: 7, futDays: 14 },
  { id: '30d', label: '30天', histDays: 30, futDays: 30 },
  { id: '90d', label: '90天', histDays: 60, futDays: 60 },
  { id: 'thisYear', label: '今年', histDays: 124, futDays: 241 },
  { id: 'lastYear', label: '去年', histDays: 365, futDays: 0 },
  { id: 'all', label: '全部', histDays: 180, futDays: 90 },
];

function dateAddV7(d, days) {
  return new Date(d.getTime() + days * 86400000);
}

function dateDiffV7(a, b) {
  return Math.round((b - a) / 86400000);
}

function fmtMDV7(d) {
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function fmtYMDV7(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function holidayBandLabelV7(h) {
  const nameMap = {
    'Mothers Day': '母亲节',
    "Mother's Day": '母亲节',
  };
  const name = nameMap[h?.name] || h?.name || '大促';
  return `${name} x${Number(h?.mult || 1).toFixed(1)}`;
}

function extendHistoryV7(histRaw, targetDays, seed0) {
  const base = histRaw && histRaw.length ? histRaw : [0];
  const result = [];
  let seed = seed0 || 42;
  while (result.length < targetDays) {
    for (const v of base) {
      seed = (seed * 9301 + 49297) % 233280;
      const noise = (seed / 233280 - 0.5) * 0.18;
      result.push(Math.max(0, Math.round(v * (1 + noise))));
      if (result.length >= targetDays) break;
    }
  }
  return result.slice(-targetDays);
}

function buildForecastV7(baseFutureDaily, futDays, holidays) {
  const result = [];
  for (let i = 0; i < futDays; i++) {
    const absDay = i + 1;
    let mult = 1;
    for (const h of holidays) {
      if (absDay >= h.fromAbs && absDay <= h.toAbs) mult *= h.mult;
    }
    result.push({ value: Math.max(0, Math.round(baseFutureDaily * mult)), mult });
  }
  return result;
}

function buildStockConstrainedForecastV7(baseFutureDaily, futDays, holidays, startInv, invOverrides) {
  const demand = buildForecastV7(baseFutureDaily, futDays, holidays);
  const result = [];
  let inv = Math.max(0, Number(startInv) || 0);
  for (let i = 0; i < futDays; i++) {
    const absDay = i + 1;
    if (invOverrides[absDay] !== undefined) {
      inv = Math.max(0, Number(invOverrides[absDay]) || 0);
    }
    const wanted = demand[i]?.value || 0;
    const sold = inv <= 0 ? 0 : Math.min(wanted, inv);
    inv = Math.max(0, inv - sold);
    result.push({ ...demand[i], value: Math.round(sold), demand: wanted });
  }
  return result;
}

function buildInventoryV7(startInv, forecastValues, invOverrides) {
  const series = [];
  let inv = startInv;
  for (let i = 0; i < forecastValues.length; i++) {
    const absDay = i + 1;
    if (invOverrides[absDay] !== undefined) inv = invOverrides[absDay];
    inv = Math.max(0, inv - forecastValues[i]);
    series.push(inv);
  }
  return series;
}

function TrendPanelV7({ sku }) {
  const [rangeId, setRangeId] = React.useState('30d');
  const [holidays, setHolidays] = React.useState(() => getHolidays());
  const initialInvOverrides = React.useMemo(
    () => ({ ...(sku.inventoryOverrides || {}) }),
    [sku.id, sku.listingId, JSON.stringify(sku.inventoryOverrides || {})]
  );
  const [invOverrides, setInvOverrides] = React.useState(initialInvOverrides);
  const [invSaveState, setInvSaveState] = React.useState(null);
  const range = TIME_RANGES_V7.find(r => r.id === rangeId) || TIME_RANGES_V7[1];
  const isLastYear = rangeId === 'lastYear';
  const forecast = React.useMemo(
    () => buildStockConstrainedForecastV7(sku.futureDaily, range.futDays, holidays, sku.totalStock, invOverrides),
    [sku.futureDaily, sku.totalStock, range.futDays, JSON.stringify(holidays), JSON.stringify(invOverrides)]
  );
  const adjAvg = range.futDays > 0
    ? Math.round(forecast.reduce((sum, item) => sum + item.value, 0) / Math.max(1, forecast.length))
    : sku.futureDaily;
  const hasAdj = holidays.some(h => Math.abs(h.mult - 1) > 0.01);
  const hasInvOvr = Object.keys(invOverrides).length > 0;
  const visH = holidays.filter(h => !h.isPointOverride && h.toAbs > 0 && h.fromAbs < range.futDays && Math.abs(h.mult - 1) > 0.01);
  const pointOvr = holidays.filter(h => h.isPointOverride);

  React.useEffect(() => {
    setInvOverrides(initialInvOverrides);
  }, [initialInvOverrides]);

  const syncHolidayList = React.useCallback((next) => {
    const normalized = normalizeHolidayListV7(next);
    setGlobalHolidaysV7(normalized);
    return normalized;
  }, []);

  const commitHolidayList = React.useCallback((next) => {
    const normalized = syncHolidayList(next);
    setHolidays(normalized);
    return normalized;
  }, [syncHolidayList]);

  // 节日变更后 debounce 700ms 把当条 upsert 到后端,避免拖动每帧都打。
  const upsertTimers = React.useRef({});
  const scheduleUpsert = React.useCallback((merged) => {
    if (!window.api || !window.api.holidayUpsert) return;
    if (merged.isPointOverride) return;  // 单点系数覆盖,前端临时态,不持久化
    const id = merged.id;
    if (upsertTimers.current[id]) clearTimeout(upsertTimers.current[id]);
    upsertTimers.current[id] = setTimeout(() => {
      window.api.holidayUpsert({
        holiday_id: id,
        name: merged.name,
        peak_date: merged.peak,
        days_before: merged.sb,
        days_after: merged.sa,
        sales_multiplier: merged.mult ?? merged.dm ?? 1,
        color: merged.color || null,
        flag: merged.flag || null,
        country_code: merged.countryCode ?? merged.country_code ?? null,
        enabled: true,
      }).catch(err => console.warn('[holidayUpsert]', err.message));
    }, 700);
  }, []);

  const updateHoliday = (id, patch) => {
    setHolidays(prev => {
      const existing = prev.find(h => h.id === id);
      if (!existing) {
        const merged = normalizeHolidayV7({ ...patch, id, __useAbsRange: patch.fromAbs != null || patch.toAbs != null });
        scheduleUpsert(merged);
        return syncHolidayList([...prev, merged]);
      }
      const merged = normalizeHolidayV7({ ...existing, ...patch, __useAbsRange: patch.fromAbs != null || patch.toAbs != null });
      scheduleUpsert(merged);
      return syncHolidayList(prev.map(h => h.id === id ? merged : h));
    });
  };

  const saveHoliday = React.useCallback(async (draft) => {
    const normalized = normalizeHolidayV7(draft);
    commitHolidayList([
      ...holidays.filter(h => h.id !== normalized.id),
      normalized,
    ]);

    if (!window.api || !window.api.holidayUpsert) return normalized;
    try {
      const resp = await window.api.holidayUpsert({
        holiday_id: normalized.id,
        name: normalized.name,
        peak_date: normalized.peak,
        days_before: normalized.sb,
        days_after: normalized.sa,
        sales_multiplier: normalized.mult,
        color: normalized.color || null,
        flag: normalized.flag || null,
        country_code: normalized.countryCode || null,
        enabled: true,
      });
      const adapted = window.adapter?.adaptHolidays
        ? window.adapter.adaptHolidays({ holidays: [resp] })[0]
        : {
            id: resp.id,
            name: resp.name,
            peak: resp.peak_date,
            sb: resp.days_before,
            sa: resp.days_after,
            dm: resp.sales_multiplier,
            color: resp.color,
            flag: resp.flag,
            countryCode: resp.country_code,
          };
      const saved = normalizeHolidayV7(adapted || normalized);
      commitHolidayList([
        ...holidays.filter(h => h.id !== saved.id),
        saved,
      ]);
      return saved;
    } catch (err) {
      console.warn('[holidayUpsert]', err.message);
      return normalized;
    }
  }, [holidays, commitHolidayList]);

  const deleteHoliday = React.useCallback(async (id) => {
    commitHolidayList(holidays.filter(h => h.id !== id));
    if (!window.api || !window.api.holidayDelete) return;
    try {
      await window.api.holidayDelete({ holiday_id: id });
    } catch (err) {
      console.warn('[holidayDelete]', err.message);
    }
  }, [holidays, commitHolidayList]);

  const handleInvOverride = React.useCallback((absDay, qty) => {
    setInvOverrides(prev => ({ ...prev, [absDay]: qty }));
    if (!window.api || !window.api.skuInventoryOverrideUpsert || !sku.listingId) return;

    const forecastDate = sku.forecastDates?.[absDay - 1] || fmtYMDV7(dateAddV7(TODAY_V7, absDay));
    setInvSaveState({ status: 'saving', absDay });
    window.api.skuInventoryOverrideUpsert({
      listing_id: sku.listingId,
      calc_run_id: sku.calcRunId || null,
      day_offset: absDay,
      forecast_date: forecastDate,
      stock_qty: qty,
      updated_by: 'frontend',
    }).then(() => {
      setInvSaveState({ status: 'saved', absDay });
      setTimeout(() => {
        setInvSaveState(cur => (cur && cur.status === 'saved' && cur.absDay === absDay ? null : cur));
      }, 1800);
    }).catch(err => {
      console.warn('[skuInventoryOverrideUpsert]', err.message);
      setInvSaveState({ status: 'error', absDay, message: err.message || '库存点位保存失败' });
    });
  }, [sku.listingId, sku.calcRunId]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 12 }}>
        <span style={{ fontSize: 11.5, color: 'var(--text-3)', marginRight: 4 }}>时间范围</span>
        {TIME_RANGES_V7.map(r => (
          <button
            key={r.id}
            onClick={() => setRangeId(r.id)}
            className={`btn sm ${rangeId === r.id ? 'primary' : ''}`}
            style={{ fontSize: 11 }}
          >
            {r.label}
          </button>
        ))}
        <span style={{ flex: 1 }}/>
        {(hasAdj || hasInvOvr || pointOvr.length > 0) && (
          <button
            className="btn sm ghost"
            style={{ fontSize: 11, color: 'var(--text-3)' }}
            onClick={() => {
              commitHolidayList(getHolidays());
              setInvOverrides({});
            }}
          >
            重置调整
          </button>
        )}
      </div>

      <TrendChartV7
        sku={sku}
        range={range}
        holidays={holidays}
        onHolidayChange={updateHoliday}
        invOverrides={invOverrides}
        onInvOverride={handleInvOverride}
      />

      <div style={{ display: 'flex', gap: 14, padding: '6px 0 8px', fontSize: 11, color: 'var(--text-3)', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ width: 14, height: 2, background: 'var(--accent)', display: 'inline-block', borderRadius: 1 }}/>
          <span style={{ width: 12, height: 0, borderTop: '2px dashed var(--accent)', display: 'inline-block', opacity: 0.75, marginLeft: 2 }}/>
          销量（左轴）
        </span>
        {!isLastYear && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 16, height: 2, background: 'var(--p3)', display: 'inline-block', borderRadius: 1 }}/>
            库存（右轴）
          </span>
        )}
        {visH.map(h => (
          <span key={h.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: h.color, display: 'inline-block', opacity: .72 }}/>
            {h.name} x{h.mult.toFixed(1)}
          </span>
        ))}
        {pointOvr.length > 0 && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--p3-strong)' }}>
            {pointOvr.length} 处点位调整
          </span>
        )}
        {hasInvOvr && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--accent-text)' }}>
            {Object.keys(invOverrides).length} 处库存修改
          </span>
        )}
        {invSaveState && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            color: invSaveState.status === 'error' ? 'var(--p1-strong)' : 'var(--text-3)',
          }}>
            {invSaveState.status === 'saving'
              ? '库存点位保存中…'
              : invSaveState.status === 'saved'
                ? '库存点位已保存'
                : `库存点位保存失败：${invSaveState.message}`}
          </span>
        )}
        <span style={{ flex: 1 }}/>
        {hasAdj && !isLastYear && (() => {
          const diff = +(adjAvg - sku.futureDaily).toFixed(2);
          const sign = diff > 0 ? '+' : '';
          return (
            <span style={{ fontWeight: 600, color: adjAvg > sku.futureDaily ? 'var(--p3-strong)' : 'var(--p2)', fontSize: 11.5 }}>
              调整后均日销 {(+adjAvg).toFixed(2)} 件（{sign}{diff}）
            </span>
          );
        })()}
      </div>

      <div style={{ height: 1, background: 'var(--border)', margin: '0 0 12px' }}/>

      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-4)', flexWrap: 'wrap', marginBottom: 12 }}>
        <span>节日色带自动显示，<strong style={{ color: 'var(--text-3)' }}>拖动边缘</strong>调整范围，<strong style={{ color: 'var(--text-3)' }}>点击色带</strong>修改系数</span>
        <span><strong style={{ color: 'var(--text-3)' }}>点击预测蓝线</strong>修改该天系数</span>
        <span><strong style={{ color: 'var(--text-3)' }}>点击预测绿线</strong>修改该天库存</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <KV k="近 7 天日销（原始）" v={sku.last7Daily}/>
        <KV k="近 7 天日销（去噪）" v={sku.last7Denoised}/>
        <KV k="未来平均日销" v={hasAdj && !isLastYear ? `${(+adjAvg).toFixed(2)} (调后)` : (+sku.futureDaily).toFixed(2)}/>
        <KV k="未来 14 天合计" v={fmt.num(forecast.slice(0, 14).reduce((sum, item) => sum + item.value, 0))}/>
      </div>
    </div>
  );
}

function defaultHolidayDraftV7() {
  const start = fmtYMDV7(dateAddV7(TODAY_V7, 14));
  const end = fmtYMDV7(dateAddV7(TODAY_V7, 17));
  return normalizeHolidayV7({
    id: `custom-holiday-${Date.now()}`,
    name: '',
    flag: '🎯',
    peak: start,
    sb: 0,
    sa: Math.max(0, dateDiffV7(holidayPeakDateV7(start), holidayPeakDateV7(end))),
    mult: 1.3,
    color: HOLIDAY_COLORS_V7[0],
    countryCode: '',
  });
}

function holidayStartYMDV7(h) {
  const peak = holidayPeakDateV7(h.peak || h.peak_date);
  if (!peak) return '';
  return fmtYMDV7(dateAddV7(peak, -Math.max(0, Number(h.sb ?? h.days_before ?? 0) || 0)));
}

function holidayEndYMDV7(h) {
  const peak = holidayPeakDateV7(h.peak || h.peak_date);
  if (!peak) return '';
  return fmtYMDV7(dateAddV7(peak, Math.max(0, Number(h.sa ?? h.days_after ?? 0) || 0)));
}

function holidayRangePatchV7(startYmd, endYmd) {
  const start = holidayPeakDateV7(startYmd);
  const end = holidayPeakDateV7(endYmd);
  if (!start || !end) return null;
  const safeEnd = end < start ? start : end;
  return {
    peak: fmtYMDV7(start),
    sb: 0,
    sa: Math.max(0, dateDiffV7(start, safeEnd)),
  };
}

function HolidayManagerModal({ holidays, onClose, onSave, onDelete }) {
  const [editingId, setEditingId] = React.useState(null);
  const [form, setForm] = React.useState(() => defaultHolidayDraftV7());
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const sorted = normalizeHolidayListV7(holidays);

  const startCreate = () => {
    setEditingId(null);
    setForm(defaultHolidayDraftV7());
    setError('');
  };

  const startEdit = (h) => {
    const next = normalizeHolidayV7(h);
    setEditingId(next.id);
    setForm(next);
    setError('');
  };

  const setField = (key, value) => {
    setForm(prev => normalizeHolidayV7({ ...prev, [key]: value }));
  };

  const setRange = (key, value) => {
    setForm(prev => {
      const curStart = holidayStartYMDV7(prev);
      const curEnd = holidayEndYMDV7(prev);
      const patch = holidayRangePatchV7(
        key === 'start' ? value : curStart,
        key === 'end' ? value : curEnd
      );
      return patch ? normalizeHolidayV7({ ...prev, ...patch }) : prev;
    });
  };

  const validate = () => {
    if (!form.name.trim()) return '请填写节日名称';
    if (!holidayStartYMDV7(form) || !holidayEndYMDV7(form)) return '请选择有效节日时间';
    if (Number(form.mult) <= 0) return '销量系数必须大于 0';
    return '';
  };

  const submit = async () => {
    const msg = validate();
    if (msg) {
      setError(msg);
      return;
    }
    setSaving(true);
    setError('');
    try {
      await onSave(normalizeHolidayV7({
        ...form,
        id: editingId || form.id,
        name: form.name.trim(),
        countryCode: form.countryCode || null,
      }));
      startCreate();
    } catch (err) {
      setError(err.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (h) => {
    setSaving(true);
    setError('');
    try {
      await onDelete(h.id);
      if (editingId === h.id) startCreate();
    } catch (err) {
      setError(err.message || '删除失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={true} onClose={onClose} width={920}>
      <div style={{ padding: '16px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div className="h3">节日信息管理</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 3 }}>
            创建或调整节日窗口后，会立即参与当前 SKU 趋势计算，并进入工作台大促提醒。
          </div>
        </div>
        <button className="btn sm" onClick={startCreate}><Icon name="plus" size={12}/>新建节日</button>
        <button className="btn ghost icon sm" onClick={onClose}><Icon name="x" size={14}/></button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(420px, 1fr) 340px', minHeight: 460, maxHeight: 'calc(100vh - 150px)' }}>
        <div style={{ overflow: 'auto', borderRight: '1px solid var(--border)' }}>
          <table className="t" style={{ minWidth: 0 }}>
            <thead>
              <tr>
                <th>节日</th>
                <th>节日时间</th>
                <th className="num">系数</th>
                <th style={{ width: 92 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(h => (
                <tr key={h.id} className={editingId === h.id ? 'selected' : ''}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 10, height: 10, borderRadius: 2, background: h.color, display: 'inline-block' }}/>
                      <span>{h.flag}</span>
                      <span style={{ fontWeight: 500 }}>{h.name}</span>
                    </div>
                  </td>
                  <td className="tabular">{holidayStartYMDV7(h)} 至 {holidayEndYMDV7(h)}</td>
                  <td className="num tabular">x{Number(h.mult).toFixed(2)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn ghost icon sm" title="编辑" onClick={() => startEdit(h)}><Icon name="edit" size={12}/></button>
                      <button className="btn ghost icon sm" title="删除" onClick={() => remove(h)}><Icon name="trash" size={12}/></button>
                    </div>
                  </td>
                </tr>
              ))}
              {!sorted.length && (
                <tr><td colSpan="4" style={{ color: 'var(--text-3)', textAlign: 'center', padding: 28 }}>暂无节日配置</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14, overflow: 'auto' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{editingId ? '编辑节日' : '新建节日'}</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 3 }}>
              只维护节日明细和节日时间；时间范围内预测日销会乘以节日系数。
            </div>
          </div>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
            <span style={{ color: 'var(--text-3)' }}>节日名称</span>
            <input data-testid="holiday-name" className="txt" value={form.name} placeholder="例如 Prime Day 第二波"
              onChange={e => setField('name', e.target.value)}/>
          </label>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
              <span style={{ color: 'var(--text-3)' }}>开始时间</span>
              <DatePicker
                value={holidayStartYMDV7(form)}
                onChange={(value) => setRange('start', value)}
                placeholder="开始日期"
                title="开始时间"
                testId="holiday-start"
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
              <span style={{ color: 'var(--text-3)' }}>结束时间</span>
              <DatePicker
                value={holidayEndYMDV7(form)}
                onChange={(value) => setRange('end', value)}
                placeholder="结束日期"
                title="结束时间"
                testId="holiday-end"
              />
            </label>
          </div>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
            <span style={{ color: 'var(--text-3)' }}>销量系数</span>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input data-testid="holiday-mult-range" type="range" min={0.1} max={4} step={0.05} value={form.mult}
                onChange={e => setField('mult', e.target.value)}
                style={{ flex: 1, accentColor: 'var(--accent)' }}/>
              <input data-testid="holiday-mult-number" className="txt" type="number" min={0.1} max={4} step={0.05} value={form.mult}
                onChange={e => setField('mult', e.target.value)}
                style={{ width: 88, textAlign: 'right' }}/>
            </div>
          </label>

          {error && <div style={{ color: 'var(--p1-strong)', fontSize: 12 }}>{error}</div>}

          <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'flex-end', gap: 8, paddingTop: 8 }}>
            <button className="btn" onClick={startCreate} disabled={saving}>清空</button>
            <button data-testid="holiday-submit" className="btn primary" onClick={submit} disabled={saving}>
              {saving ? '保存中…' : editingId ? '保存修改' : '创建节日'}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

function TrendChartV7({ sku, range, holidays, onHolidayChange, invOverrides, onInvOverride }) {
  const svgRef = React.useRef(null);
  const [drag, setDrag] = React.useState(null);
  const [tip, setTip] = React.useState(null);
  const [editor, setEditor] = React.useState(null);
  const [edVal, setEdVal] = React.useState('');
  const edRef = React.useRef(null);
  const { histDays, futDays } = range;
  const isLastYear = range.id === 'lastYear';
  const fullHist = React.useMemo(() => {
    const raw = sku.histRaw || [];
    if (histDays <= raw.length) return raw.slice(-histDays);
    return extendHistoryV7(raw, histDays, sku.id.charCodeAt(0));
  }, [sku.id, histDays]);
  const forecast = React.useMemo(
    () => buildStockConstrainedForecastV7(sku.futureDaily, futDays, holidays, sku.totalStock, invOverrides),
    [sku.futureDaily, sku.totalStock, futDays, JSON.stringify(holidays), JSON.stringify(invOverrides)]
  );
  const futVals = forecast.map(f => f.value);
  const invSeries = React.useMemo(
    () => buildInventoryV7(sku.totalStock, futVals, invOverrides),
    [sku.totalStock, JSON.stringify(futVals), JSON.stringify(invOverrides)]
  );
  const W = 960;
  const H = 310;
  const PAD = { t: 32, b: 36, l: 50, r: 20, ra: 58 };
  const cW = W - PAD.l - PAD.r - PAD.ra;
  const cH = H - PAD.t - PAD.b;
  const baseY = PAD.t + cH;
  const histLen = fullHist.length;
  const totalLen = histLen + (isLastYear ? 0 : futDays);
  const sMax = Math.max(...fullHist, ...futVals, 1) * 1.25;
  const iMax = Math.max(...invSeries, sku.totalStock, 1);
  const toX = i => PAD.l + (i / Math.max(1, totalLen - 1)) * cW;
  const toSY = v => PAD.t + cH - (v / sMax) * cH;
  const toIY = v => PAD.t + cH - (v / iMax) * cH;
  const nowX = toX(histLen - 1);
  const xLabels = React.useMemo(() => {
    const step = Math.max(1, Math.round(totalLen / 10));
    const labels = [];
    for (let i = 0; i < totalLen; i += step) {
      const d = i < histLen
        ? dateAddV7(TODAY_V7, -(histLen - 1 - i))
        : dateAddV7(TODAY_V7, i - histLen + 1);
      labels.push({ x: toX(i), label: fmtMDV7(d), isFut: i >= histLen });
    }
    return labels;
  }, [totalLen, histLen, range.id]);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(p => ({
    y: PAD.t + cH * (1 - p),
    sv: Math.round(sMax * p),
    iv: Math.round(iMax * p),
  }));
  const lp = pts => pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join('');
  const ac = (pts, by) => pts.length < 2 ? '' : `${lp(pts)} L${pts[pts.length - 1][0].toFixed(1)},${by} L${pts[0][0].toFixed(1)},${by} Z`;
  const hp = fullHist.map((v, i) => [toX(i), toSY(v)]);
  const fp = futVals.map((v, i) => [toX(histLen - 1 + i), toSY(v)]);
  const ip = invSeries.map((v, i) => [toX(histLen - 1 + i), toIY(v)]);
  const soI = invSeries.findIndex((v, i) => i > 0 && v <= 0);
  const soX = soI > 0 ? toX(histLen - 1 + soI) : null;
  const dRestock = dateDiffV7(TODAY_V7, sku.purchaseDate);
  const rsX = dRestock > 0 && dRestock <= futDays ? toX(histLen - 1 + dRestock) : null;
  const visHolidays = React.useMemo(() => {
    if (isLastYear) return [];
    return holidays.filter(h => h.toAbs > 0 && h.fromAbs < futDays);
  }, [JSON.stringify(holidays), futDays, isLastYear]);
  const xToIdx = clientX => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return 0;
    const mx = (clientX - rect.left) * (W / rect.width);
    return Math.max(0, Math.min(totalLen - 1, Math.round((mx - PAD.l) / (cW / Math.max(1, totalLen - 1)))));
  };
  const idxToAbs = idx => idx - histLen + 1;
  const absToIdx = abs => histLen - 1 + abs;
  const absToX = abs => toX(absToIdx(abs));
  const HANDLE = 8;
  const QUICK_MULT = [0.5, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0];

  const startDrag = (e, type, hid, origFrom, origTo) => {
    e.stopPropagation();
    const idx = xToIdx(e.clientX);
    setDrag({ type, hid, startIdx: idx, origFrom, origTo, pid: e.pointerId });
    svgRef.current?.setPointerCapture?.(e.pointerId);
    setEditor(null);
  };

  const onPtrMove = e => {
    if (drag) {
      const idx = xToIdx(e.clientX);
      const abs = idxToAbs(idx);
      const delta = abs - idxToAbs(drag.startIdx);
      const h = holidays.find(x => x.id === drag.hid);
      if (!h) return;
      if (drag.type === 'band') {
        const span = drag.origTo - drag.origFrom;
        const nf = Math.max(1, drag.origFrom + delta);
        onHolidayChange(drag.hid, { fromAbs: nf, toAbs: nf + span });
      } else if (drag.type === 'left') {
        onHolidayChange(drag.hid, { fromAbs: Math.max(1, Math.min(drag.origTo - 1, drag.origFrom + delta)) });
      } else if (drag.type === 'right') {
        onHolidayChange(drag.hid, { toAbs: Math.min(futDays, Math.max(drag.origFrom + 1, drag.origTo + delta)) });
      }
      return;
    }
    const idx = xToIdx(e.clientX);
    const isFut = idx >= histLen;
    const fi = isFut ? idx - histLen : null;
    const sv = isFut ? (futVals[fi] ?? 0) : fullHist[idx];
    const iv = isFut ? (invSeries[fi] ?? null) : null;
    const dayOff = isFut ? (fi + 1) : -(histLen - 1 - idx);
    const d = dateAddV7(TODAY_V7, dayOff);
    setTip({ x: toX(idx), y: toSY(sv), sv, iv, isFut, fi, absDay: isFut ? fi + 1 : null, d, mult: isFut ? forecast[fi]?.mult : null });
  };

  const onPtrUp = () => {
    if (drag) {
      svgRef.current?.releasePointerCapture?.(drag.pid);
      setDrag(null);
    }
  };

  const handleChartClick = e => {
    if (drag) return;
    const idx = xToIdx(e.clientX);
    if (idx < histLen) return;
    const fi = idx - histLen;
    const absDay = fi + 1;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const clickY = (e.clientY - rect.top) * (H / rect.height);
    const salesY = toSY(futVals[fi] ?? 0);
    const invY = toIY(invSeries[fi] ?? 0);
    const distS = Math.abs(clickY - salesY);
    const distI = Math.abs(clickY - invY);
    const px = (toX(idx) / W) * rect.width + rect.left;
    const py = (Math.min(salesY, invY) / H) * rect.height + rect.top;
    if (distS <= distI + 20) {
      const curMult = forecast[fi]?.mult ?? 1;
      setEditor({ type: 'sales', absDay, fi, x: px, y: py, currentVal: curMult });
      setEdVal(curMult.toFixed(2));
    } else {
      const curInv = invSeries[fi] ?? 0;
      setEditor({ type: 'inv', absDay, fi, x: px, y: py, currentVal: curInv });
      setEdVal(String(curInv));
    }
    setTip(null);
    setTimeout(() => edRef.current?.focus(), 50);
  };

  const commitEdit = () => {
    if (!editor) return;
    if (editor.type === 'sales') {
      const v = parseFloat(edVal);
      if (!isNaN(v) && v > 0) {
        onHolidayChange(`__point_${editor.absDay}`, {
          id: `__point_${editor.absDay}`,
          name: `第${editor.absDay}天调整`,
          flag: '✏️',
          fromAbs: editor.absDay,
          toAbs: editor.absDay,
          mult: v,
          color: v >= 1 ? '#10b981' : '#f59e0b',
          isPointOverride: true,
        });
      }
    } else {
      const v = parseInt(edVal, 10);
      if (!isNaN(v) && v >= 0) onInvOverride(editor.absDay, v);
    }
    setEditor(null);
  };

  return (
    <div style={{ position: 'relative', touchAction: 'none' }}>
      <svg ref={svgRef} width="100%" height={H}
        viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
        style={{ display: 'block', overflow: 'visible', cursor: drag ? 'ew-resize' : 'crosshair' }}
        onPointerMove={onPtrMove}
        onPointerUp={onPtrUp}
        onPointerLeave={() => { if (!drag) setTip(null); }}
        onClick={handleChartClick}
      >
        <defs>
          <linearGradient id="v7sh" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.12"/>
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="v7sf" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.055"/>
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="v7ig" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--p3)" stopOpacity="0.12"/>
            <stop offset="100%" stopColor="var(--p3)" stopOpacity="0.01"/>
          </linearGradient>
          <clipPath id="v7clip"><rect x={PAD.l} y={PAD.t - 4} width={cW} height={cH + 8}/></clipPath>
        </defs>

        {yTicks.slice(1).map(({ y }) => (
          <line key={y} x1={PAD.l} y1={y} x2={PAD.l + cW} y2={y} stroke="var(--border)" strokeDasharray="2 7" strokeWidth="0.7"/>
        ))}
        {yTicks.map(({ y, sv }) => (
          <text key={y} x={PAD.l - 6} y={y + 3.5} fontSize="9" fill="var(--accent)" textAnchor="end" fontFamily="var(--font-mono)" opacity="0.85">{sv}</text>
        ))}
        <text x={14} y={PAD.t + cH / 2} fontSize="9" fill="var(--accent)" textAnchor="middle" transform={`rotate(-90,14,${PAD.t + cH / 2})`} opacity="0.7">日销量</text>
        {!isLastYear && yTicks.map(({ y, iv }) => (
          <text key={y} x={PAD.l + cW + PAD.ra - 4} y={y + 3.5} fontSize="9" fill="var(--p3)" textAnchor="end" fontFamily="var(--font-mono)" opacity="0.8">{iv}</text>
        ))}
        {!isLastYear && (
          <text x={W - 6} y={PAD.t + cH / 2} fontSize="9" fill="var(--p3)" textAnchor="middle" transform={`rotate(90,${W - 6},${PAD.t + cH / 2})`} opacity="0.7">库存量</text>
        )}
        {xLabels.map(({ x, label, isFut }) => (
          <text key={x} x={x} y={H - 8} fontSize="9" fill={isFut ? 'var(--text-3)' : 'var(--text-4)'} textAnchor="middle" fontFamily="var(--font-mono)">{label}</text>
        ))}
        {!isLastYear && (
          <rect x={nowX} y={PAD.t} width={PAD.l + cW - nowX} height={cH} fill="var(--bg-sunken)" opacity="0.38" clipPath="url(#v7clip)"/>
        )}

        <g clipPath="url(#v7clip)">
          {visHolidays.map(h => {
            const x1 = absToX(Math.max(1, h.fromAbs));
            const x2 = absToX(Math.min(futDays, h.toAbs));
            const bw = Math.max(0, x2 - x1);
            if (bw < 2) return null;
            const isPoint = h.isPointOverride;
            const bandLabel = isPoint ? `x${h.mult.toFixed(1)}` : holidayBandLabelV7(h);
            const labelW = Math.min(132, Math.max(44, bandLabel.length * 6.2 + 10));
            const labelX = Math.max(PAD.l + 2, Math.min(x1 + 1, PAD.l + cW - labelW - 2));
            return (
              <g key={h.id}>
                <rect x={x1} y={PAD.t} width={bw} height={cH}
                  fill={h.color + (h.mult >= 1 ? '18' : '14')}
                  style={{ cursor: isPoint ? 'default' : 'grab' }}
                  onPointerDown={isPoint ? undefined : e => startDrag(e, 'band', h.id, h.fromAbs, h.toAbs)}
                />
                {!isPoint && <>
                  <rect x={x1 - HANDLE / 2} y={PAD.t} width={HANDLE} height={cH} fill="transparent" style={{ cursor: 'ew-resize' }} onPointerDown={e => startDrag(e, 'left', h.id, h.fromAbs, h.toAbs)}/>
                  <line x1={x1} y1={PAD.t} x2={x1} y2={PAD.t + cH} stroke={h.color} strokeWidth="1" strokeDasharray="3 3" opacity="0.48"/>
                  <rect x={x2 - HANDLE / 2} y={PAD.t} width={HANDLE} height={cH} fill="transparent" style={{ cursor: 'ew-resize' }} onPointerDown={e => startDrag(e, 'right', h.id, h.fromAbs, h.toAbs)}/>
                  <line x1={x2} y1={PAD.t} x2={x2} y2={PAD.t + cH} stroke={h.color} strokeWidth="1" strokeDasharray="3 3" opacity="0.48"/>
                </>}
                {bw > 16 && (
                  <g style={{ pointerEvents: 'none' }}>
                    <rect x={labelX} y={PAD.t - 1} width={labelW} height={17} rx="3" fill={h.color} opacity="0.58"/>
                    <text x={labelX + 5} y={PAD.t + 12} fontSize="9.5" fill="#fff" fontWeight="600">
                      {bandLabel}
                    </text>
                  </g>
                )}
                {!isPoint && bw > 18 && <>
                  <text x={x1 + 3} y={PAD.t + cH / 2 + 4} fontSize="10" fill={h.color} opacity="0.5" style={{ pointerEvents: 'none' }}>‹</text>
                  <text x={x2 - 10} y={PAD.t + cH / 2 + 4} fontSize="10" fill={h.color} opacity="0.5" style={{ pointerEvents: 'none' }}>›</text>
                </>}
              </g>
            );
          })}

          <path d={ac(hp, baseY)} fill="url(#v7sh)"/>
          <path d={lp(hp)} fill="none" stroke="var(--accent)" strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round"/>
          {!isLastYear && <>
            <path d={ac(fp, baseY)} fill="url(#v7sf)"/>
            <path d={lp(fp)} fill="none" stroke="var(--accent)" strokeWidth="1.65" strokeDasharray="5 3" strokeLinejoin="round" strokeLinecap="round" opacity="0.9"/>
            {futVals.map((v, i) => {
              const m = forecast[i]?.mult;
              if (!m || Math.abs(m - 1) < 0.02) return null;
              return <circle key={i} cx={toX(histLen - 1 + i)} cy={toSY(v)} r="3.3" fill={m > 1 ? 'var(--p3)' : 'var(--p2)'} stroke="var(--surface)" strokeWidth="1.5"/>;
            })}
            {Object.entries(invOverrides).map(([abs, qty]) => {
              const ai = parseInt(abs, 10);
              if (ai < 1 || ai > futDays) return null;
              const ix = toX(histLen - 1 + ai - 1);
              const iy = toIY(qty);
              return (
                <g key={abs}>
                  <circle cx={ix} cy={iy} r="5" fill="var(--accent)" stroke="var(--surface)" strokeWidth="2"/>
                  <text x={ix} y={iy - 8} fontSize="9" fill="var(--accent-text)" textAnchor="middle" fontWeight="600">+{fmt.num(qty)}</text>
                </g>
              );
            })}
            <path d={ac(ip, baseY)} fill="url(#v7ig)"/>
            <path d={lp(ip)} fill="none" stroke="var(--p3)" strokeWidth="1.65" strokeLinejoin="round" strokeLinecap="round" opacity="0.72"/>
          </>}
          {tip && !editor && (
            <>
              <line x1={tip.x} y1={PAD.t} x2={tip.x} y2={PAD.t + cH} stroke="var(--text-3)" strokeWidth="1" opacity="0.28" strokeDasharray="2 2"/>
              <circle cx={tip.x} cy={tip.y} r="4.5" fill="var(--accent)" stroke="var(--surface)" strokeWidth="2"/>
              {tip.iv !== null && <circle cx={tip.x} cy={toIY(tip.iv)} r="4" fill="var(--p3)" stroke="var(--surface)" strokeWidth="2"/>}
            </>
          )}
        </g>

        {!isLastYear && (
          <>
            <line x1={nowX} y1={PAD.t - 8} x2={nowX} y2={PAD.t + cH} stroke="var(--text-3)" strokeWidth="1.2" strokeDasharray="3 2"/>
            <rect x={nowX - 14} y={PAD.t - 21} width={28} height={14} rx="3" fill="var(--surface-2)" stroke="var(--border)"/>
            <text x={nowX} y={PAD.t - 10} fontSize="9" fill="var(--text-3)" textAnchor="middle" fontWeight="600">今日</text>
          </>
        )}
        {soX && (
          <g>
            {/* 把"预计断货"标签放到图表上方（和"今日"同一行），避免与节日色带顶部标签压叠 */}
            <line x1={soX} y1={PAD.t - 8} x2={soX} y2={PAD.t + cH} stroke="var(--p1)" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.85"/>
            <rect x={soX - 22} y={PAD.t - 21} width={44} height={14} rx="3" fill="var(--p1-soft)" stroke="var(--p1)" strokeWidth="0.5" strokeOpacity="0.5"/>
            <text x={soX} y={PAD.t - 10} fontSize="9" fill="var(--p1-strong)" textAnchor="middle" fontWeight="700">预计断货</text>
            <circle cx={soX} cy={PAD.t + cH} r="4" fill="var(--p1)"/>
          </g>
        )}
        {rsX && (
          <g>
            <line x1={rsX} y1={PAD.t} x2={rsX} y2={PAD.t + cH} stroke="var(--p3-strong)" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.7"/>
            <rect x={rsX - 22} y={PAD.t + cH - 18} width={44} height={14} rx="3" fill="var(--p3)" opacity="0.12"/>
            <text x={rsX} y={PAD.t + cH - 7} fontSize="9" fill="var(--p3-strong)" textAnchor="middle" fontWeight="700">建议补货</text>
          </g>
        )}
      </svg>

      {tip && !editor && !drag && (() => {
        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) return null;
        const px = (tip.x / W) * rect.width + rect.left;
        const py = (tip.y / H) * rect.height + rect.top;
        const flip = px > rect.left + rect.width * 0.62;
        return (
          <div style={{
            position: 'fixed', zIndex: 300, pointerEvents: 'none',
            left: flip ? px - 196 : px + 14,
            top: Math.max(8, py - 12),
            background: 'var(--surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--sh-pop)',
            padding: '9px 13px',
            fontSize: 12,
            minWidth: 174,
          }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-3)', marginBottom: 5 }}>
              {fmtYMDV7(tip.d)}
              {tip.isFut && <span style={{ marginLeft: 6, color: 'var(--text-4)' }}>预测</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block', flexShrink: 0 }}/>
              <span style={{ color: 'var(--text-3)', fontSize: 11 }}>日销量</span>
              <span style={{ fontWeight: 700, fontSize: 16, fontVariantNumeric: 'tabular-nums', marginLeft: 'auto' }}>
                {tip.sv}<span style={{ fontWeight: 400, fontSize: 11, color: 'var(--text-3)', marginLeft: 2 }}>件</span>
              </span>
            </div>
            {tip.iv !== null && (
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--p3)', display: 'inline-block', flexShrink: 0 }}/>
                <span style={{ color: 'var(--text-3)', fontSize: 11 }}>预计库存</span>
                <span style={{ fontWeight: 700, fontSize: 16, fontVariantNumeric: 'tabular-nums', marginLeft: 'auto', color: tip.iv < 50 ? 'var(--p1)' : tip.iv < 200 ? 'var(--p2)' : 'var(--p3)' }}>
                  {fmt.num(tip.iv)}<span style={{ fontWeight: 400, fontSize: 11, color: 'var(--text-3)', marginLeft: 2 }}>件</span>
                </span>
              </div>
            )}
            {tip.isFut && tip.mult && Math.abs(tip.mult - 1) >= 0.02 && (
              <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid var(--border)', fontSize: 11, color: tip.mult > 1 ? 'var(--p3-strong)' : 'var(--p2)', display: 'flex', gap: 5 }}>
                <span>节日系数 x{tip.mult.toFixed(2)}</span>
                <span style={{ color: 'var(--text-4)', marginLeft: 'auto' }}>{tip.mult > 1 ? '+' : ''}{Math.round((tip.mult - 1) * 100)}%</span>
              </div>
            )}
            {tip.isFut && <div style={{ marginTop: 4, fontSize: 10, color: 'var(--text-4)' }}>点击可修改</div>}
          </div>
        );
      })()}

      {editor && (() => {
        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) return null;
        const flip = editor.x > rect.left + rect.width * 0.55;
        const isSales = editor.type === 'sales';
        const d = dateAddV7(TODAY_V7, editor.absDay);
        return (
          <div style={{
            position: 'fixed', zIndex: 400,
            left: Math.max(8, flip ? editor.x - 272 : editor.x + 10),
            top: Math.max(8, editor.y - 10),
            background: 'var(--surface)',
            border: `1px solid ${isSales ? 'var(--accent)' : 'var(--p3)'}`,
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--sh-pop)',
            padding: '12px 14px',
            width: 258,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--text)' }}>
                  {isSales ? '修改销量系数' : '修改库存数量'}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 1 }}>
                  {fmtMDV7(d)} · 第 {editor.absDay} 天
                </div>
              </div>
              <button onClick={() => setEditor(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', fontSize: 16, padding: '2px 4px' }}>×</button>
            </div>
            {isSales ? (
              <>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-3)' }}>系数</span>
                    <span style={{ fontSize: 20, fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: parseFloat(edVal) > 1 ? 'var(--p3-strong)' : parseFloat(edVal) < 1 ? 'var(--p2)' : 'var(--text)' }}>
                      x{(parseFloat(edVal) || 1).toFixed(2)}
                      <span style={{ fontSize: 11, marginLeft: 4, fontWeight: 500 }}>
                        ({parseFloat(edVal) > 1 ? '+' : ''}{Math.round(((parseFloat(edVal) || 1) - 1) * 100)}%)
                      </span>
                    </span>
                  </div>
                  <input type="range" min={0.1} max={4.0} step={0.05} value={edVal} onChange={e => setEdVal(e.target.value)} style={{ width: '100%', accentColor: 'var(--accent)' }}/>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9.5, color: 'var(--text-4)', marginTop: 2 }}>
                    <span>x0.1</span><span>x4.0</span>
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {QUICK_MULT.map(v => (
                    <button key={v} onClick={() => setEdVal(String(v))}
                      style={{
                        padding: '2px 8px',
                        fontSize: 11,
                        borderRadius: 'var(--r)',
                        cursor: 'pointer',
                        border: `1px solid ${Math.abs(parseFloat(edVal) - v) < 0.01 ? 'var(--accent)' : 'var(--border)'}`,
                        background: Math.abs(parseFloat(edVal) - v) < 0.01 ? 'var(--accent-soft)' : 'var(--surface)',
                        color: v > 1 ? 'var(--p3-strong)' : v < 1 ? 'var(--p2)' : 'var(--text-3)',
                      }}>
                      {v === 1.0 ? '基准' : `${v > 1 ? '+' : ''}${Math.round((v - 1) * 100)}%`}
                    </button>
                  ))}
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--text-4)' }}>
                  系数作用于该天预测日销，拖动节日色带可批量调整
                </div>
              </>
            ) : (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-3)' }}>设置该天库存数量（件）</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input ref={edRef} className="txt" type="number" min={0} value={edVal}
                      onChange={e => setEdVal(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditor(null); }}
                      style={{ flex: 1, textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontSize: 16, fontWeight: 600 }}/>
                    <span style={{ fontSize: 12, color: 'var(--text-3)' }}>件</span>
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-4)' }}>
                    当前预测：{fmt.num(invSeries[editor.fi] ?? 0)} 件
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {[0, 100, 200, 500, 1000].map(v => (
                    <button key={v} onClick={() => setEdVal(String(v))}
                      style={{ padding: '2px 8px', fontSize: 11, borderRadius: 'var(--r)', cursor: 'pointer', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text-2)' }}>
                      {v === 0 ? '清零' : fmt.num(v)}
                    </button>
                  ))}
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--text-4)' }}>
                  确认后保存库存点位，并从该点重新计算库存趋势
                </div>
              </>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn accent sm" style={{ flex: 1 }} onClick={commitEdit}>确认</button>
              <button className="btn sm" onClick={() => setEditor(null)}>取消</button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

function SKUDetail({ skuId, setRoute, openRules, openCreatePO, openAI, aiOpen, aiMode }) {
  const baseSku = SKUS.find(s => s.id === skuId) || SKUS[0];
  const [enriched, setEnriched] = React.useState(null);
  const [loadingDetail, setLoadingDetail] = React.useState(false);

  // 详情页挂载后拉 /skus/detail + /skus/trends 把历史/预测序列合并进 sku
  React.useEffect(() => {
    if (!baseSku || !window.api || !baseSku.listingId) return;
    let cancelled = false;
    setLoadingDetail(true);
    Promise.all([
      window.api.skuDetail(baseSku.listingId).catch(() => null),
      window.api.skuTrends(baseSku.listingId).catch(() => null),
    ]).then(([detailResp, trendsResp]) => {
      if (cancelled) return;
      if (trendsResp) {
        setEnriched(window.adapter.mergeTrendsIntoSku(baseSku, trendsResp, detailResp));
      }
      setLoadingDetail(false);
    });
    return () => { cancelled = true; };
  }, [skuId, baseSku && baseSku.listingId]);

  const sku = enriched || baseSku;
  const tab = 'overview';
  if (!sku) {
    return <div style={{ padding: 32, color: 'var(--text-3)' }}>加载中…</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', minWidth: 0 }}>
        <div style={{ padding: '24px 32px 48px', maxWidth: 1480, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Breadcrumb */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-3)' }}>
            <button className="btn ghost sm" onClick={() => setRoute({ page: 'list' })} style={{ padding: '0 6px' }}>
              <Icon name="chevron-left" size={13}/>返回列表
            </button>
            <span>·</span>
            <span>备货计划</span>
            <Icon name="chevron-right" size={11}/>
            <span style={{ color: 'var(--text-2)' }}>{sku.msku} · {sku.store}</span>
          </div>

          {/* Header */}
          <header style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <div style={{
              width: 72, height: 72, borderRadius: 8,
              background: 'linear-gradient(180deg, var(--surface-3), var(--surface-2))',
              border: '1px solid var(--border)', flex: 'none',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 11,
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,.04)',
            }}>{sku.msku.slice(-3)}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <h1 className="h1" style={{ margin: 0 }}>{sku.name}</h1>
                <PriorityBadge level={sku.priority} size="md"/>
                <span className="chip">{sku.status}</span>
              </div>
              <div style={{ display: 'flex', gap: 14, fontSize: 12, color: 'var(--text-3)', marginTop: 6, flexWrap: 'wrap' }} className="mono">
                <span>MSKU: <span style={{ color: 'var(--text-2)' }}>{sku.msku}</span></span>
                <span>SKU: <span style={{ color: 'var(--text-2)' }}>{sku.sku}</span></span>
                <span>ASIN: <span style={{ color: 'var(--text-2)' }}>{sku.asin}</span></span>
                <span>FNSKU: <span style={{ color: 'var(--text-2)' }}>{sku.fnsku}</span></span>
              </div>
              <div style={{ display: 'flex', gap: 14, fontSize: 12, color: 'var(--text-3)', marginTop: 4 }}>
                <span>{sku.country.flag} {sku.store} · {sku.country.name}</span>
                <span>负责人：{sku.owner}</span>
                <span>品线：{sku.line}</span>
                <span>分类：{sku.category}</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flex: 'none' }}>
              <button className="btn" onClick={() => openRules({ sku })}><Icon name="settings" size={13}/>规则设置</button>
              <button className="btn primary" onClick={() => openCreatePO([sku.id])}><Icon name="lightning" size={13}/>生成采购计划</button>
            </div>
          </header>

          {/* Risk conclusion banner */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0,
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--sh-inset-top)',
          }}>
            <RiskCellWithExplain sku={sku}/>
            <DetailStat label="预计断货时间" main={fmt.dateLong(sku.stockoutDate)} sub={fmt.rel(sku.stockoutDate) + ' · 仅 FBA 侧'}/>
            <DetailStat label="建议采购量" main={fmt.num(sku.suggestQty) + ' 件'} sub={`覆盖周期需求 ${sku.coverageDemand} − 总库存 ${sku.totalStock}`}/>
            <DetailStat label="建议采购时间" main={fmt.dateLong(sku.purchaseDate)} sub={(() => {
              const r = fmt.rel(sku.purchaseDate);
              const isPast = r.endsWith('天前') || r === '昨天';
              return (isPast ? '' : r + ' · ') + '全链路口径';
            })()} last/>
          </div>

          {/* Key metrics row */}
          <Panel title="关键指标" sub="所有口径基于 MSKU + 店铺 计算">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 16 }}>
              <KV k="总库存" v={fmt.num(sku.totalStock)}/>
              <KV k="FBA 库存" v={fmt.num(sku.fbaAvail + sku.fbaInTransit)} hint="FBA 可用 + 在途"/>
              <KV k="本地库存" v={fmt.num(sku.localTotal)} hint="本地实际 + 本地预计"/>
              <KV k="未来平均日销" v={(+sku.futureDaily).toFixed(2)}/>
              <KV k="可售天数" v={(+sku.sellable).toFixed(2) + ' 天'} hint="总库存 ÷ 未来平均日销"/>
              <KV k="采购时效" v={sku.purchaseLeadTime + ' 天'}/>
              <KV k="安全天数" v={sku.safeDays + ' 天'}/>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
              <KV
                k="上次发货"
                v={sku.lastShipmentAt ? fmt.dateLong(sku.lastShipmentAt) : '—'}
                hint={sku.lastShipmentAt ? fmt.rel(sku.lastShipmentAt) + ' · rl_fba_shipment_item' : '暂无 FBA 发货记录'}/>
              <KV
                k="上次采购"
                v={sku.lastPurchaseAt ? fmt.dateLong(sku.lastPurchaseAt) : '—'}
                hint={sku.lastPurchaseAt ? fmt.rel(sku.lastPurchaseAt) + ' · 来自采购计划' : '暂无采购记录'}/>
              <KV
                k="预计到货"
                v={sku.estimatedArrivalAt ? fmt.dateLong(sku.estimatedArrivalAt) : '—'}
                hint={sku.estimatedArrivalAt
                  ? fmt.rel(sku.estimatedArrivalAt) + ' · 取最早一笔在途'
                  : '暂无在途货件'}/>
            </div>
          </Panel>

          {/* Trend chart */}
          <Panel
            title="销量 & 库存趋势"
            sub="节日色带自动显示 · 点击蓝线改系数 · 点击绿线改库存 · 拖动边缘调范围"
          >
            <TrendPanelV7 sku={sku}/>
          </Panel>

          {/* Inventory composition */}
          <Panel title="库存构成">
            <div style={{ marginBottom: 14 }}>
              <StackedBar segments={[
                { label: 'FBA 可用', value: sku.fbaAvail, color: 'var(--accent)' },
                { label: 'FBA 在途', value: sku.fbaInTransit, color: 'oklch(0.78 0.12 240)' },
                { label: '本地实际', value: sku.localActual, color: 'var(--p3)' },
                { label: '本地预计', value: sku.localPlan, color: 'oklch(0.85 0.05 160)' },
              ]} height={10}/>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
              <InvItem color="var(--accent)" label="FBA 可用" value={sku.fbaAvail} note="平台立即可发货"/>
              <InvItem color="oklch(0.78 0.12 240)" label="FBA 在途" value={sku.fbaInTransit} note="入库中 / 转运中" expandable inboundList={sku.inboundList}/>
              <InvItem color="var(--p3)" label="本地实际" value={sku.localActual} note="本地仓现货"/>
              <InvItem color="oklch(0.85 0.05 160)" label="本地预计" value={sku.localPlan} note="待入库 / 计划入库"/>
            </div>
          </Panel>

          {/* Current rule */}
          <Panel
            title="当前规则"
            right={<button className="btn sm" onClick={() => openRules({ sku })}><Icon name="edit" size={12}/>修改规则</button>}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', background: 'var(--surface-2)', borderRadius: 'var(--r)', marginBottom: 10 }}>
              <Icon name="info" size={14} color="var(--accent)"/>
              <span style={{ fontSize: 12.5 }}>该 MSKU + 店铺已配置 <strong>特配规则</strong>，覆盖全局规则。</span>
              <span style={{ flex: 1 }}/>
              <span className="chip" style={{ background: 'var(--accent-soft)', color: 'var(--accent-text)', borderColor: 'transparent' }}>特配</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              <KV k="安全天数" v={sku.safeDays + ' 天'}/>
              <KV k="采购时长" v={sku.purchaseDuration + ' 天'}/>
              <KV k="采购交期" v={sku.purchaseDelivery + ' 天'}/>
              <KV k="质检时长" v={sku.qcDays + ' 天'}/>
              <KV k="物流方式" v={sku.logistics.mode + ' · ' + sku.logistics.days + 'd'}/>
              <KV k="销量预测" v="动态销量 (近 7d)"/>
              <KV k="排除异常" v="否"/>
              <KV k="固定日销" v="未设置"/>
            </div>
          </Panel>
        </div>
      </div>

      {/* SKU AI panel — split mode shows it inline */}
      {aiOpen && aiMode === 'split' && (
        <div style={{ width: 420, flex: 'none', borderLeft: '1px solid var(--border)', background: 'var(--bg-sunken)' }}>
          <SKUAIPanel sku={sku} onClose={() => openAI(false)} mode="split"/>
        </div>
      )}
    </div>
  );
}

function RiskCellWithExplain({ sku }) {
  const [open, setOpen] = React.useState(false);
  const label = sku.priority === 'p1' ? '紧急'
    : sku.priority === 'p2' ? '重要'
    : sku.priority === 'p3' ? '关注' : '安全';
  const strong = sku.priority === 'p1' ? 'var(--p1-strong)'
    : sku.priority === 'p2' ? 'var(--p2-strong)' : 'var(--text)';
  const bg = sku.priority === 'p1' ? 'linear-gradient(180deg, rgba(249,112,102,.12), rgba(249,112,102,.06))'
    : sku.priority === 'p2' ? 'linear-gradient(180deg, rgba(253,186,116,.12), rgba(253,186,116,.055))' : 'var(--surface-2)';

  // round corners on first cell of the banner
  return (
    <div
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      style={{
        position: 'relative',
        padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 4,
        background: bg, borderRight: '1px solid var(--border)',
        borderTopLeftRadius: 'var(--r-md)', borderBottomLeftRadius: 'var(--r-md)',
        cursor: 'help',
      }}
    >
      <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 4 }}>
        风险等级
        <Icon name="info" size={11} color="var(--text-4)"/>
      </div>
      <div style={{ fontSize: 22, fontWeight: 600, color: strong }}>
        {sku.priority.toUpperCase()} · {label}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
        FBA 可售 {(+sku.fbaSellable).toFixed(2)} 天 · 阈值 P1 ≤ 7d
        <span style={{ color: 'var(--text-4)', marginLeft: 6 }}>查看计算</span>
      </div>

      {open && (
        <div
          role="tooltip"
          style={{
            position: 'absolute', zIndex: 100,
            top: 'calc(100% + 8px)', left: 0,
            width: 460, maxWidth: 'calc(100vw - 48px)',
            background: 'var(--surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--sh-pop)',
            padding: '12px 14px',
            display: 'flex', flexDirection: 'column', gap: 0,
            cursor: 'default',
            pointerEvents: 'auto',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-3)', fontWeight: 500, marginBottom: 8 }}>
            <Icon name="sparkles" size={12} color="var(--accent)"/>
            计算解释
            <span style={{ color: 'var(--text-4)', fontWeight: 400, marginLeft: 'auto' }}>基于 MSKU + 店铺</span>
          </div>
          <CalcRow k="覆盖周期" v={`${sku.purchaseLeadTime}d + ${sku.safeDays}d = ${sku.totalCoverage}d`}/>
          <CalcRow k="覆盖需求" v={`${sku.totalCoverage}d × ${(+sku.futureDaily).toFixed(2)} = ${(+sku.coverageDemand).toFixed(2)} 件`}/>
          <CalcRow k="总库存" v={`${sku.totalStock} = FBA ${sku.fbaAvail + sku.fbaInTransit} + 本地 ${sku.localTotal}`}/>
          <CalcRow k="建议采购" v={`${sku.coverageDemand} − ${sku.totalStock} = ${fmt.num(sku.suggestQty)} 件`} highlight/>
          <CalcRow k="风险判定" v={`FBA 可售 ${(+sku.fbaSellable).toFixed(2)}d → ${sku.priority.toUpperCase()}（仅 FBA 侧）`}/>
          <CalcRow k="预计断货" v={`今天 + ${(+sku.fbaSellable).toFixed(2)}d = ${fmt.dateLong(sku.stockoutDate)}`}/>
          <CalcRow k="建议采购日" v={`断货 − ${sku.purchaseLeadTime}d = ${fmt.dateLong(sku.purchaseDate)}`} last/>
        </div>
      )}
    </div>
  );
}

function DetailStat({ label, main, sub, hint, last }) {
  return (
    <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 4, borderRight: last ? 'none' : '1px solid var(--border)' }}>
      <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 4 }}>
        {label}{hint && <span title={hint} style={{ cursor: 'help', fontSize: 10 }}>ⓘ</span>}
      </div>
      <div className="tabular" style={{ fontSize: 18, fontWeight: 600 }}>{main}</div>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{sub}</div>
    </div>
  );
}

const LOGISTICS_LABEL = {
  fba_working: 'FBA 计划入库',
  fba_shipped: 'FBA 已发货',
  fba_receiving: 'FBA 入库中',
  sea: '海派', sea_express: '快船', sea_air_express: '空派',
  purchase: '采购', transfer: '调拨', processing: '加工', local_receiving: '本地入库',
  air: '空运',
};

const INBOUND_STATUS_LABEL = {
  in_transit: '在途', receiving: '入库中', pending: '待发',
};

function InvItem({ color, label, value, note, expandable, inboundList }) {
  const [open, setOpen] = React.useState(false);
  const hasList = expandable && inboundList && inboundList.length > 0;
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!open) return;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  return (
    <div ref={ref} style={{ display: 'flex', flexDirection: 'column', gap: 4, position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-3)' }}>
        <span style={{ width: 8, height: 8, borderRadius: 2, background: color }}/>
        {label}
        {hasList && (
          <span
            onClick={() => setOpen(v => !v)}
            style={{
              marginLeft: 'auto', cursor: 'pointer',
              fontSize: 10.5, color: 'var(--accent-text)',
              padding: '1px 5px', borderRadius: 4,
              background: open ? 'var(--accent-soft)' : 'transparent',
            }}>
            {inboundList.length} 笔 {open ? '收起 ▴' : '展开 ▾'}
          </span>
        )}
      </div>
      <div className="tabular" style={{ fontSize: 18, fontWeight: 600 }}>{fmt.num(value)}</div>
      <div style={{ fontSize: 11, color: 'var(--text-4)' }}>{note}</div>
      {hasList && open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0,
          minWidth: 280, zIndex: 50,
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-md)', boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
          padding: 8, fontSize: 11.5,
        }}>
          <div style={{ fontSize: 10.5, color: 'var(--text-4)', marginBottom: 6, padding: '0 4px' }}>
            货件 / 物流方式 / 预计到货
          </div>
          {inboundList.map(b => {
            const mode = LOGISTICS_LABEL[b.inbound_type] || b.inbound_type || '—';
            const status = INBOUND_STATUS_LABEL[b.inbound_status] || b.inbound_status || '';
            const eta = b.expected_arrival_date
              ? new Date(b.expected_arrival_date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
              : '—';
            return (
              <div key={b.inbound_id} style={{
                display: 'grid', gridTemplateColumns: '90px 1fr auto auto',
                gap: 8, padding: '6px 4px', alignItems: 'center',
                borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.04))',
              }}>
                <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.source_order_no || b.inbound_id}</span>
                <span style={{ color: 'var(--text-2)' }}>{mode}{status ? ` · ${status}` : ''}</span>
                <span className="tabular" style={{ color: 'var(--text-2)' }}>{fmt.num(b.qty)} 件</span>
                <span style={{ fontSize: 11, color: 'var(--accent-text)' }}>{eta}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function CalcRow({ k, v, highlight, last }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '7px 0',
      borderBottom: last ? 'none' : '1px solid var(--border)',
      background: highlight ? 'var(--accent-soft)' : 'transparent',
      margin: highlight ? '0 -14px' : '0',
      paddingLeft: highlight ? 14 : 0, paddingRight: highlight ? 14 : 0,
    }}>
      <span style={{ width: 76, fontSize: 11.5, color: 'var(--text-3)', flex: 'none' }}>{k}</span>
      <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: highlight ? 'var(--accent-text)' : 'var(--text-2)', fontWeight: highlight ? 600 : 400, lineHeight: 1.4 }}>
        {v}
      </span>
    </div>
  );
}

Object.assign(window, {
  SKUDetail,
  HolidayManagerModal,
  getHolidays,
  setGlobalHolidaysV7,
  normalizeHolidayV7,
});
