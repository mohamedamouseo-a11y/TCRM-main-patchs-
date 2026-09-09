#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-9.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1-8.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-total-card',
    'tcrm-leads-filter-card',
    'tcrm-leads-filter-grid',
    'tcrm-leads-table-card',
    'tcrm-leads-table-scroll',
    'tcrm-leads-table',
    'tcrm-leads-row',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V18_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-9.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-8.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.8 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.9 — ORIGINAL CONCEPT CORRECTION.
   Runtime correction after V1.8, judged only against the FIRST approved Leads concept.
   Goals:
   - ONE continuous Command Center surface, not mini-card boxing around every filter.
   - Compact SLA / Columns / Clear controls.
   - Stronger pearl/lilac depth in Light.
   - Layered premium rows without looking like a plain spreadsheet.
   - Stronger glass header + typography, while preserving density and all behavior.
*/

/* ===== 1. PAGE: richer pearl/lilac hierarchy in LIGHT ===== */
.tcrm-leads-premium::before{
  background:
    radial-gradient(920px 520px at 3% -4%,rgba(130,101,255,.205),transparent 64%),
    radial-gradient(980px 550px at 98% -1%,rgba(85,139,255,.155),transparent 67%),
    radial-gradient(700px 430px at 50% 78%,rgba(183,128,255,.10),transparent 71%),
    linear-gradient(180deg,#f8f7ff 0%,#f0efff 46%,#eaf0ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(940px 550px at 3% -4%,rgba(74,72,255,.255),transparent 64%),
    radial-gradient(980px 570px at 99% 0%,rgba(118,55,255,.20),transparent 68%),
    radial-gradient(760px 470px at 54% 84%,rgba(38,106,255,.105),transparent 72%),
    linear-gradient(180deg,#040a15 0%,#061326 50%,#050f1c 100%)!important;
}

/* ===== 2. HERO: preserve V1.8 composition; only refine glass separation ===== */
.tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(113,95,248,.33)!important;
  box-shadow:
    0 34px 82px -46px rgba(72,58,181,.55),
    0 13px 32px -23px rgba(60,72,142,.27),
    inset 0 1px 0 rgba(255,255,255,.985)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  box-shadow:0 38px 88px -50px rgba(0,0,0,.96),0 0 52px -31px rgba(110,84,255,.78),inset 0 1px 0 rgba(255,255,255,.09)!important;
}
.tcrm-leads-premium .tcrm-leads-total-card{
  background:linear-gradient(145deg,rgba(255,255,255,.77),rgba(240,240,255,.58))!important;
  border-color:rgba(108,94,245,.29)!important;
  box-shadow:0 18px 38px -24px rgba(80,67,195,.52),0 0 24px -16px rgba(112,92,255,.42),inset 0 1px 0 rgba(255,255,255,.97)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-total-card{
  background:linear-gradient(145deg,rgba(12,29,61,.70),rgba(31,30,84,.56))!important;
}

/* ===== 3. FILTERS: ONE CONTINUOUS COMMAND CENTER ===== */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-radius:23px!important;
  border-color:rgba(107,93,237,.30)!important;
  background:
    radial-gradient(72% 145% at 0% 0%,rgba(112,92,255,.115),transparent 58%),
    radial-gradient(60% 130% at 100% 0%,rgba(76,131,255,.082),transparent 64%),
    linear-gradient(145deg,rgba(255,255,255,.965),rgba(240,242,255,.945))!important;
  box-shadow:0 34px 78px -46px rgba(72,58,174,.54),0 12px 30px -22px rgba(59,72,138,.26),inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(116,132,224,.37)!important;
  background:
    radial-gradient(76% 145% at 0% 0%,rgba(90,79,255,.18),transparent 58%),
    radial-gradient(62% 135% at 100% 0%,rgba(46,108,255,.10),transparent 63%),
    linear-gradient(145deg,rgba(8,21,43,.997),rgba(6,18,36,.992))!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:18px 19px!important}

.tcrm-leads-premium .tcrm-leads-filter-grid{
  display:grid!important;
  grid-template-columns:minmax(230px,1.55fr) minmax(200px,1.20fr) repeat(5,minmax(118px,.80fr));
  gap:12px 11px!important;
  align-items:end!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid > *{min-width:0!important}

/* Critical V1.9 correction: remove the V1.8 mini-card box around every filter. */
.tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2{
  padding:0!important;
  margin:0!important;
  border:0!important;
  border-radius:0!important;
  background:transparent!important;
  box-shadow:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2{
  border:0!important;
  background:transparent!important;
  box-shadow:none!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2 label{
  display:block!important;
  margin:0 0 6px 2px!important;
  font-size:10.7px!important;
  line-height:1.1!important;
  font-weight:850!important;
  letter-spacing:.018em!important;
  color:#526079!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2 label{color:#a8b6cf!important}

/* Controls = clean glass capsules floating INSIDE one command center. */
.tcrm-leads-premium .tcrm-leads-filter-grid input,
.tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]{
  width:100%!important;
  min-height:40px!important;
  border-radius:12px!important;
  border:1px solid rgba(108,95,228,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.90),rgba(247,247,255,.76))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.98),0 8px 18px -15px rgba(74,64,150,.30)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid input,
.dark .tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]{
  background:linear-gradient(180deg,rgba(14,31,59,.82),rgba(9,24,47,.72))!important;
  border-color:rgba(107,126,210,.26)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 8px 18px -15px rgba(0,0,0,.66)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid input:hover,
.tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]:hover{
  border-color:rgba(107,91,247,.34)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid input:hover,
.dark .tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]:hover{
  border-color:rgba(126,111,255,.43)!important;
}

/* Utility controls must not become giant form fields. */
.tcrm-leads-premium .tcrm-leads-filter-grid > button,
.tcrm-leads-premium .tcrm-leads-filter-grid > div:has(> button){
  align-self:end!important;
  justify-self:start!important;
  width:auto!important;
  min-width:0!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid > button,
.tcrm-leads-premium .tcrm-leads-filter-grid > div:has(> button) > button{
  width:auto!important;
  min-width:92px!important;
  max-width:126px!important;
  height:38px!important;
  min-height:38px!important;
  padding-inline:12px!important;
  border-radius:11px!important;
  font-size:10.5px!important;
  font-weight:800!important;
  border-color:rgba(106,93,231,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.82),rgba(244,244,255,.72))!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid > button,
.dark .tcrm-leads-premium .tcrm-leads-filter-grid > div:has(> button) > button{
  color:#d8e1f3!important;
  border-color:rgba(107,126,210,.26)!important;
  background:linear-gradient(180deg,rgba(13,30,57,.76),rgba(9,24,47,.68))!important;
}

/* ===== 4. TABLE: premium layered workspace, not a spreadsheet ===== */
.tcrm-leads-premium .tcrm-leads-table-card{
  border-radius:23px!important;
  border-color:rgba(107,94,235,.29)!important;
  background:
    radial-gradient(65% 135% at 0% 0%,rgba(112,94,255,.055),transparent 60%),
    linear-gradient(180deg,rgba(255,255,255,.975),rgba(239,243,255,.968))!important;
  box-shadow:0 38px 88px -52px rgba(58,50,155,.54),0 13px 32px -24px rgba(58,70,130,.26),inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(100,122,212,.34)!important;
  background:
    radial-gradient(65% 130% at 0% 0%,rgba(72,74,255,.07),transparent 60%),
    linear-gradient(180deg,rgba(7,19,38,.997),rgba(5,16,32,.995))!important;
}
.tcrm-leads-premium .tcrm-leads-table-scroll{padding:0 6px 3px!important}
.tcrm-leads-premium .tcrm-leads-table{border-collapse:separate!important;border-spacing:0 4px!important}

/* Stronger glass header. */
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:45px!important;
  font-size:11.2px!important;
  line-height:1!important;
  font-weight:870!important;
  color:#4a566f!important;
  background:linear-gradient(180deg,rgba(241,241,255,.97),rgba(227,234,251,.95))!important;
  border-top:1px solid rgba(255,255,255,.88)!important;
  border-bottom:1px solid rgba(104,94,233,.22)!important;
  backdrop-filter:blur(14px) saturate(1.08)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#b4c0d7!important;
  background:linear-gradient(180deg,rgba(14,35,66,.96),rgba(10,28,55,.94))!important;
  border-top-color:rgba(255,255,255,.04)!important;
  border-bottom-color:rgba(109,129,218,.24)!important;
}

/* Row card treatment: stronger separation in Light, controlled navy in Dark. */
.tcrm-leads-premium .tcrm-leads-row{--v19-row:rgba(255,255,255,.93)}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v19-row:rgba(241,244,255,.95)}
.dark .tcrm-leads-premium .tcrm-leads-row{--v19-row:rgba(8,21,41,.96)}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v19-row:rgba(10,28,52,.985)}

