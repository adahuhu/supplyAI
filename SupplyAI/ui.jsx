// Shared UI primitives — sparkline, donut, sparkbar, icon set, drawer, modal, etc.

// ── Icons ─────────────────────────────────────────────
function Icon({ name, size = 14, stroke = 1.6, color = 'currentColor', style }) {
  const s = size;
  const common = { width: s, height: s, viewBox: '0 0 24 24', fill: 'none', stroke: color, strokeWidth: stroke, strokeLinecap: 'round', strokeLinejoin: 'round', style };
  switch (name) {
    case 'search': return <svg {...common}><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg>;
    case 'filter': return <svg {...common}><path d="M3 5h18M6 12h12M10 19h4"/></svg>;
    case 'columns': return <svg {...common}><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M15 3v18"/></svg>;
    case 'plus': return <svg {...common}><path d="M12 5v14M5 12h14"/></svg>;
    case 'chevron-right': return <svg {...common}><path d="m9 6 6 6-6 6"/></svg>;
    case 'chevron-down': return <svg {...common}><path d="m6 9 6 6 6-6"/></svg>;
    case 'chevron-left': return <svg {...common}><path d="m15 6-6 6 6 6"/></svg>;
    case 'home': return <svg {...common}><path d="M3 9.5 12 3l9 6.5V21H3z"/><path d="M9 21V12h6v9"/></svg>;
    case 'list': return <svg {...common}><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>;
    case 'sparkles': return <svg {...common}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></svg>;
    case 'bot': return <svg {...common}><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>;
    case 'settings': return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>;
    case 'box': return <svg {...common}><path d="m21 8-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>;
    case 'truck': return <svg {...common}><path d="M1 3h15v13H1zM16 8h4l3 3v5h-7"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>;
    case 'alert': return <svg {...common}><path d="M12 2 2 21h20Z"/><path d="M12 9v5M12 18v.01"/></svg>;
    case 'check': return <svg {...common}><path d="m20 6-11 11-5-5"/></svg>;
    case 'x': return <svg {...common}><path d="M18 6 6 18M6 6l12 12"/></svg>;
    case 'arrow-up': return <svg {...common}><path d="M12 19V5M5 12l7-7 7 7"/></svg>;
    case 'arrow-down': return <svg {...common}><path d="M12 5v14M19 12l-7 7-7-7"/></svg>;
    case 'arrow-right': return <svg {...common}><path d="M5 12h14M12 5l7 7-7 7"/></svg>;
    case 'send': return <svg {...common}><path d="m22 2-7 20-4-9-9-4z"/></svg>;
    case 'refresh': return <svg {...common}><path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/></svg>;
    case 'download': return <svg {...common}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>;
    case 'package': return <svg {...common}><path d="M16 16V8a4 4 0 0 0-8 0v8"/><rect x="2" y="9" width="20" height="13" rx="2"/></svg>;
    case 'users': return <svg {...common}><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
    case 'sun': return <svg {...common}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>;
    case 'calendar': return <svg {...common}><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>;
    case 'moon': return <svg {...common}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>;
    case 'menu': return <svg {...common}><path d="M3 12h18M3 6h18M3 18h18"/></svg>;
    case 'more': return <svg {...common}><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>;
    case 'expand': return <svg {...common}><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>;
    case 'info': return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>;
    case 'help': return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2-3 4M12 17h.01"/></svg>;
    case 'bell': return <svg {...common}><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>;
    case 'flag': return <svg {...common}><path d="M4 21V4h13l-2 4 2 4H4"/></svg>;
    case 'tag': return <svg {...common}><path d="M20 12 12 4H4v8l8 8z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>;
    case 'globe': return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>;
    case 'store': return <svg {...common}><path d="M3 3h18l-1 6H4z"/><path d="M5 9v11h14V9"/><path d="M9 22v-7h6v7"/></svg>;
    case 'eye': return <svg {...common}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>;
    case 'edit': return <svg {...common}><path d="M11 4H4v16h16v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
    case 'trash': return <svg {...common}><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>;
    case 'sort': return <svg {...common}><path d="M3 6h12M3 12h8M3 18h4"/><path d="m17 7 3-3 3 3M20 4v16M23 17l-3 3-3-3"/></svg>;
    case 'lightning': return <svg {...common}><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>;
    default: return <svg {...common}><circle cx="12" cy="12" r="9"/></svg>;
  }
}

