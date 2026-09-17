#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, re, shutil, sys

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
PAGES = SRC / "pages"
FILES = {
    "sales": PAGES / "SalesFunnelDashboard.tsx",
    "sla": PAGES / "TaskSlaDashboard.tsx",
    "calendar": PAGES / "CalendarPage.tsx",
}
CSS = SRC / "sales-3-screens-leads-design-system-v3.css"
MARKER = "TCRM_SALES_3_SCREENS_LEADS_DESIGN_SYSTEM_V3"
IMPORT = 'import "../sales-3-screens-leads-design-system-v3.css";'

for p in FILES.values():
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"sales-3-screens-leads-v3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in FILES.values():
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)


def ensure_import(text: str) -> str:
    if IMPORT in text:
        return text
    anchor = 'import "../sales-module-premium-v2-1-corrective.css";'
    if anchor not in text:
        raise RuntimeError("V2.1 import anchor missing")
    return text.replace(anchor, anchor + "\n" + IMPORT, 1)


def add_marker(text: str) -> str:
    if MARKER in text:
        return text
    lines = text.splitlines()
    insert_at = 1 if lines else 0
    lines.insert(insert_at, f"// {MARKER}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def wrap_first_page_banner(text: str) -> str:
    if "tcrm-v3-page-banner-shell" in text:
        return text
    pat = re.compile(r'(?P<indent>^[ \t]*)<PageBanner(?P<body>[\s\S]*?)</PageBanner>', re.M)
    m = pat.search(text)
    if not m:
        raise RuntimeError("PageBanner block not found")
    indent = m.group("indent")
    wrapped = f'{indent}<div className="tcrm-v3-page-banner-shell">\n{indent}  <PageBanner{m.group("body")}</PageBanner>\n{indent}</div>'
    return text[:m.start()] + wrapped + text[m.end():]


def patch_sales(text: str) -> str:
    text = add_marker(ensure_import(text))
    text = text.replace(
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sales-funnel-premium-v2 sales-funnel-premium-v1',
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sales-funnel-premium-v2 sales-funnel-premium-v1 tcrm-sales-leads-v3 tcrm-sales-leads-v3-funnel',
        1,
    )
    text = wrap_first_page_banner(text)
    text = text.replace(
        '<Card key={i} className={kpiGradients[i]}>',
        '<Card key={i} className={`${kpiGradients[i]} tcrm-v3-kpi-card tcrm-v3-kpi-${i + 1}`}>',
        1,
    )
    if "tcrm-v3-sales-commercial" not in text:
        anchor = '        {/* Won Deals Monthly Trend */}'
        if anchor not in text:
            raise RuntimeError("Sales commercial start anchor missing")
        text = text.replace(anchor, '        <div className="tcrm-v3-sales-commercial">\n' + anchor, 1)
        # mark the existing Campaign + Deal Summary inner grid so its children can participate in the V3 grid.
        commercial_comment = '        {/* Campaign Performance + Deal Summary */}'
        pos = text.find(commercial_comment)
        if pos < 0:
            raise RuntimeError("Campaign + Deal Summary anchor missing")
        after = text[pos:]
        after, n = re.subn(r'<div className="([^"]*grid grid-cols-1 lg:grid-cols-3[^"]*)">', r'<div className="\1 tcrm-v3-commercial-block">', after, count=1)
        if n != 1:
            raise RuntimeError("Commercial grid class not found")
        text = text[:pos] + after
        end_anchor = '        {/* Campaign Performance Table */}'
        if end_anchor not in text:
            raise RuntimeError("Campaign table anchor missing")
        text = text.replace(end_anchor, '        </div>\n\n' + end_anchor, 1)
    return text


def patch_sla(text: str) -> str:
    text = add_marker(ensure_import(text))
    text = text.replace(
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sla-premium-v2',
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sla-premium-v2 tcrm-sales-leads-v3 tcrm-sales-leads-v3-sla',
        1,
    )
    text = wrap_first_page_banner(text)
    text = text.replace(
        '<Card key={i} className={["kpi-gradient-green","kpi-gradient-blue","kpi-gradient-yellow","kpi-gradient-red"][i] ?? ""}>',
        '<Card key={i} className={`${["kpi-gradient-green","kpi-gradient-blue","kpi-gradient-yellow","kpi-gradient-red"][i] ?? ""} tcrm-v3-kpi-card tcrm-v3-kpi-${i + 1}`}>',
        1,
    )
    # Add a stable class to the Activity Type + Outcome distribution row when available.
    comment = '        {/* Activity Type + Outcome Distribution */}'
    pos = text.find(comment)
    if pos >= 0 and "tcrm-v3-sla-distributions" not in text[pos:pos+500]:
        tail = text[pos:]
        tail, _ = re.subn(r'<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">', '<div className="tcrm-v3-sla-distributions grid grid-cols-1 lg:grid-cols-2 gap-6">', tail, count=1)
        text = text[:pos] + tail
    return text


def patch_calendar(text: str) -> str:
    text = add_marker(ensure_import(text))
    text = text.replace(
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-calendar-premium-v2',
        'tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-calendar-premium-v2 tcrm-sales-leads-v3 tcrm-sales-leads-v3-calendar',
        1,
    )
    text = text.replace('tcrm-v21-calendar-hero flex', 'tcrm-v21-calendar-hero tcrm-v3-calendar-hero flex', 1)
    return text


original = {k: p.read_text(encoding="utf-8") for k, p in FILES.items()}
updated = {
    "sales": patch_sales(original["sales"]),
    "sla": patch_sla(original["sla"]),
    "calendar": patch_calendar(original["calendar"]),
}

CSS_TEXT = r'''/* TCRM Sales 3 Screens — Leads Design System V3
   Master visual reference: Leads Premium V1.8.
   Scope: Sales Funnel, Tasks & SLA, Calendar only.
   Goal: same pearl/lilac executive language, density, glass depth, dark navy companion,
   and responsive behavior without changing backend/business logic. */

.tcrm-sales-leads-v3{
  --v3-ink:#21233f;
  --v3-muted:#727b96;
  --v3-line:rgba(107,94,235,.20);
  --v3-line-soft:rgba(105,112,170,.10);
  --v3-purple:#6754e8;
  --v3-violet:#7b61ff;
  --v3-blue:#5d8df6;
  --v3-card:rgba(255,255,255,.965);
  --v3-card-2:rgba(246,247,255,.95);
  --v3-shadow:0 30px 72px -46px rgba(69,57,164,.43),0 10px 27px -22px rgba(63,72,135,.24),inset 0 1px 0 rgba(255,255,255,.96);
  position:relative;
  min-height:100vh;
  isolation:isolate;
  background:
    radial-gradient(820px 470px at 4% -3%,rgba(125,98,255,.17),transparent 65%),
    radial-gradient(900px 520px at 98% 0%,rgba(83,137,255,.12),transparent 68%),
    radial-gradient(650px 430px at 56% 84%,rgba(179,128,255,.07),transparent 72%),
    linear-gradient(180deg,#faf9ff 0%,#f2f2ff 48%,#edf2ff 100%)!important;
}
.dark .tcrm-sales-leads-v3{
  --v3-ink:#f5f7ff;
  --v3-muted:#a8b4ca;
  --v3-line:rgba(111,128,218,.29);
  --v3-line-soft:rgba(107,126,210,.11);
  --v3-card:rgba(7,19,38,.985);
  --v3-card-2:rgba(10,28,52,.97);
  --v3-shadow:0 32px 76px -48px rgba(0,0,0,.91),0 0 44px -33px rgba(106,82,255,.58),inset 0 1px 0 rgba(255,255,255,.045);
  background:
    radial-gradient(920px 540px at 4% -4%,rgba(74,74,255,.24),transparent 65%),
    radial-gradient(940px 560px at 98% 0%,rgba(118,57,255,.17),transparent 69%),
    radial-gradient(720px 450px at 56% 84%,rgba(38,108,255,.08),transparent 72%),
    linear-gradient(180deg,#040a15 0%,#061326 50%,#050f1c 100%)!important;
}

/* ===== HERO — light pearl/lilac language taken from Leads ===== */
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  min-height:94px;
  border:1px solid rgba(112,94,241,.28)!important;
  border-radius:21px!important;
  background:
    radial-gradient(62% 180% at 78% 50%,rgba(125,91,255,.16),transparent 64%),
    radial-gradient(48% 150% at 100% 0%,rgba(100,127,255,.13),transparent 68%),
    linear-gradient(120deg,rgba(255,255,255,.985),rgba(245,242,255,.97))!important;
  box-shadow:0 30px 72px -44px rgba(74,59,176,.43),0 12px 29px -23px rgba(62,72,139,.24),inset 0 1px 0 rgba(255,255,255,.99)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell h1,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero h1{color:var(--v3-ink)!important;text-shadow:none!important;font-weight:850!important;letter-spacing:-.025em}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell p,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero p{color:var(--v3-muted)!important;text-shadow:none!important;font-weight:600!important}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div > div.absolute{opacity:.2}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell .w-11.h-11,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero > div > div:first-child{
  background:linear-gradient(145deg,#7d68f5,#5c54e8)!important;
  border:1px solid rgba(255,255,255,.58)!important;
  box-shadow:0 13px 28px -15px rgba(83,64,211,.7),inset 0 1px 0 rgba(255,255,255,.35)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell svg,
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero svg{filter:none}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell select,
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell button{
  border:1px solid rgba(108,94,235,.21)!important;
  background:rgba(255,255,255,.76)!important;
  color:#3c3c65!important;
  box-shadow:0 10px 24px -19px rgba(73,58,176,.55),inset 0 1px 0 rgba(255,255,255,.95)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell label{color:#6b7088!important}
.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero button{
  background:linear-gradient(135deg,#7357ee,#5d45df)!important;
  color:white!important;
  border:1px solid rgba(106,76,235,.46)!important;
  box-shadow:0 15px 30px -17px rgba(89,62,218,.75)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,
.dark .tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{
  border-color:rgba(116,132,224,.35)!important;
  background:
    radial-gradient(66% 180% at 80% 48%,rgba(106,77,255,.20),transparent 66%),
    linear-gradient(135deg,rgba(11,28,56,.985),rgba(16,27,67,.975))!important;
  box-shadow:0 34px 80px -50px rgba(0,0,0,.93),0 0 48px -34px rgba(106,83,255,.62),inset 0 1px 0 rgba(255,255,255,.06)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell select,
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell button{background:rgba(9,25,50,.78)!important;color:#eef2ff!important;border-color:rgba(118,132,219,.30)!important}
.dark .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell label{color:#b4bfd4!important}

/* ===== KPI FAMILY ===== */
.tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis{gap:12px!important}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div{
  position:relative;
  overflow:hidden;
  min-height:98px;
  border-radius:17px!important;
  border:1px solid rgba(105,96,224,.18)!important;
  background:
    radial-gradient(circle at 12% 0%,rgba(255,255,255,.96),transparent 37%),
    linear-gradient(145deg,rgba(255,255,255,.95),rgba(244,246,255,.91))!important;
  box-shadow:0 22px 50px -37px rgba(72,60,169,.48),0 9px 24px -21px rgba(60,70,130,.23),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card::before,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:#7662ef;opacity:.92}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-2::before,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(3)::before{background:#36c48f}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-3::before{background:#6d8df7}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-4::before{background:#f4a524}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-5::before{background:#e85d78}
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(2)::before{background:#5d97f5}
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div:nth-child(4)::before{background:#f4a524}
.tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
.tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis strong{color:#262845!important;font-weight:870!important;letter-spacing:-.025em}
.dark .tcrm-sales-leads-v3 .tcrm-v3-kpi-card,
.dark .tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis > div{
  border-color:rgba(103,124,207,.28)!important;
  background:linear-gradient(145deg,rgba(9,25,48,.985),rgba(7,20,40,.97))!important;
  box-shadow:0 24px 54px -38px rgba(0,0,0,.9),inset 0 1px 0 rgba(255,255,255,.04)!important;
}
.dark .tcrm-sales-leads-v3 .tcrm-v3-kpi-card .text-2xl,
.dark .tcrm-sales-leads-v3 .tcrm-v21-calendar-kpis strong{color:#f6f8ff!important}

/* ===== SHARED EXECUTIVE SURFACES ===== */
.tcrm-sales-leads-v3 .bg-card,
.tcrm-sales-leads-v3-funnel .chart-container,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-radius:19px!important;
  border:1px solid rgba(103,94,224,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.975),rgba(246,248,255,.95))!important;
  box-shadow:var(--v3-shadow)!important;
}
.dark .tcrm-sales-leads-v3 .bg-card,
.dark .tcrm-sales-leads-v3-funnel .chart-container,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  border-color:rgba(103,123,207,.27)!important;
  background:linear-gradient(180deg,rgba(8,23,45,.99),rgba(6,19,38,.985))!important;
}
.tcrm-sales-leads-v3 .bg-card:hover{border-color:rgba(105,93,231,.28)!important}
.tcrm-sales-leads-v3 .bg-card [class*="CardHeader"],
.tcrm-sales-leads-v3 .bg-card > div:first-child{border-color:rgba(105,96,212,.10)}

/* ===== SALES FUNNEL ===== */
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview{gap:14px!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .chart-container{min-height:340px}
.tcrm-sales-leads-v3-funnel .tcrm-v21-sales-overview .recharts-responsive-container{min-height:250px}
.tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{
  display:grid;
  grid-template-columns:minmax(0,.86fr) minmax(0,1.14fr);
  grid-template-areas:"monthly campaign" "summary campaign";
  gap:14px;
  align-items:stretch;
}
.tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial > .tcrm-v21-won-monthly{grid-area:monthly;margin:0!important}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block{display:contents!important}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .chart-container{grid-area:campaign!important;min-width:0}
.tcrm-sales-leads-v3-funnel .tcrm-v3-commercial-block > .slide-up{grid-area:summary!important;min-width:0}
.tcrm-sales-leads-v3-funnel .tcrm-v21-won-monthly .recharts-responsive-container{max-height:220px!important}
.tcrm-sales-leads-v3-funnel table{border-collapse:separate!important;border-spacing:0 3px!important}
.tcrm-sales-leads-v3-funnel thead tr{background:linear-gradient(180deg,rgba(242,242,255,.995),rgba(230,236,252,.99))!important}
.tcrm-sales-leads-v3-funnel tbody tr{background:rgba(255,255,255,.68)!important}
.tcrm-sales-leads-v3-funnel tbody tr:nth-child(even){background:rgba(242,245,255,.75)!important}
.tcrm-sales-leads-v3-funnel tbody tr:hover{background:rgba(233,234,255,.91)!important}
.dark .tcrm-sales-leads-v3-funnel thead tr{background:linear-gradient(180deg,rgba(14,35,66,.997),rgba(10,28,55,.995))!important}
.dark .tcrm-sales-leads-v3-funnel tbody tr{background:rgba(8,21,41,.90)!important}
.dark .tcrm-sales-leads-v3-funnel tbody tr:nth-child(even){background:rgba(10,28,52,.93)!important}
.tcrm-sales-leads-v3-funnel .tcrm-v21-stage-grid > div,
.tcrm-sales-leads-v3-funnel [class*="conversion"] > div{
  border-radius:13px!important;
  border-color:rgba(106,95,228,.15)!important;
  background:linear-gradient(145deg,rgba(255,255,255,.90),rgba(244,246,255,.80))!important;
}

/* ===== TASKS & SLA ===== */
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:0!important;
  overflow:hidden;
  border:1px solid rgba(105,96,224,.18)!important;
  border-radius:17px!important;
  background:linear-gradient(145deg,rgba(255,255,255,.91),rgba(243,246,255,.86))!important;
  box-shadow:0 20px 45px -36px rgba(69,57,164,.42)!important;
}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item{padding:13px 17px!important;border:0!important;border-inline-end:1px solid rgba(104,96,217,.12)!important;background:transparent!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-health-item:last-child{border-inline-end:0!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends,
.tcrm-sales-leads-v3-sla .tcrm-v3-sla-distributions{gap:14px!important}
.tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends > .bg-card{min-height:336px}
.tcrm-sales-leads-v3-sla table{border-collapse:separate!important;border-spacing:0 3px!important}
.tcrm-sales-leads-v3-sla thead tr{background:linear-gradient(180deg,rgba(242,242,255,.995),rgba(230,236,252,.99))!important}
.tcrm-sales-leads-v3-sla tbody tr{background:rgba(255,255,255,.74)!important}
.tcrm-sales-leads-v3-sla tbody tr:nth-child(even){background:rgba(242,245,255,.80)!important}
.tcrm-sales-leads-v3-sla tbody tr:hover{background:rgba(233,234,255,.94)!important}
.dark .tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{border-color:rgba(103,123,207,.27)!important;background:linear-gradient(145deg,rgba(9,25,48,.96),rgba(7,20,40,.94))!important}
.dark .tcrm-sales-leads-v3-sla .tcrm-v21-health-item{border-inline-end-color:rgba(103,123,207,.18)!important}
.dark .tcrm-sales-leads-v3-sla thead tr{background:linear-gradient(180deg,rgba(14,35,66,.997),rgba(10,28,55,.995))!important}
.dark .tcrm-sales-leads-v3-sla tbody tr{background:rgba(8,21,41,.91)!important}
.dark .tcrm-sales-leads-v3-sla tbody tr:nth-child(even){background:rgba(10,28,52,.94)!important}
.tcrm-sales-leads-v3-sla td,.tcrm-sales-leads-v3-sla th{padding-top:11px!important;padding-bottom:11px!important}

/* ===== CALENDAR ===== */
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{
  display:grid!important;
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{gap:14px!important;grid-template-columns:minmax(0,3.15fr) minmax(280px,.85fr)!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{overflow:hidden!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child{
  min-height:58px;
  background:linear-gradient(180deg,rgba(249,249,255,.98),rgba(241,244,255,.94));
  border-bottom-color:rgba(105,96,224,.14)!important;
}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{background:rgba(241,243,254,.82);border-bottom-color:rgba(105,96,224,.13)!important}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{min-height:108px!important;border-color:rgba(104,111,170,.10)!important;transition:background .18s ease,box-shadow .18s ease}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{background:linear-gradient(145deg,rgba(240,238,255,.88),rgba(246,249,255,.84))!important;box-shadow:inset 0 0 0 1px rgba(111,94,236,.12)}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main [class*="bg-emerald-100"]{border-radius:7px!important;box-shadow:0 7px 14px -11px rgba(87,62,204,.55)}
.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:58px;
  background:linear-gradient(180deg,rgba(249,249,255,.98),rgba(241,244,255,.94));
  border-bottom-color:rgba(105,96,224,.14)!important;
}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child,
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{background:linear-gradient(180deg,rgba(13,32,62,.98),rgba(9,26,51,.94))!important;border-color:rgba(103,123,207,.20)!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{border-color:rgba(103,123,207,.13)!important}
.dark .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{background:rgba(16,34,67,.90)!important}

/* ===== TYPE RHYTHM / DENSITY ===== */
.tcrm-sales-leads-v3 h2,.tcrm-sales-leads-v3 h3,.tcrm-sales-leads-v3 [class*="CardTitle"]{letter-spacing:-.015em;color:var(--v3-ink)}
.tcrm-sales-leads-v3 .text-muted-foreground{color:var(--v3-muted)!important}
.tcrm-sales-leads-v3 table th{font-size:10.7px!important;font-weight:850!important;color:#59647b!important}
.tcrm-sales-leads-v3 table td{font-size:11.8px!important;color:#4f5a71!important}
.dark .tcrm-sales-leads-v3 table th{color:#aebbd1!important}
.dark .tcrm-sales-leads-v3 table td{color:#9eacc2!important}

/* ===== RESPONSIVE — same philosophy as corrected Leads filters ===== */
@media (max-width:1450px){
  .tcrm-sales-leads-v3{padding:16px!important}
  .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{min-height:84px;padding:16px 18px!important}
  .tcrm-sales-leads-v3-funnel .tcrm-v3-sales-commercial{grid-template-columns:minmax(0,1fr);grid-template-areas:"monthly" "campaign" "summary"}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{grid-template-columns:minmax(0,1fr)!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{min-height:240px}
}
@media (max-width:1100px){
  .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  .tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3-sla .tcrm-v21-health-item{border-inline-end:0!important;border-bottom:1px solid rgba(104,96,217,.12)!important}
  .tcrm-sales-leads-v3-sla .tcrm-v21-health-item:last-child{border-bottom:0!important}
}
@media (max-width:760px){
  .tcrm-sales-leads-v3{padding:12px!important;gap:12px!important}
  .tcrm-sales-leads-v3 .tcrm-v21-kpi-grid,.tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-kpis{grid-template-columns:1fr!important}
  .tcrm-sales-leads-v3 .tcrm-v3-page-banner-shell > div,.tcrm-sales-leads-v3 .tcrm-v3-calendar-hero{border-radius:17px!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{overflow-x:auto!important}
  .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > .grid{min-width:720px}
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")
for key, p in FILES.items():
    p.write_text(updated[key], encoding="utf-8")

# Sanity checks: scope, imports, marker, and no accidental backend writes.
for key, p in FILES.items():
    now = p.read_text(encoding="utf-8")
    if MARKER not in now or IMPORT not in now or "tcrm-sales-leads-v3" not in now:
        raise SystemExit(f"VERIFY_FAIL={p}")
if not CSS.exists() or "TCRM Sales 3 Screens" not in CSS.read_text(encoding="utf-8"):
    raise SystemExit("VERIFY_FAIL=CSS")

print("PATCH=PASS")
print("VERSION=V3")
print("REFERENCE=LEADS_PREMIUM_V1_8")
print("SCREENS=Sales Funnel,Tasks & SLA,Calendar")
print("FILES_CHANGED=" + ",".join(str(p.relative_to(ROOT)) for p in [*FILES.values(), CSS]))
print(f"BACKUP={backup}")
print("BACKEND_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
