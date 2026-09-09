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

V25_MARKER = "/* TCRM Dashboard Original Concept V25 Structural Fidelity */"
MARKER = "/* TCRM Dashboard V26 Premium Control Polish */"

for p in (CSS, AGENT, TEAM, LEADS):
    if not p.exists():
        raise SystemExit(f"ERROR=TARGET_MISSING:{p}")

css = CSS.read_text(encoding="utf-8")
if V25_MARKER not in css:
    raise SystemExit("ERROR=V25_BASELINE_NOT_FOUND")

if MARKER in css:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

protected_before = {
    str(AGENT): hashlib.sha256(AGENT.read_bytes()).hexdigest(),
    str(TEAM): hashlib.sha256(TEAM.read_bytes()).hexdigest(),
    str(LEADS): hashlib.sha256(LEADS.read_bytes()).hexdigest(),
}

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v26-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / CSS.name)

V26 = r'''

/* TCRM Dashboard V26 Premium Control Polish */
/* Visual-only polish: SLA, activities, quality badges, date-range picker, KPI icon/text readability. */

/* ---------------------------------------------------------
   1) KPI ICON LEGIBILITY + TYPOGRAPHY
   --------------------------------------------------------- */
.tcrm-premium-dashboard .luxury-kpi-icon {
  width: 48px !important;
  height: 48px !important;
  min-width: 48px !important;
  min-height: 48px !important;
  filter: saturate(1.16) contrast(1.08);
}
.tcrm-premium-dashboard .luxury-kpi-icon-core {
  inset: 7px !important;
  border-radius: 13px !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  background: color-mix(in srgb, currentColor 14%, transparent) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.78),
    0 0 16px -7px currentColor !important;
}
.tcrm-premium-dashboard .luxury-kpi-icon-core svg {
  width: 23px !important;
  height: 23px !important;
  stroke-width: 2.55 !important;
  opacity: 1 !important;
  filter: drop-shadow(0 0 5px currentColor) contrast(1.15) !important;
}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(1) .luxury-kpi-icon-core,
.tcrm-premium-dashboard > .stagger-children > a:nth-child(2) .luxury-kpi-icon-core {
  background: linear-gradient(145deg, rgba(99,102,241,.20), rgba(96,165,250,.10)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.86), 0 0 22px -6px rgba(99,102,241,.78) !important;
}
.dark .tcrm-premium-dashboard > .stagger-children > a:nth-child(1) .luxury-kpi-icon-core,
.dark .tcrm-premium-dashboard > .stagger-children > a:nth-child(2) .luxury-kpi-icon-core {
  background: linear-gradient(145deg, rgba(99,102,241,.34), rgba(59,130,246,.15)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.16), 0 0 26px -5px rgba(112,102,255,.95) !important;
}
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > .text-2xl {
  color:#101828 !important;
  font-weight:850 !important;
  letter-spacing:-.045em !important;
  text-shadow:0 1px 0 rgba(255,255,255,.8);
}
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p {
  color:#526078 !important;
  opacity:1 !important;
  font-weight:650 !important;
  line-height:1.28 !important;
}
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p:last-of-type {
  color:#3b465c !important;
  font-size:11px !important;
  font-weight:700 !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > .text-2xl {
  color:#f8fbff !important;
  text-shadow:0 0 12px rgba(167,139,250,.12) !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p {
  color:#aebbd0 !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] > p:last-of-type {
  color:#d2d9e6 !important;
}

/* ---------------------------------------------------------
   2) LEAD QUALITY BADGES — remove emoji/basic-chip feel
   --------------------------------------------------------- */
.tcrm-premium-dashboard .lead-quality-hot,
.tcrm-premium-dashboard .lead-quality-warm,
.tcrm-premium-dashboard .lead-quality-cold,
.tcrm-premium-dashboard .lead-quality-bad,
.tcrm-premium-dashboard .lead-quality-unknown {
  position:relative !important;
  min-width:72px !important;
  height:27px !important;
  padding:0 10px !important;
  gap:6px !important;
  border-radius:999px !important;
  font-size:10px !important;
  font-weight:800 !important;
  letter-spacing:.015em !important;
  backdrop-filter:blur(10px) saturate(135%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.78),0 6px 16px -11px rgba(15,23,42,.35) !important;
}
.tcrm-premium-dashboard .lead-quality-hot > span:first-child,
.tcrm-premium-dashboard .lead-quality-warm > span:first-child,
.tcrm-premium-dashboard .lead-quality-cold > span:first-child,
.tcrm-premium-dashboard .lead-quality-bad > span:first-child,
.tcrm-premium-dashboard .lead-quality-unknown > span:first-child {
  display:none !important;
}
.tcrm-premium-dashboard .lead-quality-hot::before,
.tcrm-premium-dashboard .lead-quality-warm::before,
.tcrm-premium-dashboard .lead-quality-cold::before,
.tcrm-premium-dashboard .lead-quality-bad::before,
.tcrm-premium-dashboard .lead-quality-unknown::before {
  content:"";
  width:7px;height:7px;flex:0 0 7px;border-radius:50%;
  background:currentColor;
  box-shadow:0 0 0 3px color-mix(in srgb,currentColor 12%,transparent),0 0 10px currentColor;
}
.tcrm-premium-dashboard .lead-quality-hot {color:#a84a00 !important;border-color:rgba(245,158,11,.34) !important;background:linear-gradient(135deg,rgba(255,247,219,.96),rgba(255,237,184,.82)) !important;}
.tcrm-premium-dashboard .lead-quality-bad {color:#c24157 !important;border-color:rgba(244,63,94,.28) !important;background:linear-gradient(135deg,rgba(255,241,244,.97),rgba(255,226,232,.86)) !important;}
.tcrm-premium-dashboard .lead-quality-unknown {color:#526079 !important;border-color:rgba(100,116,139,.24) !important;background:linear-gradient(135deg,rgba(248,250,252,.96),rgba(232,238,246,.84)) !important;}
.tcrm-premium-dashboard .lead-quality-warm {color:#b55d00 !important;border-color:rgba(249,115,22,.28) !important;background:linear-gradient(135deg,rgba(255,247,237,.97),rgba(255,230,201,.84)) !important;}
.tcrm-premium-dashboard .lead-quality-cold {color:#2563c8 !important;border-color:rgba(59,130,246,.28) !important;background:linear-gradient(135deg,rgba(239,246,255,.97),rgba(219,234,254,.84)) !important;}
.dark .tcrm-premium-dashboard .lead-quality-hot {color:#ffc04b !important;border-color:rgba(245,158,11,.38) !important;background:linear-gradient(135deg,rgba(120,72,8,.40),rgba(63,43,12,.58)) !important;}
.dark .tcrm-premium-dashboard .lead-quality-bad {color:#ff7b92 !important;border-color:rgba(244,63,94,.38) !important;background:linear-gradient(135deg,rgba(106,31,48,.42),rgba(52,23,35,.60)) !important;}
.dark .tcrm-premium-dashboard .lead-quality-unknown {color:#c1cada !important;border-color:rgba(148,163,184,.30) !important;background:linear-gradient(135deg,rgba(51,65,85,.55),rgba(30,41,59,.68)) !important;}
.dark .tcrm-premium-dashboard .lead-quality-warm {color:#ffad66 !important;border-color:rgba(249,115,22,.34) !important;background:linear-gradient(135deg,rgba(111,55,14,.42),rgba(59,33,18,.60)) !important;}
.dark .tcrm-premium-dashboard .lead-quality-cold {color:#7eb7ff !important;border-color:rgba(59,130,246,.36) !important;background:linear-gradient(135deg,rgba(30,64,120,.42),rgba(21,39,70,.62)) !important;}

/* ---------------------------------------------------------
   3) CLOSED DATE-RANGE TRIGGER — no more blank white capsule
   --------------------------------------------------------- */
.tcrm-premium-dashboard .tcrm-luxury-date-control .tcrm-date-range-trigger {
  min-width:268px !important;
  height:42px !important;
  padding:0 14px !important;
  color:#fff !important;
  border:1px solid rgba(255,255,255,.34) !important;
  background:linear-gradient(135deg,rgba(24,26,68,.34),rgba(79,70,229,.22)) !important;
  backdrop-filter:blur(18px) saturate(145%) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 10px 26px -16px rgba(18,11,69,.74),0 0 0 1px rgba(124,110,255,.08) !important;
  text-shadow:0 1px 8px rgba(17,24,39,.24);
}
.tcrm-premium-dashboard .tcrm-luxury-date-control .tcrm-date-range-trigger:hover {
  color:#fff !important;
  border-color:rgba(255,255,255,.48) !important;
  background:linear-gradient(135deg,rgba(31,32,86,.46),rgba(96,79,238,.32)) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.28),0 14px 32px -17px rgba(24,17,100,.80),0 0 22px -14px rgba(196,181,253,.70) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-date-control .tcrm-date-range-trigger span,
.tcrm-premium-dashboard .tcrm-luxury-date-control .tcrm-date-range-trigger svg {
  color:#fff !important;
  opacity:1 !important;
}

/* ---------------------------------------------------------
   4) DATE RANGE POPOVER — premium light/dark executive glass
   --------------------------------------------------------- */
.tcrm-date-range-popover {
  overflow:hidden !important;
  border-radius:22px !important;
  border:1px solid rgba(118,126,170,.20) !important;
  background:rgba(252,253,255,.985) !important;
  box-shadow:0 32px 90px -32px rgba(23,29,59,.48),0 14px 36px -22px rgba(79,70,229,.26),inset 0 1px 0 rgba(255,255,255,.96) !important;
  backdrop-filter:blur(24px) saturate(145%) !important;
}
.tcrm-date-range-shell {
  background:linear-gradient(145deg,rgba(255,255,255,.995),rgba(247,249,255,.98)) !important;
}
.tcrm-date-range-presets {
  min-width:164px !important;
  padding:14px 12px !important;
  border-color:rgba(99,102,241,.10) !important;
  background:linear-gradient(180deg,rgba(246,247,255,.98),rgba(240,244,255,.78)) !important;
}
.tcrm-date-range-preset {
  min-height:34px !important;
  border:1px solid transparent !important;
  border-radius:10px !important;
  font-size:12px !important;
  font-weight:650 !important;
  color:#3f4a62 !important;
}
.tcrm-date-range-preset:hover {
  background:rgba(99,102,241,.08) !important;
  color:#4338ca !important;
}
.tcrm-date-range-preset.bg-blue-600,
.tcrm-date-range-preset[class*="bg-blue-600"] {
  color:#fff !important;
  border-color:rgba(255,255,255,.18) !important;
  background:linear-gradient(135deg,#5b5cf2,#7047e8) !important;
  box-shadow:0 10px 20px -12px rgba(79,70,229,.70),inset 0 1px 0 rgba(255,255,255,.26) !important;
}
.tcrm-date-range-calendar {
  padding:14px 16px 12px !important;
  background:radial-gradient(circle at 50% 0,rgba(99,102,241,.045),transparent 18rem) !important;
}
.tcrm-date-range-calendar [role="grid"] {
  border-spacing:3px !important;
}
.tcrm-date-range-calendar button {
  border-radius:10px !important;
  font-weight:650 !important;
  color:#334155;
  transition:background .18s ease,color .18s ease,box-shadow .18s ease,transform .18s ease !important;
}
.tcrm-date-range-calendar button:hover {
  background:rgba(99,102,241,.09) !important;
  color:#4338ca !important;
  transform:translateY(-1px);
}
.tcrm-date-range-start button,
.tcrm-date-range-end button,
.tcrm-date-range-start,
.tcrm-date-range-end {
  color:#fff !important;
  background:linear-gradient(135deg,#5d5ff4,#7647e8) !important;
  box-shadow:0 0 0 1px rgba(255,255,255,.38),0 0 0 3px rgba(99,102,241,.12),0 8px 20px -10px rgba(79,70,229,.74) !important;
}
.tcrm-date-range-middle,
.tcrm-date-range-middle button {
  color:#4338ca !important;
  background:linear-gradient(180deg,rgba(99,102,241,.12),rgba(99,102,241,.07)) !important;
}
.tcrm-date-range-today {
  box-shadow:inset 0 0 0 1px rgba(99,102,241,.42),0 0 12px -8px rgba(99,102,241,.70) !important;
}
.tcrm-date-range-footer {
  min-height:54px !important;
  border-color:rgba(99,102,241,.10) !important;
  background:linear-gradient(180deg,rgba(248,250,255,.92),rgba(242,245,255,.98)) !important;
}
.tcrm-date-range-apply {
  min-width:72px !important;
  height:32px !important;
  border-radius:10px !important;
  background:linear-gradient(135deg,#5a5cf2,#7047e8) !important;
  box-shadow:0 9px 20px -11px rgba(79,70,229,.72),inset 0 1px 0 rgba(255,255,255,.22) !important;
}
.tcrm-date-range-clear {
  height:32px !important;
  border-radius:10px !important;
}
.dark .tcrm-date-range-popover {
  border-color:rgba(118,130,255,.26) !important;
  background:rgba(10,20,38,.985) !important;
  box-shadow:0 36px 96px -34px rgba(0,0,0,.92),0 0 42px -27px rgba(91,84,255,.60),inset 0 1px 0 rgba(255,255,255,.06) !important;
}
.dark .tcrm-date-range-shell {
  background:linear-gradient(145deg,rgba(14,27,49,.995),rgba(8,19,36,.995)) !important;
}
.dark .tcrm-date-range-presets {
  border-color:rgba(126,137,255,.13) !important;
  background:linear-gradient(180deg,rgba(18,31,56,.98),rgba(11,23,43,.98)) !important;
}
.dark .tcrm-date-range-preset {
  color:#c2ccdc !important;
}
.dark .tcrm-date-range-preset:hover {
  color:#f2f0ff !important;
  background:rgba(100,92,255,.14) !important;
}
.dark .tcrm-date-range-calendar {
  background:radial-gradient(circle at 50% 0,rgba(101,90,255,.10),transparent 20rem) !important;
}
.dark .tcrm-date-range-calendar button {
  color:#d5dcea !important;
}
.dark .tcrm-date-range-calendar button:hover {
  color:#fff !important;
  background:rgba(104,96,255,.16) !important;
}
.dark .tcrm-date-range-middle,
.dark .tcrm-date-range-middle button {
  color:#d9d6ff !important;
  background:linear-gradient(180deg,rgba(91,84,255,.20),rgba(73,67,200,.13)) !important;
}
.dark .tcrm-date-range-footer {
  border-color:rgba(126,137,255,.14) !important;
  background:linear-gradient(180deg,rgba(14,27,49,.96),rgba(10,21,39,.99)) !important;
}

/* ---------------------------------------------------------
   5) SLA ALERTS — executive danger surface, cleaner type
   --------------------------------------------------------- */
.tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border:1px solid rgba(244,63,94,.34) !important;
  background:linear-gradient(155deg,rgba(255,255,255,.985),rgba(255,247,249,.965)) !important;
  box-shadow:0 22px 52px -36px rgba(190,24,93,.42),0 0 28px -22px rgba(244,63,94,.48),inset 0 1px 0 rgba(255,255,255,.94) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-header"] {
  min-height:48px !important;
  padding:14px 16px 10px !important;
  border-bottom:1px solid rgba(244,63,94,.10);
  background:linear-gradient(90deg,rgba(255,241,244,.70),transparent 65%);
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-title"] {
  color:#d92f52 !important;
  font-size:12px !important;
  font-weight:850 !important;
  letter-spacing:.015em !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-title"] svg {
  width:16px !important;height:16px !important;
  stroke-width:2.4 !important;
  filter:drop-shadow(0 0 6px rgba(244,63,94,.42));
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] .divide-y > a > div {
  padding:11px 16px !important;
  border-color:rgba(244,63,94,.08) !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] .divide-y > a > div > p {
  color:#2d3444 !important;
  font-size:11px !important;
  font-weight:750 !important;
}
.tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] .text-destructive {
  color:#e54865 !important;
  font-size:9px !important;
  font-weight:650 !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border-color:rgba(255,82,116,.42) !important;
  background:linear-gradient(155deg,rgba(30,29,47,.985),rgba(18,24,43,.99)) !important;
  box-shadow:0 28px 64px -40px rgba(0,0,0,.95),0 0 36px -20px rgba(255,66,105,.40),inset 0 1px 0 rgba(255,255,255,.055) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-header"] {
  border-bottom-color:rgba(255,82,116,.14);
  background:linear-gradient(90deg,rgba(116,33,54,.18),transparent 70%);
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] .divide-y > a > div > p {
  color:#f3f6fb !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card [data-slot="card-content"] .text-destructive {
  color:#ff718d !important;
}

/* ---------------------------------------------------------
   6) MY ACTIVITIES — more premium icon holders and hierarchy
   --------------------------------------------------------- */
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child {
  border-color:rgba(99,102,241,.18) !important;
}
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-header"] {
  min-height:48px !important;
  padding:14px 16px 10px !important;
  border-bottom:1px solid rgba(99,102,241,.09);
}
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-title"] {
  color:#2f3850 !important;
  font-size:12px !important;
  font-weight:850 !important;
  letter-spacing:.01em !important;
}
.tcrm-premium-dashboard .luxury-activity-icon,
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child .text-base > span {
  width:30px !important;
  height:30px !important;
  min-width:30px !important;
  border-radius:10px !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  color:#5b55e8 !important;
  border:1px solid rgba(99,102,241,.20) !important;
  background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(238,240,255,.92)) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.98),0 7px 16px -10px rgba(79,70,229,.55),0 0 15px -10px rgba(99,102,241,.54) !important;
}
.tcrm-premium-dashboard .luxury-activity-icon svg,
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child .text-base > span svg {
  width:14px !important;height:14px !important;stroke-width:2.35 !important;
}
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-content"] .divide-y > div {
  min-height:46px !important;
  padding:8px 14px !important;
}
.tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-content"] p:first-child {
  color:#303a50 !important;
  font-weight:750 !important;
}
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-title"],
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child [data-slot="card-content"] p:first-child {
  color:#f3f5fb !important;
}
.dark .tcrm-premium-dashboard .luxury-activity-icon,
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .grid > .space-y-4 > [data-slot="card"]:last-child .text-base > span {
  color:#a9a1ff !important;
  border-color:rgba(122,115,255,.30) !important;
  background:linear-gradient(145deg,rgba(76,69,190,.22),rgba(25,32,58,.88)) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.09),0 0 22px -10px rgba(100,90,255,.72) !important;
}
'''

