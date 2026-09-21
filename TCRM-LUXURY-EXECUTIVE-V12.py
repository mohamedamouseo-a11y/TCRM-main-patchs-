#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"

SALES_PAGE = SRC / "pages/SalesFunnelDashboard.tsx"
CAL_PAGE = SRC / "pages/CalendarPage.tsx"
SALES_CSS = SRC / "sales-funnel-reference-lock-v11.css"
CAL_CSS = SRC / "calendar-sla-reference-lock-v9.css"

MARKER = "TCRM_LUXURY_EXECUTIVE_V12"

for p in (SALES_PAGE, CAL_PAGE, SALES_CSS, CAL_CSS):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

sales_page = SALES_PAGE.read_text(encoding="utf-8")
cal_page = CAL_PAGE.read_text(encoding="utf-8")
sales_css = SALES_CSS.read_text(encoding="utf-8")
cal_css = CAL_CSS.read_text(encoding="utf-8")

if "tcrm-sales-funnel-reference-lock-v11" not in sales_page:
    raise SystemExit("ERROR=V11_SALES_NOT_FOUND")
if "tcrm-calendar-reference-lock-v9" not in cal_page:
    raise SystemExit("ERROR=V9_CALENDAR_NOT_FOUND")
if "TCRM_CALENDAR_REFERENCE_POLISH_V10" not in cal_css:
    raise SystemExit("ERROR=V10_CALENDAR_POLISH_NOT_FOUND")

backup = ROOT / ".patch-backups" / f"luxury-executive-v12-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (SALES_PAGE, CAL_PAGE, SALES_CSS, CAL_CSS):
    shutil.copy2(p, backup / p.name)

# Mark pages only; keep current clean imports and business structure.
for p in (SALES_PAGE, CAL_PAGE):
    text = p.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Refine Calendar microcopy to feel more executive, while preserving behavior.
cal_page = CAL_PAGE.read_text(encoding="utf-8")
cal_page = cal_page.replace(
    '{isRTL ? "ابقَ منظماً" : "Stay organized"}',
    '{isRTL ? "مركز التقويم التنفيذي" : "Executive Calendar"}'
)
cal_page = cal_page.replace(
    '{isRTL ? "حوّل المحادثات إلى فرص" : "Turn conversations into opportunities"}',
    '{isRTL ? "الاجتماعات والمتابعات والفرص في مكان واحد" : "Meetings, follow-ups & opportunities"}'
)
cal_page = cal_page.replace(
    '{isRTL ? "حافظ على إنتاجيتك" : "Stay Productive"}',
    '{isRTL ? "جدولة أكثر ذكاءً" : "Schedule with intent"}'
)
cal_page = cal_page.replace(
    '{isRTL ? "حافظ على تقويمك محدثاً حتى لا تفوت أي فرصة." : "Keep your calendar updated so you never miss an opportunity."}',
    '{isRTL ? "حافظ على وضوح الاجتماعات والمتابعات والفرص القادمة." : "Keep meetings, follow-ups and opportunities visible."}'
)
CAL_PAGE.write_text(cal_page, encoding="utf-8")

