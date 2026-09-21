#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SRC = ROOT / "client/src"
CAL = SRC / "pages/CalendarPage.tsx"
CSS = SRC / "calendar-sla-reference-lock-v9.css"
MARKER = "TCRM_CALENDAR_REFERENCE_POLISH_V10"

for p in (CAL, CSS):
    if not p.exists():
        raise SystemExit(f"MISSING={p}")

backup = ROOT / ".patch-backups" / f"calendar-reference-polish-v10-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (CAL, CSS):
    shutil.copy2(p, backup / p.name)

cal = CAL.read_text(encoding="utf-8")
if MARKER not in cal:
    lines = cal.splitlines()
    lines.insert(1 if lines else 0, f"// {MARKER}")
    cal = "\n".join(lines) + "\n"

# Add reference hero note using real/static UX copy only.
if "tcrm-v10-hero-note" not in cal:
    hero_anchor = '''          {hasPermission("meetings.create") && (
            <Button
              onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
              className="gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 shadow-md shadow-violet-200"
            >'''
    hero_insert = '''          <div className="tcrm-v10-hero-note" aria-hidden="true">
            <CalendarIcon size={28} />
            <div>
              <strong>{isRTL ? "ابقَ منظماً" : "Stay organized"}</strong>
              <span>{isRTL ? "حوّل المحادثات إلى فرص" : "Turn conversations into opportunities"}</span>
            </div>
          </div>
          {hasPermission("meetings.create") && (
            <Button
              onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
              className="gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 shadow-md shadow-violet-200"
            >'''
    if hero_anchor not in cal:
        raise SystemExit("ERROR=HERO_ANCHOR_NOT_FOUND")
    cal = cal.replace(hero_anchor, hero_insert, 1)

# Upgrade month toolbar with working Previous / Next / Today controls.
old_toolbar = '''            {/* Month navigation */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <button
                onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                className="rounded-xl p-2 hover:bg-slate-100 transition-colors"
              >
                {isRTL ? <ChevronRight size={18} className="text-slate-600" /> : <ChevronLeft size={18} className="text-slate-600" />}
              </button>
              <h2 className="text-base font-bold text-slate-800">
                {format(currentMonth, "MMMM yyyy", { locale: isRTL ? ar : undefined })}
              </h2>
              <button
                onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                className="rounded-xl p-2 hover:bg-slate-100 transition-colors"
              >
                {isRTL ? <ChevronLeft size={18} className="text-slate-600" /> : <ChevronRight size={18} className="text-slate-600" />}
              </button>
            </div>'''
new_toolbar = '''            {/* Month navigation */}
            <div className="tcrm-v10-calendar-toolbar flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="tcrm-v10-calendar-nav">
                <button
                  onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                  className="rounded-xl p-2 hover:bg-slate-100 transition-colors"
                  aria-label={isRTL ? "الشهر السابق" : "Previous month"}
                >
                  {isRTL ? <ChevronRight size={18} className="text-slate-600" /> : <ChevronLeft size={18} className="text-slate-600" />}
                </button>
                <button
                  onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                  className="rounded-xl p-2 hover:bg-slate-100 transition-colors"
                  aria-label={isRTL ? "الشهر التالي" : "Next month"}
                >
                  {isRTL ? <ChevronLeft size={18} className="text-slate-600" /> : <ChevronRight size={18} className="text-slate-600" />}
                </button>
                <button
                  onClick={() => setCurrentMonth(new Date())}
                  className="tcrm-v10-today-btn"
                >
                  {isRTL ? "اليوم" : "Today"}
                </button>
              </div>
              <h2 className="tcrm-v10-month-title text-base font-bold text-slate-800">
                <CalendarIcon size={17} />
                <span>{format(currentMonth, "MMMM yyyy", { locale: isRTL ? ar : undefined })}</span>
              </h2>
              <div className="tcrm-v10-toolbar-balance" aria-hidden="true" />
            </div>'''
if "tcrm-v10-calendar-toolbar" not in cal:
    if old_toolbar not in cal:
        raise SystemExit("ERROR=TOOLBAR_ANCHOR_NOT_FOUND")
    cal = cal.replace(old_toolbar, new_toolbar, 1)

# Upgrade empty state with useful copy + real New Meeting action + non-interactive productivity note.
old_empty = '''                <div className="text-center py-10">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                    <CalendarIcon size={22} className="text-slate-300" />
                  </div>
                  <p className="text-xs text-slate-400 font-medium">{isRTL ? "لا توجد اجتماعات قادمة" : "No upcoming meetings"}</p>
                  {hasPermission("meetings.create") && (
                    <button
                      onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
                      className="mt-2 text-xs text-violet-500 hover:text-violet-700 font-medium"
                    >
                      {isRTL ? "+ إنشاء اجتماع" : "+ Create meeting"}
                    </button>
                  )}
                </div>'''
