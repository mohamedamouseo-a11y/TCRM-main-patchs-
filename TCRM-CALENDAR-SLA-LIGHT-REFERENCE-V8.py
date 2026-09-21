#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
CAL = SRC / "pages/CalendarPage.tsx"
SLA = SRC / "pages/TaskSlaDashboard.tsx"
CSS = SRC / "calendar-sla-light-reference-v8.css"
MARKER = "TCRM_CALENDAR_SLA_LIGHT_REFERENCE_V8"
IMPORT = 'import "../calendar-sla-light-reference-v8.css";'

for p in (CAL, SLA):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"calendar-sla-light-reference-v8-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (CAL, SLA):
    shutil.copy2(p, backup / p.name)
if CSS.exists():
    shutil.copy2(CSS, backup / CSS.name)

def add_import(path: Path):
    text = path.read_text(encoding="utf-8")
    if MARKER not in text:
        lines = text.splitlines()
        lines.insert(1 if lines else 0, f"// {MARKER}")
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if IMPORT not in text:
        anchor = 'import "../sales-3-screens-light-reference-v7.css";'
        if anchor in text:
            text = text.replace(anchor, anchor + "\n" + IMPORT, 1)
        else:
            lines = text.splitlines()
            pos = 0
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    pos = i + 1
            lines.insert(pos, IMPORT)
            text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")

for p in (CAL, SLA):
    add_import(p)

# Calendar title exists in source; add a V8 hook instead of rebuilding the hero.
cal = CAL.read_text(encoding="utf-8")
if "tcrm-v8-calendar-title" not in cal:
    old = 'className="tcrm-v7-calendar-title flex items-center gap-3"'
    new = 'className="tcrm-v7-calendar-title tcrm-v8-calendar-title flex items-center gap-3"'
    if old not in cal:
        raise SystemExit("ERROR=CALENDAR_TITLE_HOOK_NOT_FOUND")
    cal = cal.replace(old, new, 1)
    CAL.write_text(cal, encoding="utf-8")

CSS_TEXT = r'''/* TCRM V8 — Calendar + SLA targeted Light reference fix
   Reviewed against current CalendarPage.tsx / TaskSlaDashboard.tsx and V3-V7 CSS.
   No fake data or new business controls. Light mode only. */

/* ================= CALENDAR ================= */

/* Hard-position the EXISTING real title block.
   V7 confirmed the markup exists but runtime visual still hid it. */
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero{
  position:relative!important;
  display:flex!important;
  align-items:center!important;
  min-height:92px!important;
  padding:16px 18px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  position:absolute!important;
  z-index:50!important;
  inset-inline-start:18px!important;
  top:50%!important;
  transform:translateY(-50%)!important;
  align-items:center!important;
  gap:12px!important;
  width:auto!important;
  min-width:260px!important;
  max-width:55%!important;
  height:auto!important;
  overflow:visible!important;
  clip:auto!important;
  clip-path:none!important;
  filter:none!important;
  pointer-events:auto!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title > div:first-child{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  position:relative!important;
  z-index:51!important;
  width:44px!important;
  height:44px!important;
  min-width:44px!important;
  min-height:44px!important;
  padding:0!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:13px!important;
  background:linear-gradient(135deg,#755ff4,#5f49e8)!important;
  box-shadow:0 14px 28px -17px rgba(88,63,215,.70)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title > div:last-child{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  position:relative!important;
  z-index:51!important;
  width:auto!important;
  height:auto!important;
  overflow:visible!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title h1{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  margin:0!important;
  color:#17213c!important;
  font-size:20px!important;
  line-height:1.15!important;
  font-weight:850!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title p{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  margin-top:4px!important;
  color:#74809a!important;
  font-size:11.5px!important;
  line-height:1.3!important;
  font-weight:600!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero > button{
  position:relative!important;
  z-index:52!important;
  margin-inline-start:auto!important;
  min-height:42px!important;
  padding-inline:18px!important;
  border-radius:12px!important;
}

/* Reference uses a full-height right rail, not a floating short card. */
html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
  display:grid!important;
  grid-template-columns:minmax(0,4.25fr) minmax(250px,.75fr)!important;
  gap:12px!important;
  align-items:stretch!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main{
  min-width:0!important;
  height:100%!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
  position:static!important;
  align-self:stretch!important;
  height:100%!important;
  min-height:100%!important;
  display:flex!important;
  flex-direction:column!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:first-child{
  flex:0 0 auto!important;
  min-height:52px!important;
  padding:11px 13px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming > div:last-child{
  flex:1 1 auto!important;
  min-height:0!important;
  max-height:none!important;
  overflow-y:auto!important;
  padding:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming .text-center.py-10{
  min-height:250px!important;
  padding:0 10px!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main > div:first-child{
  min-height:54px!important;
  padding:10px 14px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.border-b{
  min-height:46px!important;
  align-items:center!important;
}

html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-main .grid.grid-cols-7.divide-x.divide-y > div{
  min-height:94px!important;
  padding:7px!important;
}

/* ================= TASKS & SLA ================= */

html:not(.dark) .tcrm-sales-leads-v3-sla{
  padding:18px 20px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v3-page-banner-shell > div{
  min-height:86px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-kpis{
  gap:10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v3-kpi-card{
  min-height:86px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-health{
  min-height:44px!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-health-item{
  padding:9px 14px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends,
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-distribution{
  gap:12px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-trends .recharts-responsive-container{
  height:205px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-distribution .recharts-responsive-container{
  height:180px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla [data-slot="card-header"]{
  min-height:44px!important;
  padding:10px 13px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla [data-slot="card-content"]{
  padding:12px 13px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-agent-performance [data-slot="card-content"],
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-activity-table [data-slot="card-content"],
html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches [data-slot="card-content"]{
  padding:0!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla table thead tr{
  background:linear-gradient(180deg,#f4f5ff,#edf0fc)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla table th{
  padding:7px 10px!important;
  color:#65718a!important;
  font-size:9.5px!important;
  font-weight:850!important;
  letter-spacing:.015em!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla table td{
  padding:7px 10px!important;
  font-size:10px!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches{
  border:1px solid rgba(239,77,98,.22)!important;
  border-top:3px solid #ef4d62!important;
  box-shadow:0 16px 38px -31px rgba(208,48,73,.34)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches [data-slot="card-header"]{
  background:linear-gradient(180deg,#fff7f8,#fff)!important;
}

html:not(.dark) .tcrm-sales-leads-v3-sla .tcrm-v21-sla-breaches tbody tr:hover{
  background:#fff7f8!important;
}

@media (max-width:1365px){
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-layout{
    grid-template-columns:1fr!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v21-calendar-upcoming{
    height:auto!important;
    min-height:0!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title{
    max-width:60%!important;
  }
}

@media (max-width:760px){
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero{
    min-height:138px!important;
    align-items:flex-end!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v8-calendar-title{
    top:16px!important;
    transform:none!important;
    max-width:calc(100% - 36px)!important;
  }
  html:not(.dark) .tcrm-sales-leads-v3-calendar .tcrm-v3-calendar-hero > button{
    width:100%!important;
  }
}
'''

CSS.write_text(CSS_TEXT, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=CALENDAR_SLA_LIGHT_REFERENCE_V8")
print("CALENDAR_EXISTING_TITLE_HARD_FIXED=YES")
print("CALENDAR_UPCOMING_REFERENCE_RAIL=YES")
print("SLA_POLISH=YES")
print("SALES_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=3")
print(f"BACKUP={backup}")
