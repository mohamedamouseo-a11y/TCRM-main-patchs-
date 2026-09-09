#!/usr/bin/env python3
from pathlib import Path
import shutil, datetime, hashlib

ROOT = Path.cwd()
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"
PROTECTED = [
    ROOT / "client/src/pages/AgentDashboard.tsx",
    ROOT / "client/src/pages/TeamDashboard.tsx",
    ROOT / "client/src/pages/LeadsList.tsx",
    ROOT / "client/src/components/ReminderCalendar.tsx",
    ROOT / "client/src/components/DateRangePicker.tsx",
]
V27 = "/* TCRM Dashboard V27 Final Precision Polish */"
MARKER = "/* TCRM Dashboard V28 Final Micro Polish */"

if not CSS.exists():
    raise SystemExit("ERROR=CSS_TARGET_MISSING")
for p in PROTECTED:
    if not p.exists():
        raise SystemExit(f"ERROR=PROTECTED_FILE_MISSING:{p}")

css = CSS.read_text(encoding="utf-8")
if V27 not in css:
    raise SystemExit("ERROR=V27_BASELINE_NOT_FOUND")
if MARKER in css:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v28-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / CSS.name)

V28 = r'''

/* TCRM Dashboard V28 Final Micro Polish */
/* CSS-only final micro-fidelity pass. No business logic, data, routes, APIs, permissions or component behavior changed. */

/* 1) LOWER CANVAS — remove excess empty vertical feeling while preserving continuous atmosphere */
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .lg\:col-span-2 > .tcrm-luxury-canvas {
  min-height: 540px !important;
  padding-top: 34px !important;
  padding-bottom: 28px !important;
  justify-content: flex-end !important;
  background-position: center !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-content {
  transform: translateY(-4px);
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  font-size: clamp(2.45rem, 3.05vw, 3.35rem) !important;
  line-height: .99 !important;
  margin-top: 18px !important;
  margin-bottom: 14px !important;
}

/* 2) BOTTOM VALUE STRIP — fully integrated, no visible card/bar */
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-canvas-values,
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-luxury-canvas-values {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  overflow: visible !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-canvas-values::before,
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-canvas-values::after,
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-luxury-canvas-values::before,
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-luxury-canvas-values::after {
  content: none !important;
  display: none !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas .tcrm-canvas-value {
  background: transparent !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon {
  width: 48px !important;
  height: 48px !important;
  min-width: 48px !important;
  border-radius: 999px !important;
  box-shadow: 0 0 0 5px rgba(99,102,241,.055), 0 0 26px -6px rgba(99,102,241,.66), inset 0 1px 0 rgba(255,255,255,.96) !important;
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value-icon {
  box-shadow: 0 0 0 5px rgba(99,102,241,.08), 0 0 30px -5px rgba(116,93,255,.90), inset 0 1px 0 rgba(255,255,255,.13) !important;
}
.tcrm-premium-dashboard .tcrm-canvas-value-icon svg {
  width: 21px !important;
  height: 21px !important;
  stroke-width: 2.25 !important;
}

/* 3) SLA ALERTS — stronger information hierarchy without changing content */
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-title"] {
  font-size: 13px !important;
  font-weight: 850 !important;
  letter-spacing: -.005em !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] a > div {
  padding: 13px 16px !important;
  min-height: 56px !important;
  position: relative;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] a > div::before {
  content: "";
  position: absolute;
  left: 8px;
  top: 50%;
  width: 4px;
  height: 24px;
  border-radius: 99px;
  transform: translateY(-50%);
  background: linear-gradient(180deg, rgba(244,63,94,.95), rgba(244,63,94,.20));
  box-shadow: 0 0 12px rgba(244,63,94,.34);
}
[dir="rtl"] .tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] a > div::before {
  left: auto;
  right: 8px;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card p.text-sm {
  font-size: 12px !important;
  line-height: 1.25 !important;
  font-weight: 800 !important;
  letter-spacing: -.01em !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card span.text-xs.text-destructive {
  font-size: 10px !important;
  line-height: 1.3 !important;
  font-weight: 750 !important;
}

/* 4) MY ACTIVITIES — true circular luminous holders + clearer rows */
.tcrm-premium-dashboard .luxury-activity-icon,
.tcrm-premium-dashboard .luxury-activity-icon * {
  border-radius: 999px !important;
}
.tcrm-premium-dashboard .luxury-activity-icon {
  width: 34px !important;
  height: 34px !important;
  min-width: 34px !important;
  aspect-ratio: 1 / 1 !important;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.tcrm-premium-dashboard [data-slot="card-content"] .text-base:has(.luxury-activity-icon) {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.tcrm-premium-dashboard .luxury-activity-icon svg {
  width: 15px !important;
  height: 15px !important;
  stroke-width: 2.35 !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-content"] > .divide-y > div {
  min-height: 54px !important;
  padding: 11px 15px !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child p.text-xs.font-medium {
  font-size: 11px !important;
  font-weight: 800 !important;
}
.tcrm-premium-dashboard > .grid.grid-cols-1.lg\:grid-cols-3 > .space-y-4 > [data-slot="card"]:last-child p.text-xs.text-muted-foreground {
  font-size: 9.5px !important;
  opacity: .88 !important;
}

/* 5) REMINDER CALENDAR — weekday contrast + selected-day finishing */
.tcrm-premium-dashboard .tcrm-calendar-weekdays > div {
  font-size: 10px !important;
  font-weight: 750 !important;
  color: #65738a !important;
  opacity: 1 !important;
}
.dark .tcrm-premium-dashboard .tcrm-calendar-weekdays > div {
  color: #9ca9bc !important;
}
.tcrm-premium-dashboard .tcrm-calendar-day {
  font-size: 11px !important;
  transition: transform .18s ease, background .18s ease, box-shadow .18s ease !important;
}
.tcrm-premium-dashboard .tcrm-calendar-day:hover {
  transform: translateY(-1px);
}
.tcrm-premium-dashboard .tcrm-calendar-day[class*="bg-indigo-600"] {
  transform: scale(1.04);
}

/* 6) DATE PICKER — final glass/detail pass using stable hooks only */
#date {
  letter-spacing: -.01em !important;
  font-weight: 750 !important;
}
.tcrm-date-range-popover {
  border-radius: 22px !important;
  backdrop-filter: blur(28px) saturate(150%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(150%) !important;
}
.tcrm-date-range-presets {
  gap: 2px !important;
}
.tcrm-date-range-preset {
  min-height: 35px !important;
  border: 1px solid transparent !important;
}
.tcrm-date-range-preset[class*="bg-blue-600"] {
  transform: translateX(1px);
}
.tcrm-date-range-calendar button {
  min-width: 35px !important;
  min-height: 35px !important;
  border-radius: 10px !important;
}
.tcrm-date-range-start,
.tcrm-date-range-end,
.tcrm-date-range-start button,
.tcrm-date-range-end button {
  box-shadow: 0 0 0 1px rgba(255,255,255,.38), 0 0 0 4px rgba(99,102,241,.11), 0 11px 24px -10px rgba(79,70,229,.82), 0 0 22px -8px rgba(99,102,241,.48) !important;
}
.dark .tcrm-date-range-start,
.dark .tcrm-date-range-end,
.dark .tcrm-date-range-start button,
.dark .tcrm-date-range-end button {
  box-shadow: 0 0 0 1px rgba(255,255,255,.20), 0 0 0 4px rgba(99,102,241,.13), 0 12px 26px -10px rgba(0,0,0,.85), 0 0 28px -7px rgba(111,91,255,.68) !important;
}

/* 7) KPI — one last dark readability nudge */
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p {
  color: #bac6d8 !important;
  opacity: 1 !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p:last-of-type {
  color: #e1e7f0 !important;
}
'''

CSS.write_text(css.rstrip() + V28 + "\n", encoding="utf-8")

for p in PROTECTED:
    now = hashlib.sha256(p.read_bytes()).hexdigest()
    if now != hashes[str(p)]:
        raise SystemExit(f"ERROR=PROTECTED_FILE_CHANGED:{p}")

print("PATCH=YES")
print("V28_FINAL_MICRO_POLISH=YES")
print("CSS_ONLY=YES")
print("BACKUP_CREATED=YES")
print("FILES_CHANGED=client/src/dashboard-premium-luminous-v16.css")
print("ERROR=NONE")
