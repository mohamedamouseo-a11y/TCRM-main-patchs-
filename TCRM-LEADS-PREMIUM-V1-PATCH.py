#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

# Premium stylesheet import — idempotent.
css_import = 'import "../leads-premium-v1.css";'
if css_import not in text:
    anchor = 'import { countries } from "@/lib/countries-data";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate LeadsList import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

# Root hook.
old = 'className="p-6 space-y-6 fade-in" dir={isRTL ? "rtl" : "ltr"}'
new = 'className="p-6 space-y-6 fade-in tcrm-leads-premium" dir={isRTL ? "rtl" : "ltr"}'
if "tcrm-leads-premium" not in text:
    if old not in text:
        raise SystemExit("ERROR=Could not locate Leads root")
    text = text.replace(old, new, 1)

# Hero hooks.
hero_old = 'className="relative overflow-hidden rounded-2xl px-6 py-5 slide-up"'
hero_new = 'className="relative overflow-hidden rounded-2xl px-6 py-5 slide-up tcrm-leads-hero"'
if "tcrm-leads-hero" not in text:
    if hero_old not in text:
        raise SystemExit("ERROR=Could not locate Leads hero")
    text = text.replace(hero_old, hero_new, 1)

inner_old = 'className="relative flex items-center justify-between gap-3 flex-wrap"'
inner_new = 'className="relative flex items-center justify-between gap-3 flex-wrap tcrm-leads-hero-inner"'
if "tcrm-leads-hero-inner" not in text:
    if inner_old not in text:
        raise SystemExit("ERROR=Could not locate Leads hero inner")
    text = text.replace(inner_old, inner_new, 1)

# Add a compact total counter to the hero action area without changing behavior.
if "tcrm-leads-total-card" not in text:
    action_anchor = '          <div className="flex items-center gap-2">\n            {(user?.role === "Admin" || user?.role === "admin" || user?.role === "SalesManager") && ('
    replacement = '          <div className="flex items-center gap-2 tcrm-leads-hero-actions">\n            <div className="tcrm-leads-total-card">\n              <strong>{(data?.total ?? 0).toLocaleString()}</strong>\n              <span>{isRTL ? "إجمالي العملاء" : "Total Leads"}</span>\n            </div>\n            {(user?.role === "Admin" || user?.role === "admin" || user?.role === "SalesManager") && ('
    if action_anchor not in text:
        raise SystemExit("ERROR=Could not locate Leads hero actions")
    text = text.replace(action_anchor, replacement, 1)

# Filter card hook.
filter_old = '<Card className="rounded-[24px] border-border/60 shadow-sm">'
filter_new = '<Card className="rounded-[24px] border-border/60 shadow-sm tcrm-leads-filter-card">'
if "tcrm-leads-filter-card" not in text:
    if filter_old not in text:
        raise SystemExit("ERROR=Could not locate Leads filter card")
    text = text.replace(filter_old, filter_new, 1)

# Table card hook.
if "tcrm-leads-table-card" not in text:
    marker = '        </Card>\n\n        <Card>\n          <CardContent className="p-0">\n            {isLoading ? ('
    repl = '        </Card>\n\n        <Card className="tcrm-leads-table-card">\n          <CardContent className="p-0">\n            {isLoading ? ('
    if marker not in text:
        raise SystemExit("ERROR=Could not locate Leads table card")
    text = text.replace(marker, repl, 1)

# Table density hooks.
if "tcrm-leads-table" not in text:
    table_old = 'className="w-full min-w-[980px] text-sm" dir={isRTL ? "rtl" : "ltr"}'
    table_new = 'className="w-full min-w-[980px] text-sm tcrm-leads-table" dir={isRTL ? "rtl" : "ltr"}'
    if table_old not in text:
        raise SystemExit("ERROR=Could not locate Leads table")
    text = text.replace(table_old, table_new, 1)

if "tcrm-leads-table-head" not in text:
    head_old = 'className="border-b border-border bg-muted/30"'
    head_new = 'className="border-b border-border bg-muted/30 tcrm-leads-table-head"'
    if head_old not in text:
        raise SystemExit("ERROR=Could not locate Leads table head")
    text = text.replace(head_old, head_new, 1)

