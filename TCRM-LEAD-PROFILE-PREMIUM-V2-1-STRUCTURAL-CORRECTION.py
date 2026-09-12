#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-1.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V2_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_STRUCTURAL_FIDELITY_TEAM_DASHBOARD"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_1_STRUCTURAL_CORRECTION"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V2_MARKER,
    'import "../lead-profile-premium-v2.css";',
    'tcrm-lead-profile-premium-v2 min-h-screen p-4 md:p-6',
    'className="tcrm-lp-v2-main min-w-0"',
    'className="tcrm-lp-v2-overview-grid"',
    'className="tcrm-lp-v2-card tcrm-lp-v2-notes-card"',
    'className="tcrm-lp-rail space-y-3',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_1=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-1.bak"
shutil.copy2(TSX, backup)

# 1) V2.1 import + marker.
import_anchor = 'import "../lead-profile-premium-v2.css";'
if 'import "../lead-profile-premium-v2-1.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-1.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V2_MARKER}", f"// {V2_MARKER}\n// {MARKER}", 1)

# 2) Overview-active scope. This lets V2.1 replace the legacy oversized rail ONLY
#    on Overview while preserving it on Details and every existing functional tab.
root_old = 'className="tcrm-lead-profile-premium-v1 tcrm-lead-profile-premium-v2 min-h-screen p-4 md:p-6"'
root_new = 'className={`tcrm-lead-profile-premium-v1 tcrm-lead-profile-premium-v2 tcrm-lead-profile-premium-v2-1 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen p-4 md:p-6`}'
if root_old not in src:
    raise SystemExit("ERROR: V2 root class anchor missing")
src = src.replace(root_old, root_new, 1)

# 3) Add a real identity anchor to the hero without inventing a portrait.
#    Initials are derived from the current lead name/phone only.
h1_anchor = '<h1 className="min-w-0 break-words text-xl font-bold text-foreground md:text-2xl">{lead.name ?? lead.phone}</h1>'
if h1_anchor not in src:
    raise SystemExit("ERROR: hero h1 anchor missing")
avatar = r'''<div className="tcrm-lp-v21-avatar" aria-hidden="true">
                              {String(lead.name ?? lead.phone ?? "?").trim().split(/\s+/).slice(0,2).map((part) => part[0] || "").join("").toUpperCase() || "?"}
                            </div>
                            <h1 className="min-w-0 break-words text-xl font-bold text-foreground md:text-2xl">{lead.name ?? lead.phone}</h1>'''
src = src.replace(h1_anchor, avatar, 1)

# 4) Build the third Overview column inside the V2 Overview itself.
#    The previous V2 used the legacy rail as the third zone. Under RTL it became
#    the huge primary column. V2.1 keeps the legacy rail for non-Overview tabs and
#    uses compact, data-backed executive cards here instead.
notes_marker = 'className="tcrm-lp-v2-card tcrm-lp-v2-notes-card"'
notes_pos = src.find(notes_marker)
if notes_pos == -1:
    raise SystemExit("ERROR: V2 notes card marker missing")

end_pattern = '                    </div>\n                  </div>\n                </TabsContent>'
end_pos = src.find(end_pattern, notes_pos)
if end_pos == -1:
    raise SystemExit("ERROR: V2 Overview closing anchor missing")