// ── Sparkline (line chart, premium) ─────────────────
function Sparkline({ data, width = 80, height = 24, color = 'var(--accent)', fill = true, strokeWidth = 1.4, showDots = true, padY = 4 }) {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / Math.max(1, data.length - 1);
  const usableH = height - padY * 2;
  const points = data.map((v, i) => [i * stepX, padY + (1 - (v - min) / range) * usableH]);
  const path = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
  const area = `${path} L${width},${height} L0,${height} Z`;
  const id = 'sl-' + Math.random().toString(36).slice(2, 8);
  const last = points[points.length - 1];
  return (
    <svg width={width} height={height} style={{ display: 'block', overflow: 'visible' }}>
      {fill && (
        <>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.22"/>
              <stop offset="100%" stopColor={color} stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${id})`} />
        </>
      )}
      <path d={path} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinejoin="round" strokeLinecap="round" />
      {showDots && (
        <>
          <circle cx={last[0]} cy={last[1]} r="3.2" fill="var(--surface)" stroke={color} strokeWidth="1.4"/>
        </>
      )}
    </svg>
  );
}

// ── ChartArea — 历史 + 预测的拼接折线 ──────────────
// 历史段实线 + 渐变面;预测段虚线、不填充;最后一个历史点和第一个预测点连续。
function ChartArea({ history = [], future = [], height = 140, color = 'var(--accent)' }) {
  const all = [...history, ...future];
  if (all.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, color: 'var(--text-4)' }}>
        暂无趋势数据
      </div>
    );
  }
  const min = Math.min(...all);
  const max = Math.max(...all);
  const range = max - min || 1;
  const padY = 10;
  const padX = 6;
  const innerW = (w) => w - padX * 2;
  const innerH = height - padY * 2;
  const id = 'ca-' + Math.random().toString(36).slice(2, 8);
  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg viewBox={`0 0 800 ${height}`} preserveAspectRatio="none" width="100%" height={height} style={{ display: 'block', overflow: 'visible' }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.22"/>
            <stop offset="100%" stopColor={color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        {(() => {
          const W = 800;
          const totalN = all.length;
          const stepX = innerW(W) / Math.max(1, totalN - 1);
          const points = all.map((v, i) => [padX + i * stepX, padY + (1 - (v - min) / range) * innerH]);

          const histPts = points.slice(0, history.length);
          // 让 future 段从 history 最后一点延续(避免视觉断层)
          const futStart = history.length > 0 ? history.length - 1 : 0;
          const futPts = points.slice(futStart);

          const histPath = histPts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
          const futPath = futPts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
          const area = histPath
            ? `${histPath} L${histPts[histPts.length - 1][0]},${height} L${histPts[0][0]},${height} Z`
            : '';

          // 分隔线 — history / future 边界
          const boundaryX = history.length > 0 ? padX + (history.length - 1) * stepX : null;

          return (
            <>
              {histPath && <path d={area} fill={`url(#${id})`}/>}
              {histPath && <path d={histPath} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round"/>}
              {futPath && <path d={futPath} fill="none" stroke={color} strokeWidth="1.6" strokeDasharray="4 4" strokeLinejoin="round" strokeLinecap="round" opacity="0.85"/>}
              {boundaryX != null && (
                <line x1={boundaryX} x2={boundaryX} y1={padY} y2={height - padY}
                  stroke="var(--border)" strokeDasharray="2 3" strokeWidth="1"/>
              )}
            </>
          );
        })()}
      </svg>
    </div>
  );
}

// ── Sparkbar ──────────────────────────
function Sparkbar({ data, width = 80, height = 24, color = 'var(--text-3)' }) {
  const max = Math.max(...data, 1);
  const bw = width / data.length;
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {data.map((v, i) => {
        const h = Math.max(1, (v / max) * (height - 2));
        return <rect key={i} x={i * bw + 0.5} y={height - h} width={Math.max(1, bw - 1.5)} height={h} fill={color} opacity="0.55" rx="1"/>;
      })}
    </svg>
  );
}

