#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os
import shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
PAGES = [
    SRC / "pages/SalesFunnelDashboard.tsx",
    SRC / "pages/CalendarPage.tsx",
]
CSS = SRC / "sales-calendar-light-v6.css"

MARKER = "TCRM_SALES_CALENDAR_LIGHT_V6"
IMPORT_LINE = 'import "../sales-calendar-light-v6.css";'

for p in PAGES:
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"sales-calendar-light-v6-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

for p in PAGES:
    shutil.copy2(p, backup / p.name)

if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

def ensure_import(path: Path):
    text = path.read_text(encoding="utf-8")

    if MARKER not in text:
        text = f"// {MARKER}\n" + text

    if IMPORT_LINE not in text:
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "\n".join(lines) + "\n"

    path.write_text(text, encoding="utf-8")

for p in PAGES:
    ensure_import(p)

CSS_TEXT = r"""
/* TCRM Sales Funnel + Calendar — Light Mode Professional Polish V6
   Scope: UI only for light mode.
   Reference: premium light CRM dashboard style.
   No backend/data/logic changes.
*/

html:not(.dark) .tcrm-sales-leads-v3,
html:not(.dark) .tcrm-sales-leads-v3-calendar {
  --v6-purple:#6b5cff;
  --v6-purple-soft:#f3f0ff;
  --v6-blue:#4b8df8;
  --v6-green:#23c16b;
  --v6-amber:#f5a524;
  --v6-red:#ef5350;
  --v6-ink:#18243d;
  --v6-muted:#74819a;
  --v6-border:rgba(107,92,255,.13);
  --v6-border-strong:rgba(107,92,255,.22);
  --v6-surface:#fff;
  --v6-surface-2:#fbfbff;
  --v6-bg:linear-gradient(180deg,#f7f7fd 0%,#f4f5ff 46%,#f1f4ff 100%);
  --v6-shadow:0 12px 30px -20px rgba(62,70,120,.18),0 2px 8px rgba(82,89,145,.06);
  background:var(--v6-bg)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero{
  position:relative!important;
  overflow:hidden!important;
  min-height:94px!important;
  padding:18px 20px!important;
  border-radius:20px!important;
  border:1px solid var(--v6-border-strong)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(107,92,255,.10) 1px,transparent 1.2px) 0 0/16px 16px,
    linear-gradient(135deg,#fff 0%,#f9f8ff 52%,#f3f1ff 100%)!important;
  box-shadow:var(--v6-shadow)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell h1,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero h1{
  color:var(--v6-ink)!important;
  font-size:19px!important;
  font-weight:850!important;
  letter-spacing:-.02em!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell p,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero p{
  color:var(--v6-muted)!important;
  font-size:12px!important;
  font-weight:600!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell button,
html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell select,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero button{
  min-height:40px!important;
  border-radius:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero button{
  background:linear-gradient(135deg,#725cff,#5f49ea)!important;
  color:#fff!important;
  border:0!important;
  box-shadow:0 14px 26px -16px rgba(107,92,255,.52)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
  gap:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div{
  position:relative!important;
  overflow:hidden!important;
  min-height:96px!important;
  border-radius:18px!important;
  border:1px solid var(--v6-border)!important;
  background:linear-gradient(180deg,var(--v6-surface),var(--v6-surface-2))!important;
  box-shadow:var(--v6-shadow)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card::before,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:3px;
  background:var(--v6-purple);
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-2::before,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div:nth-child(3)::before{
  background:var(--v6-green);
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-3::before,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div:nth-child(2)::before{
  background:var(--v6-blue);
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-4::before,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis > div:nth-child(4)::before{
  background:var(--v6-amber);
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis strong{
  color:var(--v6-ink)!important;
  font-size:22px!important;
  font-weight:850!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v3-kpi-card .kpi-icon,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpi-icon{
  width:31px!important;
  height:31px!important;
  border-radius:10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .bg-card,
html:not(.dark) .tcrm-sales-leads-v3-funnel .chart-container,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-radius:18px!important;
  border:1px solid var(--v6-border)!important;
  background:linear-gradient(180deg,#fff 0%,#fbfbff 100%)!important;
  box-shadow:var(--v6-shadow)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 [class*="CardHeader"],
html:not(.dark) .tcrm-sales-leads-v3 .chart-container > div:first-child,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:50px!important;
  padding:12px 16px!important;
  border-bottom:1px solid rgba(107,92,255,.08)!important;
  background:linear-gradient(180deg,#fff 0%,#fafbff 100%)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 [class*="CardContent"]{
  padding:14px 16px!important;
}

html:not(.dark) .tcrm-sales-leads-v3 h2,
html:not(.dark) .tcrm-sales-leads-v3 h3,
html:not(.dark) .tcrm-sales-leads-v3 [class*="CardTitle"],
html:not(.dark) .tcrm-sales-leads-v3-calendar h2,
html:not(.dark) .tcrm-sales-leads-v3-calendar h3{
  color:var(--v6-ink)!important;
  font-weight:820!important;
  letter-spacing:-.01em!important;
}

html:not(.dark) .tcrm-sales-leads-v3 .text-muted-foreground,
html:not(.dark) .tcrm-sales-leads-v3-calendar .text-muted-foreground{
  color:var(--v6-muted)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{
  grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr)!important;
  gap:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .chart-container{
  min-height:330px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
  grid-template-columns:minmax(330px,.8fr) minmax(0,1.2fr)!important;
  grid-template-areas:"monthly campaign" "summary campaign"!important;
  gap:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid,
html:not(.dark) .tcrm-sales-leads-v3-funnel [class*="conversion"]{
  border-radius:18px!important;
  overflow:hidden!important;
  border:1px solid var(--v6-border)!important;
  background:linear-gradient(180deg,#fff,#fbfbff)!important;
  box-shadow:var(--v6-shadow)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid > div,
html:not(.dark) .tcrm-sales-leads-v3-funnel [class*="conversion"] > div{
  background:transparent!important;
  border-color:rgba(107,92,255,.10)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table{
  border-collapse:separate!important;
  border-spacing:0 2px!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table thead tr{
  background:linear-gradient(180deg,#f4f5ff,#eef1ff)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table tbody tr{
  background:rgba(255,255,255,.78)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table tbody tr:nth-child(even){
  background:rgba(247,248,255,.9)!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table th{
  color:#64708b!important;
  font-size:10.5px!important;
  font-weight:850!important;
  padding:9px 10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3 table td{
  color:#4f5b73!important;
  font-size:11.3px!important;
  padding:9px 10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,3.3fr) minmax(285px,.7fr)!important;
  gap:12px!important;
  align-items:start!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
  min-width:0!important;
  overflow:hidden!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  min-width:0!important;
  position:sticky!important;
  top:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  background:rgba(243,245,255,.9)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:108px!important;
  padding:8px!important;
  border-color:rgba(107,92,255,.08)!important;
  transition:background .16s ease,box-shadow .16s ease!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:linear-gradient(180deg,#f9f9ff,#f5f6ff)!important;
  box-shadow:inset 0 0 0 1px rgba(107,92,255,.10)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-violet-100"],
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-blue-100"],
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-emerald-100"],
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-amber-100"],
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-rose-100"]{
  border-radius:8px!important;
  padding:3px 6px!important;
  font-weight:700!important;
  box-shadow:0 6px 12px -10px rgba(72,64,180,.35)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child{
  max-height:590px!important;
  padding:10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div{
  border-radius:12px!important;
  border:1px solid transparent!important;
  padding:10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div:hover{
  background:rgba(245,246,255,.95)!important;
  border-color:var(--v6-border)!important;
}

@media (max-width:1365px){
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
    grid-template-columns:1fr!important;
    grid-template-areas:"monthly" "campaign" "summary"!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
    position:static!important;
  }
}

@media (max-width:1024px){
  html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
}

@media (max-width:700px){
  html:not(.dark) .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
    overflow-x:auto!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > .grid{
    min-width:720px!important;
  }
}
"""
CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("MODE=LIGHT_ONLY")
print("SCREENS=SalesFunnel,Calendar")
print("BACKEND_UNCHANGED=YES")
print("FILES_CHANGED=3")
