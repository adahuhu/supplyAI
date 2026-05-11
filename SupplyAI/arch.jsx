// 信息架构 + 路径页

function ArchPage({ setRoute }) {
  return (
    <div style={{ padding: '24px 32px 48px', maxWidth: 1480, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div className="h1">信息架构 & 用户路径</div>
        <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 4 }}>
          供应链分析工作台 — 9 大模块 · 3 个核心页面 · 4 个弹窗 / 抽屉
        </div>
      </div>

      <Panel title="信息架构图">
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.9, whiteSpace: 'pre', color: 'var(--text-2)', overflow: 'auto', padding: '4px 0' }}>
{`SupplyAI 工作台
├─ 工作台 Dashboard ─────────────── 快速发现问题
│   ├─ 风险总览（P1/P2/P3/安全）  → 点击筛选列表
│   ├─ 断货风险（FBA 7d）         → 跳转列表 + 筛选
│   ├─ 建议采购总览              → 批量生成入口
│   ├─ 库存健康（环形图 + 健康分）
│   ├─ 高风险 SKU 队列            → 行点击进入 SKU 详情
│   ├─ 今日建议动作（4 类）
│   └─ 全局 AI 入口              → 右侧抽屉
│
├─ 备货计划列表 ───────────────── 全量查询 + 批量
│   ├─ 筛选区（基础 6 项 + 高级 6 项）
│   ├─ 风险 Tab（全/P1/P2/P3/安全/建议/7d 断货）
│   ├─ 表格（21 列 · 双侧 sticky · 列配置）
│   ├─ 批量操作（规则 / 生成 PO / 导出）
│   └─ 默认排序：P1>P2>P3>安全 → 断货时间 → 更新
│
├─ SKU 分析详情 ──────────────── 单 SKU 决策
│   ├─ 头部信息（图、四级标识、负责人）
│   ├─ 风险结论（4 卡：等级/断货/采购量/采购时间）
│   ├─ 关键指标（7 KV）
│   ├─ 销量趋势（历史 30d + 预测 14d）
│   ├─ 库存构成（堆叠条 + 4 项）
│   ├─ 计算解释（7 行公式追溯）
│   ├─ 当前规则（特配标识 + 8 字段）
│   └─ SKU AI 助手 → 抽屉 / 分栏
│
├─ 全局 AI 面板  ────────────── Dashboard 上唤起
├─ SKU AI 面板   ────────────── SKU 详情内唤起
├─ 规则设置弹窗  ────────────── Tab1 补货 + Tab2 预测
├─ 列配置抽屉    ────────────── 列表页
└─ 采购计划创建确认 ────────── 跳转外部采购中心`}
        </div>
      </Panel>

      <Panel title="核心用户路径">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <PathRow num="01" title="运营 · 紧急处理日常"
            steps={['Dashboard', '点击 P1 卡片', '列表 P1 Tab', '勾选所选项', '批量生成采购计划', '跳转采购中心']}
            onClick={() => setRoute({ page: 'dashboard' })}/>
          <PathRow num="02" title="运营 · 单 SKU 异常分析"
            steps={['Dashboard', '高风险队列', 'SKU 详情', '查看计算解释', '问 AI 「为什么 P1」', '调整规则', '生成采购计划']}
            onClick={() => setRoute({ page: 'sku' })}/>
          <PathRow num="03" title="管理者 · 早晨健康检查"
            steps={['Dashboard', '全局 AI「今天该关注什么」', '点击 SKU', '看趋势', '回到列表筛选']}
            onClick={() => setRoute({ page: 'dashboard' })}/>
          <PathRow num="04" title="运营 · 批量配规则"
            steps={['列表', '筛选品线 / 高销量', '勾选 N 条', '批量规则设置', '保存 → 计算中 → 完成']}
            onClick={() => setRoute({ page: 'list' })}/>
        </div>
      </Panel>

      <Panel title="设计规范摘要">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
          <SpecCol title="颜色" items={[
            ['Accent', 'cool blue #2563eb · 仅用于交互重点'],
            ['P1 紧急', '#dc2626 + 8% 软底'],
            ['P2 重要', '#f59e0b + 10% 软底'],
            ['P3 关注', '#10b981 + 9% 软底'],
            ['安全', '#94a3b8 中性'],
            ['表面', '层级三级：bg / surface / surface-2'],
          ]}/>
          <SpecCol title="字体层级" items={[
            ['H1 / 22px / 600', '页面标题'],
            ['H2 / 17px / 600', '弹窗标题'],
            ['H3 / 14px / 600', '面板标题'],
            ['Body / 13px / 400', '正文'],
            ['Caption / 11.5px / 400', '辅助'],
            ['数字', 'tabular-nums + JetBrains Mono'],
          ]}/>
          <SpecCol title="表格密度" items={[
            ['紧凑 / 34px', '高频扫读默认'],
            ['标准 / 40px', '默认'],
            ['舒适 / 48px', '阅读优先'],
            ['Sticky', '左 2 列 + 右操作 + thead'],
            ['行 hover', '8% 悬停色 + 可选行选中色'],
          ]}/>
          <SpecCol title="图表风格" items={[
            ['趋势', '细线 1.6px + 16% 渐变填充'],
            ['预测', '虚线 + 斜纹背景区分历史/未来'],
            ['Sparkline', '行内 48×18 静音'],
            ['环形', '11px 厚度 · 2px 间隙'],
            ['堆叠条', '6–10px · 1px 间隙 · 圆角 999'],
          ]}/>
          <SpecCol title="状态样式" items={[
            ['Loading', '脉冲 ● + 「计算中…」'],
            ['Saving', '按钮文案切换 + 禁用'],
            ['Empty', '40px 圆图标 + 标题 + 子说明'],
            ['Error / Warn', '橙底 + 警告图标'],
            ['No permission', '橙底 + 操作建议'],
            ['Data 不足', '在字段位显示「数据不足」灰字'],
          ]}/>
          <SpecCol title="组件清单" items={[
            ['Layout', 'Sidebar / Topbar / Panel / Drawer / Modal'],
            ['Data', 'Table / FilterBar / FilterPill / Pagination'],
            ['Vis', 'Sparkline / Sparkbar / Donut / StackedBar'],
            ['Feedback', 'Toast / EmptyState / Pulse'],
            ['Domain', 'PriorityBadge / KV / ProductImage / CalcRow'],
            ['AI', 'AIBubble / AIAnswer / AIInput / AIPanelHeader'],
          ]}/>
        </div>
      </Panel>
    </div>
  );
}