// ── Donut ──────────────────────────
function Donut({ values, colors, size = 92, thickness = 12, gap = 2 }) {
  const total = values.reduce((a, b) => a + b, 0) || 1;
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width={size} height={size} style={{ display: 'block', transform: 'rotate(-90deg)' }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--surface-hover)" strokeWidth={thickness}/>
      {values.map((v, i) => {
        const len = (v / total) * c;
        const dash = `${Math.max(0, len - gap)} ${c - Math.max(0, len - gap)}`;
        const offset = -acc;
        acc += len;
        return (
          <circle key={i} cx={size/2} cy={size/2} r={r} fill="none"
            stroke={colors[i]} strokeWidth={thickness} strokeDasharray={dash}
            strokeDashoffset={offset} strokeLinecap="butt"/>
        );
      })}
    </svg>
  );
}

// ── ProgressBar (segmented) ──────────────────────────
function StackedBar({ segments, height = 6 }) {
  const total = segments.reduce((a, s) => a + s.value, 0) || 1;
  return (
    <div style={{ display: 'flex', height, borderRadius: 999, overflow: 'hidden', background: 'var(--surface-hover)', gap: 1 }}>
      {segments.map((s, i) => (
        <div key={i} title={`${s.label} · ${s.value}`} style={{ width: `${(s.value / total) * 100}%`, background: s.color }}/>
      ))}
    </div>
  );
}

// ── ErrorBoundary — 防止单个组件 throw 后整页黑屏 ──────────────
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(err, info) { console.error('[ErrorBoundary]', err, info); }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          padding: 16, margin: 12,
          border: '1px solid var(--p1)',
          borderRadius: 'var(--r)',
          background: 'var(--p1-soft)',
          color: 'var(--p1-strong)',
          fontSize: 12, lineHeight: 1.55,
        }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>组件渲染异常</div>
          <div className="mono" style={{ fontSize: 11, opacity: 0.85, whiteSpace: 'pre-wrap' }}>
            {String(this.state.error?.message || this.state.error)}
          </div>
          <button className="btn sm" style={{ marginTop: 10 }}
            onClick={() => this.setState({ error: null })}>重试</button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Drawer ──────────────────────────
function Drawer({ open, onClose, width = 480, side = 'right', children, title, mode = 'overlay' }) {
  // mode: 'overlay' (covers content w/ scrim) or 'split' (no scrim)
  if (!open) return null;
  return (
    <>
      {mode === 'overlay' && (
        <div onClick={onClose} className="fade-in" style={{
          position: 'fixed', inset: 0, background: 'var(--overlay)', zIndex: 90,
        }}/>
      )}
      <div className="fade-in" style={{
        position: mode === 'split' ? 'relative' : 'fixed',
        top: 0, [side]: 0, height: '100%', width,
        background: 'var(--surface)',
        borderLeft: side === 'right' ? '1px solid var(--border)' : 'none',
        borderRight: side === 'left' ? '1px solid var(--border)' : 'none',
        boxShadow: mode === 'overlay' ? 'var(--sh-pop)' : 'none',
        zIndex: 91,
        display: 'flex',
        flexDirection: 'column',
        animation: mode === 'overlay' ? 'slideRight .2s cubic-bezier(.3,.7,.4,1)' : 'fadeIn .2s',
      }}>
        {children}
      </div>
    </>
  );
}

// ── Modal ──────────────────────────
function Modal({ open, onClose, width = 720, children }) {
  if (!open) return null;
  return (
    <div className="fade-in" style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'var(--overlay)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        width, maxWidth: '100%', maxHeight: 'calc(100vh - 48px)',
        background: 'var(--surface)',
        borderRadius: 'var(--r-lg)',
        boxShadow: 'var(--sh-pop)',
        border: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {children}
      </div>
    </div>
  );
}

// ── Toast ──────────────────────────
function Toast({ msg, kind = 'info' }) {
  if (!msg) return null;
  const color = kind === 'success' ? 'var(--success)' : kind === 'error' ? 'var(--danger)' : 'var(--text)';
  return (
    <div className="fade-in" style={{
      position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
      background: 'var(--text)', color: 'var(--text-inverse)',
      padding: '8px 14px', borderRadius: 8, fontSize: 12.5,
      boxShadow: 'var(--sh-pop)', zIndex: 200,
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color }}/>
      {msg}
    </div>
  );
}

