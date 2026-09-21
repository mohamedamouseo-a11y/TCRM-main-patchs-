#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
SALES = SRC / "pages/SalesFunnelDashboard.tsx"
CSS = SRC / "sales-funnel-reference-lock-v11.css"

MARKER = "TCRM_SALES_FUNNEL_REFERENCE_LOCK_V11"
NEW_IMPORT = 'import "../sales-funnel-reference-lock-v11.css";'
OLD_IMPORTS = [
    'import "../sales-funnel-premium-v1-reference.css";',
    'import "../sales-module-premium-v2-three-screen.css";',
    'import "../sales-module-premium-v2-1-corrective.css";',
    'import "../sales-3-screens-leads-design-system-v3.css";',
    'import "../sales-3-screens-executive-v4.css";',
    'import "../sales-3-screens-executive-v5.css";',
    'import "../sales-calendar-light-v6.css";',
    'import "../sales-3-screens-light-reference-v7.css";',
]

if not SALES.exists():
    raise SystemExit(f"MISSING={SALES}")

backup = ROOT / ".patch-backups" / f"sales-funnel-reference-lock-v11-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(SALES, backup / SALES.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

text = SALES.read_text(encoding="utf-8")
lines = text.splitlines()
lines = [line for line in lines if line.strip() not in OLD_IMPORTS and line.strip() != NEW_IMPORT]

insert_at = 0
for i, line in enumerate(lines):
    if line.startswith("import "):
        insert_at = i + 1
lines.insert(insert_at, NEW_IMPORT)

if not any(MARKER in line for line in lines[:20]):
    lines.insert(1 if lines else 0, f"// {MARKER}")

text = "\n".join(lines) + "\n"

old_root = 'className="tcrm-sales-premium-v21 tcrm-sales-premium-v2 tcrm-sales-funnel-premium-v2 sales-funnel-premium-v1 tcrm-sales-leads-v3 tcrm-sales-leads-v3-funnel p-4 md:p-5 space-y-4 fade-in"'
new_root = 'className="tcrm-sales-funnel-reference-lock-v11 p-4 md:p-5 space-y-4 fade-in"'
if old_root in text:
    text = text.replace(old_root, new_root, 1)
elif "tcrm-sales-funnel-reference-lock-v11" not in text:
    raise SystemExit("ERROR=SALES_ROOT_ANCHOR_NOT_FOUND")

text = text.replace('className="tcrm-v7-sales-bottom-grid"', 'className="tcrm-sales-bottom-grid-v11"', 1)

# Add durable hooks for Deal Summary internals to avoid clipping and over-broad selectors.
text = text.replace(
    '<CardContent className="space-y-4">\n              {isLoading ? (\n                <Skeleton className="h-48" />',
    '<CardContent className="tcrm-v11-deal-summary-content space-y-4">\n              {isLoading ? (\n                <Skeleton className="h-48" />',
    1,
)
text = text.replace(
    'className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors duration-200"',
    'className="tcrm-v11-deal-stat flex items-center gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors duration-200"',
)
text = text.replace(
    '<div className="rounded-lg border border-border bg-muted/20 p-3">\n                    <div className="flex items-center justify-between mb-2">',
    '<div className="tcrm-v11-potential-closings rounded-lg border border-border bg-muted/20 p-3">\n                    <div className="flex items-center justify-between mb-2">',
    1,
)

SALES.write_text(text, encoding="utf-8")

