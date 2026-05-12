// 规则设置弹窗 — 补货规则 + 销量预测 两 Tab
// + 采购计划创建确认 modal

function RulesModal({ open, onClose, ctx, showToast }) {
  const [tab, setTab] = React.useState('replenish');
  // 规则类型只保留 global / batch。从单个 SKU 进入时,沿用 batch 写入逻辑,
  // 在适用范围里直接显示当前 MSKU+店铺,不再单列"单个特配" tab。
  const [scope, setScope] = React.useState(ctx?.batch || ctx?.sku ? 'batch' : 'global');
  const [saving, setSaving] = React.useState(false);
  const [computing, setComputing] = React.useState(false);

  // Replenish rule state
  const [safeDays, setSafeDays] = React.useState(14);
  const [purchaseDuration, setPurchaseDuration] = React.useState(12);
  const [purchaseDelivery, setPurchaseDelivery] = React.useState(5);
  const [qcDays, setQcDays] = React.useState(3);
  const [logistics, setLogistics] = React.useState([
    { id: 1, mode: '海运', days: 35 },
    { id: 2, mode: '空运', days: 8 },
  ]);

  // Forecast rule state
  const [forecastMode, setForecastMode] = React.useState('dynamic'); // 'fixed' | 'dynamic' | 'default'
  const [fixedDaily, setFixedDaily] = React.useState('');
  const [defaultDaily, setDefaultDaily] = React.useState(5);
  const [weights, setWeights] = React.useState({ d3: 0, d7: 100, d15: 0, d30: 0 });
  const [excludeDates, setExcludeDates] = React.useState([{ from: '2026-04-15', to: '2026-04-21', reason: 'Prime Day 促销' }]);
  const [excludeAbnormal, setExcludeAbnormal] = React.useState(true);
  // 异常销量阈值规则: 单日销量 > threshold 时,替换为 default
  const [abnormalThreshold, setAbnormalThreshold] = React.useState('');
  const [abnormalDefault, setAbnormalDefault] = React.useState('');

  if (!open) return null;

  const purchaseLeadTime = purchaseDuration + purchaseDelivery + qcDays + Math.max(...logistics.map(l => l.days));
  const totalCoverage = purchaseLeadTime + safeDays;

  const handleSave = async () => {
    setSaving(true);
    try {
      // 构造目标 SKU 列表:
      //   - global:一次 upsert(scope=global, 不带 mall_id+msku)
      //   - 单 SKU 进入:用 ctx.sku 的 mall_id+msku
      //   - 批量进入:遍历 ctx.skus 每个调一次
      const targets = scope === 'global'
        ? [{ scope_type: 'global', mall_id: null, msku: null }]
        : ctx?.batch && ctx.skus && ctx.skus.length
          ? ctx.skus.map(s => ({ scope_type: 'sku', mall_id: s.mall_id ?? null, msku: s.msku ?? null }))
          : ctx?.sku
            ? [{ scope_type: 'sku', mall_id: ctx.sku.mall_id ?? null, msku: ctx.sku.msku ?? null }]
            : null;

      if (!targets || targets.length === 0) {
        throw new Error('未识别到目标 SKU,请先从 SKU 行或列表勾选进入');
      }
      // 校验:scope=sku 时 mall_id+msku 必须齐全(否则后端 422)
      const missing = targets.find(t => t.scope_type === 'sku' && (!t.mall_id || !t.msku));
      if (missing) {
        throw new Error('选中 SKU 缺少 mall_id 或 msku,请刷新列表后重试');
      }

      // 1. 补货规则(批量遍历)
      if (window.api) {
        for (const t of targets) {
          await window.api.rulesUpsert({
            ...t,
            safety_days: safeDays,
            purchase_duration_days: purchaseDuration,
            delivery_days: purchaseDelivery,
            qc_days: qcDays,
            enabled: true,
            updated_by: 'frontend',
          });
        }
      }
      // 2. 销量预测规则
      const abnRule = (abnormalThreshold && abnormalDefault)
        ? { threshold: +abnormalThreshold, default: +abnormalDefault }
        : null;
      if (window.api && window.api.forecastRulesUpsert) {
        for (const t of targets) {
          await window.api.forecastRulesUpsert({
            ...t,
            forecast_mode: forecastMode,
            fixed_daily_sales: forecastMode === 'fixed' && fixedDaily ? +fixedDaily : null,
            default_daily_sales: forecastMode === 'default' ? +defaultDaily : null,
            weight_3d: weights.d3,
            weight_7d: weights.d7,
            weight_15d: weights.d15,
            weight_30d: weights.d30,
            denoise_enabled: !!abnRule,
            abnormal_dates_json: excludeDates.length ? excludeDates : null,
            abnormal_sales_rule_json: abnRule,
            updated_by: 'frontend',
          });
        }
      }
      setSaving(false);
      setComputing(true);
      if (window.api && window.api.calcRun) {
        try { await window.api.calcRun(); } catch (_) { /* 忽略 */ }
      }
      setComputing(false);
      onClose();
      showToast('规则已保存,已重新计算' + (ctx?.batch ? ` · ${targets.length} 个 MSKU` : ''));
    } catch (err) {
      setSaving(false);
      setComputing(false);
      showToast('保存失败:' + err.message);
    }
  };

  return (
    <Modal open={open} onClose={onClose} width={920}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <Icon name="settings" size={16}/>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="h2">规则设置</div>
          {ctx?.sku && (
            <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 2 }}>
              {ctx.sku.msku}{ctx.sku.store ? ` · ${ctx.sku.store}` : ''}
              {ctx.sku.country?.flag ? ` ${ctx.sku.country.flag}` : ''}
            </div>
          )}
          {ctx?.batch && (
            <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 2 }}>
              批量编辑 · 共 {ctx.count || 0} 个 MSKU+店铺
            </div>
          )}
        </div>
        <button className="btn ghost icon" onClick={onClose}><Icon name="x" size={14}/></button>
      </div>

      {/* Scope */}
      <div style={{ padding: '14px 18px', display: 'flex', gap: 16, borderBottom: '1px solid var(--border)', background: 'var(--surface-2)' }}>
        <div style={{ flex: 1 }}>
          <div className="label" style={{ marginBottom: 6 }}>规则类型</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { v: 'global', l: '全局规则', d: '所有 MSKU+店铺默认', enabled: true },
              { v: 'batch',  l: '批量特配', d: '覆盖选中 MSKU+店铺', enabled: !!(ctx?.batch || ctx?.sku), why: '需先从 SKU 行或列表勾选进入' },
            ].map(o => {
              const disabled = !o.enabled;
              return (
                <button
                  key={o.v}
                  onClick={() => { if (!disabled) setScope(o.v); }}
                  disabled={disabled}
                  title={disabled ? o.why : ''}
                  className="btn"
                  style={{
                    borderColor: scope === o.v ? 'var(--accent)' : 'var(--border)',
                    background: scope === o.v ? 'var(--accent-soft)' : 'var(--surface)',
                    color: scope === o.v ? 'var(--accent-text)' : 'var(--text)',
                    flexDirection: 'column', height: 'auto', padding: '8px 12px',
                    alignItems: 'flex-start', gap: 1,
                    opacity: disabled ? 0.45 : 1,
                    cursor: disabled ? 'not-allowed' : 'pointer',
                  }}>
                  <span style={{ fontWeight: 500 }}>{o.l}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{o.d}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div className="label" style={{ marginBottom: 6 }}>适用范围</div>
          <div style={{ padding: '8px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontSize: 12.5 }}>
            {scope === 'global' && '应用于所有未配置特配的 MSKU + 店铺'}
            {scope === 'batch' && (
              ctx?.batch
                ? `已选 ${ctx?.count || 0} 个 MSKU+店铺，本次操作会覆盖已有特配`
                : ctx?.sku
                  ? `${ctx.sku.msku} · ${ctx.sku.store}${ctx.sku.country?.flag ? ' ' + ctx.sku.country.flag : ''}`
                  : '请先从 SKU 行或列表勾选进入'
            )}
          </div>
          {scope === 'batch' && (
            <div style={{ display: 'flex', gap: 6, marginTop: 6, padding: '6px 8px', background: 'var(--p2-soft)', borderRadius: 4, fontSize: 11.5, color: 'var(--p2-strong)' }}>
              <Icon name="alert" size={11}/>批量保存会覆盖已存在的特配规则；本期不支持回退到全局
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 18px' }}>
        {[
          { v: 'replenish', l: '补货规则' },
          { v: 'forecast', l: '销量预测' },
        ].map(t => (
          <button key={t.v} onClick={() => setTab(t.v)} style={{
            appearance: 'none', border: 0, background: 'transparent',
            padding: '12px 16px', fontSize: 13, color: tab === t.v ? 'var(--text)' : 'var(--text-3)',
            fontWeight: tab === t.v ? 600 : 400,
            borderBottom: tab === t.v ? '2px solid var(--accent)' : '2px solid transparent',
            marginBottom: -1, cursor: 'pointer', fontFamily: 'inherit',
          }}>{t.l}</button>
        ))}
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', minHeight: 460, maxHeight: 580 }}>
        {tab === 'replenish' ? (
          <ReplenishTab
            safeDays={safeDays} setSafeDays={setSafeDays}
            purchaseDuration={purchaseDuration} setPurchaseDuration={setPurchaseDuration}
            purchaseDelivery={purchaseDelivery} setPurchaseDelivery={setPurchaseDelivery}
            qcDays={qcDays} setQcDays={setQcDays}
            logistics={logistics} setLogistics={setLogistics}
            purchaseLeadTime={purchaseLeadTime}
            totalCoverage={totalCoverage}
          />
        ) : (
          <ForecastTab
            mode={forecastMode} setMode={setForecastMode}
            fixedDaily={fixedDaily} setFixedDaily={setFixedDaily}
            defaultDaily={defaultDaily} setDefaultDaily={setDefaultDaily}
            weights={weights} setWeights={setWeights}
            excludeDates={excludeDates} setExcludeDates={setExcludeDates}
            abnormalThreshold={abnormalThreshold} setAbnormalThreshold={setAbnormalThreshold}
            abnormalDefault={abnormalDefault} setAbnormalDefault={setAbnormalDefault}
            sku={ctx?.sku}
          />
        )}
      </div>

      {/* Footer */}
      <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>
          {computing ? <span><span className="pulse">●</span> 计算中…</span> : (saving ? '保存中…' : '修改后保存将触发重新计算')}
        </span>
        <div style={{ flex: 1 }}/>
        <button className="btn" onClick={onClose} disabled={saving || computing}>取消</button>
        <button className="btn primary" onClick={handleSave} disabled={saving || computing}>
          {saving ? '保存中…' : computing ? '计算中…' : '保存'}
        </button>
      </div>
    </Modal>
  );
}

function FieldRow({ label, hint, children, suffix }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0' }}>
      <div style={{ width: 110, flex: 'none', fontSize: 12.5, color: 'var(--text-2)' }}>
        {label}
        {hint && <div style={{ fontSize: 10.5, color: 'var(--text-4)', fontWeight: 400 }}>{hint}</div>}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
        {children}
        {suffix && <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{suffix}</span>}
      </div>
    </div>
  );
}

function ReplenishTab({ safeDays, setSafeDays, purchaseDuration, setPurchaseDuration, purchaseDelivery, setPurchaseDelivery, qcDays, setQcDays, logistics, setLogistics, purchaseLeadTime, totalCoverage }) {
  return (
    <>
      <div style={{ flex: 1, padding: 18, overflow: 'auto' }}>
        <div className="label" style={{ marginBottom: 8 }}>时长配置</div>
        <FieldRow label="安全天数" hint="覆盖周期外储备">
          <input className="txt" type="number" value={safeDays} onChange={e => setSafeDays(+e.target.value)} style={{ width: 100 }}/>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>天</span>
        </FieldRow>
        <FieldRow label="采购时长" hint="下单到出厂">
          <input className="txt" type="number" value={purchaseDuration} onChange={e => setPurchaseDuration(+e.target.value)} style={{ width: 100 }}/>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>天</span>
        </FieldRow>
        <FieldRow label="采购交期" hint="工厂到本地仓">
          <input className="txt" type="number" value={purchaseDelivery} onChange={e => setPurchaseDelivery(+e.target.value)} style={{ width: 100 }}/>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>天</span>
        </FieldRow>
        <FieldRow label="质检时长">
          <input className="txt" type="number" value={qcDays} onChange={e => setQcDays(+e.target.value)} style={{ width: 100 }}/>
          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>天</span>
        </FieldRow>

        <div className="divider" style={{ margin: '14px 0' }}/>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div className="label">物流方式</div>
          <button className="btn sm" onClick={() => setLogistics([...logistics, { id: Date.now(), mode: '快船', days: 18 }])}>
            <Icon name="plus" size={11}/>新增
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {logistics.map((l, i) => (
            <div key={l.id} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <select className="sel" value={l.mode} onChange={e => {
                const next = [...logistics]; next[i].mode = e.target.value; setLogistics(next);
              }} style={{ flex: 1 }}>
                {['海运', '空运', '快船', '快递'].filter(m => m === l.mode || !logistics.some(x => x.mode === m)).map(m => <option key={m} value={m}>{m}</option>)}
              </select>
              <input className="txt" type="number" value={l.days}
                onChange={e => { const next = [...logistics]; next[i].days = +e.target.value; setLogistics(next); }}
                style={{ width: 100 }}/>
              <span style={{ fontSize: 12, color: 'var(--text-3)' }}>天</span>
              <button className="btn ghost icon sm" onClick={() => setLogistics(logistics.filter(x => x.id !== l.id))} disabled={logistics.length === 1}>
                <Icon name="trash" size={13}/>
              </button>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <Icon name="info" size={11}/>同一规则下运输方式不可重复 · 计算时永远取最长物流时效
        </div>
      </div>

      {/* Right summary */}
      <div style={{ width: 320, flex: 'none', borderLeft: '1px solid var(--border)', background: 'var(--surface-2)', padding: 18, overflow: 'auto' }}>
        <div className="label" style={{ marginBottom: 10 }}>实时摘要</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <SummaryItem k="采购时效" v={purchaseLeadTime + ' 天'}
            sub={`= 采购 ${purchaseDuration} + 交期 ${purchaseDelivery} + 质检 ${qcDays} + 物流 ${Math.max(...logistics.map(l => l.days))}`}/>
          <SummaryItem k="总覆盖周期" v={totalCoverage + ' 天'} sub={`= 采购时效 ${purchaseLeadTime} + 安全 ${safeDays}`} highlight/>
          <SummaryItem k="安全库存公式" v="未来日销 × 安全天数" mono/>
          <SummaryItem k="库存参与口径" v="FBA 可用 + 在途 + 本地实际 + 本地预计" mono/>
          <SummaryItem k="断货时间口径" v="仅 FBA 侧（不含本地）" mono/>
        </div>
      </div>
    </>
  );
}

function SummaryItem({ k, v, sub, highlight, mono }) {
  return (
    <div style={{
      padding: '10px 12px',
      background: highlight ? 'var(--accent-soft)' : 'var(--surface)',
      border: '1px solid ' + (highlight ? 'var(--accent-soft-2)' : 'var(--border)'),
      borderRadius: 'var(--r)',
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 2 }}>{k}</div>
      <div className={mono ? 'mono' : 'tabular'} style={{ fontSize: mono ? 11.5 : 14, fontWeight: 500, color: highlight ? 'var(--accent-text)' : 'var(--text)' }}>{v}</div>
      {sub && <div style={{ fontSize: 10.5, color: 'var(--text-4)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>{sub}</div>}
    </div>
  );
}

function ForecastTab({ mode, setMode, fixedDaily, setFixedDaily, defaultDaily, setDefaultDaily, weights, setWeights, excludeDates, setExcludeDates, abnormalThreshold, setAbnormalThreshold, abnormalDefault, setAbnormalDefault, sku }) {
  // Compute preview
  const sample = sku || SKUS[0] || { last7Denoised: 0, futureDaily: 0, msku: '—' };
  const last7 = sample.last7Denoised || 0;
  const weightSum = weights.d3 + weights.d7 + weights.d15 + weights.d30;
  const dynamicDaily = weightSum === 0 ? null : Math.round(
    (last7 * weights.d7 + (last7 * 1.05) * weights.d3 + (last7 * 0.95) * weights.d15 + (last7 * 0.92) * weights.d30) / weightSum
  );
  const finalDaily = mode === 'fixed' && fixedDaily
    ? +fixedDaily
    : (mode === 'dynamic' && dynamicDaily != null ? dynamicDaily : (mode === 'default' ? defaultDaily : sample.futureDaily));
  const stockoutDays = Math.round((sample.fbaAvail + sample.fbaInTransit) / Math.max(1, finalDaily));

  return (
    <>
      {/* Left preview */}
      <div style={{ flex: 1, padding: 18, overflow: 'auto', borderRight: '1px solid var(--border)', background: 'var(--surface-2)' }}>
        <div className="label" style={{ marginBottom: 10 }}>结果预览（实时）</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
          <PreviewKV k="近 7 天日销（原始）" v={sample.last7Daily}/>
          <PreviewKV k="近 7 天日销（去噪后）" v={sample.last7Denoised}/>
          <PreviewKV k="最终未来平均日销" v={finalDaily} highlight/>
          <PreviewKV k="预计断货时间" v={fmt.dateLong(new Date(Date.now() + stockoutDays * 86400000))}/>
          <PreviewKV k="建议采购量" v={fmt.num(Math.max(0, (sample.totalCoverage * finalDaily) - sample.totalStock)) + ' 件'} highlight/>
        </div>

        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div className="label">预测趋势图</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>历史前 7 天 · 预测后 30 天</div>
          </div>
          {(() => {
            // 历史段:优先 recent7(列表/详情都有);否则用 histRaw 末 7 天
            const hist = (sample.recent7 && sample.recent7.length)
              ? sample.recent7
              : (sample.histRaw || []).slice(-7);
            const future = Array.from({ length: 30 }, () => finalDaily);
            if (hist.length === 0 && finalDaily === 0) {
              return (
                <div style={{ height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11.5, color: 'var(--text-4)' }}>
                  暂无可视化数据 — 请先选择 SKU
                </div>
              );
            }
            return <ChartArea history={hist} future={future} height={140}/>;
          })()}
          <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-3)', marginTop: 8 }}>
            <span><span style={{ color: 'var(--accent)' }}>━</span> 历史(近 7 天)</span>
            <span><span style={{ color: 'var(--accent)' }}>┄</span> 预测(未来 30 天)</span>
          </div>
        </div>

        <div className="label" style={{ margin: '14px 0 8px' }}>未来汇总</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          <PreviewKV k="未来 7 天" v={fmt.num(finalDaily * 7)}/>
          <PreviewKV k="未来 15 天" v={fmt.num(finalDaily * 15)}/>
          <PreviewKV k="未来 30 天" v={fmt.num(finalDaily * 30)}/>
        </div>
      </div>

      {/* Right settings */}
      <div style={{ width: 380, flex: 'none', padding: 18, overflow: 'auto' }}>
        <div className="label" style={{ marginBottom: 8 }}>异常处理</div>
        <FieldRow label="排除异常时间">
          <button className="btn sm" onClick={() => setExcludeDates([...excludeDates, { from: '', to: '', reason: '' }])}>
            <Icon name="plus" size={11}/>添加
          </button>
        </FieldRow>
        {excludeDates.map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px', background: 'var(--surface-2)', borderRadius: 4, fontSize: 11.5, marginBottom: 4 }}>
            <Icon name="alert" size={11} color="var(--p2)"/>
            <span className="mono">{d.from} → {d.to}</span>
            <span style={{ color: 'var(--text-3)' }}>· {d.reason}</span>
            <span style={{ flex: 1 }}/>
            <button className="btn ghost icon sm" onClick={() => setExcludeDates(excludeDates.filter((_, j) => j !== i))}><Icon name="x" size={11}/></button>
          </div>
        ))}
        <FieldRow label="排除异常销量" hint="单日销量超过阈值时,以默认值替代">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, flex: 1 }}>
            <span style={{ color: 'var(--text-3)' }}>超过</span>
            <input className="txt" type="number" min="0"
              value={abnormalThreshold}
              onChange={e => setAbnormalThreshold(e.target.value)}
              placeholder="如 200"
              style={{ width: 80, height: 26, fontSize: 12 }}/>
            <span style={{ color: 'var(--text-3)' }}>件,</span>
            <span style={{ color: 'var(--text-3)' }}>则默认为</span>
            <input className="txt" type="number" min="0"
              value={abnormalDefault}
              onChange={e => setAbnormalDefault(e.target.value)}
              placeholder="如 80"
              style={{ width: 80, height: 26, fontSize: 12 }}/>
            <span style={{ color: 'var(--text-3)' }}>件</span>
          </div>
        </FieldRow>

        <div className="divider" style={{ margin: '14px 0' }}/>

        <div className="label" style={{ marginBottom: 8 }}>未来日销策略</div>
        <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
          {[
            { v: 'fixed', l: '固定日销量' },
            { v: 'dynamic', l: '动态销量' },
            { v: 'default', l: '默认日销' },
          ].map(o => (
            <button key={o.v} onClick={() => setMode(o.v)} className="btn sm" style={{
              flex: 1,
              borderColor: mode === o.v ? 'var(--accent)' : 'var(--border)',
              background: mode === o.v ? 'var(--accent-soft)' : 'var(--surface)',
              color: mode === o.v ? 'var(--accent-text)' : 'var(--text)',
            }}>{o.l}</button>
          ))}
        </div>

        {mode === 'fixed' && (
          <FieldRow label="固定日销量" hint="优先级最高">
            <input className="txt" type="number" value={fixedDaily} onChange={e => setFixedDaily(e.target.value)} style={{ flex: 1 }} placeholder="留空使用动态"/>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>件 / 天</span>
          </FieldRow>
        )}

        {mode === 'dynamic' && (
          <>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginBottom: 8 }}>近 N 天权重（合计 {weightSum}%，留空表示不参与）</div>
            {[
              { k: 'd3', l: '近 3 天' },
              { k: 'd7', l: '近 7 天' },
              { k: 'd15', l: '近 15 天' },
              { k: 'd30', l: '近 30 天' },
            ].map(w => (
              <FieldRow key={w.k} label={w.l}>
                <input className="txt" type="number" min={0} max={100} value={weights[w.k]} onChange={e => setWeights({ ...weights, [w.k]: +e.target.value || 0 })} style={{ width: 80 }}/>
                <span style={{ fontSize: 12, color: 'var(--text-3)' }}>%</span>
                <div style={{ flex: 1, height: 4, background: 'var(--surface-hover)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: weights[w.k] + '%', height: '100%', background: 'var(--accent)' }}/>
                </div>
              </FieldRow>
            ))}
          </>
        )}

        {mode === 'default' && (
          <FieldRow label="未来默认日销">
            <input className="txt" type="number" value={defaultDaily} onChange={e => setDefaultDaily(+e.target.value)} style={{ flex: 1 }}/>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>件 / 天</span>
          </FieldRow>
        )}

        <div style={{ display: 'flex', gap: 6, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 4, marginTop: 12 }}>
          <Icon name="info" size={12} color="var(--accent)"/>
          <div style={{ fontSize: 11, color: 'var(--text-2)', lineHeight: 1.5 }}>
            优先级：固定日销 &gt; 动态销量 &gt; 默认日销 &gt; 历史去噪 &gt; 历史原始<br/>
            历史样本不足时显示「数据不足」 · 历史口径不含今天 · 未来口径含今天
          </div>
        </div>
      </div>
    </>
  );
}

function PreviewKV({ k, v, highlight }) {
  return (
    <div style={{
      padding: '8px 10px',
      background: highlight ? 'var(--accent-soft)' : 'var(--surface)',
      border: '1px solid ' + (highlight ? 'var(--accent-soft-2)' : 'var(--border)'),
      borderRadius: 'var(--r)',
    }}>
      <div style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{k}</div>
      <div className="tabular" style={{ fontSize: 14, fontWeight: 600, color: highlight ? 'var(--accent-text)' : 'var(--text)' }}>{v}</div>
    </div>
  );
}

// ── 采购计划创建 ────────────────────────────
function CreatePOModal({ open, onClose, ids, showToast, setRoute }) {
  const [step, setStep] = React.useState('confirm'); // confirm | computing | redirect
  if (!open) return null;
  const skus = ids.map(id => SKUS.find(s => s.id === id)).filter(Boolean);
  // 过滤掉 suggest_qty <= 0 的 — 后端会拒;前端先剔除并提示
  const valid = skus.filter(s => (s.suggestQty || 0) > 0);
  const skipped = skus.length - valid.length;
  const totalQty = valid.reduce((s, x) => s + x.suggestQty, 0);

  const exceedsLimit = ids.length > 50;
  const noneSelected = ids.length === 0;
  const allSkipped = skus.length > 0 && valid.length === 0;
  const noPermission = false; // toggle for empty state demo

  const handleGo = async () => {
    setStep('computing');
    try {
      const items = valid.map(s => ({
        mall_id: s.mall_id ?? null,
        msku: s.msku,
        sku: s.sku,
        suggest_qty: s.suggestQty,
      }));
      const calcRunId = valid[0]?.calcRunId || null;
      let createdCount = valid.length;
      let newDraftId = null;
      if (window.api && items.length) {
        const resp = await window.api.purchaseDraftCreate(items, {
          calc_run_id: calcRunId,
          created_by: 'frontend',
        });
        createdCount = resp.created_count || valid.length;
        newDraftId = (resp.draft_ids && resp.draft_ids[0]) || null;
      }
      setStep('redirect');
      setTimeout(() => {
        onClose();
        setStep('confirm');
        const msg = skipped > 0
          ? `已生成 ${createdCount} 条草稿,跳过 ${skipped} 个无建议采购量的 SKU`
          : `已生成 ${createdCount} 条采购草稿`;
        showToast(msg);
        // 真跳转 — 进入采购草稿页,带 draftId 高亮
        if (setRoute) setRoute({ page: 'drafts', draftId: newDraftId });
      }, 700);
    } catch (err) {
      setStep('confirm');
      showToast('生成失败:' + err.message);
    }
  };

  return (
    <Modal open={open} onClose={onClose} width={560}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Icon name="lightning" size={16} color="var(--accent)"/>
        <div className="h2" style={{ flex: 1 }}>生成采购计划</div>
        <button className="btn ghost icon" onClick={onClose}><Icon name="x" size={14}/></button>
      </div>

      {noneSelected ? (
        <EmptyState icon="alert" title="请先勾选需要生成采购计划的商品" sub="在列表中勾选后再点击「生成采购计划」"/>
      ) : exceedsLimit ? (
        <EmptyState icon="alert" tone="warn" title="最多只能选择 50 条数据" sub={`当前已选 ${ids.length} 条，请取消多余项后再试`}/>
      ) : allSkipped ? (
        <EmptyState icon="alert" tone="warn" title="所选 SKU 均无建议采购量" sub="只有标记为「建议采购」的 SKU 可生成草稿,请重新筛选"/>
      ) : noPermission ? (
        <EmptyState icon="alert" tone="warn" title="暂无采购计划创建权限" sub="请联系管理员开通「采购计划创建」权限"/>
      ) : step === 'computing' ? (
        <div style={{ padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <div className="pulse" style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--accent-soft-2)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="refresh" size={20}/>
          </div>
          <div style={{ fontSize: 13, fontWeight: 500 }}>正在生成预填数据…</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>计算中 · 预计 1 秒</div>
        </div>
      ) : step === 'redirect' ? (
        <div style={{ padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--p3-soft)', color: 'var(--p3-strong)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="check" size={20}/>
          </div>
          <div style={{ fontSize: 13, fontWeight: 500 }}>已就绪，即将跳转</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>正在打开采购计划创建页…</div>
        </div>
      ) : (
        <>
          <div style={{ padding: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
              <KV k="勾选 SKU" v={ids.length + ' 条'}/>
              <KV k="可生成草稿" v={valid.length + ' 条'}/>
              <KV k="建议采购总量" v={fmt.num(totalQty) + ' 件'}/>
            </div>
            {skipped > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', background: 'var(--p2-soft)', color: 'var(--p2-strong)', borderRadius: 'var(--r)', fontSize: 12, marginBottom: 12 }}>
                <Icon name="alert" size={12}/>
                <span>勾选中有 {skipped} 个 SKU 无建议采购量,生成时会自动跳过</span>
              </div>
            )}
            <div className="label" style={{ marginBottom: 6 }}>预填明细</div>
            <div style={{ maxHeight: 200, overflow: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
              <table className="t" style={{ fontSize: 12 }}>
                <thead><tr><th>SKU</th><th>店铺</th><th>风险</th><th className="num">建议采购</th></tr></thead>
                <tbody>
                  {valid.slice(0, 10).map(s => (
                    <tr key={s.id}>
                      <td className="mono" style={{ fontSize: 11 }}>{s.msku}</td>
                      <td>{(s.country && s.country.flag) || ''} {s.store}</td>
                      <td><PriorityBadge level={s.priority}/></td>
                      <td className="num tabular" style={{ fontWeight: 500 }}>{fmt.num(s.suggestQty)}</td>
                    </tr>
                  ))}
                  {valid.length > 10 && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-3)' }}>… 还有 {valid.length - 10} 条</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
          <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className="btn" onClick={onClose}>取消</button>
            <button className="btn primary" onClick={handleGo} disabled={valid.length === 0}>
              <Icon name="lightning" size={13}/>生成采购计划
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}

function EmptyState({ icon, title, sub, tone = 'info' }) {
  const c = tone === 'warn' ? 'var(--p2)' : 'var(--accent)';
  const bg = tone === 'warn' ? 'var(--p2-soft)' : 'var(--accent-soft)';
  return (
    <div style={{ padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 40, height: 40, borderRadius: '50%', background: bg, color: c, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon name={icon} size={20}/>
      </div>
      <div style={{ fontSize: 13, fontWeight: 500 }}>{title}</div>
      <div style={{ fontSize: 11.5, color: 'var(--text-3)', textAlign: 'center', maxWidth: 320 }}>{sub}</div>
    </div>
  );
}

Object.assign(window, { RulesModal, CreatePOModal });
