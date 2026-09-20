#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
PAGES = [
    SRC / "pages/SalesFunnelDashboard.tsx",
    SRC / "pages/TaskSlaDashboard.tsx",
    SRC / "pages/CalendarPage.tsx",
]
CSS = SRC / "sales-3-screens-executive-v5.css"
MARKER = "TCRM_SALES_3_SCREENS_EXECUTIVE_V5"
IMPORT = 'import "../sales-3-screens-executive-v5.css";'
V4_IMPORT = 'import "../sales-3-screens-executive-v4.css";'

for p in PAGES:
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"sales-3-screens-executive-v5-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in PAGES:
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

for p in PAGES:
    text = p.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if IMPORT not in text:
        if V4_IMPORT not in text:
            raise SystemExit(f"V4_IMPORT_MISSING={p}")
        text = text.replace(V4_IMPORT, V4_IMPORT + "\n" + IMPORT, 1)
    p.write_text(text, encoding="utf-8")

CSS_TEXT = r'''/* TCRM Sales 3 Screens — Executive V5
   Reference lock: Leads page is the visual master.
   Screens: Sales Funnel, Tasks & SLA, Calendar.
   UI only. No data, routes, permissions, API or business logic changes. */

.tcrm-sales-leads-v3{
  --v5-purple:#6554e8;
  --v5-purple-2:#7a63f2;
  --v5-blue:#4f86f7;
  --v5-cyan:#18b8ca;
  --v5-green:#25b97f;
  --v5-amber:#f0a51d;
  --v5-red:#ec526a;
  --v5-ink:#20233b;
  --v5-muted:#707a93;
  --v5-line:rgba(101,84,232,.15);
  --v5-line-strong:rgba(101,84,232,.25);
  --v5-card:rgba(255,255,255,.985);
  --v5-card-soft:rgba(248,249,255,.965);
  --v5-shadow:0 18px 45px -34px rgba(67,55,153,.34),0 7px 22px -19px rgba(63,72,130,.18),inset 0 1px 0 rgba(255,255,255,.98);
  background:
    radial-gradient(900px 460px at 1% -6%,rgba(122,99,242,.13),transparent 67%),
    radial-gradient(840px 430px at 99% -2%,rgba(79,134,247,.10),transparent 70%),
    linear-gradient(180deg,#fbfaff 0%,#f5f4ff 42%,#eef2ff 100%)!important;
}
.dark .tcrm-sales-leads-v3{
  --v5-ink:#f5f7ff;
  --v5-muted:#aab5ca;
  --v5-line:rgba(105,124,208,.22);
  --v5-line-strong:rgba(118,133,225,.34);
  --v5-card:rgba(8,22,43,.985);
  --v5-card-soft:rgba(9,27,51,.97);
  --v5-shadow:0 22px 54px -38px rgba(0,0,0,.9),0 0 38px -31px rgba(100,79,244,.42),inset 0 1px 0 rgba(255,255,255,.045);
  background:
    radial-gradient(900px 500px at 0% -5%,rgba(76,70,245,.19),transparent 68%),
    radial-gradient(900px 500px at 100% 0%,rgba(116,61,244,.13),transparent 72%),
    linear-gradient(180deg,#050b15 0%,#071426 52%,#06111f 100%)!important;
}

/* ===== Reference-matched top banner ===== */
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  position:relative!important;
  overflow:hidden!important;
  min-height:86px!important;
  padding:17px 19px!important;
  border-radius:18px!important;
  border:1px solid var(--v5-line-strong)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(101,84,232,.10) 1px,transparent 1.2px) 0 0/14px 14px,
    radial-gradient(62% 190% at 84% 50%,rgba(122,99,242,.16),transparent 64%),
    linear-gradient(120deg,#ffffff 0%,#faf8ff 56%,#f4f2ff 100%)!important;
  box-shadow:var(--v5-shadow)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.dark .tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  background:
    radial-gradient(circle at 1px 1px,rgba(132,145,231,.11) 1px,transparent 1.2px) 0 0/14px 14px,
    radial-gradient(66% 190% at 84% 50%,rgba(105,77,255,.19),transparent 66%),
    linear-gradient(135deg,#0a1a34 0%,#0e1a3e 100%)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell h1,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero h1{
  color:var(--v5-ink)!important;
  font-size:20px!important;
  font-weight:850!important;
  letter-spacing:-.025em!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell p,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero p{
  color:var(--v5-muted)!important;
  font-size:12px!important;
  font-weight:600!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell button,
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell select{
  min-height:38px!important;
  border-radius:10px!important;
  border:1px solid rgba(101,84,232,.18)!important;
  background:rgba(255,255,255,.86)!important;
  color:#393b61!important;
  box-shadow:0 9px 22px -18px rgba(73,58,176,.50)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell button,
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell select{
  background:rgba(8,24,48,.82)!important;
  color:#eef2ff!important;
  border-color:rgba(116,132,224,.27)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero button{
  background:linear-gradient(135deg,#7259ef,#5e49df)!important;
  color:#fff!important;
  border:0!important;
  box-shadow:0 14px 28px -17px rgba(89,62,218,.72)!important;
}

/* ===== KPI cards: same visual family as Leads ===== */
.tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis{gap:11px!important}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div{
  position:relative!important;
  overflow:hidden!important;
  min-height:91px!important;
  border-radius:16px!important;
  border:1px solid var(--v5-line)!important;
  background:linear-gradient(145deg,var(--v5-card),var(--v5-card-soft))!important;
  box-shadow:var(--v5-shadow)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card::before,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:3px;
  background:var(--v5-purple);
  opacity:.95;
}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-2::before,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(3)::before{background:var(--v5-green)}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-3::before{background:var(--v5-blue)}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-4::before,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(4)::before{background:var(--v5-amber)}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-5::before{background:#e65f82}
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(2)::before{background:#5b93f5}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis strong{
  color:var(--v5-ink)!important;
  font-size:23px!important;
  font-weight:880!important;
  letter-spacing:-.03em!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card .kpi-icon,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpi-icon{
  width:31px!important;height:31px!important;border-radius:9px!important;
}

/* ===== Shared cards ===== */
.tcrm-sales-leads-v3 .bg-card,
.tcrm-sales-leads-v3-funnel .chart-container,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-radius:17px!important;
  border:1px solid var(--v5-line)!important;
  background:linear-gradient(180deg,var(--v5-card),var(--v5-card-soft))!important;
  box-shadow:var(--v5-shadow)!important;
}
.tcrm-sales-leads-v3 [class*="CardHeader"],
.tcrm-sales-leads-v3 .chart-container > div:first-child{
  min-height:48px!important;
  padding:12px 15px!important;
  border-bottom:1px solid rgba(101,84,232,.09)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.84),rgba(247,248,255,.62))!important;
}
.dark .tcrm-sales-leads-v3 [class*="CardHeader"],
.dark .tcrm-sales-leads-v3 .chart-container > div:first-child{
  background:linear-gradient(180deg,rgba(15,34,63,.92),rgba(10,27,52,.80))!important;
  border-bottom-color:rgba(105,124,208,.15)!important;
}
.tcrm-sales-leads-v3 [class*="CardContent"]{padding:14px 15px!important}
.tcrm-sales-leads-v3 [class*="CardTitle"]{
  color:var(--v5-ink)!important;
  font-weight:820!important;
  letter-spacing:-.015em!important;
}
.tcrm-sales-leads-v3 .text-muted-foreground{color:var(--v5-muted)!important}

/* ===== Sales Funnel ===== */
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{
  grid-template-columns:minmax(0,.98fr) minmax(0,1.02fr)!important;
  gap:12px!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .chart-container{min-height:328px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .group > .flex-1 > div{
  border-radius:7px!important;
  box-shadow:0 9px 18px -13px rgba(49,46,129,.50)!important;
}
.dark .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .group > .flex-1 > div{
  box-shadow:0 9px 20px -14px rgba(0,0,0,.80)!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
  grid-template-columns:minmax(340px,.82fr) minmax(0,1.18fr)!important;
  grid-template-areas:"monthly campaign" "summary campaign"!important;
  gap:12px!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .chart-container{
  min-height:100%!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .chart-container .recharts-responsive-container{
  height:255px!important;
  max-height:255px!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly{min-height:185px!important}
.tcrm-sales-leads-v3-funnel table,
.tcrm-sales-leads-v3-sla table{border-collapse:separate!important;border-spacing:0 2px!important}
.tcrm-sales-leads-v3-funnel thead tr,
.tcrm-sales-leads-v3-sla thead tr{
  background:linear-gradient(180deg,#f2f3ff,#e9eefb)!important;
}
.tcrm-sales-leads-v3-funnel tbody tr,
.tcrm-sales-leads-v3-sla tbody tr{
  background:rgba(255,255,255,.68)!important;
  transition:background .16s ease,transform .16s ease;
}
.tcrm-sales-leads-v3-funnel tbody tr:nth-child(even),
.tcrm-sales-leads-v3-sla tbody tr:nth-child(even){background:rgba(244,246,255,.78)!important}
.tcrm-sales-leads-v3-funnel tbody tr:hover,
.tcrm-sales-leads-v3-sla tbody tr:hover{background:rgba(235,236,255,.93)!important}
.dark .tcrm-sales-leads-v3-funnel thead tr,
.dark .tcrm-sales-leads-v3-sla thead tr{
  background:linear-gradient(180deg,#102746,#0b1d39)!important;
}
.dark .tcrm-sales-leads-v3-funnel tbody tr,
.dark .tcrm-sales-leads-v3-sla tbody tr{background:rgba(8,22,42,.92)!important}
.dark .tcrm-sales-leads-v3-funnel tbody tr:nth-child(even),
.dark .tcrm-sales-leads-v3-sla tbody tr:nth-child(even){background:rgba(10,29,53,.94)!important}
.dark .tcrm-sales-leads-v3-funnel tbody tr:hover,
.dark .tcrm-sales-leads-v3-sla tbody tr:hover{background:rgba(18,38,72,.96)!important}

/* Stage conversion strip: remove the detached/washed-out feeling */
.tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid,
.tcrm-sales-leads-v3-funnel [class*="conversion"]{
  border-radius:16px!important;
  border:1px solid var(--v5-line)!important;
  background:linear-gradient(145deg,var(--v5-card),var(--v5-card-soft))!important;
  box-shadow:var(--v5-shadow)!important;
  overflow:hidden!important;
}
.tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid > div,
.tcrm-sales-leads-v3-funnel [class*="conversion"] > div{
  border-color:rgba(101,84,232,.12)!important;
  background:transparent!important;
}

/* ===== Tasks & SLA ===== */
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
  border-radius:15px!important;
  border:1px solid var(--v5-line)!important;
  background:linear-gradient(145deg,var(--v5-card),var(--v5-card-soft))!important;
  box-shadow:var(--v5-shadow)!important;
  overflow:hidden!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item{
  padding:11px 15px!important;
  border-inline-end:1px solid rgba(101,84,232,.10)!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item:last-child{border-inline-end:0!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item span{
  color:var(--v5-muted)!important;
  font-size:10px!important;
  font-weight:700!important;
  text-transform:uppercase!important;
  letter-spacing:.05em!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item strong{
  color:var(--v5-ink)!important;
  font-size:12px!important;
  font-weight:800!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends{
  grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr)!important;
  gap:12px!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v3-sla-distributions{gap:12px!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends > .bg-card{min-height:320px!important}
.tcrm-sales-leads-v3-sla [class*="border-red"]{
  border-radius:16px!important;
  border-color:rgba(236,82,106,.22)!important;
  overflow:hidden!important;
}
.tcrm-sales-leads-v3-sla [class*="border-red"] > div:first-child{
  background:linear-gradient(180deg,rgba(255,247,248,.98),rgba(255,241,244,.92))!important;
}
.dark .tcrm-sales-leads-v3-sla [class*="border-red"] > div:first-child{
  background:linear-gradient(180deg,rgba(52,25,39,.94),rgba(30,22,41,.94))!important;
}

/* ===== Calendar ===== */
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,3.35fr) minmax(285px,.65fr)!important;
  gap:12px!important;
  align-items:start!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
  grid-column:auto!important;
  min-width:0!important;
  overflow:hidden!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  grid-column:auto!important;
  min-width:0!important;
  position:sticky!important;
  top:12px!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:52px!important;
  padding:12px 14px!important;
  border-bottom:1px solid rgba(101,84,232,.10)!important;
  background:linear-gradient(180deg,#fafaff,#f2f4ff)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  background:linear-gradient(180deg,#0f2341,#0a1a33)!important;
  border-bottom-color:rgba(105,124,208,.16)!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  background:rgba(241,243,254,.88)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  background:rgba(11,29,56,.96)!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:106px!important;
  padding:7px!important;
  border-color:rgba(103,108,169,.10)!important;
  transition:background .17s ease,box-shadow .17s ease;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:linear-gradient(145deg,rgba(241,240,255,.91),rgba(248,250,255,.86))!important;
  box-shadow:inset 0 0 0 1px rgba(101,84,232,.10)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  border-color:rgba(100,119,199,.13)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:rgba(16,35,67,.90)!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-emerald-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-amber-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-rose-100"]{
  border-radius:7px!important;
  padding:3px 5px!important;
  font-weight:700!important;
  box-shadow:0 7px 15px -12px rgba(83,61,194,.55)!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child{
  max-height:590px!important;
  padding:10px!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div{
  border-radius:11px!important;
  border:1px solid transparent!important;
  padding:10px!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div:hover{
  background:rgba(241,240,255,.78)!important;
  border-color:var(--v5-line)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child > div:hover{
  background:rgba(16,34,64,.88)!important;
}

/* ===== Typography / density ===== */
.tcrm-sales-leads-v3 table th{
  color:#59647a!important;
  font-size:10.5px!important;
  font-weight:850!important;
  padding:9px 10px!important;
}
.tcrm-sales-leads-v3 table td{
  color:#4d5870!important;
  font-size:11.4px!important;
  padding:9px 10px!important;
}
.dark .tcrm-sales-leads-v3 table th{color:#afbad0!important}
.dark .tcrm-sales-leads-v3 table td{color:#a0adc2!important}

/* ===== Responsive ===== */
@media (max-width:1365px){
  .tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview,
  .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
    grid-template-columns:1fr!important;
    grid-template-areas:"monthly" "campaign" "summary"!important;
  }
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{position:static!important}
}
@media (max-width:1024px){
  .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
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
print("V5_REFERENCE=LEADS_LIGHT_DARK")
print("SCREENS=SalesFunnel,TasksSLA,Calendar")
print("UI_ONLY=YES")
print("BACKEND_UNCHANGED=YES")
print("FILES_CHANGED=4")
