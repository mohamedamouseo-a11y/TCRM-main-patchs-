#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"

SALES = SRC / "pages/SalesFunnelDashboard.tsx"
SLA = SRC / "pages/TaskSlaDashboard.tsx"
CAL = SRC / "pages/CalendarPage.tsx"
SALES_CSS = SRC / "sales-funnel-reference-lock-v11.css"
SHARED_CSS = SRC / "calendar-sla-reference-lock-v9.css"

MARKER = "TCRM_THREE_SCREENS_GENERATED_REFERENCE_V13"

for p in (SALES, SLA, CAL, SALES_CSS, SHARED_CSS):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"three-screens-generated-reference-v13-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (SALES, SLA, CAL, SALES_CSS, SHARED_CSS):
    shutil.copy2(p, backup / p.name)

def add_marker(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

for p in (SALES, SLA, CAL):
    add_marker(p)

# SALES: add reference quote in hero and a real-data-safe tip strip.
sales = SALES.read_text(encoding="utf-8")
if "tcrm-v13-hero-quote" not in sales:
    anchor = '''        >
          <DateRangePicker value={dateRange} onChange={setDateRange} isRTL={isRTL} />
        </PageBanner>'''
    repl = '''        >
          <div className="tcrm-v13-hero-quote" aria-hidden="true">
            <span className="tcrm-v13-quote-mark">“</span>
            <strong>{isRTL ? "محادثات أكثر. فرص أكثر." : "More Conversations. More Opportunities."}</strong>
            <span className="tcrm-v13-quote-mark">”</span>
          </div>
          <DateRangePicker value={dateRange} onChange={setDateRange} isRTL={isRTL} />
        </PageBanner>'''
    if anchor not in sales:
        raise SystemExit("ERROR=SALES_HERO_ANCHOR_NOT_FOUND")
    sales = sales.replace(anchor, repl, 1)

if "tcrm-v13-stage-tip" not in sales:
    anchor = '''          </CardContent>
        </Card>
        </div>
      </div>
    </CRMLayout>'''
    repl = '''          </CardContent>
          <div className="tcrm-v13-stage-tip">
            <span>💡</span>
            <p>{isRTL ? "ركّز على نقل المزيد من العملاء من مرحلة التواصل إلى جدولة اجتماع لرفع معدل التحويل." : "Tip: Focus on moving more leads from Contacted to Meeting Scheduled to improve your conversion rate."}</p>
          </div>
        </Card>
        </div>
      </div>
    </CRMLayout>'''
    if anchor not in sales:
        raise SystemExit("ERROR=SALES_STAGE_TIP_ANCHOR_NOT_FOUND")
    sales = sales.replace(anchor, repl, 1)
SALES.write_text(sales, encoding="utf-8")

# SLA: add generated-reference quote in the PageBanner.
sla = SLA.read_text(encoding="utf-8")
if "tcrm-v13-hero-quote" not in sla:
    anchor = '''        >
          {isManager && ('''
    repl = '''        >
          <div className="tcrm-v13-hero-quote" aria-hidden="true">
            <span className="tcrm-v13-quote-mark">“</span>
            <strong>{isRTL ? "تابع الأداء. اصنع التميز." : "Track Performance. Drive Excellence."}</strong>
            <span className="tcrm-v13-quote-mark">”</span>
          </div>
          {isManager && ('''
    if anchor not in sla:
        raise SystemExit("ERROR=SLA_HERO_ANCHOR_NOT_FOUND")
    sla = sla.replace(anchor, repl, 1)
SLA.write_text(sla, encoding="utf-8")

# CALENDAR: align copy to generated reference while preserving existing real controls/actions.
cal = CAL.read_text(encoding="utf-8")
cal = cal.replace(
    '{isRTL ? "ابقَ منظماً" : "Stay organized"}',
    '{isRTL ? "ابقَ منظماً" : "Stay organized"}'
)
cal = cal.replace(
    '{isRTL ? "حوّل المحادثات إلى فرص" : "Turn conversations into opportunities"}',
    '{isRTL ? "حوّل المحادثات إلى فرص" : "Turn conversations into opportunities"}'
)
CAL.write_text(cal, encoding="utf-8")

SALES_APPEND = r'''

/* TCRM_THREE_SCREENS_GENERATED_REFERENCE_V13 — SALES FUNNEL
   Exact visual direction from the approved generated reference:
   refined lavender executive shell, richer hero, premium KPI cards,
   clean chart surfaces, polished tables and stage cards.
   Existing real data/functions only. */

.tcrm-sales-funnel-reference-lock-v11{
  --v13-ink:#11182c;
  --v13-muted:#75809a;
  --v13-purple:#654cf3;
  --v13-purple2:#826cff;
  --v13-blue:#3d83f7;
  --v13-green:#20b978;
  --v13-cyan:#19b7c8;
  --v13-amber:#f3a51e;
  --v13-red:#ef5267;
  --v13-line:rgba(91,82,169,.13);
  --v13-shadow:0 20px 56px -38px rgba(52,42,124,.32),0 5px 16px -13px rgba(45,55,104,.14);
  background:
    radial-gradient(900px 380px at 0% -8%,rgba(125,101,248,.12),transparent 65%),
    radial-gradient(720px 320px at 92% 0%,rgba(152,128,255,.08),transparent 70%),
    linear-gradient(180deg,#fcfbff 0%,#f8f8fd 47%,#f3f5fb 100%)!important;
}

/* hero */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div{
  position:relative!important;
  min-height:112px!important;
  padding:18px 20px!important;
  overflow:hidden!important;
  border:1px solid rgba(104,84,238,.18)!important;
  border-radius:22px!important;
  background:
    radial-gradient(78% 180% at 73% 45%,rgba(173,155,255,.27),transparent 64%),
    radial-gradient(60% 160% at 90% 5%,rgba(255,255,255,.62),transparent 60%),
    linear-gradient(120deg,#ffffff 0%,#faf8ff 48%,#e9e4ff 100%)!important;
  box-shadow:0 24px 64px -45px rgba(75,56,179,.40),inset 0 1px 0 rgba(255,255,255,.98)!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div::before{
  content:"";
  position:absolute;
  width:420px;
  height:210px;
  inset-inline-end:100px;
  top:-85px;
  border:1px solid rgba(112,90,231,.08);
  border-radius:50%;
  transform:rotate(-8deg);
  background:
    radial-gradient(circle at 30% 60%,rgba(104,84,238,.10),transparent 33%),
    linear-gradient(135deg,rgba(255,255,255,.16),rgba(104,84,238,.035));
  pointer-events:none;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell > div::after{
  content:"";
  position:absolute;
  width:240px;
  height:240px;
  inset-inline-end:-74px;
  top:-132px;
  border:1px solid rgba(104,84,238,.08);
  border-radius:48px;
  transform:rotate(18deg);
  pointer-events:none;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell .w-11.h-11{
  width:48px!important;
  height:48px!important;
  border-radius:15px!important;
  background:linear-gradient(145deg,#795fff,#5a40d5)!important;
  border:1px solid rgba(255,255,255,.75)!important;
  box-shadow:0 18px 36px -21px rgba(81,56,202,.70),inset 0 1px 0 rgba(255,255,255,.38)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell h1{
  color:var(--v13-ink)!important;
  font-size:22px!important;
  font-weight:900!important;
  letter-spacing:-.04em!important;
  text-shadow:none!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell p{
  color:#75809a!important;
  font-size:11.5px!important;
  font-weight:600!important;
  text-shadow:none!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v13-hero-quote{
  position:relative!important;
  z-index:2!important;
  display:flex!important;
  align-items:center!important;
  gap:8px!important;
  margin-inline-start:auto!important;
  margin-inline-end:18px!important;
  color:#6248eb!important;
  font-size:12px!important;
  font-weight:800!important;
  white-space:nowrap!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v13-quote-mark{
  color:#7359f2!important;
  font-size:24px!important;
  line-height:1!important;
  opacity:.84!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell button,
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-page-banner-shell [role="button"]{
  min-height:42px!important;
  border:1px solid rgba(78,64,166,.18)!important;
  border-radius:12px!important;
  background:linear-gradient(180deg,#5243a8,#41378d)!important;
  color:#fff!important;
  box-shadow:0 14px 28px -18px rgba(46,34,128,.70),inset 0 1px 0 rgba(255,255,255,.13)!important;
}

/* KPI row */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-kpi-grid{gap:12px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card{
  min-height:116px!important;
  position:relative!important;
  overflow:hidden!important;
  border:1px solid var(--v13-line)!important;
  border-radius:19px!important;
  background:
    radial-gradient(135px 85px at 96% 0%,rgba(104,84,238,.06),transparent 72%),
    linear-gradient(150deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card::before{
  height:2px!important;
  opacity:.9!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card::after{
  content:"";
  position:absolute;
  inset:auto 16px 12px auto;
  width:78px;
  height:28px;
  border-bottom:2px solid currentColor;
  border-radius:50%;
  opacity:.11;
  transform:skewX(-22deg) rotate(-7deg);
  pointer-events:none;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card [data-slot="card-content"]{padding:15px 16px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .kpi-icon{
  width:36px!important;height:36px!important;border-radius:12px!important;
  box-shadow:0 12px 24px -15px currentColor,inset 0 1px 0 rgba(255,255,255,.32)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card .text-2xl{
  color:var(--v13-ink)!important;
  font-size:24px!important;
  font-weight:900!important;
  letter-spacing:-.045em!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card p{font-size:10.5px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-kpi-card p.text-green-600{font-size:10px!important}

/* cards */
.tcrm-sales-funnel-reference-lock-v11 [data-slot="card"],
.tcrm-sales-funnel-reference-lock-v11 .chart-container{
  border:1px solid var(--v13-line)!important;
  border-radius:19px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-header"]{
  min-height:52px!important;
  padding:12px 15px!important;
  border-bottom:1px solid rgba(82,76,125,.075)!important;
  background:linear-gradient(180deg,#fdfdff,#fff)!important;
}
.tcrm-sales-funnel-reference-lock-v11 [data-slot="card-title"]{
  color:#1c2438!important;
  font-weight:850!important;
  letter-spacing:-.02em!important;
}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview{
  grid-template-columns:minmax(0,.94fr) minmax(0,1.06fr)!important;
  gap:14px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .chart-container{min-height:340px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .recharts-responsive-container{height:250px!important;min-height:250px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-sales-overview .group > .flex-1 > div{
  height:32px!important;
  border-radius:8px!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.25),0 9px 20px -14px rgba(42,45,95,.45)!important;
}

/* commercial row */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v3-sales-commercial{
  gap:14px!important;
  grid-template-columns:minmax(380px,.76fr) minmax(0,1.24fr)!important;
  grid-template-rows:150px auto!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly{
  height:150px!important;min-height:150px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly [data-slot="card-content"]{height:102px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-won-monthly .h-56{height:76px!important}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-chart .recharts-responsive-container{height:295px!important;min-height:295px!important}

/* deal summary: keep real data but make it visually secondary */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary{
  background:linear-gradient(180deg,#fff,#fafaff)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-summary-content{
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:8px!important;
  padding:9px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-deal-stat{
  min-height:68px!important;
  padding:8px 9px!important;
  border-radius:12px!important;
  background:#fff!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-deal-summary .tcrm-v11-potential-closings{
  grid-column:1/-1!important;
  border-radius:12px!important;
}

/* bottom row */
.tcrm-sales-funnel-reference-lock-v11 .tcrm-sales-bottom-grid-v11{
  grid-template-columns:minmax(0,1.62fr) minmax(360px,.9fr)!important;
  gap:14px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-campaign-table [data-slot="card-content"]{padding:0!important}
.tcrm-sales-funnel-reference-lock-v11 table thead tr{
  background:linear-gradient(180deg,#f7f6fc,#f1f2f8)!important;
}
.tcrm-sales-funnel-reference-lock-v11 th{
  padding:8px 10px!important;
  color:#6c7690!important;
  font-size:9.5px!important;
  font-weight:850!important;
}
.tcrm-sales-funnel-reference-lock-v11 td{
  padding:8px 10px!important;
  color:#536078!important;
  font-size:10px!important;
}
.tcrm-sales-funnel-reference-lock-v11 tbody tr:nth-child(even){background:#fafaff!important}
.tcrm-sales-funnel-reference-lock-v11 tbody tr:hover{background:#f6f4ff!important}

.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex{
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  gap:7px!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div{
  min-height:82px!important;
  padding:9px!important;
  border:1px solid rgba(88,79,140,.10)!important;
  border-radius:13px!important;
  background:linear-gradient(145deg,#fff,#fafbff)!important;
  box-shadow:0 10px 22px -19px rgba(47,51,92,.20)!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v13-stage-tip{
  margin:0 12px 12px!important;
  padding:9px 11px!important;
  display:flex!important;
  align-items:flex-start!important;
  gap:8px!important;
  border:1px solid rgba(104,84,238,.10)!important;
  border-radius:11px!important;
  background:linear-gradient(135deg,#f9f6ff,#f3f0ff)!important;
  color:#6654df!important;
  font-size:9px!important;
  font-weight:650!important;
}
.tcrm-sales-funnel-reference-lock-v11 .tcrm-v13-stage-tip p{margin:0!important;line-height:1.45!important}

@media(max-width:1365px){
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v13-hero-quote{display:none!important}
  .tcrm-sales-funnel-reference-lock-v11 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex{
    grid-template-columns:repeat(3,minmax(0,1fr))!important;
  }
}
'''

SHARED_APPEND = r'''

/* TCRM_THREE_SCREENS_GENERATED_REFERENCE_V13 — TASKS & SLA + CALENDAR */

/* shared page background */
.tcrm-sla-reference-lock-v9,
.tcrm-calendar-reference-lock-v9{
  --v13-ink:#11182c;
  --v13-muted:#75809a;
  --v13-purple:#654cf3;
  --v13-purple2:#826cff;
  --v13-blue:#3d83f7;
  --v13-green:#20b978;
  --v13-amber:#f3a51e;
  --v13-red:#ef5267;
  --v13-line:rgba(91,82,169,.13);
  --v13-shadow:0 20px 56px -38px rgba(52,42,124,.32),0 5px 16px -13px rgba(45,55,104,.14);
  background:
    radial-gradient(900px 380px at 0% -8%,rgba(125,101,248,.11),transparent 65%),
    linear-gradient(180deg,#fcfbff 0%,#f8f8fd 47%,#f3f5fb 100%)!important;
}

/* ---------- SLA ---------- */
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell > div{
  position:relative!important;
  min-height:108px!important;
  padding:18px 20px!important;
  overflow:hidden!important;
  border:1px solid rgba(104,84,238,.18)!important;
  border-radius:22px!important;
  background:
    radial-gradient(78% 180% at 73% 45%,rgba(173,155,255,.27),transparent 64%),
    radial-gradient(60% 160% at 90% 5%,rgba(255,255,255,.62),transparent 60%),
    linear-gradient(120deg,#fff 0%,#faf8ff 48%,#e9e4ff 100%)!important;
  box-shadow:0 24px 64px -45px rgba(75,56,179,.40),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell > div::after{
  content:"";
  position:absolute;
  width:360px;height:180px;
  inset-inline-end:95px;top:-72px;
  border:1px solid rgba(112,90,231,.08);
  border-radius:50%;
  transform:rotate(-8deg);
  background:linear-gradient(135deg,rgba(255,255,255,.16),rgba(104,84,238,.04));
  pointer-events:none;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell .w-11.h-11{
  width:48px!important;height:48px!important;border-radius:15px!important;
  background:linear-gradient(145deg,#795fff,#5a40d5)!important;
  box-shadow:0 18px 36px -21px rgba(81,56,202,.70),inset 0 1px 0 rgba(255,255,255,.38)!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell h1{
  color:var(--v13-ink)!important;font-size:22px!important;font-weight:900!important;letter-spacing:-.04em!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell p{
  color:#75809a!important;font-size:11.5px!important;font-weight:600!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v13-hero-quote{
  position:relative!important;z-index:2!important;
  display:flex!important;align-items:center!important;gap:8px!important;
  margin-inline-start:auto!important;margin-inline-end:16px!important;
  color:#6248eb!important;font-size:11.5px!important;font-weight:800!important;white-space:nowrap!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v13-quote-mark{
  color:#7359f2!important;font-size:22px!important;line-height:1!important;opacity:.84!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell label{color:#5f6880!important}
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell select,
.tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell button{
  min-height:40px!important;
  border-radius:11px!important;
  border:1px solid rgba(104,84,238,.15)!important;
  background:#fff!important;
  color:#39415d!important;
  box-shadow:0 9px 20px -16px rgba(61,55,137,.28)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-kpi-grid{gap:12px!important}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card{
  min-height:108px!important;
  border:1px solid var(--v13-line)!important;
  border-radius:19px!important;
  background:
    radial-gradient(130px 80px at 96% 0%,rgba(104,84,238,.055),transparent 72%),
    linear-gradient(150deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card::after{
  content:"";
  position:absolute;
  inset:auto 14px 11px auto;
  width:72px;height:26px;
  border-bottom:2px solid currentColor;
  border-radius:50%;
  opacity:.10;
  transform:skewX(-22deg) rotate(-7deg);
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card .text-2xl{
  color:var(--v13-ink)!important;font-size:23px!important;font-weight:900!important;letter-spacing:-.04em!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v3-kpi-card .kpi-icon{
  width:36px!important;height:36px!important;border-radius:12px!important;
  box-shadow:0 12px 24px -15px currentColor,inset 0 1px 0 rgba(255,255,255,.32)!important;
}

.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-health{
  min-height:50px!important;
  border-radius:15px!important;
  border-color:var(--v13-line)!important;
  box-shadow:var(--v13-shadow)!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item{
  padding:10px 15px!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item span{font-size:9px!important}
.tcrm-sla-reference-lock-v9 .tcrm-v21-health-item strong{font-size:11px!important}

.tcrm-sla-reference-lock-v9 [data-slot="card"]{
  border-color:var(--v13-line)!important;
  border-radius:18px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-sla-reference-lock-v9 [data-slot="card-header"]{
  min-height:48px!important;
  padding:11px 14px!important;
  background:linear-gradient(180deg,#fdfdff,#fff)!important;
}
.tcrm-sla-reference-lock-v9 [data-slot="card-title"]{
  color:#1c2438!important;font-weight:850!important;letter-spacing:-.02em!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends,
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution{
  gap:14px!important;
}
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-trends .recharts-responsive-container{height:225px!important;min-height:225px!important}
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-distribution .recharts-responsive-container{height:195px!important;min-height:195px!important}
.tcrm-sla-reference-lock-v9 table thead tr{
  background:linear-gradient(180deg,#f7f6fc,#f1f2f8)!important;
}
.tcrm-sla-reference-lock-v9 table th{
  padding:8px 10px!important;color:#6c7690!important;font-size:9.5px!important;font-weight:850!important;
}
.tcrm-sla-reference-lock-v9 table td{
  padding:8px 10px!important;color:#536078!important;font-size:10px!important;
}
.tcrm-sla-reference-lock-v9 table tbody tr:nth-child(even){background:#fafaff!important}
.tcrm-sla-reference-lock-v9 .tcrm-v21-sla-breaches{
  border-top:3px solid var(--v13-red)!important;
  box-shadow:0 18px 42px -34px rgba(208,48,73,.28)!important;
}

/* ---------- CALENDAR ---------- */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
  min-height:124px!important;
  position:relative!important;
  overflow:hidden!important;
  border:1px solid rgba(104,84,238,.18)!important;
  border-radius:22px!important;
  background:
    radial-gradient(76% 190% at 63% 48%,rgba(174,155,255,.28),transparent 63%),
    radial-gradient(55% 140% at 88% 5%,rgba(255,255,255,.64),transparent 60%),
    linear-gradient(120deg,#fff 0%,#faf8ff 48%,#e8e2ff 100%)!important;
  box-shadow:0 24px 64px -45px rgba(75,56,179,.40),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero::before{
  content:"";
  position:absolute;
  width:260px;height:160px;
  left:47%;top:-32px;
  border-radius:44% 56% 50% 50%;
  background:
    radial-gradient(circle at 50% 50%,rgba(108,84,238,.13),transparent 38%),
    linear-gradient(135deg,rgba(255,255,255,.18),rgba(104,84,238,.035));
  transform:rotate(-6deg);
  pointer-events:none;
}
.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9{
  gap:14px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 > div:first-child{
  width:52px!important;height:52px!important;min-width:52px!important;border-radius:16px!important;
  background:linear-gradient(145deg,#795fff,#5a40d5)!important;
  box-shadow:0 18px 36px -21px rgba(81,56,202,.70),inset 0 1px 0 rgba(255,255,255,.38)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 h1{
  color:var(--v13-ink)!important;font-size:23px!important;font-weight:900!important;letter-spacing:-.04em!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-calendar-title-v9 p{
  color:#75809a!important;font-size:11.5px!important;font-weight:600!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note{
  margin-inline-start:auto!important;margin-inline-end:28px!important;
  padding:8px 12px!important;
  border-left:2px solid rgba(104,84,238,.40)!important;
  gap:10px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note > svg{
  width:50px!important;height:50px!important;color:#765ff3!important;opacity:.18!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note strong{
  color:#654cf3!important;font-size:11.5px!important;font-weight:850!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note span{
  color:#7d879d!important;font-size:9.5px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero > button{
  min-height:44px!important;
  border-radius:12px!important;
  background:linear-gradient(180deg,#7258ef,#5a43ce)!important;
  box-shadow:0 15px 31px -19px rgba(74,54,183,.70),inset 0 1px 0 rgba(255,255,255,.18)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpis{gap:12px!important}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi{
  min-height:110px!important;
  border:1px solid var(--v13-line)!important;
  border-radius:19px!important;
  background:
    radial-gradient(130px 80px at 96% 0%,rgba(104,84,238,.055),transparent 72%),
    linear-gradient(150deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi::after{
  content:"";
  position:absolute;
  inset:auto 16px 13px auto;
  width:82px;height:28px;
  border-bottom:2px solid currentColor;
  border-radius:50%;
  opacity:.10;
  transform:skewX(-22deg) rotate(-7deg);
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi-icon{
  width:42px!important;height:42px!important;border-radius:13px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi strong{
  color:var(--v13-ink)!important;font-size:24px!important;font-weight:900!important;letter-spacing:-.045em!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi span{font-size:10.5px!important}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-layout{
  grid-template-columns:minmax(0,4fr) minmax(285px,.9fr)!important;
  gap:14px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main,
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  border:1px solid var(--v13-line)!important;
  border-radius:20px!important;
  background:linear-gradient(180deg,#fff,#fbfcff)!important;
  box-shadow:var(--v13-shadow)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar{
  min-height:62px!important;padding:10px 14px!important;
  background:linear-gradient(180deg,#fdfdff,#fafaff)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav > button{
  min-width:36px!important;min-height:36px!important;border-radius:11px!important;
  border-color:rgba(88,79,140,.12)!important;
  box-shadow:0 9px 22px -18px rgba(47,51,92,.25)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav .tcrm-v10-today-btn{
  padding-inline:15px!important;font-weight:820!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-month-title{
  color:#1d2539!important;font-size:17px!important;font-weight:900!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  min-height:50px!important;
  background:linear-gradient(180deg,#f8f8fc,#f3f4f8)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:100px!important;
  border-color:rgba(72,79,113,.085)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-violet-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-blue-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-emerald-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-amber-100"],
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main [class*="bg-rose-100"]{
  min-height:22px!important;
  border-radius:8px!important;
  padding:3px 6px!important;
  box-shadow:0 7px 16px -14px rgba(59,49,120,.26)!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:60px!important;
  background:linear-gradient(180deg,#fdfdff,#fafaff)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:last-child{
  padding:12px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:last-child > div:not(.tcrm-v10-upcoming-empty){
  border-radius:12px!important;
  border:1px solid rgba(88,79,140,.08)!important;
  background:#fff!important;
  box-shadow:0 8px 20px -18px rgba(47,51,92,.18)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-upcoming-empty > .w-12.h-12{
  width:62px!important;height:62px!important;border-radius:18px!important;
  background:linear-gradient(145deg,#f4f1ff,#ebe6ff)!important;
  box-shadow:0 14px 26px -21px rgba(89,68,194,.32)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action > button{
  min-height:60px!important;
  border:1px solid rgba(88,79,140,.08)!important;
  border-radius:12px!important;
  background:linear-gradient(145deg,#fff,#fafaff)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note{
  border-radius:13px!important;
  background:linear-gradient(135deg,#fffaf2,#f5f2ff)!important;
}

/* dark */
.dark .tcrm-sla-reference-lock-v9,
.dark .tcrm-calendar-reference-lock-v9{
  background:
    radial-gradient(900px 380px at 4% -6%,rgba(93,70,224,.18),transparent 66%),
    linear-gradient(180deg,#07111e,#081827 54%,#071321)!important;
}
.dark .tcrm-sla-reference-lock-v9 .tcrm-v3-page-banner-shell > div,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero{
  border-color:rgba(118,100,232,.22)!important;
  background:
    radial-gradient(66% 170% at 76% 48%,rgba(111,80,239,.16),transparent 66%),
    linear-gradient(135deg,#0b1c35,#101d42)!important;
}
.dark .tcrm-sla-reference-lock-v9 [data-slot="card"],
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-main,
.dark .tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming{
  background:linear-gradient(160deg,#0d2139,#0a1b30)!important;
  border-color:rgba(111,127,189,.16)!important;
  box-shadow:0 24px 54px -39px rgba(0,0,0,.90),inset 0 1px 0 rgba(255,255,255,.025)!important;
}

@media(max-width:1365px){
  .tcrm-sla-reference-lock-v9 .tcrm-v13-hero-quote{display:none!important}
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note{display:none!important}
}
'''

sales_css = SALES_CSS.read_text(encoding="utf-8")
if MARKER not in sales_css:
    SALES_CSS.write_text(sales_css + SALES_APPEND, encoding="utf-8")

shared_css = SHARED_CSS.read_text(encoding="utf-8")
if MARKER not in shared_css:
    SHARED_CSS.write_text(shared_css + SHARED_APPEND, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=THREE_SCREENS_GENERATED_REFERENCE_V13")
print("SALES=REFERENCE_LOCK")
print("SLA=REFERENCE_LOCK")
print("CALENDAR=REFERENCE_LOCK")
print("NO_NEW_CSS_IMPORTS=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=5")
print(f"BACKUP={backup}")
