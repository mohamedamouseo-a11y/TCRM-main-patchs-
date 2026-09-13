#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-6-details-formdata.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V25_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_5_REMAINING_TABS_LAYOUT_UNIFICATION"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_6_DETAILS_FORMDATA_REDESIGN"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V25_MARKER,
    'import "../lead-profile-premium-v2-5.css";',
    'tcrm-lead-profile-premium-v2-5',
    '<TabsContent value="details">',
    '<TabsContent value="formdata">',
    'className="tcrm-lp-v2-main min-w-0"',
    'className="tcrm-lp-rail space-y-3',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2.5 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_6=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-6-details-formdata.bak"
shutil.copy2(TSX, backup)

# -----------------------------------------------------------------------------
# 1) Layer V2.6 after the approved V2.5.
#    Scope is ONLY Details + Form Data. Overview and all other tabs are protected.
# -----------------------------------------------------------------------------
import_anchor = 'import "../lead-profile-premium-v2-5.css";'
if 'import "../lead-profile-premium-v2-6-details-formdata.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-6-details-formdata.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V25_MARKER}", f"// {V25_MARKER}\n// {MARKER}", 1)

root_old = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 tcrm-lead-profile-premium-v2-4 tcrm-lead-profile-premium-v2-5 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : "tcrm-lp-v25-secondary-tab-active"} min-h-screen'
root_new = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 tcrm-lead-profile-premium-v2-4 tcrm-lead-profile-premium-v2-5 tcrm-lead-profile-premium-v2-6 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : "tcrm-lp-v25-secondary-tab-active"} ${activeTab === "details" ? "tcrm-lp-v26-details-active" : activeTab === "formdata" ? "tcrm-lp-v26-formdata-active" : ""} min-h-screen'
if root_old not in src:
    raise SystemExit("ERROR: V2.5 root class anchor missing")
src = src.replace(root_old, root_new, 1)

# -----------------------------------------------------------------------------
# 2) Details tab semantic hooks.
#    No field is added, removed, renamed or populated with invented values.
# -----------------------------------------------------------------------------
details_anchor = '''<TabsContent value="details">\n              <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">'''
details_replacement = '''<TabsContent value="details" className="tcrm-lp-v26-details-tab mt-0">\n              <Card className="tcrm-lp-v26-details-card rounded-2xl border-border/40 shadow-sm overflow-hidden">'''
if details_anchor not in src:
    raise SystemExit("ERROR: Details tab anchor missing")
src = src.replace(details_anchor, details_replacement, 1)

basic_anchor = '''                      {/* Basic Info */}\n                      <div className="space-y-2.5">'''
basic_replacement = '''                      {/* Basic Info */}\n                      <div className="tcrm-lp-v26-details-section-head">\n                        <div className="tcrm-lp-v26-section-icon"><Users size={14} /></div>\n                        <div>\n                          <strong>{isRTL ? "البيانات الأساسية" : "Core Lead Information"}</strong>\n                          <span>{isRTL ? "هوية العميل والتواصل والملكية" : "Identity, contact, ownership and qualification"}</span>\n                        </div>\n                      </div>\n                      <div className="tcrm-lp-v26-details-grid">'''
if basic_anchor not in src:
    raise SystemExit("ERROR: Details basic info anchor missing")
src = src.replace(basic_anchor, basic_replacement, 1)

sales_anchor = '''                      {/* Sales Info */}\n                      <div className="space-y-2.5">'''
sales_replacement = '''                      {/* Sales Info */}\n                      <div className="tcrm-lp-v26-sales-section">'''
if sales_anchor not in src:
    raise SystemExit("ERROR: Details sales info anchor missing")
src = src.replace(sales_anchor, sales_replacement, 1)

