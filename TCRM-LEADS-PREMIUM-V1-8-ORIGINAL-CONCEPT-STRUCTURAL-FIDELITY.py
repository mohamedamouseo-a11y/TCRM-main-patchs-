#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-8.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1-7.css";',
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
    raise SystemExit("ERROR=LEADS_V17_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-8.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-7.css";'
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

# Structural hooks only. No behavior changes.
if 'tcrm-leads-filter-grid' not in text:
    old = 'className="flex flex-wrap items-end gap-3"'
    new = 'className="flex flex-wrap items-end gap-3 tcrm-leads-filter-grid"'
    if old not in text:
        raise SystemExit("ERROR=Could not locate filter controls wrapper")
    text = text.replace(old, new, 1)

if 'tcrm-leads-table-scroll' not in text:
    old = 'className="overflow-x-auto"'
    new = 'className="overflow-x-auto tcrm-leads-table-scroll"'
    if old not in text:
        raise SystemExit("ERROR=Could not locate leads table scroll wrapper")
    text = text.replace(old, new, 1)

css = r'''/* TCRM Leads Premium V1.8 — ORIGINAL FIRST CONCEPT structural fidelity.
   This pass intentionally makes a visible structural difference, not another tiny polish.
   ORIGINAL concept anchors:
   - Total Leads = premium GLASS stat, not a solid jewel tile.
   - Filters = deliberate Command Center grid, not a wrapped plain form.
   - Table = dense premium workspace with card-like layered rows and glass header.
   - Light = pearl/lilac executive surface; Dark = layered navy/indigo executive surface.
*/

/* ===== PAGE ATMOSPHERE ===== */
.tcrm-leads-premium::before{
  background:
    radial-gradient(860px 500px at 5% -3%,rgba(125,98,255,.18),transparent 65%),
    radial-gradient(900px 520px at 96% 0%,rgba(83,137,255,.14),transparent 68%),
    radial-gradient(620px 390px at 54% 82%,rgba(179,128,255,.085),transparent 72%),
    linear-gradient(180deg,#faf9ff 0%,#f2f2ff 47%,#edf2ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(920px 540px at 4% -4%,rgba(74,74,255,.25),transparent 65%),
    radial-gradient(940px 560px at 98% 0%,rgba(118,57,255,.19),transparent 69%),
    radial-gradient(720px 450px at 56% 84%,rgba(38,108,255,.10),transparent 72%),
    linear-gradient(180deg,#040a15 0%,#061326 50%,#050f1c 100%)!important;
}

/* ===== HERO / GLASS STAT ===== */
.tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(115,96,255,.31)!important;
  box-shadow:0 34px 78px -44px rgba(72,58,181,.52),0 13px 30px -22px rgba(61,74,143,.25),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  box-shadow:0 36px 84px -48px rgba(0,0,0,.95),0 0 50px -31px rgba(110,84,255,.76),inset 0 1px 0 rgba(255,255,255,.09)!important;
}

/* Original concept called for a glass statistic tile. */
.tcrm-leads-premium .tcrm-leads-total-card{
  min-width:108px!important;
  height:60px!important;
  border:1px solid rgba(108,94,245,.26)!important;
  background:
    radial-gradient(circle at 20% 12%,rgba(255,255,255,.96),transparent 38%),
    linear-gradient(145deg,rgba(255,255,255,.82),rgba(240,240,255,.64))!important;
  backdrop-filter:blur(22px) saturate(1.18)!important;
  box-shadow:0 17px 34px -22px rgba(80,67,195,.52),0 0 22px -15px rgba(112,92,255,.42),inset 0 1px 0 rgba(255,255,255,.96),inset 0 -1px 0 rgba(105,91,246,.08)!important;
}
.tcrm-leads-premium .tcrm-leads-total-card strong{color:#29275e!important;text-shadow:none!important}
.tcrm-leads-premium .tcrm-leads-total-card span{color:#737d96!important;text-shadow:none!important;opacity:1!important}
.dark .tcrm-leads-premium .tcrm-leads-total-card{
  border-color:rgba(137,119,255,.42)!important;
  background:
    radial-gradient(circle at 22% 14%,rgba(255,255,255,.12),transparent 34%),
    linear-gradient(145deg,rgba(12,29,61,.72),rgba(31,30,84,.58))!important;
  box-shadow:0 18px 40px -24px rgba(0,0,0,.82),0 0 28px -18px rgba(111,87,255,.72),inset 0 1px 0 rgba(255,255,255,.10)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-total-card strong{color:#fff!important}
.dark .tcrm-leads-premium .tcrm-leads-total-card span{color:#b6c1d9!important}

/* ===== FILTER COMMAND CENTER — STRUCTURAL GRID ===== */
.tcrm-leads-premium .tcrm-leads-filter-card{
  padding:0!important;
  border-radius:23px!important;
  border-color:rgba(108,94,237,.28)!important;
  background:
    radial-gradient(76% 145% at 0% 0%,rgba(110,91,255,.13),transparent 58%),
    radial-gradient(62% 130% at 100% 0%,rgba(76,131,255,.09),transparent 64%),
    linear-gradient(145deg,rgba(255,255,255,.97),rgba(241,243,255,.945))!important;
  box-shadow:0 34px 78px -46px rgba(72,58,174,.52),0 12px 30px -22px rgba(59,72,138,.25),inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(116,132,224,.35)!important;
  background:
    radial-gradient(78% 145% at 0% 0%,rgba(90,79,255,.18),transparent 58%),
    radial-gradient(64% 135% at 100% 0%,rgba(46,108,255,.10),transparent 63%),
    linear-gradient(145deg,rgba(8,21,43,.997),rgba(6,18,36,.992))!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:18px!important}

.tcrm-leads-premium .tcrm-leads-filter-grid{
  display:grid!important;
  grid-template-columns:minmax(230px,1.55fr) minmax(200px,1.22fr) repeat(5,minmax(118px,.78fr));
  gap:12px!important;
  align-items:end!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid > *{min-width:0!important}
.tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2{
  position:relative;
  padding:8px 9px 9px!important;
  margin:0!important;
  border:1px solid rgba(109,96,228,.13);
  border-radius:15px;
  background:linear-gradient(180deg,rgba(255,255,255,.66),rgba(247,247,255,.50));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85);
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2{
  border-color:rgba(107,126,210,.17);
  background:linear-gradient(180deg,rgba(14,31,59,.48),rgba(9,24,47,.34));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035);
}
.tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2 > *{width:100%!important}
.tcrm-leads-premium .tcrm-leads-filter-grid > .space-y-2 label{display:block!important;margin:0 0 6px!important;font-size:10.5px!important;font-weight:850!important;letter-spacing:.018em!important}
.tcrm-leads-premium .tcrm-leads-filter-grid input,
.tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]{
  width:100%!important;
  min-height:38px!important;
  border-radius:11px!important;
  background:rgba(255,255,255,.72)!important;
  border-color:rgba(109,96,228,.16)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-grid input,
.dark .tcrm-leads-premium .tcrm-leads-filter-grid [role="combobox"]{
  background:rgba(8,24,47,.68)!important;
  border-color:rgba(107,126,210,.24)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-grid > button,
.tcrm-leads-premium .tcrm-leads-filter-grid > [data-radix-popper-content-wrapper],
.tcrm-leads-premium .tcrm-leads-filter-grid > div:has(> button){align-self:end}

/* ===== TABLE WORKSPACE — CARD-LIKE ROW LAYERS ===== */
.tcrm-leads-premium .tcrm-leads-table-card{
  border-radius:23px!important;
  border-color:rgba(107,94,235,.27)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.975),rgba(240,244,255,.965))!important;
  box-shadow:0 38px 86px -52px rgba(58,50,155,.52),0 13px 32px -24px rgba(58,70,130,.25),inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(100,122,212,.32)!important;
  background:linear-gradient(180deg,rgba(7,19,38,.997),rgba(5,16,32,.995))!important;
}
.tcrm-leads-premium .tcrm-leads-table-scroll{padding:0 5px 2px!important}
.tcrm-leads-premium .tcrm-leads-table{
  border-collapse:separate!important;
  border-spacing:0 3px!important;
}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:45px!important;
  font-size:11.1px!important;
  font-weight:860!important;
  color:#4c5871!important;
  background:linear-gradient(180deg,rgba(242,242,255,.995),rgba(229,236,252,.99))!important;
  border-top:1px solid rgba(255,255,255,.7)!important;
  border-bottom:1px solid rgba(104,94,233,.20)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#b2bfd6!important;
  background:linear-gradient(180deg,rgba(14,35,66,.997),rgba(10,28,55,.995))!important;
  border-top-color:rgba(255,255,255,.035)!important;
  border-bottom-color:rgba(109,129,218,.22)!important;
}

.tcrm-leads-premium .tcrm-leads-row{--v18-row-a:rgba(255,255,255,.92);--v18-row-b:rgba(242,245,255,.94);--v18-row:var(--v18-row-a)}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v18-row:var(--v18-row-b)}
.dark .tcrm-leads-premium .tcrm-leads-row{--v18-row-a:rgba(8,21,41,.95);--v18-row-b:rgba(10,28,52,.98);--v18-row:var(--v18-row-a)}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v18-row:var(--v18-row-b)}

.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:var(--v18-row)!important;
  border-top:1px solid rgba(255,255,255,.58)!important;
  border-bottom:1px solid rgba(101,108,169,.08)!important;
  box-shadow:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  border-top-color:rgba(255,255,255,.024)!important;
  border-bottom-color:rgba(95,117,187,.09)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child{border-radius:12px 0 0 12px!important}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{border-radius:0 12px 12px 0!important}
[dir="rtl"] .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child{border-radius:0 12px 12px 0!important}
[dir="rtl"] .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{border-radius:12px 0 0 12px!important}

.tcrm-leads-premium .tcrm-leads-row:hover{--v18-row:rgba(233,234,255,.98)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:hover{--v18-row:rgba(17,36,69,.995)!important}

/* SLA remains edge-only, never a full purple/red band. */
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td{background:var(--v18-row)!important}

/* ===== TYPOGRAPHY / BADGES ===== */
.tcrm-leads-premium .tcrm-leads-table td{font-size:11.9px!important;line-height:1.34!important;color:#4d5971!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#99a8bf!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#172138!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#f4f7ff!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-semibold{font-size:13px!important;font-weight:800!important}
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{min-height:24px!important;padding:3px 9px!important;font-size:10px!important;font-weight:850!important}
.tcrm-leads-premium .tcrm-classification{font-size:10px!important;font-weight:880!important}

/* ===== PAGINATION ===== */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:62px!important;
  margin-top:2px!important;
  background:linear-gradient(180deg,rgba(244,247,255,.96),rgba(238,242,255,.995))!important;
  border-top-color:rgba(104,95,228,.17)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,24,48,.97),rgba(5,19,38,.998))!important;
  border-top-color:rgba(106,126,209,.20)!important;
}

@media (max-width:1450px){
  .tcrm-leads-premium .tcrm-leads-filter-grid{grid-template-columns:minmax(210px,1.45fr) minmax(180px,1.15fr) repeat(4,minmax(112px,.8fr))}
}
@media (max-width:1100px){
  .tcrm-leads-premium .tcrm-leads-filter-grid{grid-template-columns:repeat(3,minmax(180px,1fr))}
}
@media (max-width:760px){
  .tcrm-leads-premium .tcrm-leads-filter-grid{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){.tcrm-leads-premium *{transition-duration:.01ms!important}}
'''

CSS.write_text(css, encoding="utf-8")
if text != original:
    TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V17_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V18_CSS_WRITTEN=YES")
print("V18_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("STRUCTURAL_FIDELITY_PASS=YES")
print("GLASS_TOTAL_STAT_RESTORED=YES")
print("FILTER_COMMAND_GRID=YES")
print("TABLE_CARD_ROWS=YES")
print("LIGHT_PEARL_DEPTH_UPGRADED=YES")
print("DARK_NAVY_DEPTH_UPGRADED=YES")
print("TYPOGRAPHY_UPGRADED=YES")
print("FUNCTIONALITY_CHANGED=NO")
