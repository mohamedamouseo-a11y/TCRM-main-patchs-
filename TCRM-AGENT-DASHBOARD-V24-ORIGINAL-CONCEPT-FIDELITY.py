#!/usr/bin/env python3
from pathlib import Path
import shutil
import datetime
import hashlib

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/AgentDashboard.tsx"
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"
MARKER = "/* TCRM Dashboard Original Concept V24 Fidelity */"

if not TSX.exists() or not CSS.exists():
    raise SystemExit("ERROR=AGENT_DASHBOARD_TARGET_MISSING")

source = TSX.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")

required_source = [
    "tcrm-premium-dashboard",
    "luxury-kpi-card",
    "tcrm-luxury-leads-card",
    "tcrm-luxury-reminders-card",
    "tcrm-luxury-sla-card",
    "tcrm-luxury-canvas",
    "tcrm-canvas-values",
    "ReminderCalendar",
]
missing = [x for x in required_source if x not in source]
if missing:
    raise SystemExit("ERROR=SOURCE_GUARD_MISSING:" + "|".join(missing))

if "TCRM Dashboard Luxury Concept V16" not in css or "V23 Safe Color Variables" not in css:
    raise SystemExit("ERROR=V16_V23_BASELINE_NOT_FOUND")

if MARKER in css:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v24-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / CSS.name)

before_tsx_hash = hashlib.sha256(TSX.read_bytes()).hexdigest()

