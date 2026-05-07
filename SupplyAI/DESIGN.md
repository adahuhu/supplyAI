# SupplyAI — DESIGN.md

> Design system for **SupplyAI**, a supply-chain analytics workspace.
> Aesthetic lineage: **Linear-like** product UI — ultra-minimal, precise, lavender accent, dense data tables, restrained motion.
> Read this file before generating UI. Treat values as authoritative; don't invent new ones.

---

## 1. Visual Theme & Atmosphere

- **Mood**: quiet, precise, data-dense. Built for operators who scan tables and KPI numbers, not for marketing pages.
- **Density**: compact. Default row height 40px (32-cell variant: 34px). Generous use of `tabular-nums` so numbers align vertically across rows.
- **Philosophy**:
  - Color is a **signal**, not decoration. The lavender accent appears only on (a) primary CTAs, (b) the active sidebar item, (c) focus rings, (d) sparkline strokes.
  - Risk colors (red/amber/green) appear **only** on risk indicators (chips, dots, donut slices). Never used as backgrounds for unrelated content.
  - Type carries the hierarchy. Surfaces are flat; elevation is hairline + soft shadow, never glassy.
- **Atmosphere split**:
  - **Light mode** = cool neutral gray (oklch hue 265). Reads as "professional analyst tool", close to Linear's daylight surface.
  - **Dark mode** = near-black graphite stack (`#08090A` → `#1D1E22`). Matches Linear's hero workspace look.

---

## 2. Color Palette & Roles

All colors are defined in `tokens.css` as CSS custom properties. **Use the variable, never the literal value.**

### 2.1 Surfaces

| Token | Light | Dark | Role |
|-------|-------|------|------|
| `--bg` | `oklch(98.6% 0.004 265)` | `#08090A` | Page background |
| `--bg-sunken` | `oklch(96.8% 0.005 265)` | `#0C0D0F` | Groove behind cards / sidebar gradient bottom |
| `--surface` | `oklch(100% 0 0)` | `#111113` | Cards, modals, top-level surfaces |
| `--surface-2` | `oklch(98.4% 0.004 265)` | `#16171A` | Nested surfaces (input bg, sidebar) |
| `--surface-3` | `oklch(96.5% 0.005 265)` | `#1D1E22` | Deepest nest (hover popovers) |
| `--surface-hover` | `oklch(96.0% 0.006 265)` | `#202126` | Row / button hover |
| `--overlay` | `oklch(20% 0.01 265 / 0.42)` | `rgba(0,0,0,0.68)` | Modal scrim |

### 2.2 Borders

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `--border` | `mix(text, 7%)` | `rgba(255,255,255,0.075)` | Default hairline (1px) |
| `--border-strong` | `mix(text, 14%)` | `rgba(255,255,255,0.145)` | Hover, focus container |
| `--border-input` | `mix(text, 12%)` | `rgba(255,255,255,0.11)` | Form controls |

### 2.3 Text (warm-neutral graphite, oklch hue 265)

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `--text` | `oklch(20% 0.012 265)` | `#F7F8F8` | Primary body & display |
| `--text-2` | `oklch(38% 0.010 265)` | `#C9CDD2` | Secondary labels |
| `--text-3` | `oklch(55% 0.008 265)` | `#8A8F98` | Muted (units, captions, table headers) |
| `--text-4` | `oklch(70% 0.006 265)` | `#5F646D` | Disabled, deepest-muted |
| `--text-inverse` | `oklch(98% 0.003 265)` | `#08090A` | Text on solid accent / chips |

### 2.4 Accent — Linear lavender

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `--accent` | `#5E6AD2` | `#5E6AD2` | Primary CTA fill, sparkline default, focus rings |
| `--accent-hover` | `#6F7AEB` | `#6F7AEB` | Hover state for the above |
| `--accent-soft` | `rgba(94,106,210,0.10)` | `rgba(94,106,210,0.14)` | Active sidebar bg, selected row, focus halo |
| `--accent-soft-2` | `rgba(94,106,210,0.18)` | `rgba(94,106,210,0.22)` | Stronger soft fill (badges) |
| `--accent-text` | `#4651B8` | `#A7B0FF` | Accent-tinted text |

### 2.5 Risk palette (P1 / P2 / P3 / Safe)

