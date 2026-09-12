#!/usr/bin/env python3
from pathlib import Path
import datetime, shutil, sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/new-lead-premium-v1-4.css"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
PREV_MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_3_TEAM_DASHBOARD_LUXURY"
MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_4_TEAM_DASHBOARD_FIDELITY"
PREV_IMPORT = 'import "../new-lead-premium-v1-3.css";'
CSS_IMPORT = 'import "../new-lead-premium-v1-4.css";'

def fail(msg):
    print(f"ERROR={msg}")
    sys.exit(1)

if not TARGET.exists(): fail("TARGET_MISSING")
text = TARGET.read_text(encoding="utf-8")
original = text

guards = [
    PREV_MARKER, PREV_IMPORT,
    '<Dialog open={showNewLead} onOpenChange={setShowNewLead}>',
    'onSubmit={handleSubmit(onSubmit)}',
    'setValue("phone", fullPhone);',
    'setValue("country", c.name);',
    'setValue("leadQuality", v as any, { shouldDirty: true })',
    'setValue("fitStatus", v as any, { shouldDirty: true })',
    'setValue("stage", v, { shouldDirty: true })',
    'setValue("campaignName", v === "none" ? "" : v);',
    'setValue("ownerId", v === "none" ? undefined : Number(v), { shouldDirty: true })',
    'createLead.isPending || !!formPhoneConflict?.conflictWithAnotherSalesAgent',
    'tcrm-new-lead-contact', 'tcrm-new-lead-details', 'tcrm-new-lead-assignment', 'tcrm-new-lead-notes'
]
for token in guards:
    if token not in text: fail(f"GUARD_MISSING:{token}")

if CSS_IMPORT not in text:
    text = text.replace(PREV_IMPORT, PREV_IMPORT + '\n' + CSS_IMPORT + '\n// ' + MARKER, 1)
elif MARKER not in text:
    text = text.replace(CSS_IMPORT, CSS_IMPORT + '\n// ' + MARKER, 1)

for token in guards[2:]:
    if token not in text: fail(f"POST_GUARD_FAILED:{token}")

