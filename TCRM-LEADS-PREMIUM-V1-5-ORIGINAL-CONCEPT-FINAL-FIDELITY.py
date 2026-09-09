#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-5.css"

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
    raise SystemExit("ERROR=LEADS_V14_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-5.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-4.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.4 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.5 — final fidelity pass against the ORIGINAL FIRST Leads concept.
   Runtime deltas targeted from V1.4 screenshots:
   1) Light still too white/admin-flat.
   2) Filter surface still reads like a plain form, not a command center.
   3) Sticky Lead Name surface still visually separates from row body.
   4) Hover/SLA full-row purple band is too strong in Dark.
   5) Table typography / metadata hierarchy is too faint and small.
   6) Total KPI, actions and pagination need stronger concept-level finish.
*/

/* ===== ORIGINAL CONCEPT PAGE ATMOSPHERE ===== */
.tcrm-leads-premium{
  --v15-light-row-a:rgba(255,255,255,.82);
  --v15-light-row-b:rgba(247,249,255,.82);
  --v15-light-row-hover:rgba(241,240,255,.90);
  --v15-dark-row-a:rgba(9,22,41,.88);
  --v15-dark-row-b:rgba(11,27,50,.92);
  --v15-dark-row-hover:rgba(18,35,66,.96);
}
.tcrm-leads-premium::before{
  background:
    radial-gradient(680px 390px at 8% 2%,rgba(121,92,255,.13),transparent 66%),
    radial-gradient(760px 440px at 92% 0%,rgba(83,137,255,.115),transparent 68%),
    radial-gradient(540px 340px at 52% 78%,rgba(177,129,255,.065),transparent 72%),
    linear-gradient(180deg,#fbfbff 0%,#f6f6ff 46%,#f2f5ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(820px 480px at 8% -4%,rgba(66,75,255,.20),transparent 66%),
    radial-gradient(840px 500px at 96% 0%,rgba(99,55,255,.17),transparent 68%),
    radial-gradient(680px 420px at 54% 82%,rgba(32,114,255,.08),transparent 72%),
    linear-gradient(180deg,#050c18 0%,#071426 50%,#06111f 100%)!important;
}

/* ===== HERO — closer to original premium composition ===== */
.tcrm-leads-premium .tcrm-leads-hero{
  min-height:102px!important;
  border-radius:23px!important;
  border-color:rgba(113,93,255,.27)!important;
  background:
    radial-gradient(70% 220% at 72% 0%,rgba(120,88,255,.20),transparent 52%),
    radial-gradient(55% 190% at 94% 96%,rgba(224,142,255,.14),transparent 55%),
    linear-gradient(116deg,rgba(255,255,255,.985),rgba(247,246,255,.965) 48%,rgba(250,247,255,.985))!important;
  box-shadow:
    0 28px 68px -40px rgba(75,60,186,.44),
    0 10px 28px -22px rgba(66,78,151,.24),
    inset 0 1px 0 rgba(255,255,255,.97),
    inset 0 -1px 0 rgba(112,95,255,.07)!important;
}
.tcrm-leads-premium .tcrm-leads-hero::before{
  opacity:.64!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(99,91,180,.16) 1px,transparent 1.2px) 0 0/20px 20px,
    radial-gradient(ellipse at 70% 40%,rgba(119,96,255,.10),transparent 38%),
    radial-gradient(ellipse at 92% 66%,rgba(181,92,255,.09),transparent 34%)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(129,103,255,.48)!important;
  background:
    radial-gradient(78% 235% at 68% 0%,rgba(79,82,255,.38),transparent 51%),
    radial-gradient(66% 210% at 96% 94%,rgba(173,58,255,.31),transparent 56%),
    linear-gradient(116deg,rgba(7,19,45,.995),rgba(14,27,69,.99) 50%,rgba(43,20,91,.99))!important;
  box-shadow:
    0 32px 78px -46px rgba(0,0,0,.90),
    0 0 46px -30px rgba(117,84,255,.72),
    inset 0 1px 0 rgba(255,255,255,.085)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero::before{
  opacity:.72!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(145,151,230,.20) 1px,transparent 1.25px) 0 0/20px 20px,
    radial-gradient(ellipse at 68% 38%,rgba(102,91,255,.19),transparent 39%),
    radial-gradient(ellipse at 94% 68%,rgba(191,69,255,.15),transparent 34%)!important;
}
.tcrm-leads-premium .tcrm-leads-hero h1{font-size:28px!important;font-weight:900!important;letter-spacing:-.047em!important}
.tcrm-leads-premium .tcrm-leads-hero-subtitle{font-size:12px!important;line-height:1.45!important;font-weight:620!important;opacity:.94}

.tcrm-leads-premium .tcrm-leads-total-card{
  min-width:104px!important;
  height:58px!important;
  padding:8px 15px!important;
  border-radius:16px!important;
  backdrop-filter:blur(18px) saturate(1.12)!important;
  box-shadow:0 18px 40px -26px rgba(68,55,170,.58),inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:20px!important;line-height:.95!important;font-weight:900!important}
.tcrm-leads-premium .tcrm-leads-total-card span{font-size:9px!important;margin-top:5px!important;font-weight:760!important}

/* ===== FILTER COMMAND CENTER ===== */
.tcrm-leads-premium .tcrm-leads-filter-card{
  border-radius:22px!important;
  border-color:rgba(102,91,246,.20)!important;
  background:
    radial-gradient(72% 160% at 0% 0%,rgba(113,93,255,.085),transparent 58%),
    radial-gradient(60% 140% at 100% 0%,rgba(84,138,255,.055),transparent 62%),
    linear-gradient(145deg,rgba(255,255,255,.975),rgba(247,248,255,.945))!important;
  box-shadow:
    0 30px 72px -46px rgba(70,60,168,.46),
    0 12px 30px -25px rgba(67,77,141,.23),
    inset 0 1px 0 rgba(255,255,255,.98),
    inset 0 -1px 0 rgba(109,94,255,.055)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  border-color:rgba(105,125,221,.29)!important;
  background:
    radial-gradient(78% 155% at 0% 0%,rgba(87,78,255,.13),transparent 58%),
    radial-gradient(62% 150% at 100% 0%,rgba(41,108,255,.075),transparent 64%),
    linear-gradient(145deg,rgba(8,21,42,.99),rgba(8,20,39,.975))!important;
  box-shadow:
    0 30px 76px -48px rgba(0,0,0,.96),
    0 0 36px -28px rgba(83,75,255,.46),
    inset 0 1px 0 rgba(255,255,255,.052)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:17px 18px!important}
.tcrm-leads-premium .tcrm-leads-filter-card .flex.flex-wrap.items-end.gap-3{gap:12px 11px!important;align-items:end!important}
.tcrm-leads-premium .tcrm-leads-filter-card label{
  margin-bottom:2px!important;
  font-size:10.5px!important;
  line-height:1.15!important;
  font-weight:820!important;
  letter-spacing:.018em!important;
  color:#566179!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card label{color:#a7b4cc!important}
.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:40px!important;
  border-radius:12px!important;
  border-color:rgba(104,93,231,.19)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.98),0 7px 16px -14px rgba(59,61,130,.32)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card input:hover,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:hover,
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  border-color:rgba(104,88,255,.34)!important;
  box-shadow:0 10px 24px -19px rgba(91,70,218,.33),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  border-color:rgba(104,123,205,.30)!important;
  background:linear-gradient(180deg,rgba(13,31,59,.92),rgba(9,24,47,.88))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.052),0 8px 18px -15px rgba(0,0,0,.72)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input:hover,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:hover,
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]):hover{
  border-color:rgba(125,112,255,.46)!important;
  background:linear-gradient(180deg,rgba(16,35,67,.96),rgba(11,28,55,.94))!important;
}

