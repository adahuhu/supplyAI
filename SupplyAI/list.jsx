// 备货计划列表页 — full data table with filters, batch ops, column config.

function CopyBtn({ text }) {
  const [copied, setCopied] = React.useState(false);
  if (!text) return null;
  const handleClick = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }).catch(() => {});
  };
  return (
    <button
      onClick={handleClick}
      title={'复制 ' + text}
      style={{
        appearance: 'none', border: 'none', background: 'none', padding: '1px 3px',
        cursor: 'pointer', color: copied ? 'var(--p3-strong)' : 'var(--text-4)',
        fontSize: 10, lineHeight: 1, borderRadius: 3, flexShrink: 0,
      }}
      className={'copy-btn' + (copied ? ' copied' : '')}
    >
      {copied ? '✓' : '⎘'}
    </button>
  );
}

const LIST_SELECTED_BG = 'color-mix(in srgb, var(--accent) 18%, var(--surface))';

const LIST_SORT_ACCESSORS = {
  product: s => s.name || '',
  sku: s => s.sku || '',
  tags: s => (s.tags || []).join(','),
  store: s => s.store || '',
  status: s => s.status || '',
  priority: s => PRIORITY_ORDER[s.priority] ?? 99,
  sales7d: s => s.sales7d ?? (s.recent7 || []).reduce((a, b) => a + b, 0),
  futureDaily: s => s.futureDaily ?? 0,
  revenue7: s => s.revenue7 ?? 0,
  expense7: s => s.expense7 ?? 0,
  cost7: s => s.cost7 ?? 0,
  grossProfit7: s => s.grossProfit7 ?? 0,
  grossMargin: s => s.grossMargin ?? null,
  fbaAvail: s => s.fbaAvail ?? 0,
  fbaInTransit: s => s.fbaInTransit ?? 0,
  localTotal: s => s.localTotal ?? 0,
  localPlan: s => s.localPlan ?? 0,
  totalStock: s => s.totalStock ?? 0,
  sellable: s => s.sellable ?? null,
  stockoutDate: s => s.stockoutDate ? s.stockoutDate.getTime() : null,
  lastShipmentAt: s => s.lastShipmentAt ? s.lastShipmentAt.getTime() : null,
  lastPurchaseAt: s => s.lastPurchaseAt ? s.lastPurchaseAt.getTime() : null,
  purchaseLeadTime: s => s.purchaseLeadTime ?? 0,
  suggest: s => s.suggest ? 1 : 0,
  suggestQty: s => s.suggest ? (s.suggestQty ?? 0) : 0,
  purchaseDate: s => s.purchaseDate ? s.purchaseDate.getTime() : null,
  lastUpdated: s => s.lastUpdated ? s.lastUpdated.getTime() : null,
};

function isStockout7Sku(s) {
  if (s && Array.isArray(s.fbaAvailable7) && s.fbaAvailable7.length >= 7) {
    return s.fbaAvailable7.slice(-7).every(v => Number(v || 0) <= 0);
  }
  return !!s?.stockoutRecent7;
}

function sumBy(rows, fn) {
  return rows.reduce((sum, row) => sum + (Number(fn(row)) || 0), 0);
}

function avgBy(rows, fn) {
  const vals = rows.map(fn).filter(v => v != null && Number.isFinite(Number(v)));
  if (!vals.length) return null;
  return vals.reduce((sum, v) => sum + Number(v), 0) / vals.length;
}

function normalizeTagValue(tag) {
  return String(tag || '').trim();
}

function buildTagFilterOptions(rows) {
  const counts = new Map();
  rows.forEach((s) => {
    (s.tags || []).forEach((tag) => {
      const value = normalizeTagValue(tag);
      if (!value) return;
      counts.set(value, (counts.get(value) || 0) + 1);
    });
  });
  return Array.from(counts.entries())
    .sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0], 'zh-Hans-CN'))
    .map(([value, count]) => ({ value, label: value, count }));
}

function buildValueFilterOptions(rows, getValue, getLabel) {
  const map = new Map();
  rows.forEach((row) => {
    const rawValue = getValue(row);
    if (rawValue == null || rawValue === '') return;
    const value = String(rawValue);
    const label = getLabel ? getLabel(row, value) : value;
    const cur = map.get(value) || { value, label, count: 0 };
    cur.count += 1;
    if (!cur.label && label) cur.label = label;
    map.set(value, cur);
  });
  return Array.from(map.values())
    .sort((a, b) => (b.count - a.count) || String(a.label).localeCompare(String(b.label), 'zh-Hans-CN'));
}

function countRows(rows, predicate) {
  return rows.reduce((sum, row) => sum + (predicate(row) ? 1 : 0), 0);
}

function sellableBucketOf(s) {
  const days = s.sellable ?? 0;
  if (days < 15) return 'lt15';
  if (days <= 60) return '15to60';
  return 'gt60';
}