// ── DatePicker ──────────────────────────
function datePickerParse(value) {
  if (!value) return null;
  const parts = String(value).split('-').map(Number);
  if (parts.length !== 3 || parts.some(n => !Number.isFinite(n))) return null;
  const d = new Date(parts[0], parts[1] - 1, parts[2]);
  return Number.isNaN(d.getTime()) ? null : d;
}

function datePickerFormat(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function DatePicker({ value, onChange, placeholder = '选择日期', title, testId, style, disabled = false }) {
  const selected = datePickerParse(value);
  const baseMonth = selected || new Date();
  const [open, setOpen] = React.useState(false);
  const [month, setMonth] = React.useState(() => new Date(baseMonth.getFullYear(), baseMonth.getMonth(), 1));

  React.useEffect(() => {
    if (selected) setMonth(new Date(selected.getFullYear(), selected.getMonth(), 1));
  }, [value]);

  const start = new Date(month.getFullYear(), month.getMonth(), 1);
  const offset = start.getDay();
  const cells = Array.from({ length: 42 }, (_, i) => {
    const d = new Date(month.getFullYear(), month.getMonth(), i - offset + 1);
    return d;
  });
  const todayYmd = datePickerFormat(new Date());
  const selectedYmd = selected ? datePickerFormat(selected) : '';

  const setMonthOffset = (n) => {
    setMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + n, 1));
  };

  const choose = (d) => {
    onChange?.(datePickerFormat(d));
    setOpen(false);
  };

  return (
    <div style={{ position: 'relative', ...style }}>
      <button
        type="button"
        data-testid={testId}
        disabled={disabled}
        title={title}
        className="txt"
        onClick={() => !disabled && setOpen(true)}
        style={{
          width: '100%',
          minWidth: 0,
          height: 32,
          padding: '0 8px',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          color: value ? 'var(--text)' : 'var(--text-4)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          textAlign: 'left',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          background: 'var(--surface)',
        }}>
        <Icon name="calendar" size={12}/>
        <span style={{ flex: 1 }}>{value || placeholder}</span>
        {value && (
          <span
            onClick={(e) => {
              e.stopPropagation();
              onChange?.('');
            }}
            style={{ color: 'var(--text-4)', fontFamily: 'var(--font-sans)', fontSize: 13 }}>
            ×
          </span>
        )}
      </button>

      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 420 }}/>
          <div
            onClick={e => e.stopPropagation()}
            className="fade-in"
            style={{
              position: 'absolute',
              top: 36,
              left: 0,
              zIndex: 421,
              width: 248,
              padding: 10,
              background: 'var(--surface)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--r-md)',
              boxShadow: 'var(--sh-pop)',
              fontFamily: 'var(--font-sans)',
            }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <button className="btn ghost icon sm" type="button" onClick={() => setMonthOffset(-1)}><Icon name="chevron-left" size={13}/></button>
              <div className="tabular" style={{ fontSize: 12.5, fontWeight: 600 }}>
                {month.getFullYear()} 年 {month.getMonth() + 1} 月
              </div>
              <button className="btn ghost icon sm" type="button" onClick={() => setMonthOffset(1)}><Icon name="chevron-right" size={13}/></button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 3, marginBottom: 4 }}>
              {['日','一','二','三','四','五','六'].map(w => (
                <div key={w} style={{ textAlign: 'center', fontSize: 10.5, color: 'var(--text-4)', padding: '3px 0' }}>{w}</div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 3 }}>
              {cells.map((d) => {
                const ymd = datePickerFormat(d);
                const inMonth = d.getMonth() === month.getMonth();
                const isSelected = selectedYmd === ymd;
                const isToday = todayYmd === ymd;
                return (
                  <button
                    key={ymd}
                    type="button"
                    onClick={() => choose(d)}
                    className="tabular"
                    style={{
                      height: 28,
                      border: `1px solid ${isSelected ? 'var(--accent)' : isToday ? 'var(--border-strong)' : 'transparent'}`,
                      borderRadius: 6,
                      background: isSelected ? 'var(--accent-soft)' : 'transparent',
                      color: isSelected ? 'var(--accent-text)' : inMonth ? 'var(--text)' : 'var(--text-4)',
                      cursor: 'pointer',
                      fontSize: 11.5,
                      fontWeight: isSelected ? 700 : 500,
                    }}>
                    {d.getDate()}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ── PriorityBadge ──────────────────────────
// compact=true → 仅展示级别（P1/P2/P3/安全），不带描述词，用于宽度紧张的列
function PriorityBadge({ level, withDot = true, size = 'sm', compact = false }) {
  const full = { p1: 'P1 紧急', p2: 'P2 重要', p3: 'P3 关注', safe: '安全' };
  const short = { p1: 'P1', p2: 'P2', p3: 'P3', safe: '安全' };
  const labels = compact ? short : full;
  return (
    <span className={'chip ' + level} style={{ fontSize: size === 'sm' ? 11.5 : 12.5, height: size === 'sm' ? 22 : 26 }}>
      {withDot && <span className={'dot ' + level}/>}
      {labels[level]}
    </span>
  );
}

// ── KV row ──────────────────────────
function KV({ k, v, hint, style }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, ...style }}>
      <div style={{ fontSize: 11.5, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 4 }}>
        {k}{hint && <span title={hint} style={{ cursor: 'help', fontSize: 10 }}>ⓘ</span>}
      </div>
      <div className="tabular" style={{ fontSize: 14, fontWeight: 500 }}>{v}</div>
    </div>
  );
}

// ── ProductImage placeholder ──────────────────────────
function ProductImage({ src, alt, size = 36, label }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: 6,
      background: 'linear-gradient(180deg, var(--surface-3), var(--surface-2))',
      border: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: 'var(--text-3)', fontSize: 9, fontFamily: 'var(--font-mono)',
      flex: 'none', overflow: 'hidden',
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.04)',
    }}>
      {label || (alt || '').slice(0, 3)}
    </div>
  );
}