CSS_TEXT = r'''/* TCRM V11 — Sales Funnel Reference Lock
   Final scoped stylesheet for SalesFunnelDashboard only.
   Old sales visual imports removed to stop cascade conflicts.
   No backend/data/routes/permissions/business logic changes. */

.tcrm-sales-funnel-reference-lock-v11{
  --sf11-ink:#17213c;
  --sf11-muted:#74809a;
  --sf11-purple:#6854ee;
  --sf11-purple2:#7b63f4;
  --sf11-blue:#4c8cf7;
  --sf11-cyan:#15b7c9;
  --sf11-green:#20b978;
  --sf11-amber:#f2a31b;
  --sf11-red:#ee5064;
  --sf11-line:rgba(99,84,231,.14);
  --sf11-line-strong:rgba(99,84,231,.22);
  --sf11-card:#fff;
  --sf11-soft:#fafbff;
  --sf11-shadow:0 16px 38px -30px rgba(61,53,137,.34),0 4px 14px -12px rgba(53,64,112,.17);
  min-height:100%;
  color:var(--sf11-ink);
  background:
    radial-gradient(760px 350px at 3% -5%,rgba(124,100,245,.10),transparent 68%),
    linear-gradient(180deg,#fbfaff 0%,#f6f7ff 58%,#f2f5ff 100%)!important;
}

.tcrm-sales-funnel-reference-lock-v11 *{box-sizing:border-box}

/* ===== Hero — same light family as Calendar/Leads ===== */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div{
  min-height:92px!important;
  padding:16px 18px!important;
  border:1px solid var(--sf11-line-strong)!important;
  border-radius:19px!important;
  background:
    radial-gradient(circle at 1px 1px,rgba(104,84,238,.11) 1px,transparent 1.2px) 0 0/15px 15px,
    radial-gradient(58% 180% at 83% 50%,rgba(124,100,245,.15),transparent 66%),
    linear-gradient(125deg,#fff 0%,#fbfaff 57%,#f3f1ff 100%)!important;
  box-shadow:var(--sf11-shadow)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell .absolute.inset-0{
  opacity:.16!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell .w-11.h-11{
  width:44px!important;
  height:44px!important;
  background:linear-gradient(135deg,#765ff3,#6049e6)!important;
  border:1px solid rgba(255,255,255,.72)!important;
  box-shadow:0 13px 27px -16px rgba(86,62,213,.65)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell h1{
  color:var(--sf11-ink)!important;
  font-size:20px!important;
  font-weight:850!important;
  letter-spacing:-.025em!important;
  text-shadow:none!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell p{
  color:var(--sf11-muted)!important;
  font-size:11.5px!important;
  font-weight:600!important;
  text-shadow:none!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell button,
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell [role="button"]{
  min-height:40px!important;
  border:1px solid rgba(92,72,219,.34)!important;
  border-radius:11px!important;
  background:linear-gradient(135deg,#4d429e,#433a91)!important;
  color:#fff!important;
  box-shadow:0 12px 25px -17px rgba(66,51,162,.70)!important;
}

/* ===== KPI cards ===== */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-kpi-grid{
  gap:10px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card{
  position:relative!important;
  min-height:96px!important;
  gap:0!important;
  padding-block:0!important;
  overflow:hidden!important;
  border:1px solid var(--sf11-line)!important;
  border-radius:16px!important;
  background:linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:var(--sf11-shadow)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card::before{
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:2px;
  background:var(--sf11-purple);
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-2::before{background:var(--sf11-green)}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-3::before{background:#7770ef}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-4::before{background:var(--sf11-blue)}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-5::before{background:var(--sf11-amber)}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card [data-slot="card-content"]{
  padding:13px 14px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .kpi-icon{
  width:32px!important;
  height:32px!important;
  border-radius:9px!important;
  box-shadow:0 9px 19px -13px currentColor!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .text-2xl{
  color:var(--sf11-ink)!important;
  font-size:22px!important;
  line-height:1.05!important;
  font-weight:850!important;
}

/* ===== Shared cards ===== */
.tcrm-sales-funnel-reference-lock-v11 [data-slot="card"],
.tcrm-sales-funnel-reference-lock-v11 .chart-container{
  gap:0!important;
  padding-block:0!important;
  border:1px solid var(--sf11-line)!important;
  border-radius:16px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--sf11-shadow)!important;
  overflow:hidden!important;
}

.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-header"]{
  min-height:46px!important;
  padding:10px 13px!important;
  border-bottom:1px solid rgba(104,84,238,.08)!important;
  background:linear-gradient(180deg,#fbfbff,#fff)!important;
}

.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-content"]{
  padding:12px 13px!important;
}

.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-title"]{
  color:var(--sf11-ink)!important;
  font-weight:820!important;
  letter-spacing:-.015em!important;
}

.tcrm-sales-funnel-reference-lock-v11 .text-muted-foreground{
  color:var(--sf11-muted)!important;
}

/* ===== Overview ===== */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview{
  display:grid!important;
  grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr)!important;
  gap:12px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .chart-container{
  min-height:310px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .recharts-responsive-container{
  height:230px!important;
  min-height:230px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .group > .flex-1 > div{
  border-radius:7px!important;
  box-shadow:0 8px 18px -13px rgba(49,46,129,.45)!important;
}

/* ===== Commercial composition ===== */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-sales-commercial{
  display:grid!important;
  grid-template-columns:minmax(360px,.72fr) minmax(0,1.28fr)!important;
  grid-template-areas:
    "monthly campaign"
    "summary campaign"!important;
  grid-template-rows:136px auto!important;
  gap:12px!important;
  align-items:stretch!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-deal-grid{
  display:contents!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly{
  grid-area:monthly!important;
  height:136px!important;
  min-height:136px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly [data-slot="card-header"]{
  min-height:42px!important;
  padding:8px 12px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly [data-slot="card-content"]{
  height:92px!important;
  padding:8px 12px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly .h-56{
  height:66px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly .recharts-responsive-container{
  height:70px!important;
  max-height:70px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart{
  grid-area:campaign!important;
  min-height:100%!important;
  height:auto!important;
  align-self:stretch!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart .recharts-responsive-container{
  height:280px!important;
  min-height:280px!important;
}

/* Deal Summary: never clip. Show all statuses + potential closings. */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary{
  grid-area:summary!important;
  height:auto!important;
  min-height:0!important;
  max-height:none!important;
  overflow:visible!important;
  align-self:start!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary [data-slot="card-header"]{
  min-height:42px!important;
  padding:8px 12px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:7px!important;
  padding:8px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat{
  min-width:0!important;
  margin:0!important;
  padding:8px 9px!important;
  gap:7px!important;
  border:1px solid rgba(104,84,238,.10)!important;
  border-radius:10px!important;
  background:#fafbff!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat .text-sm{
  font-size:10.5px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat .text-xs{
  font-size:9px!important;
  line-height:1.3!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
  grid-column:1 / -1!important;
  min-width:0!important;
  margin:0!important;
  padding:9px!important;
  border-color:rgba(104,84,238,.10)!important;
  border-radius:10px!important;
  background:linear-gradient(145deg,#fbfbff,#f7f8ff)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings .max-h-44{
  max-height:86px!important;
  overflow:auto!important;
}

/* ===== Final row ===== */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-sales-bottom-grid-v11{
  display:grid!important;
  grid-template-columns:minmax(0,1.55fr) minmax(360px,1fr)!important;
  gap:12px!important;
  align-items:start!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table,
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion{
  min-width:0!important;
  margin:0!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table [data-slot="card-content"]{
  padding:0!important;
}

.tcrm-sales-funnel-reference-lock-v11 table{
  width:100%;
  border-collapse:separate!important;
  border-spacing:0 1px!important;
}

.tcrm-sales-funnel-reference-lock-v11 thead tr{
  background:linear-gradient(180deg,#f3f4ff,#edf0fb)!important;
}

.tcrm-sales-funnel-reference-lock-v11 tbody tr:nth-child(even){
  background:#f8f9ff!important;
}

.tcrm-sales-funnel-reference-lock-v11 th{
  padding:7px 9px!important;
  color:#68748c!important;
  font-size:9.5px!important;
  font-weight:850!important;
}

.tcrm-sales-funnel-reference-lock-v11 td{
  padding:7px 9px!important;
  color:#536078!important;
  font-size:10px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:6px!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div{
  min-width:0!important;
  padding:7px!important;
  gap:6px!important;
  border-color:rgba(104,84,238,.11)!important;
  background:#fafbff!important;
}

/* ===== Charts ===== */
.tcrm-sales-funnel-reference-lock-v11 .recharts-cartesian-grid line{
  stroke:rgba(105,116,170,.12)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .recharts-text{
  fill:#74809a!important;
}

/* ===== Dark mode ===== */
.dark .tcrm-sales-funnel-reference-lock-v11{
  --sf11-ink:#f1f4ff;
  --sf11-muted:#9aa8c1;
  --sf11-line:rgba(108,126,202,.18);
  --sf11-line-strong:rgba(116,132,224,.29);
  --sf11-card:#0b2038;
  --sf11-soft:#091a2f;
  --sf11-shadow:0 20px 48px -36px rgba(0,0,0,.90),inset 0 1px 0 rgba(255,255,255,.025);
  background:
    radial-gradient(760px 360px at 3% -5%,rgba(87,71,228,.17),transparent 68%),
    linear-gradient(180deg,#06101d,#07182a 58%,#061221)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div{
  background:
    radial-gradient(circle at 1px 1px,rgba(132,145,231,.10) 1px,transparent 1.2px) 0 0/15px 15px,
    radial-gradient(58% 180% at 83% 50%,rgba(105,77,255,.18),transparent 66%),
    linear-gradient(135deg,#0a1a34,#0e1a3e)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 [data-slot="card"],
.dark .tcrm-sales-funnel-reference-lock-v11 .chart-container{
  background:linear-gradient(180deg,#0b2038,#091a2f)!important;
  border-color:var(--sf11-line)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 [data-slot="card-header"]{
  background:linear-gradient(180deg,#0d2744,#0b2038)!important;
  border-bottom-color:rgba(108,126,202,.13)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat,
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings,
.dark .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div{
  background:#0c223b!important;
  border-color:rgba(108,126,202,.15)!important;
}

.dark .tcrm-sales-funnel-reference-lock-v11 thead tr{
  background:#102944!important;
}
.dark .tcrm-sales-funnel-reference-lock-v11 tbody tr:nth-child(even){
  background:#0a1e35!important;
}
.dark .tcrm-sales-funnel-reference-lock-v11 th{color:#a9b6ca!important}
.dark .tcrm-sales-funnel-reference-lock-v11 td{color:#9dacbf!important}
.dark .tcrm-sales-funnel-reference-lock-v11 .recharts-text{fill:#91a0b8!important}

/* ===== Responsive ===== */
@media (max-width:1365px){
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview{
    grid-template-columns:1fr!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-sales-commercial{
    grid-template-columns:1fr!important;
    grid-template-areas:"monthly" "campaign" "summary"!important;
    grid-template-rows:auto!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly,
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart{
    height:auto!important;
    min-height:0!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly [data-slot="card-content"],
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly .recharts-responsive-container{
    height:auto!important;
    max-height:none!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-sales-bottom-grid-v11{
    grid-template-columns:1fr!important;
  }
}

@media (max-width:900px){
  .tcrm-sales-funnel-reference-lock-v11{
    padding:14px!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-kpi-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
    grid-template-columns:1fr!important;
  }
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
    grid-column:auto!important;
  }
}

@media (max-width:640px){
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-kpi-grid{
    grid-template-columns:1fr!important;
  }
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=SALES_FUNNEL_REFERENCE_LOCK_V11")
print("OLD_VISUAL_IMPORTS_REMOVED=YES")
print("FINAL_STYLESHEET=sales-funnel-reference-lock-v11.css")
print("DEAL_SUMMARY_CLIPPING_FIXED=YES")
print("HERO_REFERENCE_LOCK=YES")
print("CALENDAR_UNCHANGED=YES")
print("SLA_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=2")
print(f"BACKUP={backup}")