Used **only** for the four risk levels in the SKU stocking model. Don't repurpose for unrelated UI.

| Level | Token | Light | Dark | Semantic |
|-------|-------|-------|------|----------|
| P1 紧急 | `--p1` / `--p1-soft` / `--p1-strong` | `oklch(56% 0.15 18)` | `#F97066` | "Stock-out within 7 days" |
| P2 重要 | `--p2` / `--p2-soft` / `--p2-strong` | `oklch(72% 0.14 70)` | `#FDBA74` | "Stock-out 8-15 days" |
| P3 关注 | `--p3` / `--p3-soft` / `--p3-strong` | `oklch(60% 0.12 152)` | `#4DD0A6` | "Stock-out 16-30 days" |
| Safe | `--safe` / `--safe-soft` | `oklch(65% 0.02 265)` | `#7E8794` | ">30 days" / no risk |

### 2.6 Semantic (forms, status)

| Token | Use |
|-------|-----|
| `--success` | Save success, healthy status dot |
| `--warn` | Validation soft-warning |
| `--danger` | Validation error, destructive button |
| `--info` | Informational callout |

---

## 3. Typography Rules

### 3.1 Font Stack

```css
--font-sans:
  "Inter var", "Inter",
  -apple-system, BlinkMacSystemFont,
  "PingFang SC", "HarmonyOS Sans SC", "Source Han Sans SC",
  "Helvetica Neue", "Segoe UI", "Microsoft YaHei",
  system-ui, sans-serif;
--font-display: "Inter var", "Inter", "PingFang SC", system-ui, sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
```

- **Inter (variable)** is the working font. Loaded from `https://rsms.me/inter/inter.css`.
- **PingFang SC / HarmonyOS Sans SC / Source Han Sans SC** for Chinese — Inter handles Latin, system Chinese fonts handle CJK glyphs. Don't override.
- **OpenType features** (always on for body):
  - `cv11` — single-storey `a`
  - `ss01` — alternate `g` (single-storey)
  - `calt` — contextual alternates
- **Numbers**: always `font-variant-numeric: tabular-nums` + `cv11 ss01 tnum` via `.tabular` or `.num-display`. Numbers in tables, KPIs, and timestamps must align vertically.

### 3.2 Hierarchy

| Class | Size | Weight | Tracking | Line-height | Use |
|-------|------|--------|----------|-------------|-----|
| `.h1` | 24px | 600 | `-0.022em` | 1.15 | Page title (`分析工作台`, `备货计划`) |
| `.h2` | 18px | 600 | `-0.014em` | 1.3 | Section title inside a panel |
| `.h3` | 14px | 600 | `-0.008em` | normal | Card title, dense subsection |
| body | 13px | 400 | normal | 1.5 | Default text |
| `.label` | 10.5px | 500 | `0.08em` UPPERCASE | normal | Section dividers in sidebar / form |
| `.muted` | inherit | inherit | inherit | inherit | `color: var(--text-3)` |
| `.num-display` | inherit | 540 | `-0.028em` | 1 | KPI big numbers |
| `.kbd` | 10.5px | regular | 0 | 1 | Keyboard shortcut chip (mono) |
| `.mono` | inherit | inherit | inherit | inherit | Code, IDs, tokens |

### 3.3 Number Display Construction

Big KPI numbers use `<NumDisplay>`:
- Currency prefix (`$`, `¥`) → `.currency` span: 0.62em, weight 500, color `--text-3`, vertical-align 0.18em.
- Unit suffix (`件`, `天`) → `.unit` span: 0.42em, weight 500, color `--text-3`.
- Letter-spacing on the number itself: `-0.028em`.

Don't render currency at full size next to the number — it overpowers the figure.

---

## 4. Component Stylings

### 4.1 Button — `.btn`

```css
height: 30px;
padding: 0 12px;
border-radius: 6px;       /* var(--r) */
border: 1px solid var(--border);
background: var(--surface);
font-size: 12.5px;
font-weight: 500;
letter-spacing: -0.005em;
transition: background .14s, border-color .14s, box-shadow .14s, transform .14s;
```