// ── Format helpers ──────────────────────────
const fmt = {
  date: (d) => d ? `${d.getMonth() + 1}/${d.getDate()}` : '—',
  dateLong: (d) => d ? `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` : '—',
  time: (d) => d ? `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}` : '—',
  rel: (d) => {
    if (!d) return '—';
    const today = new Date('2026-05-04T08:42:00');
    const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
    if (diff === 0) return '今天';
    if (diff === 1) return '明天';
    if (diff > 0) return diff + ' 天后';
    if (diff === -1) return '昨天';
    return Math.abs(diff) + ' 天前';
  },
  num: (n) => n == null ? '—' : n.toLocaleString('en-US'),
  money: (n) => n == null ? '—' : '$' + n.toLocaleString('en-US'),
  // Split currency for premium typography: $ + body
  moneySplit: (n) => n == null ? ['', '—'] : ['$', n.toLocaleString('en-US')],
  pct: (n) => n == null ? '—' : (n.toFixed(1) + '%'),
};

// ── Premium numeric display ──────────────────────
// Renders a number with subtle currency prefix + optional unit suffix.
// Use inside a `.num-display` styled container for proper kerning.
function NumDisplay({ value, currency, unit, color, size = 32 }) {
  return (
    <span className="num-display" style={{ fontSize: size, color: color || 'var(--text)' }}>
      {currency && <span className="currency">{currency}</span>}
      {value}
      {unit && <span className="unit">{unit}</span>}
    </span>
  );
}

// ── Trend chip (↑ 2.4%) ─────────────────────────
function TrendChip({ value, suffix = '%', tooltip = '较昨日' }) {
  if (value == null) return null;
  const dir = value > 0.05 ? 'up' : value < -0.05 ? 'down' : 'flat';
  const arrow = dir === 'up' ? '↑' : dir === 'down' ? '↓' : '→';
  const sign = value > 0 ? '+' : '';
  return (
    <span className={'trend ' + dir} title={tooltip}>
      <span style={{ fontSize: '0.95em', lineHeight: 1 }}>{arrow}</span>
      {sign}{value.toFixed(1)}{suffix}
    </span>
  );
}

Object.assign(window, {
  Icon, Sparkline, Sparkbar, ChartArea, Donut, StackedBar,
  Drawer, Modal, Toast, PriorityBadge, KV, ProductImage, fmt,
  NumDisplay, TrendChip, ErrorBoundary,
});