new_empty = '''                <div className="tcrm-v10-upcoming-empty text-center py-10">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                    <CalendarIcon size={22} className="text-slate-300" />
                  </div>
                  <p className="tcrm-v10-empty-title">{isRTL ? "لا توجد اجتماعات قادمة" : "No upcoming meetings"}</p>
                  <p className="tcrm-v10-empty-subtitle">{isRTL ? "ستظهر اجتماعاتك القادمة هنا" : "Your upcoming meetings will appear here"}</p>
                  {hasPermission("meetings.create") && (
                    <button
                      onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
                      className="tcrm-v10-create-meeting-btn"
                    >
                      <Plus size={13} />
                      {isRTL ? "إنشاء اجتماع" : "Create meeting"}
                    </button>
                  )}
                  <div className="tcrm-v10-quick-action">
                    <span>{isRTL ? "إجراء سريع" : "Quick Action"}</span>
                    {hasPermission("meetings.create") && (
                      <button onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}>
                        <span className="tcrm-v10-quick-icon"><Plus size={15} /></span>
                        <span>
                          <strong>{isRTL ? "اجتماع جديد" : "New Meeting"}</strong>
                          <small>{isRTL ? "جدولة اجتماع جديد" : "Schedule a new meeting"}</small>
                        </span>
                        <ChevronRight size={14} className={isRTL ? "rotate-180" : ""} />
                      </button>
                    )}
                  </div>
                  <div className="tcrm-v10-productivity-note">
                    <span>💡</span>
                    <div>
                      <strong>{isRTL ? "حافظ على إنتاجيتك" : "Stay Productive"}</strong>
                      <small>{isRTL ? "حافظ على تقويمك محدثاً حتى لا تفوت أي فرصة." : "Keep your calendar updated so you never miss an opportunity."}</small>
                    </div>
                  </div>
                </div>'''
if "tcrm-v10-upcoming-empty" not in cal:
    if old_empty not in cal:
        raise SystemExit("ERROR=UPCOMING_EMPTY_ANCHOR_NOT_FOUND")
    cal = cal.replace(old_empty, new_empty, 1)

CAL.write_text(cal, encoding="utf-8")

