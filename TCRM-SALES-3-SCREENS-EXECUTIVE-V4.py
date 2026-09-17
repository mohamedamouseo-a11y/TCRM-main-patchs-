#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
PAGES = SRC / "pages"
FILES = [
    PAGES / "SalesFunnelDashboard.tsx",
    PAGES / "TaskSlaDashboard.tsx",
    PAGES / "CalendarPage.tsx",
]
CSS = SRC / "sales-3-screens-executive-v4.css"
MARKER = "TCRM_SALES_3_SCREENS_EXECUTIVE_V4"
IMPORT = 'import "../sales-3-screens-executive-v4.css";'
V3_IMPORT = 'import "../sales-3-screens-leads-design-system-v3.css";'

for p in FILES:
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"sales-3-screens-executive-v4-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in FILES:
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

for p in FILES:
    text = p.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if IMPORT not in text:
        if V3_IMPORT not in text:
            raise SystemExit(f"V3_IMPORT_MISSING={p}")
        text = text.replace(V3_IMPORT, V3_IMPORT + "\n" + IMPORT, 1)
    p.write_text(text, encoding="utf-8")

CSS_TEXT = r'''/* TCRM Sales 3 Screens — Executive V4
   Source of truth: current Sales Funnel / Tasks & SLA / Calendar runtime structure.
   Visual master: Leads Premium light/dark palette.
   Scope: presentation/layout only. No backend, data, permissions, routes or business logic changes. */

.tcrm-sales-leads-v3{
  --v4-purple:#6853e8;
  --v4-violet:#7a62f4;
  --v4-blue:#4e88f7;
  --v4-green:#22b981;
  --v4-amber:#efa61e;
  --v4-red:#e94f68;
  --v4-ink:#20233e;
  --v4-muted:#727b94;
  --v4-border:rgba(103,91,225,.17);
  --v4-border-strong:rgba(103,91,225,.27);
  --v4-surface:rgba(255,255,255,.985);
  --v4-surface-soft:rgba(247,247,255,.96);
  --v4-shadow:0 22px 56px -38px rgba(71,57,165,.34),0 8px 24px -19px rgba(61,69,126,.19),inset 0 1px 0 rgba(255,255,255,.98);
  background:
    radial-gradient(760px 420px at 1% -3%,rgba(120,92,247,.14),transparent 68%),
    radial-gradient(840px 430px at 98% 0%,rgba(89,132,246,.10),transparent 70%),
    linear-gradient(180deg,#fbfaff 0%,#f3f2ff 52%,#eef2ff 100%)!important;
  gap:14px!important;
}
.dark .tcrm-sales-leads-v3{
  --v4-ink:#f4f6ff;
  --v4-muted:#a7b1c7;
  --v4-border:rgba(100,120,203,.24);
  --v4-border-strong:rgba(111,126,221,.36);
  --v4-surface:rgba(7,20,39,.985);
  --v4-surface-soft:rgba(10,28,52,.965);
  --v4-shadow:0 26px 60px -42px rgba(0,0,0,.92),0 0 40px -31px rgba(106,82,255,.42),inset 0 1px 0 rgba(255,255,255,.045);
  background:
    radial-gradient(850px 460px at 0% -4%,rgba(72,69,246,.20),transparent 68%),
    radial-gradient(900px 470px at 100% 0%,rgba(113,62,244,.14),transparent 72%),
    linear-gradient(180deg,#050b16 0%,#071426 48%,#06111f 100%)!important;
}

/* Shared executive rhythm */
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  min-height:82px!important;
  padding:16px 18px!important;
  border-radius:18px!important;
  border:1px solid var(--v4-border-strong)!important;
  background:
    radial-gradient(60% 180% at 84% 50%,rgba(121,93,247,.15),transparent 64%),
    linear-gradient(120deg,rgba(255,255,255,.99),rgba(246,243,255,.97))!important;
  box-shadow:var(--v4-shadow)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.dark .tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  background:
    radial-gradient(64% 190% at 84% 48%,rgba(105,77,255,.19),transparent 66%),
    linear-gradient(135deg,rgba(10,27,53,.99),rgba(14,25,61,.985))!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell h1,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero h1{
  font-size:20px!important;line-height:1.1!important;font-weight:850!important;letter-spacing:-.025em!important;color:var(--v4-ink)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell p,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero p{font-size:12px!important;color:var(--v4-muted)!important;font-weight:600!important}

.tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis{gap:10px!important}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div{
  min-height:88px!important;
  border-radius:15px!important;
  border:1px solid var(--v4-border)!important;
  background:linear-gradient(150deg,var(--v4-surface),var(--v4-surface-soft))!important;
  box-shadow:var(--v4-shadow)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis strong{font-size:23px!important;line-height:1!important;color:var(--v4-ink)!important;font-weight:880!important}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card .kpi-icon,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpi-icon{width:30px!important;height:30px!important;border-radius:9px!important;box-shadow:0 8px 18px -12px currentColor!important}

.tcrm-sales-leads-v3 .bg-card,
.tcrm-sales-leads-v3-funnel .chart-container,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-radius:16px!important;
  border:1px solid var(--v4-border)!important;
  background:linear-gradient(180deg,var(--v4-surface),var(--v4-surface-soft))!important;
  box-shadow:var(--v4-shadow)!important;
}
.dark .tcrm-sales-leads-v3 .bg-card,
.dark .tcrm-sales-leads-v3-funnel .chart-container,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{background:linear-gradient(180deg,var(--v4-surface),var(--v4-surface-soft))!important}

.tcrm-sales-leads-v3 [class*="CardHeader"],
.tcrm-sales-leads-v3 .chart-container > div:first-child{padding:13px 15px!important;border-bottom:1px solid rgba(103,91,225,.09)!important}
.tcrm-sales-leads-v3 [class*="CardContent"]{padding:14px 15px!important}
.tcrm-sales-leads-v3 h2,.tcrm-sales-leads-v3 h3,.tcrm-sales-leads-v3 [class*="CardTitle"]{color:var(--v4-ink)!important;font-weight:820!important;letter-spacing:-.015em!important}
.tcrm-sales-leads-v3 .text-muted-foreground{color:var(--v4-muted)!important}

/* SALES FUNNEL — compact executive pipeline */
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{
  grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr)!important;
  gap:12px!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .chart-container{min-height:320px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .recharts-responsive-container{height:240px!important;min-height:240px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
  grid-template-columns:minmax(330px,.76fr) minmax(0,1.24fr)!important;
  grid-template-areas:"monthly campaign" "summary campaign"!important;
  gap:12px!important;
  align-items:start!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .chart-container{align-self:start!important;min-height:0!important;height:auto!important}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .chart-container .recharts-responsive-container{height:250px!important;max-height:250px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly{min-height:180px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly .recharts-responsive-container{height:150px!important;max-height:150px!important}
.tcrm-sales-leads-v3-funnel table{border-collapse:separate!important;border-spacing:0 2px!important}
.tcrm-sales-leads-v3-funnel th{font-size:10.5px!important;font-weight:850!important;padding:9px 10px!important}
.tcrm-sales-leads-v3-funnel td{font-size:11.5px!important;padding:9px 10px!important}
.tcrm-sales-leads-v3-funnel thead tr{background:linear-gradient(180deg,rgba(239,240,255,.99),rgba(229,235,252,.98))!important}
.dark .tcrm-sales-leads-v3-funnel thead tr{background:linear-gradient(180deg,rgba(16,38,70,.99),rgba(11,29,56,.99))!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid,
.tcrm-sales-leads-v3-funnel [class*="conversion"]{border-radius:16px!important;overflow:hidden!important;background:linear-gradient(180deg,var(--v4-surface),var(--v4-surface-soft))!important;border:1px solid var(--v4-border)!important;box-shadow:var(--v4-shadow)!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid > div,
.tcrm-sales-leads-v3-funnel [class*="conversion"] > div{background:transparent!important;border-color:var(--v4-border)!important}
.dark .tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid,
.dark .tcrm-sales-leads-v3-funnel [class*="conversion"]{background:linear-gradient(180deg,#091b35,#07172d)!important}

/* TASKS & SLA — risk first, denser operational hierarchy */
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
  border-radius:14px!important;
  border:1px solid var(--v4-border)!important;
  background:linear-gradient(145deg,var(--v4-surface),var(--v4-surface-soft))!important;
  box-shadow:var(--v4-shadow)!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item{padding:11px 15px!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item span{font-size:10.5px!important;color:var(--v4-muted)!important;text-transform:uppercase;letter-spacing:.04em}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item strong{font-size:12px!important;color:var(--v4-ink)!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends{grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr)!important;gap:12px!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends > .bg-card{min-height:315px!important}
.tcrm-sales-leads-v3-sla .tcrm-v3-sla-distributions{gap:12px!important}
.tcrm-sales-leads-v3-sla table{border-collapse:separate!important;border-spacing:0 2px!important}
.tcrm-sales-leads-v3-sla th{font-size:10.5px!important;font-weight:850!important;padding:9px 10px!important}
.tcrm-sales-leads-v3-sla td{font-size:11.4px!important;padding:9px 10px!important}
.tcrm-sales-leads-v3-sla thead tr{background:linear-gradient(180deg,rgba(239,240,255,.99),rgba(229,235,252,.98))!important}
.dark .tcrm-sales-leads-v3-sla thead tr{background:linear-gradient(180deg,rgba(16,38,70,.99),rgba(11,29,56,.99))!important}
.dark .tcrm-sales-leads-v3-sla [class*="border-red"],
.dark .tcrm-sales-leads-v3-sla [class*="bg-red"]{border-color:rgba(239,80,105,.26)!important}
.dark .tcrm-sales-leads-v3-sla [class*="border-red"] > div:first-child{background:linear-gradient(180deg,rgba(53,24,39,.92),rgba(28,22,40,.92))!important;color:#ffd9df!important}

/* CALENDAR — true command-center layout, no giant empty lower panel */
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,3.25fr) minmax(270px,.75fr)!important;
  gap:12px!important;
  align-items:start!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{grid-column:auto!important;min-width:0!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{grid-column:auto!important;min-width:0!important;position:sticky;top:14px}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{min-height:52px!important;padding:12px 14px!important;background:linear-gradient(180deg,rgba(249,249,255,.99),rgba(241,244,255,.95))!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{background:linear-gradient(180deg,rgba(14,34,65,.99),rgba(9,26,51,.96))!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{background:rgba(239,241,253,.85)!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{background:rgba(11,29,56,.95)!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{min-height:104px!important;padding:7px!important;border-color:rgba(103,108,169,.10)!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{border-color:rgba(100,119,199,.13)!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-emerald-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-amber-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-rose-100"]{border-radius:6px!important;padding:3px 5px!important;font-weight:700!important;box-shadow:0 8px 16px -12px rgba(83,61,194,.58)!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child{max-height:595px!important;padding:10px!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div{border-radius:11px!important;border:1px solid transparent!important;padding:10px!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div:hover{background:rgba(241,240,255,.76)!important;border-color:var(--v4-border)!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div:hover{background:rgba(16,34,64,.85)!important}

/* Responsive: preserve the desktop composition longer, then wrap cleanly */
@media (max-width:1365px){
  .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview,
  .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{grid-template-columns:1fr!important;grid-template-areas:"monthly" "campaign" "summary"!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{position:static!important}
}
@media (max-width:1024px){
  .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important}
}
@media (max-width:700px){
  .tcrm-sales-leads-v3{padding:11px!important;gap:10px!important}
  .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{overflow-x:auto!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > .grid{min-width:720px}
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=EXECUTIVE_V4")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=" + ",".join(str(p.relative_to(ROOT)) for p in FILES + [CSS]))
print(f"BACKUP={backup}")