# -----------------------------------------------------------------------------
# 3) Form Data semantic hooks.
#    Existing customFieldsData/sourceMetadata are preserved exactly.
# -----------------------------------------------------------------------------
form_anchor = '''<TabsContent value="formdata">\n                  <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">'''
form_replacement = '''<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">\n                  <Card className="tcrm-lp-v26-formdata-card rounded-2xl border-border/40 shadow-sm overflow-hidden">'''
if form_anchor not in src:
    raise SystemExit("ERROR: Form Data tab anchor missing")
src = src.replace(form_anchor, form_replacement, 1)

empty_old = '''                          <div className="flex flex-col items-center justify-center py-8 text-center">'''
empty_new = '''                          <div className="tcrm-lp-v26-form-empty flex flex-col items-center justify-center py-8 text-center">'''
# Replace only after the form-data tab begins.
form_pos = src.find('<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">')
if form_pos < 0:
    raise SystemExit("ERROR: Form Data patched tab not found")
form_tail = src[form_pos:]
if empty_old not in form_tail:
    raise SystemExit("ERROR: Form Data empty state anchor missing")
form_tail = form_tail.replace(empty_old, empty_new, 1)
src = src[:form_pos] + form_tail

form_body_old = '''                        return (\n                          <div className="space-y-3">'''
form_body_new = '''                        return (\n                          <div className="tcrm-lp-v26-formdata-body space-y-4">'''
form_pos = src.find('<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">')
form_tail = src[form_pos:]
if form_body_old not in form_tail:
    raise SystemExit("ERROR: Form Data body anchor missing")
form_tail = form_tail.replace(form_body_old, form_body_new, 1)
src = src[:form_pos] + form_tail

form_header_old = '''                            <div className="flex items-center gap-2 pb-1 border-b border-border/30">\n                              <div className="h-3 w-1 rounded-full" style={{background:"#f97316"}} />\n                              <p className="text-[10px] font-bold uppercase tracking-wider" style={{color:"#1e3a5f"}}>{isRTL ? "حقول النموذج" : "Form Fields"}</p>\n                            </div>'''
form_header_new = '''                            <div className="tcrm-lp-v26-form-fields-head">\n                              <div className="tcrm-lp-v26-section-icon"><FileText size={14} /></div>\n                              <div className="min-w-0 flex-1">\n                                <strong>{isRTL ? "حقول النموذج" : "Form Fields"}</strong>\n                                <span>{isRTL ? "إجابات العميل كما وصلت من المصدر" : "Lead answers exactly as received from the source"}</span>\n                              </div>\n                              <em>{Object.entries(customData).filter(([key]) => key !== "inbox_url").length}</em>\n                            </div>'''
form_pos = src.find('<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">')
form_tail = src[form_pos:]
if form_header_old not in form_tail:
    raise SystemExit("ERROR: Form Fields header anchor missing")
form_tail = form_tail.replace(form_header_old, form_header_new, 1)
src = src[:form_pos] + form_tail

map_old = '''                            {Object.entries(customData)\n                              .filter(([key]) => key !== "inbox_url")\n                              .map(([key, value]) => (\n                                <InfoRow key={key} label={cleanLabel(key)} value={String(value ?? "")} multiline />\n                              ))}'''
map_new = '''                            <div className="tcrm-lp-v26-form-fields">\n                              {Object.entries(customData)\n                                .filter(([key]) => key !== "inbox_url")\n                                .map(([key, value], index) => (\n                                  <div className="tcrm-lp-v26-form-field" key={key}>\n                                    <span className="tcrm-lp-v26-form-index">{String(index + 1).padStart(2, "0")}</span>\n                                    <div className="tcrm-lp-v26-form-field-content">\n                                      <InfoRow label={cleanLabel(key)} value={String(value ?? "")} multiline />\n                                    </div>\n                                  </div>\n                                ))}\n                            </div>'''
form_pos = src.find('<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">')
form_tail = src[form_pos:]
if map_old not in form_tail:
    raise SystemExit("ERROR: Form Data fields map anchor missing")