function PathRow({ num, title, steps, onClick }) {
  return (
    <button onClick={onClick} className="btn ghost" style={{
      height: 'auto', padding: '12px 14px', textAlign: 'left',
      border: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
      alignItems: 'flex-start', gap: 8, background: 'var(--surface-2)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%' }}>
        <span className="mono" style={{ color: 'var(--text-3)', fontSize: 11 }}>{num}</span>
        <span className="h3">{title}</span>
        <span style={{ flex: 1 }}/>
        <Icon name="arrow-right" size={13} color="var(--text-3)"/>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        {steps.map((s, i) => (
          <React.Fragment key={i}>
            <span style={{
              padding: '3px 8px', borderRadius: 999,
              background: 'var(--surface)', border: '1px solid var(--border)',
              fontSize: 11.5, color: 'var(--text-2)',
            }}>{s}</span>
            {i < steps.length - 1 && <Icon name="chevron-right" size={11} color="var(--text-4)"/>}
          </React.Fragment>
        ))}
      </div>
    </button>
  );
}

function SpecCol({ title, items }) {
  return (
    <div>
      <div className="label" style={{ marginBottom: 8 }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {items.map(([k, v], i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: 10, fontSize: 12, padding: '4px 0', borderBottom: '1px dashed var(--border)' }}>
            <span style={{ width: 110, color: 'var(--text-2)', fontWeight: 500, flex: 'none' }}>{k}</span>
            <span style={{ color: 'var(--text-3)', flex: 1 }}>{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { ArchPage });