css = CSS.read_text(encoding="utf-8")
if f"/* {MARKER} */" not in css:
    css += r'''

/* TCRM_CALENDAR_REFERENCE_POLISH_V10 */

/* Hero: closer to approved reference without adding fake controls. */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-hero::after{
  content:"";
  position:absolute;
  width:116px;
  height:116px;
  inset-inline-end:340px;
  top:-34px;
  border:1px solid rgba(116,94,240,.08);
  border-radius:28px;
  transform:rotate(12deg);
  background:linear-gradient(145deg,rgba(125,102,245,.055),rgba(255,255,255,.15));
  pointer-events:none;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note{
  position:relative!important;
  z-index:2!important;
  margin-inline-start:auto!important;
  margin-inline-end:22px!important;
  display:flex!important;
  align-items:center!important;
  gap:10px!important;
  color:#6f5ce8!important;
  opacity:.96!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note > svg{
  color:#8d7af6!important;
  opacity:.24!important;
  width:42px!important;
  height:42px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note div{
  display:flex!important;
  flex-direction:column!important;
  gap:2px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note strong{
  color:#6854ee!important;
  font-size:11.5px!important;
  font-weight:800!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note span{
  color:#7c86a0!important;
  font-size:10px!important;
  font-weight:600!important;
}

/* KPI icon tiles: match approved reference card hierarchy. */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi-icon{
  border:1px solid transparent!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(1) .tcrm-v21-calendar-kpi-icon{
  color:#684ff0!important;
  background:linear-gradient(145deg,#f0edff,#e8e4ff)!important;
  border-color:#ded7ff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(2) .tcrm-v21-calendar-kpi-icon{
  color:#4188f5!important;
  background:linear-gradient(145deg,#edf5ff,#e2efff)!important;
  border-color:#d8e9ff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(3) .tcrm-v21-calendar-kpi-icon{
  color:#14a968!important;
  background:linear-gradient(145deg,#eafbf3,#dcf8ea)!important;
  border-color:#cff2df!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-kpi:nth-child(4) .tcrm-v21-calendar-kpi-icon{
  color:#ed9808!important;
  background:linear-gradient(145deg,#fff7e8,#fff0d3)!important;
  border-color:#ffe7bc!important;
}

/* Calendar command toolbar. */
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar{
  display:grid!important;
  grid-template-columns:1fr auto 1fr!important;
  align-items:center!important;
  gap:12px!important;
  min-height:58px!important;
  padding:9px 12px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav{
  display:flex!important;
  align-items:center!important;
  gap:6px!important;
  justify-self:start!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav > button{
  min-width:34px!important;
  min-height:34px!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  border:1px solid rgba(101,84,232,.12)!important;
  border-radius:9px!important;
  background:#fff!important;
  color:#5f687e!important;
  box-shadow:0 7px 18px -15px rgba(61,55,137,.34)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav > button:hover{
  background:#f6f4ff!important;
  border-color:rgba(101,84,232,.22)!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav .tcrm-v10-today-btn{
  width:auto!important;
  padding:0 13px!important;
  color:#6754e8!important;
  font-size:10.5px!important;
  font-weight:750!important;
  background:#f7f5ff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-month-title{
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:8px!important;
  margin:0!important;
  color:var(--v9-ink)!important;
  font-size:16px!important;
  font-weight:850!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-month-title svg{
  color:#6651eb!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-toolbar-balance{
  min-width:130px!important;
}

/* Upcoming reference treatment. */
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child{
  min-height:58px!important;
  padding:13px 14px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v21-calendar-upcoming > div:first-child > div:first-child{
  width:30px!important;
  height:30px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  padding:0!important;
  border-radius:9px!important;
  background:#f3efff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-upcoming-empty{
  min-height:100%!important;
  height:100%!important;
  padding:26px 10px 14px!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:flex-start!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-upcoming-empty > .w-12.h-12{
  width:58px!important;
  height:58px!important;
  margin-bottom:12px!important;
  border-radius:16px!important;
  color:#6c55ed!important;
  background:linear-gradient(145deg,#f3efff,#eeeaff)!important;
  border:1px solid #e5ddff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-upcoming-empty > .w-12.h-12 svg{
  width:26px!important;
  height:26px!important;
  color:#715af0!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-empty-title{
  margin:0!important;
  color:#26314d!important;
  font-size:12px!important;
  font-weight:820!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-empty-subtitle{
  max-width:190px!important;
  margin:5px auto 0!important;
  color:#8691a9!important;
  font-size:9.5px!important;
  line-height:1.45!important;
  font-weight:600!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-create-meeting-btn{
  min-height:34px!important;
  margin-top:12px!important;
  padding:0 15px!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:6px!important;
  border:1px solid #8d76f4!important;
  border-radius:9px!important;
  background:#fff!important;
  color:#6751e8!important;
  font-size:10px!important;
  font-weight:780!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-create-meeting-btn:hover{
  background:#f8f6ff!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action{
  width:100%!important;
  margin-top:22px!important;
  padding-top:14px!important;
  border-top:1px solid rgba(102,113,158,.10)!important;
  text-align:start!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action > span{
  display:block!important;
  margin-bottom:8px!important;
  color:#27324e!important;
  font-size:9.5px!important;
  font-weight:820!important;
  text-transform:uppercase!important;
  letter-spacing:.04em!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action > button{
  width:100%!important;
  min-height:54px!important;
  display:grid!important;
  grid-template-columns:34px 1fr 16px!important;
  align-items:center!important;
  gap:9px!important;
  padding:8px!important;
  border:0!important;
  border-radius:11px!important;
  background:#fbfbff!important;
  color:#26314d!important;
  text-align:start!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action > button:hover{
  background:#f5f3ff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-icon{
  width:32px!important;
  height:32px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:9px!important;
  color:#6752e9!important;
  background:#eeeaff!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action button > span:nth-child(2){
  display:flex!important;
  flex-direction:column!important;
  min-width:0!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action strong{
  color:#2d3650!important;
  font-size:10px!important;
  font-weight:790!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-quick-action small{
  margin-top:2px!important;
  color:#8a94aa!important;
  font-size:8.5px!important;
  font-weight:600!important;
}

.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note{
  width:100%!important;
  margin-top:auto!important;
  padding:11px!important;
  display:flex!important;
  align-items:flex-start!important;
  gap:9px!important;
  border:1px solid rgba(116,94,240,.09)!important;
  border-radius:12px!important;
  background:linear-gradient(135deg,#fff8ee,#f3f0ff)!important;
  text-align:start!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note > span{
  font-size:16px!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note > div{
  display:flex!important;
  flex-direction:column!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note strong{
  color:#6652e8!important;
  font-size:9.5px!important;
  font-weight:800!important;
}
.tcrm-calendar-reference-lock-v9 .tcrm-v10-productivity-note small{
  margin-top:3px!important;
  color:#8892a8!important;
  font-size:8.5px!important;
  line-height:1.4!important;
  font-weight:600!important;
}

@media (max-width:1365px){
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-hero-note{display:none!important}
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-toolbar-balance{display:none!important}
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar{grid-template-columns:1fr auto!important}
}

@media (max-width:760px){
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-toolbar{
    grid-template-columns:1fr!important;
  }
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-calendar-nav,
  .tcrm-calendar-reference-lock-v9 .tcrm-v10-month-title{
    justify-self:center!important;
  }
}
'''
    CSS.write_text(css, encoding="utf-8")

print("PATCH=PASS")
print("VERSION=CALENDAR_REFERENCE_POLISH_V10")
print("CALENDAR_ONLY=YES")
print("REFERENCE_POLISH=YES")
print("TODAY_CONTROL=REAL")
print("FAKE_CONTROLS=NO")
print("SLA_UNCHANGED=YES")
print("SALES_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=2")
print(f"BACKUP={backup}")
