#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
V272_CSS = ROOT / "client/src/lead-profile-premium-v2-7-2-hero-reference-height.css"
CSS = ROOT / "client/src/lead-profile-premium-v2-7-3-hero-micro-fix.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"

V272_IMPORT = 'import "../lead-profile-premium-v2-7-2-hero-reference-height.css";'
V273_IMPORT = 'import "../lead-profile-premium-v2-7-3-hero-micro-fix.css";'
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_3_HERO_MICRO_FIX"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from live TCRM project root.")
if not V272_CSS.exists():
    raise SystemExit("ERROR: V2.7.2 hero CSS missing. This micro-fix must be applied on top of V2.7.2.")

src = TSX.read_text(encoding="utf-8")
if V272_IMPORT not in src:
    raise SystemExit("ERROR: V2.7.2 CSS import missing from LeadProfile.tsx.")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_7_3=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(TSX, BACKUP_DIR / f"LeadProfile.tsx.{stamp}.v2-7-3-hero-micro-fix.bak")
if V272_CSS.exists():
    shutil.copy2(V272_CSS, BACKUP_DIR / f"lead-profile-v2-7-2.{stamp}.bak.css")

if V273_IMPORT not in src:
    src = src.replace(V272_IMPORT, V272_IMPORT + "\n" + V273_IMPORT, 1)

# Keep the marker next to the visual-layer imports. No business logic is touched.
if MARKER not in src:
    src = src.replace(V273_IMPORT, V273_IMPORT + f"\n// {MARKER}", 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.7.3 — HERO MICRO-FIX
BASE: deployed V2.7.2 Hero Reference Height Final Fix
SCOPE: HERO ONLY

VISUAL BASIS:
- original approved Lead Profile Light/Dark reference screenshots
- real V2.7.2 /leads/2184 screenshots at 1920x1080

GOAL:
- Desktop hero visual height: 185–195px (target 192px).
- Remove the remaining empty bottom band.
- Keep Identity / Context / Actions vertically centered and fully visible.
- Keep the collapse control visible but absolutely positioned so it consumes zero layout height.
- Do NOT alter KPI, tabs, Details, Form Data, secondary layout, rail, backend or business logic.
*/

@media (min-width: 1280px) {
  /* Exact reference-height envelope. */
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero {
    position: relative !important;
    height: 192px !important;
    min-height: 192px !important;
    max-height: 192px !important;
    overflow: hidden !important;
  }

  /* The colored top accent is preserved; the content area uses the remaining height. */
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero > .p-3,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero > .md\\:p-4 {
    box-sizing: border-box !important;
    height: calc(100% - 3px) !important;
    min-height: 0 !important;
    padding: 10px 16px 9px !important;
    display: flex !important;
    align-items: center !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-main {
    width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
    margin: 0 !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-shell {
    display: block !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-hero-topline {
    min-height: 0 !important;
    height: auto !important;
    align-items: center !important;
    gap: 12px !important;
    margin: 0 !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-identity,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions {
    align-self: center !important;
    margin-block: 0 !important;
  }

  /* Preserve readability without allowing any cluster to force extra hero height. */
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v21-avatar {
    width: 68px !important;
    height: 68px !important;
    flex-basis: 68px !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero h1 {
    font-size: 26px !important;
    line-height: 1.02 !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-meta {
    margin-top: 2px !important;
    gap: 4px 9px !important;
    line-height: 1.2 !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-panel {
    min-height: 0 !important;
    max-height: 78px !important;
    padding: 8px 10px !important;
    overflow: hidden !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v24-context-copy > p {
    -webkit-line-clamp: 2 !important;
    line-height: 1.3 !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions {
    gap: 5px !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-actions button {
    min-height: 30px !important;
    height: 30px !important;
    padding-inline: 9px !important;
  }

  /* The secondary status/context row must remain content-driven, never a reserved band. */
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context {
    min-height: 0 !important;
    height: auto !important;
    margin-top: 5px !important;
    padding-top: 5px !important;
    gap: 5px 8px !important;
  }

  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v22-context .rounded-full {
    min-height: 26px !important;
    height: 26px !important;
  }

  /*
   * Collapse control: zero-flow overlay.
   * V2.7.2 may expose it either as a direct hero button or through accessible
   * collapse/expand labels. These selectors intentionally exclude action buttons.
   */
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero > button,
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero button[aria-label*="collapse" i],
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero button[title*="collapse" i],
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero button[aria-label*="expand" i],
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero button[title*="expand" i] {
    position: absolute !important;
    left: 50% !important;
    right: auto !important;
    bottom: 3px !important;
    transform: translateX(-50%) !important;
    z-index: 8 !important;
    margin: 0 !important;
  }
}

/* Do not force a fixed hero height on tablet/mobile. */
@media (max-width: 1279px) {
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-hero {
    height: auto !important;
    max-height: none !important;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("LEAD_PROFILE_PREMIUM_V2_7_3=YES")
print("HERO_MICRO_FIX=YES")
print("HERO_ONLY_SCOPE=YES")
print("HERO_DESKTOP_TARGET_PX=192")
print("DETAILS_UNCHANGED=YES")
print("FORMDATA_UNCHANGED=YES")
print("KPI_UNCHANGED=YES")
print("RAIL_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("SOURCE_PROJECT_PUSHED=NO")
print(f"BACKUP_TSX={backup if 'backup' in globals() else ''}")
print(f"FILES_CHANGED={TSX.relative_to(ROOT)},{CSS.relative_to(ROOT)}")
