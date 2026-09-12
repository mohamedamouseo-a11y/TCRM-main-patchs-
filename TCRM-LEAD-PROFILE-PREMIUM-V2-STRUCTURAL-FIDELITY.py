#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_STRUCTURAL_FIDELITY_TEAM_DASHBOARD"
V1_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V1_TEAM_DASHBOARD_COMMAND_CENTER"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V1_MARKER,
    'import "../lead-profile-premium-v1.css";',
    'className="tcrm-lead-profile-premium-v1 min-h-screen p-4 md:p-6"',
    '<div className="lead-profile-grid grid gap-4">',
    '<TabsContent value="info">',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V1 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2.bak"
shutil.copy2(TSX, backup)

# -----------------------------------------------------------------------------
# 1) Import + marker + page scope. No query/mutation/permission/business logic edits.
# -----------------------------------------------------------------------------
import_anchor = 'import "../lead-profile-premium-v1.css";'
if 'import "../lead-profile-premium-v2.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V1_MARKER}", f"// {V1_MARKER}\n// {MARKER}", 1)

src = src.replace(
    'className="tcrm-lead-profile-premium-v1 min-h-screen p-4 md:p-6"',
    'className="tcrm-lead-profile-premium-v1 tcrm-lead-profile-premium-v2 min-h-screen p-4 md:p-6"',
    1,
)

# -----------------------------------------------------------------------------
# 2) Keep the existing hero actions/logic, but move score/SLA into the new signal row.
# -----------------------------------------------------------------------------
score_anchor = '<LeadScoreRing score={leadScore} t={t} />'
if score_anchor not in src:
    raise SystemExit("ERROR: LeadScoreRing anchor missing")
src = src.replace(score_anchor, '<div className="tcrm-lp-v2-legacy-score"><LeadScoreRing score={leadScore} t={t} /></div>', 1)

# -----------------------------------------------------------------------------
# 3) KPI / signal row matching the approved Lead Profile reference composition.
#    Uses ONLY data already available in LeadProfile; no new backend/API dependencies.
# -----------------------------------------------------------------------------
grid_anchor = '\n\n\n          <div className="lead-profile-grid grid gap-4">'
if grid_anchor not in src:
    raise SystemExit("ERROR: lead-profile-grid insertion anchor missing")

signal_row = r'''

          <section className="tcrm-lp-v2-signals" aria-label={isRTL ? "مؤشرات العميل" : "Lead signals"}>
            <div className="tcrm-lp-v2-signal-card tone-violet">
              <div className="tcrm-lp-v2-signal-icon"><Activity size={18} /></div>
              <div className="tcrm-lp-v2-signal-copy">
                <span>{isRTL ? "نقاط العميل" : "Lead Score"}</span>
                <strong>{leadScore}<small>/100</small></strong>
                <em>{leadScore >= 70 ? (isRTL ? "احتمالية تحويل مرتفعة" : "High conversion potential") : (isRTL ? "يحتاج متابعة" : "Needs follow-up")}</em>
              </div>
              <div className="tcrm-lp-v2-signal-micro">{leadScore}%</div>
            </div>

            <div className="tcrm-lp-v2-signal-card tone-green">
              <div className="tcrm-lp-v2-signal-icon"><Clock size={18} /></div>
              <div className="tcrm-lp-v2-signal-copy">
                <span>{isRTL ? "حالة SLA" : "SLA Status"}</span>
                <strong style={{color:slaStatus.color}}>{t(slaStatus.labelKey as any)}</strong>
                <em>{Math.round(slaProgressValue)}% · {slaElapsedHours}/{slaThresholdHours}h</em>
              </div>
              <div className="tcrm-lp-v2-progress"><i style={{width:`${Math.min(100, Math.max(0, slaProgressValue))}%`}} /></div>
            </div>

            <div className="tcrm-lp-v2-signal-card tone-blue">
              <div className="tcrm-lp-v2-signal-icon"><MessageSquare size={18} /></div>
              <div className="tcrm-lp-v2-signal-copy">
                <span>{isRTL ? "آخر تواصل" : "Last Contact"}</span>
                <strong>{lastActivityDate ? relativeTimeLabel(lastActivityDate, t, isRTL) : t("noContactYet" as any)}</strong>
                <em>{lastActivityDate ? format(lastActivityDate, "dd MMM yyyy, HH:mm") : "—"}</em>
              </div>
            </div>

            <div className="tcrm-lp-v2-signal-card tone-rose">
              <div className="tcrm-lp-v2-signal-icon"><CalendarClock size={18} /></div>
              <div className="tcrm-lp-v2-signal-copy">
                <span>{(lead as any).nextAction ? (isRTL ? "الإجراء التالي" : "Next Action") : (isRTL ? "المرحلة الحالية" : "Current Stage")}</span>
                <strong>{(lead as any).nextAction || lead.stage || "—"}</strong>
                <em>{isRTL ? "متابعة مسار البيع" : "Sales workflow"}</em>
              </div>
            </div>

            <div className="tcrm-lp-v2-signal-card tone-violet">
              <div className="tcrm-lp-v2-signal-icon"><Users size={18} /></div>
              <div className="tcrm-lp-v2-signal-copy">
                <span>{isRTL ? "مصدر العميل" : "Lead Source"}</span>
                <strong>{(lead as any).source || (lead as any).leadSource || lead.campaignName || "—"}</strong>
                <em>{lead.campaignName || (isRTL ? "بيانات المصدر" : "Source details")}</em>
              </div>
              <div className="tcrm-lp-v2-spark" aria-hidden="true"><i/><i/><i/><i/></div>
            </div>
          </section>'''