function TagFilter({ options, selectedValue, onChange }) {
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

  const selected = (options || []).find((o) => o.value === selectedValue);
  const valueText = selected ? `${selected.label} (${selected.count})` : '全部标签';

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button className="btn" type="button" onClick={() => setOpen((v) => !v)} style={{ paddingRight: 8 }}>
        <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>标签</span>
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
            全部标签
          </div>
          {(options || []).length === 0 && (
            <div style={{ padding: '8px 10px', fontSize: 11.5, color: 'var(--text-4)' }}>无标签</div>
          )}
          {(options || []).map((o) => {
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
                <span className="tabular" style={{
                  fontSize: 11, color: active ? 'var(--accent-text)' : 'var(--text-4)',
                  background: active ? 'transparent' : 'var(--surface-hover)',
                  padding: '1px 6px', borderRadius: 999,
                }}>{o.count}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FilterBar({ filter, setFilter, counts }) {
  const segs = [
  { v: 'all', label: '全部', count: counts?.all ?? SKUS.length },
  { v: 'p1', label: 'P1 紧急', count: counts?.p1 ?? 0, color: 'p1' },
  { v: 'p2', label: 'P2 重要', count: counts?.p2 ?? 0, color: 'p2' },
  { v: 'p3', label: 'P3 关注', count: counts?.p3 ?? 0, color: 'p3' },
  { v: 'safe', label: '安全', count: counts?.safe ?? 0, color: 'safe' },
  { v: 'suggest', label: '建议采购', count: counts?.suggest ?? 0 },
  { v: 'stockout7', label: '7 天内断货', count: counts?.stockout7 ?? 0 }];

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

function ListPage({ initialFilter = 'all', initialKeyword = '', initialMallId = null, setRoute, openRules, openCreatePO }) {
  const [filter, setFilter] = React.useState(initialFilter);
  const [keyword, setKeyword] = React.useState(initialKeyword);
  const [sort, setSort] = React.useState({ key: 'priority', dir: 'asc' });
  const [localVersion, bumpLocalVersion] = React.useReducer(x => x + 1, 0);
  // 顶部 + 高级筛选 state
  const [storeFilter, setStoreFilter] = React.useState(initialMallId ? String(initialMallId) : null);     // mall_id 字符串
  const [countryFilter, setCountryFilter] = React.useState(null); // country code
  const [ownerFilter, setOwnerFilter] = React.useState(null);     // owner 名
  const [suggestOnly, setSuggestOnly] = React.useState(null);     // 'yes' | 'no' | null
  const [statusFilter, setStatusFilter] = React.useState(null);   // '在售' | '已下架'
  const [sellableBucket, setSellableBucket] = React.useState(null); // 'lt15'/'15to60'/'gt60'
  const [brandFilter, setBrandFilter] = React.useState(null);
  const [categoryFilter, setCategoryFilter] = React.useState(null);
  const [tagFilter, setTagFilter] = React.useState(null);
  const [selected, setSelected] = React.useState(new Set());
  const [advFilters, setAdvFilters] = React.useState(false);
  const [columnsOpen, setColumnsOpen] = React.useState(false);
  const [bulkForecastOpen, setBulkForecastOpen] = React.useState(false);
  const [bulkForecastMode, setBulkForecastMode] = React.useState('filtered');

  React.useEffect(() => {
    setFilter(initialFilter || 'all');
  }, [initialFilter]);

  React.useEffect(() => {
    setKeyword(initialKeyword || '');
  }, [initialKeyword]);

  React.useEffect(() => {
    setStoreFilter(initialMallId ? String(initialMallId) : null);
  }, [initialMallId]);

  const applyFilters = React.useCallback((sourceRows, opts = {}) => {
    const skip = new Set(opts.skip || []);
    const shouldApply = (name) => !skip.has(name);
    let rows = sourceRows || [];
    if (shouldApply('segment')) {
      if (filter === 'p1') rows = rows.filter((s) => s.priority === 'p1');else
      if (filter === 'p2') rows = rows.filter((s) => s.priority === 'p2');else
      if (filter === 'p3') rows = rows.filter((s) => s.priority === 'p3');else
      if (filter === 'safe') rows = rows.filter((s) => s.priority === 'safe');else
      if (filter === 'suggest') rows = rows.filter((s) => s.suggest);else
      if (filter === 'stockout7') rows = rows.filter(isStockout7Sku);
    }

    if (shouldApply('keyword') && keyword.trim()) {
      const kw = keyword.trim().toLowerCase();
      rows = rows.filter(s =>
        (s.msku || '').toLowerCase().includes(kw)
        || (s.sku || '').toLowerCase().includes(kw)
        || (s.asin || '').toLowerCase().includes(kw)
        || (s.fnsku || '').toLowerCase().includes(kw)
        || (s.name || '').toLowerCase().includes(kw)
        || (s.store || '').toLowerCase().includes(kw)
        || (s.tags || []).some(tag => String(tag).toLowerCase().includes(kw))
      );
    }
    if (shouldApply('store') && storeFilter) rows = rows.filter(s => String(s.mallId) === storeFilter);
    if (shouldApply('country') && countryFilter) rows = rows.filter(s => (s.country?.code || '') === countryFilter);
    if (shouldApply('owner') && ownerFilter) rows = rows.filter(s => s.owner === ownerFilter);
    if (shouldApply('suggestOnly') && suggestOnly === 'yes') rows = rows.filter(s => s.suggest);
    else if (shouldApply('suggestOnly') && suggestOnly === 'no') rows = rows.filter(s => !s.suggest);
    if (shouldApply('status') && statusFilter) rows = rows.filter(s => s.status === statusFilter);
    if (shouldApply('sellable') && sellableBucket) rows = rows.filter(s => sellableBucketOf(s) === sellableBucket);
    if (shouldApply('brand') && brandFilter) rows = rows.filter(s => s.brand === brandFilter);
    if (shouldApply('category') && categoryFilter) rows = rows.filter(s => s.category === categoryFilter);
    if (shouldApply('tag') && tagFilter) {
      const selectedTag = normalizeTagValue(tagFilter);
      rows = rows.filter(s => (s.tags || []).some(tag => normalizeTagValue(tag) === selectedTag));
    }
    return rows;
  }, [filter, keyword, storeFilter, countryFilter, ownerFilter, suggestOnly, statusFilter, sellableBucket, tagFilter, brandFilter, categoryFilter, localVersion]);

  const filtered = React.useMemo(() => applyFilters(SKUS), [applyFilters]);

  const segmentCounts = React.useMemo(() => {
    const rows = applyFilters(SKUS, { skip: ['segment'] });
    return {
      all: rows.length,
      p1: countRows(rows, s => s.priority === 'p1'),
      p2: countRows(rows, s => s.priority === 'p2'),
      p3: countRows(rows, s => s.priority === 'p3'),
      safe: countRows(rows, s => s.priority === 'safe'),
      suggest: countRows(rows, s => s.suggest),
      stockout7: countRows(rows, isStockout7Sku),
    };
  }, [applyFilters]);

  const countryOptions = React.useMemo(
    () => buildValueFilterOptions(
      applyFilters(SKUS, { skip: ['country'] }),
      s => s.country?.code,
      s => `${s.country?.flag || ''} ${s.country?.name || s.country?.code || ''}`.trim()
    ),
    [applyFilters]
  );
  const storeOptions = React.useMemo(
    () => buildValueFilterOptions(applyFilters(SKUS, { skip: ['store'] }), s => s.mallId, s => s.store),
    [applyFilters]
  );
  const ownerOptions = React.useMemo(
    () => buildValueFilterOptions(applyFilters(SKUS, { skip: ['owner'] }), s => s.owner),
    [applyFilters]
  );
  const categoryOptions = React.useMemo(
    () => buildValueFilterOptions(applyFilters(SKUS, { skip: ['category'] }), s => s.category),
    [applyFilters]
  );
  const brandOptions = React.useMemo(
    () => buildValueFilterOptions(applyFilters(SKUS, { skip: ['brand'] }), s => s.brand),
    [applyFilters]
  );
  const tagOptions = React.useMemo(
    () => buildTagFilterOptions(applyFilters(SKUS, { skip: ['tag'] })),
    [applyFilters]
  );
  const suggestOptions = React.useMemo(() => {
    const rows = applyFilters(SKUS, { skip: ['suggestOnly'] });
    return [
      { value: 'yes', label: '建议采购', count: countRows(rows, s => s.suggest) },
      { value: 'no', label: '不建议', count: countRows(rows, s => !s.suggest) },
    ];
  }, [applyFilters]);
  const statusOptions = React.useMemo(() => {
    const rows = applyFilters(SKUS, { skip: ['status'] });
    return [
      { value: '在售', label: '在售', count: countRows(rows, s => s.status === '在售') },
      { value: '已下架', label: '已下架', count: countRows(rows, s => s.status === '已下架') },
    ];
  }, [applyFilters]);
  const sellableOptions = React.useMemo(() => {
    const rows = applyFilters(SKUS, { skip: ['sellable'] });
    return [
      { value: 'lt15', label: '< 15 天', count: countRows(rows, s => sellableBucketOf(s) === 'lt15') },
      { value: '15to60', label: '15-60 天', count: countRows(rows, s => sellableBucketOf(s) === '15to60') },
      { value: 'gt60', label: '> 60 天', count: countRows(rows, s => sellableBucketOf(s) === 'gt60') },
    ];
  }, [applyFilters]);

  const sorted = React.useMemo(() => {
    const rows = [...filtered];
    const getter = LIST_SORT_ACCESSORS[sort.key] || LIST_SORT_ACCESSORS.priority;
    const dir = sort.dir === 'desc' ? -1 : 1;
    rows.sort((a, b) => {
      const av = getter(a);
      const bv = getter(b);
      const aEmpty = av == null || av === '';
      const bEmpty = bv == null || bv === '';
      if (aEmpty && bEmpty) return 0;
      if (aEmpty) return 1;
      if (bEmpty) return -1;
      if (typeof av === 'string' || typeof bv === 'string') {
        return String(av).localeCompare(String(bv), 'zh-Hans-CN') * dir;
      }
      return (Number(av) - Number(bv)) * dir;
    });
    return rows;
  }, [filtered, sort]);

  const selectedRows = React.useMemo(
    () => Array.from(selected).map(id => SKUS.find(s => s.id === id)).filter(Boolean),
    [selected, localVersion]
  );

  const openBulkForecast = React.useCallback((mode = 'filtered') => {
    setBulkForecastMode(mode);
    setBulkForecastOpen(true);
  }, []);

  const applyBulkForecastDaily = React.useCallback(async (rows, nextDaily) => {
    const targets = (rows || []).filter(s => s && s.msku && (s.mall_id != null || s.mallId != null));
    if (!targets.length) throw new Error('当前没有可应用的 SKU');
    if (!window.api || !window.api.forecastRulesUpsert) throw new Error('预测规则接口不可用');

    for (const sku of targets) {
      await window.api.forecastRulesUpsert({
        scope_type: 'sku',
        mall_id: sku.mall_id ?? sku.mallId ?? null,
        msku: sku.msku,
        forecast_mode: 'fixed',
        fixed_daily_sales: nextDaily,
        default_daily_sales: null,
        weight_3d: 0,
        weight_7d: 100,
        weight_15d: 0,
        weight_30d: 0,
        denoise_enabled: false,
        abnormal_dates_json: null,
        abnormal_sales_rule_json: null,
        updated_by: 'frontend_bulk',
      });
    }
    if (window.api.calcRun) await window.api.calcRun();
    targets.forEach(sku => recalcSkuForecastList(sku, nextDaily));
    bumpLocalVersion();
  }, []);

  const totals = React.useMemo(() => ({
    sales7d: sumBy(filtered, s => s.sales7d ?? (s.recent7 || []).reduce((a, b) => a + b, 0)),
    futureDaily: sumBy(filtered, s => s.futureDaily),
    revenue7: sumBy(filtered, s => s.revenue7),
    expense7: sumBy(filtered, s => s.expense7),
    cost7: sumBy(filtered, s => s.cost7),
    grossProfit7: sumBy(filtered, s => s.grossProfit7),
    grossMarginAvg: avgBy(filtered, s => s.grossMargin),
    fbaAvail: sumBy(filtered, s => s.fbaAvail),
    fbaInTransit: sumBy(filtered, s => s.fbaInTransit),
    localTotal: sumBy(filtered, s => s.localTotal),
    localPlan: sumBy(filtered, s => s.localPlan),
    totalStock: sumBy(filtered, s => s.totalStock),
    sellableAvg: avgBy(filtered, s => s.sellable),
    purchaseLeadTimeAvg: avgBy(filtered, s => s.purchaseLeadTime),
    suggestQty: sumBy(filtered, s => s.suggest ? s.suggestQty : 0),
  }), [filtered]);

  const clearAdvFilters = React.useCallback(() => {
    setKeyword('');
    setStoreFilter(null);
    setCountryFilter(null);
    setOwnerFilter(null);
    setSuggestOnly(null);
    setStatusFilter(null);
    setSellableBucket(null);
    setTagFilter(null);
    setBrandFilter(null);
    setCategoryFilter(null);
  }, []);

  const toggleAll = () => {
    if (selected.size === filtered.length) setSelected(new Set());else
    setSelected(new Set(filtered.map((s) => s.id)));
  };
  const toggleOne = (id) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);else next.add(id);
    setSelected(next);
  };

  const setSortKey = (key) => {
    setSort(cur => cur.key === key
      ? { key, dir: cur.dir === 'asc' ? 'desc' : 'asc' }
      : { key, dir: key === 'priority' ? 'asc' : 'desc' }
    );
  };

  const SortTh = ({ id, children, className, style }) => {
    const active = sort.key === id;
    return (
      <th className={className} style={style}>
        <button
          type="button"
          onClick={() => setSortKey(id)}
          title="点击排序"
          style={{
            appearance: 'none',
            border: 0,
            background: 'transparent',
            color: 'inherit',
            font: 'inherit',
            fontWeight: 'inherit',
            padding: 0,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            cursor: 'pointer',
            justifyContent: className === 'num' ? 'flex-end' : 'flex-start',
            width: className === 'num' ? '100%' : 'auto',
          }}>
          <span>{children}</span>
          <span style={{ fontSize: 10, color: active ? 'var(--accent)' : 'var(--text-4)' }}>
            {active ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'}
          </span>
        </button>
      </th>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
     <div style={{ maxWidth: 1480, width: '100%', margin: '0 auto', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>

      {/* Header */}
      <div style={{ padding: '24px 32px 16px', display: 'flex', flexDirection: 'column', gap: 14, flex: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <div>
            <div className="h1">备货计划</div>
            <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 4 }}>粒度：MSKU + 店铺 

            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button className="btn" onClick={() => openRules({})}><Icon name="settings" size={13} />规则中心</button>
          </div>
        </div>

        {/* Filter row 1 */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', width: 280 }}>
            <Icon name="search" size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
            <input className="txt"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="SKU / 品名 / MSKU / FNSKU / ASIN"
              style={{ width: '100%', paddingLeft: 30 }} />
          </div>
          <Filter label="国家"
            options={countryOptions}
            selectedValue={countryFilter}
            onChange={setCountryFilter}/>
          <Filter label="店铺"
            options={storeOptions}
            selectedValue={storeFilter}
            onChange={setStoreFilter}/>
          <Filter label="是否建议采购"
            options={suggestOptions}
            selectedValue={suggestOnly}
            onChange={setSuggestOnly}/>
          <button className="btn ghost" onClick={() => setAdvFilters(!advFilters)} style={{ color: 'var(--accent-text)' }}>
            <Icon name="filter" size={13} />高级筛选 {advFilters ? '收起' : '展开'}
          </button>
          <div style={{ flex: 1 }} />
          <button className="btn" onClick={() => setColumnsOpen(true)}><Icon name="columns" size={13} />列配置</button>
        </div>

        {advFilters &&
        <div className="fade-in" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', padding: '10px 12px', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 'var(--r-md)' }}>
            <Filter label="负责人"
              options={ownerOptions}
              selectedValue={ownerFilter}
              onChange={setOwnerFilter}/>
            <Filter label="分类"
              options={categoryOptions}
              selectedValue={categoryFilter}
              onChange={setCategoryFilter}/>
            <Filter label="品牌"
              options={brandOptions}
              selectedValue={brandFilter}
              onChange={setBrandFilter}/>
            <TagFilter
              options={tagOptions}
              selectedValue={tagFilter}
              onChange={setTagFilter}/>
            <Filter label="状态"
              options={statusOptions}
              selectedValue={statusFilter}
              onChange={setStatusFilter}/>
            <Filter label="可售天数"
              options={sellableOptions}
              selectedValue={sellableBucket}
              onChange={setSellableBucket}/>
            <button className="btn ghost sm" onClick={clearAdvFilters}>清除全部</button>
          </div>
        }
      </div>

      <FilterBar filter={filter} setFilter={setFilter} counts={segmentCounts} />

      {/* Batch action bar — 与 header / 表格水平对齐;flex:none 不挤压表格 */}
      {selected.size > 0 &&
      <div className="fade-in" style={{
        flex: 'none',
        display: 'flex', alignItems: 'center', gap: 10,
        margin: '0 32px 12px',
        padding: '8px 12px',
        background: 'var(--accent-soft)',
        border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)',
        borderRadius: 'var(--r)',
        boxShadow: '0 2px 8px -2px color-mix(in srgb, var(--accent) 35%, transparent)',
      }}>
          <Icon name="check" size={13} color="var(--accent-text)"/>
          <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--accent-text)' }}>已选 {selected.size} 项</span>
          <span style={{ color: 'var(--text-3)', fontSize: 11.5 }}>· 批量生成最多 50 条 · 批量特配最多 200 条</span>
          <div style={{ flex: 1 }} />
          <button className="btn sm" onClick={() => openRules({
            batch: true,
            count: selected.size,
            // 把所选 SKU 详细信息传到 RulesModal,保存时遍历逐个 upsert
            skus: Array.from(selected).map(id => SKUS.find(s => s.id === id)).filter(Boolean),
          })}>
            <Icon name="settings" size={12} />批量规则设置
          </button>
          <button className="btn sm" onClick={() => openBulkForecast('selected')}>
            <Icon name="edit" size={12} />批量预测日销
          </button>
          <button className="btn sm primary" onClick={() => openCreatePO(Array.from(selected))}>
            <Icon name="lightning" size={12} />生成采购计划（{selected.size}）
          </button>
          <button className="btn sm ghost icon" onClick={() => setSelected(new Set())}><Icon name="x" size={13} /></button>
        </div>
      }

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
        <table className="t" style={{ minWidth: 2080 }}>
          <thead>
            <tr>
              <th style={{ width: 36, position: 'sticky', left: 0, background: 'var(--surface)', zIndex: 3, boxShadow: '1px 0 0 var(--border)' }}>
                <input type="checkbox" checked={selected.size === filtered.length && filtered.length > 0} onChange={toggleAll} />
              </th>
	              <SortTh id="product" style={{ position: 'sticky', left: 36, background: 'var(--surface)', zIndex: 3, minWidth: 280, boxShadow: '4px 0 6px -4px rgba(0,0,0,0.35)' }}>商品</SortTh>
	              <SortTh id="sku">SKU</SortTh>
	              <SortTh id="tags">标签</SortTh>
	              <SortTh id="store">店铺/国家</SortTh>
	              <SortTh id="status">状态</SortTh>
	              <SortTh id="priority">风险</SortTh>
	              <SortTh id="sales7d" className="num">近 7 天销量</SortTh>
	              <SortTh id="futureDaily" className="num">预测日销</SortTh>
	              <SortTh id="revenue7" className="num">收入</SortTh>
	              <SortTh id="expense7" className="num">支出</SortTh>
	              <SortTh id="cost7" className="num">成本</SortTh>
	              <SortTh id="grossProfit7" className="num">毛利润</SortTh>
	              <SortTh id="grossMargin" className="num">毛利率</SortTh>
	              <SortTh id="fbaAvail" className="num">FBA 可用</SortTh>
	              <SortTh id="fbaInTransit" className="num">FBA 在途</SortTh>
	              <SortTh id="localTotal" className="num">本地库存</SortTh>
	              <SortTh id="localPlan" className="num">本地在途</SortTh>
	              <SortTh id="totalStock" className="num">总库存</SortTh>
	              <SortTh id="sellable" className="num">可售天数</SortTh>
	              <SortTh id="stockoutDate">预计断货</SortTh>
	              <SortTh id="lastShipmentAt">上次发货</SortTh>
	              <SortTh id="lastPurchaseAt">上次采购</SortTh>
	              <SortTh id="purchaseLeadTime" className="num">采购时效</SortTh>
	              <SortTh id="suggest">建议采购</SortTh>
	              <SortTh id="suggestQty" className="num">建议采购量</SortTh>
	              <SortTh id="purchaseDate">建议采购时间</SortTh>
	              <SortTh id="lastUpdated">最后更新</SortTh>
              <th style={{ position: 'sticky', right: 0, background: 'var(--surface)', zIndex: 3, width: 80 }}>操作</th>
            </tr>
          </thead>
          <tbody>
	            {sorted.map((s) => {
              const sel = selected.has(s.id);
              return (
                <tr key={s.id} className={sel ? 'selected' : ''}
                style={{ cursor: 'pointer' }}
                onClick={() => setRoute({ page: 'sku', skuId: s.id })}>
                  <td style={{ position: 'sticky', left: 0, background: sel ? LIST_SELECTED_BG : 'var(--surface)', zIndex: 1, boxShadow: '1px 0 0 var(--border)' }} onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={sel} onChange={() => toggleOne(s.id)} />
                  </td>
                  <td style={{ position: 'sticky', left: 36, background: sel ? LIST_SELECTED_BG : 'var(--surface)', zIndex: 1, boxShadow: '4px 0 6px -4px rgba(0,0,0,0.35)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, maxWidth: 280 }}>
                      <ProductImage label={s.msku.slice(-3)} size={36} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12.5 }}>{s.name}</div>
                        <div style={{ fontSize: 10.5, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4 }} className="mono">
                          <span>{s.msku}</span><CopyBtn text={s.msku}/>
                          <span style={{ color: 'var(--text-5)' }}>·</span>
                          <span>{s.asin}</span><CopyBtn text={s.asin}/>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 2, color: 'var(--text-2)', fontWeight: 500 }}>
                      <span>{s.sku || '—'}</span><CopyBtn text={s.sku}/>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 2, color: 'var(--text-4)', marginTop: 2, fontSize: 10.5 }}>
                      <span>FNSKU {s.fnsku || '—'}</span><CopyBtn text={s.fnsku}/>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', minWidth: 120, maxWidth: 180 }}>
                      {(s.tags && s.tags.length) ? s.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="chip" style={{ height: 20, fontSize: 10.5, maxWidth: 86, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tag}</span>
                      )) : <span style={{ color: 'var(--text-4)' }}>—</span>}
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
                  <td className="num" onClick={(e) => e.stopPropagation()}>
                    <EditableForecastCell sku={s} onSaved={bumpLocalVersion}/>
                  </td>
                  <td className="num tabular">{fmt.money(s.revenue7)}</td>
                  <td className="num tabular">{fmt.money(s.expense7)}</td>
                  <td className="num tabular">{fmt.money(s.cost7)}</td>
                  <td className="num tabular" style={{ color: (s.grossProfit7 || 0) < 0 ? 'var(--p1)' : 'inherit' }}>{fmt.money(s.grossProfit7)}</td>
                  <td className="num tabular" style={{ color: s.grossMargin < 0 ? 'var(--p1)' : 'inherit' }}>{fmt.pct(s.grossMargin)}</td>
                  <td className="num tabular">{fmt.num(s.fbaAvail)}</td>
                  <td className="num" onClick={(e) => e.stopPropagation()}>
                    <FBAInboundCell sku={s} />
                  </td>
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
                  <td className="tabular muted" style={{ fontSize: 11.5 }}>
                    {s.lastShipmentAt ? fmt.dateLong(s.lastShipmentAt) : <span style={{ color: 'var(--text-4)' }}>—</span>}
                  </td>
                  <td className="tabular muted" style={{ fontSize: 11.5 }}>
                    {s.lastPurchaseAt ? fmt.dateLong(s.lastPurchaseAt) : <span style={{ color: 'var(--text-4)' }}>—</span>}
                  </td>
                  <td className="num tabular muted">{s.purchaseLeadTime}d</td>
                  <td>
                    {s.suggest ? <span className="chip p1" style={{ height: 20, fontSize: 10.5 }}>建议</span> : <span className="chip safe" style={{ height: 20, fontSize: 10.5 }}>无需</span>}
                  </td>
                  <td className="num tabular" style={{ fontWeight: 500 }}>{s.suggest ? fmt.num(s.suggestQty) : '—'}</td>
                  <td className="tabular muted">{s.suggest ? fmt.dateLong(s.purchaseDate) : '—'}</td>
                  <td className="tabular muted" style={{ fontSize: 11 }}>{fmt.time(s.lastUpdated)}</td>
                  <td style={{ position: 'sticky', right: 0, background: sel ? LIST_SELECTED_BG : 'var(--surface)', zIndex: 1 }} onClick={(e) => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: 2 }}>
                      <button className="btn ghost icon sm" title="规则设置" onClick={() => openRules({ sku: s })}><Icon name="settings" size={13} /></button>
                      <button className="btn ghost icon sm" title="生成采购计划" onClick={() => openCreatePO([s.id])}><Icon name="plus" size={13} /></button>
                    </div>
                  </td>
                </tr>);

	            })}
	          </tbody>
	          <tfoot>
	            <tr>
	              <td style={{ position: 'sticky', left: 0, background: 'var(--surface)', zIndex: 2, boxShadow: '1px 0 0 var(--border)' }} />
	              <td style={{ position: 'sticky', left: 36, background: 'var(--surface)', zIndex: 2, fontWeight: 600, boxShadow: '4px 0 6px -4px rgba(0,0,0,0.35)' }}>合计 · {filtered.length}</td>
	              <td />
	              <td />
	              <td />
	              <td />
	              <td />
	              <td className="num tabular">{fmt.num(totals.sales7d)}</td>
	              <td className="num tabular">{fmt.num(+totals.futureDaily.toFixed(2))}</td>
	              <td className="num tabular">{fmt.money(+totals.revenue7.toFixed(2))}</td>
	              <td className="num tabular">{fmt.money(+totals.expense7.toFixed(2))}</td>
	              <td className="num tabular">{fmt.money(+totals.cost7.toFixed(2))}</td>
	              <td className="num tabular">{fmt.money(+totals.grossProfit7.toFixed(2))}</td>
	              <td className="num tabular">{totals.grossMarginAvg == null ? '—' : '均 ' + fmt.pct(totals.grossMarginAvg)}</td>
	              <td className="num tabular">{fmt.num(totals.fbaAvail)}</td>
	              <td className="num tabular">{fmt.num(totals.fbaInTransit)}</td>
	              <td className="num tabular">{fmt.num(totals.localTotal)}</td>
	              <td className="num tabular">{fmt.num(totals.localPlan)}</td>
	              <td className="num tabular">{fmt.num(totals.totalStock)}</td>
	              <td className="num tabular">{totals.sellableAvg == null ? '—' : '均 ' + totals.sellableAvg.toFixed(1) + ' 天'}</td>
	              <td />
	              <td />
	              <td />
	              <td className="num tabular">{totals.purchaseLeadTimeAvg == null ? '—' : '均 ' + totals.purchaseLeadTimeAvg.toFixed(0) + 'd'}</td>
	              <td />
	              <td className="num tabular">{fmt.num(totals.suggestQty)}</td>
	              <td />
	              <td />
	              <td style={{ position: 'sticky', right: 0, background: 'var(--surface)', zIndex: 2 }} />
	            </tr>
	          </tfoot>
	        </table>
      </div>

      {/* Footer / pagination */}
      <div style={{
        flex: 'none',
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 32px',
        borderTop: '1px solid var(--border)',
        background: 'var(--surface)',
        fontSize: 12, color: 'var(--text-3)'
      }}>
        <span>共 {filtered.length} 条</span>
        <span>·</span>
	        <span>已选 {selected.size}</span>
	        <span>·</span>
	        <span>当前排序：{sort.key} {sort.dir === 'asc' ? '升序' : '降序'}</span>
	        <div style={{ flex: 1 }} />
        <span>每页</span>
        <select className="sel" style={{ height: 26, padding: '0 8px' }}><option>50</option><option>100</option></select>
        <button className="btn sm ghost icon" disabled><Icon name="chevron-left" size={13} /></button>
        <span className="tabular">1 / 1</span>
        <button className="btn sm ghost icon" disabled><Icon name="chevron-right" size={13} /></button>
      </div>
     </div>{/* /maxWidth wrapper */}

      {/* Column config drawer */}
      <Drawer open={columnsOpen} onClose={() => setColumnsOpen(false)} width={360} title="列配置">
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="h3">列配置</div>
          <button className="btn ghost icon sm" onClick={() => setColumnsOpen(false)}><Icon name="x" size={14} /></button>
        </div>
        <div style={{ padding: 16, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[
          '商品', 'SKU', '店铺/国家', '状态', '标签', '风险', '近 7 天销量', '预测日销',
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

      <BulkForecastDailyModal
        open={bulkForecastOpen}
        mode={bulkForecastMode}
        rows={bulkForecastMode === 'selected' ? selectedRows : filtered}
        onClose={() => setBulkForecastOpen(false)}
        onApply={applyBulkForecastDaily}
      />
    </div>);

}

function dateAddList(base, days) {
  const d = new Date(base || Date.now());
  d.setDate(d.getDate() + Math.ceil(days || 0));
  return d;
}

function BulkForecastDailyModal({ open, mode, rows, onClose, onApply }) {
  const safeRows = rows || [];
  const rowKey = safeRows.map(s => s.id).join('|');
  const [value, setValue] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    if (!open) return;
    const avg = avgBy(safeRows, s => s.futureDaily);
    setValue(avg == null ? '' : String(+avg.toFixed(2)));
    setErr('');
    setSaving(false);
  }, [open, rowKey, mode]);

  const count = safeRows.length;
  const currentAvg = avgBy(safeRows, s => s.futureDaily);
  const currentTotal = sumBy(safeRows, s => s.futureDaily);
  const next = Number(value);
  const nextValid = Number.isFinite(next) && next >= 0;
  const nextTotal = nextValid ? +(next * count).toFixed(2) : null;
  const title = mode === 'selected' ? '批量设置已选预测日销' : '批量设置筛选结果预测日销';
  const targetText = mode === 'selected'
    ? `将应用到已勾选的 ${count} 个 SKU`
    : `将应用到当前筛选结果的 ${count} 个 SKU`;

  const commit = async () => {
    if (!count) {
      setErr('当前没有可应用的 SKU');
      return;
    }
    if (!nextValid) {
      setErr('请输入大于等于 0 的数字');
      return;
    }
    setSaving(true);
    setErr('');
    try {
      await onApply?.(safeRows, +next.toFixed(2));
      onClose?.();
    } catch (e) {
      setErr(e.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={saving ? undefined : onClose} width={520}>
      <div style={{ padding: '16px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Icon name="edit" size={16} color="var(--accent)"/>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>{title}</div>
          <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 3 }}>{targetText}</div>
        </div>
        <button className="btn ghost icon sm" disabled={saving} onClick={onClose}><Icon name="x" size={14}/></button>
      </div>
      <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
          <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 6, background: 'var(--surface-2)' }}>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>当前数量</div>
            <div className="tabular" style={{ fontWeight: 700, marginTop: 4 }}>{count}</div>
          </div>
          <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 6, background: 'var(--surface-2)' }}>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>当前均值</div>
            <div className="tabular" style={{ fontWeight: 700, marginTop: 4 }}>{currentAvg == null ? '—' : currentAvg.toFixed(2)}</div>
          </div>
          <div style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 6, background: 'var(--surface-2)' }}>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>当前合计</div>
            <div className="tabular" style={{ fontWeight: 700, marginTop: 4 }}>{fmt.num(+currentTotal.toFixed(2))}</div>
          </div>
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-2)', fontWeight: 600 }}>新的预测日销</span>
          <input
            className="txt"
            autoFocus
            type="number"
            min="0"
            step="0.01"
            value={value}
            disabled={saving}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commit();
              if (e.key === 'Escape' && !saving) onClose?.();
            }}
            placeholder="例如 12.5"
            style={{ height: 38, fontSize: 14 }}
          />
        </label>

        <div style={{ padding: '10px 12px', border: '1px solid color-mix(in srgb, var(--accent) 25%, transparent)', background: 'var(--accent-soft)', borderRadius: 6, color: 'var(--accent-text)', fontSize: 12, lineHeight: 1.6 }}>
          保存后会同步重算当前列表里的可售天数、风险等级、建议采购量和合计数据。
          {nextTotal != null && <span className="tabular"> 新预测日销合计：{fmt.num(nextTotal)}</span>}
        </div>

        {err && (
          <div style={{ color: 'var(--p1)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Icon name="alert" size={13}/>{err}
          </div>
        )}
      </div>
      <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
        <button className="btn" disabled={saving} onClick={onClose}>取消</button>
        <button className="btn primary" disabled={saving || !count || !nextValid} onClick={commit}>
          {saving ? '保存中...' : `保存并重算（${count}）`}
        </button>
      </div>
    </Modal>
  );
}

