#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/SalesFunnelDashboard.tsx"
CSS = ROOT / "client/src/sales-funnel-premium-v1-reference.css"
MARKER = "TCRM_SALES_FUNNEL_PREMIUM_V1_LIGHT_DARK_REFERENCE_MATCH"

if not TSX.exists():
    raise SystemExit(f"Missing target: {TSX}")

src = TSX.read_text(encoding="utf-8")

if MARKER not in src:
    anchor = 'import { DeveloperListPreview, DeveloperStageCardsPreview, DeveloperTablePreviewRows, DeveloperVisualPreview } from "@/components/DeveloperEmptyVisual";\n'
    if anchor not in src:
        raise SystemExit("Import anchor not found; source changed, aborting safely.")
    src = src.replace(anchor, anchor + 'import "../sales-funnel-premium-v1-reference.css";\n\n// ' + MARKER + '\n', 1)

replacements = [
    (
        '<div className="p-6 space-y-6 fade-in" dir={isRTL ? "rtl" : "ltr"}>',
        '<div className="sales-funnel-premium-v1 p-4 md:p-5 space-y-4 fade-in" dir={isRTL ? "rtl" : "ltr"}>'
    ),
    (
        '<div className="grid grid-cols-2 md:grid-cols-5 gap-4 stagger-children">',
        '<div className="sf-kpi-grid grid grid-cols-2 md:grid-cols-5 gap-3 stagger-children">'
    ),
    (
        '<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">',
        '<div className="sf-primary-grid grid grid-cols-1 lg:grid-cols-2 gap-4">'
    ),
    (
        '<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">',
        '<div className="sf-campaign-grid grid grid-cols-1 lg:grid-cols-3 gap-4">'
    ),
    (
        '{/* Deal Summary */}\n          <Card className="slide-up"',
        '{/* Deal Summary */}\n          <Card className="sf-deal-summary slide-up"'
    ),
    (
        '{/* Campaign Performance Table */}\n        <Card className="slide-up"',
        '{/* Campaign Performance Table */}\n        <Card className="sf-campaign-table slide-up"'
    ),
    (
        '{/* Conversion Rates Stage-by-Stage */}\n        <Card className="slide-up"',
        '{/* Conversion Rates Stage-by-Stage */}\n        <Card className="sf-stage-conversion slide-up"'
    ),
]

for old, new in replacements:
    if old in src:
        src = src.replace(old, new, 1)
    elif new not in src:
        raise SystemExit(f"Expected source fragment not found:\n{old}")

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Sales Funnel Premium V1 — Light/Dark Reference Match
Scope: SalesFunnelDashboard only.
Visual target: approved ChatGPT reference (dual light/dark executive analytics dashboard).
No data, route, permission, backend, chart logic, or sidebar behavior changes.
*/