if "tcrm-leads-row" not in text:
    row_old = 'className={`border-b border-border hover:bg-muted/30 transition-colors ${'
    row_new = 'className={`border-b border-border hover:bg-muted/30 transition-colors tcrm-leads-row ${'
    if row_old not in text:
        raise SystemExit("ERROR=Could not locate Leads table rows")
    text = text.replace(row_old, row_new, 1)

# Header/cell-specific hooks.
if "tcrm-leads-th" not in text:
    base_old = 'const baseClass = `text-start px-4 py-3 font-medium text-muted-foreground whitespace-nowrap ${columnMeta[columnKey].minWidth}`;'
    base_new = 'const baseClass = `text-start px-4 py-3 font-medium text-muted-foreground whitespace-nowrap tcrm-leads-th ${columnMeta[columnKey].minWidth}`;'
    if base_old not in text:
        raise SystemExit("ERROR=Could not locate column header base class")
    text = text.replace(base_old, base_new, 1)

if "tcrm-leads-avatar" not in text:
    avatar_old = 'className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold shrink-0"'
    avatar_new = 'className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold shrink-0 tcrm-leads-avatar"'
    if avatar_old not in text:
        raise SystemExit("ERROR=Could not locate Lead avatar")
    text = text.replace(avatar_old, avatar_new, 1)

if "tcrm-fit-badge" not in text:
    fit_old = 'className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${'
    fit_new = 'className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap tcrm-fit-badge ${'
    if fit_old not in text:
        raise SystemExit("ERROR=Could not locate Fit badge")
    text = text.replace(fit_old, fit_new, 1)

if "tcrm-classification" not in text:
    cls_old = 'className="text-xs font-bold whitespace-nowrap" style={{ color: cfg.color }}'
    cls_new = 'className="text-xs font-bold whitespace-nowrap tcrm-classification" style={{ color: cfg.color }}'
    if cls_old not in text:
        raise SystemExit("ERROR=Could not locate Classification label")
    text = text.replace(cls_old, cls_new, 1)

if "tcrm-stage-badge" not in text:
    stage_old = 'className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-white whitespace-nowrap"'
    stage_new = 'className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-white whitespace-nowrap tcrm-stage-badge"'
    if stage_old not in text:
        raise SystemExit("ERROR=Could not locate Stage badge")
    text = text.replace(stage_old, stage_new, 1)

if "tcrm-leads-actions" not in text:
    action_old = 'className="flex items-center gap-1 whitespace-nowrap"'
    action_new = 'className="flex items-center gap-1 whitespace-nowrap tcrm-leads-actions"'
    if action_old not in text:
        raise SystemExit("ERROR=Could not locate action rail")
    text = text.replace(action_old, action_new, 1)