function recalcSkuForecastList(sku, nextDaily) {
  const daily = Math.max(0, Number(nextDaily) || 0);
  sku.futureDaily = +daily.toFixed(2);
  sku.coverageDemand = +(sku.totalCoverage * daily).toFixed(2);
  const planningStock = sku.planningStock ?? sku.fbaAvail ?? 0;
  sku.sellable = daily > 0 ? +(planningStock / daily).toFixed(2) : 0;
  sku.fbaSellable = daily > 0 ? +((sku.fbaAvail + sku.fbaInTransit) / daily).toFixed(2) : 0;
  sku.localSellable = daily > 0 ? +((sku.localTotal || 0) / daily).toFixed(2) : 0;
  sku.suggestQty = Math.max(0, Math.ceil(sku.coverageDemand - planningStock));
  sku.suggest = sku.suggestQty > 0;
  const asOf = DASH_STATS.asOf || new Date();
  sku.stockoutDate = daily > 0 ? dateAddList(asOf, sku.fbaSellable) : null;
  sku.purchaseDate = sku.stockoutDate ? dateAddList(sku.stockoutDate, -(sku.purchaseLeadTime || 0)) : null;
  sku.priority = sku.fbaSellable <= 7 ? 'p1'
    : sku.fbaSellable <= 15 ? 'p2'
    : sku.fbaSellable <= 30 ? 'p3'
    : 'safe';
  sku.lastUpdated = new Date();
}