right_column = r'''

                    <div className="tcrm-lp-v21-overview-right">
                      <Card className="tcrm-lp-v2-card tcrm-lp-v21-deal-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><CreditCard size={16}/><span>{isRTL ? "الصفقة / الفرصة" : "Deal / Opportunity"}</span></div>
                          {canCreateDeal && !deal && (
                            <Button variant="outline" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => setShowDeal(true)}><Plus size={13}/>{isRTL ? "إنشاء" : "Create"}</Button>
                          )}
                        </CardHeader>
                        <CardContent className="tcrm-lp-v21-compact-body">
                          {canViewDeal && deal ? (
                            <>
                              <div className="tcrm-lp-v21-deal-value">
                                <span>{isRTL ? "قيمة الصفقة" : "Deal Value"}</span>
                                <strong>{deal.valueSar ? `${Number(deal.valueSar).toLocaleString()} ${(deal as any).currency || "SAR"}` : "—"}</strong>
                                <em className={`status-${String(deal.status || "Pending").toLowerCase()}`}>{t(deal.status as any)}</em>
                              </div>
                              <div className="tcrm-lp-v21-two-metrics">
                                <div><span>{isRTL ? "المدفوع" : "Paid"}</span><strong>{Number((deal as any).paidAmount || 0).toLocaleString()}</strong></div>
                                <div><span>{isRTL ? "المتبقي" : "Remaining"}</span><strong>{Number((deal as any).remainingAmount || 0).toLocaleString()}</strong></div>
                              </div>
                            </>
                          ) : (
                            <div className="tcrm-lp-v21-compact-empty">
                              <CreditCard size={22}/><strong>{isRTL ? "لا توجد صفقة نشطة" : "No active deal yet"}</strong>
                              <p>{isRTL ? "حوّل العميل إلى صفقة عند الجاهزية." : "Convert this lead when the opportunity is ready."}</p>
                              {canCreateDeal && <Button size="sm" onClick={() => setShowDeal(true)}><Plus size={13}/>{isRTL ? "تحويل إلى صفقة" : "Convert to Deal"}</Button>}
                            </div>
                          )}
                        </CardContent>
                      </Card>

                      <Card className="tcrm-lp-v2-card tcrm-lp-v21-owner-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><Users size={16}/><span>{isRTL ? "الملكية والتعيين" : "Ownership & Assignment"}</span></div>
                          {canAssignLead && <Button variant="outline" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => openAssignDialog("collaborator")}><Edit size={13}/>{isRTL ? "تعديل" : "Edit"}</Button>}
                        </CardHeader>
                        <CardContent className="tcrm-lp-v21-owner-body">
                          <div className="tcrm-lp-v21-owner-main">
                            <div className="tcrm-lp-v21-owner-avatar">{String((lead as any).ownerName || "U").trim().slice(0,1).toUpperCase()}</div>
                            <div><span>{isRTL ? "مسند إلى" : "Assigned To"}</span><strong>{(lead as any).ownerName ?? (!lead.ownerId ? t("ownerUnassigned" as any) : "—")}</strong></div>
                          </div>
                          <div className="tcrm-lp-v21-owner-grid">
                            <div><span>{isRTL ? "المتعاونون" : "Collaborators"}</span><strong>{(leadAssignments as any[])?.length || 0}</strong></div>
                            <div><span>{isRTL ? "تاريخ الإنشاء" : "Created"}</span><strong>{format(new Date(lead.createdAt), "dd MMM yyyy")}</strong></div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card className="tcrm-lp-v2-card tcrm-lp-v21-tasks-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><CalendarClock size={16}/><span>{isRTL ? "المهام والمتابعات" : "Upcoming Tasks & Follow-ups"}</span></div>
                          <Button variant="outline" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => setActiveTab("reminders")}><Plus size={13}/>{isRTL ? "عرض" : "View"}</Button>
                        </CardHeader>
                        <CardContent className="tcrm-lp-v21-task-body">
                          <div className="tcrm-lp-v21-task-row">
                            <span className="tcrm-lp-v21-task-check" />
                            <div><strong>{(lead as any).nextAction || lead.stage || (isRTL ? "متابعة العميل" : "Lead follow-up")}</strong><p>{isRTL ? "الإجراء الحالي في مسار البيع" : "Current sales workflow action"}</p></div>
                            <em>{lead.leadQuality || "—"}</em>
                          </div>
                          <div className="tcrm-lp-v21-task-row secondary">
                            <span className="tcrm-lp-v21-task-check" />
                            <div><strong>{isRTL ? "مراجعة آخر تواصل" : "Review last contact"}</strong><p>{lastActivityDate ? format(lastActivityDate, "dd MMM yyyy, HH:mm") : (isRTL ? "لا يوجد تواصل مسجل" : "No contact recorded")}</p></div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>'''

insert_at = end_pos + len('                    </div>')
src = src[:insert_at] + right_column + src[insert_at:]

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.1 — Structural Correction
REFERENCE: approved Lead Profile concept
COLOR SYSTEM: Team Dashboard Premium — unchanged from V2
GOAL: correct physical column order, hierarchy, density and Overview composition.
*/

/* Keep the approved Team Dashboard palette. V2.1 changes structure, not identity. */
.tcrm-lead-profile-premium-v2-1{
  --v21-gap:12px;
  --v21-rail:330px;
}

