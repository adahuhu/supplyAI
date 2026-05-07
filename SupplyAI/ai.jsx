// AI panels — global (Dashboard) and per-SKU (detail).

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

function AIPanelHeader({ title, sub, badge, onClose }) {
  return (
    <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'flex-start', gap: 10, background: 'var(--surface)' }}>
      <div style={{
        width: 28, height: 28, borderRadius: 7,
        background: 'var(--accent-soft)', color: 'var(--accent-text)',
        border: '1px solid rgba(94,106,210,.22)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none',
      }}><Icon name="sparkles" size={14}/></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="h3" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {title}
          {badge && <span className="chip" style={{ background: 'var(--accent-soft)', color: 'var(--accent-text)', borderColor: 'transparent', height: 18, fontSize: 10.5 }}>{badge}</span>}
        </div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{sub}</div>}
      </div>
      <button className="btn ghost icon sm" onClick={onClose}><Icon name="x" size={14}/></button>
    </div>
  );
}

function AIInput({ placeholder = '提问 SKU 风险、采购建议、规则影响…' }) {
  const [v, setV] = React.useState('');
  return (
    <div style={{ padding: 12, borderTop: '1px solid var(--border)', background: 'var(--bg-sunken)' }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 6,
        background: 'var(--surface)',
        border: '1px solid var(--border-input)',
        borderRadius: 'var(--r-md)',
        padding: 8,
      }}>
        <textarea
          value={v}
          onChange={e => setV(e.target.value)}
          placeholder={placeholder}
          rows={2}
          style={{
            flex: 1, border: 0, outline: 'none', resize: 'none',
            background: 'transparent', color: 'inherit',
            fontFamily: 'inherit', fontSize: 12.5, lineHeight: 1.5,
          }}/>
        <button className="btn icon" disabled={!v} style={{ background: v ? 'var(--accent)' : '', color: v ? '#fff' : '', borderColor: v ? 'var(--accent)' : '' }}>
          <Icon name="send" size={13}/>
        </button>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, fontSize: 11, color: 'var(--text-4)' }}>
        <Icon name="info" size={11}/>
        <span>AI 回答基于最新计算快照与当前规则，不含节日预测</span>
      </div>
    </div>
  );
}

// ── Global AI ───────────────────────────────
function GlobalAIPanel({ onClose, setRoute }) {
  const [history, setHistory] = React.useState([
    { role: 'ai', a: GLOBAL_AI_PRESETS[0].a, q: GLOBAL_AI_PRESETS[0].q },
  ]);
  const [thinking, setThinking] = React.useState(false);
  const ask = (preset) => {
    setHistory(h => [...h, { role: 'user', text: preset.q }]);
    setThinking(true);
    setTimeout(() => {
      setHistory(h => [...h, { role: 'ai', a: preset.a, q: preset.q }]);
      setThinking(false);
    }, 700);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <AIPanelHeader
        title="全局 AI 助手"
        sub={'基于 ' + fmt.dateLong(DASH_STATS.asOf) + ' ' + fmt.time(DASH_STATS.asOf) + ' 快照'}
        badge="Dashboard"
        onClose={onClose}
      />

      <div style={{ flex: 1, overflow: 'auto', padding: 14, background: 'linear-gradient(180deg, rgba(255,255,255,.018), transparent 140px)' }}>
        {history.map((m, i) => (
          m.role === 'user'
            ? <AIBubble key={i} role="user">{m.text}</AIBubble>
            : (
              <AIBubble key={i} role="ai">
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{m.q}</div>
                <AIAnswer a={m.a} onSkuClick={(it) => {
                  const sku = SKUS.find(s => s.msku === it.msku) || SKUS[0];
                  setRoute({ page: 'sku', skuId: sku.id });
                }}/>
              </AIBubble>
            )
        ))}
        {thinking && (
          <AIBubble role="ai">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-3)', fontSize: 12 }}>
              <span className="pulse">●</span>计算中…
            </div>
          </AIBubble>
        )}

        <div style={{ marginTop: 16 }}>
          <div className="label" style={{ marginBottom: 8 }}>常用问题</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[...GLOBAL_AI_PRESETS, { q: '风险最高的 5 个是什么？' }, { q: '哪些商品建议立即采购？' }].map((p, i) => (
              <button key={i} onClick={() => p.a && ask(p)} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
                textAlign: 'left', border: '1px solid var(--border)',
                background: 'var(--surface)',
              }}>
                <Icon name="sparkles" size={11} color="var(--text-3)"/>
                <span style={{ fontSize: 12 }}>{p.q}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <AIInput/>
    </div>
  );
}

// ── SKU AI ────────────────────────────────
function SKUAIPanel({ sku, onClose, mode }) {
  const presets = SKU_AI_PRESETS(sku);
  const [history, setHistory] = React.useState([
    { role: 'ai', a: presets[0].a, q: presets[0].q },
  ]);
  const [thinking, setThinking] = React.useState(false);
  const ask = (preset) => {
    setHistory(h => [...h, { role: 'user', text: preset.q }]);
    setThinking(true);
    setTimeout(() => {
      setHistory(h => [...h, { role: 'ai', a: preset.a, q: preset.q }]);
      setThinking(false);
    }, 700);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <AIPanelHeader
        title="SKU 分析助手"
        sub={sku.msku + ' · ' + sku.store + ' · 快照 ' + fmt.time(DASH_STATS.asOf)}
        badge={'绑定 ' + sku.msku.slice(-3)}
        onClose={onClose}
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
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{m.q}</div>
                <AIAnswer a={m.a}/>
              </AIBubble>
            )
        ))}
        {thinking && (
          <AIBubble role="ai">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-3)', fontSize: 12 }}>
              <span className="pulse">●</span>计算中…
            </div>
          </AIBubble>
        )}

        <div style={{ marginTop: 8 }}>
          <div className="label" style={{ marginBottom: 8 }}>常用问题</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {presets.map((p, i) => (
              <button key={i} onClick={() => ask(p)} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
                textAlign: 'left', border: '1px solid var(--border)',
                background: 'var(--surface)',
              }}>
                <Icon name="sparkles" size={11} color="var(--text-3)"/>
                <span style={{ fontSize: 12 }}>{p.q}</span>
              </button>
            ))}
            <button className="btn ghost" style={{
              justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
              textAlign: 'left', border: '1px solid var(--border)',
              background: 'var(--surface)',
            }}>
              <Icon name="sparkles" size={11} color="var(--text-3)"/>
              <span style={{ fontSize: 12 }}>它什么时候会断货？</span>
            </button>
            <button className="btn ghost" style={{
              justifyContent: 'flex-start', height: 'auto', padding: '8px 10px',
              textAlign: 'left', border: '1px solid var(--border)',
              background: 'var(--surface)',
            }}>
              <Icon name="sparkles" size={11} color="var(--text-3)"/>
              <span style={{ fontSize: 12 }}>帮我生成采购计划</span>
            </button>
          </div>
        </div>
      </div>

      <AIInput placeholder="向 AI 追问 SKU 风险、采购量、规则影响…"/>
    </div>
  );
}

Object.assign(window, { GlobalAIPanel, SKUAIPanel });