.sales-funnel-premium-v1{
  --sf-violet:#5b5ce2;
  --sf-indigo:#4f46d8;
  --sf-blue:#3b82f6;
  --sf-cyan:#06b6d4;
  --sf-green:#22c55e;
  --sf-amber:#f59e0b;
  --sf-red:#ef4444;
  --sf-text:#17233d;
  --sf-muted:#6f7d98;
  --sf-border:rgba(92,102,173,.16);
  --sf-card:rgba(255,255,255,.92);
  --sf-card-strong:#ffffff;
  --sf-shadow:0 12px 34px -24px rgba(48,58,130,.35),0 2px 7px rgba(57,68,140,.055);
  position:relative;
  min-height:100%;
  isolation:isolate;
  color:var(--sf-text);
  background:
    radial-gradient(circle at 13% 2%,rgba(112,103,245,.09),transparent 22%),
    radial-gradient(circle at 88% 8%,rgba(62,135,255,.07),transparent 25%),
    linear-gradient(180deg,#f8f9ff 0%,#fbfcff 34%,#f7f9ff 100%);
}
.sales-funnel-premium-v1::before{
  content:"";
  position:absolute;
  inset:0;
  z-index:-1;
  pointer-events:none;
  opacity:.20;
  background-image:radial-gradient(circle,rgba(88,92,210,.14) .7px,transparent .85px);
  background-size:24px 24px;
  mask-image:linear-gradient(to bottom,#000 0,rgba(0,0,0,.55) 17%,transparent 42%);
}

/* Reference hero: luminous lilac executive strip, compact and high-contrast. */
.sales-funnel-premium-v1 > div:first-child{
  min-height:94px!important;
  margin-bottom:0!important;
  padding:18px 20px!important;
  border:1px solid rgba(96,89,218,.16)!important;
  border-radius:16px!important;
  background:
    radial-gradient(circle at 78% 28%,rgba(255,255,255,.32),transparent 24%),
    linear-gradient(112deg,#7773d6 0%,#7779dc 42%,#6868d6 72%,#5e56ca 100%)!important;
  box-shadow:0 14px 32px -22px rgba(66,61,178,.62),inset 0 1px 0 rgba(255,255,255,.28)!important;
}
.sales-funnel-premium-v1 > div:first-child h1{font-size:20px!important;font-weight:800!important;letter-spacing:-.02em!important;}
.sales-funnel-premium-v1 > div:first-child p{font-size:12px!important;opacity:.94;}
.sales-funnel-premium-v1 > div:first-child button,
.sales-funnel-premium-v1 > div:first-child [role="button"]{
  min-height:38px!important;
  border-radius:10px!important;
  border-color:rgba(255,255,255,.22)!important;
  color:#fff!important;
  background:rgba(48,43,155,.58)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 7px 18px -13px rgba(22,20,92,.8)!important;
}

/* KPI row */
.sales-funnel-premium-v1 .sf-kpi-grid > *{
  position:relative;
  min-height:136px;
  overflow:hidden;
  border:1px solid var(--sf-border)!important;
  border-radius:14px!important;
  background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(249,250,255,.93))!important;
  box-shadow:var(--sf-shadow)!important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;
}
.sales-funnel-premium-v1 .sf-kpi-grid > *::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:3px;
  background:linear-gradient(90deg,#6759df,#3f80ee,#25c2b1);
  opacity:.96;
}
.sales-funnel-premium-v1 .sf-kpi-grid > *:nth-child(2)::before{background:linear-gradient(90deg,#20bb73,#29c696);}
.sales-funnel-premium-v1 .sf-kpi-grid > *:nth-child(3)::before{background:linear-gradient(90deg,#7466eb,#4f7df1);}
.sales-funnel-premium-v1 .sf-kpi-grid > *:nth-child(4)::before{background:linear-gradient(90deg,#5267e8,#22b8bd);}
.sales-funnel-premium-v1 .sf-kpi-grid > *:nth-child(5)::before{background:linear-gradient(90deg,#f0a00c,#f59e0b);}
.sales-funnel-premium-v1 .sf-kpi-grid > *:hover{
  transform:translateY(-2px);
  border-color:rgba(91,92,226,.25)!important;
  box-shadow:0 18px 38px -25px rgba(55,61,151,.42),0 4px 12px rgba(57,68,140,.07)!important;
}
.sales-funnel-premium-v1 .sf-kpi-grid .kpi-icon{
  border-radius:10px!important;
  box-shadow:0 7px 16px -9px color-mix(in srgb,currentColor 45%,transparent)!important;
}
.sales-funnel-premium-v1 .sf-kpi-grid .text-2xl{font-size:24px!important;line-height:1!important;letter-spacing:-.025em;}
.sales-funnel-premium-v1 .sf-kpi-grid .text-muted-foreground{color:var(--sf-muted)!important;}

/* Unified premium analytics panels */
.sales-funnel-premium-v1 .chart-container,
.sales-funnel-premium-v1 .sf-deal-summary,
.sales-funnel-premium-v1 .sf-campaign-table,
.sales-funnel-premium-v1 .sf-stage-conversion{
  border:1px solid var(--sf-border)!important;
  border-radius:14px!important;
  background:var(--sf-card)!important;
  box-shadow:var(--sf-shadow)!important;
  overflow:hidden;
}
.sales-funnel-premium-v1 .chart-container > div:first-child,
.sales-funnel-premium-v1 .sf-deal-summary > div:first-child,
.sales-funnel-premium-v1 .sf-campaign-table > div:first-child,
.sales-funnel-premium-v1 .sf-stage-conversion > div:first-child{
  min-height:50px;
  border-bottom:1px solid rgba(96,107,176,.09);
  background:linear-gradient(180deg,rgba(250,251,255,.92),rgba(255,255,255,.72));
}
.sales-funnel-premium-v1 [class*="CardTitle"],
.sales-funnel-premium-v1 .font-semibold{letter-spacing:-.01em;}
.sales-funnel-premium-v1 .chart-container svg.lucide,
.sales-funnel-premium-v1 .sf-deal-summary svg.lucide,
.sales-funnel-premium-v1 .sf-stage-conversion svg.lucide{color:#5362dd;}

/* Funnel bars: keep business colors, add reference depth. */
.sales-funnel-premium-v1 .sf-primary-grid .group > .flex-1 > div{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.24),0 5px 12px -9px rgba(29,45,110,.55);
  border-radius:6px!important;
}
.sales-funnel-premium-v1 .sf-primary-grid .text-muted-foreground{color:#73809a!important;}

/* Recharts clarity */
.sales-funnel-premium-v1 .recharts-cartesian-grid line{stroke:rgba(96,108,166,.13)!important;}
.sales-funnel-premium-v1 .recharts-text{fill:#71809a!important;}
.sales-funnel-premium-v1 .recharts-line-curve{filter:drop-shadow(0 4px 6px rgba(79,70,216,.13));}
.sales-funnel-premium-v1 .recharts-default-tooltip{
  border-radius:10px!important;
  border-color:rgba(91,92,226,.16)!important;
  box-shadow:0 12px 28px -18px rgba(41,48,117,.35)!important;
}

/* Deal Summary reference treatment */
.sales-funnel-premium-v1 .sf-deal-summary [class*="bg-muted"]{
  border:1px solid rgba(95,106,171,.09);
  border-radius:10px!important;
  background:linear-gradient(135deg,#fafbff,#f6f8ff)!important;
}
.sales-funnel-premium-v1 .sf-deal-summary [class*="bg-muted"]:hover{
  border-color:rgba(91,92,226,.18);
  background:linear-gradient(135deg,#f8f9ff,#f2f4ff)!important;
}

/* Campaign table */
.sales-funnel-premium-v1 .sf-campaign-table table{border-collapse:separate;border-spacing:0;}
.sales-funnel-premium-v1 .sf-campaign-table thead tr{
  background:linear-gradient(180deg,#f6f7fc,#f2f4fb)!important;
}
.sales-funnel-premium-v1 .sf-campaign-table th{
  color:#64718b!important;
  font-size:11px!important;
  font-weight:700!important;
  letter-spacing:.01em;
}
.sales-funnel-premium-v1 .sf-campaign-table td{font-size:12px;border-color:rgba(94,105,164,.10)!important;}
.sales-funnel-premium-v1 .sf-campaign-table tbody tr:hover{background:rgba(91,92,226,.035)!important;}
.sales-funnel-premium-v1 .sf-campaign-table tbody tr:last-child{border-bottom:0!important;}

/* Stage conversion mini cards */
.sales-funnel-premium-v1 .sf-stage-conversion .stagger-children > div{
  min-width:132px!important;
  flex:1 1 132px;
  border-color:rgba(92,102,167,.13)!important;
  border-radius:10px!important;
  background:linear-gradient(145deg,#fff,#f9faff)!important;
  box-shadow:0 8px 20px -18px rgba(48,58,130,.35);
}
.sales-funnel-premium-v1 .sf-stage-conversion .stagger-children > div:hover{
  transform:translateY(-1px);
  border-color:rgba(91,92,226,.22)!important;
  box-shadow:0 12px 22px -18px rgba(48,58,130,.42)!important;
}

/* DARK — deep executive navy counterpart from the approved reference. */
.dark .sales-funnel-premium-v1{
  --sf-text:#eef3ff;
  --sf-muted:#8e9bb8;
  --sf-border:rgba(110,127,201,.18);
  --sf-card:rgba(8,16,28,.96);
  --sf-card-strong:#0a1423;
  --sf-shadow:0 18px 40px -28px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.025);
  background:
    radial-gradient(circle at 12% 2%,rgba(70,76,215,.13),transparent 23%),
    radial-gradient(circle at 86% 7%,rgba(34,102,211,.09),transparent 26%),
    linear-gradient(180deg,#050a12 0%,#07101b 42%,#050b13 100%);
}
.dark .sales-funnel-premium-v1::before{opacity:.10;background-image:radial-gradient(circle,rgba(118,132,230,.28) .7px,transparent .85px);}
.dark .sales-funnel-premium-v1 > div:first-child{
  border-color:rgba(104,111,236,.22)!important;
  background:
    radial-gradient(circle at 76% 35%,rgba(108,89,255,.13),transparent 26%),
    linear-gradient(112deg,#111d3e 0%,#172653 43%,#1a2254 73%,#2d1f67 100%)!important;
  box-shadow:0 18px 38px -25px rgba(30,39,118,.95),inset 0 1px 0 rgba(255,255,255,.06)!important;
}
.dark .sales-funnel-premium-v1 > div:first-child button,
.dark .sales-funnel-premium-v1 > div:first-child [role="button"]{
  background:rgba(35,30,115,.68)!important;
  border-color:rgba(126,132,255,.22)!important;
}
.dark .sales-funnel-premium-v1 .sf-kpi-grid > *{
  border-color:rgba(107,125,202,.16)!important;
  background:linear-gradient(145deg,rgba(8,17,30,.98),rgba(5,13,24,.96))!important;
  box-shadow:var(--sf-shadow)!important;
}
.dark .sales-funnel-premium-v1 .sf-kpi-grid > *:hover{border-color:rgba(102,112,242,.30)!important;}
.dark .sales-funnel-premium-v1 .sf-kpi-grid .text-foreground{color:#f4f7ff!important;}
.dark .sales-funnel-premium-v1 .sf-kpi-grid .text-muted-foreground{color:#8493af!important;}
.dark .sales-funnel-premium-v1 .chart-container,
.dark .sales-funnel-premium-v1 .sf-deal-summary,
.dark .sales-funnel-premium-v1 .sf-campaign-table,
.dark .sales-funnel-premium-v1 .sf-stage-conversion{
  border-color:rgba(104,121,190,.16)!important;
  background:linear-gradient(145deg,rgba(8,15,25,.98),rgba(7,14,24,.96))!important;
  box-shadow:var(--sf-shadow)!important;
}
.dark .sales-funnel-premium-v1 .chart-container > div:first-child,
.dark .sales-funnel-premium-v1 .sf-deal-summary > div:first-child,
.dark .sales-funnel-premium-v1 .sf-campaign-table > div:first-child,
.dark .sales-funnel-premium-v1 .sf-stage-conversion > div:first-child{
  border-color:rgba(105,120,189,.10);
  background:linear-gradient(180deg,rgba(12,22,36,.94),rgba(8,16,28,.88));
}
.dark .sales-funnel-premium-v1 .text-foreground,
.dark .sales-funnel-premium-v1 .font-semibold,
.dark .sales-funnel-premium-v1 .font-bold{color:#edf3ff!important;}
.dark .sales-funnel-premium-v1 .text-muted-foreground{color:#8897b3!important;}
.dark .sales-funnel-premium-v1 .recharts-cartesian-grid line{stroke:rgba(115,132,191,.12)!important;}
.dark .sales-funnel-premium-v1 .recharts-text{fill:#8191ac!important;}
.dark .sales-funnel-premium-v1 .sf-deal-summary [class*="bg-muted"]{
  border-color:rgba(106,122,188,.10)!important;
  background:linear-gradient(135deg,#0b1727,#091421)!important;
}
.dark .sales-funnel-premium-v1 .sf-deal-summary [class*="bg-muted"]:hover{
  border-color:rgba(102,112,242,.20)!important;
  background:linear-gradient(135deg,#0d1b2e,#0a1727)!important;
}
.dark .sales-funnel-premium-v1 .sf-campaign-table thead tr{background:linear-gradient(180deg,#0d1828,#0a1421)!important;}
.dark .sales-funnel-premium-v1 .sf-campaign-table th{color:#8695b2!important;}
.dark .sales-funnel-premium-v1 .sf-campaign-table td{border-color:rgba(101,117,178,.10)!important;}
.dark .sales-funnel-premium-v1 .sf-campaign-table tbody tr:hover{background:rgba(94,103,230,.055)!important;}
.dark .sales-funnel-premium-v1 .sf-stage-conversion .stagger-children > div{
  border-color:rgba(105,122,190,.14)!important;
  background:linear-gradient(145deg,#0b1625,#08131f)!important;
  box-shadow:0 12px 24px -20px rgba(0,0,0,.85);
}

@media (max-width:1280px){
  .sales-funnel-premium-v1{padding:16px!important;}
  .sales-funnel-premium-v1 .sf-kpi-grid{gap:10px!important;}
}
@media (max-width:768px){
  .sales-funnel-premium-v1 > div:first-child{padding:16px!important;}
  .sales-funnel-premium-v1 .sf-kpi-grid > *{min-height:124px;}
}
'''

CSS.write_text(css, encoding="utf-8")
print("PATCH=YES")
print("SALES_FUNNEL_PREMIUM_V1=YES")
print("LIGHT_DARK_REFERENCE_MATCH=YES")
print("FILES_CHANGED=client/src/pages/SalesFunnelDashboard.tsx,client/src/sales-funnel-premium-v1-reference.css")
print("SOURCE_PROJECT_PUSHED=NO")
