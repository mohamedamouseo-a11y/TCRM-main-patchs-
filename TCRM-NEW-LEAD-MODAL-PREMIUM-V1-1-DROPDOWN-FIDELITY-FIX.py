#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/new-lead-premium-v1-1.css"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
V1_MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1"
MARKER = "TCRM_NEW_LEAD_MODAL_PREMIUM_V1_1_DROPDOWN_FIDELITY_FIX"
V1_IMPORT = 'import "../new-lead-premium-v1.css";'
CSS_IMPORT = 'import "../new-lead-premium-v1-1.css";'


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)


if not TARGET.exists():
    fail(f"TARGET_MISSING:{TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

# V1.1 MUST layer on top of the already-applied New Lead V1.
for token in [V1_MARKER, V1_IMPORT, 'tcrm-new-lead-modal', '<Dialog open={showNewLead} onOpenChange={setShowNewLead}>']:
    if token not in text:
        fail(f"V1_GUARD_MISSING:{token}")

# Protect all critical form logic anchors. This patch is presentation + portal interaction only.
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
    '<PhoneInput',
    '<CountrySelect',
]
for token in logic_guards:
    if token not in text:
        fail(f"LOGIC_GUARD_MISSING:{token}")

if CSS_IMPORT not in text:
    text = text.replace(
        V1_IMPORT,
        V1_IMPORT + '\n' + CSS_IMPORT + '\n// ' + MARKER,
        1,
    )
elif MARKER not in text:
    text = text.replace(CSS_IMPORT, CSS_IMPORT + '\n// ' + MARKER, 1)

