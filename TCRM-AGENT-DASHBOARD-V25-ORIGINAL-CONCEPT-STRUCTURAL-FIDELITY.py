#!/usr/bin/env python3
from pathlib import Path
import shutil
import datetime
import hashlib

ROOT = Path.cwd()
AGENT = ROOT / "client/src/pages/AgentDashboard.tsx"
REMINDERS = ROOT / "client/src/components/ReminderCalendar.tsx"
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"
MARKER = "/* TCRM Dashboard Original Concept V25 Structural Fidelity */"
V24_MARKER = "/* TCRM Dashboard Original Concept V24 Fidelity */"

for p in (AGENT, REMINDERS, CSS):
    if not p.exists():
        raise SystemExit(f"ERROR=TARGET_MISSING:{p}")

agent_before = AGENT.read_text(encoding="utf-8")
rem_before = REMINDERS.read_text(encoding="utf-8")
css_before = CSS.read_text(encoding="utf-8")

required_agent = [
    "tcrm-premium-dashboard",
    "luxury-kpi-card",
    "tcrm-luxury-leads-card",
    "tcrm-luxury-reminders-card",
    "tcrm-luxury-sla-card",
    "tcrm-luxury-canvas",
    "tcrm-canvas-values",
    "luxury-activity-icon",
]
missing_agent = [x for x in required_agent if x not in agent_before]
if missing_agent:
    raise SystemExit("ERROR=AGENT_SOURCE_GUARD_MISSING:" + "|".join(missing_agent))

required_reminder = [
    'trpc.leadReminders.getToday.useQuery()',
    'trpc.leadReminders.getCalendar.useQuery({ month, year })',
    'markDoneMutation.mutate({ id: reminder.id })',
    'No tasks for today',
    '/* Calendar View */',
]
missing_reminder = [x for x in required_reminder if x not in rem_before]
if missing_reminder:
    raise SystemExit("ERROR=REMINDER_SOURCE_GUARD_MISSING:" + "|".join(missing_reminder))

if V24_MARKER not in css_before:
    raise SystemExit("ERROR=V24_BASELINE_NOT_FOUND")

if MARKER in css_before:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

agent_hash_before = hashlib.sha256(AGENT.read_bytes()).hexdigest()

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v25-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(REMINDERS, backup_dir / REMINDERS.name)
shutil.copy2(CSS, backup_dir / CSS.name)

rem = rem_before

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ERROR=REPLACE_GUARD_{label}:COUNT={count}")
    return text.replace(old, new, 1)

rem = replace_once(
    rem,
    '<div className="space-y-4">',
    '<div className="space-y-4 tcrm-reminder-stack">',
    "REMINDER_STACK",
)

rem = replace_once(
    rem,
    '<Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-purple-50/30">',
    '<Card className="tcrm-today-tasks-card border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-purple-50/30">',
    "TODAY_CARD",
)

old_empty = '''            <div className="py-6 text-center text-muted-foreground text-xs">\n              {isRTL ? "لا توجد مهام لليوم" : "No tasks for today"}\n            </div>'''
new_empty = '''            <div className="tcrm-today-empty py-6 text-center text-muted-foreground text-xs">\n              <div className="tcrm-today-empty-icon" aria-hidden="true"><Calendar size={24} /></div>\n              <div className="tcrm-today-empty-title">{isRTL ? "لا توجد مهام لليوم" : "No tasks for today"}</div>\n              <div className="tcrm-today-empty-subtitle">{isRTL ? "أنت منجز كل شيء لليوم ✨" : "You're all caught up! ✨"}</div>\n            </div>'''
rem = replace_once(rem, old_empty, new_empty, "TODAY_EMPTY")

rem = replace_once(
    rem,
    '      {/* Calendar View */}\n      <Card>',
    '      {/* Calendar View */}\n      <Card className="tcrm-reminder-calendar-card">',
    "CALENDAR_CARD",
)

rem = replace_once(
    rem,
    '<div className="flex items-center justify-between">',
    '<div className="tcrm-reminder-calendar-header flex items-center justify-between">',
    "CALENDAR_HEADER",
)

rem = replace_once(
    rem,
    '<div className="grid grid-cols-7 gap-0.5 mb-1">',
    '<div className="tcrm-calendar-weekdays grid grid-cols-7 gap-0.5 mb-1">',
    "CALENDAR_WEEKDAYS",
)