/* ===== HERO: stronger identity, less dead air ===== */
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-hero{
  min-height:138px!important;
  border-radius:18px!important;
}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-hero>.md\:p-4{padding:15px 18px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-hero h1{font-size:25px!important;line-height:1.05!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-avatar{
  width:58px;height:58px;flex:0 0 58px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;
  color:#fff;font-size:17px;font-weight:900;letter-spacing:-.03em;
  background:linear-gradient(145deg,#4f7cff,#6556ff 52%,#8b5cf6);
  border:3px solid rgba(255,255,255,.82);
  box-shadow:0 10px 28px -16px rgba(79,70,229,.62),0 0 0 1px rgba(99,102,241,.22);
}
.dark .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-avatar{
  border-color:rgba(167,184,255,.28);box-shadow:0 0 0 1px rgba(122,145,255,.48),0 0 28px -10px rgba(91,104,255,.68);
}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-hero button{min-height:32px!important;font-size:10px!important;}

/* ===== KPI strip: same Team Dashboard colors, reference-like presence ===== */
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signals{gap:10px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signal-card{
  min-height:120px!important;padding:15px 15px 13px!important;grid-template-columns:44px minmax(0,1fr)!important;gap:12px!important;
  border-radius:15px!important;
}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signal-icon{width:44px!important;height:44px!important;border-radius:14px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signal-copy>span{font-size:9px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signal-copy strong{font-size:19px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signal-copy em{font-size:8.5px!important;}

/* ===== Navigation: one strong horizontal command strip ===== */
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-tabs{margin-bottom:10px!important;border-radius:12px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-tabs>div{padding:6px 8px!important;gap:5px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-tabs button{min-height:34px!important;padding:0 13px!important;font-size:9.5px!important;}

/* ===== Critical V2 bug fix: RTL was making the legacy rail the huge primary column. ===== */
.tcrm-lead-profile-premium-v2-1 .lead-profile-grid{
  direction:ltr!important;
  grid-template-columns:minmax(0,1fr) var(--v21-rail)!important;
  gap:var(--v21-gap)!important;
  align-items:start!important;
}
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .lead-profile-grid>.tcrm-lp-v2-main,
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .lead-profile-grid>.tcrm-lp-rail{direction:rtl;}
.tcrm-lead-profile-premium-v2-1[dir="ltr"] .lead-profile-grid>.tcrm-lp-v2-main,
.tcrm-lead-profile-premium-v2-1[dir="ltr"] .lead-profile-grid>.tcrm-lp-rail{direction:ltr;}

/* On Overview, use the rebuilt reference-like 3-zone layout and remove the duplicate legacy rail. */
.tcrm-lead-profile-premium-v2-1.tcrm-lp-v21-overview-active .lead-profile-grid{grid-template-columns:minmax(0,1fr)!important;}
.tcrm-lead-profile-premium-v2-1.tcrm-lp-v21-overview-active .tcrm-lp-rail{display:none!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-main{min-width:0!important;}

.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-grid{
  direction:ltr!important;
  display:grid!important;
  grid-template-columns:minmax(290px,.92fr) minmax(440px,1.36fr) minmax(285px,.88fr)!important;
  gap:12px!important;
  align-items:start!important;
}
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .tcrm-lp-v21-overview-right{direction:rtl;}
.tcrm-lead-profile-premium-v2-1[dir="ltr"] .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-1[dir="ltr"] .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-1[dir="ltr"] .tcrm-lp-v21-overview-right{direction:ltr;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-overview-right{display:flex;flex-direction:column;gap:10px;min-width:0;}

/* Better proportions: Contact / Timeline / right executive rail. */
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-card{border-radius:13px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-card-head{min-height:43px!important;padding:8px 11px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-card-title{font-size:10.5px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-info-list{padding:8px 11px 10px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-info-list>div{min-height:29px!important;padding:4px 0!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-timeline{padding:5px 11px 8px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-timeline-item{padding:8px 0!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-timeline-card{min-height:350px;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-notes-card{min-height:150px;}

/* ===== New compact right Overview rail ===== */
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-overview-right .tcrm-lp-v2-card{box-shadow:var(--lp2-shadow)!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-body,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-body,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-body{padding:11px!important;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-empty{min-height:112px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:5px;color:var(--lp2-muted);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-empty svg{color:var(--lp2-accent);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-empty strong{font-size:10px;color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-empty p{max-width:220px;font-size:8px;line-height:1.35;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-compact-empty button{height:28px!important;min-height:28px!important;margin-top:3px;font-size:8px!important;border-radius:8px!important;background:linear-gradient(135deg,#6556ff,#4f72ff)!important;color:white!important;}

.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value{position:relative;padding:8px 9px;border-radius:10px;border:1px solid var(--lp2-border);background:rgba(99,102,241,.035);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value>span{display:block;font-size:7.5px;color:var(--lp2-muted);text-transform:uppercase;letter-spacing:.04em;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value>strong{display:block;margin-top:2px;font-size:18px;color:var(--lp2-text);letter-spacing:-.03em;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value>em{position:absolute;top:9px;right:9px;padding:2px 6px;border-radius:999px;font-size:7px;font-style:normal;font-weight:800;background:rgba(245,158,11,.12);color:#d97706;}
.tcrm-lead-profile-premium-v2-1[dir="rtl"] .tcrm-lp-v21-deal-value>em{right:auto;left:9px;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value>em.status-won{background:rgba(34,197,94,.12);color:#16a34a;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value>em.status-lost{background:rgba(239,68,68,.12);color:#dc2626;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-two-metrics{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:7px;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-two-metrics>div{padding:7px 8px;border-radius:9px;border:1px solid var(--lp2-border);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-two-metrics span{display:block;font-size:7px;color:var(--lp2-muted);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-two-metrics strong{display:block;margin-top:2px;font-size:10px;color:var(--lp2-text);}

.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-main{display:flex;align-items:center;gap:9px;padding-bottom:9px;border-bottom:1px solid rgba(99,102,241,.08);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-avatar{width:34px;height:34px;flex:0 0 34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;background:linear-gradient(145deg,#805cff,#4f7cff);font-size:10px;font-weight:900;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-main span,
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-grid span{display:block;font-size:7px;color:var(--lp2-muted);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-main strong{display:block;margin-top:2px;font-size:10px;color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-owner-grid strong{display:block;margin-top:2px;font-size:8px;color:var(--lp2-text);}

.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-body{display:flex;flex-direction:column;gap:2px;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row{display:grid;grid-template-columns:18px minmax(0,1fr) auto;gap:7px;align-items:start;padding:8px 0;border-bottom:1px solid rgba(99,102,241,.08);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row:last-child{border-bottom:0;}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row.secondary{grid-template-columns:18px minmax(0,1fr);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-check{width:14px;height:14px;margin-top:1px;border-radius:4px;border:1px solid var(--lp2-border-strong);background:rgba(99,102,241,.03);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row strong{display:block;font-size:8.5px;color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row p{margin-top:2px;font-size:7px;color:var(--lp2-muted);}
.tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-row em{font-size:7px;font-style:normal;padding:2px 5px;border-radius:999px;background:rgba(244,63,94,.10);color:#e11d48;}

/* Dark keeps Team Dashboard deep navy, just adds clearer layering. */
.dark .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-deal-value,
.dark .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-two-metrics>div{background:rgba(85,105,190,.07);border-color:rgba(103,123,210,.26);}
.dark .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-task-check{background:rgba(86,105,194,.10);}

/* Responsive correction. */
@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-1{--v21-rail:300px;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-grid{grid-template-columns:minmax(260px,.9fr) minmax(380px,1.28fr) minmax(260px,.82fr)!important;}
}
@media (max-width:1220px){
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-grid{grid-template-columns:1fr 1.2fr!important;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-overview-right{grid-column:1/-1;display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));}
  .tcrm-lead-profile-premium-v2-1 .lead-profile-grid{grid-template-columns:1fr!important;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-rail{position:static!important;max-height:none!important;}
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signals{grid-template-columns:1fr 1fr!important;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-overview-grid{grid-template-columns:1fr!important;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-overview-right{grid-column:auto;display:flex!important;}
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v21-avatar{width:44px;height:44px;flex-basis:44px;font-size:13px;}
}
@media (max-width:560px){
  .tcrm-lead-profile-premium-v2-1 .tcrm-lp-v2-signals{grid-template-columns:1fr!important;}
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_1=YES")
print("STRUCTURAL_CORRECTION=YES")
print("RTL_COLUMN_ORDER_FIXED=YES")
print("OVERVIEW_THREE_ZONE_FIXED=YES")
print("LEGACY_RAIL_PRESERVED_OUTSIDE_OVERVIEW=YES")
print("HERO_IDENTITY_ANCHOR_ADDED=YES")
print("KPI_PROPORTIONS_CORRECTED=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-1.css")