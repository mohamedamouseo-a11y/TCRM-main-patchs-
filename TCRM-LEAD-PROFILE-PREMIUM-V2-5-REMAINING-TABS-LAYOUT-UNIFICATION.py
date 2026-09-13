#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-5.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V24_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_4_REFERENCE_FIDELITY_PASS"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_5_REMAINING_TABS_LAYOUT_UNIFICATION"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V24_MARKER,
    'import "../lead-profile-premium-v2-4.css";',
    'tcrm-lead-profile-premium-v2-4',
    'className="tcrm-lp-v2-main min-w-0"',
    'className="tcrm-lp-rail space-y-3',
    'tcrm-lp-v21-overview-active',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2.4 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_5=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-5.bak"
shutil.copy2(TSX, backup)

# -----------------------------------------------------------------------------
# V2.5 layers ONLY on non-Overview tabs.
# Overview V2.4 remains the approved reference and must not be changed.
# -----------------------------------------------------------------------------
import_anchor = 'import "../lead-profile-premium-v2-4.css";'
if 'import "../lead-profile-premium-v2-5.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-5.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V24_MARKER}", f"// {V24_MARKER}\n// {MARKER}", 1)

root_old = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 tcrm-lead-profile-premium-v2-4 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
root_new = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 tcrm-lead-profile-premium-v2-4 tcrm-lead-profile-premium-v2-5 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : "tcrm-lp-v25-secondary-tab-active"} min-h-screen'
if root_old not in src:
    raise SystemExit("ERROR: V2.4 root class anchor missing")
src = src.replace(root_old, root_new, 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.5 — Remaining Tabs Layout Unification
BASE: approved V2.4 Reference Fidelity Pass
SCOPE: non-Overview tabs ONLY
TARGET TABS: Details / Form Data / Felfel Meetings / Stages & Notes / Reminders / Quotations

GOALS:
- Preserve approved Overview V2.4 pixel composition.
- Fix non-Overview physical column split to ~72% main / ~28% legacy rail.
- Keep the main tab content readable and dominant in both LTR and RTL.
- Keep the legacy Deal/Team/Notes/Attachments/Handover rail compact.
- Fix dark-mode white quotation/empty-state surfaces.
- Do not change backend, queries, mutations, permissions, routes or business logic.
*/

.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active{
  --v25-gap:14px;
  --v25-rail-min:300px;
}

/* ========================================================================== */
/* NON-OVERVIEW TWO-COLUMN CONTRACT                                            */
/* Explicit grid areas prevent RTL direction from swapping visual importance. */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .lead-profile-grid{
  display:grid!important;
  direction:ltr!important;
  grid-template-columns:minmax(0,2.65fr) minmax(var(--v25-rail-min),1fr)!important;
  grid-template-areas:"main rail"!important;
  gap:var(--v25-gap)!important;
  align-items:start!important;
  justify-items:stretch!important;
  width:100%!important;
  max-width:none!important;
}

.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main{
  grid-area:main!important;
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  align-self:start!important;
}

.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail{
  grid-area:rail!important;
  display:block!important;
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  align-self:start!important;
}

/* Restore text direction inside each physical column without changing column order. */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active[dir="rtl"] .tcrm-lp-v2-main,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active[dir="rtl"] .tcrm-lp-rail{
  direction:rtl!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active[dir="ltr"] .tcrm-lp-v2-main,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active[dir="ltr"] .tcrm-lp-rail{
  direction:ltr!important;
}

/* ========================================================================== */
/* MAIN TAB CONTENT WIDTH RECOVERY                                             */
/* Prevent tab panes/cards from retaining the narrow V1/V2 legacy max-width.  */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main>[role="tabpanel"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [role="tabpanel"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main>[data-state="active"]{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
}

.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main>*,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [data-slot="card"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .card{
  min-width:0!important;
}

/* Only remove legacy max-width caps from the active tab content tree. */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [role="tabpanel"] [class*="max-w-"]{
  max-width:none!important;
}

/* Better reading density for tables, forms, editors and timeline-like tab bodies. */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main table{
  width:100%!important;
  table-layout:auto!important;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main textarea{
  width:100%!important;
  min-height:120px;
}
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main input,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main select{
  max-width:100%;
}

/* ========================================================================== */
/* LEGACY RAIL — COMPACT, SUPPORTING, NEVER DOMINANT                           */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail>.space-y-3,
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail>*{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
}

.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [data-slot="card"]{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
}

/* Empty rail states should be compact rather than large presentation canvases. */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [class*="min-h-"]{
  min-height:0!important;
}

/* ========================================================================== */
/* QUOTATIONS DARK MODE — REMOVE WHITE SURFACE REGRESSION                      */
/* Scoped to non-Overview main content only so V2.4 Overview remains intact.  */
/* ========================================================================== */
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .bg-white,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [class~="bg-white"],
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [class*="bg-white/"]{
  background-color:rgba(9,29,58,.96)!important;
  color:var(--lp2-text)!important;
}

.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .bg-gray-50,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .bg-slate-50,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .bg-zinc-50{
  background-color:rgba(11,34,67,.88)!important;
}

.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .text-gray-900,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .text-slate-900,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .text-zinc-900{
  color:var(--lp2-text)!important;
}

.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .border-gray-200,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .border-slate-200,
.dark .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main .border-zinc-200{
  border-color:rgba(107,128,222,.28)!important;
}

/* Keep secondary tab cards aligned with V2.4 Team Dashboard depth. */
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-v2-main [data-slot="card"],
.tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail [data-slot="card"]{
  border-radius:14px;
}

/* ========================================================================== */
/* RESPONSIVE CONTRACT                                                         */
/* ========================================================================== */
@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active{
    --v25-gap:12px;
    --v25-rail-min:280px;
  }
  .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .lead-profile-grid{
    grid-template-columns:minmax(0,2.5fr) minmax(var(--v25-rail-min),1fr)!important;
  }
}

@media (max-width:1180px){
  .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .lead-profile-grid{
    grid-template-columns:1fr!important;
    grid-template-areas:"main" "rail"!important;
  }
  .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail{
    display:grid!important;
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    gap:12px!important;
  }
}

@media (max-width:720px){
  .tcrm-lead-profile-premium-v2-5.tcrm-lp-v25-secondary-tab-active .tcrm-lp-rail{
    grid-template-columns:1fr!important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_4_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_5=YES")
print("REMAINING_TABS_LAYOUT_UNIFICATION=YES")
print("OVERVIEW_V2_4_UNTOUCHED=YES")
print("NON_OVERVIEW_MAIN_72_RAIL_28=YES")
print("RTL_PHYSICAL_COLUMN_ORDER_FIXED=YES")
print("DETAILS_WIDTH_RECOVERED=YES")
print("FORM_DATA_WIDTH_RECOVERED=YES")
print("FELFEL_MEETINGS_WIDTH_RECOVERED=YES")
print("STAGES_NOTES_WIDTH_RECOVERED=YES")
print("REMINDERS_WIDTH_RECOVERED=YES")
print("QUOTATIONS_WIDTH_RECOVERED=YES")
print("QUOTATIONS_DARK_SURFACE_FIX=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-5.css")