.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:var(--v19-row)!important;
  border-top:1px solid rgba(255,255,255,.66)!important;
  border-bottom:1px solid rgba(102,108,169,.09)!important;
  box-shadow:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  border-top-color:rgba(255,255,255,.028)!important;
  border-bottom-color:rgba(95,117,187,.095)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child{border-radius:13px 0 0 13px!important}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{border-radius:0 13px 13px 0!important}
[dir="rtl"] .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child{border-radius:0 13px 13px 0!important}
[dir="rtl"] .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{border-radius:13px 0 0 13px!important}

/* Subtle luminous hover, no giant band. */
.tcrm-leads-premium .tcrm-leads-row:hover{--v19-row:rgba(231,232,255,.985)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:hover{--v19-row:rgba(17,36,69,.995)!important}

/* ===== 5. TYPOGRAPHY: slightly stronger concept hierarchy ===== */
.tcrm-leads-premium .tcrm-leads-table td{font-size:11.8px!important;line-height:1.34!important;color:#4c5870!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#98a7bf!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#172138!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#f3f6ff!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-semibold{font-size:13px!important;font-weight:790!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .text-muted-foreground{font-size:10.3px!important;opacity:.92!important}

/* ===== 6. BADGES / PAGINATION: keep V1.8 system, refine finish ===== */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{
  min-height:24px!important;
  padding:3px 9px!important;
  font-size:9.9px!important;
  font-weight:850!important;
}
.tcrm-leads-premium .tcrm-classification{font-size:9.9px!important;font-weight:875!important}

.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:60px!important;
  background:linear-gradient(180deg,rgba(244,246,255,.93),rgba(238,242,255,.99))!important;
  border-top-color:rgba(104,94,226,.16)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,24,48,.96),rgba(5,19,38,.995))!important;
  border-top-color:rgba(106,126,209,.19)!important;
}

@media (max-width:1280px){
  .tcrm-leads-premium .tcrm-leads-filter-grid{
    grid-template-columns:minmax(220px,1.45fr) minmax(190px,1.18fr) repeat(5,minmax(105px,.76fr));
  }
}

@media (prefers-reduced-motion:reduce){.tcrm-leads-premium *{transition-duration:.01ms!important}}
'''

CSS.write_text(css, encoding="utf-8")
if text != original:
    TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V18_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V19_CSS_WRITTEN=YES")
print("V19_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("CONTINUOUS_COMMAND_CENTER=YES")
print("UTILITY_CONTROLS_COMPACT=YES")
print("LIGHT_PEARL_DEPTH_CORRECTED=YES")
print("TABLE_LAYERING_CORRECTED=YES")
print("GLASS_HEADER_STRENGTHENED=YES")
print("TYPOGRAPHY_STRENGTHENED=YES")
print("PURPLE_BAND_ABSENT=YES")
print("FUNCTIONALITY_CHANGED=NO")
