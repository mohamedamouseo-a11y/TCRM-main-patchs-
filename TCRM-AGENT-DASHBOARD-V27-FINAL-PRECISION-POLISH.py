#!/usr/bin/env python3
from pathlib import Path
import shutil
import datetime
import hashlib

ROOT = Path.cwd()
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"
AGENT = ROOT / "client/src/pages/AgentDashboard.tsx"
TEAM = ROOT / "client/src/pages/TeamDashboard.tsx"
LEADS = ROOT / "client/src/pages/LeadsList.tsx"
REMINDERS = ROOT / "client/src/components/ReminderCalendar.tsx"
DATE_PICKER = ROOT / "client/src/components/DateRangePicker.tsx"

V26_MARKER = "/* TCRM Dashboard V26 Premium Control Polish */"
MARKER = "/* TCRM Dashboard V27 Final Precision Polish */"

for p in (CSS, AGENT, TEAM, LEADS, REMINDERS, DATE_PICKER):
    if not p.exists():
        raise SystemExit(f"ERROR=TARGET_MISSING:{p}")

css = CSS.read_text(encoding="utf-8")
if V26_MARKER not in css:
    raise SystemExit("ERROR=V26_BASELINE_NOT_FOUND")

if MARKER in css:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

# Read-only structural guards: V27 is CSS-only.
agent = AGENT.read_text(encoding="utf-8")
required_agent = [
    "tcrm-premium-dashboard",
    "luxury-kpi-card",
    "tcrm-luxury-leads-card",
    "tcrm-luxury-reminders-card",
    "tcrm-luxury-sla-card",
    "tcrm-luxury-canvas",
    "tcrm-canvas-values",
]
missing_agent = [x for x in required_agent if x not in agent]
if missing_agent:
    raise SystemExit("ERROR=AGENT_STRUCTURE_GUARD_MISSING:" + "|".join(missing_agent))

reminder_src = REMINDERS.read_text(encoding="utf-8")
for hook in ("tcrm-today-tasks-card", "tcrm-reminder-calendar-card", "tcrm-calendar-day"):
    if hook not in reminder_src:
        raise SystemExit(f"ERROR=V25_REMINDER_HOOK_MISSING:{hook}")

date_src = DATE_PICKER.read_text(encoding="utf-8")
for hook in ("tcrm-date-range-trigger", "tcrm-date-range-popover", "tcrm-date-range-calendar"):
    if hook not in date_src:
        raise SystemExit(f"ERROR=DATE_PICKER_HOOK_MISSING:{hook}")

protected_before = {
    str(AGENT): hashlib.sha256(AGENT.read_bytes()).hexdigest(),
    str(TEAM): hashlib.sha256(TEAM.read_bytes()).hexdigest(),
    str(LEADS): hashlib.sha256(LEADS.read_bytes()).hexdigest(),
    str(REMINDERS): hashlib.sha256(REMINDERS.read_bytes()).hexdigest(),
    str(DATE_PICKER): hashlib.sha256(DATE_PICKER.read_bytes()).hexdigest(),
}

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v27-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / CSS.name)