CSS.write_text(css + V26, encoding="utf-8")

protected_after = {
    str(AGENT): hashlib.sha256(AGENT.read_bytes()).hexdigest(),
    str(TEAM): hashlib.sha256(TEAM.read_bytes()).hexdigest(),
    str(LEADS): hashlib.sha256(LEADS.read_bytes()).hexdigest(),
}
if protected_before != protected_after:
    raise SystemExit("ERROR=PROTECTED_SOURCE_CHANGED")

final_css = CSS.read_text(encoding="utf-8")
checks = {
    "V26_MARKER": MARKER in final_css,
    "DATE_TRIGGER_POLISH": ".tcrm-luxury-date-control .tcrm-date-range-trigger" in final_css,
    "DATE_POPOVER_POLISH": ".tcrm-date-range-popover" in final_css,
    "QUALITY_BADGE_POLISH": ".lead-quality-bad" in final_css and ".lead-quality-unknown" in final_css and ".lead-quality-hot" in final_css,
    "KPI_ICON_POLISH": ".luxury-kpi-icon-core svg" in final_css,
    "SLA_POLISH": ".tcrm-luxury-sla-card" in final_css,
    "ACTIVITY_POLISH": ".luxury-activity-icon" in final_css,
}
if not all(checks.values()):
    raise SystemExit("ERROR=V26_VERIFY_FAILED:" + "|".join(k for k,v in checks.items() if not v))

print("PATCH=YES")
print("V26_PREMIUM_CONTROL_POLISH=YES")
print("CSS_ONLY=YES")
print("AGENT_DASHBOARD_TSX_PROTECTED=YES")
print("TEAM_DASHBOARD_PROTECTED=YES")
print("LEADS_PROTECTED=YES")
print("KPI_ICON_VISIBILITY_UPGRADED=YES")
print("KPI_TEXT_CONTRAST_UPGRADED=YES")
print("LEAD_QUALITY_BADGES_UPGRADED=YES")
print("DATE_TRIGGER_BLANK_CAPSULE_FIXED=YES")
print("DATE_PICKER_LIGHT_DARK_UPGRADED=YES")
print("SLA_ALERTS_PREMIUM_UPGRADED=YES")
print("MY_ACTIVITIES_ICON_HIERARCHY_UPGRADED=YES")
print("BACKUP_CREATED=YES")
print("BACKUP_DIR=" + str(backup_dir))
print("FILES_CHANGED=client/src/dashboard-premium-luminous-v16.css")
