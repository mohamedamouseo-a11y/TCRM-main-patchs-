#!/usr/bin/env python3
# TCRM_LEAD_PROFILE_PREMIUM_V2_7_4_EDIT_SAVE_ACTION_FIX
# Adds an always-visible Save/Cancel action bar when editing Lead Details.
# Frontend UX only. Reuses the existing updateLead mutation and onSaveLead handler.

from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/pages/LeadProfile.tsx"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_7_4_EDIT_SAVE_ACTION_FIX"

if not TARGET.exists():
    print("PATCH=FAIL")
    print(f"ERROR=MISSING_FILE:{TARGET}")
    sys.exit(1)

text = TARGET.read_text(encoding="utf-8")

if MARKER in text:
    print("PATCH=PASS")
    print("ALREADY_APPLIED=YES")
    print("FILES_CHANGED=NONE")
    sys.exit(0)

anchor = '                <TabsContent value="details" className="tcrm-lp-v26-details-tab mt-0">'
if anchor not in text:
    print("PATCH=FAIL")
    print("ERROR=DETAILS_TAB_ANCHOR_NOT_FOUND")
    sys.exit(1)

save_bar = '''                {/* TCRM_LEAD_PROFILE_PREMIUM_V2_7_4_EDIT_SAVE_ACTION_FIX */}\n                {activeTab === "details" && editMode && canEditLead && (\n                  <div className="tcrm-lp-v274-edit-savebar sticky top-16 z-30 mb-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-indigo-200/70 bg-white/95 px-4 py-3 shadow-lg shadow-indigo-950/10 backdrop-blur dark:border-indigo-400/20 dark:bg-slate-950/95">\n                    <div className="min-w-0">\n                      <div className="text-sm font-bold text-slate-800 dark:text-slate-100">\n                        {isRTL ? "وضع تعديل بيانات العميل" : "Editing lead details"}\n                      </div>\n                      <div className="text-xs text-slate-500 dark:text-slate-400">\n                        {isRTL ? "احفظ التغييرات قبل مغادرة الصفحة" : "Save your changes before leaving this page"}\n                      </div>\n                    </div>\n                    <div className="flex items-center gap-2">\n                      <Button\n                        type="button"\n                        variant="outline"\n                        className="rounded-xl"\n                        onClick={() => setEditMode(false)}\n                        disabled={updateLead.isPending}\n                      >\n                        {t("cancel")}\n                      </Button>\n                      <Button\n                        type="button"\n                        className="gap-2 rounded-xl text-white shadow-md"\n                        style={{ background: tokens.primaryColor }}\n                        onClick={handleSubmit(onSaveLead)}\n                        disabled={updateLead.isPending}\n                      >\n                        {updateLead.isPending ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}\n                        {updateLead.isPending ? (isRTL ? "جارٍ الحفظ..." : "Saving...") : (isRTL ? "حفظ التغييرات" : "Save Changes")}\n                      </Button>\n                    </div>\n                  </div>\n                )}\n\n'''

# Backup current local file before applying.
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / f".patch-backups/lead-profile-v2-7-4-edit-save-{stamp}/client/src/pages/LeadProfile.tsx"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(TARGET, backup)

updated = text.replace(anchor, save_bar + anchor, 1)

# Also add a top-of-file marker for quick verification.
lines = updated.splitlines()
insert_at = 0
while insert_at < len(lines) and lines[insert_at].startswith("//"):
    insert_at += 1
lines.insert(insert_at, f"// {MARKER}")
updated = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

TARGET.write_text(updated, encoding="utf-8")

print("PATCH=PASS")
print("ALREADY_APPLIED=NO")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx")
print(f"BACKUP={backup.relative_to(ROOT)}")
print("EDIT_SAVE_BAR=YES")
print("EXISTING_UPDATE_MUTATION_REUSED=YES")
print("BACKEND_CHANGED=NO")
print("ERROR=NONE")
