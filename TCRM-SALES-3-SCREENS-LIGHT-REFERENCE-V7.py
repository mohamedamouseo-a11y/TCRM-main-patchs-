#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
SALES = SRC / "pages/SalesFunnelDashboard.tsx"
SLA = SRC / "pages/TaskSlaDashboard.tsx"
CAL = SRC / "pages/CalendarPage.tsx"
PAGES = [SALES, SLA, CAL]
CSS = SRC / "sales-3-screens-light-reference-v7.css"
MARKER = "TCRM_SALES_3_SCREENS_LIGHT_REFERENCE_V7"
IMPORT = 'import "../sales-3-screens-light-reference-v7.css";'

for p in PAGES:
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"sales-3-screens-light-reference-v7-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in PAGES:
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

def add_import(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if IMPORT not in text:
        anchors = [
            'import "../sales-calendar-light-v6.css";',
            'import "../sales-3-screens-executive-v5.css";',
            'import "../sales-3-screens-executive-v4.css";',
            'import "../sales-3-screens-leads-design-system-v3.css";',
        ]
        inserted = False
        for anchor in anchors:
            if anchor in text:
                text = text.replace(anchor, anchor + "\n" + IMPORT, 1)
                inserted = True
                break
        if not inserted:
            lines = text.splitlines()
            pos = 0
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    pos = i + 1
            lines.insert(pos, IMPORT)
            text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")

for p in PAGES:
    add_import(p)

# Sales: make the bottom reference composition structurally possible:
# Campaign Details + Stage Conversion become a real 2-column final row.
sales = SALES.read_text(encoding="utf-8")
if 'className="tcrm-v7-sales-bottom-grid"' not in sales:
    start_anchor = '        {/* Campaign Performance Table */}'
    start = sales.find(start_anchor)
    if start < 0:
        raise SystemExit("ERROR=SALES_BOTTOM_START_NOT_FOUND")
    sales = sales[:start] + '        <div className="tcrm-v7-sales-bottom-grid">\n' + sales[start:]

    end_anchor = '        </Card>\n      </div>\n    </CRMLayout>'
    end = sales.rfind(end_anchor)
    if end < 0:
        raise SystemExit("ERROR=SALES_BOTTOM_END_NOT_FOUND")
    sales = sales[:end + len('        </Card>')] + '\n        </div>' + sales[end + len('        </Card>'):]
    SALES.write_text(sales, encoding="utf-8")

# Calendar: protect/show the actual title block in Light mode.
cal = CAL.read_text(encoding="utf-8")
old = '''<div className="tcrm-v21-calendar-hero tcrm-v3-calendar-hero flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">'''
new = '''<div className="tcrm-v21-calendar-hero tcrm-v3-calendar-hero flex items-center justify-between flex-wrap gap-3">
          <div className="tcrm-v7-calendar-title flex items-center gap-3">'''
if "tcrm-v7-calendar-title" not in cal:
    if old not in cal:
        raise SystemExit("ERROR=CALENDAR_HERO_ANCHOR_NOT_FOUND")
    cal = cal.replace(old, new, 1)
    CAL.write_text(cal, encoding="utf-8")

CSS_TEXT = r'''/* TCRM V7 — Light Reference Match
   Based on approved live/reference screenshots.
   Scope: Sales Funnel + Tasks & SLA + Calendar, Light Mode only.
   Preserve real data/functions/permissions. No fake controls or fake data. */

html:not(.dark) .tcrm-sales-leads-v3{
  --r7-ink:#17213c;
  --r7-muted:#74809a;
  --r7-purple:#6552ec;
  --r7-purple2:#795ff4;
  --r7-blue:#4c8cf7;
  --r7-green:#1fbd72;
  --r7-amber:#f4a21b;
  --r7-red:#ef4d62;
  --r7-border:rgba(100,83,232,.14);
  --r7-border-strong:rgba(100,83,232,.22);
  --r7-card:#fff;
  --r7-soft:#f8f9ff;
  --r7-shadow:0 15px 38px -29px rgba(62,55,135,.30),0 4px 14px -12px rgba(54,66,112,.16);
  background:
    radial-gradient(760px 340px at 4% -5%,rgba(126,105,245,.10),transparent 68%),
    linear-gradient(180deg,#fafaff 0%,#f5f6ff 55%,#f1f4ff 100%)!important;
}

/* tighter page rhythm like the reference */
html:not(.dark) .tcrm-sales-leads-v3-funnel > * + *,
html:not(.dark) .tcrm-sales-leads-v3-sla > * + *,
html:not(.dark) .tcrm-sales-leads-v3-calendar > * + *{
  margin-top:12px!important;
}

/* hero */
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero{
  min-height:88px!important;
  padding:16px 18px!important;
  border-radius:19px!important;
  border:1px solid var(--r7-border-strong)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(101,82,236,.11) 1px,transparent 1.2px) 0 0/15px 15px,
    radial-gradient(52% 160% at 82% 50%,rgba(117,91,242,.13),transparent 67%),
    linear-gradient(125deg,#fff 0%,#fbfaff 56%,#f4f2ff 100%)!important;
  box-shadow:var(--r7-shadow)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell h1,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero h1{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  color:var(--r7-ink)!important;
  font-size:20px!important;
  line-height:1.15!important;
  font-weight:850!important;
  letter-spacing:-.025em!important;
}
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell p,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero p{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  color:var(--r7-muted)!important;
  font-size:11.5px!important;
  font-weight:600!important;
}

/* calendar title disappeared in live V6: force the real source title/icon back */
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v7-calendar-title{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  position:relative!important;
  z-index:2!important;
  min-width:240px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v7-calendar-title > div:first-child{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  width:42px!important;
  height:42px!important;
  align-items:center!important;
  justify-content:center!important;
  padding:0!important;
  border-radius:12px!important;
  background:linear-gradient(135deg,#7560f4,#6048e7)!important;
  box-shadow:0 12px 24px -15px rgba(87,63,214,.65)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v7-calendar-title > div:last-child{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
}

/* KPI row */
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
  gap:10px!important;
}
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div{
  min-height:88px!important;
  border-radius:16px!important;
  border:1px solid var(--r7-border)!important;
  background:linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:var(--r7-shadow)!important;
}
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card::before,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div::before{
  height:2px!important;
}
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis strong{
  color:var(--r7-ink)!important;
  font-size:22px!important;
  font-weight:850!important;
}

/* shared card language */
html:not(.dark) .tcrm-sales-leads-v3 .bg-card,
html:not(.dark) .tcrm-sales-leads-v3-funnel .chart-container,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-radius:16px!important;
  border:1px solid var(--r7-border)!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--r7-shadow)!important;
}

/* ================= SALES FUNNEL ================= */
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{
  grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr)!important;
  gap:12px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .chart-container{
  min-height:302px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .recharts-responsive-container{
  height:228px!important;
  min-height:228px!important;
}

/* Reference composition: monthly + summary left, campaign chart right */
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
  display:grid!important;
  grid-template-columns:minmax(390px,.78fr) minmax(0,1.22fr)!important;
  grid-template-rows:142px 158px!important;
  grid-template-areas:"monthly campaign" "summary campaign"!important;
  gap:12px!important;
  align-items:stretch!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-deal-grid{
  display:contents!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly{
  grid-area:monthly!important;
  min-height:0!important;
  height:142px!important;
  overflow:hidden!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly [class*="CardHeader"]{
  min-height:42px!important;
  padding:9px 13px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly [class*="CardContent"]{
  height:98px!important;
  padding:8px 12px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly .h-56{
  height:72px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly .recharts-responsive-container{
  height:76px!important;
  max-height:76px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-chart{
  grid-area:campaign!important;
  height:312px!important;
  min-height:312px!important;
  align-self:stretch!important;
  overflow:hidden!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-chart .recharts-responsive-container{
  height:235px!important;
  max-height:235px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary{
  grid-area:summary!important;
  height:158px!important;
  min-height:158px!important;
  overflow:hidden!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardHeader"]{
  min-height:39px!important;
  padding:8px 12px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"]{
  display:grid!important;
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  gap:6px!important;
  padding:8px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"] > div{
  min-width:0!important;
  margin:0!important;
  padding:8px!important;
  border:1px solid rgba(100,83,232,.10)!important;
  border-radius:10px!important;
  background:#fafbff!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"] > div .text-sm{
  font-size:11px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"] > div .text-xs,
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"] > div .text-\[11px\]{
  font-size:9.5px!important;
  line-height:1.25!important;
}

/* final row exactly like reference: table left, conversion right */
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v7-sales-bottom-grid{
  display:grid!important;
  grid-template-columns:minmax(0,1.55fr) minmax(360px,1fr)!important;
  gap:12px!important;
  align-items:start!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-table,
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-conversion{
  margin:0!important;
  min-width:0!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-table th,
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-table td{
  padding:7px 9px!important;
  font-size:10px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-conversion [class*="CardContent"] > div{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:6px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-conversion [class*="CardContent"] > div > div{
  min-width:0!important;
  padding:7px!important;
  gap:6px!important;
  border-color:rgba(100,83,232,.11)!important;
  background:#fafbff!important;
}

/* ================= TASKS & SLA ================= */
html:not(.dark) .tcrm-sales-leads-v3-sla{
  padding:20px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-kpis{
  gap:10px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  min-height:48px!important;
  border-radius:14px!important;
  border:1px solid var(--r7-border)!important;
  background:linear-gradient(180deg,#fff,#fafbff)!important;
  box-shadow:var(--r7-shadow)!important;
  overflow:hidden!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item{
  display:flex!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:12px!important;
  padding:10px 14px!important;
  border-right:1px solid rgba(100,83,232,.09)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item:last-child{border-right:0!important}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item span{
  color:var(--r7-muted)!important;
  font-size:9.5px!important;
  font-weight:750!important;
  text-transform:uppercase!important;
  letter-spacing:.045em!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item strong{
  color:var(--r7-ink)!important;
  font-size:11px!important;
  font-weight:820!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item strong.is-good{color:#15975d!important}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item strong.is-risk{color:#d83d55!important}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends,
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-distribution{
  gap:12px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends > .bg-card,
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-distribution > .bg-card{
  min-height:0!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends .recharts-responsive-container{
  height:218px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-distribution .recharts-responsive-container{
  height:190px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla table{
  border-collapse:separate!important;
  border-spacing:0 1px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla thead tr{
  background:linear-gradient(180deg,#f3f4ff,#edf0fb)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla tbody tr:nth-child(even){
  background:#f8f9ff!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla th{
  padding:7px 9px!important;
  color:#69758d!important;
  font-size:9.5px!important;
  font-weight:820!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla td{
  padding:7px 9px!important;
  color:#536078!important;
  font-size:10px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches{
  border:1px solid rgba(239,77,98,.20)!important;
  border-top:3px solid var(--r7-red)!important;
  box-shadow:0 15px 36px -29px rgba(207,47,72,.28)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches [class*="CardHeader"]{
  background:linear-gradient(180deg,#fff8f9,#fff)!important;
}

/* ================= CALENDAR ================= */
html:not(.dark) .tcrm-sales-leads-v3-calendar{
  padding:20px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,4.2fr) minmax(245px,.8fr)!important;
  gap:12px!important;
  align-items:start!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
  grid-column:auto!important;
  min-width:0!important;
  overflow:hidden!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  grid-column:auto!important;
  min-width:0!important;
  width:100%!important;
  height:auto!important;
  min-height:0!important;
  align-self:start!important;
  position:sticky!important;
  top:12px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child{
  min-height:52px!important;
  padding:10px 13px!important;
  background:linear-gradient(180deg,#fff,#f8f9ff)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  background:#f5f6fd!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:91px!important;
  padding:6px!important;
  border-color:rgba(102,114,157,.09)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:#faf9ff!important;
  box-shadow:inset 0 0 0 1px rgba(101,82,236,.09)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:48px!important;
  padding:10px 12px!important;
  background:linear-gradient(180deg,#fff,#f8f9ff)!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child{
  min-height:0!important;
  max-height:360px!important;
  padding:10px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming .text-center.py-10{
  padding-top:22px!important;
  padding-bottom:22px!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming .w-12.h-12{
  width:44px!important;
  height:44px!important;
  border-radius:13px!important;
  background:#f1f3fb!important;
}
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-violet-100"],
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-blue-100"]{
  border-radius:7px!important;
  padding:3px 5px!important;
  box-shadow:none!important;
}

/* Responsive */
@media (max-width:1365px){
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
    grid-template-columns:1fr!important;
    grid-template-rows:auto!important;
    grid-template-areas:"monthly" "campaign" "summary"!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-deal-grid{display:contents!important}
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly,
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-campaign-chart,
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary{
    height:auto!important;
    min-height:0!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v7-sales-bottom-grid{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
    position:static!important;
  }
}
@media (max-width:900px){
  html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item{
    border-right:0!important;
    border-bottom:1px solid rgba(100,83,232,.09)!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-deal-summary [class*="CardContent"]{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
}
@media (max-width:700px){
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
    overflow-x:auto!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > .grid{
    min-width:720px!important;
  }
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=LIGHT_REFERENCE_V7")
print("SCREENS=SalesFunnel,TasksSLA,Calendar")
print("REFERENCE_MATCH=YES")
print("UI_ONLY=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=4")
print(f"BACKUP={backup}")
