#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-3.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from the EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1.css";',
    'import "../leads-premium-v1-1.css";',
    'import "../leads-premium-v1-2.css";',
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-total-card',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-table',
    'tcrm-leads-row',
    'tcrm-leads-actions',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V12_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-3.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-2.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.2 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.3 — original concept fidelity refinement
   Target: match the FIRST approved Leads concept, not merely improve V1.2.
   UI/UX only. No business logic, filters, actions, routes, permissions, data or pagination changes. */

/* ================================================================
   1. PAGE ATMOSPHERE — stronger premium separation, especially Light
   ================================================================ */
.tcrm-leads-premium{
  --v13-violet:#6f5cff;
  --v13-indigo:#5568ff;
  --v13-cyan:#4ebcff;
  --v13-pearl:#f8f8ff;
  --v13-ink:#172033;
  --v13-muted:#667189;
  --v13-line:rgba(96,82,232,.18);
  --v13-glow:rgba(101,84,255,.18);
}

.tcrm-leads-premium::before{
  background:
    radial-gradient(900px 520px at -4% -6%,rgba(113,88,255,.13),transparent 61%),
    radial-gradient(820px 500px at 104% 0%,rgba(74,143,255,.12),transparent 64%),
    radial-gradient(700px 420px at 50% 104%,rgba(165,111,255,.07),transparent 67%),
    linear-gradient(180deg,#fdfdff 0%,#f7f8ff 45%,#f2f5ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(920px 540px at -2% -7%,rgba(75,67,255,.22),transparent 62%),
    radial-gradient(860px 520px at 102% -2%,rgba(31,104,255,.17),transparent 64%),
    radial-gradient(760px 470px at 54% 104%,rgba(118,56,255,.12),transparent 68%),
    linear-gradient(180deg,#040b15 0%,#061221 48%,#050f1c 100%)!important;
}

/* ================================================================
   2. HERO — preserve V1.2 structure but bring it closer to concept
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-hero{
  border-radius:22px!important;
  border-color:rgba(104,86,244,.27)!important;
  background:
    radial-gradient(72% 250% at 67% 10%,rgba(104,82,255,.21),transparent 51%),
    radial-gradient(58% 190% at 98% 90%,rgba(194,102,255,.14),transparent 57%),
    linear-gradient(116deg,rgba(255,255,255,.995),rgba(248,246,255,.985) 52%,rgba(252,247,255,.99))!important;
  box-shadow:
    0 32px 76px -44px rgba(69,54,185,.48),
    0 12px 30px -25px rgba(65,75,145,.30),
    inset 0 1px 0 rgba(255,255,255,.98),
    inset 0 -1px 0 rgba(106,86,255,.065)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(125,105,255,.52)!important;
  background:
    radial-gradient(80% 250% at 66% 9%,rgba(72,77,255,.39),transparent 51%),
    radial-gradient(68% 220% at 98% 91%,rgba(177,52,255,.31),transparent 57%),
    linear-gradient(116deg,rgba(7,18,43,.995),rgba(12,27,69,.99) 50%,rgba(43,19,95,.99))!important;
  box-shadow:
    0 36px 88px -48px rgba(0,0,0,.92),
    0 0 58px -34px rgba(112,77,255,.72),
    inset 0 1px 0 rgba(255,255,255,.085)!important;
}
.tcrm-leads-premium .tcrm-leads-hero h1{
  font-size:28px!important;
  font-weight:900!important;
  letter-spacing:-.047em!important;
}
.tcrm-leads-premium .tcrm-leads-hero-subtitle{
  font-size:12px!important;
  line-height:1.5!important;
  font-weight:600!important;
}
.tcrm-leads-premium .tcrm-leads-hero-actions{gap:9px!important}
.tcrm-leads-premium .tcrm-leads-total-card{
  min-width:96px!important;
  height:56px!important;
  border-radius:16px!important;
  backdrop-filter:blur(18px) saturate(130%);
}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:19px!important}
.tcrm-leads-premium .tcrm-leads-hero-actions>button,
.tcrm-leads-premium .tcrm-leads-hero-actions>a button{
  min-height:41px!important;
  border-radius:12px!important;
  font-size:11.5px!important;
  letter-spacing:.005em!important;
}

/* ================================================================
   3. FILTER COMMAND CENTER — richer hierarchy, not a plain form card
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-radius:22px!important;
  border-color:rgba(100,84,235,.19)!important;
  background:
    radial-gradient(85% 150% at 0% 0%,rgba(111,87,255,.072),transparent 56%),
    radial-gradient(65% 130% at 100% 100%,rgba(89,149,255,.048),transparent 60%),
    linear-gradient(145deg,rgba(255,255,255,.992),rgba(248,249,255,.968))!important;
  box-shadow:
    0 28px 70px -44px rgba(63,51,166,.38),
    0 10px 28px -23px rgba(65,77,139,.25),
    inset 0 1px 0 rgba(255,255,255,.99),
    inset 0 -1px 0 rgba(100,84,235,.045)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card::before{
  height:2px!important;
  opacity:.9;
  background:linear-gradient(90deg,transparent 4%,rgba(110,88,255,.52) 26%,rgba(67,133,255,.32) 58%,rgba(166,85,255,.28) 78%,transparent 96%)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card::after{
  content:"";
  position:absolute;
  right:-70px;
  top:-80px;
  width:280px;
  height:190px;
  border-radius:50%;
  pointer-events:none;
  background:radial-gradient(circle,rgba(112,91,255,.08),transparent 70%);
  filter:blur(4px);
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(102,124,215,.30)!important;
  background:
    radial-gradient(90% 160% at 0% 0%,rgba(84,76,255,.13),transparent 58%),
    radial-gradient(64% 130% at 100% 100%,rgba(36,115,255,.07),transparent 60%),
    linear-gradient(145deg,rgba(8,22,43,.992),rgba(7,18,36,.985))!important;
  box-shadow:
    0 32px 82px -52px rgba(0,0,0,.98),
    0 0 42px -32px rgba(79,73,255,.54),
    inset 0 1px 0 rgba(255,255,255,.052)!important;
}

.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:18px!important}
.tcrm-leads-premium .tcrm-leads-filter-card .flex.flex-wrap.items-end{column-gap:12px!important;row-gap:14px!important}
.tcrm-leads-premium .tcrm-leads-filter-card label{
  margin-left:1px;
  font-size:10.5px!important;
  line-height:1!important;
  font-weight:800!important;
  letter-spacing:.018em!important;
  color:#59647a!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card label{color:#a9b6cd!important}

.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:40px!important;
  border-radius:12px!important;
  border-color:rgba(101,85,235,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.995),rgba(248,248,255,.94))!important;
  box-shadow:0 8px 18px -17px rgba(60,60,130,.30),inset 0 1px 0 rgba(255,255,255,.98)!important;
  font-size:11.5px!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card input:hover,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:hover,
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  border-color:rgba(103,86,242,.32)!important;
  box-shadow:0 12px 24px -19px rgba(79,66,190,.34),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  color:#eef3ff!important;
  border-color:rgba(104,124,202,.31)!important;
  background:linear-gradient(180deg,rgba(13,31,59,.95),rgba(9,24,47,.92))!important;
  box-shadow:0 10px 22px -19px rgba(0,0,0,.82),inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input:hover,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:hover,
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  border-color:rgba(120,109,255,.50)!important;
  background:linear-gradient(180deg,rgba(16,36,70,.98),rgba(11,28,55,.96))!important;
}

/* Utility controls share a clear premium system */
.tcrm-leads-premium .tcrm-leads-filter-card button[class*="gap-"]{
  font-weight:760!important;
  padding-inline:13px!important;
}

/* ================================================================
   4. TABLE SHELL — make it one premium workspace
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-table-card{
  overflow:hidden!important;
  border-radius:22px!important;
  border:1px solid rgba(99,84,226,.19)!important;
  background:
    radial-gradient(78% 95% at 0% 0%,rgba(113,91,255,.045),transparent 55%),
    linear-gradient(180deg,rgba(255,255,255,.995),rgba(249,250,255,.985))!important;
  box-shadow:
    0 32px 82px -50px rgba(60,51,155,.40),
    0 12px 30px -25px rgba(65,76,135,.24),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(97,120,208,.29)!important;
  background:
    radial-gradient(70% 90% at 0% 0%,rgba(76,72,255,.08),transparent 58%),
    linear-gradient(180deg,rgba(7,20,39,.995),rgba(6,17,34,.995))!important;
  box-shadow:
    0 36px 92px -56px rgba(0,0,0,.98),
    0 0 44px -34px rgba(80,76,255,.48),
    inset 0 1px 0 rgba(255,255,255,.042)!important;
}

.tcrm-leads-premium .tcrm-leads-table{font-size:11.25px!important}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  min-height:43px!important;
  padding-top:13px!important;
  padding-bottom:13px!important;
  font-size:10.5px!important;
  line-height:1.15!important;
  font-weight:820!important;
  letter-spacing:.016em!important;
  color:#59657b!important;
  background:linear-gradient(180deg,rgba(248,248,255,.99),rgba(242,244,253,.96))!important;
  box-shadow:inset 0 -1px 0 rgba(102,87,232,.13)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#aab8d1!important;
  background:linear-gradient(180deg,rgba(13,31,59,.99),rgba(10,26,50,.98))!important;
  box-shadow:inset 0 -1px 0 rgba(112,128,211,.18)!important;
}

/* ================================================================
   5. ROWS — subtle luminous interaction; NO giant purple bands
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky{
  padding-top:11px!important;
  padding-bottom:11px!important;
  border-bottom:1px solid rgba(91,103,145,.07)!important;
  background:rgba(255,255,255,.78)!important;
  box-shadow:none!important;
  transition:background .15s ease,border-color .15s ease,box-shadow .15s ease!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td.sticky{
  background:rgba(247,249,255,.76)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td.sticky{
  background:linear-gradient(90deg,rgba(108,91,255,.060),rgba(76,135,255,.035))!important;
  border-bottom-color:rgba(103,89,228,.14)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:first-child{
  box-shadow:inset 2px 0 0 rgba(108,89,255,.58)!important;
}

.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky{
  color:#d7e0ef!important;
  border-bottom-color:rgba(103,124,181,.085)!important;
  background:rgba(7,22,42,.84)!important;
  box-shadow:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td.sticky{
  background:rgba(9,27,50,.86)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td.sticky{
  background:linear-gradient(90deg,rgba(78,77,177,.16),rgba(48,89,157,.11))!important;
  border-bottom-color:rgba(117,111,255,.16)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td:first-child{
  box-shadow:inset 2px 0 0 rgba(124,103,255,.72)!important;
}

/* SLA breached rows retain meaning, but remove the V1.2 full-row purple block. */
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td.sticky{
  background:linear-gradient(90deg,rgba(245,158,11,.025),rgba(255,255,255,.78) 38%)!important;
  box-shadow:none!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset 2px 0 0 rgba(245,158,11,.52)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td.sticky{
  background:linear-gradient(90deg,rgba(245,158,11,.035),rgba(7,22,42,.86) 40%)!important;
  box-shadow:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset 2px 0 0 rgba(245,158,11,.58)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row:hover > td,
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row:hover > td.sticky{
  background:linear-gradient(90deg,rgba(245,158,11,.045),rgba(105,89,255,.045))!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row:hover > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row:hover > td.sticky{
  background:linear-gradient(90deg,rgba(245,158,11,.055),rgba(83,78,177,.13))!important;
}

/* ================================================================
   6. LEAD IDENTITY / TYPE HIERARCHY
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-avatar{
  width:30px!important;
  height:30px!important;
  border:1px solid rgba(255,255,255,.60)!important;
  box-shadow:0 8px 18px -10px rgba(80,55,190,.50),inset 0 1px 0 rgba(255,255,255,.28)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-avatar{
  border-color:rgba(194,186,255,.44)!important;
  box-shadow:0 0 20px -11px rgba(121,95,255,.78),inset 0 1px 0 rgba(255,255,255,.20)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody td:first-child{font-size:11.5px!important}
.tcrm-leads-premium .tcrm-leads-table tbody td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table tbody td:first-child .font-semibold{
  font-weight:780!important;
  letter-spacing:-.01em;
}
.tcrm-leads-premium .tcrm-leads-table tbody td .text-muted-foreground{font-size:10px!important;line-height:1.3!important}

/* ================================================================
   7. BADGES — unified premium chip system
   ================================================================ */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge,
.tcrm-leads-premium .tcrm-leads-table tbody td:nth-child(3) [class*="rounded"]{
  min-height:24px!important;
  padding-inline:9px!important;
  border-radius:999px!important;
  font-size:10.25px!important;
  line-height:1!important;
  font-weight:800!important;
  letter-spacing:.002em!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.34),0 7px 14px -12px rgba(20,30,80,.38)!important;
}
.dark .tcrm-leads-premium .tcrm-fit-badge,
.dark .tcrm-leads-premium .tcrm-stage-badge,
.dark .tcrm-leads-premium .tcrm-leads-table tbody td:nth-child(3) [class*="rounded"]{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.13),0 0 16px -12px rgba(111,92,255,.70)!important;
}
.tcrm-leads-premium .tcrm-classification{
  font-size:10.25px!important;
  font-weight:820!important;
  letter-spacing:.004em!important;
  text-shadow:0 0 16px currentColor;
}

/* ================================================================
   8. ACTIONS — polished compact rail
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-actions{
  gap:4px!important;
  padding:2px 3px!important;
  border-radius:11px;
}
.tcrm-leads-premium .tcrm-leads-actions button{
  min-height:30px!important;
  height:30px!important;
  border-radius:9px!important;
  color:#566177!important;
  border:1px solid rgba(94,82,205,.10)!important;
  background:rgba(248,249,255,.72)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.90)!important;
}
.tcrm-leads-premium .tcrm-leads-actions button:first-child{
  padding-inline:10px!important;
  font-size:10.5px!important;
  font-weight:760!important;
}
.tcrm-leads-premium .tcrm-leads-actions button:hover{
  color:#4f46d9!important;
  border-color:rgba(100,84,235,.22)!important;
  background:rgba(241,241,255,.96)!important;
  box-shadow:0 8px 18px -14px rgba(78,61,194,.42),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions button{
  color:#b8c6dd!important;
  border-color:rgba(105,124,198,.18)!important;
  background:rgba(12,31,58,.74)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.045)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions button:hover{
  color:#fff!important;
  border-color:rgba(120,106,255,.36)!important;
  background:rgba(25,39,81,.92)!important;
  box-shadow:0 0 20px -13px rgba(112,90,255,.72),inset 0 1px 0 rgba(255,255,255,.08)!important;
}

/* ================================================================
   9. PAGINATION FOOTER — integrated with workspace shell
   ================================================================ */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:58px;
  border-top:1px solid rgba(99,84,225,.13)!important;
  background:linear-gradient(180deg,rgba(249,250,255,.70),rgba(246,248,255,.96))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.78)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  border-top-color:rgba(103,122,198,.17)!important;
  background:linear-gradient(180deg,rgba(8,23,44,.88),rgba(6,19,37,.98))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button,
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] [role="combobox"]{
  border-radius:9px!important;
}

/* ================================================================
   10. RESPONSIVE / MOTION SAFETY
   ================================================================ */
@media (max-width:1100px){
  .tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:15px!important}
  .tcrm-leads-premium .tcrm-leads-hero h1{font-size:25px!important}
}
@media (prefers-reduced-motion:reduce){
  .tcrm-leads-premium *,
  .tcrm-leads-premium *::before,
  .tcrm-leads-premium *::after{transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}
}
'''

CSS.write_text(css, encoding="utf-8")

if text != original:
    TSX.write_text(text, encoding="utf-8")

required_final = [
    css_import,
    'tcrm-leads-premium',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-row',
]
missing_final = [x for x in required_final if x not in text]
if missing_final:
    raise SystemExit("ERROR=V13_FINAL_HOOKS_MISSING:" + ",".join(missing_final))

print("PATCH=YES")
print("V12_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V13_CSS_WRITTEN=YES")
print("V13_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("PURPLE_ROW_BANDS_FIXED=YES")
print("LIGHT_PEARL_DEPTH_UPGRADED=YES")
print("FILTER_COMMAND_CENTER_UPGRADED=YES")
print("TABLE_WORKSPACE_UPGRADED=YES")
print("TYPOGRAPHY_UPGRADED=YES")
print("BADGES_UPGRADED=YES")
print("ACTIONS_UPGRADED=YES")
print("PAGINATION_UPGRADED=YES")
print("FUNCTIONALITY_CHANGED=NO")
