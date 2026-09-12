#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/new-lead-premium-v1-3.css"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
PREV_MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_2_EXECUTIVE_FIDELITY"
MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_3_TEAM_DASHBOARD_LUXURY"
PREV_IMPORT = 'import "../new-lead-premium-v1-2.css";'
CSS_IMPORT = 'import "../new-lead-premium-v1-3.css";'


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)


if not TARGET.exists():
    fail(f"TARGET_MISSING:{TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

# V1.3 is a visual-only layer over the already-applied V1.2 New Lead modal.
guards = [
    PREV_MARKER,
    PREV_IMPORT,
    'tcrm-new-lead-modal',
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
    '<PhoneInput',
    '<CountrySelect',
    'tcrm-new-lead-footer',
    'tcrm-new-lead-notes',
]
for token in guards:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

# Import one isolated CSS layer only; no form structure or logic changes.
if CSS_IMPORT not in text:
    text = text.replace(PREV_IMPORT, PREV_IMPORT + '\n' + CSS_IMPORT + '\n// ' + MARKER, 1)
elif MARKER not in text:
    text = text.replace(CSS_IMPORT, CSS_IMPORT + '\n// ' + MARKER, 1)

# Ensure form logic remains intact after import-only source change.
for token in guards[3:]:
    if token not in text:
        fail(f"POST_GUARD_FAILED:{token}")

css = r'''/* TCRM_NEW_LEAD_MODAL_PREMIUM_V1_3_TEAM_DASHBOARD_LUXURY
   Visual-only layer over New Lead V1.2.
   PRIMARY UX/UI REFERENCE: TCRM Team Dashboard Premium V2.2 / V2.1 dark surface system.
   Design language: pearl depth, luminous indigo/violet, restrained glass, deep navy dark,
   crisp hierarchy, executive SaaS density, subtle glow. No business logic changes.
*/

/* ============================================================
   BACKDROP — make the form feel like a focused executive workspace
   ============================================================ */
body:has(.tcrm-new-lead-modal) [data-slot="dialog-overlay"] {
  background:
    radial-gradient(circle at 16% 10%, rgba(87,74,255,.15), transparent 32rem),
    radial-gradient(circle at 88% 12%, rgba(47,117,255,.12), transparent 34rem),
    rgba(10,18,38,.46) !important;
  backdrop-filter: blur(14px) saturate(.82) !important;
  -webkit-backdrop-filter: blur(14px) saturate(.82) !important;
}

/* ============================================================
   MODAL SHELL — Team Dashboard pearl/glow language
   ============================================================ */
.tcrm-new-lead-modal {
  width:min(920px,calc(100vw - 42px)) !important;
  max-width:920px !important;
  max-height:min(94vh,1040px) !important;
  border-radius:30px !important;
  border:1px solid rgba(101,110,222,.26) !important;
  background:
    radial-gradient(circle at 8% -5%,rgba(99,102,241,.10),transparent 25rem),
    radial-gradient(circle at 93% 4%,rgba(59,130,246,.075),transparent 28rem),
    linear-gradient(180deg,rgba(255,255,255,.998),rgba(246,248,255,.992)) !important;
  box-shadow:
    0 54px 140px -36px rgba(23,31,83,.48),
    0 26px 64px -34px rgba(79,70,229,.34),
    0 0 0 1px rgba(255,255,255,.76) inset,
    0 0 46px -28px rgba(86,91,255,.60) !important;
  isolation:isolate !important;
}

.tcrm-new-lead-modal::before {
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:2px;
  z-index:20;
  pointer-events:none;
  background:linear-gradient(90deg,transparent 4%,rgba(130,114,255,.86) 22%,rgba(88,124,255,.95) 52%,rgba(76,158,255,.68) 78%,transparent 96%);
  box-shadow:0 0 22px rgba(99,102,241,.50);
}

.tcrm-new-lead-modal::after {
  content:"";
  position:absolute;
  inset:1px;
  border-radius:29px;
  pointer-events:none;
  z-index:3;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.90),
    inset 0 0 36px rgba(99,102,241,.022);
}

/* ============================================================
   HERO — luminous but controlled, matching Team Dashboard accents
   ============================================================ */
.tcrm-new-lead-header {
  min-height:130px !important;
  padding:30px 38px 28px !important;
  background:
    radial-gradient(circle at 84% -20%,rgba(255,255,255,.34),transparent 32%),
    radial-gradient(circle at 72% 118%,rgba(64,149,255,.30),transparent 35%),
    radial-gradient(circle at 15% 115%,rgba(157,107,255,.40),transparent 42%),
    linear-gradient(116deg,#32105f 0%,#4f1ca3 29%,#4f46e5 65%,#5c6df4 100%) !important;
  border-bottom:1px solid rgba(255,255,255,.16) !important;
  box-shadow:
    inset 0 -1px 0 rgba(255,255,255,.11),
    0 22px 50px -28px rgba(74,58,190,.52) !important;
}

.tcrm-new-lead-header::before {
  content:"";
  position:absolute;
  inset:-80px -30px -90px 40%;
  border-radius:50%;
  pointer-events:none;
  background:
    radial-gradient(ellipse at 45% 45%,rgba(255,255,255,.22),transparent 20%),
    radial-gradient(ellipse at 52% 54%,rgba(74,169,255,.22),transparent 34%),
    radial-gradient(ellipse at 35% 66%,rgba(135,92,255,.28),transparent 42%);
  filter:blur(4px);
  transform:rotate(-8deg);
}

.tcrm-new-lead-header::after {
  content:"";
  position:absolute;
  left:0;right:0;bottom:0;
  height:1px;
  background:linear-gradient(90deg,transparent,rgba(196,181,253,.66),rgba(96,165,250,.64),transparent);
  box-shadow:0 0 18px rgba(129,140,248,.45);
  pointer-events:none;
}

.tcrm-new-lead-header-icon {
  width:58px !important;
  height:58px !important;
  border-radius:18px !important;
  background:
    radial-gradient(circle at 30% 18%,rgba(255,255,255,.40),transparent 38%),
    linear-gradient(145deg,rgba(255,255,255,.29),rgba(255,255,255,.10)) !important;
  border:1px solid rgba(255,255,255,.45) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.42),
    0 16px 34px -18px rgba(18,13,79,.72),
    0 0 28px -12px rgba(205,193,255,.72) !important;
}

.tcrm-new-lead-header h2 {
  font-size:26px !important;
  font-weight:850 !important;
  letter-spacing:-.03em !important;
  text-shadow:0 2px 20px rgba(29,18,90,.28);
}
.tcrm-new-lead-header p {
  margin-top:5px !important;
  font-size:13.5px !important;
  font-weight:520 !important;
  color:rgba(255,255,255,.80) !important;
}

.tcrm-new-lead-modal [data-slot="dialog-close"] {
  width:40px !important;
  height:40px !important;
  top:26px !important;
  right:26px !important;
  border-radius:13px !important;
  color:#fff !important;
  opacity:.95 !important;
  background:linear-gradient(145deg,rgba(255,255,255,.21),rgba(255,255,255,.08)) !important;
  border:1px solid rgba(255,255,255,.32) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.20),0 12px 24px -16px rgba(20,12,78,.65) !important;
  backdrop-filter:blur(12px) !important;
}
.tcrm-new-lead-modal [data-slot="dialog-close"]:hover {
  background:rgba(255,255,255,.25) !important;
  transform:translateY(-1px);
}
.tcrm-new-lead-modal[dir="rtl"] [data-slot="dialog-close"]{right:auto!important;left:26px!important}

/* ============================================================
   BODY — pearl depth, not flat white
   ============================================================ */
.tcrm-new-lead-form { background:transparent !important; }
.tcrm-new-lead-body {
  max-height:calc(94vh - 224px) !important;
  padding:30px 38px 32px !important;
  background:
    radial-gradient(circle at 5% 2%,rgba(99,102,241,.050),transparent 24rem),
    radial-gradient(circle at 96% 14%,rgba(59,130,246,.040),transparent 26rem),
    linear-gradient(180deg,rgba(250,251,255,.995),rgba(246,248,255,.985)) !important;
  scrollbar-width:thin !important;
  scrollbar-color:rgba(99,102,241,.28) transparent !important;
}
.tcrm-new-lead-body::-webkit-scrollbar{width:4px!important}
.tcrm-new-lead-body::-webkit-scrollbar-track{background:transparent!important}
.tcrm-new-lead-body::-webkit-scrollbar-thumb{
  background:linear-gradient(180deg,rgba(99,102,241,.42),rgba(139,92,246,.24))!important;
  border-radius:999px!important;
}

/* ============================================================
   SECTION CARDS — derived from Team Dashboard analytics cards
   ============================================================ */
.tcrm-new-lead-section {
  position:relative !important;
  overflow:hidden !important;
  padding:22px 22px 23px !important;
  margin:0 0 18px !important;
  border:1px solid rgba(102,109,214,.18) !important;
  border-radius:21px !important;
  background:
    radial-gradient(circle at 0 0,rgba(102,92,255,.055),transparent 19rem),
    radial-gradient(circle at 100% 100%,rgba(47,123,255,.040),transparent 22rem),
    linear-gradient(145deg,rgba(255,255,255,.965),rgba(248,250,255,.90)) !important;
  box-shadow:
    0 24px 60px -42px rgba(72,78,170,.36),
    inset 0 1px 0 rgba(255,255,255,.96) !important;
  transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease !important;
}
.tcrm-new-lead-section:hover {
  transform:translateY(-1px);
  border-color:rgba(103,113,232,.30) !important;
  box-shadow:
    0 28px 66px -42px rgba(72,78,170,.42),
    0 0 30px -25px rgba(99,102,241,.46),
    inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.tcrm-new-lead-section::before {
  content:"";
  position:absolute;
  inset:20px auto 20px 0;
  width:3px;
  border-radius:999px;
  background:linear-gradient(180deg,rgba(89,98,255,.96),rgba(139,92,246,.58),rgba(59,130,246,.18));
  box-shadow:0 0 18px rgba(99,102,241,.36);
  opacity:.90;
}
.tcrm-new-lead-modal[dir="rtl"] .tcrm-new-lead-section::before{left:auto;right:0}
.tcrm-new-lead-section::after {
  content:"";
  position:absolute;
  inset:0;
  pointer-events:none;
  background:linear-gradient(120deg,rgba(255,255,255,.30),transparent 24%,transparent 75%,rgba(99,102,241,.018));
}
.tcrm-new-lead-section + .tcrm-new-lead-section{padding-top:22px!important}
.tcrm-new-lead-body > .h-px{display:none!important}

.tcrm-new-lead-section-heading {
  gap:15px !important;
  margin-bottom:21px !important;
  position:relative;
  z-index:1;
}
.tcrm-new-lead-section-icon {
  width:50px !important;
  height:50px !important;
  flex-basis:50px !important;
  border-radius:15px !important;
  color:#554be2 !important;
  background:
    radial-gradient(circle at 30% 18%,rgba(255,255,255,.98),transparent 40%),
    linear-gradient(145deg,rgba(235,239,255,.99),rgba(241,237,255,.94)) !important;
  border:1px solid rgba(99,102,241,.25) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,1),
    0 12px 25px -14px rgba(79,70,229,.44),
    0 0 24px -14px rgba(99,102,241,.42) !important;
}
.tcrm-new-lead-section-title {
  font-size:14px !important;
  font-weight:850 !important;
  letter-spacing:.045em !important;
  color:#202a44 !important;
}
.tcrm-new-lead-section-subtitle {
  margin-top:4px !important;
  font-size:12.5px !important;
  line-height:1.45 !important;
  color:#77839c !important;
}

/* ============================================================
   CONTROLS — premium density / clearer focus hierarchy
   ============================================================ */
.tcrm-new-lead-body label {
  color:#27334d !important;
  font-size:11.5px !important;
  font-weight:790 !important;
  letter-spacing:.035em !important;
}
.tcrm-new-lead-body input,
.tcrm-new-lead-body textarea,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country,
.tcrm-new-lead-phone > div:first-child {
  border:1px solid rgba(126,139,174,.32) !important;
  background:
    linear-gradient(180deg,rgba(255,255,255,.998),rgba(247,249,255,.965)) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,1),
    0 7px 18px -14px rgba(42,51,93,.28) !important;
  transition:border-color .18s ease,box-shadow .18s ease,background .18s ease,transform .18s ease !important;
}
.tcrm-new-lead-body input,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country {
  height:52px !important;
  min-height:52px !important;
  border-radius:14px !important;
  font-size:13px !important;
}
.tcrm-new-lead-phone > div:first-child{min-height:52px!important;border-radius:14px!important}
.tcrm-new-lead-phone > div:first-child > button,
.tcrm-new-lead-phone > div:first-child > input{height:50px!important}
.tcrm-new-lead-body textarea{
  min-height:122px !important;
  border-radius:15px !important;
  padding:14px 15px !important;
  line-height:1.6 !important;
}
.tcrm-new-lead-body input:hover,
.tcrm-new-lead-body textarea:hover,
.tcrm-new-lead-body [data-slot="select-trigger"]:hover,
.tcrm-new-lead-country:hover,
.tcrm-new-lead-phone > div:first-child:hover {
  border-color:rgba(99,102,241,.48) !important;
  box-shadow:0 10px 22px -16px rgba(79,70,229,.30),inset 0 1px 0 #fff !important;
}
.tcrm-new-lead-body input:focus,
.tcrm-new-lead-body textarea:focus,
.tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.tcrm-new-lead-country:focus-visible,
.tcrm-new-lead-phone > div:first-child:focus-within {
  border-color:rgba(99,102,241,.92) !important;
  background:#fff !important;
  box-shadow:
    0 0 0 3px rgba(99,102,241,.11),
    0 15px 28px -18px rgba(79,70,229,.34),
    0 0 24px -18px rgba(99,102,241,.50),
    inset 0 1px 0 #fff !important;
}

/* Validation remains obvious without overpowering the design. */
.tcrm-new-lead-body .border-red-400,
.tcrm-new-lead-body input.border-red-400,
.tcrm-new-lead-body [data-slot="select-trigger"].border-red-400 {
  border-color:rgba(239,68,68,.72)!important;
  box-shadow:0 0 0 3px rgba(239,68,68,.08)!important;
}

/* ============================================================
   DROPDOWNS / POPOVERS — same luminous executive surface
   ============================================================ */
body:has(.tcrm-new-lead-modal) [data-radix-popper-content-wrapper]{z-index:850!important;pointer-events:auto!important}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content,
body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  border:1px solid rgba(102,109,214,.24) !important;
  background:
    radial-gradient(circle at 0 0,rgba(99,102,241,.08),transparent 16rem),
    linear-gradient(155deg,rgba(255,255,255,.998),rgba(246,248,255,.995)) !important;
  box-shadow:
    0 30px 70px -32px rgba(49,46,129,.48),
    0 18px 38px -28px rgba(15,23,42,.26),
    inset 0 1px 0 rgba(255,255,255,1) !important;
  backdrop-filter:blur(24px) saturate(1.12) !important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content{
  border-radius:16px!important;
  padding:7px!important;
  max-height:min(300px,var(--radix-select-content-available-height))!important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]{
  min-height:42px!important;
  border-radius:11px!important;
  font-size:12.5px!important;
  font-weight:670!important;
}
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-highlighted],
body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]:focus{
  color:#29245d!important;
  background:linear-gradient(90deg,rgba(99,102,241,.15),rgba(59,130,246,.07))!important;
  box-shadow:inset 0 0 0 1px rgba(99,102,241,.10)!important;
}

/* ============================================================
   FOOTER — executive command bar
   ============================================================ */
.tcrm-new-lead-footer {
  min-height:88px !important;
  padding:17px 38px !important;
  border-top:1px solid rgba(102,109,214,.16) !important;
  background:
    linear-gradient(180deg,rgba(251,252,255,.94),rgba(245,247,255,.975)) !important;
  box-shadow:
    0 -18px 42px -34px rgba(63,72,128,.34),
    inset 0 1px 0 rgba(255,255,255,.92) !important;
  backdrop-filter:blur(22px) saturate(1.08) !important;
}
.tcrm-new-lead-cancel,
.tcrm-new-lead-save {
  height:50px !important;
  border-radius:14px !important;
  font-size:13px !important;
  font-weight:780 !important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease !important;
}
.tcrm-new-lead-cancel {
  min-width:116px !important;
  background:rgba(255,255,255,.82) !important;
  border-color:rgba(126,139,174,.28) !important;
  box-shadow:inset 0 1px 0 #fff,0 9px 20px -17px rgba(31,41,85,.32) !important;
}
.tcrm-new-lead-save {
  min-width:164px !important;
  background:linear-gradient(112deg,#5a22b4 0%,#4f46e5 56%,#596df6 100%) !important;
  border:1px solid rgba(255,255,255,.18) !important;
  box-shadow:
    0 16px 34px -16px rgba(79,70,229,.60),
    0 0 26px -15px rgba(99,102,241,.72),
    inset 0 1px 0 rgba(255,255,255,.27) !important;
}
.tcrm-new-lead-cancel:hover,.tcrm-new-lead-save:hover{transform:translateY(-1px)}
.tcrm-new-lead-save:hover{box-shadow:0 19px 38px -16px rgba(79,70,229,.68),0 0 30px -13px rgba(99,102,241,.74),inset 0 1px 0 rgba(255,255,255,.30)!important}

/* ============================================================
   DARK — Team Dashboard V2.1 surface system
   ============================================================ */
.dark body:has(.tcrm-new-lead-modal) [data-slot="dialog-overlay"] {
  background:
    radial-gradient(circle at 10% 5%,rgba(82,68,255,.18),transparent 31rem),
    radial-gradient(circle at 89% 10%,rgba(42,122,255,.14),transparent 34rem),
    rgba(2,8,18,.72) !important;
  backdrop-filter:blur(16px) saturate(.80)!important;
}
.dark .tcrm-new-lead-modal {
  border-color:rgba(101,126,218,.34)!important;
  background:
    radial-gradient(circle at 10% 2%,rgba(82,68,255,.16),transparent 28rem),
    radial-gradient(circle at 92% 4%,rgba(42,122,255,.12),transparent 30rem),
    linear-gradient(180deg,rgba(8,20,39,.998),rgba(5,15,31,.998))!important;
  box-shadow:
    0 56px 140px -34px rgba(0,0,0,.94),
    0 0 42px -25px rgba(79,99,255,.72),
    inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark .tcrm-new-lead-modal::after{box-shadow:inset 0 1px 0 rgba(255,255,255,.055),inset 0 0 38px rgba(74,87,255,.025)!important}
.dark .tcrm-new-lead-body {
  background:
    radial-gradient(circle at 4% 0%,rgba(84,78,255,.08),transparent 22rem),
    radial-gradient(circle at 100% 20%,rgba(33,115,255,.055),transparent 24rem),
    linear-gradient(180deg,#071223 0%,#071426 100%)!important;
}
.dark .tcrm-new-lead-section {
  border-color:rgba(103,132,226,.30)!important;
  background:
    radial-gradient(circle at 0 0,rgba(84,78,255,.09),transparent 22rem),
    radial-gradient(circle at 100% 100%,rgba(33,115,255,.07),transparent 24rem),
    linear-gradient(145deg,rgba(14,30,55,.985),rgba(8,21,41,.98))!important;
  box-shadow:
    0 28px 68px -38px rgba(0,0,0,.96),
    0 0 28px -24px rgba(79,99,255,.74),
    inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark .tcrm-new-lead-section:hover {
  border-color:rgba(114,138,246,.42)!important;
  box-shadow:0 30px 70px -40px rgba(0,0,0,.98),0 0 34px -24px rgba(81,98,255,.82),inset 0 1px 0 rgba(255,255,255,.06)!important;
}
.dark .tcrm-new-lead-section-icon {
  color:#a9b5ff!important;
  background:linear-gradient(145deg,rgba(70,83,184,.26),rgba(43,58,130,.14))!important;
  border-color:rgba(113,130,255,.34)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 0 25px -12px rgba(83,91,255,.76)!important;
}
.dark .tcrm-new-lead-section-title{color:#f3f6ff!important}
.dark .tcrm-new-lead-section-subtitle{color:#9eacc7!important}
.dark .tcrm-new-lead-body label{color:#d6dff1!important}
.dark .tcrm-new-lead-body input,
.dark .tcrm-new-lead-body textarea,
.dark .tcrm-new-lead-body [data-slot="select-trigger"],
.dark .tcrm-new-lead-country,
.dark .tcrm-new-lead-phone > div:first-child {
  color:#edf3ff!important;
  border-color:rgba(103,132,226,.26)!important;
  background:linear-gradient(180deg,rgba(12,27,51,.96),rgba(8,21,41,.96))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 8px 20px -17px rgba(0,0,0,.85)!important;
}
.dark .tcrm-new-lead-body input::placeholder,
.dark .tcrm-new-lead-body textarea::placeholder{color:#71809b!important}
.dark .tcrm-new-lead-body input:focus,
.dark .tcrm-new-lead-body textarea:focus,
.dark .tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.dark .tcrm-new-lead-country:focus-visible,
.dark .tcrm-new-lead-phone > div:first-child:focus-within {
  border-color:rgba(114,138,246,.76)!important;
  background:rgba(12,27,51,.99)!important;
  box-shadow:0 0 0 3px rgba(99,102,241,.12),0 0 26px -16px rgba(81,98,255,.82),inset 0 1px 0 rgba(255,255,255,.055)!important;
}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content,
.dark body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  color:#edf3ff!important;
  border-color:rgba(103,132,226,.34)!important;
  background:
    radial-gradient(circle at 0 0,rgba(84,78,255,.12),transparent 18rem),
    linear-gradient(155deg,rgba(12,27,51,.998),rgba(7,18,36,.998))!important;
  box-shadow:0 30px 72px -30px rgba(0,0,0,.92),0 0 30px -22px rgba(79,99,255,.78),inset 0 1px 0 rgba(255,255,255,.05)!important;
}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]{color:#dfe7f8!important}
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"][data-highlighted],
.dark body:has(.tcrm-new-lead-modal) .tcrm-new-lead-select-content [data-slot="select-item"]:focus{color:#fff!important;background:linear-gradient(90deg,rgba(91,87,255,.23),rgba(51,108,255,.11))!important}
.dark .tcrm-new-lead-footer {
  border-top-color:rgba(103,132,226,.22)!important;
  background:linear-gradient(180deg,rgba(9,22,42,.96),rgba(6,17,34,.985))!important;
  box-shadow:0 -18px 44px -34px rgba(0,0,0,.90),inset 0 1px 0 rgba(255,255,255,.04)!important;
}
.dark .tcrm-new-lead-cancel {
  color:#dbe5f7!important;
  background:rgba(14,30,55,.86)!important;
  border-color:rgba(103,132,226,.28)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04)!important;
}

/* ============================================================
   RESPONSIVE / RTL
   ============================================================ */
@media (max-width:760px){
  .tcrm-new-lead-modal{width:calc(100vw - 18px)!important;border-radius:22px!important;max-height:96vh!important}
  .tcrm-new-lead-header{min-height:104px!important;padding:22px!important}
  .tcrm-new-lead-header-icon{width:46px!important;height:46px!important}
  .tcrm-new-lead-header h2{font-size:21px!important}
  .tcrm-new-lead-body{padding:20px!important;max-height:calc(96vh - 190px)!important}
  .tcrm-new-lead-section{padding:18px!important;border-radius:17px!important}
  .tcrm-new-lead-section-icon{width:44px!important;height:44px!important;flex-basis:44px!important}
  .tcrm-new-lead-footer{min-height:74px!important;padding:12px 18px!important}
  .tcrm-new-lead-cancel{min-width:96px!important}
  .tcrm-new-lead-save{min-width:132px!important}
}

@media (prefers-reduced-motion:reduce){
  .tcrm-new-lead-section,.tcrm-new-lead-cancel,.tcrm-new-lead-save,.tcrm-new-lead-modal [data-slot="dialog-close"]{transition:none!important}
}
'''

# Backup only the one application source file we intentionally touch.
if original != text:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / f"LeadsList.tsx.{stamp}.new-lead-v1-3.bak"
    shutil.copy2(TARGET, backup)
    TARGET.write_text(text, encoding="utf-8")
else:
    backup = None

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("NEW_LEAD_PREMIUM_V1_3=YES")
print("TEAM_DASHBOARD_REFERENCE=YES")
print("TEAM_DASHBOARD_V2_2_LIGHT_PEARL_DEPTH=YES")
print("TEAM_DASHBOARD_V2_1_DARK_SURFACE_SYSTEM=YES")
print("LUXURY_MODAL_SHELL=YES")
print("LUMINOUS_HEADER=YES")
print("EXECUTIVE_SECTION_CARDS=YES")
print("PREMIUM_CONTROLS=YES")
print("PREMIUM_FOOTER=YES")
print("DROPDOWN_FIX_PRESERVED=YES")
print("PALETTE_CHANGED=NO")
print("FORM_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
if backup:
    print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx,client/src/new-lead-premium-v1-3.css")
print("ERROR=NONE")
