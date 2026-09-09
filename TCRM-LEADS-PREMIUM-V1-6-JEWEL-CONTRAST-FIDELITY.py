#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-6.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from the EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1.css";',
    'import "../leads-premium-v1-1.css";',
    'import "../leads-premium-v1-2.css";',
    'import "../leads-premium-v1-3.css";',
    'import "../leads-premium-v1-4.css";',
    'import "../leads-premium-v1-5.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-total-card',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-table',
    'tcrm-leads-row',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V15_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-6.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-5.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.5 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.6 — jewel contrast fidelity pass against ORIGINAL FIRST Leads concept */

/* 1) Stronger page hierarchy without changing density */
.tcrm-leads-premium{
  --v16-jewel:#6f63ff;
  --v16-indigo:#4f5cf7;
  --v16-pearl:#f4f3ff;
  --v16-ink:#172036;
}
.tcrm-leads-premium::before{
  background:
    radial-gradient(780px 440px at 6% 0%,rgba(119,94,255,.16),transparent 66%),
    radial-gradient(820px 460px at 94% 2%,rgba(74,130,255,.12),transparent 68%),
    linear-gradient(180deg,#fafaff 0%,#f4f4ff 48%,#eff3ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(860px 500px at 6% -4%,rgba(73,72,255,.23),transparent 65%),
    radial-gradient(880px 520px at 96% 0%,rgba(118,54,255,.17),transparent 68%),
    linear-gradient(180deg,#050b17 0%,#061426 48%,#06111e 100%)!important;
}

/* 2) Hero KPI should read as a jewel, not another white mini-card */
.tcrm-leads-premium .tcrm-leads-total-card{
  min-width:108px!important;
  height:60px!important;
  border:1px solid rgba(105,93,255,.32)!important;
  background:
    radial-gradient(circle at 24% 18%,rgba(255,255,255,.74),transparent 28%),
    linear-gradient(145deg,rgba(108,91,255,.96),rgba(79,92,247,.94) 58%,rgba(116,73,225,.92))!important;
  box-shadow:
    0 16px 34px -18px rgba(84,69,215,.62),
    0 0 24px -14px rgba(103,89,255,.55),
    inset 0 1px 0 rgba(255,255,255,.55),
    inset 0 -1px 0 rgba(39,32,121,.18)!important;
}
.tcrm-leads-premium .tcrm-leads-total-card strong,
.tcrm-leads-premium .tcrm-leads-total-card span{color:#fff!important;text-shadow:0 1px 12px rgba(31,24,93,.22)!important}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:21px!important}
.tcrm-leads-premium .tcrm-leads-total-card span{opacity:.86!important}
.dark .tcrm-leads-premium .tcrm-leads-total-card{
  border-color:rgba(136,119,255,.45)!important;
  background:
    radial-gradient(circle at 25% 18%,rgba(255,255,255,.13),transparent 26%),
    linear-gradient(145deg,rgba(74,68,225,.88),rgba(51,59,178,.90) 55%,rgba(91,43,174,.88))!important;
  box-shadow:0 18px 38px -20px rgba(0,0,0,.82),0 0 28px -16px rgba(104,87,255,.78),inset 0 1px 0 rgba(255,255,255,.15)!important;
}

/* 3) Filter Command Center — stronger glass capsules and visible grouping */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(111,96,241,.24)!important;
  background:
    radial-gradient(64% 120% at 0% 0%,rgba(108,90,255,.105),transparent 58%),
    radial-gradient(55% 110% at 100% 0%,rgba(75,126,255,.07),transparent 62%),
    linear-gradient(145deg,rgba(255,255,255,.97),rgba(245,246,255,.94))!important;
  box-shadow:
    0 28px 66px -42px rgba(75,61,181,.46),
    0 10px 28px -22px rgba(61,73,142,.22),
    inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(113,130,221,.31)!important;
  background:
    radial-gradient(70% 140% at 0% 0%,rgba(86,77,255,.15),transparent 58%),
    radial-gradient(60% 130% at 100% 0%,rgba(44,105,255,.08),transparent 62%),
    linear-gradient(145deg,rgba(8,21,42,.99),rgba(7,19,38,.985))!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{
  padding:18px!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:41px!important;
  border-radius:13px!important;
  border-color:rgba(111,99,225,.22)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.985),rgba(246,246,255,.92))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.98),0 6px 14px -12px rgba(70,62,145,.34)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  background:linear-gradient(180deg,rgba(14,31,59,.94),rgba(10,24,47,.90))!important;
  border-color:rgba(104,124,206,.31)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card label{font-size:10.8px!important;font-weight:830!important}

/* 4) Table workspace — stronger premium shell and pearl rows in Light */
.tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(109,96,235,.22)!important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.975),rgba(246,248,255,.955))!important;
  box-shadow:
    0 34px 80px -50px rgba(60,52,157,.48),
    0 11px 30px -24px rgba(62,72,131,.22),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(99,121,210,.28)!important;
  background:linear-gradient(180deg,rgba(7,19,37,.99),rgba(6,18,35,.985))!important;
}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#59657d!important;
  font-size:10.8px!important;
  font-weight:840!important;
  background:linear-gradient(180deg,rgba(246,246,255,.99),rgba(237,241,252,.97))!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#a7b5ce!important;
  background:linear-gradient(180deg,rgba(13,32,61,.99),rgba(10,27,53,.985))!important;
}

