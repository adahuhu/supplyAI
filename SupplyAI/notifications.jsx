// 钉钉日报推送中心 — 手动触发每日 8 点经营简报。

function NotificationPage({ setRoute, showToast }) {
  const [role, setRole] = React.useState('boss');
  const [owner, setOwner] = React.useState('');
  const [mallId, setMallId] = React.useState('');
  const [country, setCountry] = React.useState('');
  const [preview, setPreview] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [sending, setSending] = React.useState(false);
  const [error, setError] = React.useState('');
  const [sendResult, setSendResult] = React.useState(null);

  const owners = window.FILTERS_DATA?.owners || [];
  const stores = window.FILTERS_DATA?.stores || [];
  const countries = window.FILTERS_DATA?.countries || [];

  const detailUrl = React.useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    params.set('api', params.get('api') || (window.api?.base || '/api/supplyai'));
    params.delete('page');
    params.delete('filter');
    params.delete('skuId');
    params.set('ai', '1');
    return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
  }, []);

  const payload = React.useMemo(() => {
    const body = { role, detail_url: detailUrl };
    if (role === 'operator') {
      if (owner) {
        body.owners = [owner];
        body.target_name = owner;
      }
      if (mallId) body.mall_ids = [Number(mallId)];
      if (country) body.country_codes = [country];
    }
    return body;
  }, [role, owner, mallId, country, detailUrl]);

  const loadPreview = React.useCallback(async () => {
    if (!window.api?.notificationPreview) return;
    setLoading(true);
    setError('');
    setSendResult(null);
    try {
      const resp = await window.api.notificationPreview(payload);
      setPreview(resp);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }, [payload]);

  React.useEffect(() => {
    loadPreview();
  }, [loadPreview]);

  const send = async () => {
    if (!window.api?.notificationSend) return;
    setSending(true);
    setError('');
    try {
      const resp = await window.api.notificationSend(payload);
      setSendResult(resp);
      showToast && showToast(resp.status === 'sent' ? '钉钉日报已发送' : '模拟发送完成');
      setPreview(resp);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setSending(false);
    }
  };

  const report = preview?.report;
  const finance = report?.finance || [];
  const metric = (label) => finance.find(m => m.label === label) || { value: 0 };

  return (
    <div style={{ minHeight: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        padding: '24px 32px 18px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
        display: 'flex',
        alignItems: 'flex-end',
        gap: 16,
        justifyContent: 'space-between',
        flexWrap: 'wrap',
      }}>
        <div>
          <div className="h1">钉钉推送</div>
          <div style={{ color: 'var(--text-3)', marginTop: 5 }}>每日经营简报 · 8:00 手动模拟触发</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn" onClick={loadPreview} disabled={loading}>
            <Icon name="refresh" size={13}/>{loading ? '生成中' : '刷新预览'}
          </button>
          <button className="btn accent" onClick={send} disabled={sending || loading || !preview}>
            <Icon name="send" size={13}/>{sending ? '发送中' : '发送钉钉'}
          </button>
        </div>
      </div>

      <div style={{ padding: '18px 32px', display: 'grid', gridTemplateColumns: '320px minmax(0, 1fr)', gap: 18 }}>
        <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r-md)', background: 'var(--surface)' }}>
            <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>
              推送对象
            </div>
            <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Segmented value={role} onChange={(v) => {
                setRole(v);
                if (v === 'boss') {
                  setOwner('');
                  setMallId('');
                  setCountry('');
                }
              }} options={[
                { value: 'boss', label: '老板' },
                { value: 'operator', label: '运营' },
              ]}/>

              {role === 'operator' && (
                <>
                  <LabeledSelect label="负责人" value={owner} onChange={setOwner}
                    options={owners.map(o => ({ value: o.value, label: `${o.label} (${o.count})` }))}/>
                  <LabeledSelect label="店铺" value={mallId} onChange={setMallId}
                    options={stores.map(s => ({ value: s.value, label: `${s.label} (${s.count})` }))}/>
                  <LabeledSelect label="国家" value={country} onChange={setCountry}
                    options={countries.map(c => ({ value: c.value, label: `${c.label} (${c.count})` }))}/>
                </>
              )}
            </div>
          </div>

          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r-md)', background: 'var(--surface)' }}>
            <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>
              推送状态
            </div>
            <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <StatusLine label="角色" value={preview?.role_label || (role === 'boss' ? '老板' : '运营')}/>
              <StatusLine label="范围" value={report?.scope_label || '—'}/>
              <StatusLine label="数据日期" value={report?.as_of_date || '—'}/>
              <StatusLine label="入口" value="分析工作台"/>
              {sendResult && (
                <div style={{
                  padding: '9px 10px',
                  borderRadius: 6,
                  background: sendResult.status === 'failed' ? 'var(--p1-soft)' : 'var(--accent-soft)',
                  color: sendResult.status === 'failed' ? 'var(--p1-strong)' : 'var(--accent-text)',
                  fontSize: 12,
                }}>
                  {sendResult.message}
                </div>
              )}
              {error && (
                <div style={{ padding: '9px 10px', borderRadius: 6, background: 'var(--p1-soft)', color: 'var(--p1-strong)', fontSize: 12 }}>
                  {error}
                </div>
              )}
            </div>
          </div>
        </section>

        <section style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 0 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(120px, 1fr))', gap: 10 }}>
            <Metric label="昨日销量" value={fmtNumber(metric('昨日销量').value)} unit="件"/>
            <Metric label="收入" value={fmtMoney(metric('收入').value)}/>
            <Metric label="成本" value={fmtMoney(metric('成本').value)}/>
            <Metric label="费用" value={fmtMoney(metric('费用').value)}/>
            <Metric label="利润" value={fmtMoney(metric('利润').value)} tone={(metric('利润').value || 0) < 0 ? 'p1' : 'p3'}/>
          </div>

          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r-md)', background: 'var(--surface)', overflow: 'hidden' }}>
            <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{preview?.title || 'SupplyAI 每日经营简报'}</div>
                <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 2 }}>{preview?.subtitle || '—'}</div>
              </div>
              <button className="btn sm" onClick={() => setRoute && setRoute({ page: 'dashboard' })}>
                <Icon name="arrow-right" size={12}/>工作台
              </button>
            </div>

            <div style={{ padding: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <SectionTitle title="今日关注" icon="bell"/>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginTop: 10 }}>
                  <MiniStat label="断货风险" value={report?.risk?.risk_sku_count || 0} unit="SKU"/>
                  <MiniStat label="P1 紧急" value={report?.risk?.p1_count || 0} unit="SKU" tone="p1"/>
                  <MiniStat label="7 天内断货" value={report?.risk?.stockout_7_count || 0} unit="SKU" tone="p2"/>
                  <MiniStat label="建议采购" value={report?.risk?.suggest_sku_count || 0} unit="SKU"/>
                </div>
                <div style={{ marginTop: 12, color: 'var(--text-2)', lineHeight: 1.7 }}>
                  {report?.summary || (loading ? '正在生成摘要…' : '暂无摘要')}
                </div>
              </div>

              <div>
                <SectionTitle title="建议动作" icon="lightning"/>
                <div style={{
                  marginTop: 10,
                  minHeight: 94,
                  padding: '12px 13px',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  background: 'var(--surface-2)',
                  lineHeight: 1.7,
                  color: 'var(--text-2)',
                }}>
                  {report?.action_text || '—'}
                </div>
              </div>
            </div>

            <div style={{ padding: '0 16px 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <SkuListBlock title="近 7 天畅销 SKU" rows={report?.top_skus || []} mode="sales"/>
              <SkuListBlock title="优先处理 SKU" rows={report?.focus_skus || []} mode="risk"/>
            </div>
          </div>

          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r-md)', background: 'var(--surface)' }}>
            <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>钉钉卡片预览</div>
            <pre style={{
              margin: 0,
              padding: 16,
              whiteSpace: 'pre-wrap',
              lineHeight: 1.65,
              color: 'var(--text-2)',
              fontSize: 12,
              maxHeight: 320,
              overflow: 'auto',
              fontFamily: 'var(--font-sans)',
            }}>{preview?.markdown || '正在生成预览…'}</pre>
          </div>
        </section>
      </div>
    </div>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${options.length}, 1fr)`, gap: 6, padding: 3, border: '1px solid var(--border)', borderRadius: 7, background: 'var(--surface-2)' }}>
      {options.map(opt => (
        <button key={opt.value} type="button" onClick={() => onChange(opt.value)}
          style={{
            height: 30,
            border: '1px solid ' + (value === opt.value ? 'var(--accent)' : 'transparent'),
            borderRadius: 5,
            background: value === opt.value ? 'var(--accent-soft)' : 'transparent',
            color: value === opt.value ? 'var(--accent-text)' : 'var(--text-2)',
            fontFamily: 'inherit',
            cursor: 'pointer',
            fontWeight: value === opt.value ? 600 : 500,
          }}>{opt.label}</button>
      ))}
    </div>
  );
}

function LabeledSelect({ label, value, onChange, options }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{label}</span>
      <select className="sel" value={value} onChange={(e) => onChange(e.target.value)} style={{ width: '100%' }}>
        <option value="">全部</option>
        {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
      </select>
    </label>
  );
}

function StatusLine({ label, value }) {
  return (
    <div style={{ display: 'flex', gap: 10, justifyContent: 'space-between', fontSize: 12 }}>
      <span style={{ color: 'var(--text-3)' }}>{label}</span>
      <span style={{ color: 'var(--text)', textAlign: 'right', maxWidth: 190, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</span>
    </div>
  );
}

function Metric({ label, value, unit, tone }) {
  const color = tone === 'p1' ? 'var(--p1)' : tone === 'p3' ? 'var(--p3)' : 'var(--text)';
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--r-md)', background: 'var(--surface)', padding: '12px 13px', minHeight: 82 }}>
      <div style={{ color: 'var(--text-3)', fontSize: 11.5 }}>{label}</div>
      <div className="tabular" style={{ marginTop: 8, fontSize: 22, lineHeight: 1, fontWeight: 650, color }}>{value}<span style={{ marginLeft: 4, fontSize: 12, color: 'var(--text-3)' }}>{unit || ''}</span></div>
    </div>
  );
}

function MiniStat({ label, value, unit, tone }) {
  const color = tone === 'p1' ? 'var(--p1)' : tone === 'p2' ? 'var(--p2)' : 'var(--accent-text)';
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '9px 10px', background: 'var(--surface-2)' }}>
      <div style={{ color: 'var(--text-3)', fontSize: 11 }}>{label}</div>
      <div className="tabular" style={{ marginTop: 5, fontSize: 18, fontWeight: 650, color }}>{value}<span style={{ marginLeft: 3, fontSize: 11, color: 'var(--text-3)' }}>{unit}</span></div>
    </div>
  );
}

function SectionTitle({ title, icon }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontWeight: 600 }}>
      <Icon name={icon} size={13}/>{title}
    </div>
  );
}

function SkuListBlock({ title, rows, mode }) {
  const subText = (row) => {
    const parts = [row.store_name, row.product_name].filter(Boolean);
    return parts.length ? parts.join(' · ') : '—';
  };
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden' }}>
      <div style={{ padding: '9px 10px', borderBottom: '1px solid var(--border)', fontWeight: 600, background: 'var(--surface-2)' }}>{title}</div>
      {(rows || []).length === 0 && (
        <div style={{ padding: 16, color: 'var(--text-4)', fontSize: 12 }}>暂无数据</div>
      )}
      {(rows || []).map((row, i) => (
        <div key={`${row.msku}-${i}`} style={{ padding: '10px 11px', borderBottom: i === rows.length - 1 ? 0 : '1px solid var(--border)', display: 'grid', gridTemplateColumns: '24px minmax(0, 1fr) auto', gap: 8, alignItems: 'center' }}>
          <div className="tabular" style={{ color: 'var(--text-3)' }}>{i + 1}</div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.msku}</div>
            <div style={{ color: 'var(--text-3)', fontSize: 11.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{subText(row)}</div>
          </div>
          <div className="tabular" style={{ textAlign: 'right', fontWeight: 600, color: mode === 'risk' && row.priority === 'p1' ? 'var(--p1)' : 'var(--text)' }}>
            {mode === 'sales' ? `${row.sales_7d} 件` : `${row.suggest_qty || 0} 件`}
          </div>
        </div>
      ))}
    </div>
  );
}

function fmtMoney(value) {
  return '$' + Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN');
}

Object.assign(window, { NotificationPage });