SALES_APPEND = r'''

/* TCRM_LUXURY_EXECUTIVE_V12
   Luxury executive visual refinement.
   Same V11 structure, data and interactions. No new stylesheet/import stack. */

.tcrm-sales-funnel-reference-lock-v11{
  --lux-ink:#12182a;
  --lux-muted:#6f7890;
  --lux-violet:#6854ed;
  --lux-violet-dark:#4d3cb8;
  --lux-indigo:#3d4db7;
  --lux-gold:#c99445;
  --lux-line:rgba(71,65,130,.13);
  --lux-shadow:
    0 18px 50px -34px rgba(40,34,99,.30),
    0 8px 22px -19px rgba(39,48,94,.16),
    inset 0 1px 0 rgba(255,255,255,.92);
  background:
    radial-gradient(1000px 380px at 5% -8%,rgba(117,91,234,.11),transparent 67%),
    radial-gradient(760px 320px at 92% 0%,rgba(200,170,255,.07),transparent 66%),
    linear-gradient(180deg,#fbfaff 0%,#f7f7fc 46%,#f3f5fb 100%)!important;
}

/* Premium executive hero */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div{
  min-height:96px!important;
  overflow:hidden!important;
  border:1px solid rgba(92,75,207,.20)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(99,78,221,.09) 1px,transparent 1.25px) 0 0/16px 16px,
    radial-gradient(56% 210% at 83% 44%,rgba(124,100,245,.17),transparent 66%),
    linear-gradient(118deg,#fff 0%,#fbfaff 52%,#f0edff 100%)!important;
  box-shadow:
    0 22px 55px -40px rgba(78,59,177,.40),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div::after{
  content:"";
  position:absolute;
  width:250px;
  height:250px;
  inset-inline-end:-62px;
  top:-122px;
  border:1px solid rgba(114,92,224,.08);
  border-radius:44px;
  transform:rotate(17deg);
  background:linear-gradient(145deg,rgba(255,255,255,.20),rgba(111,89,231,.045));
  pointer-events:none;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell .w-11.h-11{
  border-radius:14px!important;
  background:linear-gradient(145deg,#765ff2,#533fc9)!important;
  box-shadow:
    0 16px 30px -19px rgba(74,54,183,.72),
    inset 0 1px 0 rgba(255,255,255,.34)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell h1{
  color:var(--lux-ink)!important;
  font-size:21px!important;
  font-weight:900!important;
  letter-spacing:-.035em!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell p{
  color:#778098!important;
  font-size:11px!important;
  letter-spacing:.005em!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell button,
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell [role="button"]{
  min-height:42px!important;
  border:1px solid rgba(74,60,159,.18)!important;
  border-radius:12px!important;
  background:
    linear-gradient(180deg,rgba(58,49,132,.98),rgba(47,40,113,.98))!important;
  color:#fff!important;
  box-shadow:
    0 14px 30px -18px rgba(42,32,117,.72),
    inset 0 1px 0 rgba(255,255,255,.13)!important;
}

/* Luxury KPI cards */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card{
  min-height:102px!important;
  border-color:var(--lux-line)!important;
  border-radius:18px!important;
  background:
    radial-gradient(120px 80px at 92% 0%,rgba(108,84,238,.055),transparent 72%),
    linear-gradient(150deg,#fff 0%,#fcfcff 55%,#f7f8fd 100%)!important;
  box-shadow:var(--lux-shadow)!important;
  transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card:hover{
  transform:translateY(-2px)!important;
  border-color:rgba(104,84,237,.25)!important;
  box-shadow:
    0 22px 52px -36px rgba(63,50,145,.38),
    0 9px 24px -18px rgba(50,58,105,.20),
    inset 0 1px 0 #fff!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card::before{
  height:2px!important;
  opacity:.88!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card::after{
  content:"";
  position:absolute;
  width:72px;
  height:72px;
  inset-inline-end:-18px;
  top:-24px;
  border-radius:50%;
  background:radial-gradient(circle,rgba(105,84,237,.06),transparent 68%);
  pointer-events:none;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card [data-slot="card-content"]{
  padding:14px 15px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .kpi-icon{
  width:34px!important;
  height:34px!important;
  border-radius:11px!important;
  box-shadow:
    0 11px 24px -15px currentColor,
    inset 0 1px 0 rgba(255,255,255,.30)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .text-2xl{
  color:var(--lux-ink)!important;
  font-size:23px!important;
  font-weight:900!important;
  letter-spacing:-.04em!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card p{
  letter-spacing:.005em!important;
}

/* Executive analytics surfaces */
.tcrm-sales-funnel-reference-lock-v11 [data-slot="card"],
.tcrm-sales-funnel-reference-lock-v11 .chart-container{
  border-color:var(--lux-line)!important;
  border-radius:18px!important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.995),rgba(250,251,255,.985))!important;
  box-shadow:var(--lux-shadow)!important;
}

.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-header"]{
  min-height:48px!important;
  padding:11px 14px!important;
  border-bottom:1px solid rgba(78,69,129,.075)!important;
  background:
    linear-gradient(180deg,rgba(251,251,255,.98),rgba(255,255,255,.94))!important;
}

.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-title"]{
  color:#1e2539!important;
  font-weight:850!important;
  letter-spacing:-.018em!important;
}

/* Funnel + Lead Trend */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview{
  gap:14px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .chart-container{
  min-height:316px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .group{
  padding-block:1px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .group > .flex-1 > div{
  position:relative!important;
  overflow:hidden!important;
  height:31px!important;
  border-radius:8px!important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.28),
    0 9px 18px -14px rgba(34,39,90,.46)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .group > .flex-1 > div::after{
  content:"";
  position:absolute;
  inset:0;
  background:linear-gradient(180deg,rgba(255,255,255,.17),transparent 45%);
  pointer-events:none;
}

/* Commercial: cleaner luxury composition */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-sales-commercial{
  gap:14px!important;
  grid-template-columns:minmax(360px,.74fr) minmax(0,1.26fr)!important;
  grid-template-rows:138px auto!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly{
  height:138px!important;
  min-height:138px!important;
  background:
    radial-gradient(150px 90px at 100% 0%,rgba(201,148,69,.07),transparent 70%),
    linear-gradient(180deg,#fff,#fbfbfe)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart{
  background:
    radial-gradient(220px 110px at 97% 0%,rgba(104,84,237,.055),transparent 72%),
    linear-gradient(180deg,#fff,#fbfcff)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart .recharts-responsive-container{
  height:286px!important;
  min-height:286px!important;
}

/* Deal Summary as premium status deck */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary{
  border-color:rgba(79,70,134,.14)!important;
  overflow:hidden!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:8px!important;
  padding:9px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat{
  min-height:70px!important;
  align-items:flex-start!important;
  padding:9px 10px!important;
  border:1px solid rgba(88,79,140,.09)!important;
  border-radius:12px!important;
  background:linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:0 9px 20px -19px rgba(47,51,92,.20)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat:nth-child(1){
  background:linear-gradient(145deg,#fbfffd,#f3fbf7)!important;
  border-color:rgba(32,185,120,.15)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat:nth-child(2){
  background:linear-gradient(145deg,#fffdfa,#fff9ef)!important;
  border-color:rgba(242,163,27,.17)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat:nth-child(3){
  background:linear-gradient(145deg,#fffafa,#fff5f6)!important;
  border-color:rgba(238,80,100,.14)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
  grid-column:1 / -1!important;
  padding:10px 11px!important;
  border:1px solid rgba(104,84,237,.12)!important;
  border-radius:12px!important;
  background:
    radial-gradient(170px 80px at 100% 0%,rgba(104,84,237,.06),transparent 70%),
    linear-gradient(145deg,#fcfbff,#f7f7ff)!important;
}

/* Campaign details and conversion cards */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-sales-bottom-grid-v11{
  gap:14px!important;
  grid-template-columns:minmax(0,1.58fr) minmax(360px,.92fr)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table table thead tr{
  background:linear-gradient(180deg,#f6f5fb,#f1f2f8)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table tbody tr{
  transition:background .16s ease!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table tbody tr:hover{
  background:#f7f5ff!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex{
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:7px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div{
  min-height:72px!important;
  padding:9px!important;
  border:1px solid rgba(85,76,139,.10)!important;
  border-radius:12px!important;
  background:
    linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:0 9px 20px -19px rgba(45,48,91,.18)!important;
}

/* Premium chart typography */
.tcrm-sales-funnel-reference-lock-v11 .recharts-cartesian-axis-tick-value{
  font-size:10px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .recharts-cartesian-grid-horizontal line,
.tcrm-sales-funnel-reference-lock-v11 .recharts-cartesian-grid-vertical line{
  stroke:rgba(76,82,119,.085)!important;
}

/* Dark luxury counterpart */
.dark .tcrm-sales-funnel-reference-lock-v11{
  background:
    radial-gradient(900px 380px at 4% -6%,rgba(93,70,224,.18),transparent 66%),
    radial-gradient(760px 320px at 92% 0%,rgba(117,77,225,.10),transparent 68%),
    linear-gradient(180deg,#07111e,#081827 54%,#071321)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div{
  border-color:rgba(118,100,232,.22)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(146,129,241,.10) 1px,transparent 1.2px) 0 0/16px 16px,
    radial-gradient(60% 180% at 83% 50%,rgba(111,80,239,.17),transparent 67%),
    linear-gradient(135deg,#0b1c35,#101d42)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell h1{
  color:#f3f5ff!important;
}
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell p{
  color:#a5afc5!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card,
.dark .tcrm-sales-funnel-reference-lock-v11 [data-slot="card"],
.dark .tcrm-sales-funnel-reference-lock-v11 .chart-container{
  background:linear-gradient(160deg,#0d2139,#0a1b30)!important;
  border-color:rgba(111,127,189,.16)!important;
  box-shadow:
    0 24px 54px -39px rgba(0,0,0,.90),
    inset 0 1px 0 rgba(255,255,255,.025)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 [data-slot="card-header"]{
  background:linear-gradient(180deg,#102842,#0d2139)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 [data-slot="card-title"],
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .text-2xl{
  color:#f0f3fb!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat,
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings,
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div{
  background:linear-gradient(145deg,#0e243d,#0b1d33)!important;
  border-color:rgba(111,127,189,.15)!important;
}

@media (max-width:1365px){
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
    grid-column:1 / -1!important;
  }
}

@media (max-width:900px){
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
    grid-template-columns:1fr!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
    grid-column:auto!important;
  }
}
'''

