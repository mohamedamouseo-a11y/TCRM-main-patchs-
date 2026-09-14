#!/usr/bin/env python3
# TCRM_SALES_MODULE_PREMIUM_V2_1_CORRECTIVE_REFERENCE_MATCH
# Corrective structural/UI pass for Sales Funnel + Tasks & SLA + Calendar only.
# Designed to run ON TOP OF Premium V2 already applied on the server working tree.

from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

ROOT = Path.cwd()
FILES = {
    "sales": ROOT / "client/src/pages/SalesFunnelDashboard.tsx",
    "sla": ROOT / "client/src/pages/TaskSlaDashboard.tsx",
    "calendar": ROOT / "client/src/pages/CalendarPage.tsx",
}
BASE_CSS = ROOT / "client/src/sales-module-premium-v2-three-screen.css"
CSS_PATH = ROOT / "client/src/sales-module-premium-v2-1-corrective.css"
BASE_MARKER = "TCRM_SALES_MODULE_PREMIUM_V2_3_SCREENS_REFERENCE_MATCH"
MARKER = "TCRM_SALES_MODULE_PREMIUM_V2_1_CORRECTIVE_REFERENCE_MATCH"
IMPORT_LINE = 'import "../sales-module-premium-v2-1-corrective.css";'

missing = [str(p) for p in [*FILES.values(), BASE_CSS] if not p.exists()]
if missing:
    print("PATCH=NO")
    print("ERROR=MISSING_REQUIRED_FILES:" + ",".join(missing))
    sys.exit(1)

for key, path in FILES.items():
    txt = path.read_text(encoding="utf-8")
    if BASE_MARKER not in txt:
        print("PATCH=NO")
        print(f"ERROR=PREMIUM_V2_BASE_MARKER_MISSING:{key}")
        sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / f".patch-backups/sales-module-premium-v2-1-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
for path in [*FILES.values(), BASE_CSS, CSS_PATH]:
    if path.exists():
        dest = backup_dir / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def ensure_marker_import(text: str, import_anchor: str) -> str:
    if MARKER not in text:
        text = text.replace(f"// {BASE_MARKER}", f"// {BASE_MARKER}\n// {MARKER}", 1)
    if IMPORT_LINE not in text:
        idx = text.find(import_anchor)
        if idx < 0:
            raise RuntimeError(f"import anchor missing: {import_anchor}")
        text = text[:idx] + IMPORT_LINE + "\n\n" + text[idx:]
    return text


def add_root_class(text: str, class_name: str) -> str:
    idx = text.rfind("<CRMLayout>")
    if idx < 0:
        raise RuntimeError("main CRMLayout missing")
    tail = text[idx:]
    m = re.search(r'(<div\s+className=")([^"]+)("\s+dir=)', tail)
    if not m:
        raise RuntimeError("main root div missing")
    classes = m.group(2).split()
    if class_name not in classes:
        classes.insert(0, class_name)
        repl = m.group(1) + " ".join(classes) + m.group(3)
        tail = tail[:m.start()] + repl + tail[m.end():]
    return text[:idx] + tail


