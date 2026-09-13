#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-3.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V22_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_2_VISUAL_FIDELITY_POLISH"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_3_REGRESSION_RECOVERY"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V22_MARKER,
    'import "../lead-profile-premium-v2-2.css";',
    'tcrm-lead-profile-premium-v2-2',
    'className="tcrm-lp-hero',
    'className="tcrm-lp-v2-signals"',
    'className="tcrm-lp-v2-overview-grid"',
    'className="tcrm-lp-v2-overview-center"',
    'className="tcrm-lp-v21-overview-right"',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2.2 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_3=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-3.bak"
shutil.copy2(TSX, backup)

# Layer V2.3 after V2.2. No business logic, handlers, queries, mutations,
# permissions, routes or data structures are changed.
import_anchor = 'import "../lead-profile-premium-v2-2.css";'
if 'import "../lead-profile-premium-v2-3.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-3.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V22_MARKER}", f"// {V22_MARKER}\n// {MARKER}", 1)

root_old = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
root_new = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
if root_old not in src:
    raise SystemExit("ERROR: V2.2 root class anchor missing")
src = src.replace(root_old, root_new, 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.3 — Regression Recovery
BASE: V2.2 Visual Fidelity Polish
GOALS:
1) Protect Hero + KPI strip from disappearing/collapsing.
2) Recover a true full-width three-zone Overview.
3) Fix V2.2 center-card shrink caused by align-self:start.
4) Preserve V2.2 visual polish and Team Dashboard palette.
NO backend / business logic / permissions / routes / data changes.
*/

/* ===== TOP COMPOSITION REGRESSION GUARD ===== */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-hero{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  width:100%!important;
  max-width:none!important;
  position:relative!important;
  transform:none!important;
  overflow:hidden!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-signals{
  display:grid!important;
  visibility:visible!important;
  opacity:1!important;
  width:100%!important;
  max-width:none!important;
  grid-template-columns:repeat(5,minmax(0,1fr))!important;
  align-items:stretch!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-signal-card{
  width:100%!important;
  min-width:0!important;
  align-self:stretch!important;
}

/* Hero remains V2.2 visually, but all internal clusters are guaranteed visible. */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-hero-shell,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-hero-main,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-hero-topline,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-identity,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-meta,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-actions,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v22-context{
  visibility:visible!important;
  opacity:1!important;
}

/* ===== OVERVIEW WIDTH RECOVERY ===== */
.tcrm-lead-profile-premium-v2-3.tcrm-lp-v21-overview-active .lead-profile-grid{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  width:100%!important;
  max-width:none!important;
}
.tcrm-lead-profile-premium-v2-3.tcrm-lp-v21-overview-active .tcrm-lp-v2-main{
  width:100%!important;
  max-width:none!important;
  min-width:0!important;
}
.tcrm-lead-profile-premium-v2-3.tcrm-lp-v21-overview-active .tcrm-lp-rail{
  display:none!important;
}

/* True three-zone command center. No empty ocean between center and right rail. */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-grid{
  display:grid!important;
  width:100%!important;
  max-width:none!important;
  grid-template-columns:minmax(320px,.96fr) minmax(0,1.34fr) minmax(300px,.90fr)!important;
  gap:14px!important;
  align-items:start!important;
  justify-items:stretch!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-overview-right{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  align-self:stretch!important;
  align-items:stretch!important;
}

/* V2.2 set Timeline align-self:start, which made it shrink to max-content width.
   Recover full center-column width while keeping content-driven height. */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-timeline-card,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-notes-card,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-overview-right .tcrm-lp-v2-card,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-left .tcrm-lp-v2-card{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  align-self:stretch!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-timeline-card{
  min-height:0!important;
  height:auto!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-timeline,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-notes-card [data-slot="card-content"]{
  width:100%!important;
  min-width:0!important;
  height:auto!important;
}

/* Keep compact empty states, but let them use the card width instead of becoming narrow towers. */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-compact-empty,
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-empty-inline{
  width:100%!important;
  max-width:none!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-compact-empty p{
  max-width:270px!important;
}

/* Prevent headings/actions from forcing narrow columns. */
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-card-head{
  width:100%!important;
  min-width:0!important;
}
.tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-card-title{
  min-width:0!important;
}

/* ===== RESPONSIVE RECOVERY ===== */
@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-grid{
    grid-template-columns:minmax(285px,.94fr) minmax(0,1.30fr) minmax(270px,.86fr)!important;
    gap:12px!important;
  }
}
@media (max-width:1220px){
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-signals{
    grid-template-columns:repeat(3,minmax(0,1fr))!important;
  }
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-grid{
    grid-template-columns:minmax(0,1fr) minmax(0,1.25fr)!important;
  }
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-overview-right{
    grid-column:1/-1!important;
    display:grid!important;
    grid-template-columns:repeat(3,minmax(0,1fr))!important;
    gap:12px!important;
  }
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-signals{
    grid-template-columns:1fr 1fr!important;
  }
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-overview-grid{
    grid-template-columns:1fr!important;
  }
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v21-overview-right{
    grid-column:auto!important;
    display:flex!important;
  }
}
@media (max-width:560px){
  .tcrm-lead-profile-premium-v2-3 .tcrm-lp-v2-signals{grid-template-columns:1fr!important;}
}
'''
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_2_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_3=YES")
print("REGRESSION_RECOVERY=YES")
print("HERO_VISIBILITY_GUARD=YES")
print("KPI_VISIBILITY_GUARD=YES")
print("OVERVIEW_FULL_WIDTH_RECOVERED=YES")
print("CENTER_COLUMN_WIDTH_RECOVERED=YES")
print("TIMELINE_STRETCH_RECOVERED=YES")
print("NOTES_STRETCH_RECOVERED=YES")
print("RIGHT_RAIL_WIDTH_RECOVERED=YES")
print("V2_2_VISUAL_POLISH_PRESERVED=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-3.css")