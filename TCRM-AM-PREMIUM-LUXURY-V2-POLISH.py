#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
DASH = SRC / "pages/AMDashboard.tsx"
CAL = SRC / "pages/AMCalendarPage.tsx"
CSS = SRC / "index.css"

for p in (DASH, CAL, CSS):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"am-premium-luxury-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (DASH, CAL, CSS):
    shutil.copy2(p, backup / p.name)

# Require V1 hooks so this remains a tiny visual-only delta.
dash = DASH.read_text(encoding="utf-8")
cal = CAL.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")

if "am-dashboard-luxury" not in dash:
    raise SystemExit("ERROR=V1_DASH_HOOK_MISSING")
if "am-calendar-luxury" not in cal:
    raise SystemExit("ERROR=V1_CAL_HOOK_MISSING")

# Move only Portfolio Health legend to the right to use the empty card space better.
old = '''                <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: "#64748b", fontSize: "12px" }}>{v}</span>} />
              </PieChart>'''
new = '''                <Legend
                  layout="vertical"
                  verticalAlign="middle"
                  align="right"
                  iconType="circle"
                  iconSize={8}
                  formatter={(v) => <span style={{ color: "#64748b", fontSize: "12px" }}>{v}</span>}
                  wrapperStyle={{ right: 18 }}
                />
              </PieChart>'''
if new not in dash:
    if old not in dash:
        raise SystemExit("ERROR=PORTFOLIO_LEGEND_ANCHOR_NOT_FOUND")
    dash = dash.replace(old, new, 1)
    DASH.write_text(dash, encoding="utf-8")