# -----------------------------------------------------------------------------
# Sales Funnel: stronger information hierarchy and section identity.
# -----------------------------------------------------------------------------
sales_path = FILES["sales"]
sales = sales_path.read_text(encoding="utf-8")
sales = ensure_marker_import(sales, "const FUNNEL_COLORS")
sales = add_root_class(sales, "tcrm-sales-premium-v21")
sales = replace_once(
    sales,
    'className="grid grid-cols-2 md:grid-cols-5 gap-4 stagger-children"',
    'className="tcrm-v21-kpi-grid grid grid-cols-2 md:grid-cols-5 gap-4 stagger-children"',
    "sales KPI grid",
)
sales = replace_once(
    sales,
    '        {/* Funnel Visualization + Stage Breakdown */}\n        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">',
    '        {/* Funnel Visualization + Stage Breakdown */}\n        <div className="tcrm-v21-sales-overview grid grid-cols-1 lg:grid-cols-2 gap-6">',
    "sales overview grid",
)
sales = replace_once(
    sales,
    '        {/* Won Deals Monthly Trend */}\n        <Card className="chart-container">',
    '        {/* Won Deals Monthly Trend */}\n        <Card className="chart-container tcrm-v21-won-monthly">',
    "won monthly card",
)
sales = replace_once(
    sales,
    '        {/* Campaign Performance + Deal Summary */}\n        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">',
    '        {/* Campaign Performance + Deal Summary */}\n        <div className="tcrm-v21-campaign-deal-grid grid grid-cols-1 lg:grid-cols-3 gap-6">',
    "campaign deal grid",
)
sales = replace_once(
    sales,
    '<Card className="lg:col-span-2 chart-container">',
    '<Card className="lg:col-span-2 chart-container tcrm-v21-campaign-chart">',
    "campaign chart card",
)
sales = replace_once(
    sales,
    '<Card className="slide-up" style={{ animationDelay: \'0.2s\' }}>',
    '<Card className="slide-up tcrm-v21-deal-summary" style={{ animationDelay: \'0.2s\' }}>',
    "deal summary card",
)
sales = replace_once(
    sales,
    '        {/* Campaign Performance Table */}\n        <Card className="slide-up" style={{ animationDelay: \'0.3s\' }}>',
    '        {/* Campaign Performance Table */}\n        <Card className="slide-up tcrm-v21-campaign-table" style={{ animationDelay: \'0.3s\' }}>',
    "campaign table card",
)
sales = replace_once(
    sales,
    '        {/* Conversion Rates Stage-by-Stage */}\n        <Card className="slide-up" style={{ animationDelay: \'0.4s\' }}>',
    '        {/* Conversion Rates Stage-by-Stage */}\n        <Card className="slide-up tcrm-v21-stage-conversion" style={{ animationDelay: \'0.4s\' }}>',
    "stage conversion card",
)
sales_path.write_text(sales, encoding="utf-8")


# -----------------------------------------------------------------------------
# Tasks & SLA: create a stronger operational dashboard hierarchy using REAL data.
# No fake task dataset is introduced.
# -----------------------------------------------------------------------------
sla_path = FILES["sla"]
sla = sla_path.read_text(encoding="utf-8")
sla = ensure_marker_import(sla, "const COLORS")
sla = add_root_class(sla, "tcrm-sales-premium-v21")
sla = replace_once(
    sla,
    'className="grid grid-cols-2 md:grid-cols-4 gap-4"',
    'className="tcrm-v21-kpi-grid tcrm-v21-sla-kpis grid grid-cols-2 md:grid-cols-4 gap-4"',
    "sla KPI grid",
)
health_anchor = '''          ))}\n        </div>\n\n        {/* SLA Trend + Activity Trend */}'''
health_insert = '''          ))}\n        </div>\n\n        <div className="tcrm-v21-sla-health" aria-label={isRTL ? "ملخص صحة SLA" : "SLA health summary"}>\n          <div className="tcrm-v21-health-item">\n            <span>{isRTL ? "النطاق" : "Scope"}</span>\n            <strong>{selectedAgentName}</strong>\n          </div>\n          <div className="tcrm-v21-health-item">\n            <span>{isRTL ? "الحالة" : "Health"}</span>\n            <strong className={(sla?.complianceRate ?? 100) >= 80 ? "is-good" : "is-risk"}>\n              {(sla?.complianceRate ?? 100) >= 80 ? (isRTL ? "مستقر" : "Healthy") : (isRTL ? "يحتاج متابعة" : "Needs attention")}\n            </strong>\n          </div>\n          <div className="tcrm-v21-health-item">\n            <span>{isRTL ? "التجاوزات" : "Breaches"}</span>\n            <strong className={(sla?.breachedCount ?? 0) > 0 ? "is-risk" : "is-good"}>{sla?.breachedCount ?? 0}</strong>\n          </div>\n        </div>\n\n        {/* SLA Trend + Activity Trend */}'''
sla = replace_once(sla, health_anchor, health_insert, "sla health strip")
sla = replace_once(
    sla,
    '        {/* SLA Trend + Activity Trend */}\n        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">',
    '        {/* SLA Trend + Activity Trend */}\n        <div className="tcrm-v21-sla-trends grid grid-cols-1 lg:grid-cols-2 gap-6">',
    "sla trends grid",
)
sla = replace_once(
    sla,
    '        {/* Activity Type + Outcome Distribution */}\n        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">',
    '        {/* Activity Type + Outcome Distribution */}\n        <div className="tcrm-v21-sla-distribution grid grid-cols-1 lg:grid-cols-2 gap-6">',
    "sla distribution grid",
)
sla = replace_once(
    sla,
    '        {/* Agent SLA Performance Table */}\n        <Card>',
    '        {/* Agent SLA Performance Table */}\n        <Card className="tcrm-v21-sla-agent-performance">',
    "sla performance card",
)
sla = replace_once(
    sla,
    '        {/* Agent Activity Breakdown Table */}\n        <Card>',
    '        {/* Agent Activity Breakdown Table */}\n        <Card className="tcrm-v21-sla-activity-table">',
    "sla activity table card",
)
sla = replace_once(
    sla,
    '        {/* SLA Breached Leads List */}\n        <Card>',
    '        {/* SLA Breached Leads List */}\n        <Card className="tcrm-v21-sla-breaches">',
    "sla breaches card",
)
sla_path.write_text(sla, encoding="utf-8")