V27 = r'''

/* TCRM Dashboard V27 Final Precision Polish */
/* CSS-only precision pass. No data, API, routes, permissions, actions, or component logic changed. */

/* =========================================================
   1) TRUE TWO-COLUMN STRETCH — remove the gray dead zone
   V25 targeted an obsolete nested .grid shape. This selector
   targets the actual direct dashboard grid in AgentDashboard.
   ========================================================= */
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 {
  align-items: stretch !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .lg\:col-span-2 {
  display: flex !important;
  flex-direction: column !important;
  min-height: 100% !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .lg\:col-span-2 > .tcrm-luxury-canvas {
  flex: 1 1 auto !important;
  min-height: 620px !important;
  height: auto !important;
  margin-bottom: 0 !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 {
  align-self: stretch !important;
}
.tcrm-premium-dashboard {
  padding-bottom: 28px !important;
  background-attachment: local !important;
}

/* =========================================================
   2) LOWER EDITORIAL SCENE — correct scale + premium values
   ========================================================= */
.tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  font-size: clamp(2.65rem, 3.35vw, 3.65rem) !important;
  line-height: .98 !important;
  letter-spacing: -.048em !important;
  max-width: 620px !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-sub {
  margin-top: 16px !important;
  margin-bottom: 30px !important;
  font-size: .9rem !important;
  font-weight: 550 !important;
}
.tcrm-premium-dashboard .tcrm-canvas-values,
.tcrm-premium-dashboard .tcrm-luxury-canvas-values {
  width: min(100%, 760px) !important;
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value {
  min-height: 68px !important;
  padding: 6px 22px !important;
  gap: 13px !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
  border-inline-start: 1px solid rgba(99,102,241,.18) !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
  border-inline-start-color: rgba(167,139,250,.20) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon {
  width: 44px !important;
  height: 44px !important;
  min-width: 44px !important;
  border-radius: 50% !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: #5b5cf2 !important;
  border: 1px solid rgba(99,102,241,.26) !important;
  background: radial-gradient(circle at 34% 24%, #fff 0%, rgba(238,242,255,.92) 42%, rgba(99,102,241,.10) 100%) !important;
  box-shadow: 0 0 0 5px rgba(99,102,241,.055), 0 0 24px -7px rgba(99,102,241,.58), inset 0 1px 0 rgba(255,255,255,.95) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon svg {
  width: 20px !important;
  height: 20px !important;
  stroke-width: 2.15 !important;
  filter: drop-shadow(0 0 6px rgba(99,102,241,.30));
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value-icon {
  color: #c0b8ff !important;
  border-color: rgba(139,130,255,.42) !important;
  background: radial-gradient(circle at 34% 24%, rgba(139,130,255,.27), rgba(55,48,130,.28) 48%, rgba(16,25,52,.72) 100%) !important;
  box-shadow: 0 0 0 5px rgba(99,102,241,.075), 0 0 28px -6px rgba(112,91,255,.80), inset 0 1px 0 rgba(255,255,255,.12) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-title {
  font-size: .78rem !important;
  font-weight: 800 !important;
  letter-spacing: -.01em !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-subtitle {
  font-size: .68rem !important;
  opacity: .82 !important;
}

/* =========================================================
   3) CLOSED DATE TRIGGER — force readable premium glass.
   Unscoped #date selector handles PageBanner/component styles
   that were visually overriding the scoped V26 rule.
   ========================================================= */
#date.tcrm-date-range-trigger,
button#date.tcrm-date-range-trigger {
  min-width: 270px !important;
  height: 42px !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  border: 1px solid rgba(255,255,255,.34) !important;
  background: linear-gradient(135deg, rgba(37,28,92,.78), rgba(76,65,190,.58)) !important;
  background-color: rgba(49,46,129,.68) !important;
  backdrop-filter: blur(18px) saturate(155%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 10px 26px -15px rgba(20,15,75,.75), 0 0 22px -15px rgba(196,181,253,.72) !important;
  text-shadow: 0 1px 7px rgba(8,10,31,.42) !important;
}
#date.tcrm-date-range-trigger:hover,
button#date.tcrm-date-range-trigger:hover {
  color:#fff !important;
  -webkit-text-fill-color:#fff !important;
  border-color:rgba(255,255,255,.52) !important;
  background:linear-gradient(135deg,rgba(48,35,116,.88),rgba(91,73,218,.70)) !important;
}
#date.tcrm-date-range-trigger span,
#date.tcrm-date-range-trigger svg {
  color:#fff !important;
  -webkit-text-fill-color:#fff !important;
  opacity:1 !important;
  visibility:visible !important;
}
#date.tcrm-date-range-trigger > span.flex-1 {
  font-weight:700 !important;
  letter-spacing:-.01em !important;
}

/* =========================================================
   4) DATE RANGE POPOVER — higher-end executive calendar
   ========================================================= */
.tcrm-date-range-popover {
  border-radius: 24px !important;
  border: 1px solid rgba(106,101,195,.24) !important;
  background: rgba(252,253,255,.985) !important;
  box-shadow: 0 34px 95px -28px rgba(17,24,39,.48), 0 18px 42px -22px rgba(79,70,229,.34), inset 0 1px 0 rgba(255,255,255,.96) !important;
}
.tcrm-date-range-shell {
  border-radius: inherit !important;
  overflow: hidden !important;
}
.tcrm-date-range-presets {
  min-width: 170px !important;
  padding: 15px 12px !important;
  background: linear-gradient(180deg, rgba(247,247,255,.99), rgba(240,243,255,.92)) !important;
  border-color: rgba(99,102,241,.12) !important;
}
.tcrm-date-range-presets > div:first-child {
  color: #667085 !important;
  font-size: 10px !important;
  letter-spacing: .12em !important;
}
.tcrm-date-range-preset {
  min-height: 36px !important;
  padding-inline: 11px !important;
  border-radius: 10px !important;
  color: #354158 !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}
.tcrm-date-range-preset:hover {
  background: rgba(99,102,241,.085) !important;
  color: #4338ca !important;
}
.tcrm-date-range-preset[class*="bg-blue-600"] {
  background: linear-gradient(135deg, #5a60f1 0%, #7248e8 100%) !important;
  color: #fff !important;
  box-shadow: 0 10px 22px -11px rgba(79,70,229,.72), inset 0 1px 0 rgba(255,255,255,.28) !important;
}
.tcrm-date-range-calendar {
  padding: 16px 18px 14px !important;
  background: radial-gradient(circle at 50% 0%, rgba(99,102,241,.055), transparent 20rem), #fff !important;
}
.tcrm-date-range-calendar [data-slot="calendar"] {
  --cell-size: 38px;
}
.tcrm-date-range-calendar button {
  min-width: 34px !important;
  min-height: 34px !important;
  font-size: 12px !important;
  font-weight: 680 !important;
  border-radius: 9px !important;
}
.tcrm-date-range-start,
.tcrm-date-range-end,
.tcrm-date-range-start button,
.tcrm-date-range-end button {
  color: #fff !important;
  background: linear-gradient(135deg,#5963f4,#6f47e8) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,.36), 0 0 0 3px rgba(99,102,241,.12), 0 10px 22px -10px rgba(79,70,229,.78) !important;
}
.tcrm-date-range-middle,
.tcrm-date-range-middle button {
  background: linear-gradient(180deg, rgba(99,102,241,.13), rgba(99,102,241,.075)) !important;
  color: #4338ca !important;
}
.tcrm-date-range-today {
  box-shadow: inset 0 0 0 1.5px rgba(99,102,241,.52), 0 0 14px -8px rgba(99,102,241,.72) !important;
}
.tcrm-date-range-footer {
  min-height: 58px !important;
  padding: 12px 16px !important;
  background: linear-gradient(180deg, rgba(248,250,255,.98), rgba(244,246,255,.98)) !important;
  border-color: rgba(99,102,241,.12) !important;
}
.tcrm-date-range-apply {
  min-width: 72px !important;
  border-radius: 10px !important;
  background: linear-gradient(135deg,#5963f4,#6f47e8) !important;
  box-shadow: 0 9px 18px -10px rgba(79,70,229,.70), inset 0 1px 0 rgba(255,255,255,.24) !important;
}
.tcrm-date-range-clear {
  border-radius: 10px !important;
}
.dark .tcrm-date-range-popover {
  border-color: rgba(125,118,255,.30) !important;
  background: rgba(10,18,34,.985) !important;
  box-shadow: 0 36px 100px -26px rgba(0,0,0,.96), 0 0 44px -24px rgba(95,83,255,.58), inset 0 1px 0 rgba(255,255,255,.055) !important;
}
.dark .tcrm-date-range-shell {
  background: linear-gradient(145deg,#0d1729,#0a1324) !important;
}
.dark .tcrm-date-range-presets {
  background: linear-gradient(180deg,rgba(18,29,50,.98),rgba(12,22,40,.98)) !important;
  border-color: rgba(129,140,248,.16) !important;
}
.dark .tcrm-date-range-presets > div:first-child { color:#7f8ba3 !important; }
.dark .tcrm-date-range-preset { color:#c8d1df !important; }
.dark .tcrm-date-range-preset:hover {
  color:#f4f3ff !important;
  background:rgba(99,102,241,.15) !important;
}
.dark .tcrm-date-range-calendar {
  background: radial-gradient(circle at 50% 0%,rgba(99,102,241,.10),transparent 20rem), #0b1528 !important;
}
.dark .tcrm-date-range-calendar button { color:#dce4f0 !important; }
.dark .tcrm-date-range-middle,
.dark .tcrm-date-range-middle button {
  background:rgba(86,75,210,.24) !important;
  color:#e2deff !important;
}
.dark .tcrm-date-range-footer {
  color:#bdc7d8 !important;
  background:linear-gradient(180deg,rgba(14,25,44,.99),rgba(10,20,37,.99)) !important;
  border-color:rgba(129,140,248,.16) !important;
}

/* =========================================================
   5) REMINDERS CALENDAR — final micro fidelity
   ========================================================= */
.tcrm-premium-dashboard .tcrm-reminder-calendar-card [data-slot="card-header"] {
  padding: 15px 17px 12px !important;
  border-bottom: 1px solid rgba(99,102,241,.10) !important;
}
.tcrm-premium-dashboard .tcrm-reminder-calendar-card [data-slot="card-title"] {
  font-weight: 800 !important;
  letter-spacing: -.015em !important;
}
.tcrm-premium-dashboard .tcrm-reminder-calendar-card [data-slot="card-title"] > svg {
  width: 18px !important;
  height: 18px !important;
  color: #6558f5 !important;
  filter: drop-shadow(0 0 7px rgba(99,102,241,.38)) !important;
}
.tcrm-premium-dashboard .tcrm-calendar-weekdays {
  margin-top: 3px !important;
  margin-bottom: 5px !important;
}
.tcrm-premium-dashboard .tcrm-calendar-weekdays > div {
  color: #7a879c !important;
  font-size: 9px !important;
  letter-spacing: .045em !important;
  text-transform: uppercase;
}
.dark .tcrm-premium-dashboard .tcrm-calendar-weekdays > div { color:#8794aa !important; }
.tcrm-premium-dashboard .tcrm-calendar-day {
  border-radius: 11px !important;
  font-weight: 700 !important;
}
.tcrm-premium-dashboard .tcrm-calendar-day[class*="bg-indigo-600"] {
  background: linear-gradient(145deg,#6548f5,#6e63ff) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,.44), 0 0 0 4px rgba(99,102,241,.10), 0 10px 22px -8px rgba(79,70,229,.78), 0 0 24px -7px rgba(112,89,255,.78) !important;
}

/* =========================================================
   6) SLA ALERTS — stronger hierarchy, cleaner typography
   ========================================================= */
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > .tcrm-luxury-sla-card {
  border: 1px solid rgba(244,63,94,.34) !important;
  background: linear-gradient(160deg,rgba(255,255,255,.99),rgba(255,248,250,.97)) !important;
  box-shadow: 0 22px 54px -36px rgba(190,24,93,.34), 0 0 28px -20px rgba(244,63,94,.38), inset 0 1px 0 rgba(255,255,255,.94) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-header"] {
  min-height: 54px !important;
  padding: 15px 17px 11px !important;
  border-bottom: 1px solid rgba(244,63,94,.13) !important;
  background: linear-gradient(90deg,rgba(255,241,244,.82),rgba(255,255,255,0)) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-title"] {
  font-size: 12px !important;
  font-weight: 850 !important;
  letter-spacing: .01em !important;
  color: #d4284d !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-title"] svg {
  width: 17px !important;
  height: 17px !important;
  stroke-width: 2.2 !important;
  filter: drop-shadow(0 0 7px rgba(244,63,94,.42)) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] a > div {
  padding: 12px 16px !important;
  border-bottom: 1px solid rgba(244,63,94,.075) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] a:last-child > div { border-bottom:0 !important; }
.tcrm-premium-dashboard .tcrm-luxury-sla-card p.text-sm {
  color: #2c3445 !important;
  font-size: 11px !important;
  font-weight: 780 !important;
  letter-spacing: -.005em !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card span.text-xs.text-destructive {
  color: #e23c5d !important;
  font-size: 9.5px !important;
  font-weight: 700 !important;
}
.dark .tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > .tcrm-luxury-sla-card {
  border-color: rgba(244,63,94,.42) !important;
  background: linear-gradient(160deg,rgba(25,31,53,.99),rgba(17,25,45,.99)) !important;
  box-shadow: 0 28px 60px -40px rgba(0,0,0,.96), 0 0 34px -18px rgba(244,63,94,.28), inset 0 1px 0 rgba(255,255,255,.055) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-header"] {
  background: linear-gradient(90deg,rgba(102,28,52,.24),rgba(20,28,49,0)) !important;
  border-bottom-color: rgba(244,63,94,.18) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card p.text-sm { color:#f2f5fb !important; }
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card span.text-xs.text-destructive { color:#ff738d !important; }

/* =========================================================
   7) MY ACTIVITIES — circular luminous holders + hierarchy
   ========================================================= */
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child {
  border-color: rgba(99,102,241,.20) !important;
  box-shadow: 0 22px 54px -36px rgba(79,70,229,.28), inset 0 1px 0 rgba(255,255,255,.92) !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-header"] {
  min-height: 54px !important;
  padding: 15px 17px 11px !important;
  border-bottom: 1px solid rgba(99,102,241,.11) !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-title"] {
  font-size: 12px !important;
  font-weight: 850 !important;
  letter-spacing: -.01em !important;
}
.tcrm-premium-dashboard .luxury-activity-icon {
  width: 31px !important;
  height: 31px !important;
  min-width: 31px !important;
  border-radius: 50% !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: #5c58e8 !important;
  border: 1px solid rgba(99,102,241,.24) !important;
  background: radial-gradient(circle at 34% 24%,#fff,rgba(238,242,255,.90) 52%,rgba(99,102,241,.10)) !important;
  box-shadow: 0 0 0 4px rgba(99,102,241,.045), 0 0 18px -7px rgba(99,102,241,.54), inset 0 1px 0 rgba(255,255,255,.94) !important;
}
.tcrm-premium-dashboard .luxury-activity-icon svg {
  width: 14px !important;
  height: 14px !important;
  stroke-width: 2.25 !important;
  color: currentColor !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-content"] > .divide-y > div {
  min-height: 51px !important;
  padding: 10px 15px !important;
  border-bottom-color: rgba(99,102,241,.075) !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child p.text-xs.font-medium {
  color: #313b4e !important;
  font-weight: 780 !important;
}
.dark .tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child {
  border-color: rgba(111,117,245,.27) !important;
  background: linear-gradient(160deg,rgba(18,31,54,.99),rgba(10,22,42,.99)) !important;
  box-shadow: 0 28px 60px -40px rgba(0,0,0,.95), 0 0 30px -22px rgba(99,102,241,.36), inset 0 1px 0 rgba(255,255,255,.05) !important;
}
.dark .tcrm-premium-dashboard .luxury-activity-icon {
  color:#c6c0ff !important;
  border-color:rgba(129,140,248,.36) !important;
  background:radial-gradient(circle at 34% 24%,rgba(129,140,248,.27),rgba(58,55,130,.24) 50%,rgba(12,23,45,.78)) !important;
  box-shadow:0 0 0 4px rgba(99,102,241,.06),0 0 20px -6px rgba(103,90,255,.74),inset 0 1px 0 rgba(255,255,255,.09) !important;
}
.dark .tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child p.text-xs.font-medium { color:#eef2f8 !important; }

/* =========================================================
   8) FINAL KPI MICRO-CONTRAST
   ========================================================= */
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p:last-of-type {
  color: #e2e8f2 !important;
  opacity: .94 !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p:not(:last-of-type) {
  color: #bdc8d9 !important;
  opacity: .90 !important;
}

@media (max-width: 1023px) {
  .tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .lg\:col-span-2 > .tcrm-luxury-canvas {
    min-height: 520px !important;
  }
  .tcrm-premium-dashboard .tcrm-canvas-values,
  .tcrm-premium-dashboard .tcrm-luxury-canvas-values {
    grid-template-columns: 1fr !important;
  }
  .tcrm-premium-dashboard .tcrm-canvas-value + .tcrm-canvas-value {
    border-inline-start: 0 !important;
    border-top: 1px solid rgba(99,102,241,.16) !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tcrm-date-range-calendar button,
  #date.tcrm-date-range-trigger {
    transition: none !important;
  }
}
'''

