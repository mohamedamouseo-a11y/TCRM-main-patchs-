#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
CAL = SRC / "pages/CalendarPage.tsx"
SLA = SRC / "pages/TaskSlaDashboard.tsx"
CSS = SRC / "calendar-sla-reference-lock-v9.css"

OLD_IMPORTS = [
    'import "../sales-module-premium-v2-three-screen.css";',
    'import "../sales-module-premium-v2-1-corrective.css";',
    'import "../sales-3-screens-leads-design-system-v3.css";',
    'import "../sales-3-screens-executive-v4.css";',
    'import "../sales-3-screens-executive-v5.css";',
    'import "../sales-calendar-light-v6.css";',
    'import "../sales-3-screens-light-reference-v7.css";',
    'import "../calendar-sla-light-reference-v8.css";',
]
NEW_IMPORT = 'import "../calendar-sla-reference-lock-v9.css";'
MARKER = "TCRM_CALENDAR_SLA_REFERENCE_LOCK_V9"

for p in (CAL, SLA):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"calendar-sla-reference-lock-v9-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (CAL, SLA):
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

def clean_imports(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() not in OLD_IMPORTS and line.strip() != NEW_IMPORT]
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import "):
            insert_at = i + 1
    lines.insert(insert_at, NEW_IMPORT)
    if not any(MARKER in line for line in lines[:20]):
        lines.insert(1 if lines else 0, f"// {MARKER}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

for p in (CAL, SLA):
    clean_imports(p)

cal = CAL.read_text(encoding="utf-8")
old_root = 'className="tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-calendar-premium-v2 tcrm-sales-leads-v3 tcrm-sales-leads-v3-calendar p-4 md:p-6 space-y-5 fade-in"'
new_root = 'className="tcrm-calendar-reference-lock-v9 p-4 md:p-6 space-y-4 fade-in"'
if old_root in cal:
    cal = cal.replace(old_root, new_root, 1)
elif "tcrm-calendar-reference-lock-v9" not in cal:
    raise SystemExit("ERROR=CALENDAR_ROOT_ANCHOR_NOT_FOUND")

old_title = 'className="tcrm-v7-calendar-title tcrm-v8-calendar-title flex items-center gap-3"'
new_title = 'className="tcrm-calendar-title-v9 flex items-center gap-3"'
if old_title in cal:
    cal = cal.replace(old_title, new_title, 1)
elif "tcrm-calendar-title-v9" not in cal:
    raise SystemExit("ERROR=CALENDAR_TITLE_ANCHOR_NOT_FOUND")
CAL.write_text(cal, encoding="utf-8")

sla = SLA.read_text(encoding="utf-8")
old_sla_root = 'className="tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sla-premium-v2 tcrm-sales-leads-v3 tcrm-sales-leads-v3-sla p-6 space-y-6 fade-in"'
new_sla_root = 'className="tcrm-sla-reference-lock-v9 p-5 space-y-4 fade-in"'
if old_sla_root in sla:
    sla = sla.replace(old_sla_root, new_sla_root, 1)
elif "tcrm-sla-reference-lock-v9" not in sla:
    raise SystemExit("ERROR=SLA_ROOT_ANCHOR_NOT_FOUND")
SLA.write_text(sla, encoding="utf-8")

CSS_TEXT = r'''/* TCRM V9 — Calendar + Tasks & SLA Reference Lock
   Final scoped stylesheet for these two screens only.
   Old V2/V3/V4/V5/V6/V7/V8 visual imports are intentionally removed
   from CalendarPage.tsx and TaskSlaDashboard.tsx to stop cascade conflicts.
   No backend/data/permissions/business logic changes. */

/* ================= SHARED ================= */
.tcrm-calendar-reference-lock-v9,
.tcrm-sla-reference-lock-v9{
  --v9-ink:#17213c;
  --v9-muted:#74809a;
  --v9-purple:#6854ee;
  --v9-purple-2:#7c64f5;
  --v9-blue:#4f8cf7;
  --v9-green:#20b978;
  --v9-amber:#f2a31b;
  --v9-red:#ee5064;
  --v9-line:rgba(99,84,231,.14);
  --v9-line-strong:rgba(99,84,231,.22);
  --v9-card:#ffffff;
  --v9-soft:#fafbff;
  --v9-shadow:0 16px 38px -30px rgba(61,53,137,.34),0 4px 14px -12px rgba(53,64,112,.17);
  min-height:100%;
  background:
    radial-gradient(760px 350px at 3% -5%,rgba(124,100,245,.10),transparent 68%),
    linear-gradient(180deg,#fbfaff 0%,#f6f7ff 58%,#f2f5ff 100%)!important;
  color:var(--v9-ink);
}

.tcrm-calendar-reference-lock-v9 *,
.tcrm-sla-reference-lock-v9 *{
  box-sizing:border-box;
}

/* ================= CALENDAR ================= */
.tcrm-calendar-reference-lock-v9{
  padding:20px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
  position:relative!important;
  min-height:92px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:16px!important;
  overflow:hidden!important;
  padding:16px 18px!important;
  border:1px solid var(--v9-line-strong)!important;
  border-radius:19px!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(104,84,238,.11) 1px,transparent 1.2px) 0 0/15px 15px,
    radial-gradient(58% 180% at 83% 50%,rgba(124,100,245,.15),transparent 66%),
    linear-gradient(125deg,#fff 0%,#fbfaff 57%,#f3f1ff 100%)!important;
  box-shadow:var(--v9-shadow)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9{
  position:relative!important;
  z-index:2!important;
  display:flex!important;
  align-items:center!important;
  gap:12px!important;
  visibility:visible!important;
  opacity:1!important;
  min-width:280px!important;
  width:auto!important;
  height:auto!important;
  transform:none!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 > div:first-child{
  width:44px!important;
  height:44px!important;
  min-width:44px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  padding:0!important;
  border-radius:13px!important;
  background:linear-gradient(135deg,#765ff3,#6049e6)!important;
  border:1px solid rgba(255,255,255,.7)!important;
  box-shadow:0 13px 27px -16px rgba(86,62,213,.65)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 h1{
  display:block!important;
  margin:0!important;
  color:var(--v9-ink)!important;
  font-size:20px!important;
  line-height:1.15!important;
  font-weight:850!important;
  letter-spacing:-.025em!important;
  text-shadow:none!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 p{
  display:block!important;
  margin-top:4px!important;
  color:var(--v9-muted)!important;
  font-size:11.5px!important;
  line-height:1.3!important;
  font-weight:600!important;
  text-shadow:none!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero > button{
  position:relative!important;
  z-index:2!important;
  margin-inline-start:auto!important;
  min-height:42px!important;
  padding:0 18px!important;
  border:0!important;
  border-radius:12px!important;
  background:linear-gradient(135deg,#7357ee,#5e46e0)!important;
  color:#fff!important;
  box-shadow:0 14px 28px -17px rgba(89,62,218,.72)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpis{
  display:grid!important;
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  gap:10px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi{
  position:relative!important;
  min-height:88px!important;
  display:flex!important;
  align-items:center!important;
  gap:12px!important;
  overflow:hidden!important;
  padding:14px!important;
  border:1px solid var(--v9-line)!important;
  border-radius:16px!important;
  background:linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:var(--v9-shadow)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:2px;
  background:var(--v9-purple);
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(2)::before{background:var(--v9-blue)}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(3)::before{background:var(--v9-green)}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(4)::before{background:var(--v9-amber)}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi-icon{
  width:34px!important;
  height:34px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:10px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi strong{
  display:block;
  color:var(--v9-ink)!important;
  font-size:22px!important;
  line-height:1.05!important;
  font-weight:850!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi span{
  display:block;
  margin-top:4px;
  color:var(--v9-muted)!important;
  font-size:11px!important;
  font-weight:600!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,4.15fr) minmax(250px,.85fr)!important;
  gap:12px!important;
  align-items:stretch!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main,
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  min-width:0!important;
  border:1px solid var(--v9-line)!important;
  border-radius:16px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--v9-shadow)!important;
  overflow:hidden!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main{
  grid-column:auto!important;
  height:100%!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main > div:first-child{
  min-height:54px!important;
  padding:10px 14px!important;
  background:linear-gradient(180deg,#fff,#f8f9ff)!important;
  border-bottom-color:rgba(100,84,231,.10)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  min-height:46px!important;
  align-items:center!important;
  background:#f5f6fd!important;
  border-bottom-color:rgba(100,84,231,.10)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b > div{
  color:#8490a8!important;
  font-size:10.5px!important;
  font-weight:750!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:94px!important;
  padding:7px!important;
  border-color:rgba(102,113,158,.10)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:#faf9ff!important;
  box-shadow:inset 0 0 0 1px rgba(104,84,238,.08)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-emerald-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-amber-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-rose-100"]{
  border-radius:7px!important;
  padding:3px 5px!important;
  font-weight:700!important;
  box-shadow:none!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  grid-column:auto!important;
  align-self:stretch!important;
  height:100%!important;
  display:flex!important;
  flex-direction:column!important;
  position:static!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child{
  flex:0 0 auto!important;
  min-height:54px!important;
  padding:11px 13px!important;
  background:linear-gradient(180deg,#fff,#f8f9ff)!important;
  border-bottom-color:rgba(100,84,231,.10)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:last-child{
  flex:1 1 auto!important;
  min-height:0!important;
  max-height:none!important;
  overflow-y:auto!important;
  padding:12px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming .text-center.py-10{
  min-height:100%!important;
  height:100%!important;
  padding:24px 10px!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming .w-12.h-12{
  width:46px!important;
  height:46px!important;
  border-radius:13px!important;
  background:#f1f3fb!important;
}

/* ================= TASKS & SLA ================= */
.tcrm-sla-reference-lock-v9{
  padding:18px 20px!important;
}

.tcrm-sla-reference-lock-v9 [data-slot="card"]{
  gap:0!important;
  padding-block:0!important;
  overflow:hidden!important;
  border:1px solid var(--v9-line)!important;
  border-radius:16px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--v9-shadow)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell > div{
  min-height:88px!important;
  padding:16px 18px!important;
  border:1px solid var(--v9-line-strong)!important;
  border-radius:19px!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(104,84,238,.11) 1px,transparent 1.2px) 0 0/15px 15px,
    radial-gradient(58% 180% at 83% 50%,rgba(124,100,245,.15),transparent 66%),
    linear-gradient(125deg,#fff 0%,#fbfaff 57%,#f3f1ff 100%)!important;
  box-shadow:var(--v9-shadow)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell .absolute.inset-0{
  opacity:.18!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell .w-11.h-11{
  background:linear-gradient(135deg,#765ff3,#6049e6)!important;
  border:1px solid rgba(255,255,255,.7)!important;
  box-shadow:0 13px 27px -16px rgba(86,62,213,.65)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell h1{
  color:var(--v9-ink)!important;
  font-size:20px!important;
  font-weight:850!important;
  text-shadow:none!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell p{
  color:var(--v9-muted)!important;
  font-size:11.5px!important;
  font-weight:600!important;
  text-shadow:none!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell label{
  color:#6f7891!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell select,
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell button{
  min-height:38px!important;
  border:1px solid rgba(104,84,238,.18)!important;
  border-radius:10px!important;
  background:rgba(255,255,255,.88)!important;
  color:#3b4060!important;
  box-shadow:0 9px 22px -18px rgba(73,58,176,.50)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-kpi-grid{
  gap:10px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card{
  position:relative!important;
  min-height:86px!important;
  overflow:hidden!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:2px;
  background:var(--v9-purple);
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-1::before{background:var(--v9-green)}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-2::before{background:var(--v9-red)}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-3::before{background:var(--v9-amber)}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-4::before{background:var(--v9-blue)}

.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card [data-slot="card-content"]{
  padding:13px 14px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card .text-2xl{
  color:var(--v9-ink)!important;
  font-size:22px!important;
  font-weight:850!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-health{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  min-height:46px!important;
  overflow:hidden!important;
  border:1px solid var(--v9-line)!important;
  border-radius:14px!important;
  background:linear-gradient(180deg,#fff,#fafbff)!important;
  box-shadow:var(--v9-shadow)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item{
  display:flex!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:12px!important;
  padding:9px 14px!important;
  border-inline-end:1px solid rgba(104,84,238,.09)!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item:last-child{border-inline-end:0!important}

.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item span{
  color:var(--v9-muted)!important;
  font-size:9.5px!important;
  font-weight:780!important;
  text-transform:uppercase!important;
  letter-spacing:.045em!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item strong{
  color:var(--v9-ink)!important;
  font-size:11px!important;
  font-weight:820!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item strong.is-good{color:#16985d!important}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item strong.is-risk{color:#d93f58!important}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends,
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:12px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends > [data-slot="card"],
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution > [data-slot="card"]{
  min-height:0!important;
  height:auto!important;
}

.tcrm-sla-reference-lock-v9 [data-slot="card-header"]{
  min-height:44px!important;
  padding:10px 13px!important;
  border-bottom:1px solid rgba(104,84,238,.08)!important;
  background:linear-gradient(180deg,#fbfbff,#fff)!important;
}

.tcrm-sla-reference-lock-v9 [data-slot="card-content"]{
  padding:12px 13px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends .recharts-responsive-container{
  height:205px!important;
  min-height:205px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution .recharts-responsive-container{
  height:180px!important;
  min-height:180px!important;
}

.tcrm-sla-reference-lock-v9 .recharts-cartesian-grid line{
  stroke:rgba(105,116,170,.12)!important;
}

.tcrm-sla-reference-lock-v9 table{
  width:100%;
  border-collapse:separate!important;
  border-spacing:0 1px!important;
}

.tcrm-sla-reference-lock-v9 table thead tr{
  background:linear-gradient(180deg,#f3f4ff,#edf0fb)!important;
}

.tcrm-sla-reference-lock-v9 table tbody tr:nth-child(even){
  background:#f8f9ff!important;
}

.tcrm-sla-reference-lock-v9 table th{
  padding:7px 10px!important;
  color:#68748c!important;
  font-size:9.5px!important;
  font-weight:850!important;
  letter-spacing:.015em!important;
}

.tcrm-sla-reference-lock-v9 table td{
  padding:7px 10px!important;
  color:#536078!important;
  font-size:10px!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-agent-performance [data-slot="card-content"],
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-activity-table [data-slot="card-content"],
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-breaches [data-slot="card-content"]{
  padding:0!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-breaches{
  border:1px solid rgba(238,80,100,.22)!important;
  border-top:3px solid var(--v9-red)!important;
  box-shadow:0 16px 38px -31px rgba(208,48,73,.34)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-breaches [data-slot="card-header"]{
  background:linear-gradient(180deg,#fff7f8,#fff)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-breaches tbody tr:hover{
  background:#fff7f8!important;
}

/* ================= RESPONSIVE ================= */
@media (max-width:1365px){
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-layout{
    grid-template-columns:1fr!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
    height:auto!important;
  }
  .tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends,
  .tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution{
    grid-template-columns:1fr!important;
  }
}

@media (max-width:900px){
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpis{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  .tcrm-sla-reference-lock-v9 .tcrm-v21-sla-health{
    grid-template-columns:1fr!important;
  }
  .tcrm-sla-reference-lock-v9 .tcrm-v21-health-item{
    border-inline-end:0!important;
    border-bottom:1px solid rgba(104,84,238,.09)!important;
  }
}

@media (max-width:700px){
  .tcrm-calendar-reference-lock-v9,
  .tcrm-sla-reference-lock-v9{
    padding:11px!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpis{
    grid-template-columns:1fr!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
    min-height:138px!important;
    align-items:flex-start!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero > button{
    width:100%!important;
    align-self:flex-end!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main{
    overflow-x:auto!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main > .grid{
    min-width:720px!important;
  }
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=CALENDAR_SLA_REFERENCE_LOCK_V9")
print("OLD_VISUAL_IMPORTS_REMOVED=YES")
print("FINAL_STYLESHEET=calendar-sla-reference-lock-v9.css")
print("CALENDAR_REFERENCE_LOCK=YES")
print("SLA_REFERENCE_LOCK=YES")
print("SALES_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=3")
print(f"BACKUP={backup}")