# -----------------------------------------------------------------------------
# Calendar: add real-data KPI overview and premium main/rail hierarchy.
# -----------------------------------------------------------------------------
cal_path = FILES["calendar"]
cal = cal_path.read_text(encoding="utf-8")
cal = ensure_marker_import(cal, "interface EventForm")
cal = add_root_class(cal, "tcrm-sales-premium-v21")
cal = replace_once(
    cal,
    '  const upcomingEvents = (events ?? []).filter((e: any) => new Date(e.start) >= new Date()).slice(0, 8);\n  const isDeveloperVisualPreview',
    '  const upcomingEvents = (events ?? []).filter((e: any) => new Date(e.start) >= new Date()).slice(0, 8);\n  const monthEventCount = events?.length ?? 0;\n  const todayEventCount = (events ?? []).filter((e: any) => e.start && isSameDay(parseISO(e.start), new Date())).length;\n  const confirmedEventCount = (events ?? []).filter((e: any) => String(e.status ?? "").toLowerCase() === "confirmed").length;\n  const upcomingEventCount = upcomingEvents.length;\n  const isDeveloperVisualPreview',
    "calendar derived stats",
)
cal = replace_once(
    cal,
    '<div className="flex items-center justify-between flex-wrap gap-3">',
    '<div className="tcrm-v21-calendar-hero flex items-center justify-between flex-wrap gap-3">',
    "calendar hero",
)
calendar_layout_anchor = '''        </div>\n\n        <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">'''
calendar_layout_insert = '''        </div>\n\n        <div className="tcrm-v21-calendar-kpis">\n          {[\n            { label: isRTL ? "إجمالي المواعيد" : "Total Events", value: monthEventCount, icon: <CalendarIcon size={17} />, tone: "violet" },\n            { label: isRTL ? "اليوم" : "Today", value: todayEventCount, icon: <Clock size={17} />, tone: "blue" },\n            { label: isRTL ? "القادمة" : "Upcoming", value: upcomingEventCount, icon: <Users size={17} />, tone: "emerald" },\n            { label: isRTL ? "المؤكدة" : "Confirmed", value: confirmedEventCount, icon: <CalendarIcon size={17} />, tone: "amber" },\n          ].map((stat) => (\n            <div key={stat.label} className={`tcrm-v21-calendar-kpi is-${stat.tone}`}>\n              <div className="tcrm-v21-calendar-kpi-icon">{stat.icon}</div>\n              <div>\n                <strong>{isLoading ? "—" : stat.value}</strong>\n                <span>{stat.label}</span>\n              </div>\n            </div>\n          ))}\n        </div>\n\n        <div className="tcrm-v21-calendar-layout grid grid-cols-1 xl:grid-cols-4 gap-5">'''
cal = replace_once(cal, calendar_layout_anchor, calendar_layout_insert, "calendar KPI/layout insertion")
cal = replace_once(
    cal,
    '<div className="xl:col-span-3 rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">',
    '<div className="tcrm-v21-calendar-main xl:col-span-3 rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">',
    "calendar main panel",
)
cal = replace_once(
    cal,
    '<div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">\n            <div className="flex items-center gap-2.5 px-4 py-4 border-b border-slate-100">',
    '<div className="tcrm-v21-calendar-upcoming rounded-2xl border border-slate-200/80 bg-white shadow-sm overflow-hidden">\n            <div className="flex items-center gap-2.5 px-4 py-4 border-b border-slate-100">',
    "calendar upcoming panel",
)
cal_path.write_text(cal, encoding="utf-8")