src = src.replace(grid_anchor, signal_row + grid_anchor, 1)

# -----------------------------------------------------------------------------
# 4) Turn the default Info tab into the approved Overview layout while preserving
#    the original editable Info form in a dedicated Details tab.
# -----------------------------------------------------------------------------
info_item = '{v:"info",      I:Users,         l:isRTL?"المعلومات":"Info"},'
if info_item not in src:
    raise SystemExit("ERROR: info tab item anchor missing")
src = src.replace(
    info_item,
    '{v:"info",      I:Users,         l:isRTL?"نظرة عامة":"Overview"},\n                      {v:"details",   I:FileText,      l:isRTL?"التفاصيل":"Details"},',
    1,
)

# Rename only the first legacy Info content to Details.
src = src.replace('<TabsContent value="info">', '<TabsContent value="details">', 1)

details_anchor = '                {/* ── Tab: Info ── */}\n                <TabsContent value="details">'
if details_anchor not in src:
    # tolerate the exact comment changing while keeping the structural anchor strict
    details_anchor = '                <TabsContent value="details">'
    if details_anchor not in src:
        raise SystemExit("ERROR: renamed Details TabsContent anchor missing")

# Build the visual Overview from existing lead/activity/note/deal data only.
overview = r'''                {/* ── Tab: Overview — V2 structural fidelity ── */}
                <TabsContent value="info" className="mt-0">
                  <div className="tcrm-lp-v2-overview-grid">
                    <div className="tcrm-lp-v2-overview-left">
                      <Card className="tcrm-lp-v2-card tcrm-lp-v2-contact-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><Users size={16}/><span>{isRTL ? "معلومات التواصل والعمل" : "Contact & Business Information"}</span></div>
                          {canEditLead && (
                            <Button variant="outline" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => { setActiveTab("details"); setEditMode(true); }}>
                              <Edit size={13}/>{isRTL ? "تعديل" : "Edit"}
                            </Button>
                          )}
                        </CardHeader>
                        <CardContent className="tcrm-lp-v2-info-list">
                          <InfoRow label={isRTL ? "الاسم" : "Full Name"} value={lead.name || "—"} />
                          <InfoRow label={isRTL ? "الهاتف" : "Phone"} value={lead.phone || "—"} />
                          <InfoRow label={isRTL ? "البريد" : "Email"} value={(lead as any).email || "—"} />
                          <InfoRow label={isRTL ? "الدولة" : "Country"} value={lead.country || "—"} />
                          <InfoRow label={isRTL ? "المدينة" : "City"} value={(lead as any).city || "—"} />
                          <InfoRow label={isRTL ? "الشركة" : "Company"} value={(lead as any).companyName || lead.businessProfile || "—"} />
                          <InfoRow label={isRTL ? "المسمى الوظيفي" : "Job Title"} value={(lead as any).jobTitle || "—"} />
                        </CardContent>
                      </Card>

                      <Card className="tcrm-lp-v2-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><FileText size={16}/><span>{isRTL ? "معلومات إضافية" : "Additional Information"}</span></div>
                        </CardHeader>
                        <CardContent className="tcrm-lp-v2-info-list">
                          <InfoRow label={isRTL ? "المصدر" : "Lead Source"} value={(lead as any).source || (lead as any).leadSource || "—"} />
                          <InfoRow label={isRTL ? "الحملة" : "Campaign"} value={lead.campaignName || "—"} />
                          <InfoRow label={isRTL ? "الجودة" : "Lead Quality"} value={lead.leadQuality || "—"} />
                          <InfoRow label={isRTL ? "الملاءمة" : "Fit Status"} value={(lead as any).fitStatus || "Pending"} />
                          <InfoRow label={isRTL ? "التصنيف" : "Classification"} value={isRTL ? classConfig.labelAr : classConfig.label} />
                          <InfoRow label={isRTL ? "تاريخ الإنشاء" : "Created"} value={format(new Date(lead.createdAt), "dd MMM yyyy, HH:mm")} />
                        </CardContent>
                      </Card>
                    </div>

                    <div className="tcrm-lp-v2-overview-center">
                      <Card className="tcrm-lp-v2-card tcrm-lp-v2-timeline-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><Activity size={16}/><span>{isRTL ? "الخط الزمني للنشاط" : "Activity Timeline"}</span></div>
                          <Button variant="ghost" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => setActiveTab("stages")}>{isRTL ? "عرض الكل" : "View All"}</Button>
                        </CardHeader>
                        <CardContent className="tcrm-lp-v2-timeline">
                          {feedItems.length ? feedItems.slice(0,5).map((item:any) => {
                            const TimelineIcon = item.kind === "activity" ? (activityIconMap[item.data?.type] || Activity) : FileText;
                            const title = item.kind === "activity" ? (item.data?.type || (isRTL ? "نشاط" : "Activity")) : (isRTL ? "ملاحظة مضافة" : "Note Added");
                            const body = item.kind === "activity" ? (item.data?.notes || item.data?.outcome || "") : (item.data?.content || "");
                            return (
                              <div key={item.id} className="tcrm-lp-v2-timeline-item">
                                <div className="tcrm-lp-v2-timeline-icon"><TimelineIcon size={15}/></div>
                                <div className="tcrm-lp-v2-timeline-copy">
                                  <strong>{title}</strong>
                                  {body && <p>{String(body)}</p>}
                                </div>
                                <time>{format(item.date, "dd MMM yyyy")}<small>{format(item.date, "HH:mm")}</small></time>
                              </div>
                            );
                          }) : (
                            <div className="tcrm-lp-v2-empty-inline"><Activity size={20}/><span>{isRTL ? "لا يوجد نشاط مسجل بعد" : "No activity recorded yet"}</span></div>
                          )}
                        </CardContent>
                      </Card>

                      <Card className="tcrm-lp-v2-card tcrm-lp-v2-notes-card">
                        <CardHeader className="tcrm-lp-v2-card-head">
                          <div className="tcrm-lp-v2-card-title"><MessageSquare size={16}/><span>{isRTL ? "الملاحظات والملاحظات الذكية" : "Notes & Smart Notes"}</span></div>
                          <Button variant="outline" size="sm" className="tcrm-lp-v2-mini-action" onClick={() => setActiveTab("stages")}><Plus size={13}/>{isRTL ? "إضافة" : "Add Note"}</Button>
                        </CardHeader>
                        <CardContent>
                          {internalNotes?.length ? (
                            <div className="tcrm-lp-v2-note-preview">
                              <div className="tcrm-lp-v2-note-avatar">{String((internalNotes as any[])[0]?.authorName || "N").slice(0,1).toUpperCase()}</div>
                              <div><strong>{(internalNotes as any[])[0]?.authorName || (isRTL ? "ملاحظة داخلية" : "Internal note")}</strong><p>{(internalNotes as any[])[0]?.content || "—"}</p></div>
                            </div>
                          ) : (
                            <div className="tcrm-lp-v2-empty-inline"><MessageSquare size={20}/><span>{isRTL ? "لا توجد ملاحظات بعد" : "No notes yet"}</span></div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </TabsContent>

'''

