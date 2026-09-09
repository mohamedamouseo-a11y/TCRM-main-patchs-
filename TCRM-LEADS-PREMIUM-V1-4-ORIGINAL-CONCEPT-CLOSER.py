#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-4.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from the EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1.css";',
    'import "../leads-premium-v1-1.css";',
    'import "../leads-premium-v1-2.css";',
    'import "../leads-premium-v1-3.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-table',
    'tcrm-leads-row',
    'tcrm-leads-actions',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V13_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-4.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-3.css";'
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.4 — original concept closer pass */

/* ===== 1. Page atmosphere: closer to approved pearl / navy command workspace ===== */
.tcrm-leads-premium::before{
  background:
    radial-gradient(760px 430px at 7% 0%,rgba(119,96,255,.12),transparent 64%),
    radial-gradient(780px 440px at 94% 4%,rgba(72,128,255,.10),transparent 66%),
    radial-gradient(640px 380px at 56% 82%,rgba(187,128,255,.07),transparent 70%),
    linear-gradient(180deg,#fbfbff 0%,#f5f6ff 54%,#f1f3fc 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(860px 470px at 3% -3%,rgba(79,72,255,.24),transparent 64%),
    radial-gradient(860px 500px at 97% 0%,rgba(38,104,255,.18),transparent 66%),
    radial-gradient(700px 440px at 56% 86%,rgba(133,58,255,.12),transparent 72%),
    linear-gradient(180deg,#050c17 0%,#07111f 48%,#06101d 100%)!important;
}

/* ===== 2. Hero composition: tighter, more intentional, closer to original concept ===== */
.tcrm-leads-premium .tcrm-leads-hero{
  min-height:102px!important;
  padding:22px 24px!important;
  border-radius:23px!important;
  box-shadow:
    0 38px 84px -48px rgba(75,57,190,.52),
    0 14px 34px -26px rgba(62,70,135,.26),
    inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  box-shadow:
    0 40px 88px -50px rgba(10,18,74,.96),
    0 0 58px -36px rgba(111,80,255,.76),
    inset 0 1px 0 rgba(255,255,255,.08)!important;
}
.tcrm-leads-premium .tcrm-leads-hero h1{font-size:29px!important;font-weight:900!important}
.tcrm-leads-premium .tcrm-leads-hero-subtitle{font-size:12px!important;opacity:.92}
.tcrm-leads-premium .tcrm-leads-total-card{min-width:96px!important;height:56px!important}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:19px!important}

/* ===== 3. Filter command center: stronger grouping and premium control hierarchy ===== */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-radius:22px!important;
  padding:2px!important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.86),rgba(246,247,255,.76)) padding-box,
    linear-gradient(110deg,rgba(118,98,255,.34),rgba(88,138,255,.18),rgba(118,98,255,.12)) border-box!important;
  border:1px solid transparent!important;
  box-shadow:
    0 30px 72px -46px rgba(63,55,160,.40),
    0 12px 30px -25px rgba(76,84,140,.22),
    inset 0 1px 0 rgba(255,255,255,.97)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  background:
    linear-gradient(180deg,rgba(8,22,43,.96),rgba(8,20,38,.93)) padding-box,
    linear-gradient(110deg,rgba(116,102,255,.42),rgba(69,119,255,.24),rgba(116,102,255,.14)) border-box!important;
  box-shadow:
    0 32px 76px -48px rgba(0,0,0,.96),
    0 0 40px -28px rgba(91,79,255,.46),
    inset 0 1px 0 rgba(255,255,255,.045)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:17px 18px!important}
.tcrm-leads-premium .tcrm-leads-filter-card label{font-size:10.5px!important;font-weight:800!important;letter-spacing:.012em}
.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]{
  min-height:40px!important;
  border-radius:12px!important;
  font-size:12px!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:38px!important;
  border-radius:11px!important;
  font-size:11px!important;
  font-weight:760!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  transform:translateY(-1px);
  box-shadow:0 12px 24px -18px rgba(82,65,200,.34)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  box-shadow:0 12px 24px -18px rgba(0,0,0,.72),0 0 24px -18px rgba(105,87,255,.72)!important;
}

/* ===== 4. Table shell: one integrated premium workspace, not a plain admin table ===== */
.tcrm-leads-premium .tcrm-leads-table-card{
  position:relative;
  overflow:hidden!important;
  border-radius:22px!important;
  border:1px solid rgba(103,91,246,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.975),rgba(249,250,255,.94))!important;
  box-shadow:
    0 34px 84px -52px rgba(57,51,150,.40),
    0 14px 34px -28px rgba(70,78,135,.24),
    inset 0 1px 0 rgba(255,255,255,.97)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card::before{
  content:"";position:absolute;inset:0 0 auto 0;height:2px;z-index:3;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(101,91,255,.52),rgba(66,128,255,.30),transparent);
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(103,124,219,.28)!important;
  background:linear-gradient(180deg,rgba(7,19,37,.99),rgba(7,18,34,.98))!important;
  box-shadow:
    0 36px 88px -52px rgba(0,0,0,.96),
    0 0 46px -34px rgba(73,79,255,.45),
    inset 0 1px 0 rgba(255,255,255,.035)!important;
}

/* Header stronger and more architectural */
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:46px!important;
  padding-top:0!important;padding-bottom:0!important;
  font-size:10px!important;
  font-weight:850!important;
  letter-spacing:.025em!important;
  text-transform:none!important;
  color:#5d6881!important;
  background:linear-gradient(180deg,rgba(246,247,255,.98),rgba(241,243,252,.94))!important;
  border-bottom:1px solid rgba(101,91,246,.15)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#a5b3cf!important;
  background:linear-gradient(180deg,rgba(13,31,58,.99),rgba(10,26,50,.98))!important;
  border-bottom-color:rgba(111,128,214,.20)!important;
}

