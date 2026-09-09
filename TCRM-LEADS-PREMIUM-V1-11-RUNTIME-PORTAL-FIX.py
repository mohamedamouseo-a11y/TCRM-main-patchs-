#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-11.css"
SRC = ROOT / "client/src"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required = [
    'import "../leads-premium-v1-10.css";',
    'tcrm-leads-premium',
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V110_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-11.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-10.css";'
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

if text != original:
    TSX.write_text(text, encoding="utf-8")

# Runtime screenshot proved the audit marker still exists somewhere in client/src.
# Remove ONLY the exact audit comment marker, wherever it actually lives.
marker_core = r'SMART_SEARCH_AUDIT_EXEMPT\s*:\s*specialized\s+campaign\s+selector\s*,\s*not\s+the\s+primary\s+free-text\s+entity\s+search'
jsx_comment = re.compile(r'\{\s*/\*\s*' + marker_core + r'\s*\*/\s*\}', re.I | re.S)
raw_comment = re.compile(r'/\*\s*' + marker_core + r'\s*\*/', re.I | re.S)

removed = 0
changed_marker_files = []
for p in SRC.rglob('*'):
    if p.suffix not in {'.tsx', '.ts', '.jsx', '.js'} or not p.is_file():
        continue
    s = p.read_text(encoding='utf-8', errors='ignore')
    if 'SMART_SEARCH_AUDIT_EXEMPT' not in s:
        continue
    s2, n1 = jsx_comment.subn('', s)
    s3, n2 = raw_comment.subn('', s2)
    if n1 + n2:
        p.write_text(s3, encoding='utf-8')
        removed += n1 + n2
        changed_marker_files.append(str(p.relative_to(ROOT)))

css = r'''/* TCRM Leads Premium V1.11 — runtime portal fidelity + audit text hard fix.
   Original FIRST Leads concept remains the visual reference.
   Radix/Command portals render outside the Leads page wrapper, so this layer uses body:has(.tcrm-leads-premium)
   to style ONLY portal surfaces while the Leads screen is mounted.
*/

/* ===== PORTAL SURFACE ===== */
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] > div,
body:has(.tcrm-leads-premium) .tcrm-leads-select-content,
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{
  border:1px solid rgba(105,93,225,.22)!important;
  border-radius:16px!important;
  background:
    radial-gradient(120% 100% at 0% 0%,rgba(120,96,255,.08),transparent 48%),
    linear-gradient(155deg,rgba(255,255,255,.985),rgba(246,246,255,.975))!important;
  box-shadow:
    0 26px 58px -30px rgba(49,45,116,.45),
    0 12px 24px -18px rgba(59,65,127,.22),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
  backdrop-filter:blur(22px) saturate(1.12)!important;
  overflow:hidden!important;
}
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] > div,
.dark body:has(.tcrm-leads-premium) .tcrm-leads-select-content,
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{
  border-color:rgba(111,126,213,.30)!important;
  background:
    radial-gradient(120% 100% at 0% 0%,rgba(93,78,255,.14),transparent 50%),
    linear-gradient(155deg,rgba(11,27,52,.985),rgba(7,20,40,.99))!important;
  box-shadow:
    0 30px 64px -32px rgba(0,0,0,.88),
    0 0 34px -24px rgba(91,78,255,.46),
    inset 0 1px 0 rgba(255,255,255,.055)!important;
}

/* ===== SELECT / COMMAND ITEMS ===== */
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"],
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-item],
body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"],
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content [cmdk-item]{
  min-height:36px!important;
  margin:2px 5px!important;
  padding:7px 10px!important;
  border-radius:10px!important;
  font-size:12px!important;
  font-weight:620!important;
  color:#3f4960!important;
  transition:background-color .14s ease,color .14s ease,box-shadow .14s ease!important;
}
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"],
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-item]{
  color:#c7d1e5!important;
}
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"][data-highlighted],
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-item][data-selected="true"]{
  background:linear-gradient(90deg,rgba(106,91,255,.12),rgba(77,126,255,.07))!important;
  color:#28244f!important;
  box-shadow:inset 0 0 0 1px rgba(107,93,232,.10)!important;
}
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"][data-highlighted],
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-item][data-selected="true"]{
  background:linear-gradient(90deg,rgba(108,91,255,.19),rgba(56,111,255,.10))!important;
  color:#fff!important;
  box-shadow:inset 0 0 0 1px rgba(120,107,255,.16)!important;
}
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"][data-state="checked"]{
  background:linear-gradient(90deg,rgba(108,92,255,.14),rgba(81,126,255,.08))!important;
  color:#26234e!important;
  font-weight:760!important;
}
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [role="option"][data-state="checked"]{
  background:linear-gradient(90deg,rgba(113,93,255,.23),rgba(58,110,255,.12))!important;
  color:#fff!important;
}

/* ===== COMMAND SEARCH ===== */
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-input-wrapper]{
  margin:7px!important;
  border:1px solid rgba(104,94,220,.14)!important;
  border-radius:11px!important;
  background:rgba(248,248,255,.86)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.dark body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-input-wrapper]{
  border-color:rgba(106,124,205,.20)!important;
  background:rgba(8,24,47,.72)!important;
}
body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] [cmdk-input]{
  min-height:38px!important;
  font-size:12px!important;
}

/* ===== COLUMNS POPOVER ===== */
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{
  padding:12px!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content h4,
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content [class*="font-medium"]{
  color:#202840!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content h4,
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content [class*="font-medium"]{
  color:#f3f6ff!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content label,
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content [class*="rounded"]:has([role="checkbox"]){
  border-color:rgba(103,93,213,.13)!important;
  border-radius:11px!important;
  background:rgba(249,249,255,.70)!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content label,
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content [class*="rounded"]:has([role="checkbox"]){
  border-color:rgba(104,123,203,.18)!important;
  background:rgba(10,27,52,.62)!important;
}

/* Keep portal width intentional, not browser-default narrow. */
body:has(.tcrm-leads-premium) .tcrm-leads-select-content{min-width:var(--radix-select-trigger-width)!important;max-width:min(360px,calc(100vw - 24px))!important}
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{max-width:min(380px,calc(100vw - 24px))!important}

@media (prefers-reduced-motion:reduce){
  body:has(.tcrm-leads-premium) [data-radix-popper-content-wrapper] *{transition-duration:.01ms!important}
}
'''

CSS.write_text(css, encoding='utf-8')

# Final source-level verification for the runtime leak.
remaining = []
for p in SRC.rglob('*'):
    if p.suffix in {'.tsx', '.ts', '.jsx', '.js'} and p.is_file():
        s = p.read_text(encoding='utf-8', errors='ignore')
        if 'SMART_SEARCH_AUDIT_EXEMPT' in s:
            remaining.append(str(p.relative_to(ROOT)))

print('PATCH=YES')
print('V110_BASE=YES')
print('TSX_CHANGED=' + ('YES' if text != original else 'NO'))
print('V111_CSS_WRITTEN=YES')
print('V111_CSS_IMPORTED=YES')
print('AUDIT_MARKERS_REMOVED=' + str(removed))
print('AUDIT_MARKER_SOURCE_CLEAR=' + ('YES' if not remaining else 'NO'))
print('AUDIT_MARKER_REMAINING_FILES=' + (','.join(remaining) if remaining else 'NONE'))
print('PORTAL_RUNTIME_SCOPING=YES')
print('DROPDOWN_GLASS_UPGRADED=YES')
print('COLUMNS_POPOVER_UPGRADED=YES')
print('FUNCTIONALITY_CHANGED=NO')
