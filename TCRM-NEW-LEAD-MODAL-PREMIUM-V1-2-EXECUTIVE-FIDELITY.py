#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/new-lead-premium-v1-2.css"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
PREV_MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_1_DROPDOWN_FIDELITY_FIX"
MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_2_EXECUTIVE_FIDELITY"
PREV_IMPORT = 'import "../new-lead-premium-v1-1.css";'
CSS_IMPORT = 'import "../new-lead-premium-v1-2.css";'


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)


if not TARGET.exists():
    fail(f"TARGET_MISSING:{TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

for token in [
    PREV_MARKER,
    PREV_IMPORT,
    'tcrm-new-lead-modal',
    '<Dialog open={showNewLead} onOpenChange={setShowNewLead}>',
    'onSubmit={handleSubmit(onSubmit)}',
    'setValue("phone", fullPhone);',
    'setValue("campaignName", v === "none" ? "" : v);',
    'createLead.isPending || !!formPhoneConflict?.conflictWithAnotherSalesAgent',
]:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

# Add isolated V1.2 CSS layer.
if CSS_IMPORT not in text:
    text = text.replace(
        PREV_IMPORT,
        PREV_IMPORT + '\n' + CSS_IMPORT + '\n// ' + MARKER,
        1,
    )
elif MARKER not in text:
    text = text.replace(CSS_IMPORT, CSS_IMPORT + '\n// ' + MARKER, 1)

# Scope Select positioning changes ONLY to the New Lead modal block.
start = text.find('<Dialog open={showNewLead} onOpenChange={setShowNewLead}>')
end = text.find('<ExportCenter open={showExport}', start)
if start < 0 or end < 0:
    fail("NEW_LEAD_BLOCK_NOT_FOUND")

block = text[start:end]
old_select = '<SelectContent className="tcrm-leads-select-content">'
new_select = '<SelectContent className="tcrm-leads-select-content tcrm-new-lead-select-content" position="popper" align="start" sideOffset={7}>'
select_count = block.count(old_select)
if select_count < 4:
    fail(f"SELECT_COUNT_UNEXPECTED:{select_count}")
block = block.replace(old_select, new_select)
text = text[:start] + block + text[end:]

# Re-check logic after structural-only SelectContent prop change.
logic_guards = [
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
for token in logic_guards:
    if token not in text:
        fail(f"POST_LOGIC_GUARD_FAILED:{token}")

css = r'''/* TCRM_NEW_LEAD_MODAL_PREMIUM_V1_2_EXECUTIVE_FIDELITY
   Executive premium layer over V1.1.
   Identity lock: Agent Dashboard V28 / Team Dashboard V2.2 / Leads Premium.
   Palette unchanged: deep violet + indigo + electric blue / pearl light / navy dark.
*/

/* ===== MODAL PRESENCE ===== */
.tcrm-new-lead-modal {
  width: min(860px, calc(100vw - 38px)) !important;
  max-width: 860px !important;
  border-radius: 28px !important;
  border: 1px solid rgba(112,99,235,.34) !important;
  background:
    radial-gradient(circle at 12% -8%, rgba(124,92,255,.075), transparent 25%),
    radial-gradient(circle at 90% 4%, rgba(59,130,246,.055), transparent 28%),
    linear-gradient(180deg, rgba(255,255,255,.998), rgba(247,249,255,.992)) !important;
  box-shadow:
    0 44px 120px rgba(15,23,42,.26),
    0 20px 54px rgba(79,70,229,.15),
    0 0 0 1px rgba(255,255,255,.70) inset,
    0 0 46px rgba(99,102,241,.06) !important;
}

.tcrm-new-lead-modal::after {
  content:"";
  position:absolute;
  inset:1px;
  border-radius:27px;
  pointer-events:none;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.82);
  z-index:5;
}

/* ===== HERO / HEADER ===== */
.tcrm-new-lead-header {
  min-height: 122px !important;
  padding: 28px 34px 26px !important;
  background:
    radial-gradient(circle at 82% -10%, rgba(255,255,255,.30), transparent 28%),
    radial-gradient(circle at 63% 118%, rgba(96,165,250,.24), transparent 35%),
    radial-gradient(circle at 14% 116%, rgba(167,139,250,.38), transparent 42%),
    linear-gradient(116deg, #33065f 0%, #5520a5 28%, #4f46e5 66%, #5f6df3 100%) !important;
  box-shadow:
    inset 0 -1px 0 rgba(255,255,255,.18),
    0 18px 48px rgba(72,52,178,.16) !important;
}

.tcrm-new-lead-header::before {
  content:"";
  position:absolute;
  width:290px;
  height:290px;
  right:-58px;
  top:-176px;
  border-radius:50%;
  border:1px solid rgba(255,255,255,.15);
  box-shadow:0 0 0 24px rgba(255,255,255,.025),0 0 0 52px rgba(255,255,255,.018);
  pointer-events:none;
}

.tcrm-new-lead-header-icon {
  width:56px !important;
  height:56px !important;
  border-radius:17px !important;
  background:linear-gradient(145deg,rgba(255,255,255,.30),rgba(255,255,255,.12)) !important;
  border-color:rgba(255,255,255,.44) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.38),
    0 14px 32px rgba(24,16,82,.28),
    0 0 28px rgba(196,181,253,.18) !important;
}

.tcrm-new-lead-header h2 {
  font-size:24px !important;
  font-weight:790 !important;
  letter-spacing:-.025em !important;
  text-shadow:0 2px 18px rgba(32,24,99,.22);
}

.tcrm-new-lead-header p {
  font-size:13.5px !important;
  color:rgba(255,255,255,.82) !important;
}

.tcrm-new-lead-modal [data-slot="dialog-close"] {
  width:38px !important;
  height:38px !important;
  top:24px !important;
  right:24px !important;
  background:linear-gradient(145deg,rgba(255,255,255,.18),rgba(255,255,255,.08)) !important;
  border-color:rgba(255,255,255,.34) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.20),0 8px 20px rgba(25,18,85,.14) !important;
}
.tcrm-new-lead-modal[dir="rtl"] [data-slot="dialog-close"]{right:auto!important;left:24px!important}

/* ===== BODY / EXECUTIVE SECTION CARDS ===== */
.tcrm-new-lead-body {
  padding:28px 34px 30px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(99,102,241,.045), transparent 27%),
    linear-gradient(180deg, rgba(251,252,255,.98), rgba(247,249,255,.96)) !important;
  scrollbar-color:rgba(99,102,241,.24) transparent !important;
}
.tcrm-new-lead-body::-webkit-scrollbar{width:4px!important}
.tcrm-new-lead-body::-webkit-scrollbar-thumb{background:rgba(99,102,241,.28)!important;border-radius:999px!important}

.tcrm-new-lead-section {
  position:relative;
  padding:20px 20px 21px !important;
  margin:0 0 16px !important;
  border:1px solid rgba(110,105,190,.12);
  border-radius:19px;
  background:
    radial-gradient(circle at 100% 0%, rgba(99,102,241,.045), transparent 30%),
    linear-gradient(150deg, rgba(255,255,255,.90), rgba(248,250,255,.76));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.95),
    0 12px 28px rgba(39,47,90,.045);
}

.tcrm-new-lead-section::before {
  content:"";
  position:absolute;
  left:0;
  top:20px;
  bottom:20px;
  width:2px;
  border-radius:999px;
  background:linear-gradient(180deg,rgba(99,102,241,.74),rgba(139,92,246,.16));
  opacity:.70;
}
.tcrm-new-lead-modal[dir="rtl"] .tcrm-new-lead-section::before{left:auto;right:0}

.tcrm-new-lead-section + .tcrm-new-lead-section { padding-top:20px !important; }
.tcrm-new-lead-body > .h-px { display:none !important; }
.tcrm-new-lead-section-heading { gap:14px !important; margin-bottom:20px !important; }

.tcrm-new-lead-section-icon {
  width:48px !important;
  height:48px !important;
  flex-basis:48px !important;
  border-radius:15px !important;
  color:#5147dc !important;
  background:
    radial-gradient(circle at 30% 20%, rgba(255,255,255,.92), transparent 40%),
    linear-gradient(145deg, rgba(237,240,255,.98), rgba(244,240,255,.92)) !important;
  border-color:rgba(99,102,241,.24) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,1),
    0 10px 24px rgba(79,70,229,.11),
    0 0 24px rgba(99,102,241,.07) !important;
}

.tcrm-new-lead-section-title {
  font-size:13.5px !important;
  font-weight:830 !important;
  letter-spacing:.065em !important;
  color:#1f2942 !important;
}
.tcrm-new-lead-section-subtitle {
  margin-top:5px !important;
  font-size:12.5px !important;
  line-height:1.35 !important;
  color:#7a869f !important;
}

/* ===== FORM CONTROLS ===== */
.tcrm-new-lead-body label {
  color:#2e3952 !important;
  font-size:11.5px !important;
  font-weight:760 !important;
}

.tcrm-new-lead-body input,
.tcrm-new-lead-body textarea,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country,
.tcrm-new-lead-phone > div:first-child {
  border-color:rgba(125,137,168,.30) !important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.995),rgba(247,249,255,.94)) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.98),
    0 4px 12px rgba(38,46,86,.035) !important;
}

.tcrm-new-lead-body input,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country {
  height:50px !important;
  min-height:50px !important;
  border-radius:14px !important;
}
.tcrm-new-lead-phone > div:first-child{min-height:50px!important;border-radius:14px!important}
.tcrm-new-lead-phone > div:first-child > button,
.tcrm-new-lead-phone > div:first-child > input{height:48px!important}
.tcrm-new-lead-body textarea{min-height:116px!important;border-radius:15px!important}

.tcrm-new-lead-body input:hover,
.tcrm-new-lead-body textarea:hover,
.tcrm-new-lead-body [data-slot="select-trigger"]:hover,
.tcrm-new-lead-country:hover,
.tcrm-new-lead-phone > div:first-child:hover {
  border-color:rgba(99,102,241,.42) !important;
}

.tcrm-new-lead-body input:focus,
.tcrm-new-lead-body textarea:focus,
.tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.tcrm-new-lead-country:focus-visible,
.tcrm-new-lead-phone > div:first-child:focus-within {
  border-color:rgba(99,102,241,.86) !important;
  background:#fff !important;
  box-shadow:
    0 0 0 3px rgba(99,102,241,.11),
    0 12px 26px rgba(79,70,229,.08),
    inset 0 1px 0 rgba(255,255,255,1) !important;
}

/* ===== PORTALED DROPDOWNS: TIGHT ANCHOR + PREMIUM SURFACE ===== */
body:has(.tcrm-new-lead-modal) [data-radix-popper-content-wrapper] {
  z-index:800 !important;
  pointer-events:auto !important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content {
  width:var(--radix-select-trigger-width) !important;
  min-width:var(--radix-select-trigger-width) !important;
  max-width:min(380px,calc(100vw - 24px)) !important;
  max-height:min(300px,var(--radix-select-content-available-height)) !important;
  padding:6px !important;
  overflow-y:auto !important;
  border:1px solid rgba(99,102,241,.25) !important;
  border-radius:16px !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(124,92,255,.10), transparent 34%),
    linear-gradient(155deg,rgba(255,255,255,.998),rgba(246,248,255,.995)) !important;
  box-shadow:
    0 30px 70px -30px rgba(49,46,129,.46),
    0 16px 34px -24px rgba(15,23,42,.22),
    inset 0 1px 0 rgba(255,255,255,1) !important;
  backdrop-filter:blur(24px) saturate(1.14) !important;
}

body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"] {
  min-height:41px !important;
  margin:2px 0 !important;
  padding:8px 32px 8px 11px !important;
  border-radius:11px !important;
  font-size:12.5px !important;
  font-weight:650 !important;
  transition:background .14s ease,color .14s ease,box-shadow .14s ease,transform .14s ease !important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-highlighted],
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]:focus {
  color:#29245d !important;
  background:linear-gradient(90deg,rgba(99,102,241,.14),rgba(124,92,255,.075)) !important;
  box-shadow:inset 0 0 0 1px rgba(99,102,241,.10) !important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-state="checked"] {
  color:#332b78 !important;
  font-weight:760 !important;
  background:linear-gradient(90deg,rgba(99,102,241,.16),rgba(59,130,246,.07)) !important;
}

/* Phone/Country popovers use the same premium portal language. */
body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  width:min(330px,calc(100vw - 24px)) !important;
  max-height:min(340px,calc(100vh - 36px)) !important;
  border-radius:16px !important;
  overflow:hidden !important;
  box-shadow:
    0 30px 70px -30px rgba(49,46,129,.46),
    0 16px 34px -24px rgba(15,23,42,.22),
    inset 0 1px 0 rgba(255,255,255,1) !important;
}

/* ===== FOOTER ===== */
.tcrm-new-lead-footer {
  min-height:84px !important;
  padding:16px 34px !important;
  border-top-color:rgba(99,102,241,.16) !important;
  background:linear-gradient(180deg,rgba(251,252,255,.93),rgba(246,248,255,.96)) !important;
  backdrop-filter:blur(22px) saturate(1.08) !important;
  box-shadow:0 -16px 38px rgba(52,62,105,.05) !important;
}
.tcrm-new-lead-cancel,
.tcrm-new-lead-save {
  height:48px !important;
  border-radius:14px !important;
  font-weight:750 !important;
}
.tcrm-new-lead-cancel{min-width:112px!important}
.tcrm-new-lead-save {
  min-width:158px !important;
  background:linear-gradient(112deg,#5520a5 0%,#4f46e5 55%,#6366f1 100%) !important;
  box-shadow:
    0 14px 30px rgba(79,70,229,.30),
    0 0 26px rgba(99,102,241,.12),
    inset 0 1px 0 rgba(255,255,255,.26) !important;
}

/* ===== DARK ===== */
.dark .tcrm-new-lead-modal {
  background:
    radial-gradient(circle at 12% -8%, rgba(92,76,255,.13), transparent 26%),
    radial-gradient(circle at 90% 4%, rgba(59,130,246,.08), transparent 28%),
    linear-gradient(180deg,rgba(12,26,50,.998),rgba(6,16,31,.998)) !important;
  border-color:rgba(119,133,255,.44) !important;
  box-shadow:
    0 48px 130px rgba(0,0,0,.62),
    0 18px 58px rgba(74,62,201,.20),
    0 0 48px rgba(99,102,241,.07) !important;
}
.dark .tcrm-new-lead-body {
  background:
    radial-gradient(circle at 100% 0%,rgba(99,102,241,.09),transparent 28%),
    linear-gradient(180deg,rgba(11,25,48,.99),rgba(7,18,35,.99)) !important;
}
.dark .tcrm-new-lead-section {
  border-color:rgba(119,133,255,.18) !important;
  background:
    radial-gradient(circle at 100% 0%,rgba(99,102,241,.09),transparent 34%),
    linear-gradient(150deg,rgba(15,31,57,.88),rgba(9,23,44,.82)) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 14px 30px rgba(0,0,0,.13) !important;
}
.dark .tcrm-new-lead-section-title{color:#f4f7ff!important}
.dark .tcrm-new-lead-section-subtitle{color:#9eacc4!important}
.dark .tcrm-new-lead-section-icon {
  color:#c4b5fd !important;
  background:linear-gradient(145deg,rgba(80,70,205,.25),rgba(17,32,58,.90)) !important;
  border-color:rgba(129,140,248,.31) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 12px 26px rgba(0,0,0,.20),0 0 26px rgba(99,102,241,.09) !important;
}
.dark .tcrm-new-lead-body input,
.dark .tcrm-new-lead-body textarea,
.dark .tcrm-new-lead-body [data-slot="select-trigger"],
.dark .tcrm-new-lead-country,
.dark .tcrm-new-lead-phone > div:first-child {
  border-color:rgba(119,133,255,.27) !important;
  background:linear-gradient(180deg,rgba(15,32,59,.96),rgba(10,25,48,.94)) !important;
  color:#f2f6ff !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 5px 14px rgba(0,0,0,.09) !important;
}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content,
.dark body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  border-color:rgba(119,133,255,.34) !important;
  background:
    radial-gradient(circle at 8% 0%,rgba(99,82,255,.17),transparent 38%),
    linear-gradient(155deg,rgba(13,29,55,.998),rgba(7,19,38,.998)) !important;
  box-shadow:0 34px 78px -28px rgba(0,0,0,.90),0 0 38px -25px rgba(99,82,255,.52),inset 0 1px 0 rgba(255,255,255,.055) !important;
}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]{color:#d7deed!important}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-highlighted],
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]:focus,
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-state="checked"] {
  color:#fff!important;
  background:linear-gradient(90deg,rgba(110,91,255,.24),rgba(65,105,255,.12))!important;
}
.dark .tcrm-new-lead-footer {
  border-top-color:rgba(119,133,255,.18)!important;
  background:linear-gradient(180deg,rgba(9,22,42,.93),rgba(6,17,33,.97))!important;
}

@media (max-width:640px){
  .tcrm-new-lead-modal{width:calc(100vw - 18px)!important;border-radius:21px!important}
  .tcrm-new-lead-header{min-height:100px!important;padding:21px!important}
  .tcrm-new-lead-body{padding:18px!important}
  .tcrm-new-lead-section{padding:17px!important;border-radius:16px!important}
  .tcrm-new-lead-footer{padding:12px 18px!important;min-height:72px!important}
  .tcrm-new-lead-section-icon{width:42px!important;height:42px!important;flex-basis:42px!important}
  .tcrm-new-lead-modal [data-slot="dialog-close"]{top:18px!important;right:18px!important}
  .tcrm-new-lead-modal[dir="rtl"] [data-slot="dialog-close"]{right:auto!important;left:18px!important}
}

@media (prefers-reduced-motion:reduce){
  .tcrm-new-lead-modal *,
  body:has(.tcrm-new-lead-modal) [data-slot="select-content"],
  body:has(.tcrm-new-lead-modal) [data-slot="popover-content"]{transition-duration:.001ms!important;animation-duration:.001ms!important}
}
'''

if original != text:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / f"LeadsList.tsx.{stamp}.new-lead-v1-2.bak"
    shutil.copy2(TARGET, backup)
    TARGET.write_text(text, encoding="utf-8")
else:
    backup = None

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("NEW_LEAD_PREMIUM_V1_2=YES")
print("EXECUTIVE_FIDELITY=YES")
print("DASHBOARD_V28_IDENTITY=YES")
print("PALETTE_CHANGED=NO")
print(f"NEW_LEAD_SELECTS_ANCHORED={select_count}")
print("DROPDOWN_TRIGGER_WIDTH_LOCK=YES")
print("DROPDOWN_MAX_HEIGHT_SCROLL=YES")
print("SECTION_GLASS_CARDS=YES")
print("PREMIUM_DEPTH=YES")
print("FORM_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
if backup:
    print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx,client/src/new-lead-premium-v1-2.css")
print("ERROR=NONE")