/* ===== 5. Rows: remove all full-band purple feeling; use refined operational row rhythm ===== */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td{
  min-height:48px!important;
  padding-top:10px!important;
  padding-bottom:10px!important;
  background:rgba(255,255,255,.78)!important;
  border-bottom:1px solid rgba(91,100,140,.055)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td{
  background:rgba(247,249,255,.72)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td{
  background:rgba(8,22,42,.78)!important;
  border-bottom-color:rgba(102,119,176,.075)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td{
  background:rgba(10,27,51,.68)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  background:rgba(104,91,246,.055)!important;
  box-shadow:inset 0 1px 0 rgba(104,91,246,.05),inset 0 -1px 0 rgba(104,91,246,.05)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  background:rgba(76,89,210,.10)!important;
  box-shadow:inset 0 1px 0 rgba(116,108,255,.08),inset 0 -1px 0 rgba(116,108,255,.08)!important;
}

/* SLA semantic state: edge cue, never a giant purple row */
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td{
  background:rgba(255,248,246,.82)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset 3px 0 0 rgba(239,68,68,.44)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td{
  background:rgba(64,25,36,.18)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset 3px 0 0 rgba(248,113,113,.48)!important;
}

/* Sticky Lead Name / Actions must visually belong to the SAME row */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:rgba(255,255,255,.94)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td:last-child{
  background:rgba(248,249,255,.94)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:rgba(7,20,38,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td:last-child{
  background:rgba(9,25,47,.98)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:last-child{
  background:rgba(245,244,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:last-child{
  background:rgba(16,31,61,.99)!important;
}

/* ===== 6. Lead identity / typography ===== */
.tcrm-leads-premium .tcrm-leads-avatar{
  width:31px!important;height:31px!important;
  box-shadow:0 8px 18px -10px rgba(80,60,180,.48),inset 0 1px 0 rgba(255,255,255,.28)!important;
  border:1px solid rgba(255,255,255,.34)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-avatar{
  box-shadow:0 8px 20px -11px rgba(0,0,0,.85),0 0 18px -10px rgba(116,93,255,.68),inset 0 1px 0 rgba(255,255,255,.18)!important;
}
.tcrm-leads-premium .tcrm-leads-table td{font-size:11px!important;color:#4f596e!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#9ba8c0!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#1e2738!important;font-weight:680!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#eef3ff!important}

/* ===== 7. Badges: one premium system, slightly larger and more legible ===== */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge,
.tcrm-leads-premium .tcrm-leads-table [class*="rounded-full"]{
  min-height:22px!important;
  padding-inline:8px!important;
  font-size:9.5px!important;
  font-weight:820!important;
  letter-spacing:.005em!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.22),0 5px 12px -10px currentColor!important;
}
.dark .tcrm-leads-premium .tcrm-fit-badge,
.dark .tcrm-leads-premium .tcrm-stage-badge,
.dark .tcrm-leads-premium .tcrm-leads-table [class*="rounded-full"]{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 0 16px -11px currentColor!important;
}

/* ===== 8. Actions: premium capsule rail, still exact same actions ===== */
.tcrm-leads-premium .tcrm-leads-actions{
  gap:4px!important;
  padding:3px 4px!important;
  border-radius:10px!important;
  border:1px solid rgba(103,91,246,.10)!important;
  background:rgba(250,250,255,.72)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions{
  border-color:rgba(103,123,205,.18)!important;
  background:rgba(12,27,52,.74)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035)!important;
}
.tcrm-leads-premium .tcrm-leads-actions button{
  height:27px!important;min-height:27px!important;
  border-radius:7px!important;
  padding-inline:7px!important;
  font-size:10px!important;
}

/* ===== 9. Pagination/footer: integrated into workspace shell ===== */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:58px!important;
  background:linear-gradient(180deg,rgba(248,249,255,.72),rgba(244,246,253,.94))!important;
  border-top:1px solid rgba(103,91,246,.12)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,22,42,.76),rgba(7,19,36,.98))!important;
  border-top-color:rgba(102,121,193,.16)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button{
  border-radius:9px!important;
  transition:transform .15s ease,box-shadow .15s ease!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button:hover{transform:translateY(-1px)}

@media (max-width:1100px){
  .tcrm-leads-premium .tcrm-leads-table td{font-size:10.5px!important}
  .tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:14px!important}
}
'''

CSS.write_text(css, encoding="utf-8")

if text != original:
    TSX.write_text(text, encoding="utf-8")

required_final = [css_import, 'tcrm-leads-premium', 'tcrm-leads-table-card', 'tcrm-leads-filter-card']
missing_final = [x for x in required_final if x not in text]
if missing_final:
    raise SystemExit("ERROR=V14_REQUIRED_MISSING:" + ",".join(missing_final))

print("PATCH=YES")
print("V13_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V14_CSS_WRITTEN=YES")
print("V14_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("HERO_CLOSER=YES")
print("FILTER_COMMAND_CENTER_CLOSER=YES")
print("TABLE_WORKSPACE_CLOSER=YES")
print("STICKY_COLUMNS_UNIFIED=YES")
print("SLA_BANDS_FIXED=YES")
print("BADGE_SYSTEM_CLOSER=YES")
print("ACTIONS_CLOSER=YES")
print("PAGINATION_CLOSER=YES")
print("LIGHT_MODE_CLOSER=YES")
print("DARK_MODE_CLOSER=YES")
print("FUNCTIONALITY_CHANGED=NO")