V24 = r'''

/* TCRM Dashboard Original Concept V24 Fidelity */
/* Visual-only: original luminous Light/Dark concept fidelity. No data, API, route, permission or action changes. */

/* 1. CONTINUOUS PAGE ATMOSPHERE — remove the lower gray/background leak */
.tcrm-premium-dashboard {
  min-height: 100vh !important;
  overflow: visible;
  background:
    radial-gradient(circle at 18% 18%, rgba(124,58,237,.095), transparent 28rem),
    radial-gradient(circle at 74% 34%, rgba(59,130,246,.075), transparent 34rem),
    radial-gradient(ellipse at 42% 88%, rgba(99,102,241,.10), transparent 42rem),
    linear-gradient(180deg,#fbfcff 0%,#f5f7ff 48%,#eef3fb 100%) !important;
}
.tcrm-premium-dashboard::before {
  inset: 0 !important;
  opacity: .72 !important;
  mask-image: linear-gradient(to bottom, black 0%, black 82%, transparent 100%) !important;
  background-image:
    linear-gradient(rgba(99,102,241,.027) 1px,transparent 1px),
    linear-gradient(90deg,rgba(99,102,241,.027) 1px,transparent 1px),
    radial-gradient(circle at 12% 26%,rgba(124,58,237,.08),transparent 24rem) !important;
  background-size: 44px 44px,44px 44px,auto !important;
}
.dark .tcrm-premium-dashboard {
  background:
    radial-gradient(circle at 16% 10%,rgba(86,58,210,.18),transparent 30rem),
    radial-gradient(circle at 74% 22%,rgba(44,103,236,.13),transparent 34rem),
    radial-gradient(ellipse at 44% 78%,rgba(70,49,180,.18),transparent 42rem),
    linear-gradient(180deg,#07101d 0%,#091326 46%,#0a1428 100%) !important;
}
.dark .tcrm-premium-dashboard::before {
  opacity: .78 !important;
  background-image:
    linear-gradient(rgba(125,140,255,.035) 1px,transparent 1px),
    linear-gradient(90deg,rgba(125,140,255,.035) 1px,transparent 1px),
    radial-gradient(circle at 20% 28%,rgba(112,70,255,.13),transparent 26rem) !important;
}

/* 2. HERO — deeper violet/blue nebula and luminous edge like the original concept */
.tcrm-premium-dashboard > div:first-child {
  position: relative;
  overflow: hidden;
  border-color: rgba(255,255,255,.30) !important;
  background:
    radial-gradient(circle at 91% -8%,rgba(209,199,255,.58),transparent 25rem),
    radial-gradient(circle at 67% 115%,rgba(67,135,255,.40),transparent 27rem),
    radial-gradient(circle at 10% 35%,rgba(98,48,210,.48),transparent 22rem),
    linear-gradient(112deg,#351061 0%,#5520b6 33%,#493fe1 68%,#7368ff 100%) !important;
  box-shadow:
    0 30px 80px -34px rgba(70,40,190,.78),
    0 12px 34px -22px rgba(79,70,229,.90),
    0 0 0 1px rgba(133,113,255,.16),
    inset 0 1px 0 rgba(255,255,255,.34),
    inset 0 -1px 0 rgba(20,20,70,.30) !important;
}
.tcrm-premium-dashboard > div:first-child::before {
  background:
    radial-gradient(circle at 8% 24%,rgba(255,255,255,.28) 0 1px,transparent 1.6px),
    radial-gradient(circle at 34% 62%,rgba(255,255,255,.18) 0 1px,transparent 1.5px),
    radial-gradient(circle at 71% 20%,rgba(255,255,255,.22) 0 1px,transparent 1.5px),
    linear-gradient(106deg,transparent 0 35%,rgba(255,255,255,.17) 48%,transparent 61%),
    radial-gradient(circle at 72% -5%,rgba(255,255,255,.24),transparent 23rem) !important;
  background-size: 90px 78px,120px 104px,145px 125px,auto,auto !important;
  mix-blend-mode: screen;
}

/* 3. KPI STRIP — stronger neon glass + generated mini sparkline, no JSX needed */
.tcrm-premium-dashboard > .stagger-children > a:nth-child(1){--v24-kpi:99,102,241}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(2){--v24-kpi:96,92,255}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(3){--v24-kpi:34,197,94}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(4){--v24-kpi:77,124,255}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(5){--v24-kpi:245,158,11}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(6){--v24-kpi:239,68,68}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(7){--v24-kpi:139,92,246}
.tcrm-premium-dashboard > .stagger-children > a:nth-child(8){--v24-kpi:16,185,129}
.tcrm-premium-dashboard .luxury-kpi-card {
  min-height: 154px !important;
  border-color: rgba(var(--v24-kpi,99,102,241),.28) !important;
  background:
    radial-gradient(circle at 18% 8%,rgba(var(--v24-kpi,99,102,241),.09),transparent 8rem),
    linear-gradient(155deg,rgba(255,255,255,.995),rgba(246,248,255,.94)) !important;
  box-shadow:
    0 24px 50px -34px rgba(var(--v24-kpi,99,102,241),.42),
    0 10px 24px -20px rgba(15,23,42,.28),
    inset 0 1px 0 #fff,
    0 0 0 1px rgba(255,255,255,.62) !important;
}
.tcrm-premium-dashboard .luxury-kpi-card::before {
  height: 2px !important;
  background: linear-gradient(90deg,transparent 2%,rgba(var(--v24-kpi,99,102,241),.95) 48%,transparent 98%) !important;
  box-shadow: 0 0 18px rgba(var(--v24-kpi,99,102,241),.48) !important;
}
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"] {
  position: relative;
  min-height: 152px;
  z-index: 2;
}
.tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"]::after {
  content:"";
  position:absolute;
  right:13px;
  bottom:12px;
  width:58px;
  height:22px;
  opacity:.72;
  pointer-events:none;
  background:linear-gradient(180deg,rgba(var(--v24-kpi,99,102,241),.44),rgba(var(--v24-kpi,99,102,241),.035));
  clip-path:polygon(0 78%,12% 58%,24% 68%,37% 35%,51% 52%,64% 22%,78% 44%,90% 12%,100% 20%,100% 100%,0 100%);
  filter:drop-shadow(0 0 7px rgba(var(--v24-kpi,99,102,241),.36));
}
.dark .tcrm-premium-dashboard .luxury-kpi-card {
  border-color: rgba(var(--v24-kpi,99,102,241),.42) !important;
  background:
    radial-gradient(circle at 18% 4%,rgba(var(--v24-kpi,99,102,241),.15),transparent 8rem),
    linear-gradient(150deg,rgba(19,33,58,.985),rgba(10,22,42,.98)) !important;
  box-shadow:
    0 28px 58px -38px rgba(0,0,0,.96),
    0 0 34px -22px rgba(var(--v24-kpi,99,102,241),.88),
    inset 0 1px 0 rgba(255,255,255,.085),
    0 0 0 1px rgba(var(--v24-kpi,99,102,241),.08) !important;
}
.dark .tcrm-premium-dashboard .luxury-kpi-card:hover {
  border-color: rgba(var(--v24-kpi,99,102,241),.68) !important;
  box-shadow:
    0 30px 62px -36px rgba(0,0,0,.98),
    0 0 40px -18px rgba(var(--v24-kpi,99,102,241),.72),
    inset 0 1px 0 rgba(255,255,255,.10) !important;
}

/* 4. LEADS SURFACE — denser premium shell and subtle luminous frame */
.tcrm-premium-dashboard .tcrm-luxury-leads-card {
  border-color: rgba(112,121,220,.20) !important;
  box-shadow:
    0 26px 60px -40px rgba(56,46,160,.34),
    inset 0 1px 0 rgba(255,255,255,.82),
    0 0 0 1px rgba(99,102,241,.025) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-leads-card {
  border-color: rgba(113,126,255,.28) !important;
  background:linear-gradient(155deg,rgba(20,34,59,.985),rgba(12,25,46,.985)) !important;
  box-shadow:
    0 28px 64px -40px rgba(0,0,0,.96),
    0 0 38px -30px rgba(93,84,255,.66),
    inset 0 1px 0 rgba(255,255,255,.055) !important;
}

/* 5. RIGHT RAIL — Today Tasks + Reminders + SLA + Activities */
.tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"],
.tcrm-premium-dashboard .tcrm-luxury-sla-card,
.tcrm-premium-dashboard > div:nth-of-type(3) > .space-y-4 > [data-slot="card"]:last-child {
  overflow:hidden;
  border-color:rgba(108,117,220,.20) !important;
  background:linear-gradient(155deg,rgba(255,255,255,.985),rgba(247,249,255,.95)) !important;
  box-shadow:0 20px 50px -36px rgba(57,48,155,.36),inset 0 1px 0 rgba(255,255,255,.9) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"],
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card,
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .space-y-4 > [data-slot="card"]:last-child {
  border-color:rgba(109,123,255,.27) !important;
  background:linear-gradient(155deg,rgba(18,32,56,.99),rgba(11,23,43,.99)) !important;
  box-shadow:0 24px 58px -40px rgba(0,0,0,.95),0 0 30px -25px rgba(86,88,255,.62),inset 0 1px 0 rgba(255,255,255,.055) !important;
}
/* Today Tasks is the first real card inside ReminderCalendar: preserve its real reminder data/actions. */
.tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"]:first-child {
  min-height:150px;
  position:relative;
}
.tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"]:first-child [data-slot="card-content"] > .text-center {
  min-height:76px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:600;
  letter-spacing:.01em;
}
.tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"]:first-child::after {
  content:"";
  position:absolute;
  width:96px;height:96px;right:-30px;top:-32px;border-radius:50%;
  background:radial-gradient(circle,rgba(99,102,241,.14),transparent 68%);
  pointer-events:none;
}
/* Calendar depth */
.tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"]:nth-child(2) {
  box-shadow:0 24px 54px -38px rgba(71,61,170,.34),inset 0 1px 0 rgba(255,255,255,.86) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-reminders-card > .space-y-4 > [data-slot="card"]:nth-child(2) {
  box-shadow:0 26px 58px -40px rgba(0,0,0,.96),0 0 30px -25px rgba(94,88,255,.64),inset 0 1px 0 rgba(255,255,255,.05) !important;
}
/* SLA gets the original red luminous perimeter */
.tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border-color:rgba(239,68,68,.40) !important;
  box-shadow:0 20px 52px -38px rgba(239,68,68,.28),0 0 0 1px rgba(239,68,68,.06),inset 0 1px 0 rgba(255,255,255,.82) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-sla-card {
  border-color:rgba(255,72,91,.56) !important;
  box-shadow:0 26px 60px -42px rgba(0,0,0,.98),0 0 32px -20px rgba(255,52,78,.70),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
/* Activities: style both the recovered icon wrapper and the pre-wrapper fallback safely. */
.tcrm-premium-dashboard .luxury-activity-icon,
.tcrm-premium-dashboard > div:nth-of-type(3) > .space-y-4 > [data-slot="card"]:last-child span.text-base {
  width:28px;height:28px;min-width:28px;border-radius:9px;
  display:inline-flex;align-items:center;justify-content:center;
  color:#5d62f0;
  background:linear-gradient(145deg,rgba(99,102,241,.14),rgba(139,92,246,.06));
  border:1px solid rgba(99,102,241,.18);
  box-shadow:0 8px 18px -12px rgba(79,70,229,.58),inset 0 1px 0 rgba(255,255,255,.82) !important;
}
.dark .tcrm-premium-dashboard .luxury-activity-icon,
.dark .tcrm-premium-dashboard > div:nth-of-type(3) > .space-y-4 > [data-slot="card"]:last-child span.text-base {
  color:#9aa7ff;
  background:linear-gradient(145deg,rgba(90,92,255,.22),rgba(126,72,220,.09));
  border-color:rgba(113,126,255,.28);
  box-shadow:0 0 18px -8px rgba(91,92,255,.78),inset 0 1px 0 rgba(255,255,255,.055) !important;
}

/* 6. LOWER CANVAS — convert card into the original full atmospheric scene */
.tcrm-premium-dashboard .tcrm-luxury-canvas {
  min-height:620px !important;
  margin-top:22px !important;
  margin-inline:-10px !important;
  width:calc(100% + 20px) !important;
  padding:4.25rem 3.1rem 2.6rem !important;
  align-items:stretch !important;
  border:0 !important;
  border-radius:0 !important;
  background:
    radial-gradient(ellipse at 12% 18%,rgba(137,92,246,.15),transparent 25rem),
    radial-gradient(ellipse at 76% 62%,rgba(71,132,255,.14),transparent 30rem),
    radial-gradient(ellipse at 48% 105%,rgba(109,89,255,.18),transparent 34rem),
    linear-gradient(164deg,rgba(250,250,255,.74),rgba(239,244,255,.82)) !important;
  box-shadow:none !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas::before {
  inset:0 !important;
  opacity:.78 !important;
  mask-image:linear-gradient(to bottom,rgba(0,0,0,.55),black 42%,black 100%) !important;
  background:
    radial-gradient(circle at 10% 14%,rgba(109,92,255,.16) 0 1px,transparent 1.6px),
    radial-gradient(circle at 42% 38%,rgba(86,116,255,.13) 0 1px,transparent 1.5px),
    radial-gradient(circle at 72% 22%,rgba(133,92,246,.13) 0 1px,transparent 1.5px),
    repeating-linear-gradient(132deg,rgba(99,102,241,.035) 0 1px,transparent 1px 34px) !important;
  background-size:95px 82px,130px 112px,155px 138px,auto !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas::after {
  left:-12% !important;right:-12% !important;bottom:-7% !important;height:55% !important;
  opacity:.82;
  background:
    repeating-radial-gradient(ellipse at 50% 112%,transparent 0 26px,rgba(103,82,255,.075) 27px 28px,transparent 29px 53px),
    radial-gradient(ellipse at 50% 105%,rgba(103,82,255,.22),transparent 65%) !important;
  filter:blur(.1px) drop-shadow(0 -10px 26px rgba(91,77,220,.08));
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas {
  background:
    radial-gradient(ellipse at 14% 17%,rgba(116,67,232,.28),transparent 25rem),
    radial-gradient(ellipse at 76% 58%,rgba(42,101,230,.18),transparent 32rem),
    radial-gradient(ellipse at 52% 105%,rgba(84,60,210,.28),transparent 36rem),
    linear-gradient(160deg,#0b1528 0%,#0c1830 58%,#11183a 100%) !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas::before {
  opacity:.95 !important;
  background:
    radial-gradient(circle at 10% 14%,rgba(183,171,255,.38) 0 1px,transparent 1.6px),
    radial-gradient(circle at 42% 38%,rgba(116,157,255,.28) 0 1px,transparent 1.5px),
    radial-gradient(circle at 72% 22%,rgba(169,135,255,.30) 0 1px,transparent 1.5px),
    repeating-linear-gradient(132deg,rgba(123,116,255,.05) 0 1px,transparent 1px 34px) !important;
  background-size:95px 82px,130px 112px,155px 138px,auto !important;
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas::after {
  opacity:1;
  background:
    repeating-radial-gradient(ellipse at 50% 112%,transparent 0 25px,rgba(118,92,255,.15) 26px 27px,transparent 28px 51px),
    radial-gradient(ellipse at 50% 105%,rgba(92,64,226,.40),transparent 64%) !important;
  filter:drop-shadow(0 -14px 30px rgba(88,68,230,.22));
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-content {
  max-width:none !important;
  width:100%;
  min-height:520px;
  display:flex;
  flex-direction:column;
  align-items:flex-start;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  display:flex;
  flex-direction:column;
  gap:.02em;
  margin-top:14px;
  margin-bottom:1rem !important;
  font-size:clamp(2.3rem,3.2vw,3.35rem) !important;
  line-height:1.04 !important;
  letter-spacing:-.055em !important;
  text-shadow:0 10px 30px rgba(72,54,175,.13);
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas-headline {
  color:#eef1ff !important;
  text-shadow:0 0 28px rgba(137,121,255,.22),0 14px 38px rgba(0,0,0,.30);
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-sub {
  max-width:330px;
  font-size:.93rem !important;
}
.tcrm-premium-dashboard .tcrm-luxury-canvas-values {
  margin-top:auto !important;
  width:min(100%,620px) !important;
  padding-top:24px;
  border-top:1px solid rgba(100,95,205,.12);
}
.dark .tcrm-premium-dashboard .tcrm-luxury-canvas-values {
  border-top-color:rgba(130,126,255,.16);
}
.tcrm-premium-dashboard .tcrm-canvas-value {
  border:1px solid rgba(108,102,210,.11);
  border-radius:14px;
  padding:12px 13px;
  background:rgba(255,255,255,.30);
  backdrop-filter:blur(10px);
}
.dark .tcrm-premium-dashboard .tcrm-canvas-value {
  border-color:rgba(129,126,255,.17);
  background:rgba(44,42,105,.20);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035);
}

/* 7. RESPONSIVE fidelity */
@media (max-width:1023px){
  .tcrm-premium-dashboard .tcrm-luxury-canvas{min-height:500px !important;margin-inline:0 !important;width:100% !important;border-radius:20px !important;}
  .tcrm-premium-dashboard .tcrm-luxury-canvas-content{min-height:400px;}
}
@media (max-width:640px){
  .tcrm-premium-dashboard{padding-inline:.75rem !important;}
  .tcrm-premium-dashboard .tcrm-luxury-canvas{min-height:440px !important;padding:2.6rem 1.25rem 1.6rem !important;}
  .tcrm-premium-dashboard .tcrm-luxury-canvas-content{min-height:360px;}
  .tcrm-premium-dashboard .tcrm-luxury-canvas-values{grid-template-columns:1fr !important;gap:8px !important;}
  .tcrm-premium-dashboard .luxury-kpi-card [data-slot="card-content"]::after{width:44px;height:18px;}
}
'''