CSS = r'''/* TCRM_SALES_MODULE_PREMIUM_V2_1_CORRECTIVE_REFERENCE_MATCH
   Corrective layer on top of Premium V2.
   Goal: stronger UX hierarchy, denser executive composition, real-data only,
   and closer visual behavior to the approved premium references. */

.tcrm-sales-premium-v21 {
  --v21-ink: #14213d;
  --v21-muted: #72809a;
  --v21-border: rgba(91, 102, 170, .16);
  --v21-violet: #665cf2;
  --v21-indigo: #4d56df;
  --v21-blue: #4088f5;
  --v21-cyan: #16b7cf;
  --v21-green: #16b979;
  --v21-amber: #f59e0b;
  --v21-red: #ef5362;
  padding: 22px 24px !important;
  gap: 0 !important;
}

.tcrm-sales-premium-v21 > * + * { margin-top: 16px !important; }

.tcrm-sales-premium-v21 [data-slot="card"] {
  border-radius: 18px !important;
  border-color: var(--v21-border) !important;
  box-shadow: 0 18px 48px -36px rgba(39,48,116,.48), 0 2px 10px rgba(40,52,117,.055) !important;
}

.tcrm-sales-premium-v21 [data-slot="card-header"] {
  min-height: 48px !important;
  padding: 14px 16px 9px !important;
}

.tcrm-sales-premium-v21 [data-slot="card-content"] {
  padding: 12px 16px 16px !important;
}

.tcrm-sales-premium-v21 .tcrm-v21-kpi-grid { gap: 10px !important; }

.tcrm-sales-premium-v21 .tcrm-v21-kpi-grid > [data-slot="card"] {
  min-height: 104px !important;
  background:
    radial-gradient(circle at 90% 8%, rgba(111,99,246,.09), transparent 30%),
    linear-gradient(160deg, rgba(255,255,255,.99), rgba(248,249,255,.95)) !important;
}

.tcrm-sales-premium-v21 .tcrm-v21-kpi-grid [data-slot="card-content"] { padding: 14px !important; }
.tcrm-sales-premium-v21 .tcrm-v21-kpi-grid .text-2xl { font-size: 1.55rem !important; line-height: 1.8rem !important; letter-spacing: -.035em; }

.tcrm-sales-premium-v21 .recharts-cartesian-grid line { stroke: rgba(112,124,171,.12) !important; }
.tcrm-sales-premium-v21 .recharts-text { fill: #7b879f; }

/* ---------------- Sales Funnel ---------------- */
.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sales-overview,
.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-campaign-deal-grid {
  gap: 14px !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sales-overview > [data-slot="card"] {
  min-height: 322px;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-won-monthly [data-slot="card-content"] {
  min-height: 154px;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-won-monthly .h-56 {
  height: 8.5rem !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-campaign-deal-grid {
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, .8fr) !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-deal-summary [data-slot="card-content"] {
  display: grid;
  gap: 8px !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-deal-summary [data-slot="card-content"] > div {
  border-radius: 12px !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-campaign-table table th,
.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-campaign-table table td {
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex {
  display: grid !important;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px !important;
}

.tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex > div {
  min-width: 0 !important;
  padding: 10px !important;
  border-radius: 12px !important;
}

/* ---------------- Tasks & SLA ---------------- */
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-health {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 10px;
  padding: 10px;
  border: 1px solid rgba(100,111,177,.14);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,.76), rgba(247,249,255,.88));
  box-shadow: 0 12px 30px -28px rgba(46,57,128,.45);
}

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 11px;
  border-radius: 11px;
  background: rgba(255,255,255,.72);
  border: 1px solid rgba(105,116,177,.11);
}

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item span { font-size: 11px; color: #7a879f; font-weight: 600; }
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item strong { font-size: 12px; color: var(--v21-ink); }
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item .is-good { color: #109a68; }
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item .is-risk { color: #e34f60; }

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-trends,
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-distribution { gap: 14px !important; }

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-trends > [data-slot="card"] { min-height: 320px; }
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-distribution > [data-slot="card"] { min-height: 260px; }

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-agent-performance table th,
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-agent-performance table td,
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-activity-table table th,
.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-activity-table table td {
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-breaches {
  border-color: rgba(239,83,98,.16) !important;
}

.tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-breaches [data-slot="card-header"] {
  background: linear-gradient(180deg, rgba(255,247,248,.92), rgba(255,255,255,0)) !important;
}

/* ---------------- Calendar ---------------- */
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-hero {
  min-height: 88px;
  padding: 16px 18px;
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 18px;
  color: white;
  background:
    radial-gradient(circle at 90% -30%, rgba(255,255,255,.24), transparent 32%),
    linear-gradient(108deg, #6661e8 0%, #7467ed 52%, #5d51d4 100%);
  box-shadow: 0 18px 40px -30px rgba(74,64,195,.72);
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-hero h1 { color: white !important; font-size: 1.15rem !important; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-hero p { color: rgba(255,255,255,.72) !important; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-hero > div:first-child > div:first-child {
  background: rgba(255,255,255,.16) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 8px 24px -16px rgba(10,15,70,.5) !important;
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-hero button {
  border: 1px solid rgba(255,255,255,.26) !important;
  box-shadow: 0 10px 28px -16px rgba(20,16,93,.7) !important;
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 10px;
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi {
  min-height: 86px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  border-radius: 16px;
  border: 1px solid rgba(95,107,175,.14);
  background: linear-gradient(160deg, rgba(255,255,255,.98), rgba(248,250,255,.95));
  box-shadow: 0 15px 36px -31px rgba(46,55,124,.48), 0 2px 8px rgba(40,52,116,.05);
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi-icon {
  width: 38px; height: 38px; border-radius: 12px;
  display: grid; place-items: center;
  background: rgba(102,92,242,.11); color: #665cf2;
}
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi.is-blue .tcrm-v21-calendar-kpi-icon { background: rgba(64,136,245,.11); color: #4088f5; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi.is-emerald .tcrm-v21-calendar-kpi-icon { background: rgba(22,185,121,.11); color: #16a86f; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi.is-amber .tcrm-v21-calendar-kpi-icon { background: rgba(245,158,11,.12); color: #e69100; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi strong { display:block; font-size: 1.35rem; line-height: 1.4rem; color: var(--v21-ink); letter-spacing: -.03em; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi span { display:block; margin-top:4px; font-size:11px; color:#7c879d; font-weight:600; }

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-layout { gap: 14px !important; align-items: stretch; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main,
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming {
  border-radius: 18px !important;
  border-color: rgba(95,108,174,.15) !important;
  box-shadow: 0 18px 44px -35px rgba(42,53,125,.5), 0 2px 9px rgba(39,50,112,.05) !important;
}

.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main > .grid.grid-cols-7 > div { min-height: 102px !important; }
.tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming { min-height: 100%; }

/* ---------------- Dark mode ---------------- */
.dark .tcrm-sales-premium-v21 {
  --v21-ink: #eef3ff;
  --v21-muted: #91a0bc;
  --v21-border: rgba(112,130,193,.18);
}

.dark .tcrm-sales-premium-v21 [data-slot="card"],
.dark .tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi,
.dark .tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-health,
.dark .tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item {
  background: linear-gradient(160deg, rgba(12,31,54,.98), rgba(8,25,45,.97)) !important;
  border-color: rgba(108,129,191,.17) !important;
  box-shadow: 0 20px 50px -38px rgba(0,0,0,.9), inset 0 1px 0 rgba(255,255,255,.018) !important;
}

.dark .tcrm-sales-premium-v21 .tcrm-v21-kpi-grid > [data-slot="card"] {
  background:
    radial-gradient(circle at 92% 7%, rgba(103,92,242,.13), transparent 30%),
    linear-gradient(160deg, rgba(13,33,57,.98), rgba(8,25,45,.98)) !important;
}

.dark .tcrm-sales-premium-v21 [data-slot="card-title"],
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi strong,
.dark .tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item strong { color: #eef3ff !important; }

.dark .tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-health-item span,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpi span { color: #8fa0bd !important; }

.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming {
  background: #0c2743 !important;
  border-color: rgba(105,129,191,.18) !important;
}

.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main .border-slate-100,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming .border-slate-100,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main .divide-slate-100 > :not([hidden]) ~ :not([hidden]) {
  border-color: rgba(103,126,181,.13) !important;
}

.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main .text-slate-800,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming .text-slate-800,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main .text-slate-700,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming .text-slate-700 { color: #e9effc !important; }

.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-main .text-slate-400,
.dark .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-upcoming .text-slate-400 { color: #8ea0bd !important; }

.dark .tcrm-sales-premium-v21 table thead tr { background: rgba(18,48,78,.74) !important; }
.dark .tcrm-sales-premium-v21 table thead th { color: #92a3bf !important; }
.dark .tcrm-sales-premium-v21 table tbody td { border-bottom-color: rgba(94,117,174,.10) !important; }

@media (max-width: 1280px) {
  .tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-campaign-deal-grid { grid-template-columns: 1fr !important; }
  .tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex { grid-template-columns: repeat(3,minmax(0,1fr)); }
}

@media (max-width: 900px) {
  .tcrm-sales-premium-v21 { padding: 16px !important; }
  .tcrm-calendar-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-calendar-kpis { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .tcrm-sla-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-sla-health { grid-template-columns: 1fr; }
  .tcrm-sales-funnel-premium-v2.tcrm-sales-premium-v21 .tcrm-v21-stage-conversion [data-slot="card-content"] > .flex { grid-template-columns: repeat(2,minmax(0,1fr)); }
}
'''
CSS_PATH.write_text(CSS, encoding="utf-8")