.tcrm-leads-premium .tcrm-leads-row{--v16-row:rgba(255,255,255,.86)}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v16-row:rgba(245,247,255,.88)}
.dark .tcrm-leads-premium .tcrm-leads-row{--v16-row:rgba(9,22,42,.90)}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v16-row:rgba(11,27,50,.94)}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:var(--v16-row)!important;
  border-bottom-color:rgba(99,105,163,.075)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  border-bottom-color:rgba(95,116,183,.085)!important;
}

/* Soft luminous hover only */
.tcrm-leads-premium .tcrm-leads-row:hover{--v16-row:rgba(239,239,255,.94)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:hover{--v16-row:rgba(17,35,66,.97)!important}
.tcrm-leads-premium .tcrm-leads-row:hover > td{box-shadow:inset 0 1px 0 rgba(112,95,255,.07),inset 0 -1px 0 rgba(112,95,255,.05)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:hover > td{box-shadow:inset 0 1px 0 rgba(118,106,255,.10),inset 0 -1px 0 rgba(118,106,255,.07)!important}

/* 5) Lead identity / readability */
.tcrm-leads-premium .tcrm-leads-table td{font-size:11.3px!important;color:#556077!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#8f9eb7!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#182239!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#f1f5ff!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-semibold{font-size:12.8px!important;font-weight:780!important}
.tcrm-leads-premium .tcrm-leads-avatar{
  width:31px!important;height:31px!important;
  box-shadow:0 6px 16px -8px rgba(73,55,188,.58),0 0 0 2px rgba(105,91,246,.10),inset 0 1px 0 rgba(255,255,255,.28)!important;
}

/* 6) Jewel badge grammar */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{
  min-height:23px!important;
  padding:3px 9px!important;
  border-radius:999px!important;
  border-width:1px!important;
  font-size:9.7px!important;
  font-weight:830!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.32),0 5px 13px -9px currentColor!important;
}
.tcrm-leads-premium .tcrm-classification{font-size:9.7px!important;font-weight:860!important}

/* 7) Hero action buttons should match jewel hierarchy */
.tcrm-leads-premium .tcrm-leads-hero-actions>button,
.tcrm-leads-premium .tcrm-leads-hero-actions>a button{
  height:41px!important;
  border-radius:12px!important;
  font-weight:820!important;
  box-shadow:0 12px 26px -18px rgba(64,55,160,.46)!important;
}

/* 8) Pagination integrated glass footer */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:60px!important;
  background:linear-gradient(180deg,rgba(247,249,255,.92),rgba(243,246,255,.98))!important;
  border-top-color:rgba(104,94,226,.14)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,24,47,.94),rgba(6,20,40,.99))!important;
  border-top-color:rgba(103,122,204,.17)!important;
}

@media (prefers-reduced-motion:reduce){.tcrm-leads-premium *{transition-duration:.01ms!important}}
'''

CSS.write_text(css, encoding="utf-8")
if text != original:
    TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V15_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V16_CSS_WRITTEN=YES")
print("V16_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("TOTAL_KPI_JEWELIZED=YES")
print("FILTER_COMMAND_CENTER_DEEPENED=YES")
print("LIGHT_PEARL_ROWS_UPGRADED=YES")
print("DARK_ROW_DEPTH_UPGRADED=YES")
print("STICKY_SURFACES_UNIFIED=YES")
print("TABLE_READABILITY_UPGRADED=YES")
print("BADGE_JEWEL_SYSTEM=YES")
print("HERO_ACTIONS_POLISHED=YES")
print("PAGINATION_GLASS_INTEGRATED=YES")
print("FUNCTIONALITY_CHANGED=NO")