form_tail = form_tail.replace(map_old, map_new, 1)
src = src[:form_pos] + form_tail

source_old = '''                                <div className="rounded-lg border border-border/40 bg-muted/20 p-2.5 space-y-2">'''
source_new = '''                                <div className="tcrm-lp-v26-source-card rounded-xl border border-border/40 bg-muted/20 p-3 space-y-2">'''
form_pos = src.find('<TabsContent value="formdata" className="tcrm-lp-v26-formdata-tab mt-0">')
form_tail = src[form_pos:]
if source_old not in form_tail:
    raise SystemExit("ERROR: Form Data source card anchor missing")
form_tail = form_tail.replace(source_old, source_new, 1)
src = src[:form_pos] + form_tail

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.6 — Details + Form Data Redesign
BASE: approved V2.5 Remaining Tabs Layout Unification
VISUAL BASIS: real V2.5 runtime screenshots for /leads/2184 (Details + Form Data, Light/Dark)
COLOR BASIS: Team Dashboard palette — PRESERVED

STRICT SCOPE:
- Details tab only
- Form Data tab only
- Overview / Felfel / Stages & Notes / Reminders / Quotations must remain unchanged
- No backend, query, mutation, route, permission or business-logic changes
- No invented lead data or fake labels/answers
*/

.tcrm-lead-profile-premium-v2-6{
  --v26-surface:#ffffff;
  --v26-surface-soft:#f8faff;
  --v26-surface-alt:#f3f6ff;
  --v26-border:rgba(99,102,241,.16);
  --v26-border-strong:rgba(99,102,241,.27);
  --v26-text:#18213a;
  --v26-muted:#73809a;
  --v26-indigo:#6366f1;
  --v26-blue:#3b82f6;
  --v26-violet:#8b5cf6;
  --v26-shadow:0 18px 44px -34px rgba(44,54,130,.36),0 8px 20px -18px rgba(74,82,170,.20),inset 0 1px 0 rgba(255,255,255,.94);
}
.dark .tcrm-lead-profile-premium-v2-6{
  --v26-surface:#0b2345;
  --v26-surface-soft:#0d294f;
  --v26-surface-alt:#102f59;
  --v26-border:rgba(111,132,226,.27);
  --v26-border-strong:rgba(115,136,239,.42);
  --v26-text:#eef4ff;
  --v26-muted:#9dafce;
  --v26-shadow:0 22px 48px -34px rgba(0,0,0,.94),0 0 24px -23px rgba(99,102,241,.65),inset 0 1px 0 rgba(255,255,255,.055);
}

/* -------------------------------------------------------------------------- */
/* SHARED DETAILS / FORM DATA SURFACE                                          */
/* -------------------------------------------------------------------------- */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card{
  background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(248,250,255,.96))!important;
  border-color:var(--v26-border)!important;
  box-shadow:var(--v26-shadow)!important;
  border-radius:18px!important;
}
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card,
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card{
  background:linear-gradient(145deg,rgba(9,31,61,.98),rgba(8,27,54,.98))!important;
}

