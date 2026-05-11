// 浮动 AI 按钮 (FAB) — 强化入口。
// 始终显示"AI 分析" 文字 + bot 图标,有渐变 + 微脉冲光晕。
// 抽屉打开时自动隐藏,避免遮挡。

function AIFab({ onOpen, hidden }) {
  if (hidden) return null;

  const accent = 'var(--accent)';
  const grad = `linear-gradient(135deg, ${accent} 0%, color-mix(in srgb, ${accent} 50%, #c084fc) 100%)`;

  return (
    <>
      <style>{`
        @keyframes ai-fab-pulse {
          0%, 100% { box-shadow: 0 10px 28px -6px color-mix(in srgb, var(--accent) 75%, transparent),
                                 0 4px 10px rgba(0,0,0,0.22),
                                 0 0 0 0 color-mix(in srgb, var(--accent) 45%, transparent); }
          50%      { box-shadow: 0 10px 28px -6px color-mix(in srgb, var(--accent) 75%, transparent),
                                 0 4px 10px rgba(0,0,0,0.22),
                                 0 0 0 14px transparent; }
        }
        .ai-fab {
          animation: ai-fab-pulse 2.6s ease-in-out infinite;
          transition: transform 160ms ease, filter 160ms ease;
        }
        .ai-fab:hover {
          transform: translateY(-2px);
          filter: brightness(1.08) saturate(1.05);
        }
        .ai-fab:active { transform: translateY(0); }
      `}</style>
      <button
        className="ai-fab"
        onClick={onOpen}
        title="AI 分析 (⌘J)"
        style={{
          position: 'fixed',
          right: 24,
          bottom: 24,
          zIndex: 90,
          height: 52,
          padding: '0 20px 0 16px',
          borderRadius: 26,
          border: '1px solid rgba(255,255,255,0.18)',
          background: grad,
          color: '#fff',
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 10,
          fontFamily: 'inherit',
          fontSize: 14,
          fontWeight: 600,
          letterSpacing: '-0.005em',
          whiteSpace: 'nowrap',
        }}>
        <Icon name="bot" size={20} color="#fff" stroke={2} />
        <span>AI 分析</span>
        <span style={{
          fontSize: 10.5,
          padding: '2px 6px',
          background: 'rgba(255,255,255,0.20)',
          borderRadius: 5,
          fontWeight: 500,
          letterSpacing: 0.2,
        }}>⌘J</span>
      </button>
    </>
  );
}

Object.assign(window, { AIFab });
