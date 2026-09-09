#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-2.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1.css";',
    'import "../leads-premium-v1-1.css";',
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
    raise SystemExit("ERROR=LEADS_V11_REQUIRED_MISSING:" + ",".join(missing))

css_import = 'import "../leads-premium-v1-2.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-1.css";'
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

css = r'''/* TCRM Leads Premium V1.2 — 1:1 fidelity upgrade toward approved concept */

.tcrm-leads-premium{
  --v12-pearl:#f7f7ff;
  --v12-ink:#121a2c;
  --v12-violet:#6d5dfc;
  --v12-indigo:#4f63ff;
  --v12-cyan:#36bffa;
  --v12-panel:rgba(255,255,255,.91);
  --v12-panel-strong:rgba(255,255,255,.985);
  --v12-panel-soft:rgba(249,250,255,.88);
  --v12-line:rgba(103,91,246,.16);
  --v12-line-strong:rgba(103,91,246,.28);
  --v12-shadow:0 28px 70px -46px rgba(63,55,160,.42),0 12px 34px -28px rgba(50,61,120,.28);
  position:relative;
}

.dark .tcrm-leads-premium{
  --v12-pearl:#07111f;
  --v12-ink:#f5f7ff;
  --v12-panel:rgba(8,23,43,.92);
  --v12-panel-strong:rgba(9,25,47,.985);
  --v12-panel-soft:rgba(10,28,53,.84);
  --v12-line:rgba(110,126,232,.22);
  --v12-line-strong:rgba(117,104,255,.42);
  --v12-shadow:0 30px 82px -50px rgba(0,0,0,.95),0 0 44px -34px rgba(84,70,255,.52);
}

/* ===== Page atmosphere / hierarchy ===== */
.tcrm-leads-premium::before{
  background:
    radial-gradient(720px 420px at 4% -2%,rgba(111,76,255,.10),transparent 62%),
    radial-gradient(760px 440px at 96% 2%,rgba(66,129,255,.095),transparent 64%),
    radial-gradient(520px 340px at 58% 88%,rgba(175,119,255,.055),transparent 68%),
    linear-gradient(180deg,#fcfcff 0%,#f7f8ff 52%,#f4f6ff 100%)!important;
}
.dark .tcrm-leads-premium::before{
  background:
    radial-gradient(840px 480px at 2% -5%,rgba(76,64,255,.22),transparent 62%),
    radial-gradient(860px 500px at 98% 0%,rgba(40,104,255,.16),transparent 65%),
    radial-gradient(680px 440px at 60% 84%,rgba(117,52,255,.10),transparent 70%),
    linear-gradient(180deg,#050d19 0%,#071426 48%,#06111f 100%)!important;
}

/* ===== Hero — more layered, aurora, luxury ===== */
.tcrm-leads-premium .tcrm-leads-hero{
  min-height:96px!important;
  padding:20px 22px!important;
  border-radius:22px!important;
  border:1px solid rgba(105,87,255,.23)!important;
  background:
    radial-gradient(78% 220% at 68% 18%,rgba(108,77,255,.18),transparent 52%),
    radial-gradient(62% 180% at 92% 88%,rgba(201,111,255,.12),transparent 54%),
    linear-gradient(118deg,rgba(253,253,255,.985),rgba(246,244,255,.975) 52%,rgba(251,247,255,.985))!important;
  box-shadow:
    0 34px 76px -44px rgba(80,61,200,.50),
    0 14px 32px -26px rgba(55,68,145,.28),
    inset 0 1px 0 rgba(255,255,255,.96),
    inset 0 -1px 0 rgba(102,82,255,.05)!important;
  isolation:isolate;
}
.tcrm-leads-premium .tcrm-leads-hero::after{
  content:"";
  position:absolute;
  inset:0;
  pointer-events:none;
  z-index:0;
  opacity:.58;
  background:
    linear-gradient(100deg,transparent 0 64%,rgba(114,88,255,.10) 64.3% 64.7%,transparent 65%),
    radial-gradient(circle at 72% 132%,transparent 0 26%,rgba(105,93,255,.16) 26.4% 26.7%,transparent 27.1%),
    radial-gradient(circle at 72% 132%,transparent 0 38%,rgba(152,90,255,.11) 38.4% 38.7%,transparent 39.1%);
  mix-blend-mode:multiply;
}
.dark .tcrm-leads-premium .tcrm-leads-hero{
  border-color:rgba(123,100,255,.48)!important;
  background:
    radial-gradient(85% 230% at 65% 12%,rgba(76,81,255,.38),transparent 52%),
    radial-gradient(72% 200% at 95% 86%,rgba(173,55,255,.30),transparent 56%),
    linear-gradient(116deg,rgba(8,21,49,.99),rgba(13,28,71,.985) 50%,rgba(40,19,92,.985))!important;
  box-shadow:
    0 36px 84px -48px rgba(21,28,97,.96),
    0 0 52px -34px rgba(112,77,255,.78),
    inset 0 1px 0 rgba(255,255,255,.08),
    inset 0 -1px 0 rgba(123,101,255,.12)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-hero::after{
  opacity:.74;
  mix-blend-mode:screen;
  background:
    linear-gradient(100deg,transparent 0 64%,rgba(139,105,255,.16) 64.3% 64.7%,transparent 65%),
    radial-gradient(circle at 72% 132%,transparent 0 26%,rgba(107,110,255,.22) 26.4% 26.7%,transparent 27.1%),
    radial-gradient(circle at 72% 132%,transparent 0 38%,rgba(180,68,255,.17) 38.4% 38.7%,transparent 39.1%);
}
.tcrm-leads-premium .tcrm-leads-hero-inner{position:relative;z-index:2;min-height:56px!important}
.tcrm-leads-premium .tcrm-leads-hero h1{font-size:27px!important;letter-spacing:-.045em!important;text-shadow:0 1px 0 rgba(255,255,255,.45)}
.dark .tcrm-leads-premium .tcrm-leads-hero h1{text-shadow:0 0 20px rgba(147,129,255,.22)}
.tcrm-leads-premium .tcrm-leads-hero-subtitle{font-size:11.5px!important;color:#68728a!important}
.dark .tcrm-leads-premium .tcrm-leads-hero-subtitle{color:#b8c5df!important}

.tcrm-leads-premium .tcrm-leads-total-card{
  min-width:92px!important;
  height:54px!important;
  border-radius:15px!important;
  border:1px solid rgba(109,93,252,.20)!important;
  background:linear-gradient(145deg,rgba(255,255,255,.90),rgba(246,246,255,.74))!important;
  box-shadow:0 18px 36px -26px rgba(76,64,180,.55),inset 0 1px 0 rgba(255,255,255,.92),inset 0 -1px 0 rgba(103,91,246,.07)!important;
}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:18px!important;letter-spacing:-.03em;color:#272756!important}
.tcrm-leads-premium .tcrm-leads-total-card span{font-size:8.5px!important;letter-spacing:.015em;color:#777f95!important}
.dark .tcrm-leads-premium .tcrm-leads-total-card{
  border-color:rgba(139,121,255,.40)!important;
  background:linear-gradient(145deg,rgba(11,27,58,.80),rgba(19,29,71,.64))!important;
  box-shadow:0 18px 40px -28px rgba(0,0,0,.8),0 0 28px -18px rgba(110,85,255,.72),inset 0 1px 0 rgba(255,255,255,.085)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-total-card strong{color:#fff!important}
.dark .tcrm-leads-premium .tcrm-leads-total-card span{color:#aebbd6!important}

.tcrm-leads-premium .tcrm-leads-hero-actions>button,
.tcrm-leads-premium .tcrm-leads-hero-actions>a button{
  height:40px!important;
  border-radius:12px!important;
  padding-inline:15px!important;
  font-size:11px!important;
  font-weight:800!important;
  transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease,filter .16s ease!important;
}
.tcrm-leads-premium .tcrm-leads-hero-actions>button:hover,
.tcrm-leads-premium .tcrm-leads-hero-actions>a button:hover{transform:translateY(-1px);filter:saturate(1.08)}
.tcrm-leads-premium .tcrm-leads-hero-actions>button:last-child,
.tcrm-leads-premium .tcrm-leads-hero-actions>a:last-child button{
  box-shadow:0 15px 30px -18px rgba(92,54,220,.58),inset 0 1px 0 rgba(255,255,255,.22)!important;
}

/* ===== Filters — command center, not plain form ===== */
.tcrm-leads-premium .tcrm-leads-filter-card{
  position:relative;
  overflow:hidden;
  border-radius:21px!important;
  border:1px solid var(--v12-line)!important;
  background:
    radial-gradient(72% 120% at 3% 0%,rgba(108,92,246,.055),transparent 55%),
    linear-gradient(145deg,var(--v12-panel-strong),var(--v12-panel))!important;
  box-shadow:var(--v12-shadow),inset 0 1px 0 rgba(255,255,255,.93),inset 0 -1px 0 rgba(102,92,246,.045)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card::before{
  content:"";position:absolute;inset:0 0 auto 0;height:2px;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(113,91,255,.42),rgba(70,130,255,.28),transparent);
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{
  background:
    radial-gradient(85% 140% at 0% 0%,rgba(88,79,255,.11),transparent 60%),
    linear-gradient(145deg,rgba(8,22,43,.985),rgba(8,20,39,.965))!important;
  border-color:rgba(107,126,220,.27)!important;
  box-shadow:0 30px 76px -50px rgba(0,0,0,.96),0 0 36px -30px rgba(85,76,255,.55),inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card label{
  font-size:10px!important;
  font-weight:780!important;
  letter-spacing:.015em;
  color:#5f6980!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card label{color:#9eabc3!important}
.tcrm-leads-premium .tcrm-leads-filter-card input,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  min-height:38px;
  border-radius:11px!important;
  border-color:rgba(103,91,246,.16)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(249,249,255,.90))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.92),0 8px 18px -16px rgba(54,54,120,.30)!important;
  transition:border-color .16s ease,box-shadow .16s ease,background .16s ease,transform .16s ease!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card input:focus,
.tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:focus,
.tcrm-leads-premium .tcrm-leads-filter-card button:focus-visible{
  border-color:rgba(105,88,255,.48)!important;
  box-shadow:0 0 0 3px rgba(101,88,255,.10),0 10px 24px -18px rgba(90,71,220,.36),inset 0 1px 0 rgba(255,255,255,.95)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"],
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:not([role="checkbox"]){
  color:#e9efff!important;
  border-color:rgba(101,121,200,.28)!important;
  background:linear-gradient(180deg,rgba(13,30,57,.88),rgba(10,25,49,.82))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 10px 22px -18px rgba(0,0,0,.78)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input::placeholder{color:#687995!important}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input:focus,
.dark .tcrm-leads-premium .tcrm-leads-filter-card [role="combobox"]:focus,
.dark .tcrm-leads-premium .tcrm-leads-filter-card button:focus-visible{
  border-color:rgba(121,105,255,.56)!important;
  box-shadow:0 0 0 3px rgba(98,83,255,.13),0 0 28px -20px rgba(99,82,255,.72),inset 0 1px 0 rgba(255,255,255,.06)!important;
}
/* utility controls get a distinct premium rail */
.tcrm-leads-premium .tcrm-leads-filter-card button[class*="gap-"]{
  font-weight:750!important;
}
.tcrm-leads-premium .tcrm-leads-filter-card button[class*="destructive"]{
  box-shadow:0 10px 24px -17px rgba(239,68,68,.45)!important;
}

/* ===== Table shell ===== */
.tcrm-leads-premium .tcrm-leads-table-card{
  position:relative;
  overflow:hidden;
  border-radius:21px!important;
  border:1px solid var(--v12-line)!important;
  background:
    radial-gradient(90% 80% at 0% 0%,rgba(110,93,255,.025),transparent 60%),
    linear-gradient(180deg,var(--v12-panel-strong),var(--v12-panel-soft))!important;
  box-shadow:var(--v12-shadow),inset 0 1px 0 rgba(255,255,255,.92)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card::before{
  content:"";position:absolute;left:0;right:0;top:0;height:2px;z-index:5;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(98,90,255,.36),rgba(77,139,255,.24),transparent);
}
.dark .tcrm-leads-premium .tcrm-leads-table-card{
  background:
    radial-gradient(90% 90% at 0% 0%,rgba(85,79,255,.07),transparent 65%),
    linear-gradient(180deg,rgba(8,23,44,.985),rgba(7,19,37,.975))!important;
  border-color:rgba(102,123,211,.27)!important;
  box-shadow:0 34px 86px -54px rgba(0,0,0,.97),0 0 38px -32px rgba(84,76,255,.45),inset 0 1px 0 rgba(255,255,255,.04)!important;
}
.tcrm-leads-premium .tcrm-leads-table{border-collapse:separate!important;border-spacing:0!important}
.tcrm-leads-premium .tcrm-leads-table thead{position:sticky;top:0;z-index:25}
.tcrm-leads-premium .tcrm-leads-table-head > th{
  height:42px;
  color:#667087!important;
  font-size:10px!important;
  font-weight:820!important;
  letter-spacing:.012em;
  background:linear-gradient(180deg,rgba(248,249,255,.985),rgba(242,244,252,.96))!important;
  border-bottom:1px solid rgba(101,91,246,.13)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85),inset 0 -1px 0 rgba(101,91,246,.05)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-head > th{
  color:#98a8c3!important;
  background:linear-gradient(180deg,rgba(13,32,61,.985),rgba(11,27,52,.975))!important;
  border-bottom-color:rgba(100,120,204,.20)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035),inset 0 -1px 0 rgba(111,126,220,.08)!important;
}

/* ===== Rows — luminous operational density ===== */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td{
  height:48px;
  background:rgba(255,255,255,.54)!important;
  border-bottom:1px solid rgba(104,112,155,.055)!important;
  color:#4c566c;
  transition:background .15s ease,box-shadow .15s ease,color .15s ease!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td{
  background:rgba(248,249,255,.62)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  background:linear-gradient(90deg,rgba(105,92,246,.075),rgba(73,128,255,.045),rgba(255,255,255,.76))!important;
  box-shadow:inset 0 1px 0 rgba(103,91,246,.07),inset 0 -1px 0 rgba(103,91,246,.07)!important;
  color:#273148;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td{
  background:rgba(7,20,39,.76)!important;
  border-bottom-color:rgba(102,120,184,.075)!important;
  color:#94a2b9;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:nth-child(even) > td{
  background:rgba(9,25,48,.78)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row:hover > td{
  background:linear-gradient(90deg,rgba(73,73,183,.25),rgba(25,51,90,.68),rgba(10,29,56,.84))!important;
  box-shadow:inset 0 1px 0 rgba(118,111,255,.12),inset 0 -1px 0 rgba(118,111,255,.10),inset 3px 0 0 rgba(113,92,255,.55)!important;
  color:#dce6fa;
}
/* sticky surfaces must be visually seamless with the row */
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky{background:inherit!important;background-clip:padding-box!important}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky:first-child{box-shadow:8px 0 18px -18px rgba(52,56,105,.26)}
.tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky:last-child{box-shadow:-8px 0 18px -18px rgba(52,56,105,.26)}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky:first-child{box-shadow:10px 0 22px -18px rgba(0,0,0,.62)}
.dark .tcrm-leads-premium .tcrm-leads-table tbody .tcrm-leads-row > td.sticky:last-child{box-shadow:-10px 0 22px -18px rgba(0,0,0,.62)}

/* ===== Lead identity ===== */
.tcrm-leads-premium .tcrm-leads-avatar{
  width:31px!important;height:31px!important;
  border:1px solid rgba(255,255,255,.68)!important;
  box-shadow:0 8px 18px -10px rgba(84,56,180,.62),0 0 0 3px rgba(108,92,246,.06)!important;
  font-weight:850!important;
}
.dark .tcrm-leads-premium .tcrm-leads-avatar{
  border-color:rgba(188,181,255,.44)!important;
  box-shadow:0 8px 20px -10px rgba(0,0,0,.75),0 0 16px -9px rgba(111,91,255,.72),0 0 0 3px rgba(111,91,255,.07)!important;
}
.tcrm-leads-premium .tcrm-leads-table tbody td:first-child .font-medium{font-weight:760!important;letter-spacing:-.01em;color:#1d263b!important}
.dark .tcrm-leads-premium .tcrm-leads-table tbody td:first-child .font-medium{color:#f1f5ff!important}
.tcrm-leads-premium .tcrm-leads-table tbody td:first-child .text-muted-foreground{font-size:10px!important;color:#7b8498!important}
.dark .tcrm-leads-premium .tcrm-leads-table tbody td:first-child .text-muted-foreground{color:#8090aa!important}

/* ===== Premium chip system ===== */
.tcrm-leads-premium .tcrm-leads-table td span.rounded-full:not(.tcrm-leads-avatar),
.tcrm-leads-premium .tcrm-fit-badge,
.tcrm-leads-premium .tcrm-stage-badge{
  min-height:22px;
  padding-inline:8px!important;
  border-width:1px!important;
  font-size:10px!important;
  font-weight:800!important;
  letter-spacing:.005em;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.46),0 6px 13px -11px currentColor!important;
  backdrop-filter:blur(8px);
}
.dark .tcrm-leads-premium .tcrm-leads-table td span.rounded-full:not(.tcrm-leads-avatar),
.dark .tcrm-leads-premium .tcrm-fit-badge,
.dark .tcrm-leads-premium .tcrm-stage-badge{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 0 14px -10px currentColor!important;
}
.tcrm-leads-premium .tcrm-classification{
  font-size:10px!important;
  font-weight:850!important;
  letter-spacing:.005em;
  text-shadow:0 0 12px color-mix(in srgb,currentColor 22%,transparent);
}

/* ===== Actions rail ===== */
.tcrm-leads-premium .tcrm-leads-actions{
  display:inline-flex!important;
  align-items:center!important;
  gap:3px!important;
  padding:3px!important;
  border-radius:10px!important;
  border:1px solid rgba(101,91,246,.09)!important;
  background:rgba(247,248,255,.72)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.76)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions{
  border-color:rgba(102,121,205,.18)!important;
  background:rgba(14,31,59,.72)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035)!important;
}
.tcrm-leads-premium .tcrm-leads-actions button{
  height:26px!important;min-height:26px!important;min-width:26px!important;
  border-radius:7px!important;padding-inline:7px!important;
  color:#586178!important;
}
.tcrm-leads-premium .tcrm-leads-actions button:hover{
  color:#4f46e5!important;
  background:linear-gradient(180deg,rgba(112,92,246,.10),rgba(91,105,255,.07))!important;
  border-color:rgba(99,91,246,.18)!important;
  box-shadow:0 7px 15px -12px rgba(81,68,196,.42)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-actions button{color:#a8b5cf!important}
.dark .tcrm-leads-premium .tcrm-leads-actions button:hover{color:#fff!important;background:rgba(105,91,246,.16)!important;border-color:rgba(124,109,255,.28)!important;box-shadow:0 0 16px -10px rgba(109,88,255,.75)!important}

/* ===== Pagination / footer integrated ===== */
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  min-height:54px;
  background:linear-gradient(180deg,rgba(250,251,255,.76),rgba(246,248,255,.96))!important;
  border-top:1px solid rgba(99,91,246,.12)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.80)!important;
}
.dark .tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"]{
  background:linear-gradient(180deg,rgba(9,24,46,.80),rgba(7,20,39,.97))!important;
  border-top-color:rgba(103,122,208,.16)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025)!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button{
  border-radius:9px!important;
  transition:transform .15s ease,box-shadow .15s ease,background .15s ease!important;
}
.tcrm-leads-premium .tcrm-leads-table-card [class*="border-t"] button:hover{transform:translateY(-1px)}

/* Scrollbar polish for dense operational table */
.tcrm-leads-premium .tcrm-leads-table-card .overflow-x-auto{scrollbar-width:thin;scrollbar-color:rgba(102,91,246,.32) transparent}
.tcrm-leads-premium .tcrm-leads-table-card .overflow-x-auto::-webkit-scrollbar{height:7px}
.tcrm-leads-premium .tcrm-leads-table-card .overflow-x-auto::-webkit-scrollbar-thumb{background:linear-gradient(90deg,rgba(93,82,225,.28),rgba(115,92,246,.42));border-radius:999px}
.dark .tcrm-leads-premium .tcrm-leads-table-card .overflow-x-auto::-webkit-scrollbar-thumb{background:linear-gradient(90deg,rgba(101,86,255,.38),rgba(131,86,255,.56))}

@media (max-width:900px){
  .tcrm-leads-premium .tcrm-leads-hero{padding:16px!important;min-height:unset!important}
  .tcrm-leads-premium .tcrm-leads-total-card{min-width:82px!important;height:50px!important}
}

@media (prefers-reduced-motion:reduce){
  .tcrm-leads-premium *{transition-duration:.01ms!important;animation-duration:.01ms!important;animation-iteration-count:1!important}
}
'''

CSS.write_text(css, encoding="utf-8")

if text != original:
    TSX.write_text(text, encoding="utf-8")

required_final = [
    css_import,
    'tcrm-leads-premium',
    'tcrm-leads-hero',
    'tcrm-leads-filter-card',
    'tcrm-leads-table-card',
    'tcrm-leads-row',
    'tcrm-leads-actions',
]
missing_final = [x for x in required_final if x not in text]
if missing_final:
    raise SystemExit("ERROR=V12_FIDELITY_HOOKS_MISSING:" + ",".join(missing_final))

print("PATCH=YES")
print("V11_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V12_CSS_WRITTEN=YES")
print("V12_CSS_IMPORTED=YES")
print("HERO_FIDELITY_UPGRADED=YES")
print("FILTERS_FIDELITY_UPGRADED=YES")
print("TABLE_SHELL_UPGRADED=YES")
print("ROWS_UPGRADED=YES")
print("BADGES_UPGRADED=YES")
print("ACTIONS_UPGRADED=YES")
print("PAGINATION_UPGRADED=YES")
print("LIGHT_MODE_PREMIUM=YES")
print("DARK_MODE_PREMIUM=YES")
print("FUNCTIONALITY_CHANGED=NO")