| Variant | When | Spec |
|---------|------|------|
| `.btn` | Default | Surface bg, hairline border |
| `.btn.primary` | Single primary CTA per view | `--accent` fill, white text, `inset 0 1px 0 rgba(255,255,255,.14)` |
| `.btn.accent` | Same as primary, slightly stronger shadow | `--accent` fill + `--sh-2` |
| `.btn.ghost` | Toolbar icons, muted secondary | Transparent, hover surface |
| `.btn.sm` | Dense toolbars | Height 26px, padding 0 8px, font 12px |
| `.btn.icon` | Icon-only square | Width 30px (or 26px with `.sm`) |

Hover: `background → --surface-hover`, `border → --border-strong`, plus a 3px `--accent-soft` halo box-shadow.
Active: `transform: translateY(0.5px)`.
Disabled: `opacity: 0.45; cursor: not-allowed`.

**Don't**: pile multiple primary buttons in a row; use icon + ghost; use shadows heavier than `--sh-2` on a button.

### 4.2 Chip — `.chip`

```css
height: 22px;
padding: 0 8px;
border-radius: 999px;       /* pill */
font-size: 11.5px;
font-weight: 500;
background: var(--surface-2);
color: var(--text-2);
border: 1px solid var(--border);
```

Variants (`.chip.p1` / `.p2` / `.p3` / `.safe`): use the corresponding `*-soft` background and `*-strong` text color, with **transparent** border.

### 4.3 Risk Dot — `.dot`

6px circle. `.dot.p1/p2/p3` get a 2px halo via `box-shadow: 0 0 0 2px var(--p*-soft)` to make the dot visible on dense rows.

### 4.4 Trend chip — `.trend`

```css
height: 18px; padding: 0 6px; border-radius: 4px;
font-size: 11px; font-weight: 500;
font-variant-numeric: tabular-nums;
```

`.up` → green soft, `.down` → red soft, `.flat` → safe soft. Format: `↑ 2.4%` / `↓ -1.8%`.

### 4.5 Input — `input.txt`, `select.sel`

```css
height: 30px; padding: 0 10px;
border: 1px solid var(--border-input);
border-radius: 6px;
background: var(--surface-2);
font-size: 12.5px;
```

Focus: `border-color: var(--accent)` + `box-shadow: 0 0 0 3px var(--accent-soft)`.
Select arrow: 10×6 inline SVG triangle, never the OS default.

### 4.6 Card — `.card`

```css
background: color-mix(in srgb, var(--surface) 94%, transparent);
border: 1px solid var(--border);
border-radius: 8px;     /* var(--r-md) */
box-shadow: var(--sh-inset-top);
```

Light: `--sh-inset-top` is `none` (flat). Dark: 1px white-3.5% inner top edge.

`.card.interactive` adds:
- pointer cursor
- on hover: `--border-strong`, `--surface-hover` blend, `--sh-3`, `transform: translateY(-1px)`

### 4.7 Sidebar nav item

- Inactive: transparent bg, transparent border, `--text-2`, weight 400.
- Active: `--accent-soft` bg, `--border-strong` border, `--accent-text`, weight 500, **and a 2px inset left rail in `--accent`** via `box-shadow: inset 2px 0 0 var(--accent)`.
- Hover: `--surface-hover` bg.

### 4.8 Topbar

- Height 52px.
- Background: `color-mix(in srgb, var(--surface) 86%, transparent)` + `backdrop-filter: blur(14px)`. **Never hardcode an RGBA bg** — that breaks one theme.
- Border-bottom: 1px `--border`.
- Search input is anchored, max-width 360px, with `⌘K` `.kbd` chip on the right.

### 4.9 Table — `table.t`