function EditableForecastCell({ sku, onSaved }) {
  const [editing, setEditing] = React.useState(false);
  const [value, setValue] = React.useState(String(sku.futureDaily ?? 0));
  const [saving, setSaving] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    if (!editing) setValue(String(sku.futureDaily ?? 0));
  }, [sku.futureDaily, editing]);

  const commit = async () => {
    const next = Number(value);
    if (!Number.isFinite(next) || next < 0) {
      setErr('请输入有效数字');
      return;
    }
    const prev = { ...sku };
    recalcSkuForecastList(sku, next);
    onSaved?.();
    setSaving(true);
    setErr('');
    try {
      if (window.api && window.api.forecastRulesUpsert) {
        await window.api.forecastRulesUpsert({
          scope_type: 'sku',
          mall_id: sku.mall_id ?? sku.mallId ?? null,
          msku: sku.msku,
          forecast_mode: 'fixed',
          fixed_daily_sales: next,
          default_daily_sales: null,
          weight_3d: 0,
          weight_7d: 100,
          weight_15d: 0,
          weight_30d: 0,
          denoise_enabled: false,
          abnormal_dates_json: null,
          abnormal_sales_rule_json: null,
          updated_by: 'frontend',
        });
        if (window.api.calcRun) await window.api.calcRun();
      }
      setEditing(false);
    } catch (e) {
      Object.assign(sku, prev);
      setErr(e.message || '保存失败');
      onSaved?.();
    } finally {
      setSaving(false);
    }
  };

  if (!editing) {
    return (
      <button
        className="btn ghost"
        title="点击修改预测日销"
        onClick={() => setEditing(true)}
        style={{ height: 24, padding: '0 7px', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}
      >
        {(+sku.futureDaily).toFixed(2)}
        <Icon name="edit" size={10} color="var(--text-4)"/>
      </button>
    );
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, position: 'relative' }}>
      <input
        className="txt"
        type="number"
        min="0"
        step="0.01"
        value={value}
        disabled={saving}
        autoFocus
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter') commit();
          if (e.key === 'Escape') { setEditing(false); setErr(''); }
        }}
        style={{ width: 76, height: 24, padding: '0 6px', textAlign: 'right', fontSize: 12 }}
      />
      <button className="btn ghost icon sm" title="保存" onClick={commit} disabled={saving}>
        <Icon name={saving ? 'refresh' : 'check'} size={11}/>
      </button>
      <button className="btn ghost icon sm" title="取消" onClick={() => { setEditing(false); setErr(''); }} disabled={saving}>
        <Icon name="x" size={11}/>
      </button>
      {err && (
        <span style={{
          position: 'absolute', right: 0, top: 'calc(100% + 4px)', zIndex: 40,
          background: 'var(--surface)', color: 'var(--p1)', border: '1px solid var(--border)',
          borderRadius: 4, padding: '4px 6px', fontSize: 10.5, whiteSpace: 'nowrap',
        }}>{err}</span>
      )}
    </div>
  );
}

