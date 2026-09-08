#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/TeamDashboard.tsx"
CSS = ROOT / "client/src/team-dashboard-premium-v2-1.css"

if not TSX.exists():
    raise SystemExit("ERROR=TeamDashboard.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

required = [
    'import "../team-dashboard-premium-v1.css";',
    'import "../team-dashboard-premium-v2.css";',
    'tcrm-team-dashboard-premium',
    'tcrm-team-chart-card',
    'tcrm-team-performance-card',
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit("ERROR=V2_BASE_MISSING:" + ",".join(missing))

v21_import = 'import "../team-dashboard-premium-v2-1.css";'
if v21_import not in text:
    anchor = 'import "../team-dashboard-premium-v2.css";'
    text = text.replace(anchor, anchor + "\n" + v21_import, 1)

# Make Leads by Agent values unmistakably visible in both modes.
old_label = '<LabelList dataKey="count" position="top" fill="var(--team-text)" fontSize={11} fontWeight={800} />'
new_label = '<LabelList dataKey="count" position="top" offset={9} fill="var(--team-text)" fontSize={13} fontWeight={900} className="tcrm-team-bar-value" />'
if old_label in text:
    text = text.replace(old_label, new_label, 1)
elif 'className="tcrm-team-bar-value"' not in text:
    raise SystemExit("ERROR=Could not locate Leads by Agent LabelList")

css = r'''
/* TCRM Team Dashboard Premium V2.1 — Dark Recovery + fidelity corrections */

/* Keep light mode aligned to approved pearl/pastel concept. */
.tcrm-team-dashboard-premium .tcrm-team-bar-value{
  fill:#202a44!important;
  paint-order:stroke;
  stroke:rgba(255,255,255,.96);
  stroke-width:3px;
  stroke-linejoin:round;
}

/* DARK SURFACE SYSTEM — intentionally high-specificity and loaded after V2. */
.dark .tcrm-team-dashboard-premium{
  --team-text:#f4f7ff;
  --team-muted:#aebbd3;
  --team-surface:rgba(10,22,42,.94);
  --team-surface-strong:rgba(12,27,51,.985);
  --team-border:rgba(101,126,218,.28);
  --team-border-strong:rgba(113,137,237,.48);
  --team-grid:rgba(108,132,205,.16);
  --team-tooltip:rgba(7,18,36,.985);
}

.dark .tcrm-team-dashboard-premium::before{
  background:
    radial-gradient(circle at 10% 5%,rgba(82,68,255,.20),transparent 31rem),
    radial-gradient(circle at 89% 10%,rgba(42,122,255,.16),transparent 34rem),
    radial-gradient(circle at 52% 66%,rgba(118,61,220,.10),transparent 36rem),
    linear-gradient(180deg,#050c19 0%,#071223 46%,#071426 100%)!important;
}

.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-card,
.dark .tcrm-team-dashboard-premium .kpi-gradient-blue,
.dark .tcrm-team-dashboard-premium .kpi-gradient-green,
.dark .tcrm-team-dashboard-premium .kpi-gradient-yellow,
.dark .tcrm-team-dashboard-premium .kpi-gradient-red{
  background:
    radial-gradient(circle at 88% 88%,rgba(var(--team-accent),.10),transparent 42%),
    linear-gradient(145deg,rgba(17,34,61,.985),rgba(9,22,43,.97))!important;
  border-color:rgba(var(--team-accent),.34)!important;
  box-shadow:
    0 24px 58px -34px rgba(0,0,0,.95),
    0 0 28px -20px rgba(var(--team-accent),.72),
    inset 0 1px 0 rgba(255,255,255,.065)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-value,
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-label{
  color:#f5f8ff!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-subtitle,
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-period{
  color:#9baac5!important;
  opacity:1!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-spark{
  opacity:.98!important;
  filter:drop-shadow(0 0 10px rgba(var(--team-accent),.50))!important;
}

.dark .tcrm-team-dashboard-premium .chart-container,
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-card{
  background:
    radial-gradient(circle at 0 0,rgba(84,78,255,.09),transparent 22rem),
    radial-gradient(circle at 100% 100%,rgba(33,115,255,.07),transparent 24rem),
    linear-gradient(145deg,rgba(14,30,55,.985),rgba(8,21,41,.98))!important;
  border:1px solid rgba(103,132,226,.30)!important;
  color:#edf3ff!important;
  box-shadow:
    0 28px 68px -38px rgba(0,0,0,.96),
    0 0 28px -24px rgba(79,99,255,.74),
    inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark .tcrm-team-dashboard-premium .chart-container::before,
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card::before,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-card::before{
  background:
    radial-gradient(circle at 0 0,rgba(109,96,255,.11),transparent 19rem),
    radial-gradient(circle at 100% 100%,rgba(37,112,255,.08),transparent 20rem)!important;
}

.dark .tcrm-team-dashboard-premium .tcrm-team-chart-heading [class*="CardTitle"],
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-heading .font-semibold,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-header [class*="CardTitle"],
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-header .font-semibold,
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card h1,
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card h2,
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card h3{
  color:#f3f6ff!important;
  opacity:1!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-heading p,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-header p{
  color:#9eacc7!important;
  opacity:1!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-chip,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-chip{
  color:#eaf0ff!important;
  background:rgba(74,96,176,.18)!important;
  border-color:rgba(112,137,229,.30)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-key{
  color:#aebbd3!important;
}

/* Recharts readability in dark mode. */
.dark .tcrm-team-dashboard-premium .recharts-cartesian-axis-tick text,
.dark .tcrm-team-dashboard-premium .recharts-text,
.dark .tcrm-team-dashboard-premium .recharts-legend-item-text{
  fill:#9fadc6!important;
  color:#9fadc6!important;
  opacity:1!important;
}
.dark .tcrm-team-dashboard-premium .recharts-cartesian-grid line{
  stroke:rgba(116,137,202,.15)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-bar-value{
  fill:#f4f7ff!important;
  stroke:rgba(7,18,36,.94)!important;
  stroke-width:3px!important;
}
.dark .tcrm-team-dashboard-premium .recharts-bar-rectangle path{
  filter:drop-shadow(0 8px 12px rgba(78,91,255,.34))!important;
}
.dark .tcrm-team-dashboard-premium .recharts-pie-sector path{
  stroke:#0a1830!important;
  stroke-width:2px!important;
  filter:drop-shadow(0 10px 16px rgba(0,0,0,.42))!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-donut-total{
  fill:#f6f8ff!important;
  font-weight:900!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-donut-caption{
  fill:#9dacC7!important;
}

/* Side legends — prevent the white/washed-out V2 look. */
.dark .tcrm-team-dashboard-premium .tcrm-team-side-legend{
  background:rgba(7,19,38,.22)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-legend-row{
  color:#dfe7f8!important;
  border-bottom-color:rgba(119,139,198,.14)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-legend-name{
  color:#e8eefc!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-legend-pct,
.dark .tcrm-team-dashboard-premium .tcrm-team-legend-row strong{
  color:#9fadc6!important;
}

/* Empty analytics state. */
.dark .tcrm-team-dashboard-premium .tcrm-team-empty-chart{
  background:linear-gradient(180deg,rgba(10,25,48,.20),rgba(6,18,36,.05))!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-empty-grid{
  opacity:.42!important;
  background-image:
    linear-gradient(rgba(111,133,199,.11) 1px,transparent 1px),
    linear-gradient(90deg,rgba(111,133,199,.11) 1px,transparent 1px)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-empty-copy strong{
  color:#eef3ff!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-empty-copy p{
  color:#9eacc7!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-empty-icon{
  color:#94a5ff!important;
  background:rgba(80,92,255,.16)!important;
  border-color:rgba(113,130,255,.28)!important;
  box-shadow:0 0 25px -12px rgba(83,91,255,.76)!important;
}

/* Agent Performance dark executive table. */
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table{
  color:#eaf0fc!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table thead,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table thead tr{
  background:linear-gradient(90deg,rgba(31,53,91,.80),rgba(24,45,79,.68))!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table th{
  color:#aebbd2!important;
  border-color:rgba(116,138,204,.18)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table td{
  color:#e6edf9!important;
  border-color:rgba(112,134,198,.13)!important;
  background:transparent!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table tbody tr{
  background:rgba(7,19,38,.08)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table tbody tr:hover{
  background:rgba(77,94,170,.13)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-agent-cell strong{
  color:#f3f6ff!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-meter{
  background:rgba(113,134,191,.18)!important;
  box-shadow:inset 0 1px 2px rgba(0,0,0,.30)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-meter-cell>span{
  color:#b8c4d9!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-won-value{
  color:#36d98d!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-sla-badge{
  box-shadow:0 0 18px -8px rgba(239,68,68,.90)!important;
}

/* Stronger dark concept border/glow without changing layout. */
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card:hover,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-card:hover{
  border-color:rgba(114,138,246,.42)!important;
  box-shadow:0 30px 70px -40px rgba(0,0,0,.98),0 0 34px -24px rgba(81,98,255,.82),inset 0 1px 0 rgba(255,255,255,.06)!important;
}

@media (max-width:900px){
  .dark .tcrm-team-dashboard-premium .tcrm-team-chart-card,
  .dark .tcrm-team-dashboard-premium .tcrm-team-performance-card{background:linear-gradient(145deg,#0e1e37,#09162a)!important;}
}
'''

CSS.write_text(css.rstrip() + "\n", encoding="utf-8")
TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V2_BASE=YES")
print(f"TSX_CHANGED={'YES' if text != original else 'NO'}")
print("V21_CSS_WRITTEN=YES")
print("V21_CSS_IMPORTED=YES")
print("DARK_SURFACES_FIXED=YES")
print("DARK_TEXT_FIXED=YES")
print("BAR_VALUES_ENHANCED=YES")