- `border-collapse: separate; border-spacing: 0;`
- `font-size: 12.5px`.
- `thead th`: sticky top, `--text-3`, font-size 11px, font-weight 500, text-transform **none** (Linear isn't all-caps).
- `tbody td`: padding `var(--row-pad-y) var(--row-pad-x)`, hairline border-bottom.
- Hover: `--surface-hover` blended at 76%.
- Selected row: `--accent-soft`.
- Numeric cells: `.num` (right-aligned, tabular-nums).

### 4.10 Filter segmented bar

Underline-on-active style. Active tab gets a 2px solid `--accent` bottom border, `--text` text, weight 600. Counts shown in a tabular-nums pill (`--surface-hover` bg, or `--accent-soft` when active).

### 4.11 Section marker — `.marker`

A 3px-wide, 1em-tall lavender strip placed before page titles. Subtle but unmistakably "this is a Linear-style heading."

### 4.12 Hero summary card

The "今日工作摘要"-style hero is the **single visual anchor** of a workspace page. **At most one per page.** It compresses scattered signals (high-risk count, urgency, scope, monetary impact) into one action-driven statement.

```
┌────────────────────────────────────────────────────┐
│ ┃                                                  │
│ ┃ TODAY'S SUMMARY                                  │
│ ┃                                                  │
│ ┃ 12 个 SKU  需要立即下采购                          │ ← 52px num
│ ┃                                                  │   18px statement
│ ┃ ● 8 个 7 天内断货 · 5 个店铺 · ¥48,200    [批量生成] │
│ ┃                                          [查看 →] │
└────────────────────────────────────────────────────┘
   3px accent rail
```

**Spec**:

| Property | Value |
|----------|-------|
| Width | Full content width (no grid columns) |
| Padding | `22px 26px` (more generous than regular cards) |
| Background | `linear-gradient(135deg, var(--accent-soft) 0%, transparent 55%), var(--surface)` |
| Left rail | 3px solid `var(--accent)` absolutely positioned |
| Hero number | 52px, weight 540, letter-spacing -0.028em (`.num-display .tabular`) |
| Statement | 18px, weight 500, letter-spacing -0.012em |
| Meta line | 12.5px, color `--text-2`, separator `·` in `--text-4` |
| Primary CTA | `.btn.primary`, height **36px** (taller than regular 30px) |
| Secondary | `.btn.ghost.sm` with `--accent-text` color |
| Section above | `.label` UPPERCASE eyebrow ("今日工作摘要") |

**Rules**:

- Hero is **always** the first content unit after the page title. Above the financial / KPI rows, above any panel grid.
- The number in the hero must be **actionable** — answer "what should I do today?" not "what is the system state?"
- Never put two hero cards on one page. If you need a second focal moment, demote it to a regular `.card`.
- The accent left rail + accent-soft gradient is the only place we use a tinted card background. Keep it scarce so it remains a "hero only" signal.

---

## 5. Layout Principles

### 5.1 App shell

- **Sidebar (left)**: 220px expanded / 56px collapsed. Border-right hairline. Background is a vertical gradient `--surface-2 → --bg-sunken`. Sections separated by an UPPERCASE `.label`.
- **Topbar**: 52px. Sits above content area. Search left-of-center, status + AI button right.
- **Content area**: `padding: 18px 22px 40px`. Max-width 1480px, min-width 980px (data-dense — don't go narrower than this on desktop).

### 5.2 Spacing scale

```css
--gap-1: 4px;   /* tight inline (chip+icon) */
--gap-2: 8px;   /* default item gap */
--gap-3: 12px;  /* card-internal section gap */
--gap-4: 16px;  /* card-to-card gap, page row gap */
--gap-5: 24px;  /* section break */
--gap-6: 32px;  /* major section break */
```

Use only these. Don't introduce `--gap-7` or arbitrary 5/7/9/11px values.

### 5.3 Grid patterns

| Layout | Grid spec | Notes |
|--------|-----------|-------|
| KPI row (5-up) | `repeat(auto-fit, minmax(208px, 1fr))`, gap 10 | Used for daily snapshot KPIs |
| Panel row (4-up) | `repeat(auto-fit, minmax(280px, 1fr))`, gap 10 | Wider min so panel titles don't wrap |
| 2-col side-by-side | `grid-template-columns: 1fr 1fr`, gap 16 | Symmetric callouts |
| Detail KV grid | `repeat(3, 1fr)` for compact panel-internal stat triples | |

**Never** use floats for layout; flex/grid only.

### 5.4 Whitespace philosophy

- Between rows in a table: 0px (let hairline borders do the work).
- Between sibling cards: 10-16px.
- Between page sections: 16-24px.
- Inside a card: 13-14px padding, 9-12px gap between header/body/footer.

---

## 6. Depth & Elevation

The system uses **four** shadow tokens. Don't author new shadows.

| Token | Spec | Use |
|-------|------|-----|
| `--sh-1` | `0 1px 0 ink/4%` | Sticky table header, subtle separator |
| `--sh-2` | `0 1px 1.5px ink/4%, 0 0 0 0.5px ink/6%` | Default card, button.accent |
| `--sh-3` | `0 1px 2px / 0 8px 24px -8px ink/10% / 0 0 0 0.5px ink/6%` | Hover-lifted card |
| `--sh-pop` | `0 12px 40px -8px ink/18%, 0 0 0 0.5px ink/8%` | Modal, command palette, popover |
| `--sh-inset-top` | Light: `none`. Dark: `inset 0 1px 0 rgba(255,255,255,0.035)` | Card top edge, dark-mode only |

**Surface hierarchy** (z-axis intent, not real z-index):

```
overlay scrim          (--overlay)
  └ modal               (--sh-pop, --surface)
     └ popover/tooltip  (--sh-pop, --surface-3)
topbar                  (sticky, --surface @ 86% + blur)
content
  └ card                (--sh-2, --surface)
     └ nested panel     (no shadow, --surface-2)
sidebar                 (linear gradient, no shadow)
page                    (--bg)
```

Don't stack three cards with `--sh-3`. Pick one focal layer.

---

## 7. Do's and Don'ts

### ✅ Do

- Use **CSS variables** from `tokens.css`. Always.
- Use `tabular-nums` on every number that appears in a list, table, or KPI.
- Keep transitions ≤ 200ms. Default to 140-180ms.
- Use the lavender accent **sparingly** — one accent moment per row of UI.
- Use `--text-3` for muted captions, `--text-2` for secondary labels — never invent a new gray.
- Render Chinese with the system stack; don't force a webfont for CJK.
- Pair every interactive element with a focus state (`box-shadow: 0 0 0 3px var(--accent-soft)`).
- Write hairline dividers as `1px solid var(--border)` — never `2px`, never `--text-3`.

### ❌ Don't

- Don't hardcode colors. `#fff`, `rgba(17,17,19,0.86)`, `#5E6AD2` literals are forbidden outside `tokens.css`.
- Don't introduce new accent colors. Lavender is the only "brand" color.
- Don't use the risk palette (red/amber/green) outside risk indicators.
- Don't use heavy/glassy inner highlights on light-mode cards (we set `--sh-inset-top: none` for a reason).
- Don't all-caps table headers. Linear isn't carbon/Material; lower-case `--text-3` headers only.
- Don't put two primary buttons next to each other.
- Don't use border-radius greater than 12px on data UI (cards/panels). Reserve 16px for marketing-style hero blocks if they ever exist.
- Don't use shadows for state. Use border-color and background blends.
- Don't pad inputs taller than 30px on desktop. Density matters.
- Don't use serif typefaces, condensed sans, or display fonts. Inter only.
- Don't stack `motion-safe` parallax / scroll-triggered animation. The product is calm.
- Don't render dollar/yuan signs at full size — always scale them per `.num-display .currency`.

---

## 8. Responsive Behavior

### 8.1 Breakpoints

| Width | Behavior |
|-------|----------|
| `≥ 1280px` | Full layout, all 5 KPIs in one row, sidebar expanded |
| `1024–1280px` | KPI row wraps to 3+2; sidebar still expanded |
| `760–1024px` | Sidebar collapsible (icon-only @ 56px); search input shrinks |
| `< 760px` | Sidebar becomes off-canvas; topbar hides search; AI button collapses to icon-only |

The `narrow` flag in `Topbar` triggers at `< 760px`.

### 8.2 Touch targets

- Minimum tap area: 30×30px on mobile (matches button height). Ghost icon buttons: pad to 32×32 via the parent.
- `kbd` chips and `.dot` indicators are decorative — never interactive on touch.

### 8.3 Collapsing strategy

- KPI row: `auto-fit minmax(208px, 1fr)` collapses naturally.
- Panel row: `auto-fit minmax(280px, 1fr)` — 280 chosen so 4-up wraps to 2+2 on a 768-820px viewport before titles can wrap.
- Tables: horizontal scroll inside `.tbl-wrap`. Don't try to stack table rows into cards on mobile — operators expect tabular layout.
- Modal: full-bleed at `< 640px`, otherwise centered max-width 640-800px.

### 8.4 Density variants

```css
[data-density="compact"] { --row-h: 34px; --row-pad-y: 7px; --row-pad-x: 10px; }
[data-density="comfy"]   { --row-h: 48px; --row-pad-y: 14px; --row-pad-x: 14px; }
```

Default is 40px. Compact for power users on long scrolls; comfy for new users / accessibility.

---

## 9. Agent Prompt Guide

### 9.1 Quick reference

```
Theme:        Linear-like, lavender accent #5E6AD2, oklch hue 265 grays
Font:         Inter var (body 13px, h1 24px / -0.022em)
Surfaces:     --bg / --surface / --surface-2 / --surface-3
Borders:      hairline 1px, var(--border) (~7% ink), var(--border-strong) (~14% ink)
Accent only:  primary CTA, active sidebar item, focus ring, sparkline
Risk only:    chip / dot / donut for P1 P2 P3 Safe
Shadows:      --sh-1 / --sh-2 / --sh-3 / --sh-pop (use one, don't stack)
Motion:       140-180ms, ease, restrained
Density:      40px row default, tabular-nums on every number
```

### 9.2 Ready-to-use prompts

**Build a new dashboard panel**
> Build a `.card` panel using SupplyAI tokens. Title in `.h3`, sub in `var(--text-3)` 11.5px. Body uses tabular-nums for any numbers. Padding 13-14px, internal gap 12px. No new shadows — `--sh-2` if hoverable, otherwise inherit from `.card`. Keep accent off unless it's a CTA inside.

**Build a data table view**
> Use `table.t` from `tokens.css`. Sticky thead with `--text-3` 11px non-uppercase headers. Tbody hover blends to `--surface-hover` at 76%. Numeric columns get `.num` class (right-aligned + tabular-nums). Selected rows: `--accent-soft` background. Wrap the table in `.tbl-wrap` for horizontal scroll.

**Build a KPI card**
> Use `<StatCard>` pattern: small dot+label (11.5px `--text-3`), big `<NumDisplay>` (size 27, optional currency/unit), trend chip (`.trend.up/.down`), and a Sparkline (28px tall, 1.25 stroke). One per metric. Don't add icons inside the value; they fight the number.

**Build a risk indicator**
> Use `.chip.p1/p2/p3/safe` for level chips, `.dot.p1/p2/p3/safe` for inline indicators, and `Donut` for distribution. Never invent a new red/amber/green for non-risk content.

**Build a settings modal**
> Use `--sh-pop` shadow on `--surface`. Title in `.h2`. Form fields are `input.txt` / `select.sel`, label-on-top, 12.5px label in `--text-2`. Footer right-aligned with `.btn.ghost` (Cancel) + `.btn.primary` (Save). Don't make the modal taller than 80vh; scroll the body.

### 9.3 Sanity checks before merging

- [ ] Every color comes from a CSS variable (no `#xxx` literals in JSX).
- [ ] Every number that isn't a single-digit count has `tabular-nums`.
- [ ] Hover/focus/active states defined for every interactive element.
- [ ] Light mode and dark mode both verified — no hardcoded `rgba(17,17,19,...)`-style values.
- [ ] No `transform: scale` on hover for cards larger than a button (Linear doesn't do this).
- [ ] No element uses `border-radius` > 12px in data UI.
- [ ] Page passes the squint test: should look like a quiet Linear/Vercel-class workspace, not a marketing page.

---

## Appendix A — File Map

| File | Owns |
|------|------|
| `tokens.css` | All design tokens (colors, type, spacing, shadows, base resets, utility classes `.btn .chip .card .dot .trend .kbd .num-display .h1 .h2 .h3 .label .mono .tabular table.t`) |
| `shell.jsx` | Sidebar + Topbar layout |
| `dashboard.jsx` | KPI cards, panel layouts, sparklines, donuts |
| `list.jsx` | Filter bar, data table, batch ops toolbar |
| `sku.jsx` | SKU detail page (large header, KPI row, sales chart) |
| `rules.jsx` | Replenishment + sales-forecast rules modal |
| `ai.jsx` | AI analysis side panel |

## Appendix B — Lineage

- **Strong influence**: Linear (lavender accent, density, typography, sidebar pattern, dark graphite stack).
- **Light influence**: Vercel (typographic hierarchy discipline, hairline-first surfaces, restrained motion).
- **Explicitly rejected**: Material (elevation theatre), Carbon (all-caps headers), Notion (warm beige tint), generic Bootstrap (heavy buttons, default focus rings).

If a design choice doesn't fit the Linear lineage and isn't explicitly listed here, **it doesn't belong in SupplyAI.**
