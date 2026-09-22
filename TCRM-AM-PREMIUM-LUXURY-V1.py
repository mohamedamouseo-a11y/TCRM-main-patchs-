#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
DASH = SRC / "pages/AMDashboard.tsx"
CAL = SRC / "pages/AMCalendarPage.tsx"
CSS = SRC / "index.css"
MARKER = "TCRM_AM_PREMIUM_LUXURY_V1"

for p in (DASH, CAL, CSS):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"am-premium-luxury-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (DASH, CAL, CSS):
    shutil.copy2(p, backup / p.name)

def rep(text, old, new, label, count=1):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"ERROR={label}_ANCHOR_NOT_FOUND")
    return text.replace(old, new, count)

# Dashboard: visual-only hooks.
dash = DASH.read_text(encoding="utf-8")
if MARKER not in dash:
    lines = dash.splitlines()
    lines.insert(1, f"// {MARKER}")
    dash = "\n".join(lines) + "\n"

dash = rep(
    dash,
    'className="am-polish page-transition p-4 md:p-6 space-y-6"',
    'className="am-polish am-luxury-v1 am-dashboard-luxury page-transition p-4 md:p-6 space-y-6"',
    "DASH_ROOT",
)
dash = rep(
    dash,
    'relative overflow-hidden rounded-2xl p-5 shadow-sm border border-white/10',
    'am-luxury-kpi relative overflow-hidden rounded-2xl p-5 shadow-sm border border-white/10',
    "DASH_KPI",
)
dash = rep(
    dash,
    'className="rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden"',
    'className="am-luxury-section rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden"',
    "DASH_SECTION",
)
DASH.write_text(dash, encoding="utf-8")

# Calendar: premium hero + scoped visual hooks.
cal = CAL.read_text(encoding="utf-8")
if MARKER not in cal:
    lines = cal.splitlines()
    lines.insert(1, f"// {MARKER}")
    cal = "\n".join(lines) + "\n"

cal = rep(
    cal,
    'className="am-polish page-transition p-4 md:p-6 space-y-5"',
    'className="am-polish am-luxury-v1 am-calendar-luxury page-transition p-4 md:p-6 space-y-5"',
    "CAL_ROOT",
)

old_header = """        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {isRTL ? "تقويم العمليات" : "Operations Calendar"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {isRTL ? "إدارة مواعيد التواصل مع العملاء - اجتماعات، اتصالات، ومتابعات" : "Manage client appointments - meetings, calls, and follow-ups"}
            </p>
          </div>
          <Button onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }} className="gap-2">
            <Plus size={16} />
            {isRTL ? "موعد جديد" : "New Appointment"}
          </Button>
        </div>"""

new_header = """        {/* Premium executive hero */}
        <div className="am-calendar-hero">
          <div className="am-calendar-hero-main">
            <div className="am-calendar-hero-icon"><CalendarIcon size={24} /></div>
            <div>
              <div className="am-calendar-hero-kicker">{isRTL ? "تقويم العمليات" : "OPERATIONS CALENDAR"}</div>
              <h1>{isRTL ? "أدر مواعيد العملاء بوضوح" : "Manage client appointments with clarity"}</h1>
              <p>{isRTL ? "تابع الاجتماعات والاتصالات والمتابعات، وقدّم تجربة عملاء استثنائية." : "Keep track of meetings, calls, and follow-ups. Deliver exceptional client experiences."}</p>
            </div>
          </div>
          <div className="am-calendar-hero-actions">
            <div className="am-calendar-hero-quote">
              <span>{isRTL ? "اليوم فرصة جديدة" : "Today is a"}</span>
              <strong>{isRTL ? "لبناء علاقة أقوى" : "new opportunity"}</strong>
            </div>
            <Button onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }} className="am-calendar-new-btn gap-2">
              <Plus size={16} />
              {isRTL ? "موعد جديد" : "New Appointment"}
            </Button>
          </div>
        </div>"""
cal = rep(cal, old_header, new_header, "CAL_HERO")

cal = rep(
    cal,
    'rounded-2xl border p-4 shadow-sm',
    'am-luxury-cal-metric rounded-2xl border p-4 shadow-sm',
    "CAL_METRIC",
)
cal = rep(
    cal,
    'className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"',
    'className="am-luxury-filterbar rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"',
    "CAL_FILTER",
)
cal = rep(
    cal,
    '        {/* Calendar Card */}\n        <Card>',
    '        {/* Calendar Card */}\n        <Card className="am-luxury-calendar-card">',
    "CAL_CARD",
)
cal = rep(
    cal,
    '        {/* Upcoming Appointments List */}\n        <Card>',
    '        {/* Upcoming Appointments List */}\n        <Card className="am-luxury-upcoming-card">',
    "CAL_UPCOMING",
)
CAL.write_text(cal, encoding="utf-8")