CAL_APPEND = r'''

/* TCRM_LUXURY_EXECUTIVE_V12 — Calendar only
   Luxury polish over the clean V9/V10 reference lock. */

.tcrm-calendar-reference-lock-v9{
  --cal-lux-ink:#12182a;
  --cal-lux-muted:#727b92;
  --cal-lux-violet:#6854ed;
  --cal-lux-gold:#c99445;
  --cal-lux-line:rgba(74,67,128,.13);
  --cal-lux-shadow:
    0 18px 50px -34px rgba(40,34,99,.29),
    0 8px 22px -19px rgba(39,48,94,.15),
    inset 0 1px 0 rgba(255,255,255,.93);
  background:
    radial-gradient(1000px 380px at 5% -8%,rgba(117,91,234,.10),transparent 67%),
    linear-gradient(180deg,#fbfaff 0%,#f7f7fc 48%,#f3f5fb 100%)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
  min-height:98px!important;
  border-color:rgba(92,75,207,.20)!important;
  border-radius:20px!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(99,78,221,.085) 1px,transparent 1.25px) 0 0/16px 16px,
    radial-gradient(56% 210% at 83% 44%,rgba(124,100,245,.16),transparent 66%),
    linear-gradient(118deg,#fff 0%,#fbfaff 52%,#f0edff 100%)!important;
  box-shadow:
    0 22px 55px -40px rgba(78,59,177,.40),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 > div:first-child{
  width:46px!important;
  height:46px!important;
  min-width:46px!important;
  border-radius:14px!important;
  background:linear-gradient(145deg,#765ff2,#533fc9)!important;
  box-shadow:
    0 16px 30px -19px rgba(74,54,183,.72),
    inset 0 1px 0 rgba(255,255,255,.34)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 h1{
  color:var(--cal-lux-ink)!important;
  font-size:21px!important;
  font-weight:900!important;
  letter-spacing:-.035em!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 p{
  color:#778098!important;
  font-size:11px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note{
  margin-inline-end:28px!important;
  gap:11px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note > svg{
  width:46px!important;
  height:46px!important;
  color:#7c65f2!important;
  opacity:.19!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note strong{
  color:#6550e5!important;
  font-size:11px!important;
  font-weight:850!important;
  letter-spacing:.01em!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note span{
  color:#7c8498!important;
  font-size:9.5px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero > button{
  min-height:43px!important;
  padding-inline:19px!important;
  border-radius:12px!important;
  background:linear-gradient(180deg,#6b54e9,#5742c7)!important;
  box-shadow:
    0 15px 31px -19px rgba(74,54,183,.70),
    inset 0 1px 0 rgba(255,255,255,.18)!important;
}

/* Luxury KPIs */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi{
  min-height:94px!important;
  border-color:var(--cal-lux-line)!important;
  border-radius:18px!important;
  background:
    radial-gradient(115px 75px at 92% 0%,rgba(108,84,238,.05),transparent 72%),
    linear-gradient(150deg,#fff 0%,#fcfcff 55%,#f7f8fd 100%)!important;
  box-shadow:var(--cal-lux-shadow)!important;
  transition:transform .18s ease,border-color .18s ease!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:hover{
  transform:translateY(-2px)!important;
  border-color:rgba(104,84,237,.24)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi-icon{
  width:38px!important;
  height:38px!important;
  border-radius:12px!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.75)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi strong{
  color:var(--cal-lux-ink)!important;
  font-size:23px!important;
  font-weight:900!important;
  letter-spacing:-.04em!important;
}

/* Calendar shell */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-layout{
  gap:14px!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main,
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  border-color:var(--cal-lux-line)!important;
  border-radius:19px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--cal-lux-shadow)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar{
  min-height:60px!important;
  padding:10px 13px!important;
  background:
    linear-gradient(180deg,#fdfdff,#fafaff)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav > button{
  min-width:35px!important;
  min-height:35px!important;
  border-radius:10px!important;
  border-color:rgba(86,75,145,.12)!important;
  background:linear-gradient(180deg,#fff,#fafaff)!important;
  box-shadow:0 8px 20px -16px rgba(48,46,91,.28)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav .tcrm-v10-today-btn{
  padding-inline:14px!important;
  color:#5f4bd6!important;
  font-weight:820!important;
  background:linear-gradient(180deg,#faf8ff,#f3f0ff)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-month-title{
  color:#1f2639!important;
  font-size:16px!important;
  font-weight:900!important;
  letter-spacing:-.02em!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  min-height:48px!important;
  background:linear-gradient(180deg,#f8f8fc,#f3f4f8)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b > div{
  color:#7a849a!important;
  font-size:10px!important;
  font-weight:820!important;
  letter-spacing:.055em!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:96px!important;
  border-color:rgba(72,79,113,.085)!important;
  background:rgba(255,255,255,.74)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div:hover{
  background:linear-gradient(145deg,#fbfaff,#f6f5ff)!important;
}

/* Event pills: more editorial and premium */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-emerald-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-amber-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-rose-100"]{
  min-height:21px!important;
  border-radius:7px!important;
  padding:3px 6px!important;
  border-width:1px!important;
  box-shadow:0 7px 15px -14px rgba(59,49,120,.26)!important;
}

/* Upcoming rail */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child{
  background:linear-gradient(180deg,#fdfdff,#fafaff)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-upcoming-empty > .w-12.h-12{
  width:60px!important;
  height:60px!important;
  border-radius:18px!important;
  background:linear-gradient(145deg,#f4f1ff,#ebe6ff)!important;
  border-color:#e3dcff!important;
  box-shadow:0 14px 26px -21px rgba(89,68,194,.32)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-empty-title{
  color:#242b3e!important;
  font-size:11.5px!important;
  font-weight:850!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-create-meeting-btn{
  min-height:36px!important;
  border-color:rgba(104,84,237,.35)!important;
  border-radius:10px!important;
  color:#5d49d8!important;
  background:linear-gradient(180deg,#fff,#faf9ff)!important;
  box-shadow:0 10px 22px -18px rgba(70,55,162,.35)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action{
  border-top-color:rgba(72,79,113,.085)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action > button{
  min-height:58px!important;
  border:1px solid rgba(81,73,130,.08)!important;
  border-radius:12px!important;
  background:linear-gradient(145deg,#fff,#fafaff)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note{
  border-color:rgba(154,117,47,.13)!important;
  border-radius:13px!important;
  background:
    linear-gradient(135deg,#fffaf2,#f5f2ff)!important;
  box-shadow:0 10px 22px -20px rgba(87,68,137,.20)!important;
}

/* Dark luxury counterpart */
.dark .tcrm-calendar-reference-lock-v9{
  background:
    radial-gradient(900px 380px at 4% -6%,rgba(93,70,224,.18),transparent 66%),
    linear-gradient(180deg,#07111e,#081827 54%,#071321)!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
  border-color:rgba(118,100,232,.22)!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(146,129,241,.10) 1px,transparent 1.2px) 0 0/16px 16px,
    radial-gradient(60% 180% at 83% 50%,rgba(111,80,239,.17),transparent 67%),
    linear-gradient(135deg,#0b1c35,#101d42)!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 h1{
  color:#f3f5ff!important;
}
.dark .tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 p,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note span{
  color:#a5afc5!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  background:linear-gradient(160deg,#0d2139,#0a1b30)!important;
  border-color:rgba(111,127,189,.16)!important;
  box-shadow:
    0 24px 54px -39px rgba(0,0,0,.90),
    inset 0 1px 0 rgba(255,255,255,.025)!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child{
  background:linear-gradient(180deg,#102842,#0d2139)!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  background:#10243c!important;
}

.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  background:#0b1d32!important;
  border-color:rgba(111,127,189,.11)!important;
}
'''

if MARKER not in sales_css:
    SALES_CSS.write_text(sales_css + SALES_APPEND, encoding="utf-8")
if MARKER not in cal_css:
    CAL_CSS.write_text(cal_css + CAL_APPEND, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=LUXURY_EXECUTIVE_V12")
print("SALES_LUXURY=YES")
print("CALENDAR_LUXURY=YES")
print("SLA_UNCHANGED=YES")
print("NO_NEW_STYLESHEET_STACK=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=4")
print(f"BACKUP={backup}")
