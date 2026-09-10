#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/new-lead-premium-v1.css"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1"
CSS_IMPORT = 'import "../new-lead-premium-v1.css";'


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        fail(f"ANCHOR_MISSING:{label}")
    return text.replace(old, new, 1)


if not TARGET.exists():
    fail(f"TARGET_MISSING:{TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

if MARKER in text and CSS.exists() and CSS_IMPORT in text:
    print("PATCH=YES")
    print("ALREADY_APPLIED=YES")
    print("NEW_LEAD_PREMIUM_V1=YES")
    print("ERROR=NONE")
    sys.exit(0)

required = [
    'import "../leads-premium-v1-11.css";',
    '<Dialog open={showNewLead} onOpenChange={setShowNewLead}>',
    '<DialogContent className="max-w-2xl overflow-hidden p-0" dir={isRTL ? "rtl" : "ltr"}>',
    '<form onSubmit={handleSubmit(onSubmit)}>',
    'createLead.isPending || !!formPhoneConflict?.conflictWithAnotherSalesAgent',
    '<PhoneInput',
    '<CountrySelect',
    '{/* Section 1: Contact Info */}',
    '{/* Section 2: Lead Details */}',
    '{/* Section 3: Assignment (admins only) */}',
    '{/* Section 4: Notes */}',
]
for token in required:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

# Marker + isolated stylesheet import. Existing Leads premium styles remain the base identity.
text = replace_once(
    text,
    'import "../leads-premium-v1-11.css";',
    'import "../leads-premium-v1-11.css";\n' + CSS_IMPORT + f'\n// {MARKER}',
    "CSS_IMPORT",
)

# Scope the redesign to New Lead only.
text = replace_once(
    text,
    '<DialogContent className="max-w-2xl overflow-hidden p-0" dir={isRTL ? "rtl" : "ltr"}>',
    '<DialogContent className="max-w-2xl overflow-hidden p-0 tcrm-new-lead-modal" dir={isRTL ? "rtl" : "ltr"}>',
    "DIALOG_CLASS",
)
text = replace_once(
    text,
    'className="relative px-6 pt-6 pb-5 overflow-hidden"\n            style={{ background: `linear-gradient(135deg, ${tokens.primaryColor} 0%, ${tokens.primaryColor}cc 100%)` }}',
    'className="relative px-6 pt-6 pb-5 overflow-hidden tcrm-new-lead-header"\n            style={{ background: `linear-gradient(135deg, ${tokens.primaryColor} 0%, ${tokens.primaryColor}cc 100%)` }}',
    "HEADER_CLASS",
)
text = replace_once(
    text,
    'className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center shrink-0 border border-white/30"',
    'className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center shrink-0 border border-white/30 tcrm-new-lead-header-icon"',
    "HEADER_ICON_CLASS",
)
text = replace_once(
    text,
    '<form onSubmit={handleSubmit(onSubmit)}>',
    '<form onSubmit={handleSubmit(onSubmit)} className="tcrm-new-lead-form">',
    "FORM_CLASS",
)
text = replace_once(
    text,
    '<div className="relative overflow-y-auto max-h-[calc(88vh-180px)] px-6 py-5 space-y-6">',
    '<div className="relative overflow-y-auto max-h-[calc(88vh-180px)] px-6 py-5 space-y-6 tcrm-new-lead-body">',
    "BODY_CLASS",
)

# Section shells.
text = replace_once(
    text,
    '{/* Section 1: Contact Info */}\n              <section className="relative space-y-4">',
    '{/* Section 1: Contact Info */}\n              <section className="relative space-y-4 tcrm-new-lead-section tcrm-new-lead-contact">',
    "CONTACT_SECTION",
)
text = replace_once(
    text,
    '{/* Section 2: Lead Details */}\n              <section className="relative space-y-4">',
    '{/* Section 2: Lead Details */}\n              <section className="relative space-y-4 tcrm-new-lead-section tcrm-new-lead-details">',
    "DETAILS_SECTION",
)
text = replace_once(
    text,
    '<section className="relative space-y-4">\n                    <div className="flex items-center gap-2">\n                      <div className="w-1 h-5 rounded-full bg-purple-400 shrink-0" />',
    '<section className="relative space-y-4 tcrm-new-lead-section tcrm-new-lead-assignment">\n                    <div className="tcrm-new-lead-section-heading">\n                      <div className="tcrm-new-lead-section-icon tcrm-new-lead-section-icon-assignment"><Users className="w-[18px] h-[18px]" /></div>',
    "ASSIGNMENT_SECTION_START",
)
text = replace_once(
    text,
    '{/* Section 4: Notes */}\n              <div className="h-px bg-gradient-to-r from-transparent via-zinc-200 to-transparent" />\n              <section className="relative space-y-4">',
    '{/* Section 4: Notes */}\n              <div className="h-px bg-gradient-to-r from-transparent via-zinc-200 to-transparent" />\n              <section className="relative space-y-4 tcrm-new-lead-section tcrm-new-lead-notes">',
    "NOTES_SECTION",
)

# Premium section headings with icon tiles/subcopy; no form controls or data logic changed.
contact_heading = '''                <div className="flex items-center gap-2">\n                  <div className="w-1 h-5 rounded-full shrink-0" style={{ background: tokens.primaryColor }} />\n                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">\n                    {isRTL ? "معلومات التواصل" : "Contact Information"}\n                  </span>\n                </div>'''
contact_new = '''                <div className="tcrm-new-lead-section-heading">\n                  <div className="tcrm-new-lead-section-icon"><Phone size={18} /></div>\n                  <div className="tcrm-new-lead-section-copy">\n                    <span className="tcrm-new-lead-section-title">{isRTL ? "معلومات التواصل" : "Contact Information"}</span>\n                    <p className="tcrm-new-lead-section-subtitle">{isRTL ? "البيانات الأساسية للتواصل مع العميل" : "Basic details about the lead"}</p>\n                  </div>\n                </div>'''
text = replace_once(text, contact_heading, contact_new, "CONTACT_HEADING")

details_heading = '''                <div className="flex items-center gap-2">\n                  <div className="w-1 h-5 rounded-full bg-orange-400 shrink-0" />\n                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">\n                    {isRTL ? "تفاصيل العميل" : "Lead Details"}\n                  </span>\n                </div>'''
details_new = '''                <div className="tcrm-new-lead-section-heading">\n                  <div className="tcrm-new-lead-section-icon tcrm-new-lead-section-icon-details"><SlidersHorizontal size={18} /></div>\n                  <div className="tcrm-new-lead-section-copy">\n                    <span className="tcrm-new-lead-section-title">{isRTL ? "تفاصيل العميل" : "Lead Details"}</span>\n                    <p className="tcrm-new-lead-section-subtitle">{isRTL ? "تقييم وتصنيف العميل المحتمل" : "Qualify and categorize the lead"}</p>\n                  </div>\n                </div>'''
text = replace_once(text, details_heading, details_new, "DETAILS_HEADING")

# Finish Assignment heading after its icon replacement.
assignment_tail = '''                      <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">\n                        {isRTL ? "التعيين" : "Assignment"}\n                      </span>\n                    </div>'''
assignment_new = '''                      <div className="tcrm-new-lead-section-copy">\n                        <span className="tcrm-new-lead-section-title">{isRTL ? "التعيين" : "Assignment"}</span>\n                        <p className="tcrm-new-lead-section-subtitle">{isRTL ? "تعيين العميل إلى عضو من فريق المبيعات" : "Assign the lead to a team member"}</p>\n                      </div>\n                    </div>'''
text = replace_once(text, assignment_tail, assignment_new, "ASSIGNMENT_HEADING_TAIL")

notes_heading = '''                <div className="flex items-center gap-2">\n                  <div className="w-1 h-5 rounded-full bg-zinc-400 shrink-0" />\n                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">\n                    {isRTL ? "ملاحظات" : "Notes"}\n                  </span>\n                </div>'''
notes_new = '''                <div className="tcrm-new-lead-section-heading">\n                  <div className="tcrm-new-lead-section-icon tcrm-new-lead-section-icon-notes"><MessageSquare size={18} /></div>\n                  <div className="tcrm-new-lead-section-copy">\n                    <span className="tcrm-new-lead-section-title">{isRTL ? "ملاحظات" : "Notes"}</span>\n                    <p className="tcrm-new-lead-section-subtitle">{isRTL ? "أضف سياقًا يساعد في المتابعة القادمة" : "Add context for the next follow-up"}</p>\n                  </div>\n                </div>'''
text = replace_once(text, notes_heading, notes_new, "NOTES_HEADING")

# Component-level hooks for polished compound controls.
text = replace_once(
    text,
    '                    defaultCountryCode="SA"\n                    isRTL={isRTL}\n                    error={phoneError}',
    '                    defaultCountryCode="SA"\n                    isRTL={isRTL}\n                    className="tcrm-new-lead-phone"\n                    error={phoneError}',
    "PHONE_CLASS",
)
text = replace_once(
    text,
    '<CountrySelect value={watch("country")} onChange={(name) => setValue("country", name)} isRTL={isRTL} />',
    '<CountrySelect value={watch("country")} onChange={(name) => setValue("country", name)} isRTL={isRTL} className="tcrm-new-lead-country" />',
    "COUNTRY_CLASS",
)

# Footer/buttons.
text = replace_once(
    text,
    '<div className="flex gap-2.5 justify-end px-6 py-4 border-t border-zinc-100 bg-zinc-50/80">',
    '<div className="flex gap-2.5 justify-end px-6 py-4 border-t border-zinc-100 bg-zinc-50/80 tcrm-new-lead-footer">',
    "FOOTER_CLASS",
)
text = replace_once(
    text,
    'className="rounded-xl text-sm h-9 px-5"\n              >\n                {t("cancel")}',
    'className="rounded-xl text-sm h-9 px-5 tcrm-new-lead-cancel"\n              >\n                {t("cancel")}',
    "CANCEL_CLASS",
)
text = replace_once(
    text,
    'className="text-white rounded-xl text-sm h-9 min-w-[130px] shadow-sm"\n                disabled={createLead.isPending',
    'className="text-white rounded-xl text-sm h-9 min-w-[130px] shadow-sm tcrm-new-lead-save"\n                disabled={createLead.isPending',
    "SAVE_CLASS",
)

# Verify logic anchors are still byte-present after class-only/heading structural changes.
logic_checks = [
    'onSubmit={handleSubmit(onSubmit)}',
    'setValue("phone", fullPhone);',
    'setValue("country", c.name);',
    'setValue("leadQuality", v as any, { shouldDirty: true })',
    'setValue("fitStatus", v as any, { shouldDirty: true })',
    'setValue("stage", v, { shouldDirty: true })',
    'setValue("campaignName", v === "none" ? "" : v);',
    'setValue("ownerId", v === "none" ? undefined : Number(v), { shouldDirty: true })',
    'createLead.isPending || !!formPhoneConflict?.conflictWithAnotherSalesAgent',
]
for token in logic_checks:
    if token not in text:
        fail(f"LOGIC_GUARD_FAILED:{token}")

css = r'''/* TCRM_NEW_LEAD_MODAL_PREMIUM_V1
   Identity lock: Agent Dashboard V28 + Team Dashboard V2.2 + Leads Premium V1.x
   Visual-only New Lead modal redesign. */

.tcrm-new-lead-modal {
  --nl-indigo: #6366f1;
  --nl-indigo-deep: #4f46e5;
  --nl-violet: #5b21b6;
  --nl-violet-deep: #3b0764;
  --nl-blue: #3b82f6;
  --nl-text: #182238;
  --nl-muted: #6c768d;
  --nl-border: rgba(99, 102, 241, .20);
  --nl-border-strong: rgba(99, 102, 241, .32);
  width: min(760px, calc(100vw - 32px)) !important;
  max-width: 760px !important;
  max-height: min(92vh, 920px) !important;
  overflow: hidden !important;
  border-radius: 24px !important;
  border: 1px solid var(--nl-border-strong) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.995) 0%, rgba(248,250,255,.985) 100%) !important;
  box-shadow:
    0 32px 90px rgba(15,23,42,.24),
    0 12px 34px rgba(79,70,229,.12),
    inset 0 1px 0 rgba(255,255,255,.92) !important;
  isolation: isolate;
}

.tcrm-new-lead-modal::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background:
    radial-gradient(circle at 9% 3%, rgba(139,92,246,.10), transparent 22%),
    radial-gradient(circle at 93% 12%, rgba(59,130,246,.08), transparent 24%);
  z-index: -1;
}

.tcrm-new-lead-header {
  min-height: 104px;
  padding: 24px 30px 22px !important;
  background:
    radial-gradient(circle at 88% 8%, rgba(255,255,255,.20), transparent 30%),
    radial-gradient(circle at 12% 118%, rgba(129,140,248,.30), transparent 42%),
    linear-gradient(118deg, #3b0764 0%, #5b21b6 32%, #4f46e5 70%, #6366f1 100%) !important;
  border-bottom: 1px solid rgba(255,255,255,.18);
}

.tcrm-new-lead-header::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .42;
  background-image:
    radial-gradient(circle at 1px 1px, rgba(255,255,255,.54) 1px, transparent 0);
  background-size: 22px 22px;
  mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.24) 25%, #000 100%);
}

.tcrm-new-lead-header > .absolute.inset-0 { opacity: 0 !important; }

.tcrm-new-lead-header-icon {
  width: 48px !important;
  height: 48px !important;
  border-radius: 15px !important;
  background: linear-gradient(145deg, rgba(255,255,255,.28), rgba(255,255,255,.14)) !important;
  border: 1px solid rgba(255,255,255,.40) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.28), 0 10px 24px rgba(26,20,84,.22);
}

.tcrm-new-lead-header h2 {
  font-size: 21px !important;
  line-height: 1.15 !important;
  letter-spacing: -.02em;
  font-weight: 760 !important;
  text-shadow: 0 1px 12px rgba(30,27,75,.18);
}

.tcrm-new-lead-header p {
  margin-top: 5px !important;
  color: rgba(255,255,255,.76) !important;
  font-size: 13px !important;
}

.tcrm-new-lead-modal [data-slot="dialog-close"] {
  top: 22px !important;
  right: 22px !important;
  width: 34px !important;
  height: 34px !important;
  border-radius: 999px !important;
  color: rgba(255,255,255,.90) !important;
  background: rgba(255,255,255,.10) !important;
  border: 1px solid rgba(255,255,255,.28) !important;
  backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.15);
}

.tcrm-new-lead-modal [data-slot="dialog-close"]:hover {
  color: #fff !important;
  background: rgba(255,255,255,.18) !important;
  transform: translateY(-1px);
}

.tcrm-new-lead-modal[dir="rtl"] [data-slot="dialog-close"] {
  right: auto !important;
  left: 22px !important;
}

.tcrm-new-lead-form {
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.tcrm-new-lead-body {
  max-height: calc(min(92vh, 920px) - 178px) !important;
  padding: 24px 30px 26px !important;
  gap: 0 !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(99,102,241,.035), transparent 28%),
    linear-gradient(180deg, rgba(255,255,255,.985), rgba(248,250,255,.92));
  scrollbar-width: thin;
  scrollbar-color: rgba(99,102,241,.38) transparent;
}

.tcrm-new-lead-body::-webkit-scrollbar { width: 7px; }
.tcrm-new-lead-body::-webkit-scrollbar-track { background: transparent; }
.tcrm-new-lead-body::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(99,102,241,.50), rgba(139,92,246,.38));
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.tcrm-new-lead-section {
  padding: 0 0 22px;
}

.tcrm-new-lead-section + .tcrm-new-lead-section {
  padding-top: 22px;
}

.tcrm-new-lead-body > .h-px {
  height: 1px !important;
  margin: 0 0 22px !important;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,.18) 16%, rgba(99,102,241,.18) 84%, transparent) !important;
}

.tcrm-new-lead-section-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 17px;
}

.tcrm-new-lead-section-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  color: #4f46e5;
  background: linear-gradient(145deg, rgba(238,242,255,.98), rgba(245,243,255,.96));
  border: 1px solid rgba(99,102,241,.16);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 8px 18px rgba(79,70,229,.08);
}

.tcrm-new-lead-section-icon-details {
  color: #6366f1;
  background: linear-gradient(145deg, rgba(238,242,255,.98), rgba(239,246,255,.96));
}

.tcrm-new-lead-section-icon-assignment {
  color: #7c3aed;
  background: linear-gradient(145deg, rgba(245,243,255,.98), rgba(238,242,255,.96));
}

.tcrm-new-lead-section-icon-notes {
  color: #64748b;
  background: linear-gradient(145deg, rgba(248,250,252,.99), rgba(238,242,255,.94));
}

.tcrm-new-lead-section-copy { min-width: 0; }

.tcrm-new-lead-section-title {
  display: block;
  color: var(--nl-text);
  font-size: 12px;
  line-height: 1.2;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .085em;
}

.tcrm-new-lead-section-subtitle {
  margin-top: 4px;
  color: #7b86a0;
  font-size: 11.5px;
  line-height: 1.3;
  font-weight: 500;
}

.tcrm-new-lead-body label {
  color: #34405a !important;
  font-size: 11px !important;
  font-weight: 720 !important;
  letter-spacing: .055em !important;
}

.tcrm-new-lead-body input,
.tcrm-new-lead-body textarea,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country {
  border-color: rgba(148,163,184,.30) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,255,.90)) !important;
  color: #25304a !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.92), 0 1px 2px rgba(15,23,42,.025);
  transition: border-color .18s ease, box-shadow .18s ease, background .18s ease, transform .18s ease !important;
}

.tcrm-new-lead-body input,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country {
  height: 46px !important;
  border-radius: 12px !important;
}

.tcrm-new-lead-body textarea {
  border-radius: 14px !important;
  min-height: 104px !important;
  padding: 12px 14px !important;
}

.tcrm-new-lead-body input::placeholder,
.tcrm-new-lead-body textarea::placeholder {
  color: #9aa5ba !important;
}

.tcrm-new-lead-body input:focus,
.tcrm-new-lead-body textarea:focus,
.tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.tcrm-new-lead-country:focus-visible {
  border-color: rgba(99,102,241,.78) !important;
  background: #fff !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.11), 0 7px 18px rgba(79,70,229,.06) !important;
  outline: none !important;
}

/* PhoneInput compound field */
.tcrm-new-lead-phone > div:first-child {
  min-height: 46px !important;
  border-radius: 12px !important;
  border-color: rgba(148,163,184,.30) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,255,.90)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.92);
}

.tcrm-new-lead-phone > div:first-child:focus-within {
  border-color: rgba(99,102,241,.78) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.11), 0 7px 18px rgba(79,70,229,.06) !important;
}

.tcrm-new-lead-phone > div:first-child > button {
  height: 44px !important;
  padding-inline: 12px !important;
  background: rgba(238,242,255,.72) !important;
  border-color: rgba(99,102,241,.14) !important;
}

.tcrm-new-lead-phone > div:first-child > input {
  height: 44px !important;
  border: 0 !important;
  box-shadow: none !important;
  background: transparent !important;
}

.tcrm-new-lead-footer {
  position: relative;
  z-index: 2;
  min-height: 76px;
  align-items: center;
  padding: 14px 30px !important;
  border-top: 1px solid rgba(99,102,241,.13) !important;
  background: rgba(250,251,255,.90) !important;
  backdrop-filter: blur(18px);
  box-shadow: 0 -10px 30px rgba(51,65,85,.035);
}

.tcrm-new-lead-cancel,
.tcrm-new-lead-save {
  height: 44px !important;
  border-radius: 12px !important;
  padding-inline: 22px !important;
  font-weight: 700 !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}

.tcrm-new-lead-cancel {
  min-width: 104px;
  color: #334155 !important;
  border-color: rgba(148,163,184,.34) !important;
  background: rgba(255,255,255,.88) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 4px 12px rgba(15,23,42,.04);
}

.tcrm-new-lead-save {
  min-width: 136px !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.20) !important;
  background: linear-gradient(112deg, #5b21b6 0%, #4f46e5 55%, #6366f1 100%) !important;
  box-shadow: 0 11px 24px rgba(79,70,229,.24), inset 0 1px 0 rgba(255,255,255,.22) !important;
}

.tcrm-new-lead-cancel:hover:not(:disabled),
.tcrm-new-lead-save:hover:not(:disabled) {
  transform: translateY(-1px);
}

.tcrm-new-lead-save:hover:not(:disabled) {
  box-shadow: 0 14px 30px rgba(79,70,229,.31), inset 0 1px 0 rgba(255,255,255,.25) !important;
}

/* Keep validation semantics visible without changing validation logic. */
.tcrm-new-lead-body .border-red-400,
.tcrm-new-lead-body .border-red-500 {
  border-color: rgba(239,68,68,.78) !important;
  box-shadow: 0 0 0 3px rgba(239,68,68,.09) !important;
}

/* DARK — same Dashboard/Team/Leads deep-navy + indigo identity. */
.dark .tcrm-new-lead-modal {
  --nl-text: #f4f7ff;
  --nl-muted: #a7b3c9;
  --nl-border: rgba(119,133,255,.24);
  --nl-border-strong: rgba(119,133,255,.40);
  background: linear-gradient(180deg, rgba(13,27,51,.992), rgba(7,17,31,.995)) !important;
  border-color: var(--nl-border-strong) !important;
  box-shadow: 0 36px 100px rgba(0,0,0,.54), 0 10px 42px rgba(79,70,229,.17) !important;
}

.dark .tcrm-new-lead-body {
  background:
    radial-gradient(circle at 100% 0%, rgba(99,102,241,.10), transparent 30%),
    linear-gradient(180deg, rgba(13,27,51,.985), rgba(7,17,31,.99));
}

.dark .tcrm-new-lead-section-title { color: #f4f7ff; }
.dark .tcrm-new-lead-section-subtitle { color: #9aa8c2; }

.dark .tcrm-new-lead-section-icon {
  color: #c4b5fd;
  background: linear-gradient(145deg, rgba(79,70,229,.22), rgba(30,41,59,.82));
  border-color: rgba(129,140,248,.27);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 9px 22px rgba(0,0,0,.16);
}

.dark .tcrm-new-lead-section-icon-details { color: #a5b4fc; }
.dark .tcrm-new-lead-section-icon-assignment { color: #d8b4fe; }
.dark .tcrm-new-lead-section-icon-notes { color: #cbd5e1; }

.dark .tcrm-new-lead-body label { color: #c8d2e7 !important; }

.dark .tcrm-new-lead-body input,
.dark .tcrm-new-lead-body textarea,
.dark .tcrm-new-lead-body [data-slot="select-trigger"],
.dark .tcrm-new-lead-country,
.dark .tcrm-new-lead-phone > div:first-child {
  border-color: rgba(119,133,255,.26) !important;
  background: linear-gradient(180deg, rgba(15,31,57,.92), rgba(11,28,52,.88)) !important;
  color: #f1f5ff !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 1px 2px rgba(0,0,0,.10);
}

.dark .tcrm-new-lead-body input::placeholder,
.dark .tcrm-new-lead-body textarea::placeholder { color: #71809c !important; }

.dark .tcrm-new-lead-body input:focus,
.dark .tcrm-new-lead-body textarea:focus,
.dark .tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.dark .tcrm-new-lead-country:focus-visible,
.dark .tcrm-new-lead-phone > div:first-child:focus-within {
  border-color: rgba(129,140,248,.74) !important;
  background: rgba(15,31,57,.98) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.17), 0 10px 22px rgba(0,0,0,.12) !important;
}

.dark .tcrm-new-lead-phone > div:first-child > button {
  background: rgba(49,46,129,.22) !important;
  border-color: rgba(129,140,248,.22) !important;
}

.dark .tcrm-new-lead-footer {
  border-color: rgba(119,133,255,.18) !important;
  background: rgba(8,20,39,.90) !important;
  box-shadow: 0 -10px 30px rgba(0,0,0,.12);
}

.dark .tcrm-new-lead-cancel {
  color: #d8e0f0 !important;
  background: rgba(15,31,57,.92) !important;
  border-color: rgba(119,133,255,.29) !important;
}

@media (max-width: 640px) {
  .tcrm-new-lead-modal {
    width: calc(100vw - 20px) !important;
    max-height: 94vh !important;
    border-radius: 20px !important;
  }
  .tcrm-new-lead-header { padding: 20px 20px 18px !important; min-height: 92px; }
  .tcrm-new-lead-body { padding: 20px !important; max-height: calc(94vh - 164px) !important; }
  .tcrm-new-lead-footer { padding: 12px 20px !important; min-height: 68px; }
  .tcrm-new-lead-section-icon { width: 38px; height: 38px; flex-basis: 38px; }
  .tcrm-new-lead-modal [data-slot="dialog-close"] { top: 18px !important; right: 18px !important; }
  .tcrm-new-lead-modal[dir="rtl"] [data-slot="dialog-close"] { right: auto !important; left: 18px !important; }
}

@media (prefers-reduced-motion: reduce) {
  .tcrm-new-lead-modal *, .tcrm-new-lead-modal *::before, .tcrm-new-lead-modal *::after {
    transition-duration: .001ms !important;
  }
}
'''

if original == text:
    fail("NO_SOURCE_CHANGE")

# Back up source; new CSS is additive.
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / f"LeadsList.tsx.{stamp}.new-lead-v1.bak"
shutil.copy2(TARGET, backup)

TARGET.write_text(text, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("NEW_LEAD_PREMIUM_V1=YES")
print("ORIGINAL_CONCEPT_IMPLEMENTED=YES")
print("DASHBOARD_V28_IDENTITY=YES")
print("TEAM_DASHBOARD_V2_2_IDENTITY=YES")
print("LEADS_PREMIUM_IDENTITY=YES")
print("LIGHT_THEME=YES")
print("DARK_THEME=YES")
print("RTL_LTR=YES")
print("RESPONSIVE=YES")
print("FORM_LOGIC_UNCHANGED=YES")
print("CREATE_LEAD_FLOW_UNCHANGED=YES")
print("VALIDATION_UNCHANGED=YES")
print("PHONE_LOGIC_UNCHANGED=YES")
print("CAMPAIGN_LOGIC_UNCHANGED=YES")
print("ASSIGNMENT_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx,client/src/new-lead-premium-v1.css")
print("ERROR=NONE")
