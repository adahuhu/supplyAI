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

function AIPanelHeader({ title, sub, onClose, onToggleWide, wide }) {
  return (
    <div style={{ padding: '13px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'flex-start', gap: 10, background: 'var(--surface)' }}>
      <div style={{
        width: 28, height: 28, borderRadius: 7,
        background: 'var(--accent-soft)', color: 'var(--accent-text)',
        border: '1px solid rgba(94,106,210,.22)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none',
      }}><Icon name="bot" size={14}/></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="h3">{title}</div>
        {sub && <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{sub}</div>}
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

function AIInput({ placeholder = '提问 SKU 风险、采购建议、规则影响…', onSend, disabled }) {
  const [v, setV] = React.useState('');
  const submit = () => {
    const text = v.trim();
    if (!text || disabled) return;
    onSend && onSend(text);
    setV('');
  };
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
        <span>AI 回答基于最新计算快照与当前规则。回车发送 / Shift+回车换行</span>
      </div>
    </div>
  );
}

// 工具名 → 中文标签(用于流式 thinking 占位)
const TOOL_LABEL = {
  query_skus: '查询 SKU 列表',
  get_sku_detail: '查询 SKU 详情',
  query_risk_queue: '查询风险队列',
  generate_purchase_draft: '生成采购草稿',
  query_dashboard_snapshot: '查询工作台快照',
  query_finance: '查询财务',
  query_holidays: '查询节假日',
};

// ── Global AI ───────────────────────────────
// 7 个 AI 场景 — 按飞书产品文档需求。
// 每个场景对应一类决策:单 SKU/优先级/活动/风险/方案/新品/管理层。
const GLOBAL_AI_QUESTIONS = [
  { tag: '单 SKU 决策',     q: '挑一个高风险 SKU,告诉我还能卖多久,要不要补、补多少?' },
  { tag: '本周补货优先级', q: '本周哪些 SKU 必须补货?按紧急度排序并说明原因。' },
  { tag: '活动备货模拟',   q: 'Prime Day 想做到日销翻倍,要为哪些 SKU 备多少货、什么时候发?' },
  { tag: '断货风险预警',   q: '这周有哪些爆款可能断货?预计损失销量和利润是多少?' },
  { tag: '多方案对比',     q: '只海运 vs 海+空混合,成本和断货风险分别是什么?' },
  { tag: '新品孵化建议',   q: '新品 3 周表现一般,要不要继续补货?优化哪些动作?' },
  { tag: '管理层摘要',     q: '本周补货层面最大的风险、机会、决策点是什么?' },
];

function GlobalAIPanel({ onClose, setRoute, dashFilters, history, setHistory, wide, onToggleWide }) {
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
      // 流式:先推一个空 ai bubble,每 delta 增量追加
      setHistory(h => [...h, { role: 'ai', text: '', streaming: true }]);
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
      await window.api.aiChatStream(msgs, context, (ev) => {
        if (ev.type === 'delta') appendDelta(ev.text || '');
        else if (ev.type === 'tool_start') setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        else if (ev.type === 'tool_end') setToolStatus('');
        else if (ev.type === 'error') appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        else if (ev.type === 'done') {
          // 清掉 streaming 标记
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
        title="全局 AI 助手"
        sub={'基于 ' + fmt.dateLong(DASH_STATS.asOf) + ' ' + fmt.time(DASH_STATS.asOf) + ' 快照'}
        onClose={onClose}
        onToggleWide={onToggleWide}
        wide={wide}
      />

      <div style={{ flex: 1, overflow: 'auto', padding: 14, background: 'linear-gradient(180deg, rgba(255,255,255,.018), transparent 140px)' }}>
        {history.map((m, i) => (
          m.role === 'user'
            ? <AIBubble key={i} role="user">{m.text}</AIBubble>
            : (
              <AIBubble key={i} role="ai">
                {m.q && <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>{m.q}</div>}
                <div style={{ fontSize: 12.5, lineHeight: 1.55 }}
                  dangerouslySetInnerHTML={{ __html: window.renderMarkdown ? window.renderMarkdown(m.text) : m.text }}/>
              </AIBubble>
            )
        ))}
        {thinking && (() => {
          const last = history[history.length - 1];
          const hasGrowing = last && last.role === 'ai' && last.text;
          // 已经在 stream 内容时不再叠一个 placeholder bubble
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

        <div style={{ marginTop: 16 }}>
          <div className="label" style={{ marginBottom: 8 }}>常用场景</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
            {GLOBAL_AI_QUESTIONS.map((item, i) => (
              <button key={i} onClick={() => sendToBackend(item.q)} disabled={thinking} className="btn ghost" style={{
                justifyContent: 'flex-start', height: 'auto', padding: '10px 12px',
                textAlign: 'left', border: '1px solid var(--border)',
                background: 'var(--surface)',
                flexDirection: 'column', alignItems: 'flex-start', gap: 4,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                  <Icon name="sparkles" size={11} color="var(--accent)"/>
                  <span style={{
                    fontSize: 10.5, fontWeight: 500,
                    color: 'var(--accent-text)',
                    background: 'var(--accent-soft)',
                    padding: '1px 6px', borderRadius: 4,
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

function SKUAIPanel({ sku, onClose, mode, history, setHistory, wide, onToggleWide }) {
  const [thinking, setThinking] = React.useState(false);
  const [toolStatus, setToolStatus] = React.useState('');
  // 挂载后调 /ai/explain — 仅在该 SKU 历史为空时(首次打开),已有历史就跳过
  React.useEffect(() => {
    if (!window.api || !sku.listingId) return;
    if (history && history.length > 0) return; // 已有对话,不重复 explain
    let cancelled = false;
    setThinking(true);
    // 先 push 一个空 AI bubble,流式 delta 累积进它
    setHistory(h => [...h, { role: 'ai', text: '', q: 'AI 解释', streaming: true }]);
    const append = (delta) => {
      if (cancelled) return;
      setHistory(h => {
        const next = h.slice();
        const last = next[next.length - 1];
        if (last && last.role === 'ai') {
          next[next.length - 1] = { ...last, text: (last.text || '') + delta };
        }
        return next;
      });
    };
    window.api.aiExplainStream(sku.listingId, (ev) => {
      if (cancelled) return;
      if (ev.type === 'delta') append(ev.text || '');
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
      setHistory(h => [...h, { role: 'ai', text: '', streaming: true }]);
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
      await window.api.aiChatStream(msgs, context, (ev) => {
        if (ev.type === 'delta') appendDelta(ev.text || '');
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
                <div style={{ fontSize: 12.5, lineHeight: 1.55 }}
                  dangerouslySetInnerHTML={{ __html: window.renderMarkdown ? window.renderMarkdown(m.text) : m.text }}/>
              </AIBubble>
            )
        ))}
        {thinking && (() => {
          const last = history[history.length - 1];
          const hasGrowing = last && last.role === 'ai' && last.text;
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

Object.assign(window, { GlobalAIPanel, SKUAIPanel });