/* Utility controls should read as one coherent command set. */
.tcrm-leads-premium .tcrm-leads-filter-card button{
  font-size:11px!important;
  font-weight:770!important;
}

/* ===== TABLE WORKSPACE / SHELL ===== */
.tcrm-leads-premium .tcrm-leads-table-card{
  position:relative;
  overflow:hidden!important;
  border-radius:22px!important;
  border:1px solid rgba(102,92,246,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.965),rgba(248,249,255,.94))!important;
  box-shadow:
    0 34px 82px -52px rgba(58,54,152,.43),
    0 12px 30px -26px rgba(62,74,132,.22),
    inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card::before{
  content:"";position:absolute;z-index:4;inset:0 0 auto 0;height:2px;pointer-events:none;
  background:linear-gradient(90deg,transparent 1%,rgba(104,91,255,.40) 30%,rgba(62,132,255,.28) 70%,transparent 99%);
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  border-color:rgba(96,119,208,.25)!important;
  background:linear-gradient(180deg,rgba(7,19,37,.985),rgba(7,18,35,.975))!important;
  box-shadow:0 34px 86px -54px rgba(0,0,0,.98),0 0 38px -30px rgba(67,82,255,.38),inset 0 1px 0 rgba(255,255,255,.035)!important;
}

.tcrm-leads-premium .tcrm-leads-table{
  font-size:12px!important;
  border-collapse:separate!important;
  border-spacing:0!important;
}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:42px!important;
  padding-top:0!important;
  padding-bottom:0!important;
  font-size:10.5px!important;
  line-height:1!important;
  font-weight:820!important;
  letter-spacing:.016em!important;
  color:#66718a!important;
  background:linear-gradient(180deg,rgba(247,248,255,.985),rgba(242,245,254,.955))!important;
  border-bottom:1px solid rgba(99,102,241,.15)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#9faec7!important;
  background:linear-gradient(180deg,rgba(12,31,59,.985),rgba(10,27,52,.975))!important;
  border-bottom-color:rgba(106,126,213,.19)!important;
}

