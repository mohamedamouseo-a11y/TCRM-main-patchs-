#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-1.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

required_v1 = [
    'import "../leads-premium-v1.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-total-card',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-row',
]
missing = [x for x in required_v1 if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V1_REQUIRED_MISSING:" + ",".join(missing))

# Final polish stylesheet import — idempotent.
css_import = 'import "../leads-premium-v1-1.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1.css";'
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

# Replace the old count subtitle with the approved workspace subtitle.
# Total count remains visible in the dedicated Total Leads card.
old_subtitle = '''            <p className="text-white/70 text-sm mt-0.5">\n              {data?.total ?? 0} {t("count")}\n            </p>'''
new_subtitle = '''            <p className="text-white/70 text-sm mt-0.5 tcrm-leads-hero-subtitle">\n              {isRTL ? "إدارة ومتابعة جميع العملاء المحتملين" : "Manage and track all your sales leads"}\n            </p>'''
if "tcrm-leads-hero-subtitle" not in text:
    if old_subtitle not in text:
        raise SystemExit("ERROR=Could not locate Leads hero subtitle")
    text = text.replace(old_subtitle, new_subtitle, 1)

css = r'''/* TCRM Leads Premium V1.1 — final polish only */

/* Hero copy hierarchy */
.tcrm-leads-premium .tcrm-leads-hero-subtitle{
  margin-top:6px!important;
  max-width:430px;
  font-size:11px!important;
  line-height:1.35!important;
  font-weight:600!important;
  letter-spacing:.005em;
  color:#727b92!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero-subtitle{
  color:#b2c0dc!important;
}

/* Light mode: stronger pearl depth without making the workspace heavy */
.tcrm-leads-premium .tcrm-leads-hero{
  box-shadow:
    0 22px 58px -34px rgba(75,59,190,.34),
    0 8px 24px -20px rgba(55,65,145,.22),
    inset 0 1px 0 rgba(255,255,255,.92)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card{
  background:
    radial-gradient(circle at 8% 0%,rgba(124,58,237,.045),transparent 24rem),
    linear-gradient(145deg,rgba(255,255,255,.985),rgba(248,249,255,.955))!important;
  border-color:rgba(99,102,241,.17)!important;
  box-shadow:
    0 24px 56px -38px rgba(63,55,160,.34),
    0 8px 24px -22px rgba(63,72,140,.22),
    inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(99,102,241,.16)!important;
  box-shadow:
    0 28px 68px -44px rgba(55,52,150,.36),
    0 10px 26px -24px rgba(65,75,135,.22),
    inset 0 1px 0 rgba(255,255,255,.9)!important;
}

/* Keep Dark exactly in the established navy/glass direction */
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  background:linear-gradient(145deg,rgba(10,25,48,.97),rgba(8,22,42,.94))!important;
  border-color:rgba(104,126,219,.25)!important;
  box-shadow:0 26px 62px -40px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.045)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(103,126,225,.22)!important;
  box-shadow:0 28px 68px -44px rgba(0,0,0,.94),inset 0 1px 0 rgba(255,255,255,.035)!important;
}

/* Row/sticky-column consistency — sticky cells must visually belong to their row */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td{
  background:var(--leads-row)!important;
  transition:background-color .16s ease,border-color .16s ease,box-shadow .16s ease;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td{
  background:color-mix(in srgb,var(--leads-row) 72%,transparent)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  background:var(--leads-row-hover)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky{
  background:var(--leads-row)!important;
  background-clip:padding-box!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td.sticky{
  background:color-mix(in srgb,var(--leads-row) 72%,transparent)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td.sticky{
  background:var(--leads-row-hover)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky{
  border-bottom-color:rgba(94,116,180,.10)!important;
}

/* Table header depth and separation */
.tcrm-leads-premium .tcrm-leads-table-head > th{
  box-shadow:inset 0 -1px 0 rgba(99,102,241,.10);
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  box-shadow:inset 0 -1px 0 rgba(130,145,220,.14);
}

/* Compact action rail: closer to the approved concept */
.tcrm-leads-premium .tcrm-leads-actions{
  gap:2px!important;
  align-items:center;
}
.tcrm-leads-premium .tcrm-leads-actions button{
  height:28px!important;
  min-height:28px!important;
  border-radius:8px!important;
  padding-left:8px!important;
  padding-right:8px!important;
  box-shadow:none!important;
  border:1px solid transparent!important;
  background:transparent!important;
}
.tcrm-leads-premium .tcrm-leads-actions button:hover{
  background:rgba(99,102,241,.07)!important;
  border-color:rgba(99,102,241,.12)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions button{
  color:#c6d1e8!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions button:hover{
  color:#fff!important;
  background:rgba(99,102,241,.13)!important;
  border-color:rgba(118,126,255,.22)!important;
}

/* Small density polish while preserving the same number of visible rows */
.tcrm-leads-premium .tcrm-leads-table td{
  padding-top:10px!important;
  padding-bottom:10px!important;
}
.tcrm-leads-premium .tcrm-leads-table .tcrm-leads-th{
  padding-top:11px!important;
  padding-bottom:11px!important;
}

/* Campaign re-engagement note: keep it premium in Dark too */
.dark .tcrm-leads-premium .tcrm-leads-table td .border-amber-200.bg-amber-50{
  background:rgba(120,82,16,.18)!important;
  border-color:rgba(245,158,11,.38)!important;
  color:#f9c86b!important;
}

/* Pagination should read as the table footer, not a separate widget */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  border-top-color:rgba(99,102,241,.12)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  border-top-color:rgba(108,127,204,.15)!important;
}

@media (max-width:900px){
  .tcrm-leads-premium .tcrm-leads-hero-subtitle{max-width:100%;}
}
'''

CSS.write_text(css, encoding="utf-8")

if text != original:
    TSX.write_text(text, encoding="utf-8")

required_final = [
    css_import,
    "tcrm-leads-hero-subtitle",
    "tcrm-leads-premium",
    "tcrm-leads-filter-card",
    "tcrm-leads-table-card",
]
missing_final = [x for x in required_final if x not in text]
if missing_final:
    raise SystemExit("ERROR=FINAL_POLISH_HOOKS_MISSING:" + ",".join(missing_final))

print("PATCH=YES")
print("V1_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V11_CSS_WRITTEN=YES")
print("V11_CSS_IMPORTED=YES")
print("HERO_SUBTITLE_FIXED=YES")
print("ROW_SURFACES_FIXED=YES")
print("LIGHT_DEPTH_POLISHED=YES")
print("ACTIONS_POLISHED=YES")
print("FUNCTIONALITY_CHANGED=NO")