// FBAInboundCell — 点击 FBA 在途数字弹出 popover,懒加载 inbound_list
// 字段:shipment_id / 物流方式 / 数量 / 预计到货
function FBAInboundCell({ sku }) {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [details, setDetails] = React.useState(null);
  const [err, setErr] = React.useState('');

  const total = sku.fbaInTransit || 0;

  const load = async () => {
    if (details || loading || !window.api) return;
    setLoading(true);
    setErr('');
    try {
      const resp = await window.api.skuDetail(sku.listingId);
      setDetails(resp.inbound_list || []);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (open) load();
  }, [open]);

  if (total === 0) {
    return <span className="tabular muted" style={{ color: 'var(--text-4)' }}>0</span>;
  }

  return (
    <span style={{ position: 'relative', display: 'inline-flex' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(v => !v); }}
        className="btn ghost"
        style={{
          height: 22, padding: '0 8px',
          fontSize: 12.5, fontVariantNumeric: 'tabular-nums',
          fontWeight: 500,
          borderColor: 'var(--border)',
          color: 'var(--text-2)',
          cursor: 'pointer',
        }}
        title="点击查看在途明细"
      >
        {total}
        <Icon name="chevron-down" size={11} color="var(--text-3)"/>
      </button>
      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 60 }}/>
          <div onClick={(e) => e.stopPropagation()} style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            zIndex: 70,
            minWidth: 360,
            background: 'var(--surface)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--r-md)',
            boxShadow: '0 12px 32px -6px rgba(0,0,0,0.28)',
            padding: 10,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 6px 8px', borderBottom: '1px solid var(--border)' }}>
              <Icon name="package" size={12} color="var(--accent)"/>
              <div style={{ fontSize: 11.5, fontWeight: 500 }}>FBA 在途明细</div>
              <div style={{ flex: 1 }}/>
              <span className="tabular" style={{ fontSize: 11, color: 'var(--text-3)' }}>共 {total} 件</span>
            </div>
            <div style={{ maxHeight: 280, overflow: 'auto', marginTop: 6 }}>
              {loading && (
                <div style={{ padding: 16, textAlign: 'center', fontSize: 11.5, color: 'var(--text-3)' }}>
                  加载中…
                </div>
              )}
              {err && (
                <div style={{ padding: 12, fontSize: 11.5, color: 'var(--p1)' }}>{err}</div>
              )}
              {!loading && !err && details && details.length === 0 && (
                <div style={{ padding: 16, textAlign: 'center', fontSize: 11.5, color: 'var(--text-4)' }}>
                  暂无在途明细
                </div>
              )}
              {!loading && !err && details && details.length > 0 && (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}>
                  <thead>
                    <tr style={{ background: 'var(--surface-2)' }}>
                      <th style={{ textAlign: 'left', padding: '4px 6px', fontWeight: 500, color: 'var(--text-3)' }}>货件 / 发货单</th>
                      <th style={{ textAlign: 'left', padding: '4px 6px', fontWeight: 500, color: 'var(--text-3)' }}>来源</th>
                      <th style={{ textAlign: 'left', padding: '4px 6px', fontWeight: 500, color: 'var(--text-3)' }}>物流方式</th>
                      <th style={{ textAlign: 'right', padding: '4px 6px', fontWeight: 500, color: 'var(--text-3)' }}>数量</th>
                      <th style={{ textAlign: 'left', padding: '4px 6px', fontWeight: 500, color: 'var(--text-3)' }}>预计到货</th>
                    </tr>
                  </thead>
                  <tbody>
                    {details.map((d, i) => {
                      const sourceLabel = INBOUND_TYPE_LABEL[d.inbound_type] || d.inbound_type || '—';
                      const logisticsLabel = d.logistics_type
                        ? (LOGISTICS_TYPE_LABEL[d.logistics_type] || d.logistics_type)
                        : null;
                      return (
                      <tr key={d.inbound_id || i} style={{ borderTop: '1px solid var(--border)' }}>
                        <td style={{ padding: '6px 6px' }}>
                          <div className="mono" style={{ fontSize: 11, fontWeight: 500 }}>{d.inbound_id}</div>
                          {d.source_order_no && d.source_order_no !== d.inbound_id && (
                            <div className="mono" style={{ fontSize: 10, color: 'var(--text-4)' }}>{d.source_order_no}</div>
                          )}
                        </td>
                        <td style={{ padding: '6px 6px', fontSize: 11, color: 'var(--text-3)' }}>
                          {sourceLabel}
                        </td>
                        <td style={{ padding: '6px 6px' }}>
                          {logisticsLabel ? (
                            <span style={{
                              fontSize: 11, padding: '1px 6px', borderRadius: 3,
                              background: 'var(--accent-soft)', color: 'var(--accent-text)',
                              fontWeight: 500,
                            }}>{logisticsLabel}</span>
                          ) : (
                            <span style={{ color: 'var(--text-4)', fontSize: 11 }}>—</span>
                          )}
                        </td>
                        <td className="tabular" style={{ padding: '6px 6px', textAlign: 'right', fontWeight: 500 }}>
                          {d.qty}
                        </td>
                        <td style={{ padding: '6px 6px', color: 'var(--text-2)' }}>
                          {d.expected_arrival_date ? fmt.dateLong(new Date(d.expected_arrival_date)) : '—'}
                        </td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </span>
  );
}

const INBOUND_TYPE_LABEL = {
  fba_working: 'FBA 计划入库',
  fba_shipped: 'FBA 已发货',
  fba_receiving: 'FBA 入库中',
  purchase: '本地采购',
  transfer: '调拨',
  local_receiving: '本地收货',
  processing: '加工中',
};

const LOGISTICS_TYPE_LABEL = {
  sea: '海派',
  sea_express: '快船',
  sea_air_express: '空派',
  air: '空运',
  air_express: '空派快递',
  truck: '陆运',
  express: '快递',
  fba_direct: 'FBA 直发',
};

function SalesTrendCell({ data }) {
  const [open, setOpen] = React.useState(false);
  const arr = data || [];
  const hasData = arr.length > 0 && arr.some(v => v > 0);
  const total = arr.reduce((a, b) => a + b, 0);
  const today = new Date('2026-05-04');
  const max = Math.max(...arr, 1);

  if (!hasData) {
    return (
      <span style={{ fontSize: 11, color: 'var(--text-4)', fontStyle: 'italic' }}>数据不足</span>
    );
  }

  // 趋势图按数据色染色:有上升给 accent,持平/下降给 text-3
  const trendUp = arr.length >= 2 && arr[arr.length - 1] >= arr[0];
  const sparkColor = trendUp ? 'var(--accent)' : 'var(--p2)';

  return (
    <div
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onClick={(e) => e.stopPropagation()}
      style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end', cursor: 'help' }}>
      <Sparkline data={arr} width={72} height={22} color={sparkColor} strokeWidth={1.6} showDots={false}/>
      <span className="tabular" style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{total}</span>
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
