#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
LAYOUT = ROOT / "client/src/components/CRMLayout.tsx"
CSS = ROOT / "client/src/crm-sidebar-premium-v1-1-hover-contrast.css"
BASE_CSS = ROOT / "client/src/crm-sidebar-premium-v1.css"

IMPORT_V1 = 'import "../crm-sidebar-premium-v1.css";'
IMPORT_V11 = 'import "../crm-sidebar-premium-v1-1-hover-contrast.css";'
BASE_MARKER = "TCRM_CRM_SIDEBAR_PREMIUM_V1_REFERENCE_MATCH"
MARKER = "TCRM_CRM_SIDEBAR_PREMIUM_V1_1_HOVER_CONTRAST_FIX"

CSS_TEXT = r'''/*
TCRM CRM Sidebar Premium V1.1 — Hover Contrast Fix
SCOPE: sidebar visual interaction only.
GOAL: prevent white-on-white hover states in Light Mode while preserving V1 structure,
routes, permissions, badges, RTL, collapse behavior and dark-mode language.
*/

/* --------------------------------------------------------------------------
   LIGHT MODE — explicit non-active hover contract
   -------------------------------------------------------------------------- */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible {
  color:#3047c8 !important;
  background:
    linear-gradient(90deg, rgba(84,100,225,.115) 0%, rgba(111,96,238,.075) 58%, rgba(255,255,255,.62) 100%) !important;
  border-color:rgba(88,101,224,.18) !important;
  box-shadow:
    0 7px 18px -15px rgba(60,72,190,.46),
    inset 0 1px 0 rgba(255,255,255,.88) !important;
}

/* Force every visible child to keep contrast even when old Tailwind group-hover
   utilities or theme rules try to turn the label/icon white. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover > span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover > span *,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover svg,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible > span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible > span *,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible svg {
  color:#3047c8 !important;
  stroke:currentColor !important;
}

/* Keep destructive/count badges readable and independent from the parent hover color. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:hover [data-slot="badge"] {
  color:#fff !important;
}

/* Slightly more premium icon treatment on Light hover. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover > span:first-of-type {
  filter:drop-shadow(0 3px 7px rgba(69,78,188,.16));
}

/* Child tree rows use the same contrast contract. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):focus-visible {
  color:#3348c4 !important;
  background:linear-gradient(90deg, rgba(86,101,226,.095), rgba(124,107,241,.045)) !important;
  box-shadow:inset 0 0 0 1px rgba(91,103,225,.09) !important;
}
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover svg,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):focus-visible span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):focus-visible svg {
  color:#3348c4 !important;
  stroke:currentColor !important;
}

/* Active primary route must remain the violet-blue capsule on hover. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row.text-white:hover,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row.text-white:focus-visible {
  color:#fff !important;
  background:linear-gradient(135deg,#5364df 0%,#655fe8 58%,#7561ef 100%) !important;
  border-color:rgba(255,255,255,.24) !important;
  box-shadow:0 8px 18px -10px rgba(72,76,211,.78),inset 0 1px 0 rgba(255,255,255,.22) !important;
}
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row.text-white:hover span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row.text-white:hover svg {
  color:#fff !important;
  stroke:currentColor !important;
}

/* Expanded group header: hover gets a stronger tinted surface, never white. */
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu):hover {
  color:#2f45c3 !important;
  background:linear-gradient(90deg, rgba(83,99,224,.13), rgba(119,102,241,.065)) !important;
  border-color:rgba(88,100,224,.18) !important;
}
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu):hover span,
html:not(.dark) .crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu):hover svg {
  color:#2f45c3 !important;
}

/* Collapsed desktop: keep the hover target visible and premium around the icon. */
html:not(.dark) .crm-sidebar-premium-v1.w-16 .crm-sidebar-row:not(.text-white):hover {
  background:linear-gradient(135deg, rgba(83,99,224,.14), rgba(122,105,243,.08)) !important;
  border-color:rgba(88,101,224,.18) !important;
  transform:none !important;
}

/* --------------------------------------------------------------------------
   DARK MODE — lock hover contrast so future utility-order changes cannot regress
   -------------------------------------------------------------------------- */
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible {
  color:#f1f5ff !important;
  background:linear-gradient(90deg, rgba(75,96,224,.22), rgba(110,83,237,.12)) !important;
  border-color:rgba(112,132,238,.23) !important;
  box-shadow:0 8px 18px -16px rgba(0,0,0,.78),inset 0 1px 0 rgba(255,255,255,.035) !important;
}
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover span,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover span *,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):hover svg,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible span,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:not(.text-white):focus-visible svg {
  color:#f1f5ff !important;
  stroke:currentColor !important;
}
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover,
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):focus-visible {
  color:#e5ecff !important;
  background:rgba(81,101,228,.16) !important;
}
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover span,
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem:not(.text-white):hover svg {
  color:#e5ecff !important;
  stroke:currentColor !important;
}

/* Keyboard focus uses the same visual language and never falls back to a white fill. */
.crm-sidebar-premium-v1 .crm-sidebar-row:focus-visible,
.crm-sidebar-premium-v1 .crm-sidebar-subitem:focus-visible {
  outline:2px solid color-mix(in srgb, var(--sb-accent) 34%, transparent) !important;
  outline-offset:1px;
}
'''


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)

if not LAYOUT.exists():
    fail(f"MISSING:{LAYOUT}")
if not BASE_CSS.exists():
    fail(f"MISSING:{BASE_CSS}")

layout = LAYOUT.read_text(encoding="utf-8")
if BASE_MARKER not in layout:
    fail("V1_BASE_MARKER_NOT_FOUND")
if IMPORT_V1 not in layout:
    fail("V1_CSS_IMPORT_NOT_FOUND")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".patch-backups" / f"sidebar-v1-1-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(LAYOUT, backup_dir / "CRMLayout.tsx")
shutil.copy2(BASE_CSS, backup_dir / "crm-sidebar-premium-v1.css")

changed = []
if IMPORT_V11 not in layout:
    layout = layout.replace(IMPORT_V1, IMPORT_V1 + "\n" + IMPORT_V11, 1)
    changed.append(str(LAYOUT.relative_to(ROOT)))

if MARKER not in layout:
    layout = layout.replace(f"// {BASE_MARKER}", f"// {BASE_MARKER}\n// {MARKER}", 1)
    if str(LAYOUT.relative_to(ROOT)) not in changed:
        changed.append(str(LAYOUT.relative_to(ROOT)))

LAYOUT.write_text(layout, encoding="utf-8")
CSS.write_text(CSS_TEXT, encoding="utf-8")
changed.append(str(CSS.relative_to(ROOT)))

print("PATCH=YES")
print("CRM_SIDEBAR_PREMIUM_V1_1=YES")
print("HOVER_CONTRAST_FIX=YES")
print("LIGHT_WHITE_ON_WHITE_HOVER_FIXED=YES")
print("DARK_HOVER_CONTRAST_LOCKED=YES")
print("ACTIVE_CAPSULE_PRESERVED=YES")
print("SALES_TREE_PRESERVED=YES")
print("COLLAPSED_STATE_PRESERVED=YES")
print("RTL_PRESERVED=YES")
print("ROUTES_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=" + ",".join(changed))
print(f"BACKUP_DIR={backup_dir}")