rem = replace_once(
    rem,
    '<div className="grid grid-cols-7 gap-0.5">',
    '<div className="tcrm-calendar-grid grid grid-cols-7 gap-0.5">',
    "CALENDAR_GRID",
)

rem = replace_once(
    rem,
    'className={`aspect-square rounded-md flex flex-col items-center justify-center relative transition-all text-xs',
    'className={`tcrm-calendar-day aspect-square rounded-md flex flex-col items-center justify-center relative transition-all text-xs',
    "CALENDAR_DAY",
)

V25 = r'''

/* TCRM Dashboard Original Concept V25 Structural Fidelity */
/* Visual fidelity only. Real reminder queries/actions, CRM routes, data, permissions and business logic are preserved. */

/* A. STRUCTURAL CONTINUITY — left visual scene must fill the same vertical story as the right rail. */
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .lg\:col-span-2 {
  display:flex;
  flex-direction:column;
  min-height:100%;
}
.tcrm-premium-dashboard .tcrm-luxury-leads-card {
  flex:0 0 auto;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas {
  flex:1 1 auto;
  min-height:clamp(580px,52vw,760px) !important;
  margin-top:18px !important;
  border:0 !important;
  border-radius:0 !important;
  box-shadow:none !important;
  align-items:flex-end !important;
  padding:clamp(40px,5vw,76px) clamp(30px,4vw,58px) 42px !important;
  background:
    radial-gradient(circle at 13% 18%,rgba(124,58,237,.12),transparent 24rem),
    radial-gradient(circle at 70% 38%,rgba(59,130,246,.10),transparent 30rem),
    radial-gradient(ellipse at 48% 100%,rgba(99,102,241,.18),transparent 42rem),
    linear-gradient(180deg,rgba(250,251,255,.78),rgba(238,243,255,.96)) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas {
  background:
    radial-gradient(circle at 12% 14%,rgba(104,62,255,.22),transparent 25rem),
    radial-gradient(circle at 70% 33%,rgba(41,93,231,.18),transparent 32rem),
    radial-gradient(ellipse at 50% 100%,rgba(80,58,220,.34),transparent 46rem),
    linear-gradient(180deg,#091326 0%,#0a1428 50%,#0a1530 100%) !important;
}

/* Star field + atmospheric grain. */
.tcrm-premium-dashboard .tcrm-luxury-canvas::before {
  inset:0 !important;
  opacity:.72 !important;
  mask-image:none !important;
  background-image:
    radial-gradient(circle,rgba(99,102,241,.19) 0 1px,transparent 1.5px),
    radial-gradient(circle,rgba(139,92,246,.12) 0 1px,transparent 1.4px),
    linear-gradient(135deg,rgba(99,102,241,.025) 1px,transparent 1px) !important;
  background-size:58px 58px,91px 91px,34px 34px !important;
  background-position:0 0,21px 27px,0 0 !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas::before {
  background-image:
    radial-gradient(circle,rgba(170,163,255,.30) 0 1px,transparent 1.5px),
    radial-gradient(circle,rgba(109,136,255,.19) 0 1px,transparent 1.4px),
    linear-gradient(135deg,rgba(125,140,255,.035) 1px,transparent 1px) !important;
}

/* Original-concept mountain/wave field instead of the circular arc approximation. */
.tcrm-premium-dashboard .tcrm-luxury-canvas::after {
  left:-5% !important;
  right:-5% !important;
  bottom:-2% !important;
  height:48% !important;
  opacity:.58 !important;
  animation:v25-wave-drift 18s ease-in-out infinite alternate !important;
  background-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%201200%20360'%3E%3Cpath%20d='M0%20288%20C120%20210%20240%20254%20358%20184%20S602%20228%20718%20142%20S966%20196%201200%2094'%20fill='none'%20stroke='%236366f1'%20stroke-opacity='.25'%20stroke-width='2'/%3E%3Cpath%20d='M0%20318%20C140%20252%20262%20286%20390%20222%20S636%20256%20758%20182%20S986%20226%201200%20134'%20fill='none'%20stroke='%238b5cf6'%20stroke-opacity='.22'%20stroke-width='2'/%3E%3Cpath%20d='M0%20342%20C150%20294%20302%20308%20428%20262%20S664%20284%20792%20230%20S1014%20256%201200%20192'%20fill='none'%20stroke='%2360a5fa'%20stroke-opacity='.18'%20stroke-width='2'/%3E%3C/svg%3E") !important;
  background-repeat:no-repeat !important;
  background-position:center bottom !important;
  background-size:122% 100% !important;
  filter:drop-shadow(0 0 16px rgba(99,102,241,.14));
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas::after {
  opacity:.88 !important;
  background-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%201200%20360'%3E%3Cpath%20d='M0%20288%20C120%20210%20240%20254%20358%20184%20S602%20228%20718%20142%20S966%20196%201200%2094'%20fill='none'%20stroke='%238b7cff'%20stroke-opacity='.42'%20stroke-width='2'/%3E%3Cpath%20d='M0%20318%20C140%20252%20262%20286%20390%20222%20S636%20256%20758%20182%20S986%20226%201200%20134'%20fill='none'%20stroke='%237c5cff'%20stroke-opacity='.36'%20stroke-width='2'/%3E%3Cpath%20d='M0%20342%20C150%20294%20302%20308%20428%20262%20S664%20284%20792%20230%20S1014%20256%201200%20192'%20fill='none'%20stroke='%235f8fff'%20stroke-opacity='.30'%20stroke-width='2'/%3E%3C/svg%3E") !important;
  filter:drop-shadow(0 0 20px rgba(112,92,255,.30));
}
@keyframes v25-wave-drift {
  from{transform:translate3d(-1.5%,0,0) scale(1.01)}
  to{transform:translate3d(1.5%,-1%,0) scale(1.035)}
}

/* Editorial quote block lower in the scene. */
.tcrm-premium-dashboard .tcrm-luxury-canvas-content {
  width:min(100%,680px) !important;
  max-width:680px !important;
  z-index:2 !important;
}
.tcrm-premium-dashboard .tcrm-canvas-kicker {
  width:48px !important;
  height:48px !important;
  border-radius:15px !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  color:#6d5dfc !important;
  background:radial-gradient(circle at 35% 25%,rgba(255,255,255,.95),rgba(99,102,241,.11)) !important;
  border:1px solid rgba(99,102,241,.22) !important;
  box-shadow:0 0 28px -10px rgba(99,102,241,.62),inset 0 1px 0 rgba(255,255,255,.9) !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-kicker {
  color:#b6adff !important;
  background:radial-gradient(circle at 35% 25%,rgba(129,140,248,.26),rgba(67,56,202,.12)) !important;
  border-color:rgba(139,130,255,.38) !important;
  box-shadow:0 0 30px -8px rgba(111,91,255,.68),inset 0 1px 0 rgba(255,255,255,.10) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  position:relative;
  margin-top:24px !important;
  margin-bottom:18px !important;
  font-family:ui-serif,Georgia,Cambria,"Times New Roman",serif !important;
  font-size:clamp(2.35rem,4vw,4.25rem) !important;
  line-height:.96 !important;
  font-weight:600 !important;
  letter-spacing:-.055em !important;
  color:#2f2b8f !important;
  text-shadow:0 10px 32px rgba(99,102,241,.08);
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  color:#f4f3ff !important;
  text-shadow:0 0 28px rgba(139,124,255,.22);
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-headline::before {
  content:"“";
  position:absolute;
  left:-.46em;
  top:-.22em;
  font-size:1.25em;
  color:rgba(99,102,241,.32);
  font-family:Georgia,serif;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas-headline::before {color:rgba(167,139,250,.42)}
.tcrm-premium-dashboard .tcrm-canvas-accent {
  width:74px !important;
  height:3px !important;
  border-radius:99px !important;
  background:linear-gradient(90deg,#6d5dfc,#60a5fa,transparent) !important;
  box-shadow:0 0 16px rgba(99,102,241,.38) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-sub {
  margin:16px 0 28px !important;
  font-size:.92rem !important;
  color:#667085 !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas-sub {color:rgba(214,220,235,.76) !important}

/* B. THREE VALUE ITEMS — no mini cards; luminous inline icon + divider like the original. */
.tcrm-premium-dashboard .tcrm-luxury-canvas-values {
  display:grid !important;
  grid-template-columns:repeat(3,minmax(0,1fr)) !important;
  gap:0 !important;
  width:100% !important;
  border-top:1px solid rgba(99,102,241,.13);
  padding-top:10px;
}
.tcrm-premium-dashboard .tcrm-canvas-value {
  min-width:0 !important;
  padding:12px 22px !important;
  display:grid !important;
  grid-template-columns:48px minmax(0,1fr) !important;
  align-items:center !important;
  gap:13px !important;
  background:transparent !important;
  border:0 !important;
  border-radius:0 !important;
  box-shadow:none !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value:first-child {padding-left:0 !important}
.tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
  border-left:1px solid rgba(99,102,241,.15) !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
  border-left-color:rgba(139,130,255,.24) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon {
  width:46px !important;
  height:46px !important;
  border-radius:50% !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  color:#6258f5 !important;
  background:radial-gradient(circle at 34% 24%,rgba(255,255,255,.98),rgba(99,102,241,.10)) !important;
  border:1px solid rgba(99,102,241,.24) !important;
  box-shadow:0 0 0 5px rgba(99,102,241,.055),0 0 24px -9px rgba(99,102,241,.72),inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value-icon {
  color:#c0b8ff !important;
  background:radial-gradient(circle at 35% 22%,rgba(129,140,248,.28),rgba(52,46,125,.20)) !important;
  border-color:rgba(140,130,255,.38) !important;
  box-shadow:0 0 0 5px rgba(104,83,255,.07),0 0 26px -8px rgba(111,91,255,.78),inset 0 1px 0 rgba(255,255,255,.10) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon svg {width:21px !important;height:21px !important;stroke-width:1.85}
.tcrm-premium-dashboard .tcrm-canvas-value-copy {gap:3px !important}
.tcrm-premium-dashboard .tcrm-canvas-value-title {
  font-size:.82rem !important;
  line-height:1.15 !important;
  color:#35325f !important;
  font-weight:760 !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-subtitle {
  font-size:.70rem !important;
  line-height:1.25 !important;
  color:#7b849b !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value-title {color:#f1f2ff !important}
.dark .tcrm-premium-dashboard .tcrm-canvas-value-subtitle {color:rgba(173,184,207,.74) !important}

/* C. REAL TODAY TASKS — richer empty state without adding fake actions. */
.tcrm-premium-dashboard .tcrm-today-tasks-card {
  min-height:172px !important;
  border-color:rgba(100,103,231,.22) !important;
  background:
    radial-gradient(circle at 88% 10%,rgba(124,58,237,.10),transparent 12rem),
    linear-gradient(155deg,rgba(255,255,255,.99),rgba(247,249,255,.95)) !important;
}
.dark .tcrm-premium-dashboard .tcrm-today-tasks-card {
  border-color:rgba(119,125,255,.30) !important;
  background:
    radial-gradient(circle at 88% 8%,rgba(96,72,255,.16),transparent 12rem),
    linear-gradient(155deg,rgba(18,31,57,.99),rgba(10,22,42,.99)) !important;
}
.tcrm-premium-dashboard .tcrm-today-tasks-card [data-slot="card-title"] svg {
  color:#6d5dfc !important;
  filter:drop-shadow(0 0 7px rgba(109,93,252,.42));
}
.tcrm-premium-dashboard .tcrm-today-empty {
  min-height:104px !important;
  display:flex !important;
  flex-direction:column !important;
  align-items:center !important;
  justify-content:center !important;
  gap:5px !important;
  padding:14px 20px 20px !important;
}
.tcrm-premium-dashboard .tcrm-today-empty-icon {
  width:44px;
  height:44px;
  border-radius:14px;
  display:flex;
  align-items:center;
  justify-content:center;
  margin-bottom:4px;
  color:#6d5dfc;
  background:radial-gradient(circle at 36% 24%,#fff,rgba(99,102,241,.11));
  border:1px solid rgba(99,102,241,.22);
  box-shadow:0 0 0 5px rgba(99,102,241,.045),0 10px 26px -13px rgba(99,102,241,.55),inset 0 1px 0 #fff;
}
.dark .tcrm-premium-dashboard .tcrm-today-empty-icon {
  color:#b7aeff;
  background:radial-gradient(circle at 36% 24%,rgba(125,135,255,.26),rgba(46,42,100,.22));
  border-color:rgba(135,128,255,.34);
  box-shadow:0 0 0 5px rgba(104,83,255,.06),0 0 24px -9px rgba(110,88,255,.66),inset 0 1px 0 rgba(255,255,255,.09);
}
.tcrm-premium-dashboard .tcrm-today-empty-title {font-size:.76rem;font-weight:700;color:#46506a}
.tcrm-premium-dashboard .tcrm-today-empty-subtitle {font-size:.66rem;color:#8b95aa}
.dark .tcrm-premium-dashboard .tcrm-today-empty-title {color:#eef1ff}
.dark .tcrm-premium-dashboard .tcrm-today-empty-subtitle {color:rgba(166,178,202,.72)}

/* D. REMINDER CALENDAR — compact premium grid, luminous selected day, clear header icon. */
.tcrm-premium-dashboard .tcrm-reminder-calendar-card {
  overflow:hidden;
  border-color:rgba(102,108,225,.22) !important;
  background:
    radial-gradient(circle at 90% 0%,rgba(99,102,241,.075),transparent 14rem),
    linear-gradient(155deg,rgba(255,255,255,.995),rgba(247,249,255,.96)) !important;
  box-shadow:0 24px 56px -40px rgba(65,55,170,.36),inset 0 1px 0 rgba(255,255,255,.96) !important;
}
.dark .tcrm-premium-dashboard .tcrm-reminder-calendar-card {
  border-color:rgba(113,122,255,.29) !important;
  background:
    radial-gradient(circle at 90% 0%,rgba(104,77,255,.13),transparent 15rem),
    linear-gradient(155deg,rgba(18,31,56,.995),rgba(10,22,42,.995)) !important;
  box-shadow:0 26px 60px -40px rgba(0,0,0,.96),0 0 32px -26px rgba(94,82,255,.65),inset 0 1px 0 rgba(255,255,255,.055) !important;
}
.tcrm-premium-dashboard .tcrm-reminder-calendar-header {
  min-height:34px;
}
.tcrm-premium-dashboard .tcrm-reminder-calendar-header [data-slot="card-title"] svg {
  width:18px !important;
  height:18px !important;
  color:#665cf5 !important;
  padding:2px;
  border-radius:6px;
  background:rgba(99,102,241,.08);
  box-shadow:0 0 18px -5px rgba(99,102,241,.72);
}
.dark .tcrm-premium-dashboard .tcrm-reminder-calendar-header [data-slot="card-title"] svg {
  color:#b7afff !important;
  background:rgba(104,83,255,.13);
  box-shadow:0 0 20px -4px rgba(104,83,255,.82);
}
.tcrm-premium-dashboard .tcrm-reminder-calendar-card [data-slot="card-content"] {
  padding:8px 14px 16px !important;
}
.tcrm-premium-dashboard .tcrm-calendar-weekdays {
  gap:3px !important;
  margin-bottom:5px !important;
}
.tcrm-premium-dashboard .tcrm-calendar-weekdays > div {
  font-size:9px !important;
  letter-spacing:.02em;
  color:#8a93a8 !important;
}
.dark .tcrm-premium-dashboard .tcrm-calendar-weekdays > div {color:rgba(160,174,200,.66) !important}
.tcrm-premium-dashboard .tcrm-calendar-grid {
  gap:4px !important;
}
.tcrm-premium-dashboard .tcrm-calendar-day {
  border-radius:10px !important;
  font-weight:650 !important;
  color:#34405b;
  min-width:0;
}
.dark .tcrm-premium-dashboard .tcrm-calendar-day {color:#e5e9f5}
.tcrm-premium-dashboard .tcrm-calendar-day:hover {
  background:rgba(99,102,241,.075) !important;
  transform:translateY(-1px);
}
.dark .tcrm-premium-dashboard .tcrm-calendar-day:hover {background:rgba(105,96,255,.12) !important}
.tcrm-premium-dashboard .tcrm-calendar-day.bg-indigo-600 {
  color:white !important;
  background:linear-gradient(145deg,#754dff 0%,#5d6cff 100%) !important;
  box-shadow:0 0 0 2px rgba(255,255,255,.90),0 0 0 4px rgba(99,102,241,.16),0 10px 24px -8px rgba(86,70,255,.64),0 0 28px -6px rgba(99,102,241,.46) !important;
  transform:scale(1.06);
}
.dark .tcrm-premium-dashboard .tcrm-calendar-day.bg-indigo-600 {
  box-shadow:0 0 0 2px rgba(10,22,42,.96),0 0 0 4px rgba(122,108,255,.32),0 12px 28px -8px rgba(68,49,219,.88),0 0 34px -4px rgba(104,83,255,.70) !important;
}

/* E. KPI SPARKLINES — smooth mask instead of blocky mountain polygons. */
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"]::after {
  width:62px !important;
  height:26px !important;
  right:12px !important;
  bottom:11px !important;
  clip-path:none !important;
  background:linear-gradient(180deg,rgba(var(--v24-kpi,99,102,241),.66),rgba(var(--v24-kpi,99,102,241),.10)) !important;
  -webkit-mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2028'%3E%3Cpath%20d='M1%2024%20C7%2022%209%2018%2014%2019%20C20%2020%2022%2012%2028%2014%20C34%2016%2037%208%2043%209%20C49%2010%2052%204%2063%205%20L63%2028%20L1%2028Z'%20fill='black'/%3E%3C/svg%3E") !important;
  -webkit-mask-repeat:no-repeat !important;
  -webkit-mask-position:center !important;
  -webkit-mask-size:100% 100% !important;
  mask-image:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2028'%3E%3Cpath%20d='M1%2024%20C7%2022%209%2018%2014%2019%20C20%2020%2022%2012%2028%2014%20C34%2016%2037%208%2043%209%20C49%2010%2052%204%2063%205%20L63%2028%20L1%2028Z'%20fill='black'/%3E%3C/svg%3E") !important;
  mask-repeat:no-repeat !important;
  mask-position:center !important;
  mask-size:100% 100% !important;
  filter:drop-shadow(0 0 8px rgba(var(--v24-kpi,99,102,241),.48)) !important;
}

/* F. MY LEADS — stronger avatar rings and active tab glow. */
.tcrm-premium-dashboard .tcrm-luxury-leads-card .w-9.h-9.rounded-full {
  box-shadow:0 0 0 2px rgba(255,255,255,.96),0 0 0 4px rgba(99,102,241,.10),0 8px 18px -10px rgba(79,70,229,.52) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-leads-card .w-9.h-9.rounded-full {
  box-shadow:0 0 0 2px rgba(14,26,48,.96),0 0 0 4px rgba(129,116,255,.20),0 0 22px -8px rgba(113,93,255,.72) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-lead-tab[data-state="active"] {
  box-shadow:0 0 0 1px rgba(99,102,241,.20),0 8px 22px -13px rgba(99,102,241,.55),inset 0 1px 0 rgba(255,255,255,.86) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-lead-tab[data-state="active"] {
  box-shadow:0 0 0 1px rgba(132,122,255,.28),0 0 22px -8px rgba(106,84,255,.72),inset 0 1px 0 rgba(255,255,255,.08) !important;
}

/* G. SLA + ACTIVITIES — stronger original-concept luminous hierarchy. */
.tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border-color:rgba(244,63,94,.32) !important;
  box-shadow:0 0 0 1px rgba(244,63,94,.06),0 0 26px -18px rgba(244,63,94,.62),0 20px 48px -38px rgba(120,20,45,.32),inset 0 1px 0 rgba(255,255,255,.86) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border-color:rgba(251,87,117,.44) !important;
  box-shadow:0 0 0 1px rgba(251,87,117,.10),0 0 34px -16px rgba(244,63,94,.68),0 24px 58px -40px rgba(0,0,0,.96),inset 0 1px 0 rgba(255,255,255,.05) !important;
}
.tcrm-premium-dashboard .luxury-activity-icon {
  width:28px !important;
  height:28px !important;
  flex:0 0 28px !important;
  border-radius:50% !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  color:#5f57ee !important;
  background:radial-gradient(circle at 35% 25%,#fff,rgba(99,102,241,.10)) !important;
  border:1px solid rgba(99,102,241,.22) !important;
  box-shadow:0 0 0 4px rgba(99,102,241,.04),0 7px 18px -10px rgba(79,70,229,.52),inset 0 1px 0 #fff !important;
}
.dark .tcrm-premium-dashboard .luxury-activity-icon {
  color:#b8b0ff !important;
  background:radial-gradient(circle at 35% 25%,rgba(128,139,255,.24),rgba(52,48,120,.16)) !important;
  border-color:rgba(133,124,255,.32) !important;
  box-shadow:0 0 0 4px rgba(105,84,255,.05),0 0 20px -8px rgba(109,88,255,.72),inset 0 1px 0 rgba(255,255,255,.08) !important;
}

/* H. Right rail refinement — tighter vertical rhythm and glass depth. */
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 {
  gap:14px !important;
}
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 [data-slot="card-header"] {
  border-bottom:1px solid rgba(99,102,241,.085);
}
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 [data-slot="card-header"] {
  border-bottom-color:rgba(133,124,255,.13);
}

@media (max-width:1023px) {
  .tcrm-premium-dashboard .tcrm-luxury-canvas {
    min-height:520px !important;
    border-radius:20px !important;
    padding:40px 28px 30px !important;
  }
  .tcrm-premium-dashboard .tcrm-luxury-canvas-values {
    grid-template-columns:1fr !important;
    gap:6px !important;
  }
  .tcrm-premium-dashboard .tcrm-canvas-value {
    padding:10px 0 !important;
  }
  .tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
    border-left:0 !important;
    border-top:1px solid rgba(99,102,241,.12) !important;
  }
}
@media (prefers-reduced-motion:reduce) {
  .tcrm-premium-dashboard .tcrm-luxury-canvas::after {animation:none !important}
}
'''

