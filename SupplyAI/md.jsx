// 轻量 markdown 渲染 — 用于 AI 回答(无第三方依赖).
// 支持:**bold** / `code` / 标题 # ## ### / 列表 - / 表格 | a | b | / 段落
// 不支持:链接、图片、HTML 内联(不需要)

(function () {
  function escapeHtml(s) {
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // 风险等级 → 彩色 chip
  const RISK_BADGE = {
    'P1': '<span style="display:inline-flex;align-items:center;gap:3px;padding:1px 6px;background:var(--p1-soft);color:var(--p1-strong);border-radius:4px;font-size:0.85em;font-weight:600;letter-spacing:0.02em;">P1</span>',
    'P2': '<span style="display:inline-flex;align-items:center;gap:3px;padding:1px 6px;background:var(--p2-soft);color:var(--p2-strong);border-radius:4px;font-size:0.85em;font-weight:600;letter-spacing:0.02em;">P2</span>',
    'P3': '<span style="display:inline-flex;align-items:center;gap:3px;padding:1px 6px;background:var(--p3-soft);color:var(--p3-strong);border-radius:4px;font-size:0.85em;font-weight:600;letter-spacing:0.02em;">P3</span>',
  };

  // 行内:**bold**、`code`、P1/P2/P3 风险 badge
  function renderInline(s) {
    let html = escapeHtml(s);
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`([^`]+)`/g, '<code style="font-family:var(--font-mono);background:var(--surface-2);padding:1px 5px;border-radius:3px;font-size:0.92em;">$1</code>');
    // 整词 P1/P2/P3 → chip(不动嵌在 MSKU 之类内的 P1)
    html = html.replace(/(^|[\s一-鿿>·,;:])(P[123])(?=$|[\s一-鿿<·,;:])/g,
      (_m, prefix, lvl) => prefix + (RISK_BADGE[lvl] || lvl));
    return html;
  }

  // 表格块:|a|b|c| 第二行 |---|---|---|
  function renderTable(lines, startIdx) {
    const headerLine = lines[startIdx];
    const sepLine = lines[startIdx + 1] || '';
    if (!/^\s*\|.*\|\s*$/.test(headerLine)) return null;
    if (!/^\s*\|[\s\-:|]+\|\s*$/.test(sepLine)) return null;

    const splitRow = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
    const headers = splitRow(headerLine);
    const rows = [];
    let i = startIdx + 2;
    for (; i < lines.length; i++) {
      const ln = lines[i];
      if (!/^\s*\|.*\|\s*$/.test(ln)) break;
      rows.push(splitRow(ln));
    }
    const thead = '<thead><tr>' + headers.map(h => `<th style="text-align:left;padding:6px 10px;font-size:11px;color:var(--text-3);font-weight:500;border-bottom:1px solid var(--border);">${renderInline(h)}</th>`).join('') + '</tr></thead>';
    const tbody = '<tbody>' + rows.map(r =>
      '<tr>' + r.map((c, idx) =>
        `<td style="padding:6px 10px;font-size:12px;border-bottom:1px solid var(--border-subtle,rgba(255,255,255,0.04));${idx === 0 ? '' : 'text-align:right;font-variant-numeric:tabular-nums;'}">${renderInline(c)}</td>`
      ).join('') + '</tr>'
    ).join('') + '</tbody>';
    const html = `<div style="overflow:auto;margin:6px 0 8px;"><table style="border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--border);border-radius:6px;">${thead}${tbody}</table></div>`;
    return { html, consumed: i - startIdx };
  }

  function renderMarkdown(src) {
    if (!src) return '';
    const lines = src.split('\n');
    const out = [];
    let i = 0;
    let inList = false;
    while (i < lines.length) {
      const line = lines[i];

      // 表格
      const tbl = renderTable(lines, i);
      if (tbl) {
        if (inList) { out.push('</ul>'); inList = false; }
        out.push(tbl.html);
        i += tbl.consumed;
        continue;
      }

      // 标题
      const h = line.match(/^(#{1,4})\s+(.+)$/);
      if (h) {
        if (inList) { out.push('</ul>'); inList = false; }
        const level = Math.min(4, h[1].length);
        const sizes = { 1: 17, 2: 15, 3: 13, 4: 12.5 };
        out.push(`<div style="font-size:${sizes[level]}px;font-weight:600;margin:8px 0 4px;">${renderInline(h[2])}</div>`);
        i++;
        continue;
      }

      // 无序列表
      const li = line.match(/^\s*[-*]\s+(.+)$/);
      if (li) {
        if (!inList) { out.push('<ul style="margin:4px 0 6px;padding-left:18px;line-height:1.55;">'); inList = true; }
        out.push(`<li style="font-size:12.5px;margin:2px 0;">${renderInline(li[1])}</li>`);
        i++;
        continue;
      }

      // 段落 / 空行
      if (inList) { out.push('</ul>'); inList = false; }
      if (line.trim() === '') {
        out.push('<div style="height:4px;"></div>');
      } else {
        out.push(`<div style="font-size:12.5px;line-height:1.55;margin:2px 0;">${renderInline(line)}</div>`);
      }
      i++;
    }
    if (inList) out.push('</ul>');
    return out.join('');
  }

  window.renderMarkdown = renderMarkdown;
})();