css = r'''/* TCRM_NEW_LEAD_MODAL_PREMIUM_V1_4_TEAM_DASHBOARD_FIDELITY
   Visual fidelity correction over V1.3.
   PRIMARY UX/UI REFERENCE: TCRM Team Dashboard Premium V2.2 light + V2.1 dark.
   Fixes observed runtime QA: weak field hierarchy, undersized select triggers,
   inconsistent dark controls, excessive wash, and footer/body balance.
*/

/* ---------- Shell / composition ---------- */
.tcrm-new-lead-modal{
  width:min(940px,calc(100vw - 36px))!important;
  max-width:940px!important;
  border-radius:28px!important;
  border-color:rgba(102,109,214,.24)!important;
  box-shadow:0 52px 132px -40px rgba(35,43,104,.48),0 24px 58px -32px rgba(79,70,229,.30),inset 0 1px 0 rgba(255,255,255,.90)!important;
}
.tcrm-new-lead-header{
  min-height:116px!important;
  padding:26px 38px 24px!important;
}
.tcrm-new-lead-header h2{font-size:25px!important}
.tcrm-new-lead-header-icon{width:56px!important;height:56px!important}

/* ---------- Body / spacing: executive, not oversized ---------- */
.tcrm-new-lead-body{
  padding:28px 38px 30px!important;
  gap:0!important;
  background:radial-gradient(circle at 5% 0%,rgba(99,102,241,.046),transparent 24rem),radial-gradient(circle at 96% 8%,rgba(59,130,246,.035),transparent 26rem),linear-gradient(180deg,#fbfcff 0%,#f5f7fd 100%)!important;
}
.tcrm-new-lead-section{
  padding:21px 22px 22px!important;
  margin:0 0 18px!important;
  border-radius:20px!important;
  border-color:rgba(102,109,214,.20)!important;
  background:radial-gradient(circle at 0 0,rgba(102,92,255,.052),transparent 18rem),linear-gradient(145deg,rgba(255,255,255,.985),rgba(247,249,255,.94))!important;
  box-shadow:0 24px 58px -42px rgba(72,78,170,.36),inset 0 1px 0 rgba(255,255,255,.98)!important;
}
.tcrm-new-lead-section-heading{margin-bottom:18px!important}
.tcrm-new-lead-section-icon{width:48px!important;height:48px!important;flex-basis:48px!important}
.tcrm-new-lead-section-title{font-size:14px!important;letter-spacing:.025em!important}

/* ---------- Critical runtime fix: every field/select must fill its grid cell ---------- */
.tcrm-new-lead-modal .tcrm-new-lead-section .grid > div{min-width:0!important;width:100%!important}
.tcrm-new-lead-modal .tcrm-new-lead-section input,
.tcrm-new-lead-modal .tcrm-new-lead-section textarea,
.tcrm-new-lead-modal .tcrm-new-lead-section [data-slot="select-trigger"],
.tcrm-new-lead-modal .tcrm-new-lead-section button[role="combobox"],
.tcrm-new-lead-modal .tcrm-new-lead-country,
.tcrm-new-lead-modal .tcrm-new-lead-phone{width:100%!important;max-width:none!important}
.tcrm-new-lead-modal .tcrm-new-lead-details > .grid,
.tcrm-new-lead-modal .tcrm-new-lead-contact > .grid{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  column-gap:14px!important;
  row-gap:14px!important;
}
.tcrm-new-lead-modal .tcrm-new-lead-details [data-slot="select-trigger"],
.tcrm-new-lead-modal .tcrm-new-lead-details button[role="combobox"],
.tcrm-new-lead-modal .tcrm-new-lead-assignment [data-slot="select-trigger"],
.tcrm-new-lead-modal .tcrm-new-lead-assignment button[role="combobox"]{
  display:flex!important;
  width:100%!important;
  min-width:0!important;
  justify-content:space-between!important;
}

/* ---------- Controls: Team Dashboard pearl depth ---------- */
.tcrm-new-lead-modal .tcrm-new-lead-body input,
.tcrm-new-lead-modal .tcrm-new-lead-body textarea,
.tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"],
.tcrm-new-lead-modal .tcrm-new-lead-country,
.tcrm-new-lead-modal .tcrm-new-lead-phone > div:first-child{
  border:1px solid rgba(122,136,174,.30)!important;
  background:linear-gradient(180deg,#fff 0%,#f8faff 100%)!important;
  color:#202a44!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,1),0 8px 20px -16px rgba(48,57,104,.34)!important;
}
.tcrm-new-lead-modal .tcrm-new-lead-body input,
.tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"],
.tcrm-new-lead-modal .tcrm-new-lead-country{height:50px!important;min-height:50px!important;border-radius:13px!important}
.tcrm-new-lead-modal .tcrm-new-lead-phone > div:first-child{min-height:50px!important;border-radius:13px!important}
.tcrm-new-lead-modal .tcrm-new-lead-phone > div:first-child>button,
.tcrm-new-lead-modal .tcrm-new-lead-phone > div:first-child>input{height:48px!important}
.tcrm-new-lead-modal .tcrm-new-lead-body input:hover,
.tcrm-new-lead-modal .tcrm-new-lead-body textarea:hover,
.tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"]:hover,
.tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"]:hover{border-color:rgba(99,102,241,.46)!important}
.tcrm-new-lead-modal .tcrm-new-lead-body input:focus,
.tcrm-new-lead-modal .tcrm-new-lead-body textarea:focus,
.tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"]:focus-visible{
  border-color:rgba(99,102,241,.88)!important;
  box-shadow:0 0 0 3px rgba(99,102,241,.10),0 14px 28px -20px rgba(79,70,229,.40),inset 0 1px 0 #fff!important;
}

/* ---------- Footer: slimmer command bar ---------- */
.tcrm-new-lead-footer{
  min-height:78px!important;
  padding:14px 38px!important;
  background:linear-gradient(180deg,rgba(251,252,255,.96),rgba(245,247,255,.99))!important;
  border-top-color:rgba(102,109,214,.16)!important;
}
.tcrm-new-lead-cancel,.tcrm-new-lead-save{height:48px!important;border-radius:13px!important}
.tcrm-new-lead-save{min-width:164px!important;box-shadow:0 16px 34px -16px rgba(79,70,229,.62),0 0 28px -15px rgba(99,102,241,.70),inset 0 1px 0 rgba(255,255,255,.28)!important}

/* ---------- Dark: strict Team Dashboard V2.1 surface consistency ---------- */
.dark .tcrm-new-lead-modal{
  border-color:rgba(103,123,210,.34)!important;
  background:radial-gradient(circle at 10% 0%,rgba(82,68,255,.14),transparent 28rem),radial-gradient(circle at 92% 4%,rgba(42,122,255,.10),transparent 30rem),linear-gradient(180deg,#071223 0%,#06101f 100%)!important;
}
.dark .tcrm-new-lead-body{
  background:radial-gradient(circle at 4% 0%,rgba(84,78,255,.075),transparent 22rem),radial-gradient(circle at 100% 18%,rgba(33,115,255,.05),transparent 24rem),linear-gradient(180deg,#071223 0%,#071426 100%)!important;
}
.dark .tcrm-new-lead-section{
  border-color:rgba(103,132,226,.30)!important;
  background:radial-gradient(circle at 0 0,rgba(84,78,255,.085),transparent 22rem),radial-gradient(circle at 100% 100%,rgba(33,115,255,.06),transparent 24rem),linear-gradient(145deg,rgba(14,30,55,.985),rgba(8,21,41,.98))!important;
  box-shadow:0 28px 64px -42px rgba(0,0,0,.92),inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark .tcrm-new-lead-modal .tcrm-new-lead-body input:not([type="checkbox"]),
.dark .tcrm-new-lead-modal .tcrm-new-lead-body textarea,
.dark .tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"],
.dark .tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"],
.dark .tcrm-new-lead-modal .tcrm-new-lead-country,
.dark .tcrm-new-lead-modal .tcrm-new-lead-phone > div:first-child{
  color:#edf3ff!important;
  background:linear-gradient(180deg,rgba(12,27,51,.99),rgba(8,21,41,.985))!important;
  background-color:#0c1b33!important;
  border-color:rgba(103,132,226,.30)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.045),0 8px 20px -17px rgba(0,0,0,.78)!important;
}
.dark .tcrm-new-lead-modal .tcrm-new-lead-body input[type="datetime-local"]{color-scheme:dark!important;background-color:#0c1b33!important}
.dark .tcrm-new-lead-modal .tcrm-new-lead-body input::placeholder,
.dark .tcrm-new-lead-modal .tcrm-new-lead-body textarea::placeholder{color:#7f8da7!important;opacity:1!important}
.dark .tcrm-new-lead-modal .tcrm-new-lead-body [data-slot="select-trigger"] span,
.dark .tcrm-new-lead-modal .tcrm-new-lead-body button[role="combobox"] span{color:#dfe7f8!important}
.dark .tcrm-new-lead-footer{background:linear-gradient(180deg,rgba(8,21,41,.985),rgba(6,17,34,.998))!important;border-top-color:rgba(103,132,226,.24)!important}
.dark .tcrm-new-lead-cancel{color:#e4ebf8!important;background:rgba(13,29,54,.96)!important;border-color:rgba(103,132,226,.30)!important}

/* Portals keep V1.2 interaction fix and match the same surfaces. */
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content{width:var(--radix-select-trigger-width)!important;min-width:var(--radix-select-trigger-width)!important;max-width:min(430px,calc(100vw - 24px))!important}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content,
.dark body:has(.tcrm-new-lead-modal) [data-slot="popover-content"]{
  color:#eef3ff!important;
  border-color:rgba(103,132,226,.34)!important;
  background:radial-gradient(circle at 0 0,rgba(84,78,255,.10),transparent 16rem),linear-gradient(155deg,rgba(13,29,54,.998),rgba(7,19,38,.998))!important;
  box-shadow:0 30px 72px -30px rgba(0,0,0,.94),0 0 28px -20px rgba(79,99,255,.52),inset 0 1px 0 rgba(255,255,255,.05)!important;
}

@media(max-width:640px){
  .tcrm-new-lead-modal{width:calc(100vw - 16px)!important;border-radius:21px!important}
  .tcrm-new-lead-header{min-height:96px!important;padding:20px!important}
  .tcrm-new-lead-body{padding:18px!important}
  .tcrm-new-lead-section{padding:17px!important}
  .tcrm-new-lead-modal .tcrm-new-lead-details > .grid,
  .tcrm-new-lead-modal .tcrm-new-lead-contact > .grid{grid-template-columns:1fr!important}
  .tcrm-new-lead-footer{padding:12px 18px!important;min-height:70px!important}
}
'''

if original != text:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / f"LeadsList.tsx.{stamp}.new-lead-v1-4.bak"
    shutil.copy2(TARGET, backup)
    TARGET.write_text(text, encoding="utf-8")
else:
    backup = None
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("NEW_LEAD_PREMIUM_V1_4=YES")
print("TEAM_DASHBOARD_PRIMARY_REFERENCE=YES")
print("FULL_WIDTH_SELECT_FIX=YES")
print("DARK_CONTROL_CONSISTENCY_FIX=YES")
print("LIGHT_PEARL_DEPTH_REFINED=YES")
print("FORM_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
if backup: print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx,client/src/new-lead-premium-v1-4.css")
print("ERROR=NONE")