CSS.write_text(css.rstrip() + V27 + "\n", encoding="utf-8")

# Ensure this patch itself did not alter protected source files.
for path, old_hash in protected_before.items():
    p = Path(path)
    new_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    if new_hash != old_hash:
        raise SystemExit(f"ERROR=PROTECTED_FILE_CHANGED:{path}")

final_css = CSS.read_text(encoding="utf-8")
required_css = [
    MARKER,
    "TRUE TWO-COLUMN STRETCH",
    "#date.tcrm-date-range-trigger",
    "DATE RANGE POPOVER",
    "SLA ALERTS",
    "MY ACTIVITIES",
    "tcrm-canvas-value-icon",
]
missing_css = [x for x in required_css if x not in final_css]
if missing_css:
    raise SystemExit("ERROR=V27_VERIFY_MISSING:" + "|".join(missing_css))

print("PATCH=YES")
print("V27_FINAL_PRECISION_POLISH=YES")
print("CSS_ONLY=YES")
print(f"BACKUP_CREATED=YES:{backup_dir}")
print("DATE_TRIGGER_FORCE_FIX=YES")
print("DATE_PICKER_PRECISION_POLISH=YES")
print("SLA_HIERARCHY_POLISH=YES")
print("ACTIVITY_ICON_POLISH=YES")
print("LOWER_GRID_STRETCH_SELECTOR_FIXED=YES")
print("LOWER_VALUE_STRIP_REMOVED=YES")
print("HEADLINE_SCALE_REFINED=YES")
print("FILES_CHANGED=client/src/dashboard-premium-luminous-v16.css")
print("ERROR=NONE")
