#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-7-2-hero-reference-height.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"

V271_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_1_FINAL_DENSITY_CORRECTION"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_2_HERO_REFERENCE_HEIGHT_FINAL_FIX"
V271_IMPORT = 'import "../lead-profile-premium-v2-7-1-final-density.css";'
V272_IMPORT = 'import "../lead-profile-premium-v2-7-2-hero-reference-height.css";'

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
for token in [
    V271_MARKER,
    V271_IMPORT,
    "tcrm-lp-hero",
    "tcrm-lp-v22-hero-shell",
    "tcrm-lp-v22-hero-main",
    "tcrm-lp-v22-context",
    "setHeaderCollapsed",
]:
    if token not in src:
        raise SystemExit(f"ERROR: required applied V2.7.1 anchor missing: {token}")

v271_css = ROOT / "client/src/lead-profile-premium-v2-7-1-final-density.css"
if not v271_css.exists():
    raise SystemExit("ERROR: V2.7.1 CSS file missing. Apply V2.7.1 first.")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_7_2=YES")
    print("HERO_REFERENCE_HEIGHT_FINAL_FIX=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-7-2.bak"
shutil.copy2(TSX, backup)

if V272_IMPORT not in src:
    src = src.replace(V271_IMPORT, V271_IMPORT + "\n" + V272_IMPORT, 1)
if MARKER not in src:
    src = src.replace(f"// {V271_MARKER}", f"// {V271_MARKER}\n// {MARKER}", 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.7.2 — Hero Reference Height Final Fix
BASE: V2.7.1 Final Density Correction
VISUAL BASIS: approved Lead Profile reference + real V2.7.1 /leads/2184 screenshots

STRICT SCOPE:
- HERO ONLY.
- Fix the remaining ~40px structural height leak caused by the Collapse control participating in normal document flow.
- Target desktop Hero height at 1920px: approximately 195–210px.
- Preserve Identity / Lead Context / Actions / status controls and all real data.
- Preserve V2.7 Details, Form Data, rail, KPI cards, tabs, colors and 72/28 layout.
- No backend / API / queries / mutations / permissions / routes / business logic changes.
*/

/* ========================================================================== */
/* 1) REMOVE THE LAST STRUCTURAL HEIGHT LEAK                                   */
/* The collapse button is a direct child of .tcrm-lp-v22-hero-shell.           */
/* V2.4+ makes the shell block-like, so this button was adding its own row     */
/* beneath the hero main content. Keep the control visible but take it out     */
/* of normal flow. This should recover ~32–40px without shrinking content.     */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell{
  position:relative!important;
  min-height:0!important;
  height:auto!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell>button:last-child{
  position:absolute!important;
  inset-inline-end:1px!important;
  bottom:1px!important;
  margin:0!important;
  width:30px!important;
  height:30px!important;
  min-width:30px!important;
  min-height:30px!important;
  z-index:5!important;
}

/* Keep a tiny safe slot for the floating collapse control without creating   */
/* another visual row. The status/action content remains unchanged.            */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap{
  padding-inline-end:34px!important;
}

/* ========================================================================== */
/* 2) FINAL 4–6PX REFERENCE TUNING — NO TYPOGRAPHY SHRINK                      */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero>.md\\:p-4{
  padding-top:9px!important;
  padding-bottom:7px!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context{
  margin-top:3px!important;
  padding-top:3px!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap{
  margin-top:3px!important;
}

/* Preserve the V2.7.1 dimensions and visual hierarchy of actual content. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-avatar{
  width:68px!important;
  height:68px!important;
  flex-basis:68px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
  min-height:58px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions button{
  min-height:30px!important;
  height:30px!important;
}

/* ========================================================================== */
/* 3) EXPLICIT NON-SCOPE GUARDS                                                */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card{
  /* Intentionally no visual redesign in V2.7.2. */
}

/* On smaller layouts return the collapse control to flow; the 195–210px      */
/* desktop target applies to the 1920px QA viewport only.                      */
@media (max-width:1279px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell>button:last-child{
    position:static!important;
    margin-top:4px!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context+div.flex.flex-wrap{
    padding-inline-end:0!important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_7_1_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_7_2=YES")
print("HERO_REFERENCE_HEIGHT_FINAL_FIX=YES")
print("HERO_ONLY_SCOPE=YES")
print("COLLAPSE_CONTROL_REMOVED_FROM_DESKTOP_FLOW=YES")
print("HERO_CONTENT_TYPOGRAPHY_PRESERVED=YES")
print("DETAILS_V2_7_DESIGN_PRESERVED=YES")
print("FORMDATA_V2_7_DESIGN_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("SOURCE_PROJECT_PUSHED=NO")
print(f"BACKUP={backup}")
print(f"FILES_CHANGED={TSX.relative_to(ROOT)},{CSS.relative_to(ROOT)}")