CSS.write_text(css.rstrip() + V24 + "\n", encoding="utf-8")

if hashlib.sha256(TSX.read_bytes()).hexdigest() != before_tsx_hash:
    shutil.copy2(backup_dir / CSS.name, CSS)
    raise SystemExit("ERROR=AGENT_DASHBOARD_TSX_CHANGED_UNEXPECTEDLY")

final_css = CSS.read_text(encoding="utf-8")
required_css = [
    MARKER,
    "min-height:620px",
    "repeating-radial-gradient",
    "luxury-kpi-card [data-slot=\"card-content\"]::after",
    "tcrm-luxury-sla-card",
    "tcrm-luxury-reminders-card",
]
missing_css = [x for x in required_css if x not in final_css]
if missing_css:
    shutil.copy2(backup_dir / CSS.name, CSS)
    raise SystemExit("ERROR=V24_VERIFY_FAILED:" + "|".join(missing_css))

print("PATCH=YES")
print("V24_ORIGINAL_CONCEPT_FIDELITY=YES")
print("CSS_ONLY=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("AGENT_DASHBOARD_TSX_CHANGED=NO")
print("BOTTOM_BACKGROUND_LEAK_FIX=YES")
print("HERO_NEBULA_UPGRADE=YES")
print("KPI_NEON_UPGRADE=YES")
print("KPI_CSS_SPARKLINES=YES")
print("TODAY_TASKS_REAL_COMPONENT_PRESERVED=YES")
print("REMINDERS_REAL_COMPONENT_PRESERVED=YES")
print("SLA_LUMINOUS_UPGRADE=YES")
print("ACTIVITY_VISUAL_UPGRADE=YES")
print("LOWER_CANVAS_FULL_ATMOSPHERIC=YES")
print("BACKUP_CREATED=YES")
print("BACKUP_DIR=" + str(backup_dir))
print("FILES_CHANGED=client/src/dashboard-premium-luminous-v16.css")
