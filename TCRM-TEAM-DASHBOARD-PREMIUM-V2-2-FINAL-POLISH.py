#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/TeamDashboard.tsx"
CSS = ROOT / "client/src/team-dashboard-premium-v2-2.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/TeamDashboard.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../team-dashboard-premium-v2.css";',
    'import "../team-dashboard-premium-v2-1.css";',
    'tcrm-team-dashboard-premium',
    'tcrm-team-chart-card',
    'tcrm-team-kpi-card',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=V21_BASE_REQUIRED_MISSING:" + ",".join(missing))

final_import = 'import "../team-dashboard-premium-v2-2.css";'
if final_import not in text:
    anchor = 'import "../team-dashboard-premium-v2-1.css";'
    text = text.replace(anchor, anchor + "\n" + final_import, 1)

css = r'''/* TCRM Team Dashboard Premium V2.2 — final polish only */

/* ===== Tooltip readability: especially Dark Mode Pie/Donut hover ===== */
.tcrm-team-dashboard-premium{
  --team-tooltip-bg:rgba(255,255,255,.985);
  --team-tooltip-text:#172036;
  --team-tooltip-muted:#667085;
  --team-tooltip-border:rgba(99,102,241,.22);
}
.dark .tcrm-team-dashboard-premium{
  --team-tooltip-bg:rgba(13,27,51,.985);
  --team-tooltip-text:#f4f7ff;
  --team-tooltip-muted:#b7c3da;
  --team-tooltip-border:rgba(119,133,255,.44);
  --team-tooltip:rgba(13,27,51,.985);
}

.tcrm-team-dashboard-premium .recharts-tooltip-wrapper{z-index:50!important;outline:none!important;}
.tcrm-team-dashboard-premium .recharts-default-tooltip{
  background:var(--team-tooltip-bg)!important;
  border:1px solid var(--team-tooltip-border)!important;
  border-radius:12px!important;
  padding:10px 12px!important;
  box-shadow:0 16px 38px -18px rgba(30,41,90,.42)!important;
  backdrop-filter:blur(16px)!important;
  -webkit-backdrop-filter:blur(16px)!important;
  color:var(--team-tooltip-text)!important;
}
.dark .tcrm-team-dashboard-premium .recharts-default-tooltip{
  box-shadow:0 20px 48px -20px rgba(0,0,0,.88),0 0 0 1px rgba(121,134,255,.08) inset!important;
}
.tcrm-team-dashboard-premium .recharts-tooltip-label{
  color:var(--team-tooltip-text)!important;
  font-weight:800!important;
  font-size:11px!important;
  line-height:1.35!important;
  margin:0 0 5px!important;
}
.tcrm-team-dashboard-premium .recharts-tooltip-item-list{margin:0!important;padding:0!important;}
.tcrm-team-dashboard-premium .recharts-tooltip-item,
.tcrm-team-dashboard-premium .recharts-tooltip-item-name,
.tcrm-team-dashboard-premium .recharts-tooltip-item-value,
.tcrm-team-dashboard-premium .recharts-tooltip-item-separator{
  color:var(--team-tooltip-text)!important;
  font-size:11px!important;
  font-weight:700!important;
}
.tcrm-team-dashboard-premium .recharts-tooltip-item-value{font-weight:850!important;}
.tcrm-team-dashboard-premium .recharts-tooltip-cursor{fill:rgba(99,102,241,.055)!important;stroke:rgba(99,102,241,.10)!important;}
.dark .tcrm-team-dashboard-premium .recharts-tooltip-cursor{fill:rgba(104,119,255,.07)!important;stroke:rgba(116,132,255,.14)!important;}

/* Force SVG chart text to remain readable in both themes */
.dark .tcrm-team-dashboard-premium .recharts-text,
.dark .tcrm-team-dashboard-premium .recharts-cartesian-axis-tick-value,
.dark .tcrm-team-dashboard-premium .recharts-label-list text{fill:#dce6fa!important;}
.dark .tcrm-team-dashboard-premium .tcrm-team-donut-total{fill:#f5f8ff!important;}
.dark .tcrm-team-dashboard-premium .tcrm-team-donut-caption{fill:#aebbd3!important;}

/* ===== KPI final proportions ===== */
.tcrm-team-dashboard-premium .tcrm-team-kpi-card{min-height:118px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-content{padding:15px 17px 13px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-icon{width:41px!important;height:41px!important;border-radius:13px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-value{font-size:31px!important;margin-top:8px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-footer{padding-top:6px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-spark{height:31px!important;width:72px!important;}

/* ===== Analytics density ===== */
.tcrm-team-dashboard-premium .tcrm-team-chart-card{min-height:312px!important;}
.tcrm-team-dashboard-premium .tcrm-team-chart-header,
.tcrm-team-dashboard-premium .tcrm-team-performance-header{padding:14px 17px 6px!important;}
.tcrm-team-dashboard-premium .tcrm-team-chart-content{padding:2px 15px 12px!important;}
.tcrm-team-dashboard-premium .tcrm-team-donut-layout{min-height:244px!important;}
.tcrm-team-dashboard-premium .tcrm-team-empty-chart{min-height:244px!important;}

/* ===== Light mode: pearl depth, not flat white ===== */
.tcrm-team-dashboard-premium .tcrm-team-kpi-card{
  box-shadow:0 22px 54px -36px rgba(68,73,170,.34),inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.tcrm-team-dashboard-premium .tcrm-team-chart-card,
.tcrm-team-dashboard-premium .tcrm-team-performance-card{
  border-color:rgba(102,109,214,.18)!important;
  box-shadow:0 24px 60px -42px rgba(72,78,170,.36),inset 0 1px 0 rgba(255,255,255,.92)!important;
}

/* Restore stronger dark-specific depth after light polish */
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-card{
  box-shadow:0 26px 58px -36px rgba(0,0,0,.94),0 0 28px -24px rgba(var(--team-accent),.75),inset 0 1px 0 rgba(255,255,255,.06)!important;
}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-card{
  border-color:rgba(103,123,210,.30)!important;
  box-shadow:0 28px 64px -42px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.05)!important;
}

/* Small premium interactions only */
.tcrm-team-dashboard-premium .tcrm-team-chart-card,
.tcrm-team-dashboard-premium .tcrm-team-performance-card,
.tcrm-team-dashboard-premium .tcrm-team-kpi-card{transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease;}
.tcrm-team-dashboard-premium .tcrm-team-chart-card:hover,
.tcrm-team-dashboard-premium .tcrm-team-performance-card:hover{transform:translateY(-1px);border-color:rgba(103,113,232,.30)!important;}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-card:hover,
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-card:hover{border-color:rgba(118,135,255,.42)!important;}

@media (max-width:900px){
  .tcrm-team-dashboard-premium .tcrm-team-kpi-card{min-height:112px!important;}
  .tcrm-team-dashboard-premium .tcrm-team-kpi-value{font-size:27px!important;}
}
'''

CSS.write_text(css.rstrip() + "\n", encoding="utf-8")
TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V21_BASE=YES")
print(f"TSX_CHANGED={'YES' if text != original else 'NO'}")
print("V22_CSS_WRITTEN=YES")
print("V22_CSS_IMPORTED=YES")
print("TOOLTIP_DARK_FIXED=YES")
print("FINAL_POLISH=YES")