css_after = css_before + V25

# Preserve all real reminder behavior before writing.
for critical in [
    'trpc.leadReminders.getToday.useQuery()',
    'trpc.leadReminders.getCalendar.useQuery({ month, year })',
    'markDoneMutation.mutate({ id: reminder.id })',
    'utils.leadReminders.getToday.invalidate()',
    'utils.leadReminders.getCalendar.invalidate()',
    'href={`/leads/${reminder.leadId}`}',
]:
    if critical not in rem:
        raise SystemExit("ERROR=REAL_REMINDER_FUNCTIONALITY_GUARD_FAILED:" + critical)

REMINDERS.write_text(rem, encoding="utf-8")
CSS.write_text(css_after, encoding="utf-8")

agent_hash_after = hashlib.sha256(AGENT.read_bytes()).hexdigest()
if agent_hash_before != agent_hash_after:
    raise SystemExit("ERROR=AGENT_DASHBOARD_TSX_CHANGED")

final_rem = REMINDERS.read_text(encoding="utf-8")
final_css = CSS.read_text(encoding="utf-8")

checks = {
    "V25_MARKER": MARKER in final_css,
    "TODAY_EMPTY": "tcrm-today-empty-icon" in final_rem and "You're all caught up!" in final_rem,
    "CALENDAR_CLASS": "tcrm-reminder-calendar-card" in final_rem and "tcrm-calendar-day" in final_rem,
    "WAVE_ART": "v25-wave-drift" in final_css,
    "LOWER_VALUES": "THREE VALUE ITEMS" in final_css,
    "SMOOTH_SPARK": "KPI SPARKLINES" in final_css,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit("ERROR=POST_WRITE_VERIFY_FAILED:" + "|".join(failed))

print("PATCH=YES")
print("V25_ORIGINAL_CONCEPT_STRUCTURAL_FIDELITY=YES")
print("AGENT_DASHBOARD_TSX_PROTECTED=YES")
print("REAL_REMINDER_LOGIC_PRESERVED=YES")
print("TODAY_TASKS_EMPTY_STATE_UPGRADED=YES")
print("CALENDAR_STRUCTURE_HOOKS_ADDED=YES")
print("LOWER_CANVAS_STRETCH_FIX=YES")
print("LOWER_VALUE_CARDS_REMOVED_VISUALLY=YES")
print("MOUNTAIN_WAVE_ART_UPGRADED=YES")
print("KPI_SMOOTH_SPARKLINE_UPGRADED=YES")
print("SLA_ACTIVITY_POLISH=YES")
print("BACKUP_CREATED=YES")
print("BACKUP_DIR=" + str(backup_dir))
print("FILES_CHANGED=client/src/components/ReminderCalendar.tsx,client/src/dashboard-premium-luminous-v16.css")