marker = "/* TCRM_AM_PREMIUM_LUXURY_V2_POLISH:START */"
if marker not in css:
    css += r'''

/* TCRM_AM_PREMIUM_LUXURY_V2_POLISH:START */

/* Dashboard — fix washed-out KPI visuals and tighten hierarchy */
.am-dashboard-luxury .am-luxury-kpi{
  min-height:108px!important;
  padding:17px 18px!important;
}
.am-dashboard-luxury .am-luxury-kpi > .flex{
  position:relative;
  z-index:2;
}
.am-dashboard-luxury .am-luxury-kpi > .flex > div:last-child{
  width:40px!important;
  height:40px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  padding:0!important;
  border:1px solid currentColor!important;
  border-radius:13px!important;
  box-shadow:0 12px 24px -18px currentColor!important;
}
.am-dashboard-luxury .am-luxury-kpi:nth-child(1) > .flex > div:last-child{
  color:#6548ea!important;background:#f0ecff!important;border-color:#dcd3ff!important;
}
.am-dashboard-luxury .am-luxury-kpi:nth-child(2) > .flex > div:last-child{
  color:#0f9f73!important;background:#e8fbf4!important;border-color:#c8f2e2!important;
}
.am-dashboard-luxury .am-luxury-kpi:nth-child(3) > .flex > div:last-child{
  color:#e58a00!important;background:#fff6df!important;border-color:#ffe8ad!important;
}
.am-dashboard-luxury .am-luxury-kpi:nth-child(4) > .flex > div:last-child{
  color:#e7355a!important;background:#fff0f3!important;border-color:#ffd5df!important;
}
.am-dashboard-luxury .am-luxury-kpi > .flex > div:last-child svg{
  color:currentColor!important;
  stroke-width:2.2!important;
}
.am-dashboard-luxury .am-luxury-kpi p:first-child{
  font-size:11px!important;
  font-weight:750!important;
  letter-spacing:-.01em!important;
}
.am-dashboard-luxury .am-luxury-kpi p.mt-2{
  margin-top:5px!important;
  font-size:28px!important;
  line-height:1!important;
}
.am-dashboard-luxury .am-luxury-kpi::before{
  content:"";
  position:absolute;
  left:0;right:0;top:0;
  height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.9),transparent);
}
.am-dashboard-luxury .am-luxury-section{
  overflow:hidden!important;
}
.am-dashboard-luxury .am-luxury-section > div:first-child{
  padding:13px 16px!important;
}
.am-dashboard-luxury .am-luxury-section > div:last-child{
  padding:16px!important;
}
.am-dashboard-luxury .am-luxury-section table tbody td{
  padding-top:10px!important;
  padding-bottom:10px!important;
}
.am-dashboard-luxury .am-luxury-section .recharts-legend-wrapper{
  padding-left:10px!important;
}
.am-dashboard-luxury .am-luxury-section .recharts-default-legend{
  text-align:left!important;
}
.am-dashboard-luxury .am-luxury-section .recharts-legend-item{
  margin:8px 0!important;
  display:block!important;
}

/* Calendar — remove cheap stripe motif and give each metric a premium accent */
.am-calendar-luxury .am-luxury-cal-metric::after{
  display:none!important;
}
.am-calendar-luxury .am-luxury-cal-metric{
  min-height:104px!important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;
}
.am-calendar-luxury .am-luxury-cal-metric:hover{
  transform:translateY(-2px);
  border-color:rgba(89,68,218,.20)!important;
  box-shadow:var(--am-shadow-hover)!important;
}
.am-calendar-luxury .am-luxury-cal-metric > .flex > span:last-child{
  width:38px!important;
  height:38px!important;
  border-radius:12px!important;
  border:1px solid rgba(88,71,185,.10)!important;
  background:#f7f5ff!important;
  color:#6250d9!important;
}
.am-calendar-luxury .grid.gap-3.sm\\:grid-cols-2.xl\\:grid-cols-4 > .am-luxury-cal-metric:nth-child(2){
  background:linear-gradient(150deg,#fffdf8,#fff9eb)!important;
  border-color:#f3dfae!important;
}
.am-calendar-luxury .grid.gap-3.sm\\:grid-cols-2.xl\\:grid-cols-4 > .am-luxury-cal-metric:nth-child(2) > .flex > span:last-child{
  background:#fff2ce!important;color:#d98b00!important;border-color:#f4dd9e!important;
}
.am-calendar-luxury .grid.gap-3.sm\\:grid-cols-2.xl\\:grid-cols-4 > .am-luxury-cal-metric:nth-child(4) > .flex > span:last-child{
  background:#ebfbf4!important;color:#10a978!important;border-color:#cbefdf!important;
}
.am-calendar-luxury .am-luxury-filterbar{
  padding:11px 13px!important;
}
.am-calendar-luxury .am-luxury-filterbar button{
  min-height:30px!important;
  padding-inline:12px!important;
  font-weight:750!important;
}
.am-calendar-luxury .am-luxury-calendar-card [data-slot="card-header"]{
  padding:14px 18px!important;
}
.am-calendar-luxury .am-luxury-calendar-card [data-slot="card-title"]{
  font-weight:900!important;
  letter-spacing:-.025em!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8){
  min-height:102px!important;
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8) .space-y-0\\.5 > div:not(:last-child){
  min-height:20px;
  display:flex;
  align-items:center;
  border-radius:6px!important;
  border:1px solid rgba(59,130,246,.10);
  box-shadow:0 4px 10px -9px rgba(37,55,110,.32);
}
.am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8):hover{
  box-shadow:inset 0 0 0 1px rgba(98,80,217,.08);
}
.am-calendar-luxury .am-luxury-upcoming-card{
  min-height:230px;
}
.am-calendar-luxury .am-luxury-upcoming-card [data-slot="card-title"]{
  font-weight:850!important;
  letter-spacing:-.02em!important;
}

/* Better large-screen density */
@media (min-width:1450px){
  .am-dashboard-luxury{max-width:none!important}
  .am-dashboard-luxury .am-luxury-section table{font-size:12px!important}
  .am-calendar-luxury .am-luxury-calendar-card .grid-cols-7 > div:nth-child(n+8){min-height:110px!important}
}

/* TCRM_AM_PREMIUM_LUXURY_V2_POLISH:END */
'''
    CSS.write_text(css, encoding="utf-8")

print("PATCH=PASS")
print("DASHBOARD=PREMIUM_POLISH_V2")
print("CALENDAR=PREMIUM_POLISH_V2")
print("PORTFOLIO_LEGEND=RIGHT")
print("CALENDAR_STRIPES=REMOVED")
print("KPI_ICONS=FIXED")
print("BACKEND_CHANGED=NO")
print("FILES_CHANGED=2")
print(f"BACKUP={backup}")
print("ERROR=NONE")
