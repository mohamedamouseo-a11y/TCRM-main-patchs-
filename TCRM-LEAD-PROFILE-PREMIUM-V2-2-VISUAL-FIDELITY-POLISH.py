#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-2.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V21_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_1_STRUCTURAL_CORRECTION"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_2_VISUAL_FIDELITY_POLISH"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V21_MARKER,
    'import "../lead-profile-premium-v2-1.css";',
    'tcrm-lead-profile-premium-v2-1',
    'className="tcrm-lp-v2-overview-grid"',
    'className="tcrm-lp-v21-overview-right"',
    'className="tcrm-lp-v21-avatar"',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2.1 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_2=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-2.bak"
shutil.copy2(TSX, backup)

# 1) Add V2.2 import + marker. V2.2 is visual-only and layers on top of V2.1.
import_anchor = 'import "../lead-profile-premium-v2-1.css";'
if 'import "../lead-profile-premium-v2-2.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-2.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V21_MARKER}", f"// {V21_MARKER}\n// {MARKER}", 1)

# 2) Add one page scope class. No data/query/permission/business logic changes.
root_old = 'tcrm-lead-profile-premium-v2-1 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
root_new = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
if root_old not in src:
    raise SystemExit("ERROR: V2.1 root class anchor missing")
src = src.replace(root_old, root_new, 1)

# 3) Add deterministic HERO visual hooks to existing containers only.
#    These replacements do not move handlers or change any functionality.
visual_hooks = [
    (
        '<div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">',
        '<div className="tcrm-lp-v22-hero-shell flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">',
    ),
    (
        '<div className="min-w-0 flex-1 space-y-2">',
        '<div className="tcrm-lp-v22-hero-main min-w-0 flex-1 space-y-2">',
    ),
    (
        '<div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">',
        '<div className="tcrm-lp-v22-hero-topline flex flex-col gap-2 md:flex-row md:items-start md:justify-between">',
    ),
    (
        '<div className="min-w-0 space-y-1.5">',
        '<div className="tcrm-lp-v22-identity min-w-0 space-y-1.5">',
    ),
    (
        '<div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-muted-foreground">',
        '<div className="tcrm-lp-v22-meta flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-muted-foreground">',
    ),
    (
        '<div className="flex flex-wrap items-center gap-2 lg:justify-end">',
        '<div className="tcrm-lp-v22-actions flex flex-wrap items-center gap-2 lg:justify-end">',
    ),
    (
        '<div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">',
        '<div className="tcrm-lp-v22-context flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">',
    ),
]