css = r'''/* TCRM_NEW_LEAD_MODAL_PREMIUM_V1_1_DROPDOWN_FIDELITY_FIX
   Layered on New Lead V1.
   Goals:
   1) Restore Radix Select/Popover interaction inside modal.
   2) Keep dropdown portals above the modal/overlay and pointer-interactive.
   3) Tighten scale/hierarchy/depth to Agent Dashboard V28 / Leads Premium identity.
   No business logic changes. */

/* ============================================================
   PORTAL INTERACTION FIX — CRITICAL
   Radix Dialog can place pointer-events:none on BODY while open.
   Select/Popover content is portaled back to BODY, outside the
   dialog content node which explicitly has pointer-events:auto.
   Force the portaled layers and their Popper wrapper interactive.
   ============================================================ */
body:has(.tcrm-new-lead-modal) [data-radix-popper-content-wrapper],
body:has(.tcrm-new-lead-modal) [data-slot="select-content"],
body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  pointer-events: auto !important;
  z-index: 700 !important;
}

/* The actual floating surfaces must remain above dialog shell/overlay. */
body:has(.tcrm-new-lead-modal) [data-slot="select-content"],
body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  border: 1px solid rgba(99,102,241,.24) !important;
  border-radius: 15px !important;
  background:
    radial-gradient(115% 100% at 0% 0%, rgba(124,92,255,.09), transparent 48%),
    linear-gradient(155deg, rgba(255,255,255,.995), rgba(247,248,255,.99)) !important;
  box-shadow:
    0 28px 64px -28px rgba(49,46,129,.38),
    0 12px 26px -20px rgba(15,23,42,.20),
    inset 0 1px 0 rgba(255,255,255,.98) !important;
  backdrop-filter: blur(22px) saturate(1.10) !important;
}

body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"] {
  min-height: 38px !important;
  margin: 2px 5px !important;
  border-radius: 10px !important;
  font-size: 12.5px !important;
  font-weight: 620 !important;
  color: #39445d !important;
}

body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"]:focus,
body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"][data-highlighted] {
  background: linear-gradient(90deg, rgba(99,102,241,.13), rgba(124,92,255,.07)) !important;
  color: #29255a !important;
}

body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] input {
  pointer-events: auto !important;
}

/* Country / phone popup list rows. */
body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] button {
  pointer-events: auto !important;
}

.dark body:has(.tcrm-new-lead-modal) [data-slot="select-content"],
.dark body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
  border-color: rgba(119,133,255,.32) !important;
  background:
    radial-gradient(120% 100% at 0% 0%, rgba(99,82,255,.16), transparent 50%),
    linear-gradient(155deg, rgba(13,28,53,.995), rgba(7,19,38,.997)) !important;
  box-shadow:
    0 32px 70px -28px rgba(0,0,0,.88),
    0 0 34px -25px rgba(99,82,255,.48),
    inset 0 1px 0 rgba(255,255,255,.055) !important;
}

.dark body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"] {
  color: #d5dced !important;
}

.dark body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"]:focus,
.dark body:has(.tcrm-new-lead-modal) [data-slot="select-content"] [data-slot="select-item"][data-highlighted] {
  color: #fff !important;
  background: linear-gradient(90deg, rgba(110,91,255,.22), rgba(65,105,255,.11)) !important;
}

/* ============================================================
   V1.1 DASHBOARD FIDELITY POLISH
   Same indigo/violet/blue identity. No new palette.
   ============================================================ */
.tcrm-new-lead-modal {
  width: min(820px, calc(100vw - 36px)) !important;
  max-width: 820px !important;
  border-radius: 26px !important;
  border-color: rgba(99,102,241,.30) !important;
  box-shadow:
    0 38px 110px rgba(15,23,42,.25),
    0 14px 44px rgba(79,70,229,.14),
    0 0 0 1px rgba(255,255,255,.46) inset !important;
}

.tcrm-new-lead-header {
  min-height: 112px !important;
  padding: 26px 32px 24px !important;
  background:
    radial-gradient(circle at 86% 0%, rgba(255,255,255,.24), transparent 28%),
    radial-gradient(circle at 20% 120%, rgba(129,140,248,.36), transparent 42%),
    radial-gradient(circle at 58% 30%, rgba(96,165,250,.15), transparent 36%),
    linear-gradient(118deg, #3b0764 0%, #5b21b6 31%, #4f46e5 68%, #6366f1 100%) !important;
  box-shadow: inset 0 -1px 0 rgba(255,255,255,.14), 0 16px 38px rgba(79,70,229,.12);
}

.tcrm-new-lead-header-icon {
  width: 52px !important;
  height: 52px !important;
  border-radius: 16px !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.34),
    0 12px 28px rgba(25,18,85,.24),
    0 0 24px rgba(196,181,253,.16) !important;
}

.tcrm-new-lead-header h2 {
  font-size: 22px !important;
  font-weight: 780 !important;
}

.tcrm-new-lead-header p {
  font-size: 13.5px !important;
  color: rgba(255,255,255,.80) !important;
}

.tcrm-new-lead-body {
  padding: 27px 32px 29px !important;
  scrollbar-width: thin;
  scrollbar-color: rgba(99,102,241,.28) transparent;
}

.tcrm-new-lead-body::-webkit-scrollbar { width: 4px !important; }
.tcrm-new-lead-body::-webkit-scrollbar-thumb {
  border: 0 !important;
  background: linear-gradient(180deg, rgba(99,102,241,.40), rgba(139,92,246,.26)) !important;
  border-radius: 999px !important;
}

.tcrm-new-lead-section { padding-bottom: 25px !important; }
.tcrm-new-lead-section + .tcrm-new-lead-section { padding-top: 25px !important; }
.tcrm-new-lead-section-heading { gap: 13px !important; margin-bottom: 19px !important; }

.tcrm-new-lead-section-icon {
  width: 46px !important;
  height: 46px !important;
  flex-basis: 46px !important;
  border-radius: 14px !important;
  border-color: rgba(99,102,241,.22) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.98),
    0 9px 20px rgba(79,70,229,.10),
    0 0 22px rgba(99,102,241,.055) !important;
}

.tcrm-new-lead-section-title {
  font-size: 13px !important;
  letter-spacing: .075em !important;
  font-weight: 820 !important;
}

.tcrm-new-lead-section-subtitle {
  margin-top: 4px !important;
  font-size: 12.5px !important;
  color: #78849e !important;
}

.tcrm-new-lead-body label {
  font-size: 11.5px !important;
  font-weight: 750 !important;
  color: #303c57 !important;
}

.tcrm-new-lead-body input,
.tcrm-new-lead-body [data-slot="select-trigger"],
.tcrm-new-lead-country {
  height: 48px !important;
  min-height: 48px !important;
  border-radius: 13px !important;
  border-color: rgba(133,148,177,.34) !important;
}

.tcrm-new-lead-phone > div:first-child { min-height: 48px !important; border-radius: 13px !important; }
.tcrm-new-lead-phone > div:first-child > button,
.tcrm-new-lead-phone > div:first-child > input { height: 46px !important; }

.tcrm-new-lead-body input:focus,
.tcrm-new-lead-body textarea:focus,
.tcrm-new-lead-body [data-slot="select-trigger"]:focus-visible,
.tcrm-new-lead-country:focus-visible,
.tcrm-new-lead-phone > div:first-child:focus-within {
  border-color: rgba(99,102,241,.82) !important;
  box-shadow:
    0 0 0 3px rgba(99,102,241,.12),
    0 10px 24px rgba(79,70,229,.075) !important;
}

.tcrm-new-lead-footer {
  min-height: 80px !important;
  padding: 15px 32px !important;
  background: rgba(250,251,255,.93) !important;
  border-top-color: rgba(99,102,241,.15) !important;
  box-shadow: 0 -14px 36px rgba(51,65,85,.045) !important;
}

.tcrm-new-lead-cancel,
.tcrm-new-lead-save {
  height: 46px !important;
  border-radius: 13px !important;
  font-weight: 730 !important;
}

.tcrm-new-lead-save {
  min-width: 148px !important;
  box-shadow:
    0 13px 28px rgba(79,70,229,.28),
    0 0 22px rgba(99,102,241,.10),
    inset 0 1px 0 rgba(255,255,255,.24) !important;
}

.dark .tcrm-new-lead-modal {
  border-color: rgba(119,133,255,.42) !important;
  box-shadow:
    0 42px 120px rgba(0,0,0,.58),
    0 14px 48px rgba(79,70,229,.18),
    0 0 0 1px rgba(255,255,255,.025) inset !important;
}

.dark .tcrm-new-lead-section-subtitle { color: #9ba9c4 !important; }
.dark .tcrm-new-lead-body label { color: #d0d8e8 !important; }
.dark .tcrm-new-lead-section-icon {
  border-color: rgba(129,140,248,.31) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.065),
    0 10px 24px rgba(0,0,0,.19),
    0 0 24px rgba(99,102,241,.08) !important;
}

@media (max-width: 640px) {
  .tcrm-new-lead-modal {
    width: calc(100vw - 20px) !important;
    border-radius: 20px !important;
  }
  .tcrm-new-lead-header { min-height: 96px !important; padding: 20px !important; }
  .tcrm-new-lead-body { padding: 20px !important; }
  .tcrm-new-lead-footer { min-height: 70px !important; padding: 12px 20px !important; }
  .tcrm-new-lead-section-icon { width: 40px !important; height: 40px !important; flex-basis: 40px !important; }
}

@media (prefers-reduced-motion: reduce) {
  body:has(.tcrm-new-lead-modal) [data-slot="select-content"],
  body:has(.tcrm-new-lead-modal) [data-slot="popover-content"] {
    animation-duration: .001ms !important;
  }
}
'''

# Preserve original logic anchors after import-only source change.
for token in logic_guards:
    if token not in text:
        fail(f"POST_LOGIC_GUARD_FAILED:{token}")

# Idempotent: only write when needed.
if original != text:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / f"LeadsList.tsx.{stamp}.new-lead-v1-1.bak"
    shutil.copy2(TARGET, backup)
    TARGET.write_text(text, encoding="utf-8")
else:
    backup = None

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("NEW_LEAD_PREMIUM_V1_1=YES")
print("DROPDOWN_PORTAL_POINTER_EVENTS_FIX=YES")
print("DROPDOWN_PORTAL_Z_INDEX_FIX=YES")
print("SELECT_DROPDOWNS_TARGETED=YES")
print("PHONE_COUNTRY_POPOVER_TARGETED=YES")
print("COUNTRY_SELECT_POPOVER_TARGETED=YES")
print("DASHBOARD_FIDELITY_POLISH=YES")
print("PALETTE_CHANGED=NO")
print("FORM_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
if backup:
    print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx,client/src/new-lead-premium-v1-1.css")
print("ERROR=NONE")
