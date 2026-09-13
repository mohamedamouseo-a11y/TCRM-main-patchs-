#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-7-1-final-density.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"

V27_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_REFERENCE_FIDELITY_POLISH"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_1_FINAL_DENSITY_CORRECTION"
V27_IMPORT = 'import "../lead-profile-premium-v2-7-reference-fidelity.css";'
V271_IMPORT = 'import "../lead-profile-premium-v2-7-1-final-density.css";'

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
for token in [V27_MARKER, V27_IMPORT, "tcrm-lp-v22-hero-shell", "tcrm-lp-v24-context-panel", "tcrm-lp-v26-details-card", "tcrm-lp-v26-formdata-card"]:
    if token not in src:
        raise SystemExit(f"ERROR: required pushed V2.7 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_7_1=YES")
    print("FINAL_DENSITY_CORRECTION=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-7-1.bak"
shutil.copy2(TSX, backup)

if V271_IMPORT not in src:
    src = src.replace(V27_IMPORT, V27_IMPORT + "\n" + V271_IMPORT, 1)
if MARKER not in src:
    src = src.replace(f"// {V27_MARKER}", f"// {V27_MARKER}\n// {MARKER}", 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.7.1 — Final Density Correction
BASE: V2.7 Reference Fidelity Polish
VISUAL BASIS: approved reference + real V2.7 runtime screenshots /leads/2184

STRICT INTENT:
- FINAL micro-polish only.
- Reduce common Hero height/dead space by about 25–30% at 1920px desktop.
- Preserve Identity / Lead Context / Actions composition and all real lead data.
- Compact empty Deal / Team / Notes rail states so supporting cards do not dominate.
- Preserve V2.7 Details and Form Data structure, row system, typography and data.
- Preserve V2.5 72/28 secondary-tab layout and RTL physical order.
- Preserve Team Dashboard color system.
- No backend / API / permissions / queries / mutations / routes / business logic changes.
*/

/* ========================================================================== */
/* 1) HERO — FORCE CONTENT-DRIVEN HEIGHT                                       */
/* V2.7 improved inner density but the runtime card still retained excess      */
/* vertical canvas. These overrides remove every residual min-height source.   */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero{
  min-height:0!important;
  height:auto!important;
  max-height:none!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.md\\:p-4{
  min-height:0!important;
  height:auto!important;
  padding:11px 16px 9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-main,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-identity,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context{
  min-height:0!important;
  height:auto!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell{
  gap:4px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-main{
  gap:3px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline{
  gap:11px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-identity>.flex.flex-wrap.items-center{
  gap:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-avatar{
  width:68px!important;
  height:68px!important;
  flex:0 0 68px!important;
  font-size:19px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero h1{
  font-size:27px!important;
  line-height:1!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-meta{
  margin-top:2px!important;
  gap:4px 9px!important;
  font-size:10px!important;
  line-height:1.15!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-meta button{
  min-height:27px!important;
  height:27px!important;
  padding-inline:8px!important;
  font-size:9px!important;
}

/* Middle context becomes a compact information strip, not a tall quote card. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
  min-height:58px!important;
  height:auto!important;
  grid-template-columns:25px minmax(0,1fr)!important;
  gap:7px!important;
  padding:7px 10px!important;
  border-radius:11px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-quote{
  height:25px!important;
  font-size:31px!important;
  line-height:.72!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>span{
  margin-bottom:2px!important;
  font-size:8px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>p{
  font-size:10px!important;
  line-height:1.25!important;
  -webkit-line-clamp:2!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>small{
  margin-top:2px!important;
  font-size:8px!important;
}

/* Primary actions stay complete but consume less vertical space. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions{
  gap:5px!important;
  row-gap:5px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions button{
  min-height:30px!important;
  height:30px!important;
  padding-inline:9px!important;
  border-radius:9px!important;
  font-size:9px!important;
}

/* Status / timing / secondary-action rows are the main V2.7 vertical-space leak. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context{
  margin-top:4px!important;
  padding-top:4px!important;
  gap:4px 8px!important;
  line-height:1.1!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context .rounded-full{
  min-height:26px!important;
  height:26px!important;
  padding-block:2px!important;
  font-size:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap{
  margin-top:4px!important;
  gap:5px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap button{
  min-height:28px!important;
  height:28px!important;
  padding-inline:9px!important;
  font-size:9px!important;
}

/* If any historical Tailwind min-height utility remains inside the Hero, neutralize it. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero [class*="min-h-"]{
  min-height:0!important;
}

@media (min-width:1280px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline{
    grid-template-columns:minmax(350px,1.04fr) minmax(260px,.72fr) minmax(430px,1.10fr)!important;
    align-items:center!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
    width:100%!important;
    max-width:330px!important;
    justify-self:center!important;
  }
}

/* ========================================================================== */
/* 2) KPI / NAV PROXIMITY — REMOVE UNUSED VERTICAL GAPS                        */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero+*{
  margin-top:10px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v2-signals{
  margin-top:0!important;
  gap:10px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-tabs{
  margin-top:0!important;
  margin-bottom:9px!important;
}

/* ========================================================================== */
/* 3) OVERVIEW RIGHT RAIL — REFERENCE-SCALE EMPTY STATES                       */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-overview-right{
  gap:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-overview-right .tcrm-lp-v2-card-head{
  min-height:43px!important;
  padding:8px 11px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-body,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-owner-body,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-task-body{
  padding:9px 11px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-empty{
  min-height:74px!important;
  padding:7px 6px!important;
  gap:4px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-empty svg{
  width:21px!important;
  height:21px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-empty strong{
  font-size:10px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-empty p{
  margin-top:0!important;
  font-size:8px!important;
  line-height:1.25!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-compact-empty button{
  min-height:28px!important;
  height:28px!important;
  font-size:8px!important;
}

/* ========================================================================== */
/* 4) SECONDARY-TAB LEGACY RAIL — EMPTY CARDS MUST SUPPORT, NOT DOMINATE       */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail>.space-y-3{
  display:flex!important;
  flex-direction:column!important;
  gap:9px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [data-slot="card"]{
  height:auto!important;
  min-height:0!important;
  border-radius:14px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [data-slot="card-header"]{
  min-height:42px!important;
  padding:8px 11px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [data-slot="card-content"]{
  min-height:0!important;
  height:auto!important;
  padding:9px 11px 10px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [class~="py-8"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [class~="py-10"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [class~="py-12"]{
  padding-top:12px!important;
  padding-bottom:12px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail .flex.flex-col.items-center.justify-center{
  min-height:76px!important;
  height:auto!important;
  gap:5px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail .flex.flex-col.items-center.justify-center svg{
  width:22px!important;
  height:22px!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail .flex.flex-col.items-center.justify-center p{
  margin-top:2px!important;
  margin-bottom:2px!important;
  line-height:1.25!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail .flex.flex-col.items-center.justify-center button{
  min-height:28px!important;
  height:28px!important;
  padding-inline:9px!important;
}

/* Do not disturb V2.7 Details / Form Data main-content system. */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card{
  min-height:0!important;
}

/* ========================================================================== */
/* 5) RESPONSIVE SAFETY                                                        */
/* ========================================================================== */
@media (max-width:1279px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline{
    gap:8px!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-avatar{
    width:62px!important;
    height:62px!important;
    flex-basis:62px!important;
  }
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.p-3,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.md\\:p-4{
    padding:10px 11px!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions button,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap button{
    height:auto!important;
    min-height:30px!important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_7_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_7_1=YES")
print("FINAL_DENSITY_CORRECTION=YES")
print("HERO_CONTENT_DRIVEN_HEIGHT=YES")
print("HERO_DEAD_SPACE_CORRECTION=YES")
print("OVERVIEW_EMPTY_RAIL_COMPACTED=YES")
print("SECONDARY_EMPTY_RAIL_COMPACTED=YES")
print("DETAILS_V2_7_STRUCTURE_PRESERVED=YES")
print("FORMDATA_V2_7_STRUCTURE_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"FILES_CHANGED={TSX.relative_to(ROOT)},{CSS.relative_to(ROOT)}")