for old, new in visual_hooks:
    if new in src:
        continue
    if old not in src:
        raise SystemExit(f"ERROR: V2.2 visual hook anchor missing: {old[:96]}")
    src = src.replace(old, new, 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.2 — Visual Fidelity Polish
BASE: V2.1 Structural Correction
REFERENCE: approved Lead Profile Light/Dark concept
COLOR SYSTEM: Team Dashboard Premium — PRESERVED
SCOPE: visual hierarchy, density, spacing, depth and typography only.
NO backend / API / permissions / mutations / routes / business logic changes.
*/

.tcrm-lead-profile-premium-v2-2{
  --v22-card-shadow:0 22px 52px -38px rgba(61,68,154,.42),0 8px 20px -18px rgba(73,80,170,.20),inset 0 1px 0 rgba(255,255,255,.96);
  --v22-card-border:rgba(96,103,210,.22);
}
.dark .tcrm-lead-profile-premium-v2-2{
  --v22-card-shadow:0 26px 62px -40px rgba(0,0,0,.94),0 0 26px -22px rgba(98,112,255,.40),inset 0 1px 0 rgba(255,255,255,.055);
  --v22-card-border:rgba(110,129,221,.34);
}

/* ===== HERO — use the full width intentionally, no dead middle ===== */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero{
  min-height:0!important;
  border-radius:19px!important;
  box-shadow:0 24px 58px -34px rgba(73,69,255,.34),0 9px 24px -20px rgba(70,81,170,.24),inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero{
  box-shadow:0 30px 72px -38px rgba(0,0,0,.98),0 0 32px -21px rgba(98,112,255,.60),inset 0 1px 0 rgba(255,255,255,.075)!important;
}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero>.md\:p-4{padding:16px 18px 15px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-hero-shell{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;gap:10px!important;align-items:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-hero-main{width:100%;min-width:0;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-hero-topline{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;gap:24px!important;align-items:center!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-identity{min-width:0;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-identity>.flex.flex-wrap.items-center{gap:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-avatar{
  width:70px!important;height:70px!important;flex-basis:70px!important;
  font-size:20px!important;border-width:3px!important;
  box-shadow:0 13px 32px -16px rgba(79,70,229,.72),0 0 0 1px rgba(99,102,241,.25)!important;
}
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-avatar{box-shadow:0 0 0 1px rgba(122,145,255,.54),0 0 30px -8px rgba(91,104,255,.72)!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero h1{font-size:28px!important;line-height:1.04!important;font-weight:900!important;letter-spacing:-.046em!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-meta{margin-top:2px;gap:6px 13px!important;font-size:11px!important;line-height:1.35;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-meta button{min-height:30px!important;font-size:10px!important;padding-inline:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-actions{max-width:610px;justify-content:flex-end!important;align-content:flex-start;gap:7px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-actions button{min-height:34px!important;height:34px!important;padding-inline:12px!important;font-size:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-context{
  margin-top:7px;padding-top:10px;border-top:1px solid rgba(99,102,241,.11);
  display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:14px!important;
}
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-context{border-top-color:rgba(126,145,255,.17);}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-context .rounded-full{min-height:32px;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-context+div.flex.flex-wrap{margin-top:7px!important;}

/* ===== KPI STRIP — more readable, closer to reference proportions ===== */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signals{gap:11px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-card{
  min-height:124px!important;padding:16px 16px 14px!important;border-radius:16px!important;
  border-color:var(--v22-card-border)!important;box-shadow:var(--v22-card-shadow)!important;
}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-icon{width:46px!important;height:46px!important;border-radius:14px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-copy>span{font-size:10px!important;line-height:1.25!important;font-weight:800!important;letter-spacing:.025em!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-copy strong{font-size:20px!important;line-height:1.08!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-copy em{font-size:9px!important;line-height:1.3!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-micro{font-size:9px!important;}

/* ===== NAVIGATION — stronger visual presence, still compact ===== */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-tabs{margin-bottom:11px!important;border-color:var(--v22-card-border)!important;box-shadow:var(--v22-card-shadow)!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-tabs>div{padding:7px 8px!important;gap:5px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-tabs button{min-height:36px!important;padding-inline:14px!important;font-size:10px!important;font-weight:750!important;}

/* ===== MAIN COMMAND CENTER — dense, content-driven, no forced empty oceans ===== */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-overview-grid{gap:12px!important;align-items:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-overview-right{gap:11px!important;align-self:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card{
  border-color:var(--v22-card-border)!important;box-shadow:var(--v22-card-shadow)!important;border-radius:14px!important;
}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card-head{
  min-height:47px!important;padding:10px 13px!important;
  background:linear-gradient(90deg,rgba(99,102,241,.055),rgba(59,130,246,.022))!important;
}
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card-head{background:linear-gradient(90deg,rgba(91,104,216,.15),rgba(41,74,140,.075))!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card-title{font-size:12px!important;font-weight:850!important;gap:9px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card-title svg{width:17px;height:17px;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-mini-action{height:29px!important;min-height:29px!important;padding-inline:10px!important;font-size:9px!important;}

/* Contact / additional information gets a little more breathing room without becoming tall. */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-info-list{padding:9px 13px 11px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-info-list>div{min-height:31px!important;padding:5px 0!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-info-list>div>*{font-size:9px;}

/* Timeline height follows content. This is the main V2.1 empty-space correction. */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-card{min-height:0!important;height:auto!important;align-self:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline{min-height:0!important;height:auto!important;padding:7px 13px 9px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-item{padding:10px 0!important;grid-template-columns:40px minmax(0,1fr) auto!important;gap:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-icon{width:32px!important;height:32px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-copy strong{font-size:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-copy p{font-size:9px!important;line-height:1.4!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-item time,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-timeline-item time small{font-size:8px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-empty-inline{min-height:62px!important;padding:10px!important;}

/* Notes also stays compact/content-driven. */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-notes-card{min-height:0!important;height:auto!important;align-self:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-notes-card [data-slot="card-content"]{padding:11px 13px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-note-preview{padding:10px!important;gap:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-note-avatar{width:30px!important;height:30px!important;flex-basis:30px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-note-preview strong{font-size:10px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-note-preview p{font-size:9px!important;line-height:1.42!important;}

/* Right executive rail: stronger hierarchy, tighter empty state. */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-overview-right .tcrm-lp-v2-card{align-self:start!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-compact-body,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-owner-body,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-task-body{padding:12px 13px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-compact-empty{min-height:96px!important;padding:10px 8px!important;gap:6px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-compact-empty svg{width:24px;height:24px;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-compact-empty strong{font-size:11px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-compact-empty p{font-size:8.5px!important;line-height:1.4!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-owner-avatar{width:36px!important;height:36px!important;flex-basis:36px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-owner-main strong{font-size:10.5px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-task-row strong{font-size:9px!important;}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-task-row p{font-size:7.5px!important;}

/* ===== LIGHT MODE — pearl/lilac depth, still the Team Dashboard palette ===== */
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-card,
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-tabs{
  background:linear-gradient(145deg,rgba(255,255,255,.975),rgba(247,249,255,.93))!important;
}
.tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card:hover{border-color:rgba(99,102,241,.31)!important;}

/* ===== DARK MODE — preserve deep navy, add layer separation only ===== */
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card,
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-signal-card,
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-tabs{
  background:linear-gradient(145deg,rgba(14,31,58,.97),rgba(9,24,47,.94))!important;
}
.dark .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v2-card:hover{border-color:rgba(126,143,255,.46)!important;}

/* ===== Responsive fidelity ===== */
@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-avatar{width:62px!important;height:62px!important;flex-basis:62px!important;font-size:18px!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero h1{font-size:25px!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-actions{max-width:520px;}
}
@media (max-width:1180px){
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-hero-topline{grid-template-columns:1fr!important;gap:10px!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-actions{max-width:none;justify-content:flex-start!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-context{grid-template-columns:1fr!important;}
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v21-avatar{width:54px!important;height:54px!important;flex-basis:54px!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-hero h1{font-size:22px!important;}
  .tcrm-lead-profile-premium-v2-2 .tcrm-lp-v22-hero-shell{grid-template-columns:1fr!important;}
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_1_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_2=YES")
print("VISUAL_FIDELITY_POLISH=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("HERO_DISTRIBUTION_POLISHED=YES")
print("HERO_IDENTITY_ANCHOR_ENLARGED=YES")
print("KPI_READABILITY_POLISHED=YES")
print("NAVIGATION_POLISHED=YES")
print("TIMELINE_CONTENT_DRIVEN_HEIGHT=YES")
print("NOTES_CONTENT_DRIVEN_HEIGHT=YES")
print("EMPTY_STATES_COMPACTED=YES")
print("LIGHT_DEPTH_POLISHED=YES")
print("DARK_LAYERING_POLISHED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-2.css")
