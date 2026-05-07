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
function TrendChip({ value, suffix = '%' }) {
  if (value == null) return null;
  const dir = value > 0.05 ? 'up' : value < -0.05 ? 'down' : 'flat';
  const arrow = dir === 'up' ? '↑' : dir === 'down' ? '↓' : '→';
  const sign = value > 0 ? '+' : '';
  return (
    <span className={'trend ' + dir}>
      <span style={{ fontSize: '0.95em', lineHeight: 1 }}>{arrow}</span>
      {sign}{value.toFixed(1)}{suffix}
    </span>
  );
}

Object.assign(window, {
  Icon, Sparkline, Sparkbar, Donut, StackedBar,
  Drawer, Modal, Toast, PriorityBadge, KV, ProductImage, fmt,
  NumDisplay, TrendChip,
});