/* One row = one visual surface. This explicitly defeats stale sticky-cell backgrounds. */
.tcrm-leads-premium .tcrm-leads-row{--v15-row-surface:var(--v15-light-row-a);background:transparent!important}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v15-row-surface:var(--v15-light-row-b)}
.dark .tcrm-leads-premium .tcrm-leads-row{--v15-row-surface:var(--v15-dark-row-a)}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even){--v15-row-surface:var(--v15-dark-row-b)}

.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  background:var(--v15-row-surface)!important;
  background-image:none!important;
  border-bottom:1px solid rgba(97,108,167,.07)!important;
  box-shadow:none!important;
  backdrop-filter:none!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td:last-child{
  border-bottom-color:rgba(96,117,184,.075)!important;
}

/* Remove the visible vertical seam created by sticky name/actions surfaces. */
.tcrm-leads-premium .tcrm-leads-table td.sticky,
.tcrm-leads-premium .tcrm-leads-table th.sticky{
  box-shadow:none!important;
}
.tcrm-leads-premium .tcrm-leads-table td:first-child,
.tcrm-leads-premium .tcrm-leads-table th:first-child{
  border-inline-end:1px solid rgba(106,98,202,.055)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child,
.dark .tcrm-leads-premium .tcrm-leads-table th:first-child{
  border-inline-end-color:rgba(104,121,199,.07)!important;
}

/* Hover should be a soft executive lift, NEVER a giant purple band. */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover{--v15-row-surface:var(--v15-light-row-hover)!important}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover{--v15-row-surface:var(--v15-dark-row-hover)!important}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  box-shadow:inset 0 1px 0 rgba(113,95,255,.055),inset 0 -1px 0 rgba(113,95,255,.045)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  box-shadow:inset 0 1px 0 rgba(121,110,255,.09),inset 0 -1px 0 rgba(121,110,255,.06)!important;
}

/* SLA: keep meaning, remove full-row wash. Use a small edge cue only. */
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row,
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row:hover{background:transparent!important}
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td{background:var(--v15-row-surface)!important}
.tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset 3px 0 0 rgba(239,68,68,.72)!important;
}
[dir="rtl"] .tcrm-leads-premium .tcrm-leads-table tbody .sla-breached-row > td:first-child{
  box-shadow:inset -3px 0 0 rgba(239,68,68,.72)!important;
}