.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head{
  padding:15px 17px!important;
  background:linear-gradient(115deg,#4338ca 0%,#2563eb 50%,#7c3aed 100%)!important;
  border-bottom:1px solid rgba(255,255,255,.16)!important;
}
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head,
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head{
  background:linear-gradient(115deg,#162b69 0%,#17458e 50%,#4c2b92 100%)!important;
}

.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head p:first-of-type,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head p:first-of-type{
  font-size:13px!important;
  font-weight:850!important;
  letter-spacing:0!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>.tcrm-lp-section-head p:last-of-type,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-v26-formdata-card>.tcrm-lp-section-head p:last-of-type{
  font-size:10px!important;
  opacity:.86!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-section-icon{
  width:34px;
  height:34px;
  flex:0 0 34px;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:11px;
  color:var(--v26-indigo);
  background:linear-gradient(145deg,rgba(99,102,241,.13),rgba(59,130,246,.09));
  border:1px solid rgba(99,102,241,.18);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.8);
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-section-icon{
  color:#a5b4fc;
  background:linear-gradient(145deg,rgba(99,102,241,.22),rgba(59,130,246,.12));
  border-color:rgba(129,140,248,.28);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
}

/* -------------------------------------------------------------------------- */
/* DETAILS — structured information workspace                                  */
/* -------------------------------------------------------------------------- */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card>[data-slot="card-content"],
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-card .p-4{
  padding:16px!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head{
  display:flex;
  align-items:center;
  gap:10px;
  margin:2px 0 11px;
  padding-bottom:10px;
  border-bottom:1px solid var(--v26-border);
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head strong{
  display:block;
  color:var(--v26-text);
  font-size:13px;
  line-height:1.2;
  font-weight:850;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-section-head span{
  display:block;
  margin-top:3px;
  color:var(--v26-muted);
  font-size:10px;
  line-height:1.35;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:9px;
  margin-bottom:15px;
}

/* InfoRow outputs become compact premium field tiles without changing InfoRow. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div{
  min-width:0;
  min-height:66px;
  padding:10px 12px!important;
  border:1px solid var(--v26-border)!important;
  border-radius:13px!important;
  background:linear-gradient(145deg,var(--v26-surface),var(--v26-surface-soft))!important;
  box-shadow:0 8px 18px -18px rgba(55,65,145,.35),inset 0 1px 0 rgba(255,255,255,.72);
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div{
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div:hover{
  border-color:var(--v26-border-strong)!important;
}

/* Give long note-like rows the full reading width. */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid>div:nth-last-child(-n+2){
  min-height:72px;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section{
  margin-top:4px;
  padding:14px;
  border:1px solid var(--v26-border);
  border-radius:14px;
  background:linear-gradient(145deg,rgba(99,102,241,.045),rgba(59,130,246,.025));
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section{
  background:linear-gradient(145deg,rgba(99,102,241,.105),rgba(59,130,246,.055));
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section>.flex.items-center{
  margin-bottom:10px!important;
  padding-bottom:9px!important;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-sales-section>div:not(.flex){
  margin-top:7px;
}

/* Edit mode: stop the form from becoming one very tall narrow stack. */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab .grid.grid-cols-1.gap-3{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:11px!important;
}
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab input,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab [role="combobox"],
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab textarea{
  border-color:var(--v26-border)!important;
  background:var(--v26-surface-soft)!important;
}
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab input,
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab [role="combobox"],
.dark .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab textarea{
  color:var(--v26-text)!important;
}

/* -------------------------------------------------------------------------- */
/* FORM DATA — question / answer command sheet                                 */
/* -------------------------------------------------------------------------- */
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-formdata-body{
  width:100%;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head{
  display:flex;
  align-items:center;
  gap:10px;
  padding:1px 0 11px;
  border-bottom:1px solid var(--v26-border);
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head strong{
  display:block;
  color:var(--v26-text);
  font-size:13px;
  line-height:1.2;
  font-weight:850;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head span{
  display:block;
  margin-top:3px;
  color:var(--v26-muted);
  font-size:10px;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head em{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:31px;
  height:25px;
  padding-inline:8px;
  border-radius:999px;
  border:1px solid var(--v26-border-strong);
  background:rgba(99,102,241,.08);
  color:var(--v26-indigo);
  font-size:10px;
  font-style:normal;
  font-weight:850;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields-head em{
  color:#c7d2fe;
  background:rgba(99,102,241,.16);
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-fields{
  display:flex;
  flex-direction:column;
  gap:8px;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field{
  position:relative;
  display:grid;
  grid-template-columns:34px minmax(0,1fr);
  gap:10px;
  align-items:stretch;
  min-width:0;
  padding:9px 11px 9px 9px;
  border:1px solid var(--v26-border);
  border-radius:13px;
  background:linear-gradient(145deg,var(--v26-surface),var(--v26-surface-soft));
  transition:border-color .18s ease,transform .18s ease,box-shadow .18s ease;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field:hover{
  border-color:var(--v26-border-strong);
  box-shadow:0 12px 24px -22px rgba(61,72,170,.55);
  transform:translateY(-1px);
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-index{
  width:30px;
  height:30px;
  align-self:center;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:9px;
  color:var(--v26-indigo);
  background:linear-gradient(145deg,rgba(99,102,241,.14),rgba(59,130,246,.08));
  border:1px solid rgba(99,102,241,.18);
  font-size:9px;
  font-weight:900;
  letter-spacing:.02em;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-index{
  color:#c7d2fe;
  background:linear-gradient(145deg,rgba(99,102,241,.23),rgba(59,130,246,.12));
  border-color:rgba(129,140,248,.25);
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field-content{
  min-width:0;
  display:flex;
  align-items:center;
}
.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field-content>div{
  width:100%;
  min-width:0;
  padding:0!important;
  border:0!important;
  background:transparent!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-source-card{
  border-color:var(--v26-border)!important;
  background:linear-gradient(145deg,rgba(99,102,241,.045),rgba(59,130,246,.025))!important;
}
.dark .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-source-card{
  background:linear-gradient(145deg,rgba(99,102,241,.11),rgba(59,130,246,.055))!important;
}

.tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-empty{
  min-height:250px;
  border:1px dashed var(--v26-border-strong);
  border-radius:14px;
  background:linear-gradient(145deg,var(--v26-surface-soft),var(--v26-surface-alt));
}

/* Preserve the approved V2.5 72/28 contract exactly. */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .lead-profile-grid,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .lead-profile-grid{
  grid-template-columns:minmax(0,2.65fr) minmax(var(--v25-rail-min),1fr)!important;
  grid-template-areas:"main rail"!important;
}

/* Rail is intentionally not redesigned in V2.6. Keep it as V2.5. */
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-rail,
.tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .tcrm-lp-rail{
  position:relative;
}

@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

@media (max-width:1180px){
  .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .lead-profile-grid,
  .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-formdata-active .lead-profile-grid{
    grid-template-columns:1fr!important;
    grid-template-areas:"main" "rail"!important;
  }
}

@media (max-width:760px){
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-details-grid,
  .tcrm-lead-profile-premium-v2-6.tcrm-lp-v26-details-active .tcrm-lp-v26-details-tab .grid.grid-cols-1.gap-3{
    grid-template-columns:1fr!important;
  }
  .tcrm-lead-profile-premium-v2-6 .tcrm-lp-v26-form-field{
    grid-template-columns:30px minmax(0,1fr);
    padding:8px;
  }
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_5_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_6=YES")
print("DETAILS_FORMDATA_REDESIGN=YES")
print("REAL_RUNTIME_SCREENSHOTS_USED_AS_VISUAL_BASIS=YES")
print("DETAILS_FIELD_GRID_REDESIGNED=YES")
print("DETAILS_SALES_SECTION_REDESIGNED=YES")
print("DETAILS_EDIT_MODE_GRID_POLISHED=YES")
print("FORMDATA_QUESTION_ANSWER_LAYOUT_REDESIGNED=YES")
print("FORMDATA_SOURCE_CARD_REDESIGNED=YES")
print("NO_INVENTED_LEAD_DATA=YES")
print("OVERVIEW_UNCHANGED=YES")
print("FELFEL_UNCHANGED=YES")
print("STAGES_NOTES_UNCHANGED=YES")
print("REMINDERS_UNCHANGED=YES")
print("QUOTATIONS_UNCHANGED=YES")
print("V2_5_MAIN_72_RAIL_28_PRESERVED=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-6-details-formdata.css")