src = src.replace(details_anchor, overview + details_anchor, 1)

# Add a class to the left-side tabs host for deterministic CSS targeting.
left_anchor = '<div className="min-w-0">\n              <Tabs value={activeTab}'
if left_anchor not in src:
    raise SystemExit("ERROR: left tabs host anchor missing")
src = src.replace(left_anchor, '<div className="tcrm-lp-v2-main min-w-0">\n              <Tabs value={activeTab}', 1)

TSX.write_text(src, encoding="utf-8")

# -----------------------------------------------------------------------------
# 5) V2 theme. Palette is deliberately copied from the Team Dashboard premium
#    family: pearl light surfaces + #6366f1 / #3b82f6 / #8b5cf6 accents;
#    deep navy dark surfaces + luminous blue/indigo/violet edges.
# -----------------------------------------------------------------------------
css = r'''/*
TCRM Lead Profile Premium V2 — Structural Fidelity
PRIMARY VISUAL REFERENCE: approved Lead Profile concept
COLOR SYSTEM: Team Dashboard premium family
SCOPE: .tcrm-lead-profile-premium-v2 only
NO backend / API / permission / mutation / route changes.
*/

.tcrm-lead-profile-premium-v2{
  --lp2-bg:#f7f8ff;
  --lp2-surface:rgba(255,255,255,.94);
  --lp2-surface-soft:rgba(249,250,255,.90);
  --lp2-text:#172036;
  --lp2-muted:#667085;
  --lp2-border:rgba(102,109,214,.18);
  --lp2-border-strong:rgba(99,102,241,.28);
  --lp2-accent:#6366f1;
  --lp2-blue:#3b82f6;
  --lp2-violet:#8b5cf6;
  --lp2-cyan:#4f7cff;
  --lp2-green:#22c55e;
  --lp2-rose:#f43f5e;
  --lp2-shadow:0 24px 60px -42px rgba(72,78,170,.36),inset 0 1px 0 rgba(255,255,255,.92);
  background:
    radial-gradient(circle at 18% 0%,rgba(99,102,241,.10),transparent 28%),
    radial-gradient(circle at 76% 1%,rgba(59,130,246,.08),transparent 30%),
    linear-gradient(180deg,#fbfcff 0%,#f6f8ff 46%,#f8f9ff 100%)!important;
}

.dark .tcrm-lead-profile-premium-v2{
  --lp2-bg:#07152a;
  --lp2-surface:rgba(13,27,51,.96);
  --lp2-surface-soft:rgba(10,24,47,.92);
  --lp2-text:#f4f7ff;
  --lp2-muted:#aebbd3;
  --lp2-border:rgba(103,123,210,.30);
  --lp2-border-strong:rgba(118,135,255,.44);
  --lp2-accent:#8da2ff;
  --lp2-blue:#5f8dff;
  --lp2-violet:#9b6cff;
  --lp2-cyan:#55b8ff;
  --lp2-shadow:0 28px 64px -42px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.05);
  background:
    radial-gradient(circle at 12% 0%,rgba(58,101,255,.17),transparent 30%),
    radial-gradient(circle at 84% 4%,rgba(116,76,255,.18),transparent 32%),
    linear-gradient(180deg,#07152a 0%,#081a31 44%,#071426 100%)!important;
}

/* ===== HERO: same violet/blue language as Team Dashboard, reference-like structure ===== */
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero{
  position:relative!important;
  top:auto!important;
  z-index:5!important;
  border-radius:20px!important;
  min-height:156px;
  border:1px solid rgba(99,102,241,.22)!important;
  background:
    radial-gradient(ellipse at 18% 48%,rgba(89,70,255,.18),transparent 28%),
    radial-gradient(ellipse at 58% 30%,rgba(51,129,255,.13),transparent 31%),
    radial-gradient(ellipse at 88% 55%,rgba(139,63,255,.16),transparent 32%),
    linear-gradient(112deg,rgba(255,255,255,.97),rgba(246,248,255,.94) 52%,rgba(241,244,255,.92))!important;
  box-shadow:0 22px 58px -34px rgba(73,69,255,.28),inset 0 1px 0 rgba(255,255,255,.96)!important;
}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-hero{
  border-color:rgba(90,116,255,.52)!important;
  background:
    radial-gradient(ellipse at 18% 48%,rgba(89,70,255,.45),transparent 29%),
    radial-gradient(ellipse at 56% 38%,rgba(51,129,255,.34),transparent 31%),
    radial-gradient(ellipse at 88% 55%,rgba(139,63,255,.38),transparent 32%),
    linear-gradient(112deg,rgba(8,33,75,.98),rgba(13,44,91,.97) 50%,rgba(39,28,104,.98))!important;
  box-shadow:0 28px 70px -34px rgba(0,0,0,.96),0 0 34px -24px rgba(99,102,241,.78),inset 0 1px 0 rgba(255,255,255,.08)!important;
}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero>.h-1{display:none!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero:before{
  content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background-image:radial-gradient(circle,rgba(99,102,241,.18) 1px,transparent 1px);
  background-size:22px 22px;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 35%,#000 80%,transparent);
  mask-image:linear-gradient(90deg,transparent,#000 35%,#000 80%,transparent);
}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-hero:before{background-image:radial-gradient(circle,rgba(126,150,255,.22) 1px,transparent 1px);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero>.md\:p-4{padding:20px 22px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero h1{font-size:27px!important;font-weight:880!important;letter-spacing:-.045em!important;color:var(--lp2-text)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero .text-muted-foreground{color:var(--lp2-muted)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-legacy-score,
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero .tcrm-lp-sla{display:none!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-hero button{min-height:36px!important;border-radius:10px!important;}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-hero button{background:rgba(8,28,58,.68)!important;border-color:rgba(113,139,255,.34)!important;color:#edf4ff!important;}

/* ===== KPI / signal strip ===== */
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signals{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card{
  position:relative;min-height:112px;padding:14px 14px 13px;overflow:hidden;
  display:grid;grid-template-columns:42px minmax(0,1fr);align-items:start;gap:11px;
  border-radius:16px;border:1px solid var(--lp2-border);background:linear-gradient(145deg,var(--lp2-surface),var(--lp2-surface-soft));box-shadow:var(--lp2-shadow);
}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card:after{content:"";position:absolute;inset:auto 0 0;height:2px;opacity:.75;background:linear-gradient(90deg,transparent,var(--signal,#6366f1),transparent);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card.tone-violet{--signal:var(--lp2-violet)}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card.tone-green{--signal:var(--lp2-green)}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card.tone-blue{--signal:var(--lp2-blue)}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card.tone-rose{--signal:var(--lp2-rose)}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-icon{width:42px;height:42px;border-radius:13px;display:flex;align-items:center;justify-content:center;color:var(--signal,#6366f1);background:linear-gradient(145deg,color-mix(in srgb,var(--signal,#6366f1) 14%,transparent),color-mix(in srgb,var(--signal,#6366f1) 5%,transparent));border:1px solid color-mix(in srgb,var(--signal,#6366f1) 18%,transparent);box-shadow:0 9px 22px -16px var(--signal,#6366f1);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-copy{min-width:0;display:flex;flex-direction:column;gap:3px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-copy>span{font-size:9px;font-weight:760;color:var(--lp2-muted);text-transform:uppercase;letter-spacing:.04em;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-copy strong{font-size:17px;line-height:1.08;font-weight:880;color:var(--lp2-text);letter-spacing:-.025em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-copy strong small{font-size:9px;color:var(--lp2-muted);margin-inline-start:2px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-copy em{font-size:8px;font-style:normal;color:var(--lp2-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-micro{position:absolute;right:12px;bottom:10px;font-size:8px;font-weight:800;color:var(--signal);}
[dir="rtl"].tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-micro{right:auto;left:12px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-progress{position:absolute;left:14px;right:14px;bottom:9px;height:4px;border-radius:999px;background:rgba(148,163,184,.14);overflow:hidden;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-progress i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#36c98f,#4f8cff);box-shadow:0 0 10px rgba(79,140,255,.34);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark{position:absolute;right:12px;bottom:11px;height:26px;display:flex;align-items:flex-end;gap:3px;opacity:.72;}
[dir="rtl"].tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark{right:auto;left:12px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark i{display:block;width:4px;border-radius:5px;background:linear-gradient(180deg,var(--lp2-violet),rgba(99,102,241,.15));}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark i:nth-child(1){height:9px}.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark i:nth-child(2){height:15px}.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark i:nth-child(3){height:21px}.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-spark i:nth-child(4){height:26px}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signal-card{border-color:rgba(103,123,210,.32);box-shadow:0 26px 58px -36px rgba(0,0,0,.94),0 0 28px -24px var(--signal,#6366f1),inset 0 1px 0 rgba(255,255,255,.05);}

/* ===== Navigation strip ===== */
.tcrm-lead-profile-premium-v2 .tcrm-lp-tabs{border-radius:13px!important;padding:0!important;border:1px solid var(--lp2-border)!important;background:linear-gradient(145deg,var(--lp2-surface),var(--lp2-surface-soft))!important;box-shadow:var(--lp2-shadow)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-tabs>div{padding:5px 7px!important;gap:3px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-tabs button{min-height:31px!important;padding:0 12px!important;border-radius:9px!important;color:var(--lp2-muted)!important;font-size:9px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-tabs button[style*="background"]{background:linear-gradient(135deg,#6556ff,#4f72ff)!important;color:#fff!important;box-shadow:0 7px 18px rgba(83,89,255,.24)!important;}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-tabs button{color:#aebbd3!important;}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-tabs button:hover{color:#fff!important;background:rgba(99,102,241,.09)!important;}

/* ===== Three-zone command-center composition ===== */
.tcrm-lead-profile-premium-v2 .lead-profile-grid{grid-template-columns:minmax(0,1fr) 390px!important;gap:12px!important;align-items:start!important;}
[dir="rtl"].tcrm-lead-profile-premium-v2 .lead-profile-grid{grid-template-columns:390px minmax(0,1fr)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-grid{display:grid;grid-template-columns:minmax(300px,.78fr) minmax(430px,1.22fr);gap:12px;align-items:start;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-left,.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-center{display:flex;flex-direction:column;gap:12px;min-width:0;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-card,.tcrm-lead-profile-premium-v2 .tcrm-lp-rail [data-slot="card"]{border-radius:14px!important;border:1px solid var(--lp2-border)!important;background:linear-gradient(145deg,var(--lp2-surface),var(--lp2-surface-soft))!important;box-shadow:var(--lp2-shadow)!important;overflow:hidden;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-card-head{min-height:44px!important;padding:9px 12px!important;display:flex;align-items:center;justify-content:space-between;gap:10px;border-bottom:1px solid rgba(99,102,241,.08);background:linear-gradient(90deg,rgba(99,102,241,.035),rgba(59,130,246,.018));}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-card-head{background:linear-gradient(90deg,rgba(91,104,216,.12),rgba(41,74,140,.06));border-bottom-color:rgba(113,129,255,.14);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-card-title{display:flex;align-items:center;gap:8px;min-width:0;color:var(--lp2-text);font-size:11px;font-weight:820;letter-spacing:-.015em;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-card-title svg{color:var(--lp2-accent);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-mini-action{height:27px!important;min-height:27px!important;padding:0 9px!important;border-radius:8px!important;font-size:8px!important;gap:4px!important;color:var(--lp2-accent)!important;border-color:var(--lp2-border)!important;background:rgba(99,102,241,.045)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-info-list{padding:10px 12px 12px!important;display:flex;flex-direction:column;gap:0!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-info-list>div{min-height:31px!important;padding:5px 0!important;border-bottom:1px solid rgba(99,102,241,.07);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-info-list>div:last-child{border-bottom:0;}

/* Timeline */
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline{position:relative;padding:7px 12px 10px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline:before{content:"";position:absolute;top:18px;bottom:22px;left:31px;width:1px;background:linear-gradient(var(--lp2-accent),rgba(99,102,241,.08));}
[dir="rtl"].tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline:before{left:auto;right:31px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-item{position:relative;z-index:1;display:grid;grid-template-columns:38px minmax(0,1fr) auto;gap:10px;align-items:start;padding:9px 0;border-bottom:1px solid rgba(99,102,241,.07);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-item:last-child{border-bottom:0;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-icon{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--lp2-accent);background:var(--lp2-surface);border:1px solid var(--lp2-border-strong);box-shadow:0 6px 18px -12px rgba(79,70,229,.55);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-copy strong{display:block;font-size:9px;font-weight:800;color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-copy p{margin-top:2px;font-size:8px;line-height:1.35;color:var(--lp2-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-item time{text-align:end;font-size:7px;line-height:1.3;color:var(--lp2-muted);white-space:nowrap;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-timeline-item time small{display:block;font-size:7px;}

/* Notes preview */
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-notes-card [data-slot="card-content"]{padding:11px 12px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-note-preview{display:flex;gap:9px;align-items:flex-start;padding:8px;border:1px solid rgba(99,102,241,.10);border-radius:11px;background:rgba(99,102,241,.025);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-note-avatar{width:28px;height:28px;flex:0 0 28px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#805cff,#5a46df);color:#fff;font-size:9px;font-weight:850;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-note-preview strong{display:block;font-size:9px;color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-note-preview p{margin-top:3px;font-size:8px;line-height:1.4;color:var(--lp2-muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-empty-inline{min-height:76px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:6px;color:var(--lp2-muted);font-size:8px;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-empty-inline svg{color:var(--lp2-accent);}

/* ===== Existing right rail: compact like the approved concept ===== */
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail{display:flex!important;flex-direction:column;gap:10px!important;position:static!important;max-height:none!important;overflow:visible!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail [data-slot="card"]{border-radius:14px!important;margin:0!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail [data-slot="card-header"]{padding:11px 12px 6px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail [data-slot="card-content"]{padding:10px 12px 12px!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail [data-slot="card-title"]{font-size:10px!important;font-weight:820!important;color:var(--lp2-text)!important;}
.tcrm-lead-profile-premium-v2 .tcrm-lp-rail button{min-height:28px!important;border-radius:8px!important;font-size:8px!important;}

/* V1 section heads outside Overview are normalized to the Team Dashboard palette */
.tcrm-lead-profile-premium-v2 .tcrm-lp-section-head{background:linear-gradient(112deg,#4936b8,#2850b2 48%,#7543d7)!important;padding:11px 14px!important;}
.dark .tcrm-lead-profile-premium-v2 .tcrm-lp-section-head{background:linear-gradient(112deg,#162d62,#214a91 48%,#4f3ea7)!important;}

/* Existing controls / cards maintain functionality but share one visual system */
.tcrm-lead-profile-premium-v2 [data-slot="card"]{color:var(--lp2-text);}
.tcrm-lead-profile-premium-v2 [data-slot="card"]:hover{border-color:rgba(103,113,232,.30)!important;}
.dark .tcrm-lead-profile-premium-v2 [data-slot="card"]:hover{border-color:rgba(118,135,255,.42)!important;}
.dark .tcrm-lead-profile-premium-v2 input,
.dark .tcrm-lead-profile-premium-v2 textarea,
.dark .tcrm-lead-profile-premium-v2 [role="combobox"]{background:rgba(9,23,45,.78)!important;border-color:rgba(103,123,210,.30)!important;color:#f4f7ff!important;}
.tcrm-lead-profile-premium-v2 input,
.tcrm-lead-profile-premium-v2 textarea,
.tcrm-lead-profile-premium-v2 [role="combobox"]{border-radius:9px!important;}

@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signals{grid-template-columns:repeat(3,minmax(0,1fr));}
  .tcrm-lead-profile-premium-v2 .lead-profile-grid{grid-template-columns:minmax(0,1fr) 340px!important;}
  [dir="rtl"].tcrm-lead-profile-premium-v2 .lead-profile-grid{grid-template-columns:340px minmax(0,1fr)!important;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-grid{grid-template-columns:minmax(280px,.85fr) minmax(360px,1.15fr);}
}
@media (max-width:1180px){
  .tcrm-lead-profile-premium-v2 .lead-profile-grid,[dir="rtl"].tcrm-lead-profile-premium-v2 .lead-profile-grid{grid-template-columns:1fr!important;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-grid{grid-template-columns:1fr 1fr;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-rail{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2{padding:12px!important;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signals{grid-template-columns:1fr 1fr;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-v2-overview-grid{grid-template-columns:1fr;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-rail{display:flex!important;}
  .tcrm-lead-profile-premium-v2 .tcrm-lp-hero>.p-3,.tcrm-lead-profile-premium-v2 .tcrm-lp-hero>.md\:p-4{padding:15px!important;}
}
@media (max-width:560px){.tcrm-lead-profile-premium-v2 .tcrm-lp-v2-signals{grid-template-columns:1fr;}}
'''
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("LEAD_PROFILE_PREMIUM_V2=YES")
print("STRUCTURAL_FIDELITY=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM=YES")
print("OVERVIEW_TAB_REBUILT=YES")
print("DETAILS_TAB_PRESERVED=YES")
print("KPI_SIGNAL_ROW_ADDED=YES")
print("THREE_ZONE_COMMAND_CENTER=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx, client/src/lead-profile-premium-v2.css")