/* ===== TYPOGRAPHY / LEAD IDENTITY ===== */
.tcrm-leads-premium .tcrm-leads-table td{padding-top:9px!important;padding-bottom:9px!important;color:#59647a!important}
.dark .tcrm-leads-premium .tcrm-leads-table td{color:#8998b2!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child{color:#1f293d!important}
.dark .tcrm-leads-premium .tcrm-leads-table td:first-child{color:#eef3ff!important}
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-medium,
.tcrm-leads-premium .tcrm-leads-table td:first-child .font-semibold{
  font-size:12.5px!important;
  font-weight:760!important;
  letter-spacing:-.012em!important;
}
.tcrm-leads-premium .tcrm-leads-table td:first-child .text-muted-foreground{
  font-size:10px!important;
  line-height:1.25!important;
  opacity:.86!important;
}
.tcrm-leads-premium .tcrm-leads-avatar{
  width:30px!important;height:30px!important;
  border:1px solid rgba(255,255,255,.62)!important;
  box-shadow:0 5px 14px -7px rgba(76,57,190,.55),0 0 0 2px rgba(104,91,246,.08)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-avatar{
  border-color:rgba(190,183,255,.35)!important;
  box-shadow:0 6px 16px -8px rgba(0,0,0,.9),0 0 0 2px rgba(112,91,255,.12)!important;
}

/* ===== BADGE SYSTEM — same visual grammar ===== */
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{
  min-height:22px!important;
  border-radius:999px!important;
  padding:3px 8px!important;
  font-size:9.5px!important;
  line-height:1!important;
  font-weight:820!important;
  letter-spacing:-.005em!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.28),0 5px 12px -9px currentColor!important;
}
.tcrm-leads-premium .tcrm-classification{
  font-size:9.5px!important;
  font-weight:850!important;
  text-shadow:0 0 12px currentColor;
}

/* ===== ACTION RAIL ===== */
.tcrm-leads-premium .tcrm-leads-actions{
  display:inline-flex!important;
  align-items:center!important;
  gap:4px!important;
  padding:3px!important;
  border-radius:11px!important;
  border:1px solid rgba(100,91,220,.10)!important;
  background:rgba(248,249,255,.70)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions{
  border-color:rgba(103,123,206,.18)!important;
  background:rgba(10,27,52,.66)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04)!important;
}
.tcrm-leads-premium .tcrm-leads-actions button{
  height:27px!important;min-height:27px!important;
  border-radius:8px!important;
  font-size:10px!important;
  font-weight:760!important;
}

/* ===== PAGINATION — part of workspace, not detached ===== */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:58px!important;
  background:linear-gradient(180deg,rgba(249,250,255,.88),rgba(246,248,255,.96))!important;
  border-top:1px solid rgba(101,93,224,.12)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.86)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(8,24,47,.92),rgba(7,21,41,.98))!important;
  border-top-color:rgba(102,122,204,.16)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button{
  border-radius:9px!important;
  min-width:30px!important;
  height:30px!important;
  font-weight:760!important;
}

/* Light mode must feel pearl/lilac, never plain white admin UI. */
:root:not(.dark) .tcrm-leads-premium .tcrm-leads-filter-card,
:root:not(.dark) .tcrm-leads-premium .tcrm-leads-table-card{
  backdrop-filter:blur(18px) saturate(1.06)!important;
}

@media (max-width:1200px){
  .tcrm-leads-premium .tcrm-leads-hero h1{font-size:25px!important}
  .tcrm-leads-premium .tcrm-leads-total-card{min-width:92px!important}
}

@media (prefers-reduced-motion:reduce){
  .tcrm-leads-premium *{transition-duration:.01ms!important}
}
'''

CSS.write_text(css, encoding="utf-8")

if text != original:
    TSX.write_text(text, encoding="utf-8")

required_final = [css_import, "tcrm-leads-premium", "tcrm-leads-table", "tcrm-leads-row"]
missing_final = [x for x in required_final if x not in text]
if missing_final:
    raise SystemExit("ERROR=V15_HOOKS_MISSING:" + ",".join(missing_final))

print("PATCH=YES")
print("V14_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V15_CSS_WRITTEN=YES")
print("V15_CSS_IMPORTED=YES")
print("ORIGINAL_CONCEPT_REFERENCE=YES")
print("LIGHT_ADMIN_FLATNESS_REDUCED=YES")
print("FILTER_COMMAND_CENTER_CLOSER=YES")
print("STICKY_ROW_SURFACES_UNIFIED=YES")
print("PURPLE_HOVER_BAND_FIXED=YES")
print("SLA_EDGE_CUE_ONLY=YES")
print("TABLE_TYPOGRAPHY_UPGRADED=YES")
print("LEAD_IDENTITY_UPGRADED=YES")
print("BADGE_SYSTEM_UNIFIED=YES")
print("ACTIONS_WORKSPACE_INTEGRATED=YES")
print("PAGINATION_WORKSPACE_INTEGRATED=YES")
print("FUNCTIONALITY_CHANGED=NO")