css = r'''/* TCRM Leads Premium V1 — approved Leads Command Workspace concept */
.tcrm-leads-premium{
  --leads-surface:rgba(255,255,255,.90);
  --leads-surface-strong:rgba(255,255,255,.97);
  --leads-border:rgba(99,102,241,.15);
  --leads-border-strong:rgba(99,102,241,.25);
  --leads-text:#182238;
  --leads-muted:#6c768d;
  --leads-row:rgba(248,250,255,.54);
  --leads-row-hover:rgba(99,102,241,.055);
  --leads-head:rgba(245,247,255,.94);
  --leads-shadow:0 22px 54px -36px rgba(59,55,160,.30);
  position:relative;isolation:isolate;min-height:100vh;
}
.tcrm-leads-premium::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:radial-gradient(circle at 12% 8%,rgba(124,58,237,.075),transparent 28rem),radial-gradient(circle at 88% 12%,rgba(59,130,246,.07),transparent 30rem),linear-gradient(180deg,#fbfcff 0%,#f5f7ff 100%)}
.dark .tcrm-leads-premium{--leads-surface:rgba(11,28,52,.90);--leads-surface-strong:rgba(12,31,57,.97);--leads-border:rgba(103,126,225,.24);--leads-border-strong:rgba(112,132,255,.42);--leads-text:#f1f5ff;--leads-muted:#95a3bd;--leads-row:rgba(10,27,50,.58);--leads-row-hover:rgba(94,91,255,.105);--leads-head:rgba(17,39,72,.96);--leads-shadow:0 26px 64px -38px rgba(0,0,0,.9)}
.dark .tcrm-leads-premium::before{background:radial-gradient(circle at 13% 7%,rgba(79,70,229,.18),transparent 29rem),radial-gradient(circle at 88% 9%,rgba(37,99,235,.13),transparent 31rem),linear-gradient(180deg,#07111f 0%,#081529 48%,#071426 100%)}

/* Hero */
.tcrm-leads-premium .tcrm-leads-hero{border:1px solid rgba(119,102,255,.22);border-radius:20px!important;padding:18px 20px!important;background:linear-gradient(115deg,rgba(248,248,255,.96),rgba(243,241,255,.93) 54%,rgba(250,244,255,.94))!important;box-shadow:0 18px 48px -30px rgba(86,70,210,.36),inset 0 1px 0 rgba(255,255,255,.88)}
.tcrm-leads-premium .tcrm-leads-hero::before{content:"";position:absolute;inset:-120% -15%;opacity:1!important;pointer-events:none;background:radial-gradient(ellipse at 18% 50%,rgba(114,78,255,.12),transparent 30%),radial-gradient(ellipse at 68% 42%,rgba(66,128,255,.12),transparent 32%),radial-gradient(ellipse at 92% 58%,rgba(181,74,255,.10),transparent 29%);animation:tcrmLeadsAurora 16s ease-in-out infinite alternate}
.tcrm-leads-premium .tcrm-leads-hero h1{color:#171d35!important;font-size:24px!important;line-height:1;font-weight:880!important;letter-spacing:-.04em}
.tcrm-leads-premium .tcrm-leads-hero p{color:#747d93!important;font-size:10px!important;font-weight:650}
.dark .tcrm-leads-premium .tcrm-leads-hero{border-color:rgba(114,93,255,.46);background:linear-gradient(112deg,rgba(15,31,67,.98),rgba(17,32,75,.96) 48%,rgba(50,22,96,.96))!important;box-shadow:0 24px 58px -30px rgba(34,37,125,.85),0 0 36px -24px rgba(130,74,255,.7),inset 0 1px 0 rgba(255,255,255,.07)}
.dark .tcrm-leads-premium .tcrm-leads-hero::before{background:radial-gradient(ellipse at 22% 50%,rgba(73,92,255,.35),transparent 28%),radial-gradient(ellipse at 68% 42%,rgba(84,42,230,.27),transparent 31%),radial-gradient(ellipse at 92% 58%,rgba(169,49,255,.30),transparent 29%)}
.dark .tcrm-leads-premium .tcrm-leads-hero h1{color:#fff!important}.dark .tcrm-leads-premium .tcrm-leads-hero p{color:#aab9d7!important}
.tcrm-leads-premium .tcrm-leads-hero-inner{min-height:58px}
.tcrm-leads-premium .tcrm-leads-hero-actions{position:relative;z-index:3}
.tcrm-leads-premium .tcrm-leads-total-card{min-width:84px;height:48px;border-radius:13px;padding:7px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid rgba(99,102,241,.16);background:rgba(255,255,255,.72);backdrop-filter:blur(16px);box-shadow:inset 0 1px 0 rgba(255,255,255,.75),0 12px 26px -20px rgba(70,58,180,.45)}
.tcrm-leads-premium .tcrm-leads-total-card strong{font-size:16px;line-height:1;font-weight:850;color:#292758}.tcrm-leads-premium .tcrm-leads-total-card span{margin-top:3px;font-size:8px;font-weight:700;color:#7b8397;white-space:nowrap}
.dark .tcrm-leads-premium .tcrm-leads-total-card{background:rgba(10,25,53,.58);border-color:rgba(134,117,255,.35);box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 0 25px -17px rgba(123,92,255,.8)}
.dark .tcrm-leads-premium .tcrm-leads-total-card strong{color:#fff}.dark .tcrm-leads-premium .tcrm-leads-total-card span{color:#a8b4ce}
.tcrm-leads-premium .tcrm-leads-hero-actions>button,.tcrm-leads-premium .tcrm-leads-hero-actions>a button{height:38px!important;border-radius:11px!important;font-size:11px!important;font-weight:750!important;box-shadow:0 12px 26px -18px rgba(51,48,150,.5)}
.dark .tcrm-leads-premium .tcrm-leads-hero-actions>button{background:rgba(14,30,61,.70)!important;color:#ecf2ff!important;border-color:rgba(129,142,220,.32)!important}

/* Filter command surface */
.tcrm-leads-premium .tcrm-leads-filter-card{border:1px solid var(--leads-border)!important;border-radius:18px!important;background:linear-gradient(145deg,var(--leads-surface-strong),var(--leads-surface))!important;box-shadow:var(--leads-shadow),inset 0 1px 0 rgba(255,255,255,.72)!important;backdrop-filter:blur(18px)}
.dark .tcrm-leads-premium .tcrm-leads-filter-card{box-shadow:0 24px 58px -38px rgba(0,0,0,.9),inset 0 1px 0 rgba(255,255,255,.045)!important}
.tcrm-leads-premium .tcrm-leads-filter-card [class*="CardContent"]{padding:15px!important}
.tcrm-leads-premium .tcrm-leads-filter-card label{font-size:9px!important;font-weight:800!important;letter-spacing:.012em;color:var(--leads-muted)!important}
.tcrm-leads-premium .tcrm-leads-filter-card input,.tcrm-leads-premium .tcrm-leads-filter-card button[role="combobox"],.tcrm-leads-premium .tcrm-leads-filter-card button[data-slot="select-trigger"],.tcrm-leads-premium .tcrm-leads-filter-card [data-radix-select-trigger]{height:36px!important;border-radius:10px!important;border-color:var(--leads-border)!important;background:rgba(248,250,255,.76)!important;color:var(--leads-text)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.76);transition:border-color .2s ease,box-shadow .2s ease,background .2s ease}
.dark .tcrm-leads-premium .tcrm-leads-filter-card input,.dark .tcrm-leads-premium .tcrm-leads-filter-card button[role="combobox"],.dark .tcrm-leads-premium .tcrm-leads-filter-card button[data-slot="select-trigger"],.dark .tcrm-leads-premium .tcrm-leads-filter-card [data-radix-select-trigger]{background:rgba(10,29,56,.86)!important;color:#eef3ff!important;border-color:rgba(100,124,217,.28)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.035)}
.tcrm-leads-premium .tcrm-leads-filter-card input:focus,.tcrm-leads-premium .tcrm-leads-filter-card button[role="combobox"]:focus{border-color:rgba(99,102,241,.48)!important;box-shadow:0 0 0 3px rgba(99,102,241,.08)!important}
.tcrm-leads-premium .tcrm-leads-filter-card>div>div>div>button{border-radius:10px}

/* Table command card */
.tcrm-leads-premium .tcrm-leads-table-card{overflow:hidden;border:1px solid var(--leads-border)!important;border-radius:18px!important;background:var(--leads-surface-strong)!important;box-shadow:var(--leads-shadow),inset 0 1px 0 rgba(255,255,255,.7)!important}
.dark .tcrm-leads-premium .tcrm-leads-table-card{background:rgba(8,25,48,.96)!important;box-shadow:0 26px 64px -40px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.045)!important}
.tcrm-leads-premium .tcrm-leads-table{border-collapse:separate;border-spacing:0;color:var(--leads-text)}
.tcrm-leads-premium .tcrm-leads-table-head{background:var(--leads-head)!important;border-color:var(--leads-border)!important}
.tcrm-leads-premium .tcrm-leads-th{height:38px;padding-top:8px!important;padding-bottom:8px!important;font-size:9px!important;text-transform:none;font-weight:800!important;color:var(--leads-muted)!important;letter-spacing:.008em;border-bottom:1px solid var(--leads-border)}
.tcrm-leads-premium .tcrm-leads-table td{height:44px;padding-top:7px!important;padding-bottom:7px!important;border-bottom:1px solid var(--leads-border);color:var(--leads-text);background:transparent;transition:background .18s ease,border-color .18s ease}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even) td{background:var(--leads-row)}
.tcrm-leads-premium .tcrm-leads-row:hover td{background:var(--leads-row-hover)!important;border-bottom-color:var(--leads-border-strong)}
.tcrm-leads-premium .tcrm-leads-table .sticky{background:var(--leads-surface-strong)!important}
.tcrm-leads-premium .tcrm-leads-row:nth-child(even) .sticky{background:color-mix(in srgb,var(--leads-surface-strong) 94%,#eef1ff 6%)!important}
.dark .tcrm-leads-premium .tcrm-leads-row:nth-child(even) .sticky{background:rgba(10,29,54,.98)!important}
.tcrm-leads-premium .tcrm-leads-row:hover .sticky{background:color-mix(in srgb,var(--leads-surface-strong) 92%,#6968ff 8%)!important}.dark .tcrm-leads-premium .tcrm-leads-row:hover .sticky{background:rgba(18,38,74,.98)!important}
.tcrm-leads-premium .tcrm-leads-avatar{width:30px!important;height:30px!important;border:1px solid rgba(255,255,255,.6);box-shadow:0 7px 18px -10px rgba(92,66,220,.75),0 0 0 4px rgba(99,102,241,.055)}
.dark .tcrm-leads-premium .tcrm-leads-avatar{box-shadow:0 0 18px -9px rgba(126,87,255,.9),0 0 0 4px rgba(106,86,255,.075)}
.tcrm-leads-premium .tcrm-fit-badge,.tcrm-leads-premium .tcrm-stage-badge{height:22px;padding-left:8px!important;padding-right:8px!important;font-size:9px!important;font-weight:800!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.35)}
.tcrm-leads-premium .tcrm-classification{font-size:9px!important;font-weight:850!important}
.tcrm-leads-premium .tcrm-leads-table td .text-xs{font-size:9.5px!important}.tcrm-leads-premium .tcrm-leads-table td .font-medium{font-weight:720!important}
.tcrm-leads-premium .tcrm-leads-actions{padding:2px;border-radius:9px;background:rgba(99,102,241,.035);border:1px solid transparent}
.dark .tcrm-leads-premium .tcrm-leads-actions{background:rgba(99,102,241,.075)}
.tcrm-leads-premium .tcrm-leads-actions button{height:27px!important;min-width:27px!important;border-radius:8px!important}.tcrm-leads-premium .tcrm-leads-actions button:hover{background:rgba(99,102,241,.10)!important;color:#625cf5!important}
.dark .tcrm-leads-premium .tcrm-leads-actions button:hover{background:rgba(111,103,255,.16)!important;color:#a9b5ff!important}
.tcrm-leads-premium .sla-breached-row td{background:rgba(239,68,68,.025)}.dark .tcrm-leads-premium .sla-breached-row td{background:rgba(239,68,68,.045)}

/* Pagination integration */
.tcrm-leads-premium .tcrm-leads-table-card [class*="pagination"],.tcrm-leads-premium .tcrm-leads-table-card nav{border-top-color:var(--leads-border)!important;background:linear-gradient(180deg,transparent,rgba(99,102,241,.025))}
.tcrm-leads-premium .tcrm-leads-table-card button{border-radius:9px}
.dark .tcrm-leads-premium .tcrm-leads-table-card button{border-color:rgba(108,126,208,.25)}

@keyframes tcrmLeadsAurora{0%{transform:translate3d(-2%,0,0) rotate(-1deg)}100%{transform:translate3d(2%,1%,0) rotate(1deg)}}
@media (max-width:1100px){.tcrm-leads-premium .tcrm-leads-total-card{display:none}.tcrm-leads-premium .tcrm-leads-hero{padding:15px!important}}
@media (prefers-reduced-motion:reduce){.tcrm-leads-premium .tcrm-leads-hero::before{animation:none!important}}
'''

CSS.write_text(css, encoding="utf-8")
TSX.write_text(text, encoding="utf-8")

required = [
    css_import,
    "tcrm-leads-premium",
    "tcrm-leads-hero",
    "tcrm-leads-total-card",
    "tcrm-leads-filter-card",
    "tcrm-leads-table-card",
    "tcrm-leads-table",
    "tcrm-leads-row",
    "tcrm-leads-actions",
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit("ERROR=PREMIUM_HOOKS_MISSING:" + ",".join(missing))

print("PATCH=YES")
print(f"TSX_CHANGED={'YES' if text != original else 'NO'}")
print("CSS_WRITTEN=YES")
print("CSS_IMPORTED=YES")
print("PREMIUM_HOOKS=YES")
print("FUNCTIONALITY_CHANGED=NO")