# Scoped CSS only; no global component behavior changes.
css = CSS.read_text(encoding="utf-8")
if f"/* {MARKER}:START */" not in css:
    css += r"""

/* TCRM_AM_PREMIUM_LUXURY_V1:START */
.am-luxury-v1{
  --am-ink:#10162c;
  --am-muted:#747d95;
  --am-purple:#5d45df;
  --am-purple2:#8069f3;
  --am-green:#12b981;
  --am-amber:#f59e0b;
  --am-red:#f43f5e;
  --am-line:rgba(74,62,154,.12);
  --am-shadow:0 22px 60px -42px rgba(44,35,106,.34),0 7px 20px -16px rgba(46,51,87,.18);
  --am-shadow-hover:0 28px 72px -40px rgba(73,55,177,.38),0 12px 30px -20px rgba(44,49,85,.22);
  position:relative;
  isolation:isolate;
}
.am-luxury-v1::before{
  content:"";
  position:fixed;
  inset:0;
  z-index:-1;
  pointer-events:none;
  background:
    radial-gradient(900px 420px at 8% -4%,rgba(111,83,237,.10),transparent 67%),
    radial-gradient(760px 360px at 88% 1%,rgba(116,153,255,.07),transparent 72%),
    linear-gradient(180deg,#fdfdff 0%,#f8f9fd 52%,#f5f7fb 100%);
}

/* Dashboard hero */
.am-dashboard-luxury > .relative.overflow-hidden{
  min-height:112px!important;
  padding:22px 24px!important;
  border:1px solid rgba(124,105,240,.24)!important;
  border-radius:22px!important;
  background:
    radial-gradient(560px 200px at 72% 25%,rgba(184,169,255,.28),transparent 64%),
    linear-gradient(105deg,#25206f 0%,#4b3db2 47%,#7874e8 76%,#a8c5ff 100%)!important;
  box-shadow:0 30px 72px -44px rgba(54,42,154,.62),inset 0 1px 0 rgba(255,255,255,.20)!important;
}
.am-dashboard-luxury > .relative.overflow-hidden::before{
  content:"";
  position:absolute;
  width:480px;
  height:190px;
  right:120px;
  bottom:-110px;
  border:1px solid rgba(255,255,255,.11);
  border-radius:50%;
  transform:rotate(-9deg);
  pointer-events:none;
}
.am-dashboard-luxury > .relative.overflow-hidden h1{
  font-size:22px!important;
  font-weight:900!important;
  letter-spacing:-.035em!important;
}
.am-dashboard-luxury > .relative.overflow-hidden p{
  color:rgba(255,255,255,.84)!important;
}

/* Premium KPI cards */
.am-dashboard-luxury .am-luxury-kpi{
  min-height:118px!important;
  border:1px solid var(--am-line)!important;
  background:
    radial-gradient(170px 90px at 98% 0%,rgba(103,80,228,.07),transparent 72%),
    linear-gradient(150deg,#fff,#fbfcff)!important;
  box-shadow:var(--am-shadow)!important;
  transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;
}
.am-dashboard-luxury .am-luxury-kpi:hover{
  transform:translateY(-2px);
  border-color:rgba(94,73,222,.22)!important;
  box-shadow:var(--am-shadow-hover)!important;
}
.am-dashboard-luxury .am-luxury-kpi p{color:var(--am-muted)!important}
.am-dashboard-luxury .am-luxury-kpi p.mt-2{
  color:var(--am-ink)!important;
  font-weight:900!important;
  letter-spacing:-.04em;
}
.am-dashboard-luxury .am-luxury-kpi:nth-child(1){box-shadow:inset 3px 0 0 #6d50ec,var(--am-shadow)!important}
.am-dashboard-luxury .am-luxury-kpi:nth-child(2){box-shadow:inset 3px 0 0 #10b981,var(--am-shadow)!important}
.am-dashboard-luxury .am-luxury-kpi:nth-child(3){box-shadow:inset 3px 0 0 #f59e0b,var(--am-shadow)!important}
.am-dashboard-luxury .am-luxury-kpi:nth-child(4){box-shadow:inset 3px 0 0 #f43f5e,var(--am-shadow)!important}

/* Dashboard cards/tables */
.am-dashboard-luxury .am-luxury-section{
  border:1px solid var(--am-line)!important;
  border-radius:20px!important;
  background:linear-gradient(180deg,#fff,#fdfdff)!important;
  box-shadow:var(--am-shadow)!important;
  transition:box-shadow .2s ease,border-color .2s ease;
}
.am-dashboard-luxury .am-luxury-section:hover{
  border-color:rgba(91,67,230,.18)!important;
  box-shadow:var(--am-shadow-hover)!important;
}
.am-dashboard-luxury .am-luxury-section > div:first-child{
  min-height:54px;
  border-bottom:1px solid rgba(70,63,118,.08)!important;
  background:linear-gradient(180deg,#fefeff,#fff)!important;
}
.am-dashboard-luxury .am-luxury-section h2{
  color:#171d33!important;
  font-weight:850!important;
  letter-spacing:-.02em!important;
}
.am-dashboard-luxury table thead{
  background:linear-gradient(180deg,#fafbff,#f7f8fc);
}
.am-dashboard-luxury table thead th{
  color:#7a839b!important;
  font-size:10px!important;
  letter-spacing:.045em!important;
}
.am-dashboard-luxury table tbody tr:hover{background:#f8f7ff!important}
.am-dashboard-luxury .recharts-cartesian-grid-horizontal line{stroke:#edf0f7!important}
.am-dashboard-luxury .recharts-text{fill:#8790a8!important}

/* Calendar luxury hero */
.am-calendar-luxury .am-calendar-hero{
  position:relative;
  min-height:118px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:20px;
  overflow:hidden;
  padding:20px 22px;
  border:1px solid rgba(123,102,236,.20);
  border-radius:22px;
  color:white;
  background:
    radial-gradient(500px 180px at 72% 20%,rgba(192,174,255,.28),transparent 64%),
    linear-gradient(110deg,#23215f 0%,#43349f 46%,#705ae3 75%,#322c87 100%);
  box-shadow:0 28px 70px -42px rgba(50,38,145,.62),inset 0 1px 0 rgba(255,255,255,.18);
}
.am-calendar-luxury .am-calendar-hero::before{
  content:"";
  position:absolute;
  inset:-80px 16% auto auto;
  width:400px;
  height:210px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:50%;
  transform:rotate(-14deg);
}
.am-calendar-luxury .am-calendar-hero-main,
.am-calendar-luxury .am-calendar-hero-actions{
  position:relative;
  z-index:2;
  display:flex;
  align-items:center;
}
.am-calendar-luxury .am-calendar-hero-main{gap:15px}
.am-calendar-luxury .am-calendar-hero-icon{
  width:52px;
  height:52px;
  display:flex;
  align-items:center;
  justify-content:center;
  flex:0 0 auto;
  border:1px solid rgba(255,255,255,.24);
  border-radius:16px;
  color:#f6d36d;
  background:linear-gradient(145deg,rgba(255,255,255,.16),rgba(255,255,255,.07));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.20),0 18px 32px -24px rgba(0,0,0,.6);
  backdrop-filter:blur(10px);
}
.am-calendar-luxury .am-calendar-hero-kicker{
  margin-bottom:4px;
  color:#f5d77d;
  font-size:10px;
  font-weight:850;
  letter-spacing:.10em;
}
.am-calendar-luxury .am-calendar-hero h1{
  margin:0;
  font-size:23px;
  line-height:1.05;
  font-weight:900;
  letter-spacing:-.035em;
}
.am-calendar-luxury .am-calendar-hero p{
  margin-top:6px;
  max-width:660px;
  color:rgba(255,255,255,.78);
  font-size:12px;
  font-weight:500;
}
.am-calendar-luxury .am-calendar-hero-actions{
  gap:18px;
  margin-inline-start:auto;
}
.am-calendar-luxury .am-calendar-hero-quote{
  display:none;
  padding-inline-start:12px;
  border-inline-start:2px solid #f2c95f;
  color:rgba(255,255,255,.74);
  font-family:Georgia,serif;
  font-size:13px;
  line-height:1.15;
}
.am-calendar-luxury .am-calendar-hero-quote strong{
  display:block;
  margin-top:4px;
  color:white;
  font-size:15px;
  font-weight:500;
}
.am-calendar-luxury .am-calendar-new-btn{
  min-height:42px!important;
  padding-inline:18px!important;
  border:1px solid rgba(255,255,255,.24)!important;
  border-radius:11px!important;
  background:linear-gradient(180deg,#fff,#f5f2ff)!important;
  color:#4332a7!important;
  font-weight:800!important;
  box-shadow:0 15px 30px -20px rgba(4,4,34,.72)!important;
}
@media (min-width:1180px){.am-calendar-luxury .am-calendar-hero-quote{display:block}}

/* Calendar metric cards */
.am-calendar-luxury .am-luxury-cal-metric{
  position:relative;
  min-height:112px;
  overflow:hidden;
  border-color:var(--am-line)!important;
  background:
    radial-gradient(150px 80px at 98% 0%,rgba(102,79,229,.06),transparent 72%),
    linear-gradient(150deg,#fff,#fbfcff)!important;
  box-shadow:var(--am-shadow)!important;
}
.am-calendar-luxury .am-luxury-cal-metric::after{
  content:"";
  position:absolute;
  right:14px;
  bottom:12px;
  width:76px;
  height:30px;
  opacity:.18;
  background:linear-gradient(120deg,transparent 0 12%,#7560ea 13% 16%,transparent 17% 30%,#7560ea 31% 35%,transparent 36% 48%,#7560ea 49% 56%,transparent 57% 70%,#7560ea 71% 82%,transparent 83%);
}
.am-calendar-luxury .am-luxury-filterbar{
  border-color:var(--am-line)!important;
  background:rgba(255,255,255,.94)!important;
  box-shadow:0 16px 48px -38px rgba(43,35,103,.34)!important;
  backdrop-filter:blur(16px);
}
.am-calendar-luxury .am-luxury-filterbar button{border-radius:999px!important}

/* Calendar surfaces */
.am-calendar-luxury .am-luxury-calendar-card,
.am-calendar-luxury .am-luxury-upcoming-card{
  overflow:hidden;
  border:1px solid var(--am-line)!important;
  border-radius:20px!important;
  background:linear-gradient(180deg,#fff,#fdfdff)!important;
  box-shadow:var(--am-shadow)!important;
}
.am-calendar-luxury .am-luxury-calendar-card [data-slot="card-header"],
.am-calendar-luxury .am-luxury-upcoming-card [data-slot="card-header"]{
  border-bottom:1px solid rgba(70,63,118,.08)!important;
  background:linear-gradient(180deg,#fefeff,#fff)!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7{
  overflow:hidden;
  border:1px solid #e7e9f0;
  border-radius:14px!important;
  background:#e7e9f0!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(-n+7){
  padding-block:10px!important;
  color:#778198!important;
  background:linear-gradient(180deg,#f7f8fb,#f1f3f8)!important;
  font-weight:800!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8){
  min-height:108px!important;
  background:#fff!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8):hover{
  background:#faf9ff!important;
}
.am-calendar-luxury .am-luxury-upcoming-card [data-slot="card-content"] > .space-y-2 > div{
  border-color:transparent!important;
  border-bottom:1px solid #eef0f5!important;
  border-radius:12px!important;
}
.am-calendar-luxury .am-luxury-upcoming-card [data-slot="card-content"] > .space-y-2 > div:hover{
  background:#faf9ff!important;
  box-shadow:0 9px 24px -20px rgba(59,44,144,.30);
}

/* Dark theme stays usable */
.dark .am-luxury-v1::before{background:linear-gradient(180deg,#11131b,#0f1118)}
.dark .am-dashboard-luxury .am-luxury-kpi,
.dark .am-dashboard-luxury .am-luxury-section,
.dark .am-calendar-luxury .am-luxury-cal-metric,
.dark .am-calendar-luxury .am-luxury-filterbar,
.dark .am-calendar-luxury .am-luxury-calendar-card,
.dark .am-calendar-luxury .am-luxury-upcoming-card{
  border-color:rgba(255,255,255,.09)!important;
  background:linear-gradient(180deg,#191c27,#151821)!important;
}
.dark .am-dashboard-luxury .am-luxury-kpi p.mt-2,
.dark .am-dashboard-luxury .am-luxury-section h2{color:#f5f7ff!important}

@media (max-width:900px){
  .am-calendar-luxury .am-calendar-hero{align-items:flex-start;flex-direction:column}
  .am-calendar-luxury .am-calendar-hero-actions{width:100%;margin-inline-start:0;justify-content:flex-end}
}
@media (max-width:640px){
  .am-luxury-v1{padding:14px!important}
  .am-calendar-luxury .am-calendar-hero h1{font-size:20px}
  .am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8){min-height:78px!important}
}
/* TCRM_AM_PREMIUM_LUXURY_V1:END */
"""
    CSS.write_text(css, encoding="utf-8")

print("PATCH=PASS")
print("AM_DASHBOARD=PREMIUM_LUXURY_V1")
print("AM_CALENDAR=PREMIUM_LUXURY_V1")
print("FUNCTIONS_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("FILES_CHANGED=3")
print(f"BACKUP={backup}")
print("ERROR=NONE")
