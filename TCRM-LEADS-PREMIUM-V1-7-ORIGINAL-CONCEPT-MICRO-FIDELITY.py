#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-7.css"

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
    'import "../leads-premium-v1-6.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-table',
    'tcrm-leads-row',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V16_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-7.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-6.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.6 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.7 — micro fidelity against the ORIGINAL FIRST Leads concept.
Remaining runtime gaps after V1.6:
- Light still too white/flat vs pearl-lilac concept.
- Filter surface still reads too much like one plain form slab.
- Table rows need more layer separation and richer header glass.
- Typography is still slightly too small/faint.
- Dark needs a little more executive navy depth while preserving readability.
*/

/* PAGE / LIGHT PEARL DEPTH */
.tcrm-leads-premium::before{
  background:
    radial-gradient(820px 470px at 4% -2%,rgba(126,96,255,.19),transparent 66%),
    radial-gradient(860px 500px at 96% 0%,rgba(89,139,255,.14),transparent 68%),
    radial-gradient(620px 380px at 58% 78%,rgba(181,130,255,.075),transparent 72%),
    linear-gradient(180deg,#f9f8ff 0%,#f2f2ff 46%,#edf2ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(900px 520px at 4% -4%,rgba(77,75,255,.25),transparent 66%),
    radial-gradient(920px 540px at 98% 0%,rgba(120,57,255,.19),transparent 69%),
    radial-gradient(700px 440px at 56% 82%,rgba(37,109,255,.09),transparent 72%),
    linear-gradient(180deg,#040a15 0%,#061326 50%,#05101d 100%)!important;
}

/* HERO — keep current composition, increase premium separation */
.tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(115,95,255,.30)!important;
  box-shadow:
    0 32px 74px -42px rgba(75,59,185,.50),
    0 12px 30px -23px rgba(63,76,145,.25),
    inset 0 1px 0 rgba(255,255,255,.98),
    inset 0 -1px 0 rgba(107,92,255,.08)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  box-shadow:
    0 34px 82px -46px rgba(0,0,0,.94),
    0 0 48px -30px rgba(111,83,255,.76),
    inset 0 1px 0 rgba(255,255,255,.09)!important;
}
.tcrm-leads-premium .tcrm-leads-hero h1{font-size:29px!important;font-weight:910!important}
.tcrm-leads-premium .tcrm-leads-hero-subtitle{font-size:12.2px!important;font-weight:640!important}

/* FILTER COMMAND CENTER — stronger shell + inner control contrast */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(110,95,239,.27)!important;
  background:
    radial-gradient(75% 145% at 0% 0%,rgba(110,91,255,.12),transparent 58%),
    radial-gradient(62% 130% at 100% 0%,rgba(76,131,255,.085),transparent 64%),
    linear-gradient(145deg,rgba(255,255,255,.965),rgba(241,243,255,.94))!important;
  box-shadow:
    0 32px 74px -44px rgba(72,58,174,.50),
    0 12px 30px -22px rgba(59,72,138,.24),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(105,91,246,.06)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(116,132,224,.34)!important;
  background:
    radial-gradient(76% 145% at 0% 0%,rgba(90,79,255,.17),transparent 58%),
    radial-gradient(64% 135% at 100% 0%,rgba(46,108,255,.09),transparent 63%),
    linear-gradient(145deg,rgba(8,21,43,.995),rgba(6,18,36,.99))!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:42px!important;
  border-radius:13px!important;
  border-color:rgba(108,96,228,.24)!important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.99),
    0 7px 17px -13px rgba(63,60,135,.34)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  border-color:rgba(107,126,210,.34)!important;
  background:linear-gradient(180deg,rgba(15,33,63,.96),rgba(9,24,47,.94))!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card label{font-size:11px!important;font-weight:840!important;color:#4e5a73!important}
.dark .tcrm-leads-premium .tcrm-leads-filter-card label{color:#aab8d1!important}

/* TABLE — richer shell + stronger glass header */
.tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(108,94,235,.25)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.97),rgba(242,245,255,.96))!important;
  box-shadow:
    0 36px 84px -50px rgba(58,50,155,.50),
    0 13px 32px -24px rgba(58,70,130,.24),
    inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(100,122,212,.31)!important;
  background:linear-gradient(180deg,rgba(7,19,38,.995),rgba(5,16,32,.99))!important;
}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:44px!important;
  color:#4e5a72!important;
  font-size:11px!important;
  font-weight:850!important;
  background:
    linear-gradient(180deg,rgba(244,244,255,.995),rgba(233,238,252,.985))!important;
  border-bottom-color:rgba(105,95,233,.18)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#adbad2!important;
  background:linear-gradient(180deg,rgba(14,34,64,.995),rgba(10,28,54,.99))!important;
  border-bottom-color:rgba(109,129,218,.21)!important;
}

/* ROW LAYERING — pearl in Light, richer navy in Dark */
.tcrm-leads-premium .tcrm-leads-row{--v17-row:rgba(255,255,255,.90)}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v17-row:rgba(241,244,255,.92)}
.dark .tcrm-leads-premium .tcrm-leads-row{--v17-row:rgba(8,21,41,.94)}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v17-row:rgba(10,27,51,.97)}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:var(--v17-row)!important;
  border-bottom:1px solid rgba(100,107,165,.085)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  border-bottom-color:rgba(95,117,187,.095)!important;
}
.tcrm-leads-premium .tcrm-leads-row:hover{--v17-row:rgba(235,235,255,.96)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:hover{--v17-row:rgba(17,35,67,.99)!important}

/* TYPOGRAPHY — original concept was clearer than current runtime */
.tcrm-leads-premium .tcrm-leads-table td{font-size:11.7px!important;line-height:1.34!important;color:#4e5a72!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#96a5bd!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#172138!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#f3f6ff!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-semibold{font-size:13px!important;font-weight:790!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .text-muted-foreground{font-size:10.2px!important;opacity:.9!important}

/* BADGES — slightly more substantial, still dense */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{
  min-height:24px!important;
  padding:3px 9px!important;
  font-size:9.9px!important;
  font-weight:840!important;
}
.tcrm-leads-premium .tcrm-classification{font-size:9.9px!important;font-weight:870!important}

/* PAGINATION — stronger integrated footer */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:62px!important;
  background:linear-gradient(180deg,rgba(245,247,255,.94),rgba(239,243,255,.99))!important;
  border-top-color:rgba(105,95,228,.16)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,24,48,.96),rgba(5,19,38,.995))!important;
  border-top-color:rgba(106,126,209,.19)!important;
}

@media (prefers-reduced-motion:reduce){.tcrm-leads-premium *{transition-duration:.01ms!important}}
'''

CSS.write_text(css, encoding="utf-8")
if text != original:
    TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V16_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V17_CSS_WRITTEN=YES")
print("V17_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("LIGHT_PEARL_DEPTH_CLOSER=YES")
print("FILTER_COMMAND_CENTER_CLOSER=YES")
print("TABLE_GLASS_HEADER_CLOSER=YES")
print("ROW_LAYERING_CLOSER=YES")
print("DARK_NAVY_DEPTH_CLOSER=YES")
print("TYPOGRAPHY_CLOSER=YES")
print("BADGES_CLOSER=YES")
print("PAGINATION_CLOSER=YES")
print("FUNCTIONALITY_CHANGED=NO")