# Final validation
checks = {
    "sales": [MARKER, IMPORT_LINE, "tcrm-sales-premium-v21", "tcrm-v21-stage-conversion"],
    "sla": [MARKER, IMPORT_LINE, "tcrm-v21-sla-health", "tcrm-v21-sla-breaches"],
    "calendar": [MARKER, IMPORT_LINE, "tcrm-v21-calendar-kpis", "monthEventCount"],
}
for key, needles in checks.items():
    txt = FILES[key].read_text(encoding="utf-8")
    for needle in needles:
        if needle not in txt:
            raise RuntimeError(f"validation failed: {key}:{needle}")

print("PATCH=YES")
print("TCRM_SALES_MODULE_PREMIUM_V2_1=YES")
print("SCREENS=Sales Funnel,Tasks & SLA,Calendar")
print("STRUCTURAL_TSX_CHANGES=YES")
print("CALENDAR_REAL_DATA_KPIS=YES")
print("SLA_OPERATIONAL_HEALTH_STRIP=YES")
print("TEAM_DASHBOARD_CHANGED=NO")
print("LEADS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print(f"BACKUP={backup_dir}")
print("FILES_CHANGED=client/src/pages/SalesFunnelDashboard.tsx,client/src/pages/TaskSlaDashboard.tsx,client/src/pages/CalendarPage.tsx,client/src/sales-module-premium-v2-1-corrective.css")
print("ERROR=NONE")
