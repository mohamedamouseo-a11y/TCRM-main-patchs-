#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-7-reference-fidelity.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V26_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_6_DETAILS_FORMDATA_REDESIGN"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_REFERENCE_FIDELITY_POLISH"
V26_IMPORT = 'import "../lead-profile-premium-v2-6-details-formdata.css";'
V27_IMPORT = 'import "../lead-profile-premium-v2-7-reference-fidelity.css";'

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
for token in [V26_MARKER, V26_IMPORT, "tcrm-lead-profile-premium-v2-6", "tcrm-lp-v26-details-grid", "tcrm-lp-v26-form-fields"]:
    if token not in src:
        raise SystemExit(f"ERROR: required pushed V2.6 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_7=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-7.bak"
shutil.copy2(TSX, backup)

# V2.7 is intentionally a CSS-only visual fidelity layer on top of pushed V2.6.
# No component structure, data, backend, permissions or business logic is changed.
if V27_IMPORT not in src:
    src = src.replace(V26_IMPORT, V26_IMPORT + "\n" + V27_IMPORT, 1)

if MARKER not in src:
    src = src.replace(f"// {V26_MARKER}", f"// {V26_MARKER}\n// {MARKER}", 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.7 — Reference Fidelity Polish
BASE: pushed V2.6 Details + Form Data Redesign
VISUAL BASIS:
- approved Lead Profile reference composition
- real /leads/2184 V2.6 runtime screenshots in Light + Dark

INTENT:
- Increase reference fidelity without redesigning the approved information architecture.
- Compact the common Hero so the command center reaches useful content faster.
- Reduce visual dead space while preserving the three-cluster Hero composition.
- Make Details read as dense structured information instead of many floating tiles.
- Make Form Data more compact and calmer while preserving real Q/A values.
- Tone down saturated section headers to match the reference hierarchy.
- Preserve Team Dashboard color language, V2.5 72/28 layout, RTL, backend and business logic.
*/

/* ========================================================================== */
/* 1) COMMON HERO — COMPACT REFERENCE PROPORTIONS                              */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell{
  gap:8px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-main{
  gap:6px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-identity{
  gap:4px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-meta{
  gap:5px 10px!important;
  font-size:12px!important;
  line-height:1.25!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
  min-height:0!important;
  padding:9px 11px!important;
  border-radius:13px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>span{
  font-size:9px!important;
  letter-spacing:.055em!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>p{
  margin-top:3px!important;
  font-size:11px!important;
  line-height:1.35!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy>small{
  margin-top:3px!important;
  font-size:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions{
  gap:6px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions button{
  min-height:32px!important;
  height:32px!important;
  padding-inline:10px!important;
  border-radius:10px!important;
  font-size:11px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context{
  margin-top:0!important;
  gap:8px!important;
  align-items:center!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context .rounded-full{
  min-height:30px!important;
}

@media (min-width:1280px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline{
    display:grid!important;
    grid-template-columns:minmax(330px,1.12fr) minmax(270px,.82fr) minmax(420px,auto)!important;
    align-items:center!important;
    gap:14px!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-identity,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions{
    align-self:center!important;
    margin:0!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
    width:100%!important;
    max-width:360px!important;
    justify-self:center!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions{
    justify-content:flex-end!important;
  }
  .tcrm-lead-profile-premium-v2-6[dir="rtl"] .tcrm-lp-v22-actions{
    justify-content:flex-start!important;
  }
}

/* ========================================================================== */
/* 2) DETAILS + FORM DATA — CALMER REFERENCE HEADER                            */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head{
  padding:11px 14px!important;
  background:linear-gradient(180deg,rgba(250,251,255,.98),rgba(244,247,255,.97))!important;
  border-bottom:1px solid var(--v26-border)!important;
}
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head,
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head{
  background:linear-gradient(180deg,rgba(16,43,80,.98),rgba(10,32,62,.98))!important;
  border-bottom-color:rgba(112,133,226,.22)!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head p:first-of-type,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head p:first-of-type{
  color:var(--v26-text)!important;
  font-size:12px!important;
  font-weight:820!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head p:last-of-type,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head p:last-of-type{
  color:var(--v26-muted)!important;
  font-size:9px!important;
  opacity:1!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head>.relative>.flex>div:first-child,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head>.relative>.flex>div:first-child{
  width:30px!important;
  height:30px!important;
  border-radius:9px!important;
  background:linear-gradient(145deg,rgba(99,102,241,.12),rgba(59,130,246,.07))!important;
  border:1px solid rgba(99,102,241,.16)!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head svg,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head svg{
  color:#6366f1!important;
}
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head svg,
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head svg{
  color:#a5b4fc!important;
}

/* ========================================================================== */
/* 3) DETAILS — DENSE STRUCTURED ROWS, NOT A WALL OF FLOATING TILES            */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>[data-slot="card-content"],
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card .p-4{
  padding:13px 15px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head{
  gap:8px!important;
  margin:0 0 5px!important;
  padding-bottom:7px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head .tcrm-lp-v26-section-icon{
  width:29px!important;
  height:29px!important;
  flex-basis:29px!important;
  border-radius:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head strong{
  font-size:12px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head span{
  margin-top:2px!important;
  font-size:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  column-gap:18px!important;
  row-gap:0!important;
  margin-bottom:10px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div{
  min-height:48px!important;
  padding:8px 5px!important;
  border:0!important;
  border-bottom:1px solid var(--v26-border)!important;
  border-radius:0!important;
  background:transparent!important;
  box-shadow:none!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div:hover{
  border-bottom-color:var(--v26-border-strong)!important;
  background:linear-gradient(90deg,rgba(99,102,241,.035),transparent)!important;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div:hover{
  background:linear-gradient(90deg,rgba(99,102,241,.07),transparent)!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section{
  margin-top:2px!important;
  padding:10px 5px 2px!important;
  border:0!important;
  border-top:1px solid var(--v26-border)!important;
  border-radius:0!important;
  background:transparent!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section>.flex.items-center{
  margin-bottom:6px!important;
  padding-bottom:6px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section>div:not(.flex){
  margin-top:3px!important;
}

/* Edit mode retains the same fields and behavior, but with reference density. */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab .grid.grid-cols-1.gap-3{
  gap:9px 12px!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab input,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab [role="combobox"]{
  min-height:34px!important;
  height:34px!important;
}

/* ========================================================================== */
/* 4) FORM DATA — COMPACT Q/A SHEET                                            */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>[data-slot="card-content"],
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card .p-4{
  padding:13px 15px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head{
  gap:8px!important;
  padding:0 0 8px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head .tcrm-lp-v26-section-icon{
  width:29px!important;
  height:29px!important;
  flex-basis:29px!important;
  border-radius:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head strong{
  font-size:12px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head span{
  margin-top:2px!important;
  font-size:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head em{
  height:22px!important;
  min-width:28px!important;
  padding-inline:7px!important;
  font-size:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields{
  gap:6px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field{
  grid-template-columns:30px minmax(0,1fr)!important;
  gap:8px!important;
  padding:7px 10px 7px 8px!important;
  border-radius:11px!important;
  background:linear-gradient(145deg,rgba(255,255,255,.88),rgba(248,250,255,.72))!important;
  box-shadow:none!important;
  transform:none!important;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field{
  background:linear-gradient(145deg,rgba(12,38,72,.86),rgba(9,30,59,.76))!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field:hover{
  transform:none!important;
  box-shadow:none!important;
  border-color:var(--v26-border-strong)!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-index{
  width:26px!important;
  height:26px!important;
  border-radius:8px!important;
  font-size:8px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-source-card{
  padding:10px!important;
  border-radius:11px!important;
  background:linear-gradient(145deg,rgba(99,102,241,.03),rgba(59,130,246,.018))!important;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-source-card{
  background:linear-gradient(145deg,rgba(99,102,241,.07),rgba(59,130,246,.035))!important;
}

/* ========================================================================== */
/* 5) RESPONSIVE GUARDS                                                        */
/* ========================================================================== */
@media (max-width:1279px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel{
    max-width:none!important;
  }
}
@media (max-width:860px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid{
    grid-template-columns:1fr!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div{
    min-height:44px!important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_6_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_7=YES")
print("REFERENCE_FIDELITY_POLISH=YES")
print("HERO_VERTICAL_DENSITY_POLISHED=YES")
print("HERO_THREE_CLUSTER_COMPOSITION_PRESERVED=YES")
print("HERO_DEAD_SPACE_REDUCED=YES")
print("DETAILS_DENSE_STRUCTURED_ROWS=YES")
print("DETAILS_TILE_WALL_REDUCED=YES")
print("FORMDATA_DENSITY_POLISHED=YES")
print("SECTION_HEADERS_REFERENCE_TONED=YES")
print("V2_5_MAIN_72_RAIL_28_PRESERVED=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("NO_INVENTED_LEAD_DATA=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("OVERVIEW_STRUCTURE_UNCHANGED=YES")
print("FELFEL_UNCHANGED=YES")
print("STAGES_NOTES_UNCHANGED=YES")
print("REMINDERS_UNCHANGED=YES")
print("QUOTATIONS_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-7-reference-fidelity.css")
